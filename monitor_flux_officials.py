import requests
from bs4 import BeautifulSoup
import smtplib
import os
import json
from email.message import EmailMessage
from datetime import datetime

TARGET_URL = "https://www.flux.live/news/all/"
CHECK_KEYWORD = "The Officials"
STATE_FILE = "flux_state.json"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = SMTP_USER
EMAIL_TO = os.getenv("EMAIL_TO")

def send_email(subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.send_message(msg)
    s.quit()

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"last_seen": ""}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))

def find_latest_official():
    r = requests.get(TARGET_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    candidates = []
    for a in soup.find_all(["a", "article"]):
        text = (a.get_text(" ", strip=True) or "").strip()
        href = a.get("href") or ""
        if CHECK_KEYWORD.lower() in text.lower():
            candidates.append({"title": text, "href": href})

    for c in candidates:
        if c["href"] and c["href"].startswith("/"):
            c["href"] = "https://www.flux.live" + c["href"]

    return candidates[0] if candidates else None

def main():
    state = load_state()
    latest = find_latest_official()
    if not latest:
        print("No officials found at check.")
        return

    identifier = latest.get("href") or latest.get("title")

    if identifier != state.get("last_seen"):
        subject = f"New 'The Officials' Report: {latest.get('title')}"
        body = f"Title: {latest.get('title')}\nLink: {latest.get('href')}\nChecked on: {datetime.utcnow()}"

        send_email(subject, body)
        state["last_seen"] = identifier
        save_state(state)
        print("Email sent!")
    else:
        print("No new item.")

if __name__ == "__main__":
    main()
