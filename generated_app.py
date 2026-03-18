import requests
from bs4 import BeautifulSoup

def get_ptt_gossiping_popular_posts():
    PTT_URL = 'https://www.ptt.cc'
    GOSSIPING_URL = f'{PTT_URL}/bbs/Gossiping/index.html'

    # Create a session to handle age verification and cookies
    session = requests.Session()

    # Step 1: Handle PTT's age verification
    # Send a POST request to /ask/over18 to simulate clicking "我同意"
    try:
        resp = session.post(f'{PTT_URL}/ask/over18', data={'from': GOSSIPING_URL, 'yes': 'yes'})
        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error during age verification: {e}")
        return

    # Step 2: Fetch the main Gossiping board page using the authenticated session
    try:
        resp = session.get(GOSSIPING_URL)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
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
                # X1, X2, etc. usually mean negative counts (e.g., -10, -20)
                # We'll represent them as negative integers based on the number
                push_count = -int(push_count_str[1:]) * 10 # Example: X10 -> -100
            except ValueError:
                push_count = 0
        else:
            try:
                push_count = int(push_count_str)
            except ValueError:
                push_count = 0 # Default if it's not a number, '爆', or 'X'

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