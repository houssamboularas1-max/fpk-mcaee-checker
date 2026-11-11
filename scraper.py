import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://www.fpk.ac.ma/"
KEYWORDS = ["mcaee", "temps aménagé", "temps amenage", "chimie analytique"]
DATA_FILE = "last_seen.txt"

SENDER_EMAIL = os.environ.get("GMAIL_USER")
APP_PASSWORD = os.environ.get("GMAIL_APP_PASS")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)


def fetch_announcements():
    try:
        response = requests.get(BASE_URL, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur Web: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    found_articles = []

    for a_tag in soup.find_all("a", href=True):
        title = a_tag.get_text(strip=True)
        link = urljoin(BASE_URL, a_tag["href"])

        if not title or len(title) < 5:
            continue

        title_lower = title.lower()
        if any(kw in title_lower for kw in KEYWORDS):
            found_articles.append({"title": title, "link": link})

    return found_articles


def load_last_seen():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    return set()


def save_last_seen(seen_links):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for link in seen_links:
            f.write(f"{link}\n")


def send_gmail_alert(new_items):
    if not SENDER_EMAIL or not APP_PASSWORD:
        print("Erreur: Les identifiants Gmail ne sont pas configurés.")
        return

    subject = f"🚨 إعلان جديد خاص بـ MCAEE ({len(new_items)})"

    body_content = "<h2>تمت إضافة إعلان جديد فـ موقع FPK:</h2><ul>"
    for item in new_items:
        body_content += (
            f"<li><b>{item['title']}</b><br><a href='{item['link']}'>رابط"
            " الإعلان</a></li><br>"
        )
    body_content += "</ul>"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("إيميل التنبيه تم إرساله بنجاح!")
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")


def main():
    print("جاري فحص موقع FPK...")
    articles = fetch_announcements()
    seen_links = load_last_seen()

    new_articles = [art for art in articles if art["link"] not in seen_links]

    if new_articles:
        print(f"تم إيجاد {len(new_articles)} إعلان جديد!")
        send_gmail_alert(new_articles)

        for art in new_articles:
            seen_links.add(art["link"])
        save_last_seen(seen_links)
    else:
        print("لا يوجد أي إعلان جديد حالياً.")


if __name__ == "__main__":
    main()
