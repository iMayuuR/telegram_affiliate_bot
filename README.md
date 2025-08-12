# EarnKaro Telegram Bot

This bot scrapes top deals from EarnKaro and sends them to a Telegram chat at random intervals (20–50 minutes).  
Deployable on [Render](https://render.com) with no manual input.

## Steps to Deploy on Render

1. Create a **new Web Service** on Render.
2. Connect your GitHub repo OR upload this ZIP directly.
3. In **Environment Variables**, add:
   - `TELEGRAM_BOT_TOKEN` → Your bot token from BotFather.
   - `TELEGRAM_CHAT_ID` → Your chat/group ID.
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Click **Deploy**.

Bot will run forever and send updates every 20–50 minutes.

## Requirements
- Python 3.12.3
- Libraries in `requirements.txt`
