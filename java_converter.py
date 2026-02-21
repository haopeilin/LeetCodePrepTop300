import json
import os
import time
from bs4 import BeautifulSoup
from litellm import completion

def analyze_solution_code(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    pres = soup.find_all("pre")
    
    has_java = False
    has_cpp = False
    
    for pre in pres:
        text = pre.get_text()
        if ("class " in text or "public " in text) and "public" in text and "->" not in text and "std::" not in text and "vector<" not in text and "#include" not in text and "def " not in text:
            if "System.out.print" in text or "public int" in text or "public boolean" in text or "public void" in text or "public static" in text or "public String" in text or "public List" in text or "public char" in text or "public double" in text or "public long" in text or "public Node" in text or "public int[]" in text or (("class Solution" in text or "public class" in text) and "public:" not in text):
                has_java = True
                continue
                
        if "public:" in text or "std::" in text or "vector<" in text or "#include" in text:
            has_cpp = True
            
    return has_java, has_cpp

def convert_to_java(html_content, title):
    print(f"  Converting {title} to Java...")
    # System prompt to convert provided code block to Java
    system_prompt = "You are an expert software engineer. Given an HTML article containing algorithmic solutions (usually C++), rewrite the code snippets to be in Java. Keep the surrounding text structure exactly the same, only change the code inside the <pre> tags (and the language names in paragraphs, e.g., 'C++' to 'Java'). Provide the raw HTML response. Wait do NOT wrap your response with markdown codeblocks like ```html, just output raw html string."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": html_content}
    ]
    
    try:
        response = completion(
            model='gemini/gemini-2.5-flash',
            messages=messages,
            api_key=os.getenv('GEMINI_API_KEY')
        )
        res = response.choices[0].message.content.strip()
        if res.startswith("```html"):
            res = res[7:]
        if res.startswith("```"):
            res = res[3:]
        if res.endswith("```"):
            res = res[:-3]
        return res.strip()
    except Exception as e:
        print(f"  Error converting {title}: {e}")
        return html_content

def main():
    raw_dir = "raw_questions"
    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    
    print("Converting missing Java solutions...")
    count = 0
    with open("needs_conversion.json", "r") as f:
        needs_conv = json.load(f)
        
    for filename in sorted(needs_conv):
        path = os.path.join(raw_dir, filename)
        with open(path, "r") as f:
            data = json.load(f)
            
        title = data.get("title", filename)
        solution = data.get("solution", {}).get("content", "") if data.get("solution") else ""
        
        if not solution: continue
        
        new_solution = convert_to_java(solution, title)
        
        # Optionally, verify the output actually has java now
        has_java, _ = analyze_solution_code(new_solution)
        if has_java:
            print(f"  [{title}] Successfully converted to Java!")
            # Update and save the JSON
            data["solution"]["content"] = new_solution
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
        else:
            print(f"  [{title}] Conversion failed, Java not detected in output.")
            
        count += 1
        time.sleep(2) # rate limit mitigation
        if count % 10 == 0:
            os.system(f"echo 'Batch processing progress... {count} done.'")

if __name__ == "__main__":
    main()
