import os

from dotenv import load_dotenv

load_dotenv()

TIMEZONE = "Asia/Seoul"

# 수집 대상 시간대: 전일 23:00 ~ 당일 07:00
WINDOW_START_HOUR = 23
WINDOW_END_HOUR = 7

# 네이버뉴스 섹션 코드 (사회)
SOCIETY_SID = "102"

# 언론사별 네이버뉴스 oid 코드.
# NOTE: 이 값들은 공개 자료 조사를 바탕으로 작성되었으며, 이 개발 환경에서는
# news.naver.com 에 직접 접속해 실시간으로 검증하지 못했습니다.
# 배포 전 반드시 `python test_sources.py` 를 실행해 각 언론사가 정상적으로
# 수집되는지 확인하고, 0건이 계속 나오는 언론사는 oid 값을 다시 확인해주세요.
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
]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
