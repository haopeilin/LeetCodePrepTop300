#!/usr/bin/env python3
"""
split_data.py
Reads data.js (which exports a JS array as `const questionsData = [...]`)
and writes:
  - data/<id>.json  for every question  (full data)
  - data/index.json                      (lightweight: id, title, difficulty, tags only)
"""

import json
import os
import re

DATA_JS   = os.path.join(os.path.dirname(__file__), "data.js")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "data")

def main():
    print(f"Reading {DATA_JS} ...")
    with open(DATA_JS, "r", encoding="utf-8") as f:
        raw = f.read()

    # Strip the JS variable wrapper: `const questionsData = [...]`
    # The file is a single line: const questionsData = [{ ... }];
    match = re.match(r"^\s*const\s+questionsData\s*=\s*(\[.*\])\s*;?\s*$", raw, re.DOTALL)
    if not match:
        raise ValueError("Could not parse data.js – expected `const questionsData = [...]`")

    json_str = match.group(1)
    questions = json.loads(json_str)
    print(f"Parsed {len(questions)} questions.")

    os.makedirs(OUT_DIR, exist_ok=True)

    index = []

    for q in questions:
        qid = str(q.get("id", "unknown"))

        # Write full JSON
        out_path = os.path.join(OUT_DIR, f"{qid}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(q, f, ensure_ascii=False, separators=(",", ":"))

        # Collect lightweight entry for index
        index.append({
            "id":         q.get("id"),
            "title":      q.get("title"),
            "difficulty": q.get("difficulty"),
            "tags":       q.get("tags", []),
        })

    # Write index
    index_path = os.path.join(OUT_DIR, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    # Report sizes
    index_size = os.path.getsize(index_path)
    total_size = sum(os.path.getsize(os.path.join(OUT_DIR, f))
                     for f in os.listdir(OUT_DIR) if f.endswith(".json"))

    print(f"\n✅ Done!")
    print(f"   Individual files : {len(questions)} × data/<id>.json")
    print(f"   index.json size  : {index_size / 1024:.1f} KB")
    print(f"   Total JSON size  : {total_size / 1024 / 1024:.1f} MB  (vs original {os.path.getsize(DATA_JS)/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()
