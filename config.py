import os

from dotenv import load_dotenv

load_dotenv()

TIMEZONE = "Asia/Seoul"

# 수집 대상 시간대: 전일 19:00 ~ 당일 07:00
WINDOW_START_HOUR = 19
WINDOW_END_HOUR = 7
WINDOW_END_MINUTE = 0

# 텔레그램 메시지에 포함할 웹사이트 주소
SITE_URL = os.getenv("SITE_URL", "https://imsuviiix.github.io/news_monitor/")

# 네이버뉴스 섹션 코드 (사회)
SOCIETY_SID = "102"

# 언론사별 네이버뉴스 oid 코드. (2026-07 기준 10개사 모두 실수집 검증 완료)
# 수집이 안 되는 언론사가 생기면 `python test_sources.py` 로 점검하세요.
OUTLETS = [
    {"key": "chosun", "name": "조선일보", "oid": "023"},
    {"key": "joongang", "name": "중앙일보", "oid": "025"},
    {"key": "donga", "name": "동아일보", "oid": "020"},
    {"key": "hani", "name": "한겨레", "oid": "028"},
    {"key": "khan", "name": "경향신문", "oid": "032"},
    {"key": "hankookilbo", "name": "한국일보", "oid": "469"},
    {"key": "kmib", "name": "국민일보", "oid": "005"},
    {"key": "munhwa", "name": "문화일보", "oid": "021"},
    {"key": "mk", "name": "매일경제", "oid": "009"},
    {"key": "hankyung", "name": "한국경제", "oid": "015"},
    {"key": "yna", "name": "연합뉴스", "oid": "001"},
    {"key": "newsis", "name": "뉴시스", "oid": "003"},
    {"key": "news1", "name": "뉴스1", "oid": "421"},
]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
