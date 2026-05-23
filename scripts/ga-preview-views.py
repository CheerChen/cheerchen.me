#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-analytics-data>=0.18",
# ]
# ///
"""Preview per-article view counts from GA4 Data API.

Usage:
  GA4_PROPERTY_ID=123456789 uv run scripts/ga-preview-views.py
  GA4_PROPERTY_ID=123456789 uv run scripts/ga-preview-views.py --since 2024-01-01
  GA4_PROPERTY_ID=123456789 uv run scripts/ga-preview-views.py --output-json data/ga-snapshot.json

Auth: relies on Application Default Credentials. Run once:
  gcloud auth application-default login \\
    --client-id-file=$HOME/.config/gcp/oauth-client.json \\
    --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform

Or set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)


# Map a GA pagePath to a stable page_key.
# /posts/<slug>/        -> posts/<slug>
# /ja/posts/<slug>/     -> posts/<slug>
# Anything else         -> None (ignored)
POST_PATH_RE = re.compile(r"^/(?:ja/)?posts/([^/?#]+)/?(?:\?.*)?$")


def path_to_key(path: str) -> str | None:
    m = POST_PATH_RE.match(path)
    if not m:
        return None
    return f"posts/{m.group(1)}"


def fetch_views(property_id: str, since: str, until: str) -> list[tuple[str, int]]:
    client = BetaAnalyticsDataClient()
    rows: list[tuple[str, int]] = []
    offset = 0
    page_size = 100_000

    while True:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=since, end_date=until)],
            limit=page_size,
            offset=offset,
        )
        resp = client.run_report(request)
        for row in resp.rows:
            path = row.dimension_values[0].value
            views = int(row.metric_values[0].value)
            rows.append((path, views))
        if len(resp.rows) < page_size:
            break
        offset += page_size

    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="2020-01-01", help="YYYY-MM-DD")
    parser.add_argument("--until", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw (path, views) without grouping",
    )
    parser.add_argument(
        "--output-json",
        metavar="PATH",
        help="Write grouped {page_key: views} JSON to PATH instead of printing",
    )
    args = parser.parse_args()

    property_id = os.environ.get("GA4_PROPERTY_ID")
    if not property_id:
        print("ERROR: set GA4_PROPERTY_ID env var", file=sys.stderr)
        return 2

    print(
        f"# GA4 property {property_id}, {args.since} .. {args.until}",
        file=sys.stderr,
    )
    raw = fetch_views(property_id, args.since, args.until)
    print(f"# {len(raw)} raw rows from GA", file=sys.stderr)

    if args.raw:
        for path, views in sorted(raw, key=lambda x: -x[1]):
            print(f"{views:>8}  {path}")
        return 0

    grouped: dict[str, int] = defaultdict(int)
    dropped = 0
    dropped_examples: list[str] = []
    for path, views in raw:
        key = path_to_key(path)
        if key is None:
            dropped += views
            if len(dropped_examples) < 5 and views > 0:
                dropped_examples.append(f"{views:>6}  {path}")
            continue
        grouped[key] += views

    print(
        f"# {len(grouped)} post keys, {dropped} views dropped (non-post paths)",
        file=sys.stderr,
    )
    if dropped_examples:
        print("# top non-post paths dropped:", file=sys.stderr)
        for line in dropped_examples:
            print(f"#   {line}", file=sys.stderr)

    if args.output_json:
        out = dict(sorted(grouped.items()))
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        print(f"# wrote {len(out)} keys to {args.output_json}", file=sys.stderr)
        return 0

    print(f"{'views':>8}  page_key")
    for key, views in sorted(grouped.items(), key=lambda x: -x[1]):
        print(f"{views:>8}  {key}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
