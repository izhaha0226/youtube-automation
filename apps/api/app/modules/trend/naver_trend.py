"""Naver DataLab search trend API.

Returns daily relative search volume for given keywords over a date range.
Requires NAVER_CLIENT_ID and NAVER_CLIENT_SECRET.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def fetch_search_trend(
    keywords: list[str],
    days: int = 30,
) -> list[dict]:
    if not settings.naver_client_id or not settings.naver_client_secret:
        log.info("naver_trend.skip", reason="no credentials")
        return []

    end = datetime.now()
    start = end - timedelta(days=days)

    keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords[:5]]

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id": settings.naver_client_id,
                    "X-Naver-Client-Secret": settings.naver_client_secret,
                    "Content-Type": "application/json",
                },
                json={
                    "startDate": start.strftime("%Y-%m-%d"),
                    "endDate": end.strftime("%Y-%m-%d"),
                    "timeUnit": "date",
                    "keywordGroups": keyword_groups,
                },
            )

        if resp.status_code != 200:
            log.warning("naver_trend.error", status=resp.status_code, body=resp.text[:200])
            return []

        data = resp.json()
        results = data.get("results", [])

        date_map: dict[str, dict[str, float]] = {}
        for group in results:
            kw = group["title"]
            for point in group.get("data", []):
                d = point["period"]
                if d not in date_map:
                    date_map[d] = {}
                date_map[d][kw] = point.get("ratio", 0)

        timeline = []
        for d in sorted(date_map.keys()):
            entry: dict[str, str | float] = {"date": datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d")}
            for kw in keywords[:5]:
                entry[kw] = date_map[d].get(kw, 0)
            timeline.append(entry)

        log.info("naver_trend.done", keywords=keywords[:5], points=len(timeline))
        return timeline

    except Exception as e:
        log.warning("naver_trend.error", error=str(e))
        return []
