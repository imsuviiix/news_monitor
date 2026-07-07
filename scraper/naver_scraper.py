"""
네이버뉴스 언론사별 날짜 아카이브(사회 섹션)에서 기사 목록을 수집하는 스크레이퍼.

네이버뉴스는 언론사(oid)와 날짜(date)를 지정하면 해당 언론사가 그날 송고한
기사를 섹션별로 최신순 페이지 목록으로 보여준다. 다만 목록에는 발행 시각이
"42분전", "8시간전", "1일전" 같은 상대 표기로만 나오기 때문에,
1) 상대 시각으로 수집 구간에 걸칠 가능성이 있는 후보를 고른 뒤
2) 각 기사 본문 페이지의 data-date-time 속성에서 정확한 발행 시각을 읽어
   "전일 23:00 ~ 당일 07:30" 구간을 정밀하게 필터링한다.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

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
REQUEST_SLEEP_SEC = 0.25
REQUEST_TIMEOUT = 10
ARTICLE_FETCH_WORKERS = 8

_ABS_DATE_RE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})\.?\s*(?:(오전|오후)\s*(\d{1,2}):(\d{2}))?")
_REL_RE = re.compile(r"(\d+)\s*(분|시간|일)전")
_ARTICLE_TIME_RE = re.compile(r'data-date-time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"')


def parse_date_text(text, now):
    """
    목록의 시각 표기를 (하한, 상한) naive datetime 구간으로 변환한다.
    상대 표기("8시간전")는 표기 단위만큼의 불확실성이 있으므로 구간으로 다룬다.
    해석 불가능하면 (None, None).
    """
    text = (text or "").strip()
    if not text:
        return None, None
    if text in ("지금", "방금", "방금전"):
        return now - timedelta(minutes=2), now

    m = _REL_RE.search(text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"분": timedelta(minutes=1), "시간": timedelta(hours=1), "일": timedelta(days=1)}[unit]
        upper = now - n * delta
        return upper - delta, upper

    m = _ABS_DATE_RE.search(text)
    if m:
        year, month, day, ampm, hour, minute = m.groups()
        if ampm:
            hour = int(hour)
            if ampm == "오후" and hour != 12:
                hour += 12
            if ampm == "오전" and hour == 12:
                hour = 0
            exact = datetime(int(year), int(month), int(day), hour, int(minute))
            return exact, exact
        day_start = datetime(int(year), int(month), int(day))
        return day_start, day_start + timedelta(days=1)

    return None, None


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
    """기사 목록 HTML에서 (제목, 링크, 시각표기) 목록을 추출한다."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("ul.type06_headline li, ul.type06 li"):
        title, link = None, None
        for dt in li.select("dt"):
            if "photo" in (dt.get("class") or []):
                continue
            a = dt.find("a")
            text = a.get_text(strip=True) if a else ""
            if a and text:
                title, link = text, a.get("href")
                break
        if not title or not link:
            continue
        date_span = li.select_one("span.date")
        date_text = date_span.get_text(strip=True) if date_span else ""
        items.append({"title": title, "link": link, "date_text": date_text})
    return items


def fetch_article_time(session, link):
    """기사 본문 페이지에서 정확한 발행 시각을 읽는다. 실패하면 None."""
    try:
        resp = session.get(link, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        m = _ARTICLE_TIME_RE.search(resp.text)
        if m:
            return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return None


def _collect_candidates(session, oid, date_str, ws, we, now):
    """하루치 아카이브를 최신순으로 넘기며 수집 구간에 걸칠 가능성이 있는 기사를 모은다."""
    candidates = {}
    prev_links = None
    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(session, oid, date_str, page)
        items = parse_list(html)
        if not items:
            break

        links = {item["link"] for item in items}
        if links == prev_links:  # 마지막 페이지를 넘어가면 같은 페이지가 반복됨
            break
        prev_links = links

        page_all_older = True
        for item in items:
            lower, upper = parse_date_text(item["date_text"], now)
            if lower is None:
                continue
            if upper >= ws:
                page_all_older = False
                if lower <= we:
                    candidates[item["link"]] = item
        if page_all_older:
            break
        time.sleep(REQUEST_SLEEP_SEC)
    return candidates


def fetch_outlet_window(session, oid, window_start, window_end, now=None):
    """
    window_start(전일 23:00) ~ window_end(당일 07:30) 사이에 발행된 기사를 수집한다.
    window_start / window_end는 tz-aware datetime이어야 한다.
    """
    ws = window_start.replace(tzinfo=None)
    we = window_end.replace(tzinfo=None)
    if now is None:
        now = datetime.now(window_end.tzinfo).replace(tzinfo=None)

    candidates = {}
    for date_str in {window_start.strftime("%Y%m%d"), window_end.strftime("%Y%m%d")}:
        candidates.update(_collect_candidates(session, oid, date_str, ws, we, now))

    # 후보 기사들의 정확한 발행 시각을 병렬로 조회해 구간 필터링
    results = []
    with ThreadPoolExecutor(max_workers=ARTICLE_FETCH_WORKERS) as pool:
        exact_times = pool.map(lambda it: fetch_article_time(session, it["link"]), candidates.values())
        for item, exact in zip(candidates.values(), exact_times):
            if exact and ws <= exact < we:
                results.append({"title": item["title"], "link": item["link"], "published_at": exact})

    results.sort(key=lambda it: it["published_at"])
    return results
