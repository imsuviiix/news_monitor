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
    ws = _format_time(digest["window_start"])
    we = _format_time(digest["window_end"])
    header = (
        f"\U0001F5DE <b>{digest['date']} 사회면 야간 뉴스 브리핑</b>\n"
        f"(전일 {ws} ~ 당일 {we})\n"
        f'\U0001F517 <a href="{config.SITE_URL}">웹사이트에서 보기</a>\n\n'
    )

    messages = []
    current = header

    def append_line(line, outlet_title):
        """한 줄을 추가하되, 길이 제한을 넘으면 메시지를 끊고 언론사 제목을 다시 단다."""
        nonlocal current
        if len(current) + len(line) + 1 > MAX_MESSAGE_LEN and current.strip():
            messages.append(current.rstrip())
            current = f"{outlet_title} (계속)\n" if outlet_title else ""
        current += line + "\n"

    for outlet in digest["outlets"]:
        outlet_title = f"<b>■ {outlet['name']} ({outlet['count']})</b>"
        append_line(outlet_title, None)
        if outlet["articles"]:
            for article in outlet["articles"]:
                t = _format_time(article["published_at"])
                title = _escape_html(article["title"])
                append_line(f'· <a href="{article["link"]}">{title}</a> ({t})', outlet_title)
        else:
            append_line("수집된 기사가 없습니다.", outlet_title)
        current += "\n"

    if current.strip():
        messages.append(current.rstrip())
    return messages


def send_digest(digest):
    """digest를 텔레그램으로 전송한다. 성공하면 True, 실패/미설정이면 False."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print(
            "[ERROR] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID가 설정되지 않았습니다. "
            "GitHub Actions라면 저장소 시크릿 이름이 정확한지 확인하세요."
        )
        return False

    ok = True
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
            ok = False
    return ok


def main():
    """data/latest.json을 텔레그램으로 전송. 실패하면 종료 코드 1."""
    import json
    import os
    import sys

    path = os.path.join(config.DATA_DIR, "latest.json")
    if not os.path.exists(path):
        print("[ERROR] data/latest.json이 없습니다. 먼저 수집을 실행하세요.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        digest = json.load(f)
    if not send_digest(digest):
        sys.exit(1)
    print("[telegram] 전송 완료")


if __name__ == "__main__":
    main()
