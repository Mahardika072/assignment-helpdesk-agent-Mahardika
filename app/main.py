"""
Entry point aplikasi FastAPI: IT Helpdesk Assistant.

Alur: request /ask -> router (intent detection) -> RAG atau tool -> response terstruktur
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.rag import build_index
from app.router import handle_query

logger = logging.getLogger("helpdesk")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bangun index FAISS sekali saat aplikasi start."""
    try:
        await asyncio.to_thread(build_index)
        logger.info("Index FAISS siap.")
    except Exception as exc:
        # Aplikasi tetap hidup; index akan dicoba lagi di request pertama.
        logger.warning("Index gagal dibangun saat startup: %s", exc)
    yield


app = FastAPI(title="IT Helpdesk Assistant API", lifespan=lifespan)


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    status: str
    intent: str
    data: str


def _error(http_status: int, intent: str, message: str) -> JSONResponse:
    """Response error dengan struktur yang sama seperti response sukses."""
    return JSONResponse(
        status_code=http_status,
        content={"status": "error", "intent": intent, "data": message},
    )


@app.get("/health")
async def health():
    """Endpoint sederhana untuk memastikan service berjalan."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Menerima pertanyaan bebas dari user (informasi/kebijakan ATAU cek status tiket)
    lalu meneruskannya ke router.
    """
    query = request.query.strip()
    if not query:
        return _error(400, "unknown", "Pertanyaan tidak boleh kosong.")

    try:
        result = await handle_query(query)
    except Exception as exc:
        logger.exception("Gagal memproses query: %s", exc)
        return _error(
            503,
            "unknown",
            "Maaf, layanan AI sedang tidak dapat merespons. Silakan coba lagi nanti.",
        )

    return AskResponse(**result)