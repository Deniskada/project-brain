from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

import redis
from chromadb import HttpClient

from .models import GraphData, Node, Edge


def get_redis_client() -> redis.Redis:
    url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    return redis.Redis.from_url(url)


def get_chroma_client() -> HttpClient:
    host = os.getenv("CHROMA_HOST", "http://chromadb:8000")
    if host.startswith("http://"):
        host = host[len("http://") :]
    if ":" in host:
        host, port = host.split(":", 1)
    else:
        port = "8000"
    return HttpClient(host=host, port=int(port))


class ArchitectureStorage:
    def __init__(self) -> None:
        self.redis = get_redis_client()
        self.chroma = get_chroma_client()

    def save_graph_to_redis(self, graph: GraphData) -> None:
        payload = {
            "nodes": [node.__dict__ for node in graph.nodes],
            "edges": [edge.__dict__ for edge in graph.edges],
            "stats": graph.stats,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        data = json.dumps(payload, ensure_ascii=False)
        pipe = self.redis.pipeline()
        pipe.set("arch:graph:new", data)
        pipe.rename("arch:graph:new", "arch:graph")
        pipe.set("arch:stats", json.dumps({**graph.stats, "updated_at": payload["updated_at"]}))
        pipe.execute()

    def snapshot_graph_json(self, graph: GraphData, directory: str = "data") -> str:
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"architecture_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "nodes": [n.__dict__ for n in graph.nodes],
                    "edges": [e.__dict__ for e in graph.edges],
                    "stats": graph.stats,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        return path

    def save_graph_to_chroma(self, graph: GraphData) -> None:
        nodes_col = self.chroma.get_or_create_collection("arch_nodes")
        edges_col = self.chroma.get_or_create_collection("arch_edges")

        # Clear and re-add for bootstrap simplicity (iterative update supported via apply_incremental)
        try:
            nodes_col.delete()
        except Exception:
            pass
        try:
            edges_col.delete()
        except Exception:
            pass

        # Insert nodes
        if graph.nodes:
            nodes_col.add(
                ids=[n.id for n in graph.nodes],
                documents=[n.label for n in graph.nodes],
                metadatas=[
                    {
                        "type": n.type,
                        "role": n.role,
                        "subsystem": n.subsystem,
                        "file": n.file,
                        "lines": n.lines,
                        "fqn": n.fqn,
                        "weight": n.weight,
                        "degree_in": n.degree_in,
                        "degree_out": n.degree_out,
                    }
                    for n in graph.nodes
                ],
            )

        # Insert edges
        if graph.edges:
            edges_col.add(
                ids=[self._edge_id(e) for e in graph.edges],
                documents=[e.type for e in graph.edges],
                metadatas=[{"source": e.source, "target": e.target, "type": e.type} for e in graph.edges],
            )

    @staticmethod
    def _edge_id(e: Edge) -> str:
        return f"{e.source}|{e.type}|{e.target}"

    def save_snapshot_to_chroma(self, snapshot_id: str, graph: GraphData, meta: Dict[str, Any]) -> None:
        snaps = self.chroma.get_or_create_collection("arch_snapshots")
        snaps.add(
            ids=[snapshot_id],
            documents=["architecture_snapshot"],
            metadatas=[{
                "project": str(meta.get("project") or "staffprobot"),
                "commit_sha": str(meta.get("commit_sha") or ""),
                "stats_nodes": int(graph.stats.get("total_nodes", 0)),
                "stats_edges": int(graph.stats.get("total_edges", 0)),
                "created_at": datetime.utcnow().isoformat() + "Z",
            }],
        )
        # Persist short meta to Redis list for quick retrieval
        self.record_snapshot_meta({
            "id": snapshot_id,
            "project": str(meta.get("project") or "staffprobot"),
            "commit_sha": str(meta.get("commit_sha") or ""),
            "stats_nodes": int(graph.stats.get("total_nodes", 0)),
            "stats_edges": int(graph.stats.get("total_edges", 0)),
            "created_at": datetime.utcnow().isoformat() + "Z",
        })

    def record_snapshot_meta(self, meta: Dict[str, Any]) -> None:
        key = "arch:snapshots"
        self.redis.lpush(key, json.dumps(meta))
        # cap list to last 50
        self.redis.ltrim(key, 0, 49)

    def load_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        raw = self.redis.lrange("arch:snapshots", 0, max(0, limit - 1))
        out: List[Dict[str, Any]] = []
        for r in raw:
            try:
                out.append(json.loads(r))
            except Exception:
                continue
        return out

    def apply_incremental_to_chroma(self, graph: GraphData, diff: Dict[str, Any]) -> None:
        nodes_col = self.chroma.get_or_create_collection("arch_nodes")
        edges_col = self.chroma.get_or_create_collection("arch_edges")

        # Remove nodes
        removed_nodes = diff.get("nodes_removed", [])
        if removed_nodes:
            try:
                nodes_col.delete(ids=removed_nodes)
            except Exception:
                pass

        # Remove edges
        removed_edges = diff.get("edges_removed", [])
        for e in removed_edges:
            try:
                edges_col.delete(where={"source": e.get("source"), "target": e.get("target"), "type": e.get("type")})
            except Exception:
                pass

        # Add nodes
        added_nodes = set(diff.get("nodes_added", []))
        if added_nodes:
            nodes_map = {n.id: n for n in graph.nodes}
            to_add = [nodes_map[nid] for nid in added_nodes if nid in nodes_map]
            if to_add:
                nodes_col.add(
                    ids=[n.id for n in to_add],
                    documents=[n.label for n in to_add],
                    metadatas=[
                        {
                            "type": n.type,
                            "role": n.role,
                            "subsystem": n.subsystem,
                            "file": n.file,
                            "lines": n.lines,
                            "fqn": n.fqn,
                            "weight": n.weight,
                            "degree_in": n.degree_in,
                            "degree_out": n.degree_out,
                        }
                        for n in to_add
                    ],
                )

        # Add edges
        added_edges = diff.get("edges_added", [])
        if added_edges:
            edges_col.add(
                ids=[self._edge_id(Edge(source=e["source"], target=e["target"], type=e["type"])) for e in added_edges],
                documents=[e["type"] for e in added_edges],
                metadatas=[{"source": e["source"], "target": e["target"], "type": e["type"]} for e in added_edges],
            )

    # Diff helpers
    def save_diff(self, diff: Dict[str, Any]) -> None:
        payload = json.dumps({**diff, "generated_at": datetime.utcnow().isoformat() + "Z"})
        self.redis.set("arch:diff", payload)

    def load_diff(self) -> Dict[str, Any] | None:
        raw = self.redis.get("arch:diff")
        return json.loads(raw) if raw else None

    # Tasks helpers
    def save_tasks(self, tasks: Dict[str, Any]) -> None:
        self.redis.set("arch:tasks", json.dumps(tasks, ensure_ascii=False))

    def load_tasks(self) -> Dict[str, Any] | None:
        raw = self.redis.get("arch:tasks")
        return json.loads(raw) if raw else None


