"""
get_gmail_token.py — run ONCE locally to get your Gmail refresh token.

Prerequisites:
  1. In Google Cloud Console, enable the Gmail API, configure the OAuth consent
     screen, and create an OAuth client of type "Desktop app".
  2. Download that client's JSON and save it next to this file as
     "client_secret.json".
  3. Install the helper libraries locally (NOT needed on the server):
         pip install google-auth-oauthlib

Then run:
        python get_gmail_token.py

A browser window opens — sign in as the Gmail account you want to send from
(e.g. digitallogichub1@gmail.com) and approve. If you see an
"unverified app" warning, click Advanced → "Go to ... (unsafe)" — that's fine,
it's your own app. The script then prints the three values to put in Railway:
        GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# Only the permission to SEND email — nothing else.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    # access_type=offline + prompt=consent forces Google to return a refresh
    # token (otherwise you only get a short-lived access token).
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    print("\n" + "=" * 60)
    print("  Add these to Railway → Variables:")
    print("=" * 60)
    print(f"GMAIL_CLIENT_ID={creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 60)
    if not creds.refresh_token:
        print("\n⚠️  No refresh token returned. Re-run after removing this app's")
        print("    access at https://myaccount.google.com/permissions, so Google")
        print("    shows the consent prompt again.")


if __name__ == "__main__":
    main()
