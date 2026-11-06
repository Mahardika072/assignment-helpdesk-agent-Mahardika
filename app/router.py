"""
Router: menentukan apakah query butuh RAG (informasi/kebijakan)
atau tool call (cek status tiket).

Alur: user input -> intent detection -> RAG atau tool call
"""

import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.rag import answer_from_knowledge_base
from app.tools import get_ticket_status

load_dotenv()

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
INTENT_MODEL = os.environ.get("GEN_MODEL", "gemini-2.5-flash")

# Cocok dengan: TICKET-0005, ticket 5, tiket-12, TICKET0007
TICKET_ID_PATTERN = re.compile(r"(?:ticket|tiket)[-\s]?(\d{1,4})", re.IGNORECASE)

STATUS_KEYWORDS = [
    "status", "progres", "progress", "sampai mana",
    "sudah selesai", "diproses", "perkembangan", "cek tiket", "cek ticket",
]

FAQ_KEYWORDS = [
    "cuti", "password", "vpn", "laptop", "email", "gaji", "slip",
    "reimbursement", "asuransi", "izin", "sakit", "resign", "akses",
    "software", "perangkat", "onboarding", "karyawan baru", "rekening",
]


def extract_ticket_id(query: str) -> str | None:
    """Ekstrak ticket_id dan normalkan ke format TICKET-XXXX. None jika tidak ada."""
    match = TICKET_ID_PATTERN.search(query)
    if not match:
        return None
    return f"TICKET-{int(match.group(1)):04d}"


async def _classify_with_llm(query: str) -> str:
    """Lapis terakhir: minta LLM memilih 'faq' atau 'unknown'."""
    prompt = f"""Klasifikasikan pertanyaan karyawan berikut ke dalam satu kategori:
- faq: pertanyaan tentang kebijakan, prosedur, atau informasi seputar IT, HR, cuti,
  akses/password, perangkat kerja, atau onboarding perusahaan.
- unknown: pertanyaan yang tidak berkaitan dengan hal di atas, atau terlalu ambigu
  untuk dipahami.
Jawab hanya dengan satu kata: faq atau unknown.

Pertanyaan: {query}"""

    response = await _client.aio.models.generate_content(
        model=INTENT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0),
    )
    label = (response.text or "").strip().lower()
    return "faq" if "faq" in label else "unknown"


async def detect_intent(query: str) -> str:
    """Kembalikan 'ticket_status', 'faq', atau 'unknown'."""
    q = query.lower()

    # Lapis 1: ada nomor tiket -> pasti cek status
    if extract_ticket_id(query):
        return "ticket_status"

    # Lapis 2: menyebut tiket + kata status, walau tanpa nomor
    if ("tiket" in q or "ticket" in q) and any(k in q for k in STATUS_KEYWORDS):
        return "ticket_status"

    # Lapis 2b: kata kunci FAQ yang jelas -> langsung faq, tanpa panggilan LLM
    if any(k in q for k in FAQ_KEYWORDS):
        return "faq"

    # Lapis 3: sisanya diputuskan LLM
    try:
        return await _classify_with_llm(query)
    except Exception:
        return "faq"


async def handle_query(query: str) -> dict:
    """Dipanggil endpoint /ask: deteksi intent lalu rutekan."""
    intent = await detect_intent(query)

    if intent == "ticket_status":
        ticket_id = extract_ticket_id(query)
        data = get_ticket_status(ticket_id)
        return {"status": "success", "intent": "ticket_status", "data": data}

    elif intent == "faq":
        data = await answer_from_knowledge_base(query)
        return {"status": "success", "intent": "faq", "data": data}

    else:
        return {
            "status": "error",
            "intent": "unknown",
            "data": (
                "Maaf, saya hanya dapat membantu pertanyaan seputar IT dan HR "
                "(kebijakan, akses, perangkat) serta pengecekan status tiket. "
                "Coba tanyakan dengan cara lain atau hubungi tim IT Support."
            ),
        }