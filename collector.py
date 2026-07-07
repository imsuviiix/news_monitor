"""언론사별 사회면 야간 뉴스(전일 19:00~당일 07:00)를 수집해 digest(dict)로 만든다."""
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

import config
from scraper.naver_scraper import fetch_outlet_window

KST = ZoneInfo(config.TIMEZONE)


def get_window(reference_time=None):
    """reference_time(기본: 현재 KST) 기준으로 (window_start, window_end)를 계산한다."""
    now = reference_time or datetime.now(KST)
    today = now.date()
    window_end = datetime(
        today.year, today.month, today.day,
        config.WINDOW_END_HOUR, getattr(config, "WINDOW_END_MINUTE", 0), tzinfo=KST,
    )
    yesterday = today - timedelta(days=1)
    window_start = datetime(
        yesterday.year, yesterday.month, yesterday.day, config.WINDOW_START_HOUR, 0, tzinfo=KST
    )
    return window_start, window_end


def collect_all(reference_time=None):
    window_start, window_end = get_window(reference_time)
    session = requests.Session()

    outlets_result = []
    for outlet in config.OUTLETS:
        try:
            items = fetch_outlet_window(session, outlet["oid"], window_start, window_end)
        except Exception as exc:  # 언론사 하나가 실패해도 나머지는 계속 수집
            items = []
            print(f"[WARN] {outlet['name']} 수집 실패: {exc}")

        articles = [
            {
                "title": item["title"],
                "link": item["link"],
                "published_at": item["published_at"].isoformat(),
            }
            for item in items
        ]
        outlets_result.append(
            {
                "key": outlet["key"],
                "name": outlet["name"],
                "count": len(articles),
                "articles": articles,
            }
        )

    return {
        "generated_at": datetime.now(KST).isoformat(),
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "date": window_end.date().isoformat(),
        "outlets": outlets_result,
    }


def save_digest(digest):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    dated_path = os.path.join(config.DATA_DIR, f"digest_{digest['date']}.json")
    with open(dated_path, "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)

    latest_path = os.path.join(config.DATA_DIR, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)

    return dated_path
