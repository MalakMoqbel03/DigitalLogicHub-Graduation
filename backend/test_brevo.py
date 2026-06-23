"""
test_brevo.py — quick check that your Brevo API key actually works.

Run from the backend/ folder (with your venv active so httpx is available):

    python test_brevo.py                     # sends to EMAIL_FROM (yourself)
    python test_brevo.py someone@example.com # sends to a specific address

It reads BREVO_API_KEY and EMAIL_FROM from your .env and reports exactly what
Brevo says — no Railway, no deploy involved. This isolates whether the KEY is
valid, separate from any Railway configuration issue.
"""

import sys
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

key = os.getenv("BREVO_API_KEY", "")
email_from = os.getenv("EMAIL_FROM", "")

print("— Brevo key sanity check —")
print(f"BREVO_API_KEY present : {bool(key)}")
print(f"  starts with 'xkeysib-': {key.startswith('xkeysib-')}")
print(f"  length               : {len(key)}  (a real key is ~60+ chars)")
if key != key.strip():
    print("  ⚠️  WARNING: the key has leading/trailing whitespace!")
if key.startswith(('"', "'")) or key.endswith(('"', "'")):
    print("  ⚠️  WARNING: the key has surrounding quotes — remove them!")
print(f"EMAIL_FROM            : {email_from!r}")
print()

if not key:
    print("No BREVO_API_KEY in .env. Add it and re-run.")
    sys.exit(1)

to_email = sys.argv[1] if len(sys.argv) > 1 else email_from
if not to_email:
    print("No recipient. Pass one as an argument or set EMAIL_FROM.")
    sys.exit(1)

payload = {
    "sender": {"name": "DigitalLogicHub", "email": email_from},
    "to": [{"email": to_email}],
    "subject": "DigitalLogicHub — Brevo test",
    "textContent": "If you can read this, your Brevo key works. ✅",
}
headers = {"api-key": key, "Content-Type": "application/json", "accept": "application/json"}

resp = httpx.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=15)
print(f"Brevo HTTP status: {resp.status_code}")
print(f"Brevo response   : {resp.text}")
print()
if resp.status_code in (200, 201):
    print(f"✅ SUCCESS — check {to_email} (and spam). Your key is valid.")
elif resp.status_code == 401:
    print("❌ 'Key not found' / unauthorized → the KEY itself is wrong. "
          "Generate a NEW one in Brevo → Settings → SMTP & API → API Keys "
          "(it must start with xkeysib-), copy it fully, and update .env + Railway.")
else:
    print("❌ Something else — read the Brevo response above (often an "
          "unverified sender in EMAIL_FROM).")
