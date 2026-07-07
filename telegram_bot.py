"""수집한 digest를 텔레그램으로 전송한다."""
from datetime import datetime

import requests

import config

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LEN = 3500  # 텔레그램 4096자 제한에 여유를 둔 값


def _escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_time(iso_str):
    return datetime.fromisoformat(iso_str).strftime("%H:%M")


def build_messages(digest):
    header = (
        f"\U0001F5DE <b>{digest['date']} 사회면 야간 뉴스 브리핑</b>\n"
        f"(전일 23:00 ~ 당일 07:00)\n\n"
    )

    blocks = []
    for outlet in digest["outlets"]:
        lines = [f"<b>■ {outlet['name']} ({outlet['count']})</b>"]
        if outlet["articles"]:
            for article in outlet["articles"]:
                t = _format_time(article["published_at"])
                title = _escape_html(article["title"])
                lines.append(f'· <a href="{article["link"]}">{title}</a> ({t})')
        else:
            lines.append("수집된 기사가 없습니다.")
        blocks.append("\n".join(lines))

    messages = []
    current = header
    for block in blocks:
        if len(current) + len(block) + 2 > MAX_MESSAGE_LEN and current.strip():
            messages.append(current.rstrip())
            current = ""
        current += block + "\n\n"
    if current.strip():
        messages.append(current.rstrip())
    return messages


def send_digest(digest):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[WARN] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID가 설정되지 않아 전송을 건너뜁니다.")
        return

    url = TELEGRAM_API_URL.format(token=config.TELEGRAM_BOT_TOKEN)
    for message in build_messages(digest):
        resp = requests.post(
            url,
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[ERROR] 텔레그램 전송 실패: {resp.status_code} {resp.text}")
