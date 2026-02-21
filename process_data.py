import os
import json
from bs4 import BeautifulSoup

raw_dir = "raw_questions"
output_file = "data.js"

questions = []

for filename in os.listdir(raw_dir):
    if filename.endswith(".json"):
        with open(os.path.join(raw_dir, filename), "r") as f:
            data = json.load(f)
            
            title = data.get("title", "")
            diff = data.get("difficulty", "")
            content = data.get("content", "")
            tags = [tag.get("name") for tag in data.get("topicTags", [])]
            
            java_code = ""
            code_snippets = data.get("codeSnippets") or []
            for snippet in code_snippets:
                if snippet.get("lang") == "Java":
                    java_code = snippet.get("code")
                    break
            
            # The solution content often contains explanations. We'll include it.
            solution_content = data.get("solution", {}).get("content", "") if data.get("solution") else ""
            
            if solution_content:
                soup = BeautifulSoup(solution_content, "html.parser")
                # Remove imgs, iframes, and videos
                for tag in soup.find_all(["img", "iframe", "video", "figure"]):
                    tag.decompose()
                
                # Check for Java codes in pre tags
                pres = soup.find_all("pre")
                java_pres = []
                for pre in pres:
                    text = pre.get_text()
                    if "class Solution" in text and ("public int" in text or "public boolean" in text or "public void" in text or "public String" in text or "public List" in text or "public char" in text or "public double" in text or "public long" in text or "public Node" in text or "public int[]" in text):
                        java_pres.append(pre)
                
                # If there is at least one Java pre block, remove non-Java blocks
                if java_pres:
                    for pre in pres:
                        if pre not in java_pres:
                            pre.decompose()
                
                solution_content = str(soup)
            
            questions.append({
                "id": data.get("questionFrontendId"),
                "title": title,
                "difficulty": diff,
                "content": content,
                "tags": tags,
                "java_snippet": java_code,
                "solution": solution_content
            })

# Sort by question ID
questions.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else float('inf'))

with open(output_file, "w") as f:
    f.write("const questionsData = " + json.dumps(questions, separators=(',', ':')) + ";\n")

print(f"Processed {len(questions)} questions.")
