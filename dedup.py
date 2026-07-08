"""완전 동일 기사(정확히 같은 기사)만 제거한다.

통신사 등에서 똑같은 기사가 목록에 두 번 이상 나타나는 경우가 있다. 이런 "아예
똑같은 기사"만 걸러낸다. 판단 기준은 다음 중 하나라도 같으면 동일 기사로 본다:

  1) 기사 링크(URL)가 같다  -> 네이버 기사 URL은 언론사+기사 고유번호라 링크가
     같으면 물리적으로 완전히 같은 기사다.
  2) 같은 언론사 안에서 제목과 발행 시각이 모두 같다 -> 재송고되며 URL만 새로
     받은 동일 기사를 잡기 위함.

내용이 비슷하더라도 위 조건에 해당하지 않으면(제목·발행시각·언론사 중 하나라도
다르면) 서로 다른 기사이므로 절대 제거하지 않는다.
"""


def _norm(text):
    return " ".join((text or "").split())


def dedupe_outlets(outlets):
    """완전히 동일한 기사를 제거하고(첫 기사만 유지) 제거된 건수를 반환한다."""
    removed = 0
    seen_links = set()
    for outlet in outlets:
        seen_title_time = set()
        kept_articles = []
        for article in outlet["articles"]:
            link = _norm(article.get("link"))
            title_time = (_norm(article.get("title")), _norm(article.get("published_at")))

            is_dup = (link and link in seen_links) or title_time in seen_title_time
            if is_dup:
                removed += 1
                continue

            if link:
                seen_links.add(link)
            seen_title_time.add(title_time)
            kept_articles.append(article)
        outlet["articles"] = kept_articles
        outlet["count"] = len(kept_articles)
    return removed
