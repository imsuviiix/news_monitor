"""제목 유사도 기반 중복 기사 제거.

통신사(연합뉴스·뉴시스·뉴스1)는 같은 사건을 거의 동일한 제목으로 각각 송고하고,
[속보]→[2보]→[종합]처럼 같은 기사의 버전이 여러 번 올라온다.
config.OUTLETS 순서(신문사 우선)대로 훑으면서, 앞서 이미 남긴 기사와 제목이
사실상 같은 기사는 제거한다. 즉 신문사 기사가 우선 유지되고 통신사 중복이 빠진다.
"""
import re
from difflib import SequenceMatcher

SIMILARITY_THRESHOLD = 0.8

# [단독], [속보], (종합), 【포토】, <2보> 같은 장식/버전 표기 제거용
_BRACKET_RE = re.compile(r"[\[(【<][^\])】>]{0,15}[\])】>]")
_PUNCT_RE = re.compile(r"[^0-9a-zA-Z가-힣]+")


def normalize_title(title):
    text = _BRACKET_RE.sub(" ", title or "")
    text = _PUNCT_RE.sub(" ", text).lower()
    return " ".join(text.split())


def is_similar(a, b, threshold=SIMILARITY_THRESHOLD):
    if a == b:
        return True
    matcher = SequenceMatcher(None, a, b)
    # 싼 어림값으로 먼저 거른 뒤에만 정밀 비교 (전체 쌍 비교 비용 절감)
    if matcher.real_quick_ratio() < threshold or matcher.quick_ratio() < threshold:
        return False
    return matcher.ratio() >= threshold


def dedupe_outlets(outlets):
    """outlets(수집 결과 리스트)에서 중복 기사를 제거하고 제거된 건수를 반환한다."""
    kept_norms = []
    removed = 0
    for outlet in outlets:
        kept_articles = []
        for article in outlet["articles"]:
            norm = normalize_title(article["title"])
            if norm and any(is_similar(norm, kept) for kept in kept_norms):
                removed += 1
                continue
            if norm:
                kept_norms.append(norm)
            kept_articles.append(article)
        outlet["articles"] = kept_articles
        outlet["count"] = len(kept_articles)
    return removed
