"""
상시 실행 프로세스로 두고 평일 07:01(KST)에 자동으로 뉴스를 수집/전송하고 싶을 때 사용.
서버에서 `python scheduler.py` 로 실행해두면 된다. (systemd 등으로 재시작되도록 구성 권장)
cron을 사용할 수 있는 환경이라면 이 스크립트 대신 cron + run_daily.py 조합도 가능하다.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo

import config
from run_daily import main as run_daily_main


def job():
    print("[scheduler] 예약 실행: 야간 뉴스 수집 시작")
    run_daily_main()


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=ZoneInfo(config.TIMEZONE))
    scheduler.add_job(job, "cron", day_of_week="mon-fri", hour=7, minute=1)
    print("스케줄러 시작됨: 평일 07:01(KST)에 실행됩니다. (Ctrl+C로 종료)")
    scheduler.start()
