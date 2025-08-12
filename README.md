# EarnKaro Telegram Affiliate Bot - Render Worker Package

This package runs as a **Background Worker** on Render and periodically scrapes EarnKaro's "Today's Best Deals" page,
converts links with simple affiliate tagging for Amazon/Flipkart, and posts to a Telegram chat/channel.

## Files
- main.py            -> main worker script
- requirements.txt   -> Python dependencies
- runtime.txt        -> Python version for Render (3.12.3)
- render.yaml        -> Render service definition (worker)
- .env.example       -> example environment variables

## Deploy on Render
1. Create a new **Private Repo** or upload this ZIP via Render dashboard (Static/Other -> Upload).
2. In Render, go to **New → Web Service** or use **Deploy from Repo**. (If you upload ZIP directly, choose "Private Service" and then choose type Worker)
3. Ensure the service type is **Worker** (background process). The included `render.yaml` is configured for a worker.
4. Set Environment Variables in Render dashboard (or create a .env locally):
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your channel username (e.g., @FlipkartAmazonAjioSale) or numeric chat id
   - Optional: POSTS_PER_BATCH, MIN_INTERVAL_MIN, MAX_INTERVAL_MIN
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python main.py`

## Notes
- For EarnKaro pages that require login/OTP, this simple scraper may not reach every link; for deeper automation (profit links creation) Playwright automation and persistent storage of login state is recommended.
- Rotate tokens & passwords if leaked. Keep `.env` out of public repos.
