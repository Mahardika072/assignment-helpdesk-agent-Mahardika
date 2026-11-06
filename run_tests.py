import json
import urllib.request
import urllib.error

URL = "http://127.0.0.1:8000/ask"

# (label, query, intent yang diharapkan)
SCENARIOS = [
    ("RAG #1", "Berapa jatah cuti tahunan karyawan tetap?", "faq"),
    ("RAG #2", "Gimana cara reset password VPN?", "faq"),
    ("Tool #1 (ada)", "Apa status TICKET-0005 saya?", "ticket_status"),
    ("Tool #2 (tidak ada)", "Tolong cek TICKET-0099", "ticket_status"),
    ("Di luar cakupan", "Siapa presiden Indonesia?", "unknown"),
    ("Tambahan: tidak ada di KB", "Apakah kantor menyediakan parkir gratis?", "faq"),
]


def ask(query):
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


lines = ["# Hasil Pengujian Endpoint /ask\n"]
for label, query, expected in SCENARIOS:
    code, result = ask(query)
    actual = result.get("intent")
    ok = "BENAR" if actual == expected else "SALAH"
    print(f"[{ok}] {label}: harapan={expected}, aktual={actual}, HTTP={code}")
    print("   ", result.get("data"), "\n")
    lines += [
        f"## {label}",
        f"- **Query:** {query}",
        f"- **Intent diharapkan:** {expected}",
        f"- **Intent aktual:** {actual} ({ok})",
        f"- **HTTP status:** {code}",
        f"- **Response:** {result.get('data')}",
        "",
    ]

with open("documentation/test_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Tersimpan di documentation/test_results.md")