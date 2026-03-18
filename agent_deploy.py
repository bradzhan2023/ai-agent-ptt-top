import os
import sys
import requests
import json
from git import Repo

# ================= 配置區域 =================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "bradzhan2023"
# 這裡改為自動偵測目錄名稱作為 Repo 名稱，這樣你換到哪個資料夾，它就推到哪個 Repo
CURRENT_DIR = os.path.basename(os.getcwd())
GITHUB_REPO = CURRENT_DIR 

APP_FILE = "generated_app.py"
AGENT_FILE = "agent_deploy.py"
README_FILE = "README.md"

if not GEMINI_API_KEY or not GITHUB_TOKEN:
    print("❌ 錯誤：請先執行 export 設定環境變數！")
    exit(1)

GITHUB_REPO_URL = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
# ===========================================

def get_available_model():
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={GEMINI_API_KEY}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for m in models:
                    if 'flash' in m['name'] and 'generateContent' in m.get('supportedGenerationMethods', []):
                        return m['name'], version
        except: continue
    raise Exception("無法獲取模型")

def call_gemini_api(prompt, model_id, api_ver):
    url = f"https://generativelanguage.googleapis.com/{api_ver}/{model_id}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    raise Exception(f"API Error: {response.text}")

def developer_agent_incremental(task, model_id, api_ver):
    existing_code = ""
    if os.path.exists(APP_FILE):
        with open(APP_FILE, "r", encoding="utf-8") as f:
            existing_code = f.read()
    
    if existing_code:
        print(f"🔄 偵測到現有代碼，正在增量開發新功能：{task}")
        prompt = f"目前的 Python 代碼如下：\n{existing_code}\n\n請在保留原功能下新增功能：{task}。只輸出完整的 Python 代碼，不含說明或標籤。"
    else:
        print(f"🆕 正在建立新功能：{task}")
        prompt = f"請寫一個 Python 腳本來完成此任務：{task}。只輸出 Python 代碼，不含說明或標籤。"
    
    code = call_gemini_api(prompt, model_id, api_ver)
    return code.replace("```python", "").replace("```", "").strip()

def github_release_agent(task_name, app_code, readme_content):
    print(f"🚀 [Release Agent] 同步至 GitHub Repo: {GITHUB_REPO}...")
    with open(APP_FILE, "w", encoding="utf-8") as f: f.write(app_code)
    with open(README_FILE, "w", encoding="utf-8") as f: f.write(readme_content)

    try:
        repo = Repo(".")
        if 'origin' in [r.name for r in repo.remotes]:
            repo.remote('origin').set_url(GITHUB_REPO_URL)
        else:
            repo.create_remote('origin', GITHUB_REPO_URL)

        repo.index.add([APP_FILE, AGENT_FILE, README_FILE])
        commit_msg = f"AI Update: {task_name}"
        repo.index.commit(commit_msg)
        repo.git.push(GITHUB_REPO_URL, 'main')
        print(f"✅ 部署成功！請查看 GitHub！")
    except Exception as e:
        print(f"❌ Git 失敗: {e}")

if __name__ == "__main__":
    # --- 關鍵改動：從命令列讀取任務 ---
    if len(sys.argv) < 2:
        print("💡 使用方式: python3 agent_deploy.py \"你的任務描述\"")
        print("範例: python3 agent_deploy.py \"寫一個爬取 PTT 八卦版前 20 篇標題的爬蟲\"")
        exit(1)
        
    my_task = sys.argv[1]
    
    try:
        model_id, api_ver = get_available_model()
        clean_code = developer_agent_incremental(my_task, model_id, api_ver)
        
        print(f"📖 [Document] 生成文件中...")
        with open(AGENT_FILE, "r", encoding="utf-8") as f: script_content = f.read()
        doc_prompt = f"請為此專案寫一個繁體中文 README.md。介紹這是一個由 AI Agent 開發的專案。目前的任務是：{my_task}。"
        readme_md = call_gemini_api(doc_prompt, model_id, api_ver)
        
        github_release_agent(my_task, clean_code, readme_md)
    except Exception as e:
        print(f"💥 錯誤: {e}")