import base64
from googleapiclient.discovery import build

def get_latest_email(credentials):
    service = build("gmail", "v1", credentials=credentials)

    results = service.users().messages().list(
        userId="me",
        maxResults=1,
        labelIds=["INBOX"]
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return None

    msg = service.users().messages().get(
        userId="me",
        id=messages[0]["id"],
        format="full"  # ensures payload + snippet available
    ).execute()

    payload = msg["payload"]
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")

    # Try to get plain text body, fallback to snippet
    body = ""
    parts = payload.get("parts", [])
    if parts:
        for part in parts:
            mime = part.get("mimeType")
            data = part.get("body", {}).get("data")
            if mime == "text/plain" and data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                break

    if not body:
        body = msg.get("snippet", "")

    return {
        "subject": subject,
        "sender": sender,
        "body": body
    }
