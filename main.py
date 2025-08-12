import os
import time
import random
import requests
from bs4 import BeautifulSoup

# Telegram bot token & chat ID from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://earnkaro.com/deals"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def scrape_deals():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        deals = soup.find_all("div", class_="deal-card")[:5]  # Top 5 deals
        for deal in deals:
            title = deal.find("h3").get_text(strip=True) if deal.find("h3") else "No Title"
            link = deal.find("a")["href"] if deal.find("a") else "#"
            message = f"<b>{title}</b>\n{link}"
            send_telegram_message(message)
    except Exception as e:
        print(f"Error scraping deals: {e}")

if __name__ == "__main__":
    print("Bot started...")
    while True:
        scrape_deals()
        wait_time = random.randint(1200, 3000)  # 20-50 min random interval
        print(f"Waiting {wait_time//60} min before next run...")
        time.sleep(wait_time)
