"""
Modul RAG: embedding knowledge base, simpan ke FAISS, semantic search,
lalu jawab dengan LLM berdasarkan hasil retrieval.
"""

import asyncio
import os

import faiss
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

EMBED_MODEL = "gemini-embedding-001"
GEN_MODEL = os.environ.get("GEN_MODEL", "gemini-2.5-flash")
EMBED_DIM = 768

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "it_helpdesk_knowledge_base.csv")

# Disimpan sekali, dipakai ulang di setiap request
_index = None
_df = None


def _embed(texts: list[str], task_type: str) -> np.ndarray:
    """Ubah daftar teks menjadi matriks vektor ternormalisasi."""
    vecs = []
    for i in range(0, len(texts), 50):
        res = _client.models.embed_content(
            model=EMBED_MODEL,
            contents=texts[i:i + 50],
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBED_DIM,
            ),
        )
        vecs.extend(e.values for e in res.embeddings)
    arr = np.array(vecs, dtype="float32")
    faiss.normalize_L2(arr)
    return arr


def build_index():
    """Muat knowledge base, embed tiap entri, simpan ke index FAISS."""
    global _index, _df

    df = pd.read_csv(KNOWLEDGE_BASE_PATH)
    df["doc_text"] = df.apply(
        lambda r: (
            f"Kategori: {r['category']}\n"
            f"Pertanyaan: {r['question']}\n"
            f"Jawaban: {r['answer']}"
        ),
        axis=1,
    )

    vectors = _embed(df["doc_text"].tolist(), "RETRIEVAL_DOCUMENT")
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(vectors)
    assert index.ntotal == len(df), "Jumlah vektor tidak sama dengan jumlah entri"

    _df = df
    _index = index


def _ensure_index():
    """Bangun index hanya jika belum ada (lazy loading)."""
    if _index is None:
        build_index()


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    """Cari top_k entri FAQ paling relevan beserta skor kemiripan."""
    _ensure_index()
    q_vec = _embed([query], "RETRIEVAL_QUERY")
    scores, ids = _index.search(q_vec, top_k)

    results = []
    for score, i in zip(scores[0], ids[0]):
        row = _df.iloc[i]
        results.append({
            "faq_id": int(row["faq_id"]),
            "score": float(score),
            "category": row["category"],
            "question": row["question"],
            "answer": row["answer"],
        })
    return results


def _build_prompt(query: str, results: list[dict]) -> str:
    context = "\n\n".join(
        f"[FAQ {n + 1}] Kategori: {r['category']}\n"
        f"Pertanyaan: {r['question']}\n"
        f"Jawaban: {r['answer']}"
        for n, r in enumerate(results)
    )
    return f"""# Persona
Kamu adalah asisten IT Helpdesk internal perusahaan yang ramah, sopan, dan ringkas.

# Task
Jawab pertanyaan karyawan HANYA berdasarkan bagian Context di bawah.
Jangan memakai pengetahuan umum dan jangan mengarang informasi.
Jika Context tidak memuat jawaban, katakan dengan jujur bahwa informasi tersebut
tidak tersedia di knowledge base, lalu sarankan menghubungi tim IT Support atau HR.

# Context
{context}

# Format
- Gunakan Bahasa Indonesia dengan nada ramah dan profesional.
- Maksimal 3-4 kalimat. Gunakan poin jika ada langkah-langkah.
- Jangan menyebut kata "Context" atau nomor FAQ dalam jawaban.

# Pertanyaan Karyawan
{query}

# Jawaban"""


async def answer_from_knowledge_base(query: str) -> str:
    """Dipanggil router ketika intent = 'faq'."""
    # semantic_search bersifat blocking, jadi dijalankan di thread terpisah
    results = await asyncio.to_thread(semantic_search, query)
    prompt = _build_prompt(query, results)

    response = await _client.aio.models.generate_content(
        model=GEN_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return response.text