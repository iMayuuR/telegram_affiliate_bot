import os
import time
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import threading
from flask import Flask

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EARNKARO_TODAY_URL = "https://earnkaro.com/top-selling-products/today-best-deals"
POSTS_PER_BATCH = int(os.getenv('POSTS_PER_BATCH', '5'))
MIN_INTERVAL_MIN = int(os.getenv('MIN_INTERVAL_MIN', '30'))
MAX_INTERVAL_MIN = int(os.getenv('MAX_INTERVAL_MIN', '75'))

# आपके affiliate details
AMAZON_TAG = os.getenv('AMAZON_AFFILIATE_TAG', 'your-amazon-tag')
FLIPKART_ID = os.getenv('FLIPKART_AFFILIATE_ID', 'your-flipkart-id')
USE_EARNKARO = os.getenv('USE_EARNKARO', 'true').lower() == 'true'

def send_telegram_text(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set')
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID, 
        'text': text, 
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        r = requests.post(url, data=payload, timeout=15)
        print(f'📤 Telegram send status: {r.status_code}')
        return r.status_code == 200
    except Exception as e:
        print(f'❌ Telegram send error: {e}')
        return False

def make_multi_affiliate(url):
    """Multi-level affiliate linking"""
    if not url:
        return url
    
    original_url = url
    
    # Step 1: Add your direct affiliate tags
    if 'amazon.in' in url and 'tag=' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}tag={AMAZON_TAG}"
    
    if 'flipkart.com' in url and 'affid=' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}affid={FLIPKART_ID}"
    
    # Add more retailers as needed
    if 'myntra.com' in url and 'utm_source=' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}utm_source=affiliate"
    
    # Step 2: Wrap with EarnKaro if enabled
    if USE_EARNKARO:
        # EarnKaro के through redirect
        import urllib.parse
        encoded_url = urllib.parse.quote(url, safe='')
        final_url = f"https://earnkaro.com/link?url={encoded_url}"
        return final_url
    
    return url

# बाकी functions same रहेंगे... (scraping, formatting, etc.)

def scrape_today_best(limit=20):
    """Enhanced scraping function"""
    print(f"🔍 Starting to scrape: {EARNKARO_TODAY_URL}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        r = requests.get(EARNKARO_TODAY_URL, headers=headers, timeout=30)
        print(f"📡 Status: {r.status_code}, Length: {len(r.text)}")
        
        if r.status_code != 200:
            return []
            
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        # Enhanced patterns for better deal detection
        all_links = soup.find_all('a', href=True)
        print(f"🔗 Found {len(all_links)} total links")
        
        # Broad patterns for multiple retailers
        valid_patterns = [
            '/hp-', '/product-', '/p/', '/deal', '/offer',
            'amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com',
            'nykaa.com', 'meesho.com', 'paytm', 'snapdeal',
            'tatacliq', 'reliance', 'jiomart'
        ]
        
        for a in all_links:
            href = (a.get('href') or '').strip()
            text = (a.get_text() or '').strip()
            
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
                
            if any(pattern in href.lower() for pattern in valid_patterns):
                if href.startswith('/'):
                    href = 'https://earnkaro.com' + href
                
                results.append({
                    'title': text[:80] if text else 'Special Deal',
                    'url': href
                })
                
                if len(results) >= limit:
                    break
        
        print(f"✅ Found {len(results)} deals")
        return results
        
    except Exception as e:
        print(f'❌ Scraping error: {e}')
        return []

def format_message(item):
    """Enhanced message formatting"""
    title = item.get('title', 'Deal').strip()
    url = item.get('affiliate') or item.get('url')
    
    if len(title) > 80:
        title = title[:77] + "..."
    
    # Dynamic emojis
    emoji = "🔥"
    if 'amazon' in title.lower():
        emoji = "📦"
    elif 'flipkart' in title.lower():
        emoji = "🛍️"
    elif any(word in title.lower() for word in ['fashion', 'clothing']):
        emoji = "👗"
    
    return f"{emoji} <b>{title}</b>\n🛒 <a href='{url}'>Get Deal Now</a>\n\n💰 <i>Exclusive affiliate offers!</i>"

# बाकी code same...
def main_bot_function():
    print("🚀 Multi-Affiliate Bot started!")
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Starting new scraping cycle...")
            
            pool = scrape_today_best(limit=50)
            
            if not pool:
                print('❌ No deals found, sleeping 10 minutes')
                time.sleep(600)
                continue
            
            random.shuffle(pool)
            batch = pool[:POSTS_PER_BATCH]
            
            print(f"📤 Posting {len(batch)} deals...")
            
            for i, item in enumerate(batch, 1):
                item['affiliate'] = make_multi_affiliate(item['url'])  # Updated function
                msg = format_message(item)
                
                if send_telegram_text(msg):
                    print(f"✅ Posted deal {i}/{len(batch)}")
                else:
                    print(f"❌ Failed to post deal {i}/{len(batch)}")
                
                time.sleep(random.randint(3, 8))
            
            wait_minutes = random.randint(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN)
            print(f"⏰ Cycle completed - sleeping for {wait_minutes} minutes")
            time.sleep(wait_minutes * 60)
            
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(300)

# Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 Multi-Affiliate EarnKaro Bot</h1>
    <p>✅ Bot is running with multiple affiliate programs!</p>
    <p>💰 EarnKaro + Your Direct Affiliates</p>
    """

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == '__main__':
    threading.Thread(target=main_bot_function, daemon=True).start()
    run_flask()
