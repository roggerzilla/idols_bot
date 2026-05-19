"""
Handlers de comandos usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
from storage import get_user, create_user, add_group, get_all_groups, get_user_idols
from utils.formatter import format_user_profile
from config import ADMIN_IDS, PERSONAL_EVENTS
from services.events import create_and_broadcast_event
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    chat = update.effective_chat

    # Crear usuario si no existe
    user = get_user(user_tg.id)
    if not user:
        create_user(user_tg.id, username=user_tg.username or user_tg.first_name)
        user = get_user(user_tg.id)

    # Fallback por si user sigue siendo None
    if not user:
        user = {
            "id": user_tg.id,
            "username": user_tg.username or user_tg.first_name or "Unknown",
            "points": 1000,
            "wins": 0,
            "last_maintenance_check": datetime.utcnow().isoformat(),
            "idols": []
        }

    # Registrar grupo si es nuevo
    if chat.type in ("group", "supergroup"):
        groups = get_all_groups()
        if chat.id not in groups:
            add_group(chat.id, title=chat.title or "")

    kb = [
        [InlineKeyboardButton("👤 Perfil", callback_data=f"profile_{user_tg.id}"),
         InlineKeyboardButton("📖 Ayuda", callback_data=f"help_game_{user_tg.id}")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data=f"idols_0_{user_tg.id}"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data=f"gacha_{user_tg.id}")],
        [InlineKeyboardButton("🏪 Mercado", callback_data=f"market_0_{user_tg.id}"),
         InlineKeyboardButton("🧪 Fusión", callback_data=f"fusion_main_{user_tg.id}")],
        [InlineKeyboardButton("🧬 Evolucionar", callback_data=f"evo_main_{user_tg.id}"),
         InlineKeyboardButton("💰 Ganar Puntos", callback_data=f"help_pts_{user_tg.id}")],
    ]

    # Retry logic for flaky PythonAnywhere proxy
    for _ in range(3):
        try:
            await update.message.reply_text(
                f"🏠 <b>Panel de CEO — {user.get('username', user_tg.username)}</b>\n💰 Puntos: <code>{user.get('points', 0)}</code>",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.HTML
            )
            break
        except Exception as e:
            if "503" in str(e):
                import asyncio
                await asyncio.sleep(1)
                continue
            raise e


async def admin_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    ft = context.args[0].lower() if context.args else None
    eid = await create_and_broadcast_event(context.application, force_type=ft)

    if eid:
        await update.message.reply_text(f"✅ Evento #{eid} lanzado.")
    else:
        await update.message.reply_text("❌ Error al crear evento.")


async def admin_personal_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fuerza un evento personal para el admin (para pruebas)"""
    uid = update.effective_user.id

    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    idols = get_user_idols(uid)
    if not idols:
        await update.message.reply_text("❌ No tienes idols para el evento.")
        return

    # Priorizar la que se está viendo, o elegir una al azar si no
    idx = context.user_data.get("current_idol_idx")
    if idx is None or idx >= len(idols):
        idx = random.randint(0, len(idols) - 1)
    
    idol = idols[idx]

    event = random.choice(PERSONAL_EVENTS)
    event_text = (
        f"⚡ <b>FORZAR EVENTO PERSONAL (Admin)</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>{idol['name'].upper()}</b>\n\n"
        f"{event['desc']}\n\n"
        f"💰 Costo: <code>{event['cost_points']} pts</code>\n"
        f"📉 Talento: <code>-{event['stat_loss']}</code>\n"
        f"❤️ Moral: <code>+{event['moral_gain']}</code>\n"
        f"⚡ Energía: <code>+{event['energy_gain']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    kb = [
        [InlineKeyboardButton("✅ Permitir", callback_data=f"pev_acc_{event['id']}_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("❌ Denegar", callback_data=f"idols_{idx}_{uid}")]
    ]
    await update.message.reply_text(event_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


async def admin_give_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de admin para dar puntos a un usuario: /dar_puntos <user_id> <amount>"""
    uid = update.effective_user.id
    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("💡 Uso: `/dar_puntos <user_id> <cantidad>`", parse_mode=ParseMode.HTML)
        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        
        from storage import add_points, get_user
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("❌ Usuario no encontrado.")
            return

        add_points(target_id, amount)
        await update.message.reply_text(f"✅ Se han otorgado <b>{amount} pts</b> al CEO <code>{user.get('username')}</code>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Los argumentos deben ser números.")


async def admin_give_idol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de admin para dar una idol: /dar_idol <user_id> <id_or_name> [era]"""
    uid = update.effective_user.id
    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("💡 Uso: `/dar_idol <user_id> <id_o_nombre> [era]`", parse_mode=ParseMode.HTML)
        return

    try:
        target_id = int(context.args[0])
        identifier = context.args[1]
        era_filter = context.args[2] if len(context.args) > 2 else None
        
        from storage import get_all_templates, create_idol, get_user
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("❌ Usuario no encontrado.")
            return

        templates = get_all_templates()
        found_template = None

        # 1. Buscar por ID
        if identifier.isdigit() and identifier in templates:
            found_template = templates[identifier]
        
        # 2. Buscar por nombre
        if not found_template:
            matches = []
            for tid, t in templates.items():
                if t["name"].lower() == identifier.lower().replace("_", " "):
                    if era_filter:
                        if t.get("era", "").lower() == era_filter.lower().replace("_", " "):
                            matches.append(t)
                    else:
                        matches.append(t)
            
            if not matches:
                await update.message.reply_text(f"❌ No se encontró ninguna idol llamada '{identifier}'.")
                return
            elif len(matches) > 1:
                text = f"⚠️ Se encontraron {len(matches)} versiones. Sé más específico:\n"
                for m in matches:
                    text += f"• ID: <code>{m['id']}</code> | Era: {m.get('era', 'Standard')}\n"
                await update.message.reply_text(text, parse_mode=ParseMode.HTML)
                return
            else:
                found_template = matches[0]

        # Crear Idol
        new_idol = create_idol(
            user_id=target_id,
            template_id=found_template["id"],
            name=found_template["name"],
            group_name=found_template["group_name"],
            rarity=found_template["rarity"],
            base_vocal=found_template["base_vocal"],
            base_dance=found_template["base_dance"],
            base_rap=found_template["base_rap"],
            era=found_template.get("era", "Standard")
        )

        await update.message.reply_text(
            f"✅ ¡Éxito! Se ha asignado <b>{found_template['name']}</b> ({found_template['rarity']}) a <code>{user.get('username')}</code>\n"
            f"🆔 ID de instancia: <code>{new_idol['id']}</code>",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando simple para que el usuario obtenga su propio ID"""
    uid = update.effective_user.id
    await update.message.reply_text(
        f"🆔 Tu Telegram ID es: <code>{uid}</code>\n"
        f"<i>(Haz click en el número para copiarlo)</i>",
        parse_mode=ParseMode.HTML
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = (
        "📖 <b>GUÍA DEL CEO DE IDOLS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎰 <b>Gacha:</b> Consigue nuevas idols por 500 pts.\n"
        "📀 <b>Comebacks:</b> Lanza álbumes. Dependen de Vocal, Dance y Rap.\n"
        "💪 <b>Entrenar:</b> Mejora las stats de tu idol por 200 pts.\n"
        "🔞 <b>Stats NSFW:</b> Influyen en los premios de Eventos Globales.\n"
        "✈️ <b>World Tour:</b> Envía a tu idol de gira (12h) para ganar puntos pasivos.\n"
        "🏪 <b>Mercado:</b> Compra y vende idols con otros jugadores.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👑 <b>COMANDOS DE ADMIN:</b>\n"
        "/evento — Lanza evento aleatorio\n"
        "/evento nsfw — Fuerza evento NSFW\n"
        "/evento charity — Fuerza evento de caridad"
    )
    await update.message.reply_text(t, parse_mode=ParseMode.HTML)


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[1]) if len(parts) > 1 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu perfil.", show_alert=True)
        return

    user = get_user(q.from_user.id)
    if not user:
        create_user(q.from_user.id)
        user = get_user(q.from_user.id)

    # Contar idols del usuario
    from storage import get_user_idols
    idol_count = len(get_user_idols(q.from_user.id))

    text = format_user_profile(user, idol_count)

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode=ParseMode.HTML
    )


async def get_photo_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Herramienta de admin: responde con el file_id de cualquier foto enviada"""
    uid = update.effective_user.id
    from config import ADMIN_IDS, TEST_GROUP_ID
    if ADMIN_IDS and uid not in ADMIN_IDS:
        return
    chat_id = update.effective_chat.id if update.effective_chat else None
    if TEST_GROUP_ID and chat_id != TEST_GROUP_ID and chat_id != uid:
        return

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(
            f"🖼 <b>FILE ID DETECTADO</b>\n\n<code>{file_id}</code>\n\n"
            f"<i>Copia este código para tu templates.json</i>",
            parse_mode=ParseMode.HTML
        )


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes usar el menú de otro CEO.", show_alert=True)
        return

    await q.answer()

    user = get_user(q.from_user.id)
    if not user:
        create_user(q.from_user.id)
        user = get_user(q.from_user.id)

    kb = [
        [InlineKeyboardButton("👤 Perfil", callback_data=f"profile_{q.from_user.id}"),
         InlineKeyboardButton("📖 Ayuda", callback_data=f"help_game_{q.from_user.id}")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data=f"idols_0_{q.from_user.id}"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data=f"gacha_{q.from_user.id}")],
        [InlineKeyboardButton("🏪 Mercado", callback_data=f"market_0_{q.from_user.id}"),
         InlineKeyboardButton("🧪 Fusión", callback_data=f"fusion_main_{q.from_user.id}")],
        [InlineKeyboardButton("🧬 Evolucionar", callback_data=f"evo_main_{q.from_user.id}"),
         InlineKeyboardButton("💰 Ganar Puntos", callback_data=f"help_pts_{q.from_user.id}")],
    ]

    for _ in range(3):
        try:
            await q.edit_message_text(
                f"🏠 <b>Panel de CEO</b>\n💰 Puntos: <code>{user.get('points', 0)}</code>",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.HTML
            )
            break
        except Exception as e:
            if "503" in str(e):
                import asyncio
                await asyncio.sleep(1)
                continue
            raise e
