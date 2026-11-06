# Hasil Pengujian Endpoint /ask

## RAG #1
- **Query:** Berapa jatah cuti tahunan karyawan tetap?
- **Intent diharapkan:** faq
- **Intent aktual:** faq (BENAR)
- **HTTP status:** 200
- **Response:** Halo! Karyawan tetap mendapatkan jatah 12 hari cuti tahunan. Jatah tersebut baru dapat diambil setelah masa kerja minimal 3 bulan. Jika ada pertanyaan lain seputar cuti, silakan tanyakan ya!

## RAG #2
- **Query:** Gimana cara reset password VPN?
- **Intent diharapkan:** faq
- **Intent aktual:** faq (BENAR)
- **HTTP status:** 200
- **Response:** Halo! Untuk melakukan reset password VPN, Anda dapat melakukannya secara mandiri melalui portal self-service IT. Silakan hubungi tim IT Support jika akun Anda mengalami kendala terkunci. Semoga membantu!

## Tool #1 (ada)
- **Query:** Apa status TICKET-0005 saya?
- **Intent diharapkan:** ticket_status
- **Intent aktual:** ticket_status (BENAR)
- **HTTP status:** 200
- **Response:** Tiket TICKET-0005 (Reset password VPN gagal terus) atas nama Dedi Kurniawan berstatus 'Diproses'. Pembaruan terakhir: 2026-08-27.

## Tool #2 (tidak ada)
- **Query:** Tolong cek TICKET-0099
- **Intent diharapkan:** ticket_status
- **Intent aktual:** ticket_status (BENAR)
- **HTTP status:** 200
- **Response:** Tiket TICKET-0099 tidak ditemukan. Mohon periksa kembali nomor tiket Anda.

## Di luar cakupan
- **Query:** Siapa presiden Indonesia?
- **Intent diharapkan:** unknown
- **Intent aktual:** unknown (BENAR)
- **HTTP status:** 200
- **Response:** Maaf, saya hanya dapat membantu pertanyaan seputar IT dan HR (kebijakan, akses, perangkat) serta pengecekan status tiket. Coba tanyakan dengan cara lain atau hubungi tim IT Support.

## Tambahan: tidak ada di KB
- **Query:** Apakah kantor menyediakan parkir gratis?
- **Intent diharapkan:** faq
- **Intent aktual:** faq (BENAR)
- **HTTP status:** 200
- **Response:** Halo! Mohon maaf, informasi mengenai fasilitas parkir gratis tidak tersedia di *knowledge base* kami. Untuk informasi lebih lanjut, silakan menghubungi tim IT Support atau HR. Terima kasih!
