#!/usr/bin/env python3
"""
download_images.py

Finds all remote image URLs still in question descriptions / solutions,
and downloads them using the authenticated LeetCode session (so the CDN
doesn't 403). Rewrites the src in the raw JSON files to the local path.

Usage: python3 download_images.py
"""

import os
import glob
import json
import re
import time
import browser_cookie3
import requests

RAW_DIR   = "raw_questions"
IMAGE_DIR = "images"


def build_session() -> requests.Session:
    print("Reading Chrome cookies...")
    cookiejar = browser_cookie3.chrome(domain_name='.leetcode.com')
    session = requests.Session()
    session.cookies = cookiejar
    csrf = next((c.value for c in cookiejar if c.name == 'csrftoken'), '')
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://leetcode.com",
        "x-csrftoken": csrf,
    })
    return session


def find_remote_images(html: str):
    """Return list of remote https:// image URLs found in HTML."""
    if not html:
        return []
    return re.findall(r'src="(https?://[^"]+)"', html)


def download_image(url: str, local_path: str, session: requests.Session) -> bool:
    """Download a single image using the authenticated session. Returns True on success."""
    try:
        resp = session.get(url, timeout=15, stream=True)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ✗ {os.path.basename(local_path)}: {e}")
        return False


def rewrite_url(html: str, url: str, local_rel: str) -> str:
    return html.replace(f'src="{url}"', f'src="{local_rel}"')


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))

    # First pass: find everything that needs downloading
    work = []  # list of (filepath, data, [(url, local_path, rel_path), ...], field)
    total_imgs = 0

    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)

        qid = data.get("questionFrontendId", "?")

        for field in ("content",):
            html = data.get(field) or ""
            urls = find_remote_images(html)
            if urls:
                img_tasks = []
                for url in set(urls):
                    filename = url.split("/")[-1].split("?")[0]
                    if not filename or "." not in filename:
                        filename = f"img_{abs(hash(url)) % 100000}.png"
                    local_path = os.path.join(IMAGE_DIR, qid, filename)
                    rel_path   = f"images/{qid}/{filename}"
                    img_tasks.append((url, local_path, rel_path))
                work.append((filepath, data, img_tasks, field))
                total_imgs += len(img_tasks)

    affected_questions = len(work)
    print(f"Found {total_imgs} remote images across {affected_questions} questions.\n")

    if total_imgs == 0:
        print("✅ Nothing to download!")
        return

    session = build_session()
    print()

    downloaded = 0
    failed     = 0

    for filepath, data, img_tasks, field in work:
        qid   = data.get("questionFrontendId", "?")
        title = data.get("title", "?")
        print(f"[{qid}] {title}  ({len(img_tasks)} image(s))")

        html    = data.get(field) or ""
        changed = False

        for url, local_path, rel_path in img_tasks:
            # Skip if already downloaded
            if os.path.exists(local_path):
                html    = rewrite_url(html, url, rel_path)
                changed = True
                print(f"    ↳ already exists: {os.path.basename(local_path)}")
                continue

            ok = download_image(url, local_path, session)
            if ok:
                html    = rewrite_url(html, url, rel_path)
                changed = True
                downloaded += 1
                print(f"    ✓ {os.path.basename(local_path)}")
            else:
                failed += 1

            time.sleep(0.3)

        if changed:
            data[field] = html
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\n{'─'*50}")
    print(f"Downloaded: {downloaded}  |  Failed: {failed}")
    if downloaded > 0:
        print("\nNext: run  python3 process_data.py  to regenerate data.js")


if __name__ == "__main__":
    main()
