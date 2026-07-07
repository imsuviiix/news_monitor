"""수집된 야간 사회면 뉴스 digest를 보여주는 웹사이트 (로컬 확인용).

GitHub Pages 배포는 build_site.py가 같은 템플릿으로 정적 HTML을 생성한다.
"""
import glob
import json
import os

from flask import Flask, abort, render_template, url_for

import config

app = Flask(__name__)


def _digest_path(date=None):
    if date is None:
        return os.path.join(config.DATA_DIR, "latest.json")
    return os.path.join(config.DATA_DIR, f"digest_{date}.json")


def load_digest(date=None):
    path = _digest_path(date)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_available_dates():
    files = sorted(glob.glob(os.path.join(config.DATA_DIR, "digest_*.json")), reverse=True)
    return [os.path.basename(f)[len("digest_") : -len(".json")] for f in files]


def _render(digest, current_date):
    nav = [{"date": d, "href": url_for("digest_view", date=d)} for d in list_available_dates()]
    return render_template(
        "index.html",
        digest=digest,
        dates=nav,
        current_date=current_date,
        css_href=url_for("static", filename="style.css"),
        home_href=url_for("index"),
    )


@app.route("/")
def index():
    return _render(load_digest(), None)


@app.route("/digest/<date>")
def digest_view(date):
    digest = load_digest(date)
    if not digest:
        abort(404)
    return _render(digest, date)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
