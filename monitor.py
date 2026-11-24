import os
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# ==========================================
# ★監視したいサイトのURL
TARGET_URL = "https://www.cityheaven.net/tokyo/A1305/A130505/wakaba/A6ShopReservation/?girl_id=69234424"
# ==========================================

DATA_FILE = "last_text.txt"

YAHOO_ADDRESS = os.environ["YAHOO_ADDRESS"]
YAHOO_PASSWORD = os.environ["YAHOO_PASSWORD"]
TO_ADDRESS = os.environ["TO_ADDRESS"]


def get_reservation_text(url):
    # ブラウザからのアクセスに見せかけ、年齢認証をスキップするための設定
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": url,
    }
    cookies = {
        "acheck": "1",
        "nenrei": "y",
    }

    session = requests.Session()
    res = session.get(url, headers=headers, cookies=cookies, timeout=15)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    # ページ内のインラインフレーム（iframe）を探す
    iframe_url = None
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        # 予約システムや女の子IDに関連するiframeを特定
        if "69234424" in src or "reserve" in src.lower() or "yoyaku" in src.lower() or "schedule" in src.lower():
            iframe_url = urljoin(url, src)
            break

    # 特定の条件で見つからない場合、広告以外の最初のiframeを取得
    if not iframe_url:
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if src and not any(ad in src for ad in ["google", "doubleclick", "twitter", "facebook", "line"]):
                iframe_url = urljoin(url, src)
                break

    # iframeが見つかった場合は、その中身のURLにアクセスしてテキストを取得
    if iframe_url:
        print(f"予約枠のURLを検出しました: {iframe_url}")
        res_frame = session.get(iframe_url, headers=headers, cookies=cookies, timeout=15)
        res_frame.encoding = res_frame.apparent_encoding
        target_soup = BeautifulSoup(res_frame.text, "html.parser")
    else:
        print("iframeが見つからなかったため、メイン領域を取得します。")
        # iframeがない構造だった場合はヘッダーやフッターを除外
        for tag in soup(["header", "footer", "nav", "script", "style"]):
            tag.decompose()
        target_soup = soup

    # 不要なスクリプトやスタイルタグを削除してテキストのみ抽出
    for tag in target_soup(["script", "style"]):
        tag.decompose()

    lines = [line.strip() for line in target_soup.get_text().splitlines() if line.strip()]
    return "\n".join(lines)


def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = YAHOO_ADDRESS
    msg["To"] = TO_ADDRESS

    with smtplib.SMTP_SSL("smtp.mail.yahoo.co.jp", 465) as server:
        server.login(YAHOO_ADDRESS, YAHOO_PASSWORD)
        server.send_message(msg)


def main():
    current_text = get_reservation_text(TARGET_URL)

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            last_text = f.read()
    else:
        last_text = ""

    if current_text != last_text:
        print("予約枠の変更を検知しました！Yahoo!メールを送信します。")
        send_email(
            subject="【予約枠更新】空き状況が変更されました",
            body=f"予約ページの空き状況に更新がありました。\n\n{TARGET_URL}\n\n--- 現在の取得内容（一部） ---\n{current_text[:500]}",
        )
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(current_text)
    else:
        print("予約枠に変更はありませんでした。")


if __name__ == "__main__":
    main()
