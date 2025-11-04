from __future__ import annotations

import os
from typing import Any, Dict, List
import hashlib
import time
import subprocess
import datetime as dt

import httpx
from fastapi import APIRouter, HTTPException

from ...architecture.storage import get_chroma_client, get_redis_client


router = APIRouter()


def _staffprobot_base() -> str:
    return os.getenv("STAFFPROBOT_URL", "http://localhost:8001").rstrip("/")


def _get_commit_history(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        out = subprocess.check_output([
            "git", "-C", "/projects/staffprobot",
            "log", f"-n", str(limit), "--pretty=format:%h|%an|%ad|%s", "--date=iso"
        ], stderr=subprocess.STDOUT, timeout=10)
        lines = out.decode("utf-8", errors="ignore").splitlines()
        items: List[Dict[str, Any]] = []
        for line in lines:
            parts = line.split("|", 3)
            if len(parts) == 4:
                sha, author, date_str, subject = parts
                items.append({
                    "id": sha,
                    "sha": sha,
                    "author": author,
                    "date": date_str,
                    "subject": subject,
                })
        return items
    except Exception:
        return []


@router.post("/datasets/sync")
async def sync_datasets(mode: str = "full") -> Dict[str, Any]:
    """Загрузка FAQ, багов и changelog из StaffProBot в ChromaDB.
    Коллекции: faq_knowledge, bug_context, dev_changes.
    """
    base = _staffprobot_base()
    endpoints = {
        "faq_knowledge": f"{base}/api/admin/devops/export/faq",
        "bug_context": f"{base}/api/admin/devops/export/bugs",
        "dev_changes": f"{base}/api/admin/devops/export/changelog",
    }
    stats: Dict[str, Any] = {}
    chroma = get_chroma_client()
    redis = get_redis_client()

    # optional embedder (sentence-transformers)
    embedder = None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        embedder = None

    def _hash(text: str) -> str:
        return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in endpoints.items():
            t0 = time.time()
            added = updated = skipped = 0
            err = None
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    err = f"HTTP {r.status_code}"
                else:
                    items = r.json().get("items", [])
                    col = chroma.get_or_create_collection(name)
                    # load existing
                    try:
                        existing = col.get(ids=None, include=["metadatas"])
                        ids_exist = existing.get("ids", []) or []
                        metas_exist = existing.get("metadatas", []) or []
                        id2hash = {ids_exist[i]: (metas_exist[i] or {}).get("doc_hash") for i in range(len(ids_exist))}
                    except Exception:
                        id2hash = {}
                    ids = []
                    docs = []
                    metas = []
                    for idx, it in enumerate(items):
                        _id = f"{name}:{it.get('id', idx)}"
                        doc = it.get("answer") or it.get("description") or it.get("title") or ""
                        h = _hash(doc)
                        if _id in id2hash:
                            if id2hash[_id] == h:
                                skipped += 1
                                continue
                            updated += 1
                        else:
                            added += 1
                        ids.append(_id)
                        docs.append(doc)
                        metas.append({**it, "doc_hash": h})
                    if ids:
                        if embedder:
                            try:
                                emb = embedder.encode(docs, normalize_embeddings=True).tolist()  # type: ignore
                                col.add(ids=ids, documents=docs, metadatas=metas, embeddings=emb)
                            except Exception:
                                col.add(ids=ids, documents=docs, metadatas=metas)
                        else:
                            col.add(ids=ids, documents=docs, metadatas=metas)
            except Exception as e:
                err = str(e)
            finally:
                stats[name] = {"added": added, "updated": updated, "skipped": skipped, "duration_sec": round(time.time()-t0,3), "error": err}

    # commit history
    commits = _get_commit_history(100)
    t0 = time.time()
    err = None
    try:
        col = chroma.get_or_create_collection("commit_history")
        existing = col.get(ids=None)
        existed = set(existing.get("ids", []) or [])
        new_items = [c for c in commits if f"commit:{c['sha']}" not in existed]
        if new_items:
            col.add(
                ids=[f"commit:{c['sha']}" for c in new_items],
                documents=[c.get("subject", "") for c in new_items],
                metadatas=new_items,
            )
        stats["commit_history"] = {"added": len(new_items), "updated": 0, "skipped": len(commits)-len(new_items), "duration_sec": round(time.time()-t0,3), "error": err}
    except Exception as e:
        stats["commit_history"] = {"added": 0, "updated": 0, "skipped": 0, "duration_sec": round(time.time()-t0,3), "error": str(e)}

    try:
        redis.set("datasets:last_sync", str(stats))
    except Exception:
        pass

    return {"status": "ok", "stats": stats}


@router.get("/datasets/metrics")
async def datasets_metrics() -> Dict[str, Any]:
    chroma = get_chroma_client()
    names = ["faq_knowledge", "bug_context", "dev_changes", "commit_history"]
    out: Dict[str, int] = {}
    for n in names:
        try:
            col = chroma.get_or_create_collection(n)
            out[n] = len(col.get(ids=None).get("ids", []))
        except Exception:
            out[n] = 0
    return {"collections": out, "timestamp": dt.datetime.utcnow().isoformat() + "Z"}


