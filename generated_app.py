import requests
from bs4 import BeautifulSoup
import time
import random
import csv

def get_ptt_gossiping_popular_posts():
    PTT_URL = 'https://www.ptt.cc'
    GOSSIPING_URL = f'{PTT_URL}/bbs/Gossiping/index.html'

    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive',
    }

    MAX_RETRIES = 3
    MIN_DELAY = 2
    MAX_DELAY = 5

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    print("嘗試 PTT 18 歲驗證...")
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.post(f'{PTT_URL}/ask/over18', data={'from': GOSSIPING_URL, 'yes': 'yes'})
            resp.raise_for_status()
            print("18 歲驗證成功。")
            break
        except requests.exceptions.RequestException as e:
            print(f"18 歲驗證失敗 (嘗試 {attempt+1}/{MAX_RETRIES} 次): {e}")
            if attempt < MAX_RETRIES - 1:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"將在 {delay:.2f} 秒後重試...")
                time.sleep(delay)
            else:
                print("多次重試後 18 歲驗證失敗，程式終止。")
                return

    print(f"嘗試抓取 {GOSSIPING_URL} 頁面...")
    resp = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(GOSSIPING_URL)
            resp.raise_for_status()
            print("成功抓取八卦版頁面。")
            break
        except requests.exceptions.RequestException as e:
            print(f"抓取頁面失敗 (嘗試 {attempt+1}/{MAX_RETRIES} 次): {e}")
            if attempt < MAX_RETRIES - 1:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"將在 {delay:.2f} 秒後重試...")
                time.sleep(delay)
            else:
                print("多次重試後抓取頁面失敗，程式終止。")
                return

    if resp is None:
        print("無法取得頁面內容，程式終止。")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')

    posts = soup.find_all('div', class_='r-ent')

    all_posts_data = [] # 用於儲存所有文章資料的列表

    for post in posts:
        nrec_tag = post.find('div', class_='nrec')
        push_count_str = nrec_tag.text.strip() if nrec_tag else '0'

        push_count = 0
        if push_count_str == '爆':
            push_count = 100
        elif push_count_str.startswith('X'):
            # 根據新需求，將 'X' 開頭的負評視為 0
            push_count = 0
        else:
            try:
                push_count = int(push_count_str)
            except ValueError:
                push_count = 0

        title_tag_div = post.find('div', class_='title')
        title_link_tag = title_tag_div.find('a') if title_tag_div else None
        
        if title_link_tag:
            title = title_link_tag.text.strip()
        else:
            # 處理已刪除或無連結的文章標題
            title = title_tag_div.text.strip() if title_tag_div else "[無標題]"
            if "本文已被刪除" in title or "本文已被" in title:
                continue # 跳過已刪除的文章

        author_tag = post.find('div', class_='author')
        author = author_tag.text.strip() if author_tag else '[未知]'
        
        # 將文章資料加入列表
        all_posts_data.append({
            '推文數': push_count,
            '標題': title,
            '作者': author
        })
    
    if all_posts_data:
        # 根據推文數進行由大到小的排序
        all_posts_data.sort(key=lambda x: x['推文數'], reverse=True)

        print("\n--- PTT 八卦版熱門文章 (依推文數排序) ---")
        
        # 動態計算欄位寬度，確保表格整齊
        push_col_width = max(len("推文數"), max(len(str(post['推文數'])) for post in all_posts_data))
        title_col_width = max(len("標題"), max(len(post['標題']) for post in all_posts_data))
        author_col_width = max(len("作者"), max(len(post['作者']) for post in all_posts_data))
        
        # 增加一些額外填充，讓表格更美觀
        push_col_width += 2
        title_col_width += 4
        author_col_width += 2

        # 表頭格式化字串
        header_format = f"{{:<{push_col_width}}} {{:<{title_col_width}}} {{:<{author_col_width}}}"
        
        # 打印表頭
        print(header_format.format("推文數", "標題", "作者"))
        # 打印分隔線 (加4是因為有兩個分隔符號，每個佔2個空格)
        print("-" * (push_col_width + title_col_width + author_col_width + 4))

        # 打印排序後的文章內容
        for post in all_posts_data:
            print(header_format.format(post['推文數'], post['標題'], post['作者']))
        
        # 打印底部線
        print("-" * (push_col_width + title_col_width + author_col_width + 4))
    else:
        print("\n沒有收集到任何文章資料。")

    # 將爬取結果存成 CSV 檔案 (此部分功能不變)
    if all_posts_data:
        csv_file_path = 'ptt_gossiping_popular_posts.csv'
        fieldnames = ['推文數', '標題', '作者']
        
        try:
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader() # 寫入標題行
                writer.writerows(all_posts_data) # 寫入所有資料行
            print(f"\n成功將爬取結果儲存至 {csv_file_path}")
        except IOError as e:
            print(f"\n寫入 CSV 檔案失敗: {e}")
    else:
        print("\n沒有收集到任何文章資料，未生成 CSV 檔案。")

if __name__ == '__main__':
    get_ptt_gossiping_popular_posts()