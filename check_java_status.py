import json
import os
from bs4 import BeautifulSoup
import re

def is_java_code(text):
    # Check for Java-specific keywords and structures
    if "class Solution" in text or "public class" in text or "class Node" in text:
        if "public" in text or "private" in text or "protected" in text:
            # Avoid C++ specific ones
            if "std::" not in text and "vector<" not in text and "#include" not in text and "->" not in text:
                return True
    return False

raw_dir = "raw_questions"
total_questions = 0
has_java = 0
no_java = 0
no_java_list = []

for filename in os.listdir(raw_dir):
    if not filename.endswith(".json"):
        continue
    
    with open(os.path.join(raw_dir, filename), "r") as f:
        data = json.load(f)
        
    title = data.get("title", filename)
    solution_content = data.get("solution", {}).get("content", "") if data.get("solution") else ""
    
    java_found = False
    
    if solution_content:
        soup = BeautifulSoup(solution_content, "html.parser")
        pres = soup.find_all("pre")
        
        for pre in pres:
            text = pre.get_text()
            if is_java_code(text):
                java_found = True
                break
                
    total_questions += 1
    if java_found:
        has_java += 1
    else:
        no_java += 1
        no_java_list.append(title)
        
print(f"Total Questions: {total_questions}")
print(f"Questions WITH Java solution: {has_java}")
print(f"Questions WITHOUT Java solution: {no_java}")
if no_java > 0:
    print(f"\nExample of 20 questions without Java:")
    for t in no_java_list[:20]:
        print("  -", t)
