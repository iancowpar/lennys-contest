"""Download all accessible content from Lenny's MCP server.

Fetches all entries via list_content, then reads each file via read_content,
and saves them as markdown with YAML frontmatter into data/starter-pack/.

Usage:
  python -m extraction.fetch_mcp --token <access_token> --out data/starter-pack

To refresh token automatically, set LENNYSDATA_CLIENT_ID and
LENNYSDATA_REFRESH_TOKEN in environment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path

import httpx

log = logging.getLogger("fetch_mcp")

MCP_URL = "https://mcp.lennysdata.com/mcp"
TOKEN_URL = "https://www.lennysdata.com/api/oauth/token"


def refresh_access_token(client_id: str, refresh_token: str) -> str:
    resp = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    log.info("Token refreshed, expires_in=%s", data.get("expires_in"))
    return data["access_token"]


def _mcp_call(client: httpx.Client, token: str, method: str, params: dict, req_id: int) -> dict:
    """Make a single stateless MCP call and return the result dict."""
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }
    resp = client.post(
        MCP_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    # Response is SSE: "event: message\ndata: {...}\n\n"
    for line in resp.text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise ValueError(f"No data line in response: {resp.text[:200]}")


def list_all_content(client: httpx.Client, token: str) -> list[dict]:
    """Paginate through list_content until we have everything."""
    items = []
    offset = 0
    limit = 100
    while True:
        result = _mcp_call(
            client, token, "tools/call",
            {"name": "list_content", "arguments": {"limit": limit, "offset": offset}},
            req_id=1000 + offset,
        )
        text = result["result"]["content"][0]["text"]
        page = json.loads(text)
        batch = page.get("results", [])
        items.extend(batch)
        total = page.get("total", 0)
        log.info("Listed %d/%d items", len(items), total)
        if len(items) >= total or not batch:
            break
        offset += limit
    return items


def read_file_content(client: httpx.Client, token: str, filename: str, req_id: int) -> str:
    """Read the full markdown content of a file."""
    result = _mcp_call(
        client, token, "tools/call",
        {"name": "read_content", "arguments": {"filename": filename}},
        req_id=req_id,
    )
    return result["result"]["content"][0]["text"]


def build_frontmatter(item: dict) -> str:
    """Construct YAML frontmatter from item metadata."""
    lines = ["---"]
    lines.append(f"title: {json.dumps(item['title'])}")
    if item.get("date"):
        lines.append(f"date: {item['date']}")
    if item.get("guest"):
        lines.append(f"guest: {json.dumps(item['guest'])}")
    if item.get("description"):
        lines.append(f"subtitle: {json.dumps(item['description'])}")
    if item.get("tags"):
        lines.append("tags:")
        for tag in item["tags"]:
            lines.append(f"  - {tag}")
    if item.get("word_count"):
        lines.append(f"word_count: {item['word_count']}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def save_item(item: dict, body: str, out_dir: Path) -> Path:
    """Save item as a markdown file with YAML frontmatter."""
    filename = item["filename"]
    dest = out_dir / filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Strip any existing frontmatter from the body the server returns
    if body.startswith("---"):
        # Already has frontmatter — write as-is
        dest.write_text(body, encoding="utf-8")
    else:
        # Prepend our generated frontmatter
        dest.write_text(build_frontmatter(item) + body, encoding="utf-8")

    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Access token (or set via env LENNYSDATA_ACCESS_TOKEN)")
    parser.add_argument("--out", type=Path, default=Path("data/starter-pack"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    token = (
        args.token
        or os.environ.get("LENNYSDATA_ACCESS_TOKEN")
    )

    if not token:
        # Try to refresh
        client_id = os.environ.get("LENNYSDATA_CLIENT_ID")
        refresh = os.environ.get("LENNYSDATA_REFRESH_TOKEN")
        if client_id and refresh:
            log.info("Refreshing token...")
            token = refresh_access_token(client_id, refresh)
        else:
            raise SystemExit("No token available. Pass --token or set LENNYSDATA_ACCESS_TOKEN")

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as client:
        log.info("Listing all content...")
        items = list_all_content(client, token)
        log.info("Found %d items", len(items))

        # Download each file
        saved = 0
        errors = 0
        for i, item in enumerate(items, start=1):
            filename = item["filename"]
            dest = out_dir / filename

            if dest.exists():
                log.info("[%d/%d] SKIP (exists) %s", i, len(items), filename)
                saved += 1
                continue

            try:
                log.info("[%d/%d] Downloading %s", i, len(items), filename)
                body = read_file_content(client, token, filename, req_id=i)
                path = save_item(item, body, out_dir)
                log.info("  → saved %s (%d chars)", path, len(body))
                saved += 1
            except Exception as e:
                log.error("  ✗ %s: %s", filename, e)
                errors += 1

    log.info("Done: %d saved, %d errors", saved, errors)


if __name__ == "__main__":
    main()
