import os
import json
import asyncio
from bs4 import BeautifulSoup
from litellm import acompletion

def clean_html(html_content, java_only=False):
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove unwanted tags completely
    for tag in soup(["iframe", "img", "video", "figure", "style", "script"]):
        tag.decompose()
        
    for tag in soup.find_all(True):
        if tag.name in ["div", "span"]:
            tag.unwrap()
        else:
            if tag.name == "a":
                href = tag.get("href")
                tag.attrs = {}
                if href: tag["href"] = href
            else:
                tag.attrs = {}
                
    if java_only:
        pres = soup.find_all("pre")
        java_pres = []
        for pre in pres:
            text = pre.get_text()
            if "class Solution" in text and ("public int" in text or "public boolean" in text or "public void" in text or "public String" in text or "public List" in text or "public char" in text or "public double" in text or "public long" in text or "public Node" in text or "public int[]" in text) and "public:" not in text:
                java_pres.append(pre)
        if java_pres:
            for pre in pres:
                if pre not in java_pres:
                    pre.decompose()

    return str(soup).strip()

def has_java_native(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for pre in soup.find_all("pre"):
        text = pre.get_text()
        if ("class " in text or "public " in text) and "public" in text and "->" not in text and "std::" not in text and "vector<" not in text and "#include" not in text and "def " not in text:
            if "System.out.print" in text or "public int" in text or "public boolean" in text or "public void" in text or "public static" in text or "public String" in text or "public List" in text or "public char" in text or "public double" in text or "public long" in text or "public Node" in text or "public int[]" in text or (("class Solution" in text or "public class" in text) and "public:" not in text):
                return True
    return False

async def rewrite_with_llm(cleaned_html, title, sem):
    system_prompt = (
        "You are an expert technical editor. "
        "The HTML explains a programming solution and has code snippets. "
        "1. Rewrite ALL code blocks (<pre>) to be in Java. Match the textual explanation in logic. "
        "2. Update inline language references in paragraphs (e.g. change 'C++' to 'Java'). "
        "3. Output ONLY the raw continuous HTML. "
        "Keep the text intact. DO NOT add markdown wrappers."
    )
    async with sem:
        try:
            response = await acompletion(
                model='azure/gpt-5.2-chat',
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": cleaned_html}
                ],
                api_key=os.environ.get("AZURE_API_KEY"),
                api_base='https://peili-ml8nvkg0-eastus2.cognitiveservices.azure.com/',
                api_version='2025-04-01-preview'
            )
            res = response.choices[0].message.content.strip()
            if res.startswith("```html"): res = res[7:]
            if res.startswith("```"): res = res[3:]
            if res.endswith("```"): res = res[:-3]
            return res.strip()
        except Exception as e:
            print(f"[{title}] API Error: {e}")
            return cleaned_html

async def process_file(path, sem):
    with open(path, "r") as fp:
        try: data = json.load(fp)
        except: return
        
    if "codeSnippets" in data and data["codeSnippets"]:
        data["codeSnippets"] = [s for s in data["codeSnippets"] if s.get("lang") == "Java"]
    
    solution = data.get("solution")
    if solution and "content" in solution and solution["content"]:
        content = solution["content"]
        is_java = has_java_native(content)
        cleaned = clean_html(content, java_only=is_java)
        
        if not is_java:
            print(f"Converting {os.path.basename(path)} to Java async...")
            new_content = await rewrite_with_llm(cleaned, os.path.basename(path), sem)
            solution["content"] = new_content
        else:
            solution["content"] = cleaned
            
    with open(path, "w") as fp:
        json.dump(data, fp, indent=4)

async def main():
    raw_dir = "raw_questions"
    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    sem = asyncio.Semaphore(5)
    
    tasks = []
    print(f"Spawning {len(files)} tasks...")
    for f in sorted(files):
        path = os.path.join(raw_dir, f)
        tasks.append(process_file(path, sem))
        
    await asyncio.gather(*tasks)
    print("Done processing all files!")

if __name__ == "__main__":
    asyncio.run(main())
