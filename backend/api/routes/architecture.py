from __future__ import annotations

import json
from datetime import datetime
import os
import httpx
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body

from ...architecture.architecture_parser import ArchitectureParser
from ...architecture.storage import ArchitectureStorage, get_redis_client


router = APIRouter()


def _build_mermaid(edges: List[Dict[str, str]]) -> str:
    lines = ["graph LR"]
    for e in edges[:5000]:  # safety limit
        lines.append(f"  {e['source'].replace('.', '_')} -->|{e['type']}| {e['target'].replace('.', '_')}")
    return "\n".join(lines)


def _load_graph_from_redis() -> Dict[str, Any]:
    r = get_redis_client()
    raw = r.get("arch:graph")
    if not raw:
        raise HTTPException(status_code=404, detail="Graph not built yet")
    try:
        return json.loads(raw)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupted graph data in Redis")


def _notify_devops(event: str, details: Dict[str, Any]) -> None:
    base = os.getenv("STAFFPROBOT_URL", "http://localhost:8001")
    url = f"{base.rstrip('/')}/api/admin/devops/brain/update"
    payload = {"event": event, **details}
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(url, json=payload)
    except Exception:
        # тихо игнорируем, чтобы не ломать основной процесс
        pass


@router.post("/architecture/reindex")
async def reindex_architecture(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    def job() -> None:
        storage = ArchitectureStorage()
        # Load previous graph for diff
        prev = None
        try:
            prev = _load_graph_from_redis()
        except HTTPException:
            prev = None

        parser = ArchitectureParser(project_path="/projects/staffprobot")
        graph = parser.parse()

        # Compute diff
        if prev:
            prev_nodes = {n.get("id") for n in prev.get("nodes", [])}
            prev_edges = {(e.get("source"), e.get("target"), e.get("type")) for e in prev.get("edges", [])}
            cur_nodes = {n.id for n in graph.nodes}
            cur_edges = {(e.source, e.target, e.type) for e in graph.edges}
            diff = {
                "nodes_added": sorted(list(cur_nodes - prev_nodes)),
                "nodes_removed": sorted(list(prev_nodes - cur_nodes)),
                "edges_added": sorted([{"source": s, "target": t, "type": ty} for (s, t, ty) in (cur_edges - prev_edges)], key=lambda x: (x["source"], x["target"])),
                "edges_removed": sorted([{"source": s, "target": t, "type": ty} for (s, t, ty) in (prev_edges - cur_edges)], key=lambda x: (x["source"], x["target"])),
                "prev_stats": prev.get("stats", {}),
                "cur_stats": graph.stats,
            }
            storage.save_diff(diff)

        storage.save_graph_to_redis(graph)
        storage.save_graph_to_chroma(graph)
        snap_path = storage.snapshot_graph_json(graph)
        # уведомление DevOps
        _notify_devops(
            "reindex_complete",
            {
                "stats": graph.stats,
                "snapshot": os.path.basename(snap_path),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            },
        )

    background_tasks.add_task(job)
    return {"status": "started"}


@router.post("/architecture/analyze")
async def analyze_architecture(
    background_tasks: BackgroundTasks,
    payload: Dict[str, Any] = Body(default={}),
) -> Dict[str, Any]:
    commit_sha = payload.get("commit_sha")
    project = payload.get("project", "staffprobot")

    def job() -> None:
        storage = ArchitectureStorage()
        # Previous for diff
        try:
            prev = _load_graph_from_redis()
        except HTTPException:
            prev = None

        parser = ArchitectureParser(project_path=f"/projects/{project}")
        graph = parser.parse()

        diff: Dict[str, Any] = {}
        if prev:
            prev_nodes = {n.get("id") for n in prev.get("nodes", [])}
            prev_edges = {(e.get("source"), e.get("target"), e.get("type")) for e in prev.get("edges", [])}
            cur_nodes = {n.id for n in graph.nodes}
            cur_edges = {(e.source, e.target, e.type) for e in graph.edges}
            diff = {
                "nodes_added": sorted(list(cur_nodes - prev_nodes)),
                "nodes_removed": sorted(list(prev_nodes - cur_nodes)),
                "edges_added": sorted([{"source": s, "target": t, "type": ty} for (s, t, ty) in (cur_edges - prev_edges)], key=lambda x: (x["source"], x["target"])),
                "edges_removed": sorted([{"source": s, "target": t, "type": ty} for (s, t, ty) in (prev_edges - cur_edges)], key=lambda x: (x["source"], x["target"])),
                "prev_stats": prev.get("stats", {}),
                "cur_stats": graph.stats,
                "commit_sha": commit_sha,
            }
            storage.save_diff(diff)
            # Incremental update in Chroma
            storage.apply_incremental_to_chroma(graph, diff)
        else:
            # First run: full save
            storage.save_graph_to_chroma(graph)

        # Persist graph and snapshot
        storage.save_graph_to_redis(graph)
        snapshot_path = storage.snapshot_graph_json(graph)
        snapshot_id = commit_sha or os.path.basename(snapshot_path)
        storage.save_snapshot_to_chroma(snapshot_id=snapshot_id, graph=graph, meta={"project": project, "commit_sha": commit_sha})
        # уведомление DevOps
        _notify_devops(
            "analyze_complete",
            {
                "project": project,
                "commit_sha": commit_sha,
                "cur_stats": graph.stats,
                "diff": diff or {},
                "snapshot": snapshot_id,
                "updated_at": datetime.utcnow().isoformat() + "Z",
            },
        )

    background_tasks.add_task(job)
    return {"status": "started", "project": project, "commit_sha": commit_sha}


@router.get("/architecture/graph")
async def get_graph() -> Dict[str, Any]:
    return _load_graph_from_redis()


@router.get("/architecture/node/{node_id}")
async def get_node(node_id: str) -> Dict[str, Any]:
    data = _load_graph_from_redis()
    node = next((n for n in data["nodes"] if n.get("id") == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    # neighbors
    incoming = [e for e in data["edges"] if e.get("target") == node_id]
    outgoing = [e for e in data["edges"] if e.get("source") == node_id]
    return {"node": node, "incoming": incoming, "outgoing": outgoing}


@router.get("/architecture/meta")
async def get_meta() -> Dict[str, Any]:
    data = _load_graph_from_redis()
    roles = sorted({n.get("role") for n in data["nodes"] if n.get("role")})
    subsystems = sorted({n.get("subsystem") for n in data["nodes"] if n.get("subsystem")})
    return {
        "roles": roles,
        "subsystems": subsystems,
        "stats": data.get("stats", {}),
        "updated_at": data.get("updated_at"),
    }


@router.post("/architecture/weights")
async def update_weights(payload: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    # payload example: {"roles": {...}, "subsystems": {...}}
    r = get_redis_client()
    for key in ("roles", "subsystems"):
        if key in payload:
            r.set(f"arch:weights:{key}", json.dumps(payload[key]))
    return {"status": "ok"}


@router.post("/architecture/tasks/sync")
async def sync_tasks(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    def job() -> None:
        import re
        tasks: List[Dict[str, Any]] = []
        sources: List[str] = [
            "/projects/staffprobot/doc/plans/roadmap.md",
            "/projects/staffprobot/doc/DEVOPS_COMMAND_CENTER.md",
        ]
        for path in sources:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            for line in content.splitlines():
                m = re.match(r"^\s*- \[( |x)\]\s+(.*)$", line)
                if m:
                    done = (m.group(1).lower() == "x")
                    title = m.group(2).strip()
                    tasks.append({"title": title, "done": done, "source": os.path.basename(path)})

        # Build light relations by mentioning function names (label) in task titles
        storage = ArchitectureStorage()
        graph = _load_graph_from_redis()
        function_labels = [(n.get("id"), n.get("label", "").lower()) for n in graph.get("nodes", []) if n.get("type") == "function"]
        relates: List[Dict[str, str]] = []
        for t in tasks:
            title_l = t["title"].lower()
            for node_id, label in function_labels:
                if label and label in title_l:
                    relates.append({"task": t["title"], "function_id": node_id})

        storage.save_tasks({"tasks": tasks, "relations": relates})

    background_tasks.add_task(job)
    return {"status": "started"}


@router.get("/architecture/diagram")
async def get_diagram() -> Dict[str, str]:
    data = _load_graph_from_redis()
    mermaid = _build_mermaid(data.get("edges", []))
    return {"mermaid": mermaid, "generated_at": datetime.utcnow().isoformat() + "Z"}


@router.get("/architecture/diff")
async def get_diff() -> Dict[str, Any]:
    storage = ArchitectureStorage()
    diff = storage.load_diff()
    return diff or {"status": "empty"}

@router.get("/architecture/tasks")
async def get_tasks() -> Dict[str, Any]:
    storage = ArchitectureStorage()
    return storage.load_tasks() or {"tasks": [], "relations": []}

@router.get("/architecture/snapshots")
async def get_snapshots(limit: int = 20) -> Dict[str, Any]:
    storage = ArchitectureStorage()
    return {"items": storage.load_snapshots(limit=limit)}


