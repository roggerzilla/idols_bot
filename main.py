import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.request import HTTPXRequest
from config import TELEGRAM_TOKEN
from handlers.commands import start, profile_handler, back_main, admin_evento, help_command
from handlers.actions import (
    gacha_handler, idols_handler, comeback_handler, train_handler,
    greet_handler, rest_handler, tour_handler, sell_handler, list_sell_handler,
    market_handler, buy_handler, claim_handler, noop_handler
)
from services.scheduler_tasks import process_all_maintenances
from services.events import create_and_broadcast_event
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import init_db
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def scheduled_random_event(application):
    """Random chance to trigger event (called every 30 min)"""
    if random.random() < 0.3:  # 30% chance each run
        await create_and_broadcast_event(application)
        print("🎲 Random global event triggered!")

async def post_init(application):
    await init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_all_maintenances, 'interval', hours=24)
    scheduler.add_job(scheduled_random_event, 'interval', minutes=30, args=[application])
    scheduler.start()
    print("🚀 Database & Scheduler initialized")

def main():
    proxy_url = "http://proxy.server:3128"
    
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .proxy(proxy_url)
        .get_updates_proxy(proxy_url)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .post_init(post_init)
        .build()
    )

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("evento", admin_evento))
    application.add_handler(CommandHandler("ayuda", help_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile$"))
    application.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(gacha_handler, pattern="^gacha$"))
    application.add_handler(CallbackQueryHandler(idols_handler, pattern=r"^idols_\d+$"))
    application.add_handler(CallbackQueryHandler(comeback_handler, pattern=r"^cb_\d+$"))
    application.add_handler(CallbackQueryHandler(train_handler, pattern=r"^tr_\d+$"))
    application.add_handler(CallbackQueryHandler(greet_handler, pattern=r"^gr_\d+$"))
    application.add_handler(CallbackQueryHandler(rest_handler, pattern=r"^rs_\d+$"))
    application.add_handler(CallbackQueryHandler(tour_handler, pattern=r"^tour_\d+$"))
    application.add_handler(CallbackQueryHandler(sell_handler, pattern=r"^sell_\d+$"))
    application.add_handler(CallbackQueryHandler(list_sell_handler, pattern=r"^listsell_"))
    application.add_handler(CallbackQueryHandler(market_handler, pattern=r"^market_\d+$"))
    application.add_handler(CallbackQueryHandler(buy_handler, pattern=r"^buy_\d+$"))
    application.add_handler(CallbackQueryHandler(claim_handler, pattern=r"^claim_\d+$"))
    application.add_handler(CallbackQueryHandler(noop_handler, pattern="^noop$"))

    print("🤖 Bot running: Gacha, Market, Events, Admin commands active")
    application.run_polling(bootstrap_retries=-1)

if __name__ == "__main__":
    main()
