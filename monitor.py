import os
import smtplib
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# ==========================================
# ★書き換える場所：監視したいサイトのURLを入れてください
TARGET_URL = "https://www.cityheaven.net/tokyo/A1305/A130505/wakaba/A6ShopReservation/?girl_id=69234424"
# ==========================================

DATA_FILE = "last_text.txt"

# GitHub SecretsからYahoo!メール情報を自動取得（ここは書き換え不要）
YAHOO_ADDRESS = os.environ["YAHOO_ADDRESS"]
YAHOO_PASSWORD = os.environ["YAHOO_PASSWORD"]
TO_ADDRESS = os.environ["TO_ADDRESS"]


def get_page_text(url):
    response = requests.get(url, timeout=15)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
    return "\n".join(lines)


def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = YAHOO_ADDRESS
    msg["To"] = TO_ADDRESS

    # Yahoo!メールのSMTPサーバーに接続
    with smtplib.SMTP_SSL("smtp.mail.yahoo.co.jp", 465) as server:
        server.login(YAHOO_ADDRESS, YAHOO_PASSWORD)
        server.send_message(msg)


def main():
    current_text = get_page_text(TARGET_URL)

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            last_text = f.read()
    else:
        last_text = ""

    if current_text != last_text:
        print("変更を検知しました！Yahoo!メールを送信します。")
        send_email(
            subject="【Web更新通知】サイトの内容が変更されました",
            body=f"以下のサイトに更新がありました。\n\n{TARGET_URL}",
        )
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_text)
    else:
        print("変更はありませんでした。")


if __name__ == "__main__":
    main()
