import asyncio
from app.router import detect_intent, extract_ticket_id

queries = [
    "Berapa jatah cuti tahunan saya?",
    "Apa status TICKET-0005 saya?",
    "cek tiket ticket 7 dong",
    "Bagaimana status tiket saya?",
    "Gimana cara reset password VPN?",
    "Siapa presiden Indonesia?",
]

async def main():
    for q in queries:
        intent = await detect_intent(q)
        print(f"{intent:14} | {str(extract_ticket_id(q)):12} | {q}")

asyncio.run(main())