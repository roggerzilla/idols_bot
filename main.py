"""
Bot principal usando almacenamiento JSON.
"""

import logging
import asyncio
import random
import time
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_TOKEN
from handlers.commands import start, profile_handler, back_main, admin_evento, help_command, admin_personal_event, admin_give_points, admin_give_idol
from handlers.actions import (
    gacha_handler, idols_handler, comeback_handler,
    train_menu_handler, train_execute_handler, interact_menu_handler, interact_execute_handler,
    idol_submenu_handler,
    rest_handler, tour_handler, sell_handler, list_sell_handler,
    market_handler, buy_handler, claim_handler, noop_handler, help_points_handler,
    select_idol_for_event, use_idol_for_event, nsfw_info_handler, nsfw_train_handler,
    help_game_handler, fusion_menu_handler, fusion_select_slot_handler,
    fusion_pick_idol_handler, fusion_execute_handler, fusion_clear_handler,
    personal_event_handler
)
from services.economy import process_maintenance
from services.scheduler_tasks import process_all_maintenances
from services.events import create_and_broadcast_event
from storage import init_storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.ERROR) # Silenciar errores de reconexión ruidosos

async def scheduled_random_event(application):
    """Chance aleatoria de lanzar un evento (cada 30 min)"""
    try:
        # Usamos una forma más segura de verificar si el bot está listo
        if not application:
            return
            
        if random.random() < 0.3:
            await create_and_broadcast_event(application)
            logging.info("🎲 Evento global aleatorio lanzado!")
    except Exception as e:
        logging.error(f"Error en scheduled_random_event: {e}")

async def post_init(application):
    """Inicializa el sistema JSON y scheduler."""
    init_storage()
    if 'scheduler' not in application.bot_data:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(process_all_maintenances, 'interval', hours=24)
        scheduler.add_job(scheduled_random_event, 'interval', minutes=30, args=[application])
        scheduler.start()
        application.bot_data['scheduler'] = scheduler
        print("🚀 JSON Storage & Scheduler initialized")

def create_application():
    """Crea y configura una nueva instancia de la aplicación"""
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .post_init(post_init)
        .build()
    )

    # Registro de comandos y handlers (reutilizado)
    application.add_handler(CommandHandler("startidols", start))
    application.add_handler(CommandHandler("evento", admin_evento))
    application.add_handler(CommandHandler("ayuda", help_command))
    application.add_handler(CommandHandler("mievento", admin_personal_event))
    application.add_handler(CommandHandler("dar_puntos", admin_give_points))
    application.add_handler(CommandHandler("dar_idol", admin_give_idol))

    application.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile_\\d+$"))
    application.add_handler(CallbackQueryHandler(back_main, pattern="^back_main_\\d+$"))
    application.add_handler(CallbackQueryHandler(gacha_handler, pattern="^gacha_\\d+$"))
    application.add_handler(CallbackQueryHandler(idols_handler, pattern=r"^idols_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(idol_submenu_handler, pattern=r"^ism_"))
    application.add_handler(CallbackQueryHandler(comeback_handler, pattern=r"^cb_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(train_menu_handler, pattern=r"^tr_menu_"))
    application.add_handler(CallbackQueryHandler(train_execute_handler, pattern=r"^tr_exe_"))
    application.add_handler(CallbackQueryHandler(interact_menu_handler, pattern=r"^int_menu_"))
    application.add_handler(CallbackQueryHandler(interact_execute_handler, pattern=r"^int_exe_"))
    application.add_handler(CallbackQueryHandler(personal_event_handler, pattern=r"^pev_acc_"))
    application.add_handler(CallbackQueryHandler(rest_handler, pattern=r"^rs_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(tour_handler, pattern=r"^tour_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(sell_handler, pattern=r"^sell_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(list_sell_handler, pattern=r"^listsell_"))
    application.add_handler(CallbackQueryHandler(market_handler, pattern=r"^market_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(buy_handler, pattern=r"^buy_\d+$"))
    application.add_handler(CallbackQueryHandler(claim_handler, pattern=r"^claim_\d+(_\d+)?$"))
    application.add_handler(CallbackQueryHandler(select_idol_for_event, pattern=r"^sel_event_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(use_idol_for_event, pattern=r"^use_idol_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(nsfw_info_handler, pattern=r"^nsfw_info_\d+_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(nsfw_train_handler, pattern=r"^nsfw_tr_"))
    application.add_handler(CallbackQueryHandler(help_points_handler, pattern="^help_pts_\\d+$"))
    application.add_handler(CallbackQueryHandler(help_game_handler, pattern="^help_game_\\d+$"))
    application.add_handler(CallbackQueryHandler(fusion_menu_handler, pattern="^fusion_main_\\d+$"))
    application.add_handler(CallbackQueryHandler(fusion_select_slot_handler, pattern="^fus_sel_"))
    application.add_handler(CallbackQueryHandler(fusion_pick_idol_handler, pattern="^fus_pick_"))
    application.add_handler(CallbackQueryHandler(fusion_execute_handler, pattern="^fus_exe_"))
    application.add_handler(CallbackQueryHandler(fusion_clear_handler, pattern="^fus_clear_"))
    application.add_handler(CallbackQueryHandler(noop_handler, pattern="^noop$"))

    return application

def main():
    while True:
        application = None
        try:
            application = create_application()
            logging.info("🤖 Bot iniciado. Esperando conexión...")
            # drop_pending_updates=True evita que el bot responda a mensajes viejos al arrancar
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logging.error(f"❌ Error crítico en el bucle principal: {e}")
            
            # Limpieza profunda antes de reintentar
            if application:
                try:
                    if 'scheduler' in application.bot_data:
                        application.bot_data['scheduler'].shutdown(wait=False)
                except:
                    pass
            
            logging.info("📡 Reintentando en 20 segundos...")
            time.sleep(20)

if __name__ == "__main__":
    main()
