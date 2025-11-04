from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from ...architecture.storage import get_chroma_client


router = APIRouter()


@router.get("/faq/ai")
async def faq_ai_get(query: str = Query(..., min_length=2)) -> Dict[str, Any]:
    chroma = get_chroma_client()
    col = chroma.get_or_create_collection("faq_knowledge")
    res = col.query(query_texts=[query], n_results=3, include=["documents", "metadatas", "distances"])
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    answer = docs[0] if docs else "Ответ не найден"
    sources = [
        {"file": f"faq:{m.get('id', idx)}", "lines": "-", "score": float(dists[idx]) if idx < len(dists) else None}
        for idx, m in enumerate(metas)
    ]
    return {"answer": answer, "sources": sources}


@router.post("/faq/ai")
async def faq_ai_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    q = payload.get("query") or ""
    return await faq_ai_get(query=q)


