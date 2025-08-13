import os
import time
import random
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import threading
from flask import Flask

# Load local .env if present (for local testing)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EARNKARO_TODAY_URL = "https://earnkaro.com/top-selling-products/today-best-deals"
POSTS_PER_BATCH = int(os.getenv('POSTS_PER_BATCH', '5'))
MIN_INTERVAL_MIN = int(os.getenv('MIN_INTERVAL_MIN', '30'))
MAX_INTERVAL_MIN = int(os.getenv('MAX_INTERVAL_MIN', '75'))

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
        if r.status_code != 200:
            print(f'❌ Telegram error: {r.text}')
        return r.status_code == 200
    except Exception as e:
        print(f'❌ Telegram send error: {e}')
        return False

def is_valid_product_link(href):
    """Check if URL is a valid product link"""
    if not href or href.startswith('#') or href.startswith('mailto:'):
        return False
    
    valid_patterns = [
        '/hp-', '/product-', '/p/', '/deal', '/offer',
        'flipkart.com', 'amazon.in', 'myntra.com', 'ajio.com',
        'nykaa.com', 'meesho.com', 'paytmmall.com'
    ]
    
    return any(pattern in href.lower() for pattern in valid_patterns)

def normalize_url(url):
    """Normalize and clean URLs"""
    if url.startswith('/'):
        url = 'https://earnkaro.com' + url
    return url.strip()

def scrape_today_best(limit=20):
    """Fixed scraping function"""
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
        
        # Look for any valid product links
        all_links = soup.find_all('a', href=True)
        print(f"🔗 Found {len(all_links)} total links")
        
        for a in all_links:
            href = a.get('href', '').strip()
            text = a.get_text(strip=True)
            
            if is_valid_product_link(href):
                full_url = normalize_url(href)
                results.append({
                    'title': text[:80] if text else 'Great Deal',
                    'url': full_url
                })
                
                if len(results) >= limit:
                    break
        
        print(f"✅ Found {len(results)} deals")
        return results
        
    except Exception as e:
        print(f'❌ Scraping error: {e}')
        return []

def make_affiliate(url):
    """Enhanced affiliate tagging"""
    if not url:
        return url
    
    if 'amazon.in' in url and 'tag=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}tag=techb0ad-21"
    
    if 'flipkart.com' in url and 'affid=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}affid=mayur0424"
    
    return url

def format_message(item):
    """Format message for Telegram"""
    title = item.get('title', 'Deal').strip()
    url = item.get('affiliate') or item.get('url')
    
    if len(title) > 80:
        title = title[:77] + "..."
    
    emoji = "🔥"
    if 'amazon' in title.lower():
        emoji = "📦"
    elif 'flipkart' in title.lower():
        emoji = "🛍️"
    elif any(word in title.lower() for word in ['fashion', 'clothing']):
        emoji = "👗"
    
    return f"{emoji} <b>{title}</b>\n🛒 <a href='{url}'>Get Deal</a>\n\n💡 <i>Exclusive offers daily!</i>"

def main_bot_function():
    """Main bot loop"""
    print("🚀 Bot started!")
    
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"🔄 Starting new scraping cycle...")
            
            pool = scrape_today_best(limit=50)
            
            if not pool:
                print('❌ No deals found, sleeping 10 minutes')
                time.sleep(600)
                continue
            
            # Random shuffle and pick per batch
            random.shuffle(pool)
            batch = pool[:POSTS_PER_BATCH]
            
            print(f"📤 Posting {len(batch)} deals...")
            
            for i, item in enumerate(batch, 1):
                item['affiliate'] = make_affiliate(item['url'])
                msg = format_message(item)
                
                if send_telegram_text(msg):
                    print(f"✅ Posted deal {i}/{len(batch)}")
                else:
                    print(f"❌ Failed to post deal {i}/{len(batch)}")
                
                time.sleep(random.randint(3, 8))
            
            wait_minutes = random.randint(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN)
            print(f"⏰ Cycle finished — sleeping for {wait_minutes} minutes.")
            time.sleep(wait_minutes * 60)
            
        except KeyboardInterrupt:
            print("👋 Bot stopped")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(300)

# Flask server for Railway
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 EarnKaro Affiliate Bot</h1>
    <p>✅ Bot is running!</p>
    <p>📊 Check logs for activity</p>
    """

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == '__main__':
    # Start bot in background thread
    threading.Thread(target=main_bot_function, daemon=True).start()
    # Run Flask in main thread
    run_flask()
