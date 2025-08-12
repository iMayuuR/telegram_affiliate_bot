import time
import random
import requests
from bs4 import BeautifulSoup
import telegram

# --- CONFIG ---
TELEGRAM_BOT_TOKEN = "7435299998:AAHZqIhZ5ftr_WfM4ToIYLnbl4cFdvp9hUU"
TELEGRAM_CHANNEL = "@FlipkartAmazonAjioSale"

AMAZON_TAG = "techb0ad-21"
FLIPKART_ID = "mayur0424"
FLIPKART_TOKEN = "2b9ab31105104481b365fc65a3da821a"

EARNKARO_EMAIL = "mayur0424@gmail.com"
EARNKARO_PASS = "M4yuur7!!5"
EARNKARO_USERID = "4496103"

CATEGORIES = ["Electronics", "Fashion", "Mobiles & Tablets", "Home & Furniture", "TVs & Appliances"]

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def scrape_earnkaro():
    url = "https://earnkaro.com/top-selling-products/today-best-deals"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for a in soup.select("a"):
        link = a.get("href")
        if link and ("flipkart.com" in link or "amazon.in" in link):
            products.append(link)
    return list(set(products))

def make_affiliate_link(url):
    if "amazon.in" in url:
        if "tag=" not in url:
            if "?" in url:
                url += f"&tag={AMAZON_TAG}"
            else:
                url += f"?tag={AMAZON_TAG}"
    elif "flipkart.com" in url:
        if "affid=" not in url:
            if "?" in url:
                url += f"&affid={FLIPKART_ID}"
            else:
                url += f"?affid={FLIPKART_ID}"
    return url

def post_to_telegram(message):
    bot.send_message(chat_id=TELEGRAM_CHANNEL, text=message, disable_web_page_preview=False)

def main():
    while True:
        links = scrape_earnkaro()
        for link in links:
            aff_link = make_affiliate_link(link)
            post_to_telegram(aff_link)
            time.sleep(random.randint(10, 20))  # Small gap between posts
        
        wait_minutes = random.randint(45, 90)
        time.sleep(wait_minutes * 60)

if __name__ == "__main__":
    main()
