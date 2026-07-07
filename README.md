# 사회면 야간 뉴스 브리핑

조선일보 · 중앙일보 · 동아일보 · 한겨레 · 경향신문 · 한국일보 · 국민일보 · 문화일보 · 매일경제 · 한국경제,
10개 언론사의 **사회면**에서 **전일 23:00 ~ 당일 07:00** 사이에 올라온 뉴스 헤드라인만 모아
1) 웹사이트에서 보여주고 2) 텔레그램으로 전송하는 프로젝트입니다.

## 동작 방식

- 각 언론사는 네이버뉴스에 언론사 코드(`oid`)로 등록되어 있고, 네이버뉴스는
  `언론사 + 날짜 + 섹션(사회=102)` 조합으로 그날 그 언론사가 송고한 기사 목록(발행 시각 포함)을
  볼 수 있는 페이지를 제공합니다. `scraper/naver_scraper.py`가 이 페이지를 읽어
  전일 23:00~당일 07:00 구간에 해당하는 기사만 걸러냅니다.
- `collector.py`가 10개 언론사를 순회하며 수집한 결과를 `data/digest_YYYY-MM-DD.json`,
  `data/latest.json`으로 저장합니다.
- `app.py`(Flask)가 저장된 digest를 웹페이지로 보여줍니다.
- `telegram_bot.py`가 digest를 언론사별로 정리해 텔레그램으로 전송합니다.
- `run_daily.py`가 위 과정을 한 번에 실행하는 진입점이며, 매일 아침 7시 이후 cron/스케줄러로
  실행하는 것을 전제로 만들어졌습니다.

## ⚠️ 실행 전 꼭 확인할 것

이 코드는 news.naver.com 접속이 차단된 개발 환경에서 공개 자료 조사만으로 작성되었고,
**실시간으로 접속 테스트를 하지 못했습니다.** 특히 아래 두 가지는 배포 전에 반드시 확인하세요.

1. `config.py`의 `OUTLETS` 목록에 있는 `oid` 값이 실제 언론사와 맞는지
2. `scraper/naver_scraper.py`의 CSS 선택자(`ul.type06_headline`, `ul.type06`, `span.date` 등)가
   최신 네이버뉴스 페이지 구조와 맞는지

인터넷이 되는 환경에서 아래 명령으로 바로 점검할 수 있습니다.

```bash
python test_sources.py
```

각 언론사별로 오늘자 사회면 1페이지를 읽어 몇 건이 잡히는지 보여줍니다. 특정 언론사가 계속
0건이거나 FAIL이 뜨면 `config.py`의 `oid`를 다시 찾아 수정하거나, 셀렉터를 조정해주세요.

## 설치

```bash
python -m venv venv
source venv/bin/activate  # Windows는 venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` 파일을 열어 텔레그램 봇 토큰과 chat id를 입력합니다.

### 텔레그램 봇 준비

1. 텔레그램에서 `@BotFather`를 찾아 `/newbot`으로 봇을 생성하고 토큰을 받습니다. → `TELEGRAM_BOT_TOKEN`
2. 만든 봇과 대화를 시작(아무 메시지나 전송)하거나, 메시지를 받을 그룹에 봇을 초대합니다.
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` 를 브라우저로 열어 `chat.id` 값을 확인합니다.
   (그룹은 보통 음수 id) → `TELEGRAM_CHAT_ID`

## 사용법

### 1) 수동으로 한 번 실행 (수집 + 저장 + 텔레그램 전송)

```bash
python run_daily.py
```

### 2) 웹사이트로 확인

```bash
python app.py
```

브라우저에서 http://localhost:5000 접속. 언론사별 카드로 헤드라인/시간이 표시되고,
상단 날짜 탭에서 과거 digest도 볼 수 있습니다.

### 3) 매일 아침 자동 실행

**cron 사용 (Linux/macOS 서버):**

```
5 7 * * * cd /path/to/news_monitor && /path/to/venv/bin/python run_daily.py >> run.log 2>&1
```

**상시 프로세스로 실행 (systemd 등에 올려두는 경우):**

```bash
python scheduler.py
```

매일 07:05(KST)에 자동으로 `run_daily.py`와 동일한 작업을 수행합니다.

## 시간 구간 로직

"전일 23:00 ~ 당일 07:00"은 스크립트를 **실행하는 시점의 당일 날짜** 기준으로 계산됩니다
(`collector.get_window`). 예를 들어 7월 7일 07:05에 실행하면 7월 6일 23:00 ~ 7월 7일 07:00
구간의 기사를 수집합니다. 따라서 매일 07:00 이후(권장: 07:05)에 실행해야 그날의 창이
온전히 채워집니다.

## 디렉터리 구조

```
config.py              언론사 목록(oid), 시간 구간, 텔레그램 설정
scraper/naver_scraper.py  네이버뉴스 기반 스크레이핑 핵심 로직
collector.py            전체 언론사 수집 오케스트레이션 + JSON 저장
telegram_bot.py          digest -> 텔레그램 메시지 포맷/전송
app.py                   Flask 웹사이트
templates/, static/      웹사이트 템플릿/스타일
run_daily.py             수집+저장+전송 진입점 (cron에서 호출)
scheduler.py             상시 프로세스로 매일 07:05 자동 실행하고 싶을 때
test_sources.py          언론사별 수집 상태 점검 스크립트
data/                    수집 결과 JSON 저장 위치 (gitignore)
```

## 알려진 한계

- 네이버뉴스 페이지 구조가 바뀌면 `scraper/naver_scraper.py`의 CSS 선택자를 손봐야 합니다.
- 언론사가 네이버뉴스에 송고하지 않은 기사(자사 홈페이지 단독 게재 등)는 수집되지 않습니다.
- 네이버 측의 과도한 요청 차단을 피하기 위해 요청 사이에 약간의 지연을 두었습니다. 언론사가
  많아 전체 수집에 1~2분 정도 걸릴 수 있습니다.
