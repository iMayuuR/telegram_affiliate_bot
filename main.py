import os
import time
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load local .env if present (for local testing)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # e.g. @FlipkartAmazonAjioSale or numeric id
EARNKARO_TODAY_URL = "https://earnkaro.com/top-selling-products/today-best-deals"

POSTS_PER_BATCH = int(os.getenv('POSTS_PER_BATCH', '5'))
MIN_INTERVAL_MIN = int(os.getenv('MIN_INTERVAL_MIN', '30'))
MAX_INTERVAL_MIN = int(os.getenv('MAX_INTERVAL_MIN', '75'))

def send_telegram_text(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set')
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        r = requests.post(url, data=payload, timeout=15)
        print('Telegram send status:', r.status_code)
        return r.status_code == 200
    except Exception as e:
        print('Telegram send error:', e)
        return False

def scrape_today_best(limit=20):
    try:
        r = requests.get(EARNKARO_TODAY_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        # naive selectors: find product anchor blocks
        anchors = soup.select('a[href]')
        for a in anchors:
            href = a.get('href') or ''
            text = (a.get_text() or '').strip()
            if not href or href.startswith('#'):
                continue
            # simple heuristics to pick likely product links (contains common retailer domains or /hp- or /product/)
            if any(k in href for k in ['/hp-', '/product-', '/p/', 'flipkart.com', 'amazon.in', 'myntra.com', 'ajio.com']):
                results.append({'title': text or 'Deal', 'url': href})
            if len(results) >= limit:
                break
        # normalize urls
        for item in results:
            if item['url'].startswith('/'):
                item['url'] = 'https://earnkaro.com' + item['url']
        return results
    except Exception as e:
        print('Scrape error:', e)
        return []

def make_affiliate(url):
    # Basic affiliate tagging for Amazon/Flipkart — adjust if needed
    if 'amazon.in' in url and 'tag=' not in url:
        if '?' in url:
            return url + '&tag=techb0ad-21'
        else:
            return url + '?tag=techb0ad-21'
    if 'flipkart.com' in url and 'affid=' not in url:
        if '?' in url:
            return url + '&affid=mayur0424'
        else:
            return url + '?affid=mayur0424'
    return url

def format_message(item):
    title = item.get('title') or 'Deal'
    url = item.get('affiliate') or item.get('url')
    return f"🔥 <b>{title}</b>\n🛒 {url}"

if __name__ == '__main__':
    print('Bot started. Using randomized intervals.')
    while True:
        pool = scrape_today_best(limit=50)
        if not pool:
            print('No deals found, sleeping 10 minutes')
            time.sleep(600)
            continue
        # random shuffle and pick per batch
        random.shuffle(pool)
        batch = pool[:POSTS_PER_BATCH]
        for item in batch:
            item['affiliate'] = make_affiliate(item['url'])
            msg = format_message(item)
            send_telegram_text(msg)
            time.sleep(5)  # short delay between posts
        wait_minutes = random.randint(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN)
        print(f"Cycle finished — sleeping for {wait_minutes} minutes.")
        time.sleep(wait_minutes * 60)
