#!/usr/bin/env python3
"""
audit_questions.py

Comprehensive quality check for all 300 raw question JSON files.
Checks: description, images, Java snippet, solution, code snippet languages.
"""

import os
import glob
import json
import re
from collections import defaultdict

RAW_DIR   = "raw_questions"
IMAGE_DIR = "images"

def check_image_urls(html, qid):
    """Find img src URLs that are still remote (not downloaded locally)."""
    if not html:
        return []
    pattern = re.compile(r'src="(https?://[^"]+)"')
    return pattern.findall(html)

def audit():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))
    print(f"Auditing {len(files)} question files...\n")

    issues = defaultdict(list)

    # Counters
    total                   = len(files)
    null_content            = []
    empty_content           = []
    remote_images           = []   # questions where content has un-downloaded images
    no_java_snippet         = []
    no_solution             = []
    no_solution_java_code   = []   # solution exists but no Java code block in it
    no_code_snippets        = []
    low_content             = []   # content < 100 chars (likely bad data)

    for filepath in files:
        with open(filepath) as f:
            d = json.load(f)

        qid   = d.get("questionFrontendId", "?")
        title = d.get("title", "?")
        label = f"[{qid}] {title}"

        content       = d.get("content")
        solution_obj  = d.get("solution") or {}
        solution_html = solution_obj.get("content", "") if solution_obj else ""
        code_snippets = d.get("codeSnippets") or []
        java_snippet  = next((s.get("code","") for s in code_snippets if s.get("lang") == "Java"), "")

        # ── Content checks ──────────────────────────────────────────────────
        if content is None:
            null_content.append(label)
        elif content == "":
            empty_content.append(label)
        elif len(content) < 100:
            low_content.append((label, len(content), content[:80]))
        
        # ── Remote images in content ────────────────────────────────────────
        if content:
            remote = check_image_urls(content, qid)
            if remote:
                remote_images.append((label, remote))

        # ── Java starter code ───────────────────────────────────────────────
        if not java_snippet:
            no_java_snippet.append(label)

        if not code_snippets:
            no_code_snippets.append(label)

        # ── Solution checks ─────────────────────────────────────────────────
        if not solution_html:
            no_solution.append(label)
        else:
            # Check if solution has Java code
            java_markers = ["public int", "public boolean", "public void", 
                          "public String", "public List", "class Solution",
                          "public char", "public double", "public long",
                          "public int[]", "public Node"]
            has_java_in_solution = any(m in solution_html for m in java_markers)
            if not has_java_in_solution:
                no_solution_java_code.append(label)

    # ── Print report ─────────────────────────────────────────────────────────
    def section(title, items, detail=False):
        count = len(items)
        status = "✅" if count == 0 else "⚠️ "
        print(f"{status}  {title}: {count}/{total}")
        if items:
            for item in items:
                if isinstance(item, tuple):
                    print(f"      {item[0]}")
                    for v in item[1:]:
                        if isinstance(v, list):
                            for img in v[:3]:
                                print(f"        img: {img[:80]}")
                            if len(v) > 3:
                                print(f"        ... +{len(v)-3} more")
                        else:
                            print(f"        {v[:80]}")
                else:
                    print(f"      {item}")
        print()

    print("=" * 60)
    print("AUDIT REPORT — LeetCode Top 300")
    print("=" * 60 + "\n")

    section("Null descriptions (premium-locked)", null_content)
    section("Empty descriptions", empty_content)
    section("Suspiciously short descriptions (<100 chars)", low_content, detail=True)
    section("Remote images still in description HTML", remote_images, detail=True)
    section("Missing Java starter code snippet", no_java_snippet)
    section("Missing codeSnippets array entirely", no_code_snippets)
    section("Missing solution editorial entirely", no_solution)
    section("Solution exists but no Java code detected", no_solution_java_code)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    problems = (
        len(null_content) + len(empty_content) + len(low_content) +
        len(remote_images) + len(no_java_snippet) + len(no_solution)
    )
    if problems == 0:
        print("✅  All 300 questions look good!")
    else:
        print(f"⚠️   {problems} total issues found across {total} questions")
    print()

if __name__ == "__main__":
    audit()
