"""매일 아침 실행: 야간 뉴스 수집 -> 저장 -> 텔레그램 전송. cron/스케줄러에서 호출."""
from collector import collect_all, save_digest
from telegram_bot import send_digest


def main():
    print("[run_daily] 사회면 야간 뉴스 수집 시작")
    digest = collect_all()
    path = save_digest(digest)
    print(f"[run_daily] 저장 완료: {path}")

    total = sum(o["count"] for o in digest["outlets"])
    print(f"[run_daily] 총 {total}건 수집됨")

    send_digest(digest)
    print("[run_daily] 텔레그램 전송 완료")


if __name__ == "__main__":
    main()
