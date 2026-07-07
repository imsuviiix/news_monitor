"""
네이버뉴스 언론사별 날짜 아카이브(사회 섹션)에서 기사 목록을 수집하는 스크레이퍼.

네이버뉴스는 언론사(oid)와 날짜(date)를 지정하면 해당 언론사가 그날 송고한
기사를 섹션별로 최신순 페이지 목록으로 보여준다. 이 특성을 이용해
"전일 23:00 ~ 당일 07:00" 구간에 해당하는 기사만 골라낸다.
"""
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import config

BASE_URL = "https://news.naver.com/main/list.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://news.naver.com/",
}

MAX_PAGES = 30
REQUEST_SLEEP_SEC = 0.35
REQUEST_TIMEOUT = 10

_DATE_RE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})\.?\s*(오전|오후)\s*(\d{1,2}):(\d{2})")


def parse_naver_datetime(text):
    """'2024.01.02 오전 6:12' 형태의 문자열을 naive datetime으로 변환."""
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    year, month, day, ampm, hour, minute = match.groups()
    hour = int(hour)
    if ampm == "오후" and hour != 12:
        hour += 12
    if ampm == "오전" and hour == 12:
        hour = 0
    return datetime(int(year), int(month), int(day), hour, int(minute))


def fetch_page(session, oid, date_str, page):
    """언론사(oid)의 특정 날짜(date_str, YYYYMMDD) 사회면 목록 page 페이지를 가져온다."""
    params = {
        "mode": "LSD",
        "mid": "sec",
        "sid1": config.SOCIETY_SID,
        "oid": oid,
        "date": date_str,
        "page": page,
    }
    resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    if not resp.encoding or resp.encoding.lower() in ("iso-8859-1",):
        resp.encoding = resp.apparent_encoding
    return resp.text


def parse_list(html):
    """기사 목록 HTML에서 (제목, 링크, 발행시각) 목록을 추출한다."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("ul.type06_headline li, ul.type06 li"):
        title, link = None, None
        for dt in li.select("dt"):
            a = dt.find("a")
            text = a.get_text(strip=True) if a else ""
            if a and text:
                title, link = text, a.get("href")
                break
        if not title or not link:
            continue
        date_span = li.select_one("span.date")
        published_at = parse_naver_datetime(date_span.get_text(strip=True)) if date_span else None
        items.append({"title": title, "link": link, "published_at": published_at})
    return items


def fetch_day_articles(session, oid, date_str, keep_fn, stop_fn=None):
    """
    하루치 목록을 최신순으로 페이지네이션하며 keep_fn을 만족하는 기사만 수집.
    stop_fn이 True를 반환하는 시점부터는(그 이전 기사는 더 이상 조건에 맞지 않으므로) 중단한다.
    """
    collected = []
    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(session, oid, date_str, page)
        items = parse_list(html)
        if not items:
            break

        reached_stop = False
        for item in items:
            if item["published_at"] is None:
                continue
            if stop_fn and stop_fn(item):
                reached_stop = True
                break
            if keep_fn(item):
                collected.append(item)

        if reached_stop:
            break
        time.sleep(REQUEST_SLEEP_SEC)
    return collected


def fetch_outlet_window(session, oid, window_start, window_end):
    """
    window_start(전일 23:00) ~ window_end(당일 07:00) 사이에 발행된 기사를 수집한다.
    window_start / window_end는 tz-aware datetime이어야 한다.
    """
    date_prev = window_start.strftime("%Y%m%d")
    date_today = window_end.strftime("%Y%m%d")
    ws_naive = window_start.replace(tzinfo=None)
    we_naive = window_end.replace(tzinfo=None)

    prev_items = fetch_day_articles(
        session,
        oid,
        date_prev,
        keep_fn=lambda it: it["published_at"] >= ws_naive,
        stop_fn=lambda it: it["published_at"] < ws_naive,
    )
    today_items = fetch_day_articles(
        session,
        oid,
        date_today,
        keep_fn=lambda it: it["published_at"] < we_naive,
    )

    all_items = prev_items + today_items
    all_items.sort(key=lambda it: it["published_at"])
    return all_items
