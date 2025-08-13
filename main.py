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

def scrape_today_best(limit=20):
    """Enhanced scraping with debug and multiple strategies"""
    print(f"🔍 Starting to scrape: {EARNKARO_TODAY_URL}")
    
    # Better headers to avoid detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        r = requests.get(EARNKARO_TODAY_URL, headers=headers, timeout=30)
        print(f"📡 Status: {r.status_code}, Length: {len(r.text)}")
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Debug: Save first 5000 chars to see what we're getting
        try:
            with open('debug_sample.html', 'w', encoding='utf-8') as f:
                f.write(r.text[:5000])
            print("💾 Debug sample saved")
        except:
            pass
        
        results = []
        
        # Strategy 1: Very broad search for any product-related links
        all_links = soup.find_all('a', href=True)
        print(f"🔗 Found {len(all_links)} total links")
        
        # Much broader patterns - EarnKaro specific
        broad_patterns = [
            # Original patterns
            '/hp-', '/product-', '/p/', 'flipkart.com', 'amazon.in', 'myntra.com', 'ajio.com',
            # Additional retailer patterns
            'nykaa.com', 'meesho.com', 'paytm', 'snapdeal', 'shopclues',
            'tatacliq', 'reliance', 'jiomart', 'bigbasket', 'grofers',
            # Deal-specific patterns
            '/deal', '/offer', '/sale', '/discount', '/cashback',
            # EarnKaro internal patterns
            'earnkaro.com/hp', 'earnkaro.com/deal', 'earnkaro.com/link',
            # Common e-commerce patterns
            '/buy/', '/shop/', '/store/', '/product/',
        ]
        
        for a in all_links:
            href = (a.get('href') or '').strip()
            text = (a.get_text() or '').strip()
            
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            
            # Check against broad patterns
            if any(pattern in href.lower() for pattern in broad_patterns):
                # Normalize URL
                if href.startswith('/'):
                    href = 'https://earnkaro.com' + href
                
                results.append({
                    'title': text[:80] if text else 'Special Deal',
                    'url': href
                })
                
                if len(results) >= limit:
                    break
        
        # Strategy 2: If still no results, try text-based approach
        if len(results) < 3:
            print("🆘 Trying text-based approach...")
            
            # Look for elements with deal-related text
            deal_texts = ['deal', 'offer', 'sale', 'discount', '% off', 'cashback', 'save']
            
            for text_pattern in deal_texts:
                elements = soup.find_all(text=lambda t: t and text_pattern.lower() in t.lower())
                
                for elem in elements[:20]:  # Limit to avoid too many
                    # Find parent link
                    parent = elem.parent
                    for _ in range(3):  # Go up 3 levels
                        if parent and parent.find('a', href=True):
                            link = parent.find('a', href=True)
                            href = link.get('href', '').strip()
                            
                            if href and not href.startswith('#'):
                                if href.startswith('/'):
                                    href = 'https://earnkaro.com' + href
                                
                                results.append({
                                    'title': elem.strip()[:80] or 'Deal Found',
                                    'url': href
                                })
                                
                                if len(results) >= limit:
                                    break
                            break
                        parent = parent.parent if parent else None
                    
                    if len(results) >= limit:
                        break
                
                if len(results) >= limit:
                    break
        
        # Strategy 3: Emergency - grab ANY external links
        if len(results) < 2:
            print("🚨 Emergency: grabbing any external links...")
            
            for a in all_links:
                href = (a.get('href') or '').strip()
                text = (a.get_text() or '').strip()
                
                # Any external link (not internal navigation)
                if (href and 
                    not href.startswith('#') and 
                    not href.startswith('mailto:') and
                    not any(skip in href.lower() for skip in ['login', 'register', 'about', 'contact', 'privacy', 'terms'])):
                    
                    if href.startswith('/'):
                        href = 'https://earnkaro.com' + href
                    
                    results.append({
                        'title': text[:80] if text else 'Available Deal',
                        'url': href
                    })
                    
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
        
        # Debug: Print first few deals
        for i, deal in enumerate(unique_results[:3]):
            print(f"🔍 Deal {i+1}: {deal['title'][:50]}... -> {deal['url'][:50]}...")
        
        return unique_results
        
    except Exception as e:
        print(f'❌ Scraping error: {e}')
        import traceback
        traceback.print_exc()
        return []

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
    
    # Clean and shorten title
    if len(title) > 80:
        title = title[:77] + "..."
    
    # Dynamic emoji based on content
    emoji = "🔥"
    if any(word in title.lower() for word in ['amazon', 'prime']):
        emoji = "📦"
    elif any(word in title.lower() for word in ['flipkart', 'big billion']):
        emoji = "🛍️"
    elif any(word in title.lower() for word in ['fashion', 'clothing', 'myntra']):
        emoji = "👗"
    elif any(word in title.lower() for word in ['mobile', 'phone', 'smartphone']):
        emoji = "📱"
    elif any(word in title.lower() for word in ['electronics', 'gadget']):
        emoji = "⚡"
    
    return f"{emoji} <b>{title}</b>\n🛒 <a href='{url}'>Get Deal Now</a>\n\n💡 <i>Limited time offer!</i>"

def test_scraping():
    """Test function to debug scraping"""
    print("🧪 Testing scraping function...")
    deals = scrape_today_best(10)
    
    if deals:
        print(f"✅ Test successful - Found {len(deals)} deals:")
        for i, deal in enumerate(deals[:5], 1):
            print(f"{i}. {deal['title'][:60]}...")
    else:
        print("❌ Test failed - No deals found")
        
    return len(deals) > 0

def main_bot_function():
    """Main bot loop with enhanced error handling"""
    print("🚀 Bot started!")
    
    # Test scraping first
    if not test_scraping():
        print("⚠️ Scraping test failed, but continuing...")
    
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Starting new scraping cycle...")
            
            pool = scrape_today_best(limit=50)
            
            if not pool:
                consecutive_failures += 1
                print(f'❌ No deals found (attempt {consecutive_failures}/{max_failures})')
                
                if consecutive_failures >= max_failures:
                    # Send alert and try different approach
                    alert_msg = "🚨 Bot Alert: Multiple scraping failures. Investigating..."
                    send_telegram_text(alert_msg)
                    consecutive_failures = 0
                
                print('😴 Sleeping 10 minutes before retry...')
                time.sleep(600)  # 10 minutes
                continue
            
            # Reset failure counter on success
            consecutive_failures = 0
            
            # Random shuffle and pick batch
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
                
                # Random delay between posts
                time.sleep(random.randint(3, 8))
            
            print(f"📊 Posted {successful_posts}/{len(batch)} deals successfully")
            
            # Random wait before next cycle
            wait_minutes = random.randint(MIN_INTERVAL_MIN, MAX_INTERVAL_MIN)
            print(f"⏰ Cycle completed - sleeping for {wait_minutes} minutes")
            time.sleep(wait_minutes * 60)
            
        except KeyboardInterrupt:
            print("👋 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(300)  # Wait 5 minutes before retry

# Flask server for Railway/Render
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 EarnKaro Affiliate Bot</h1>
    <p>✅ Bot is running successfully!</p>
    <p>📊 Check logs for activity details</p>
    <p>🔄 Auto-posting deals every 30-75 minutes</p>
    """

@app.route('/test')
def test_route():
    """Test endpoint to check scraping"""
    deals = scrape_today_best(5)
    return {
        "status": "success",
        "deals_found": len(deals),
        "sample_deals": deals[:3]
    }

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == '__main__':
    # Start bot in background thread
    threading.Thread(target=main_bot_function, daemon=True).start()
    
    # Run Flask in main thread
    run_flask()
