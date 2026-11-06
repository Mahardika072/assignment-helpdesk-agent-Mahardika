"""
Modul Tools: fungsi aksi yang dipanggil router untuk permintaan yang butuh
pengecekan data langsung (bukan retrieval semantik).
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_TICKETS_PATH = os.path.join(BASE_DIR, "data", "mock_tickets.csv")


def get_ticket_status(ticket_id: str | None) -> str:
    """Cari status tiket berdasarkan ticket_id di mock_tickets.csv."""
    if not ticket_id:
        return (
            "Nomor tiket tidak ditemukan dalam pertanyaan Anda. "
            "Mohon sertakan nomor tiket dengan format TICKET-XXXX, misalnya TICKET-0001."
        )

    ticket_id = ticket_id.strip().upper()

    try:
        df = pd.read_csv(MOCK_TICKETS_PATH)
    except FileNotFoundError:
        return "Maaf, data tiket sedang tidak dapat diakses. Silakan coba lagi nanti."

    match = df[df["ticket_id"].str.upper() == ticket_id]

    if match.empty:
        return (
            f"Tiket {ticket_id} tidak ditemukan. "
            "Mohon periksa kembali nomor tiket Anda."
        )

    row = match.iloc[0]
    return (
        f"Tiket {row['ticket_id']} ({row['subject']}) atas nama {row['employee_name']} "
        f"berstatus '{row['status']}'. Pembaruan terakhir: {row['last_update']}."
    )