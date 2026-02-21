#!/usr/bin/env python3
"""
fetch_missing_content.py

Fetches problem descriptions for premium-locked LeetCode questions
using the user's Chrome session cookies (read via browser_cookie3,
which handles macOS Keychain decryption).

Usage: python3 fetch_missing_content.py
"""

import os
import json
import time
import glob
import re
import urllib.request
import requests
import browser_cookie3


# ── Config ───────────────────────────────────────────────────────────────────

RAW_DIR   = "raw_questions"
IMAGE_DIR = "images"
GRAPHQL   = "https://leetcode.com/graphql/"

CONTENT_QUERY = """
query questionContent($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    content
    codeSnippets {
      lang
      langSlug
      code
    }
  }
}
"""


# ── Cookie extraction ─────────────────────────────────────────────────────────

def build_session() -> requests.Session:
    """Build a requests Session with LeetCode cookies from Chrome."""
    print("Reading Chrome cookies for leetcode.com (may prompt for Keychain access)...")
    cookiejar = browser_cookie3.chrome(domain_name='.leetcode.com')

    session = requests.Session()
    session.cookies = cookiejar

    # Extract csrftoken for the header
    csrf = ''
    for cookie in cookiejar:
        if cookie.name == 'csrftoken':
            csrf = cookie.value
            break

    if not csrf:
        for cookie in cookiejar:
            if 'csrf' in cookie.name.lower():
                csrf = cookie.value
                break

    session.headers.update({
        'Content-Type': 'application/json',
        'Referer': 'https://leetcode.com',
        'x-csrftoken': csrf,
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    })

    # Sanity check — verify we have LEETCODE_SESSION
    has_session = any(c.name == 'LEETCODE_SESSION' for c in cookiejar)
    print(f"  LEETCODE_SESSION present: {has_session}")
    print(f"  csrftoken: {'found' if csrf else 'NOT FOUND'}")
    return session


# ── GraphQL fetch ─────────────────────────────────────────────────────────────

def fetch_content(slug: str, session: requests.Session) -> dict:
    resp = session.post(
        GRAPHQL,
        json={'query': CONTENT_QUERY, 'variables': {'titleSlug': slug}},
        timeout=15
    )
    resp.raise_for_status()
    q = resp.json().get('data', {}).get('question') or {}
    return {
        'content':      q.get('content'),
        'codeSnippets': q.get('codeSnippets') or []
    }


# ── Image downloader ──────────────────────────────────────────────────────────

def download_images(html: str, qid: str) -> str:
    """Download any remote images in html to images/{qid}/ and rewrite src."""
    if not html:
        return html
    pattern = re.compile(r'src="(https?://[^"]+)"')
    urls = list(set(pattern.findall(html)))
    if not urls:
        return html
    img_dir = os.path.join(IMAGE_DIR, qid)
    os.makedirs(img_dir, exist_ok=True)
    for url in urls:
        filename = url.split('/')[-1].split('?')[0]
        local    = os.path.join(img_dir, filename)
        rel      = f'images/{qid}/{filename}'
        if not os.path.exists(local):
            try:
                urllib.request.urlretrieve(url, local)
                print(f'    ↳ image: {filename}')
            except Exception as e:
                print(f'    ↳ failed {filename}: {e}')
                continue
        html = html.replace(f'src="{url}"', f'src="{rel}"')
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Find all files with null content
    missing = []
    for filepath in sorted(glob.glob(os.path.join(RAW_DIR, '*.json'))):
        with open(filepath) as f:
            data = json.load(f)
        if data.get('content') is None:
            missing.append((filepath, data))

    print(f'Found {len(missing)} questions with null content.\n')

    session = build_session()
    print()

    success = failed = 0

    for filepath, data in missing:
        qid   = data.get('questionFrontendId', '?')
        slug  = data.get('titleSlug', '')
        title = data.get('title', '')

        print(f'[{qid}] {title}')

        if not slug:
            print('  SKIP — no titleSlug')
            failed += 1
            continue

        try:
            result = fetch_content(slug, session)
        except Exception as e:
            print(f'  ERROR: {e}')
            failed += 1
            time.sleep(2)
            continue

        content  = result['content']
        snippets = result['codeSnippets']

        if content:
            content = download_images(content, qid)
            data['content'] = content
            print(f'  ✓ description ({len(content):,} chars)')
            success += 1
        else:
            print(f'  ✗ still null (still premium-locked or login failed)')
            failed += 1

        if snippets and not data.get('codeSnippets'):
            data['codeSnippets'] = snippets
            print(f'  ✓ code snippets ({len(snippets)} langs)')

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        time.sleep(1.2)   # be polite to LeetCode

    print(f'\n{"─"*50}')
    print(f'Done. Updated: {success}  |  Still missing: {failed}')
    if success > 0:
        print('\nNext: run  python3 process_data.py  to regenerate data.js')


if __name__ == '__main__':
    main()
