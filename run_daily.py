"""매일 아침 실행: 야간 뉴스 수집 -> 저장 -> 텔레그램 전송.

--skip-telegram 옵션을 주면 수집/저장만 한다. (GitHub Actions에서는 수집과
전송을 별도 스텝으로 나눠, 전송 실패가 사이트 배포를 막지 않으면서도
실패가 눈에 띄게 한다.)
"""
import argparse
import sys

from collector import collect_all, save_digest
from telegram_bot import send_digest


def main(skip_telegram=False):
    print("[run_daily] 사회면 야간 뉴스 수집 시작")
    digest = collect_all()
    path = save_digest(digest)
    print(f"[run_daily] 저장 완료: {path}")

    total = sum(o["count"] for o in digest["outlets"])
    print(f"[run_daily] 총 {total}건 수집됨")

    if skip_telegram:
        return

    if not send_digest(digest):
        sys.exit(1)
    print("[run_daily] 텔레그램 전송 완료")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-telegram", action="store_true", help="수집/저장만 하고 텔레그램 전송은 생략")
    args = parser.parse_args()
    main(skip_telegram=args.skip_telegram)
