"""수집된 야간 사회면 뉴스 digest를 보여주는 웹사이트."""
import glob
import json
import os

from flask import Flask, abort, render_template

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


@app.route("/")
def index():
    digest = load_digest()
    return render_template("index.html", digest=digest, dates=list_available_dates(), current_date=None)


@app.route("/digest/<date>")
def digest_view(date):
    digest = load_digest(date)
    if not digest:
        abort(404)
    return render_template("index.html", digest=digest, dates=list_available_dates(), current_date=date)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
