from __future__ import annotations

import ast
import os
from typing import Dict, List, Optional, Tuple

from .models import GraphData, Node, Edge
from .weights import compute_weight, DEFAULT_ROLE_WEIGHTS, DEFAULT_SUBSYSTEM_WEIGHTS


ROLE_FOLDERS = {"owner", "manager", "employee", "admin", "moderator"}


class ImportResolver(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: Dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:  # type: ignore[override]
        for alias in node.names:
            self.imports[alias.asname or alias.name.split(".")[-1]] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # type: ignore[override]
        if not node.module:
            return
        for alias in node.names:
            self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"


class CallCollector(ast.NodeVisitor):
    def __init__(self, imports: Dict[str, str], current_module: str) -> None:
        self.imports = imports
        self.current_module = current_module
        self.calls: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # type: ignore[override]
        name = self._resolve_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    def _resolve_name(self, func: ast.AST) -> Optional[str]:
        if isinstance(func, ast.Name):
            base = self.imports.get(func.id)
            return base or f"{self.current_module}.{func.id}"
        if isinstance(func, ast.Attribute):
            # Resolve chained attributes best effort
            parts: List[str] = []
            node: ast.AST | None = func
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                root = self.imports.get(node.id, node.id)
                parts.append(root)
                parts.reverse()
                return ".".join(parts)
        return None


def _path_to_module(root: str, file_path: str) -> str:
    rel = os.path.relpath(file_path, root)
    no_ext = os.path.splitext(rel)[0]
    return no_ext.replace(os.sep, ".")


def classify_role_and_subsystem(relative_path: str) -> Tuple[str, str]:
    parts = relative_path.split(os.sep)
    role = "system"
    subsystem = os.path.splitext(os.path.basename(relative_path))[0]
    if "routes" in parts:
        i = parts.index("routes")
        if i + 1 < len(parts) and parts[i + 1] in ROLE_FOLDERS:
            role = parts[i + 1]
            if i + 2 < len(parts):
                subsystem = parts[i + 2]
    elif "handlers" in parts or "handlers_div" in parts:
        role = "system"
        if "handlers_div" in parts:
            i = parts.index("handlers_div")
            if i + 1 < len(parts):
                subsystem = parts[i + 1]
    elif "services" in parts:
        i = parts.index("services")
        if i + 1 < len(parts):
            subsystem = parts[i + 1]
    elif "entities" in parts:
        i = parts.index("entities")
        if i + 1 < len(parts):
            subsystem = parts[i + 1]
    return role, subsystem


class ArchitectureParser:
    def __init__(self, project_path: str) -> None:
        self.project_path = project_path

    def parse(self) -> GraphData:
        nodes: Dict[str, Node] = {}
        edges: List[Edge] = []

        # First pass: collect functions with FQN and metadata
        py_files: List[str] = []
        for root, _, files in os.walk(self.project_path):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

        for file_path in py_files:
            relative = os.path.relpath(file_path, self.project_path)
            role, subsystem = classify_role_and_subsystem(relative)
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    code = fh.read()
                tree = ast.parse(code, filename=file_path)
            except Exception:
                continue

            module_name = _path_to_module(self.project_path, file_path)
            resolver = ImportResolver()
            resolver.visit(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    fqn = f"{module_name}.{node.name}"
                    start_line = getattr(node, "lineno", 0)
                    end_line = getattr(node, "end_lineno", start_line)
                    node_id = fqn
                    if node_id not in nodes:
                        nodes[node_id] = Node(
                            id=node_id,
                            label=node.name,
                            type="function",
                            role=role,
                            subsystem=subsystem,
                            file=relative,
                            lines=f"{start_line}-{end_line}",
                            fqn=fqn,
                        )

                    # collect calls inside the function
                    calls = CallCollector(resolver.imports, module_name)
                    calls.visit(node)
                    for callee in calls.calls:
                        edges.append(Edge(source=node_id, target=callee, type="calls"))

        # Degree computation
        for e in edges:
            if e.source in nodes:
                nodes[e.source].degree_out += 1
            if e.target in nodes:
                nodes[e.target].degree_in += 1

        max_degree = max((n.degree_in + n.degree_out for n in nodes.values()), default=1)

        # Compute weights
        for n in nodes.values():
            n.weight = compute_weight(
                role=n.role or "system",
                subsystem=n.subsystem or "",
                degree_in=n.degree_in,
                degree_out=n.degree_out,
                max_degree=max_degree,
            )

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }
        return GraphData(nodes=list(nodes.values()), edges=edges, stats=stats)


