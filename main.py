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

# Headers to avoid bot detection
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}

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

def test_telegram_connection():
    """Test if telegram bot is working"""
    print("🧪 Testing Telegram connection...")
    test_msg = "🤖 Bot is alive and testing connection!"
    result = send_telegram_text(test_msg)
    if result:
        print("✅ Telegram connection successful!")
    else:
        print("❌ Telegram connection failed!")
    return result

def scrape_today_best(limit=20):
    """Improved scraping with better error handling and debugging"""
    print(f"🔍 Starting to scrape: {EARNKARO_TODAY_URL}")
    
    try:
        # Make request with proper headers
        r = requests.get(EARNKARO_TODAY_URL, headers=HEADERS, timeout=30)
        print(f"📡 Response status: {r.status_code}")
        print(f"📊 Response length: {len(r.text)} characters")
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code}")
            return []
            
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Debug: Save HTML for inspection
        try:
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(r.text[:10000])  # First 10k chars
            print("💾 Debug HTML saved to debug.html")
        except:
            pass
        
        results = []
        
        # Multiple scraping strategies
        print("🎯 Trying multiple scraping strategies...")
        
        # Strategy 1: Look for product cards/containers
        product_containers = soup.find_all(['div', 'article', 'section'], 
            class_=lambda x: x and any(term in x.lower() 
            for term in ['product', 'deal', 'item', 'card']))
        
        print(f"📦 Found {len(product_containers)} product containers")
        
        for container in product_containers[:limit]:
            links = container.find_all('a', href=True)
            for a in links:
                href = a.get('href', '').strip()
                text = a.get_text(strip=True)
                
                if href and self.is_valid_product_link(href):
                    results.append({
                        'title': text[:100] if text else 'Deal Available',
                        'url': self.normalize_url(href)
                    })
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break
        
        # Strategy 2: Direct anchor search (fallback)
        if len(results) < 5:
            print("🔄 Trying fallback anchor search...")
            anchors = soup.select('a[href]')
            print(f"🔗 Found {len(anchors)} total anchors")
            
            for a in anchors:
                href = a.get('href', '').strip()
                text = a.get_text(strip=True)
                
                if href and self.is_valid_product_link(href):
                    results.append({
                        'title': text[:100] if text else 'Deal Available',
                        'url': self.normalize_url(href)
                    })
                    if len(results) >= limit:
                        break
        
        # Strategy 3: Look for specific deal patterns
        if len(results) < 5:
            print("🎲 Trying pattern-based search...")
            deal_patterns = ['deal', 'offer', 'sale', 'discount', 'cashback']
            for pattern in deal_patterns:
                elements = soup.find_all(text=lambda t: t and pattern.lower() in t.lower())
                for elem in elements[:10]:
                    parent = elem.parent
                    if parent:
                        link = parent.find('a', href=True)
                        if link and self.is_valid_product_link(link.get('href', '')):
                            results.append({
                                'title': elem.strip()[:100] or 'Special Deal',
                                'url': self.normalize_url(link.get('href'))
                            })
                            if len(results) >= limit:
                                break
                if len(results) >= limit:
                    break
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for item in results:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_results.append(item)
        
        print(f"✅ Found {len(unique_results)} unique deals")
        return unique_results
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Scrape error: {e}")
        import traceback
        traceback.print_exc()
    
    return []

def is_valid_product_link(self, href):
    """Check if URL is a valid product link"""
    if not href or href.startswith('#') or href.startswith('mailto:'):
        return False
    
    # Check for retailer domains or product patterns
    valid_patterns = [
        '/hp-', '/product-', '/p/', '/deal', '/offer',
        'flipkart.com', 'amazon.in', 'myntra.com', 'ajio.com',
        'nykaa.com', 'meesho.com', 'paytmmall.com'
    ]
    
    return any(pattern in href.lower() for pattern in valid_patterns)

def normalize_url(self, url):
    """Normalize and clean URLs"""
    if url.startswith('/'):
        url = 'https://earnkaro.com' + url
    return url.strip()

def make_affiliate(url):
    """Enhanced affiliate tagging"""
    if not url:
        return url
    
    # Amazon affiliate
    if 'amazon.in' in url and 'tag=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}tag=techb0ad-21"
    
    # Flipkart affiliate
    if 'flipkart.com' in url and 'affid=' not in url:
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}affid=mayur0424"
    
    return url

def format_message(item):
    """Format message for Telegram"""
    title = item.get('title', 'Deal').strip()
    url = item.get('affiliate') or item.get('url')
    
    # Clean title
    if len(title) > 80:
        title = title[:77] + "..."
    
    # Add emojis based on content
    emoji = "🔥"
    if any(word in title.lower() for word in ['amazon', 'prime']):
        emoji = "📦"
    elif any(word in title.lower() for word in ['flipkart', 'big billion']):
        emoji = "🛍️"
    elif any(word in title.lower() for word in ['fashion', 'clothing', 'myntra']):
        emoji = "👗"
    
    return f"{emoji} <b>{title}</b>\n🛒 <a href='{url}'>Get Deal</a>\n\n💡 <i>Exclusive offers daily!</i>"

def main_bot_function():
    """Main bot loop"""
    print("🚀 Bot started. Using randomized intervals.")
    
    # Test telegram connection first
    if not test_telegram_connection():
        print("❌ Cannot connect to Telegram. Check your tokens!")
        return
    
    consecutive_failures = 0
    max_failures = 5
    
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"🔄 Starting new scraping cycle...")
            
            pool = scrape_today_best(limit=50)
            
            if not pool:
                consecutive_failures += 1
                print(f'❌ No deals found (failure #{consecutive_failures})')
                
                if consecutive_failures >= max_failures:
                    print("🚨 Too many consecutive failures. Sending alert...")
                    alert_msg = "⚠️ Bot Alert: No deals found for extended period. Please check!"
                    send_telegram_text(alert_msg)
                    consecutive_failures = 0  # Reset after sending alert
                
                print('😴 Sleeping 10 minutes before retry...')
                time.sleep(600)
                continue
            
            # Reset failure counter on success
            consecutive_failures = 0
            
            # Random shuffle and pick per batch
            random.shuffle(pool)
            batch = pool[:POSTS_PER_BATCH]
            
            print(f"📤 Posting {len(batch)} deals...")
            
            successful_posts = 0
            for i, item in enumerate(batch, 1):
                item['affiliate'] = make_affiliate(item['url'])
                msg = format_message(item)
                
                if send_telegram_text(msg):
                    successful_posts += 1
                    print(f"✅ Posted deal {i}/{len(batch)}")
                else:
                    print(f"❌ Failed to post deal {i}/{len(batch)}")
                
                time.sleep(random.randint(3, 8))  # Random delay between posts
            
            print(f"📊 Successfully posted {successful_posts}/{len(batch)} deals")
            
            wait_minutes = random.randint(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN)
            print(f"⏰ Cycle finished — sleeping for {wait_minutes} minutes.")
            time.sleep(wait_minutes * 60)
            
        except KeyboardInterrupt:
            print("👋 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(300)  # Wait 5 minutes before retry

# Flask server for Railway
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 EarnKaro Affiliate Bot</h1>
    <p>✅ Bot is running!</p>
    <p>📊 Check logs for activity</p>
    """

@app.route('/status')
def status():
    return {"status": "active", "service": "earnkaro-affiliate-bot"}

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == '__main__':
    # Start bot in background thread
    threading.Thread(target=main_bot_function, daemon=True).start()
    # Run Flask in main thread
    run_flask()
