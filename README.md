# 사회면 야간 뉴스 브리핑

조선일보 · 중앙일보 · 동아일보 · 한겨레 · 경향신문 · 한국일보 · 국민일보 · 문화일보 · 매일경제 · 한국경제,
10개 언론사의 **사회면**에서 **전일 23:00 ~ 당일 07:30** 사이에 올라온 뉴스 헤드라인만 모아
1) 웹사이트에서 보여주고 2) 텔레그램으로 전송하는 프로젝트입니다.

## 동작 방식

- 각 언론사는 네이버뉴스에 언론사 코드(`oid`)로 등록되어 있고, 네이버뉴스는
  `언론사 + 날짜 + 섹션(사회=102)` 조합으로 그날 그 언론사가 송고한 기사 목록(발행 시각 포함)을
  볼 수 있는 페이지를 제공합니다. `scraper/naver_scraper.py`가 이 페이지를 읽어
  전일 23:00~당일 07:30 구간에 해당하는 기사만 걸러냅니다.
- `collector.py`가 10개 언론사를 순회하며 수집한 결과를 `data/digest_YYYY-MM-DD.json`,
  `data/latest.json`으로 저장합니다.
- `app.py`(Flask)가 저장된 digest를 웹페이지로 보여줍니다.
- `telegram_bot.py`가 digest를 언론사별로 정리해 텔레그램으로 전송합니다.
- `run_daily.py`가 위 과정을 한 번에 실행하는 진입점이며, 매일 아침 7시 30분 이후 cron/스케줄러로
  실행하는 것을 전제로 만들어졌습니다.

## 🚀 운영 구성: GitHub Actions + GitHub Pages (서버 불필요, 무료)

`.github/workflows/daily-digest.yml` 워크플로가 **매일 07:35(KST)** 에 자동으로:

1. 10개 언론사 야간 사회면 뉴스를 수집하고
2. 텔레그램으로 전송하고
3. 수집 결과(`data/digest_*.json`)를 저장소에 커밋하고 (과거 이력 보존)
4. 정적 사이트를 빌드해 GitHub Pages로 배포합니다.

### 최초 1회 설정 (GitHub 저장소에서)

1. **Settings → Secrets and variables → Actions → New repository secret** 으로 두 개 등록:
   - `TELEGRAM_BOT_TOKEN` — BotFather에게 받은 봇 토큰
   - `TELEGRAM_CHAT_ID` — 메시지 받을 chat id
2. **Settings → Pages → Source** 를 **"GitHub Actions"** 로 설정
3. (선택) **Actions 탭 → Daily news digest → Run workflow** 로 수동 실행해 바로 테스트

이후엔 매일 아침 자동으로 돌아가고, 사이트는 `https://<계정>.github.io/news_monitor/` 에서 볼 수 있습니다.

참고:
- 스케줄 워크플로는 저장소의 **기본 브랜치**에서만 동작합니다. 이 코드를 기본 브랜치에 두세요.
- GitHub Actions 스케줄은 수분~수십분 지연될 수 있지만, 수집 구간은 실행 시점의 날짜 기준으로
  계산되므로 결과는 동일합니다.
- 저장소에 60일간 커밋이 없으면 GitHub이 스케줄을 자동 비활성화하는데, 이 워크플로는 매일
  digest를 커밋하므로 계속 활성 상태로 유지됩니다.

## 언론사 수집 점검

```bash
python test_sources.py
```

각 언론사별로 오늘자 사회면 1페이지를 읽어 몇 건이 잡히는지 보여줍니다. (2026-07 기준
10개사 모두 실수집 검증 완료.) 특정 언론사가 계속 0건이거나 FAIL이 뜨면 `config.py`의
`oid`를 확인하거나 `scraper/naver_scraper.py`의 CSS 선택자를 조정해주세요.

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

## 로컬 사용법

### 1) 수동으로 한 번 실행 (수집 + 저장 + 텔레그램 전송)

```bash
python run_daily.py
```

### 2) 웹사이트로 확인

```bash
python app.py          # 로컬 개발 서버 (http://localhost:5000)
python build_site.py   # GitHub Pages용 정적 HTML을 site/에 생성
```

언론사별 카드로 헤드라인/시간이 표시되고, 상단 날짜 탭에서 과거 digest도 볼 수 있습니다.

### 3) 직접 서버를 운영하는 경우의 대안 (GitHub Actions을 안 쓸 때)

**cron 사용 (Linux/macOS 서버):**

```
35 7 * * * cd /path/to/news_monitor && /path/to/venv/bin/python run_daily.py >> run.log 2>&1
```

**상시 프로세스로 실행 (systemd 등에 올려두는 경우):**

```bash
python scheduler.py
```

매일 07:35(KST)에 자동으로 `run_daily.py`와 동일한 작업을 수행합니다.

## 시간 구간 로직

"전일 23:00 ~ 당일 07:30"은 스크립트를 **실행하는 시점의 당일 날짜** 기준으로 계산됩니다
(`collector.get_window`). 예를 들어 7월 7일 07:35에 실행하면 7월 6일 23:00 ~ 7월 7일 07:30
구간의 기사를 수집합니다. 따라서 매일 07:30 이후(권장: 07:35)에 실행해야 그날의 창이
온전히 채워집니다.

## 디렉터리 구조

```
config.py                언론사 목록(oid), 시간 구간, 텔레그램 설정
scraper/naver_scraper.py 네이버뉴스 기반 스크레이핑 핵심 로직
collector.py             전체 언론사 수집 오케스트레이션 + JSON 저장
telegram_bot.py          digest -> 텔레그램 메시지 포맷/전송
app.py                   Flask 웹사이트 (로컬 확인용)
build_site.py            GitHub Pages용 정적 사이트 빌드
templates/, static/      웹사이트 템플릿/스타일
run_daily.py             수집+저장+전송 진입점
scheduler.py             자체 서버에서 상시 프로세스로 돌리고 싶을 때
test_sources.py          언론사별 수집 상태 점검 스크립트
data/                    수집 결과 JSON (저장소에 커밋되어 이력 보존)
.github/workflows/daily-digest.yml  매일 07:35 자동 수집+전송+배포
```

## 알려진 한계

- 네이버뉴스 페이지 구조가 바뀌면 `scraper/naver_scraper.py`의 CSS 선택자를 손봐야 합니다.
- 언론사가 네이버뉴스에 송고하지 않은 기사(자사 홈페이지 단독 게재 등)는 수집되지 않습니다.
- 네이버 측의 과도한 요청 차단을 피하기 위해 요청 사이에 약간의 지연을 두었습니다. 언론사가
  많아 전체 수집에 1~2분 정도 걸릴 수 있습니다.
