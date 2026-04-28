import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_TOKEN
from handlers.commands import start, profile_handler, back_main, fandoms_menu, join_fandom_handler
from handlers.actions import (
    gacha_handler, my_idols_handler, manage_idol_handler, 
    comeback_callback, sponsor_callback, accept_sponsor_callback,
    tour_callback, claim_global_handler
)
from services.scheduler_tasks import process_all_maintenances
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import init_db
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(application):
    await init_db()
    # Setup Scheduler for Maintenance
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_all_maintenances, 'interval', hours=24)
    
    # Global Events (Random chance every hour)
    from services.events import trigger_random_global_event
    scheduler.add_job(trigger_random_global_event, 'cron', hour='*', minute='30', args=[application])
    
    scheduler.start()
    print("🚀 Database & Scheduler initialized")

def main():
    # CONFIGURACIÓN PROXY PARA PYTHONANYWHERE
    proxy_url = "http://proxy.server:3128"
    
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .proxy(proxy_url)
        .get_updates_proxy(proxy_url)
        .post_init(post_init)
        .build()
    )

    # Comandos
    application.add_handler(CommandHandler("start", start))
    
    # Callbacks (Registro de botones)
    application.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile$"))
    application.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(gacha_handler, pattern="^gacha_pull$"))
    application.add_handler(CallbackQueryHandler(my_idols_handler, pattern="^my_idols$"))
    application.add_handler(CallbackQueryHandler(manage_idol_handler, pattern="^manage_"))
    application.add_handler(CallbackQueryHandler(comeback_callback, pattern="^comeback_"))
    application.add_handler(CallbackQueryHandler(sponsor_callback, pattern="^sponsor_"))
    application.add_handler(CallbackQueryHandler(accept_sponsor_callback, pattern="^acc_sp_"))
    application.add_handler(CallbackQueryHandler(tour_callback, pattern="^tour_"))
    application.add_handler(CallbackQueryHandler(claim_global_handler, pattern="^claim_global_"))
    application.add_handler(CallbackQueryHandler(fandoms_menu, pattern="^fandoms_menu$"))
    application.add_handler(CallbackQueryHandler(join_fandom_handler, pattern="^join_"))
    
    print("🤖 Bot is running with Proxy, Fandoms and NSFW Events...")
    application.run_polling()

if __name__ == "__main__":
    main()
