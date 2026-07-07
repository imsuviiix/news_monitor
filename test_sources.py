"""
언론사별 oid/스크레이핑 설정이 실제로 동작하는지 확인하는 진단 스크립트.

이 프로젝트는 네트워크가 제한된 개발 환경에서 작성되어 news.naver.com 에
실시간으로 접속해 검증하지 못했다. 실제 배포 전, 인터넷이 되는 환경에서
`python test_sources.py` 를 실행해 각 언론사가 정상적으로 수집되는지 확인할 것.
0건이 계속 나오는 언론사가 있다면 config.py의 oid 값을 다시 확인하거나,
scraper/naver_scraper.py의 CSS 선택자를 최신 페이지 구조에 맞게 수정해야 한다.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

import config
from scraper.naver_scraper import fetch_page, parse_list


def main():
    kst = ZoneInfo(config.TIMEZONE)
    today = datetime.now(kst).strftime("%Y%m%d")
    session = requests.Session()

    print(f"오늘 날짜({today}) 기준 각 언론사 사회면 1페이지 점검\n")
    for outlet in config.OUTLETS:
        try:
            html = fetch_page(session, outlet["oid"], today, 1)
            items = parse_list(html)
            status = "OK " if items else "빈결과"
            print(f"[{status}] {outlet['name']} (oid={outlet['oid']}) - {len(items)}건")
            for item in items[:2]:
                print(f"        - {item['title']} ({item['date_text']})")
        except Exception as exc:
            print(f"[FAIL] {outlet['name']} (oid={outlet['oid']}) - {exc}")


if __name__ == "__main__":
    main()
