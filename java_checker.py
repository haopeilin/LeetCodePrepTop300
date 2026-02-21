import json
import os
from bs4 import BeautifulSoup

def analyze_solution_code(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    pres = soup.find_all("pre")
    
    has_java = False
    has_cpp = False
    has_python = False
    has_other = False
    
    for pre in pres:
        text = pre.get_text()
        # check for java
        if ("class " in text or "public " in text) and "public" in text and "->" not in text and "std::" not in text and "vector<" not in text and "#include" not in text and "def " not in text:
            # could be java
            if "System.out.print" in text or "public int" in text or "public boolean" in text or "public void" in text or "public static" in text or "public String" in text or "public List" in text or "public char" in text or "public double" in text or "public long" in text or "public Node" in text or "public int[]" in text or (("class Solution" in text or "public class" in text) and "public:" not in text):
                has_java = True
                continue
                
        # check for cbpp
        if "public:" in text or "std::" in text or "vector<" in text or "#include" in text:
            has_cpp = True
            continue
            
        # check python
        if "def " in text or "class Solution:" in text or "self," in text or "print(" in text:
            if "{" not in text and ";" not in text:
                has_python = True
                continue
                
        # some SQL?
        if "SELECT " in text.upper() or "UPDATE " in text.upper() or "DELETE " in text.upper() or "INSERT " in text.upper():
            has_other = True
            continue
            
        has_other = True

    return has_java, has_cpp, has_python, has_other

def main():
    raw_dir = "raw_questions"
    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    
    total = 0
    java_count = 0
    no_java_list = []
    
    print("Checking questions one by one for Java solutions by analyzing code grammar and details...")
    print("-" * 50)
    
    for filename in sorted(files):
        path = os.path.join(raw_dir, filename)
        with open(path, "r") as f:
            data = json.load(f)
            
        title = data.get("title", filename)
        solution = data.get("solution", {}).get("content", "") if data.get("solution") else ""
        
        has_java, has_cpp, has_py, has_oth = analyze_solution_code(solution)
        
        status = []
        if has_java: status.append("Java")
        if has_cpp: status.append("C++")
        if has_py: status.append("Python")
        if has_oth: status.append("Other (SQL/JS/etc.)")
        if not status: status.append("No Code / No Solution")
        
        print(f"[{title}] -> Found formats: {', '.join(status)}", end="")
        if has_java:
            print("  (OK)")
            java_count += 1
        else:
            print("  (LACKS JAVA)")
            no_java_list.append((filename, title, solution))
        total += 1
        
    print("-" * 50)
    print("=== SUMMARY ===")
    print(f"Total Questions Analyzed: {total}")
    print(f"Questions WITH Java solution detected via grammar: {java_count}")
    print(f"Questions MISSING Java solution: {len(no_java_list)}")
    
    if no_java_list:
        print("\nSaving list of files needing conversion to 'needs_conversion.json'...")
        with open("needs_conversion.json", "w") as f:
            json.dump([item[0] for item in no_java_list], f)

if __name__ == "__main__":
    main()
