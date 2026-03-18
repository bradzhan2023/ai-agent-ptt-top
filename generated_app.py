import requests
from bs4 import BeautifulSoup
import time
import random

def get_ptt_gossiping_popular_posts():
    PTT_URL = 'https://www.ptt.cc'
    GOSSIPING_URL = f'{PTT_URL}/bbs/Gossiping/index.html'

    # Define User-Agent to simulate a Chrome browser
    # This helps in preventing ConnectionResetError and appearing as a legitimate client
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive',
    }

    # Retry parameters
    MAX_RETRIES = 3
    MIN_DELAY = 2  # minimum delay in seconds
    MAX_DELAY = 5  # maximum delay in seconds

    # Create a session to handle age verification and cookies
    session = requests.Session()
    # Apply default headers to the session. All subsequent requests will use these headers.
    session.headers.update(DEFAULT_HEADERS)

    # Step 1: Handle PTT's age verification with retries
    print("嘗試 PTT 18 歲驗證...")
    for attempt in range(MAX_RETRIES):
        try:
            # 發送 POST 請求模擬點擊「我同意」。
            # session 會自動處理接收和發送 cookie。
            resp = session.post(f'{PTT_URL}/ask/over18', data={'from': GOSSIPING_URL, 'yes': 'yes'})
            resp.raise_for_status() # 對於 4xx 或 5xx 響應拋出 HTTPError
            print("18 歲驗證成功。")
            break # 成功則跳出重試循環
        except requests.exceptions.RequestException as e:
            print(f"18 歲驗證失敗 (嘗試 {attempt+1}/{MAX_RETRIES} 次): {e}")
            if attempt < MAX_RETRIES - 1:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"將在 {delay:.2f} 秒後重試...")
                time.sleep(delay)
            else:
                print("多次重試後 18 歲驗證失敗，程式終止。")
                return # 所有重試都失敗，終止函數

    # 如果所有重試都失敗，則上面的 `return` 會終止函數。
    # 執行到這裡表示 18 歲驗證成功。

    # Step 2: Fetch the main Gossiping board page using the authenticated session with retries
    print(f"嘗試抓取 {GOSSIPING_URL} 頁面...")
    resp = None # Initialize resp to None
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(GOSSIPING_URL)
            resp.raise_for_status()
            print("成功抓取八卦版頁面。")
            break # 成功則跳出重試循環
        except requests.exceptions.RequestException as e:
            print(f"抓取頁面失敗 (嘗試 {attempt+1}/{MAX_RETRIES} 次): {e}")
            if attempt < MAX_RETRIES - 1:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"將在 {delay:.2f} 秒後重試...")
                time.sleep(delay)
            else:
                print("多次重試後抓取頁面失敗，程式終止。")
                return # 所有重試都失敗，終止函數

    # 如果 `resp` 仍然是 None，表示抓取失敗，此處應再次檢查。
    if resp is None:
        print("無法取得頁面內容，程式終止。")
        return

    # Step 3: Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find all post entries. Each post is typically within a div with class 'r-ent'.
    posts = soup.find_all('div', class_='r-ent')

    for post in posts:
        # Extract push count
        nrec_tag = post.find('div', class_='nrec')
        push_count_str = nrec_tag.text.strip() if nrec_tag else '0'

        push_count = 0
        if push_count_str == '爆':
            push_count = 100
        elif push_count_str.startswith('X'):
            try:
                # PTT 的 'X' 推文數表示噓文數。
                # 通常 X1 代表 <-10，X2 代表 <-20 等。
                # 這裡假設 X後面數字n代表-n*10。
                push_count = -int(push_count_str[1:]) * 10 
            except ValueError:
                push_count = 0
        else:
            try:
                push_count = int(push_count_str)
            except ValueError:
                push_count = 0 # 默認值，如果不是數字、'爆' 或 'X'

        # Extract title
        title_tag_div = post.find('div', class_='title')
        title_link_tag = title_tag_div.find('a') if title_tag_div else None
        
        # Filter out deleted posts or other non-article entries which do not have an 'a' tag
        if title_link_tag:
            title = title_link_tag.text.strip()
        else:
            # This handles cases like "(本文已被刪除)" where there's no link
            title = title_tag_div.text.strip() if title_tag_div else "[無標題]"
            # We might want to skip these deleted posts entirely for "熱門標題"
            if "本文已被刪除" in title or "本文已被" in title:
                continue

        # Extract author
        author_tag = post.find('div', class_='author')
        author = author_tag.text.strip() if author_tag else '[未知]'
        
        print(f"推文數: {push_count}, 標題: {title}, 作者: {author}")

if __name__ == '__main__':
    get_ptt_gossiping_popular_posts()