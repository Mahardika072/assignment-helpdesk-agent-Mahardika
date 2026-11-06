# IT Helpdesk Assistant (RAG + Mini-Agent)

Backend API berbasis FastAPI yang menjawab pertanyaan karyawan dengan dua cara:
**RAG** untuk pertanyaan kebijakan/informasi, dan **tool call** untuk cek status tiket.
Dijalankan di dalam container Docker.

## 1. Problem Statement

**Objective:** Tim People & IT Operations menerima banyak pertanyaan repetitif dari karyawan.
Proyek ini membangun asisten AI internal yang menangani dua jenis permintaan dalam satu sistem.

**Dua jenis permintaan:**

| Jenis | Contoh | Ditangani oleh |
|---|---|---|
| Informasi/kebijakan (`faq`) | "Berapa jatah cuti tahunan?", "Bagaimana reset password VPN?" | RAG (semantic search + LLM) |
| Cek status tiket (`ticket_status`) | "Apa status TICKET-0005 saya?" | Tool call (pencarian data pasti) |

**Batasan dan asumsi:**
- Jawaban FAQ hanya berdasarkan knowledge base. Jika informasi tidak ada, sistem mengatakannya.
- Data tiket berasal dari file mock (`data/mock_tickets.csv`), bukan sistem tiket sungguhan.
- Format nomor tiket diasumsikan `TICKET-XXXX`.
- Sistem hanya melayani pertanyaan seputar IT/HR dan status tiket.

## 2. Desain Workflow

```
query masuk (POST /ask)
        |
        v
  intent detection (router.py)
        |
   +----+--------------------+
   |                         |
ticket_status               faq                    unknown
   |                         |                        |
ekstrak ticket_id      semantic search (FAISS)     pesan penolakan
   |                    + prompt + LLM                |
tools.py (CSV)               |                        |
   +-------------------------+------------------------+
                             |
                   response {status, intent, data}
```

**Kriteria intent (tiga lapis, dari yang paling pasti):**

1. **Regex nomor tiket.** Ada pola `TICKET-XXXX` (atau `tiket 5`) -> `ticket_status`.
2. **Kata kunci status.** Menyebut "tiket/ticket" bersama kata seperti "status" atau "progres" -> `ticket_status`
   (walau tanpa nomor; tool akan meminta nomor tiket).
3. **Kata kunci FAQ.** Memuat kata seperti "cuti", "password", "vpn", "laptop" -> `faq` tanpa memanggil LLM.
4. **Klasifikasi LLM** untuk sisanya: memilih `faq` atau `unknown`.

## 3. Struktur Project

```
app/main.py     FastAPI: endpoint /ask dan /health, error handling
app/router.py   intent detection, ekstraksi ticket_id, routing
app/rag.py      embedding, FAISS, semantic search, jawaban LLM
app/tools.py    pencarian status tiket
data/           knowledge base FAQ dan data mock tiket
Dockerfile
.env.example
```

## 4. Cara Menjalankan

Siapkan API key Gemini, lalu salin `.env.example` menjadi `.env` dan isi:
```
GEMINI_API_KEY=api_key_anda
GEN_MODEL=gemini-3.5-flash-lite
```
`.env` tidak di-commit ke repository.

### Lokal (tanpa Docker)
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Buka http://127.0.0.1:8000/docs

### Dengan Docker
```bash
docker build -t helpdesk-agent .
docker run --rm --env-file .env -p 8000:8000 helpdesk-agent
```
API key diteruskan lewat environment variable saat container dijalankan,
tidak disalin ke dalam image (`.env` ada di `.dockerignore`).
Buka http://127.0.0.1:8000/docs

### Contoh request
```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
  -d '{"query": "Apa status TICKET-0005 saya?"}'
```
Response: `{"status": "...", "intent": "...", "data": "..."}`

## 5. Hasil Pengujian

Diuji lewat endpoint `/ask`. Pengujian tahap akhir juga dikonfirmasi dari dalam container Docker
(query FAQ dan query tiket). Detail lengkap ada di `documentation/test_results.md`.

| # | Skenario | Query | Intent diharapkan | Intent aktual | Hasil |
|---|---|---|---|---|---|
| 1 | RAG | Berapa jatah cuti tahunan karyawan tetap? | faq | faq | Jawaban sesuai FAQ (12 hari, setelah masa kerja minimal) |
| 2 | RAG | Gimana cara reset password VPN? | faq | faq | Jawaban sesuai FAQ (portal self-service, atau hubungi IT Support) |
| 3 | Tool (ada) | Apa status TICKET-0005 saya? | ticket_status | ticket_status | Data tiket sesuai CSV (Diproses, 2026-08-27) |
| 4 | Tool (tidak ada) | Tolong cek TICKET-0099 | ticket_status | ticket_status | Pesan "tidak ditemukan", tanpa crash |
| 5 | Di luar cakupan | Siapa presiden Indonesia? | unknown | unknown | Penolakan sopan |
| 6 | Tambahan | Apakah kantor menyediakan parkir gratis? | faq | faq | LLM menyatakan informasi tidak ada di knowledge base |

**Observasi:**
- Router mengarahkan ke komponen yang tepat pada keenam skenario.
- Jalur tool tidak memakai LLM sehingga cepat dan hasilnya deterministik.
- Skenario 6 diklasifikasikan `faq` walau jawabannya tidak ada di knowledge base. Router hanya
  membedakan jenis permintaan; penolakan terjadi di tahap RAG berkat instruksi prompt.
- Pengujian awal sempat gagal dengan HTTP 503 karena kuota harian API gratis habis (error 429) dan
  kemudian karena model lama tidak tersedia (404). Error handling mengembalikan JSON terstruktur
  tanpa membuat aplikasi crash. Pengujian lalu diulang setelah model diganti.

## 6. Keterbatasan

- Kuota API gratis sangat kecil (puluhan permintaan generate per hari), sehingga pengujian harus
  dihemat. Nama model Gemini juga bisa berubah; karena itu model dibuat dapat diatur lewat `GEN_MODEL`.
- Aturan kata kunci FAQ bersifat kasar: kalimat di luar topik yang kebetulan memuat kata seperti
  "cuti" atau "akses" bisa salah diarahkan ke `faq`. Kata kunci menghemat panggilan LLM,
  tetapi mengorbankan akurasi pada kalimat yang tidak biasa.
- Daftar kata kunci dan ekstraksi ticket_id berbasis regex terbatas pada format `TICKET-XXXX`.
- Intent hanya dua (`faq` dan `ticket_status`). Permintaan campuran dalam satu kalimat
  (misalnya tanya kebijakan sekaligus cek tiket) hanya ditangani salah satunya.
- Data tiket adalah mock statis dari CSV, tidak ada autentikasi pemilik tiket.
- Index FAISS dibangun ulang setiap aplikasi start dan tersimpan di memori;
  belum ada penyimpanan index ke disk.
- Pengujian hanya 6 skenario sehingga belum mewakili semua variasi pertanyaan.