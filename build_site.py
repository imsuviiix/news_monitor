"""data/의 digest JSON들을 정적 HTML 사이트(site/)로 빌드한다. GitHub Pages 배포용."""
import glob
import json
import os
import shutil

from jinja2 import Environment, FileSystemLoader

import config

SITE_DIR = os.path.join(config.BASE_DIR, "site")
MAX_NAV_DATES = 30


def load_digests():
    digests = []
    for path in sorted(glob.glob(os.path.join(config.DATA_DIR, "digest_*.json")), reverse=True):
        with open(path, encoding="utf-8") as f:
            digests.append(json.load(f))
    return digests


def main():
    digests = load_digests()[:MAX_NAV_DATES]

    if os.path.exists(SITE_DIR):
        shutil.rmtree(SITE_DIR)
    os.makedirs(SITE_DIR)
    shutil.copytree(os.path.join(config.BASE_DIR, "static"), os.path.join(SITE_DIR, "static"))

    env = Environment(loader=FileSystemLoader(os.path.join(config.BASE_DIR, "templates")))
    template = env.get_template("index.html")

    nav = [{"date": d["date"], "href": f"digest_{d['date']}.html"} for d in digests]
    common = {"css_href": "static/style.css", "home_href": "index.html", "dates": nav}

    latest = digests[0] if digests else None
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(template.render(digest=latest, current_date=None, **common))

    for digest in digests:
        out = os.path.join(SITE_DIR, f"digest_{digest['date']}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(template.render(digest=digest, current_date=digest["date"], **common))

    print(f"[build_site] {len(digests)}개 digest로 정적 사이트 생성 완료: {SITE_DIR}")


if __name__ == "__main__":
    main()
