"""
Handlers usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import random
import asyncio
import time
from datetime import datetime
from storage import (
    get_user, update_user, add_points, deduct_points,
    get_all_idols, get_user_idols, get_idol, update_idol, create_idol, delete_idol,
    get_event, take_event, get_all_events, get_all_groups, add_group
)
from services.economy import (
    gacha_pull, perform_comeback, start_world_tour,
    train_idol, rest_idol, buy_idol, cancel_sale, list_idol_for_sale,
    train_nsfw, calculate_event_reward, perform_fusion,
    interact_idol, apply_personal_event
)
from utils.formatter import format_idol_card, format_market_listing
from config import RARITY_CONFIG, PERSONAL_EVENTS, INTERACT_OPTIONS
from telegram.error import RetryAfter, BadRequest

def handle_telegram_errors(func):
    """Decorador para silenciar errores de Flood Control y BadRequest en ediciones."""
    async def wrapper(update, context, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except RetryAfter as e:
            # Si es un Flood control, intentamos al menos responder al query para que no se quede cargando
            try:
                if update.callback_query:
                    await update.callback_query.answer(f"⏳ Límite de Telegram. Reintenta en {e.retry_after}s.", show_alert=True)
            except: pass
            return
        except BadRequest as e:
            if "Message is not modified" in str(e):
                return
            if "Can't parse entities" in str(e):
                # Si falla el parseo, intentamos enviarlo sin parse_mode como último recurso
                try:
                    if update.callback_query:
                        await update.callback_query.edit_message_text(
                            update.callback_query.message.text + "\n(Error de formato, contacta admin)"
                        )
                except: pass
            raise e
    return wrapper

# NSFW Stat Emojis
NSFW_STAT_EMOJIS = {
    "sensualidad": "❤️",
    "puteria": "💋",
    "firmeza": "🍑",
    "habilidades_cama": "🔥",
    "fetiches": "😈"
}

NSFW_STAT_NAMES = {
    "sensualidad": "Sensualidad",
    "puteria": "Putería",
    "firmeza": "Firmeza culo/tetas",
    "habilidades_cama": "Habilidades en la Cama",
    "fetiches": "Fetiches"
}

# ─── GACHA ───
@handle_telegram_errors
async def gacha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[1]) if len(parts) > 1 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu menú de Gacha.", show_alert=True)
        return

    uid = q.from_user.id

    u = get_user(uid)
    if not u or u.get("points", 0) < 500:
        await q.edit_message_text(
            f"❌ <b>PUNTOS INSUFICIENTES</b>\n\nNecesitas <code>500 pts</code> para usar el Gacha.\n💰 Tus puntos: <code>{u['points'] if u else 0}</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{uid}")]]),
            parse_mode=ParseMode.HTML
        )
        return

    await q.answer()

    # Deduct points
    deduct_points(uid, 500)

    # --- ANIMACIÓN DE RULETA ---
    roulette_frames = [
        "🎰 <b>SINTONIZANDO...</b>\n\n[ ⬛ ⬛ ⬛ ⬛ ⬛ ]",
        "✨ <b>BUSCANDO TALENTO...</b>\n\n[ ⭐ ⬛ ⬛ ⬛ ⭐ ]",
        "💎 <b>ESCANEANDO IDOLS...</b>\n\n[ 💎 ✨ ⭐ ✨ 💎 ]",
        "🎤 <b>¡CONTRATO LISTO!</b>\n\n[ 👑 👑 👑 👑 👑 ]"
    ]
    
    for frame in roulette_frames:
        try:
            await q.edit_message_text(frame, parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.5)
        except:
            continue

    # Pull idol
    new_idol = gacha_pull(uid)

    if not new_idol:
        await q.answer("❌ Error en gacha", show_alert=True)
        return

    # Premium visuals based on rarity
    rarity_themes = {
        "C":  {"emoji": "⭐",       "border": "⚪"},
        "B":  {"emoji": "⭐⭐",      "border": "🟢"},
        "A":  {"emoji": "⭐⭐⭐",     "border": "🔵"},
        "S":  {"emoji": "🌟🌟🌟🌟",    "border": "🟣"},
        "SS": {"emoji": "💎💎💎💎💎", "border": "👑"},
        "SSS":{"emoji": "👑👑👑👑👑👑", "border": "✨"},
    }

    theme = rarity_themes.get(new_idol["rarity"], rarity_themes["C"])

    name = new_idol["name"].replace("_", " ")
    group = new_idol["group_name"].replace("_", " ")

    u = get_user(uid)

    reveal_text = (
        f"{theme['border']} <b>RAREZA {new_idol['rarity']}</b> {theme['border']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>{name.upper()}</b>\n"
        f"🏢 {group}\n"
        f"📀 Era: <code>{new_idol.get('era', 'Standard')}</code>\n"
        f"📊 Rareza: {theme['emoji']} ({new_idol['rarity']})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎤 {new_idol['vocal']} | 💃 {new_idol['dance']} | 🎧 {new_idol['rap']}\n\n"
        f"💰 Puntos restantes: <code>{u.get('points', 0)}</code>"
    )

    if new_idol.get("file_id"):
        await q.message.reply_photo(
            photo=new_idol["file_id"],
            caption=reveal_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎰 Otro Gacha (500 pts)", callback_data=f"gacha_{uid}")],
                [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")]
            ]),
            parse_mode=ParseMode.HTML
        )
        await q.delete_message()
    else:
        await q.edit_message_text(
            reveal_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎰 Otro Gacha (500 pts)", callback_data=f"gacha_{uid}")],
                [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")]
            ]), 
            parse_mode=ParseMode.HTML
        )


# ─── IDOL NAVIGATION (flat, with prev/next) ───
@handle_telegram_errors
async def idols_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    idx = int(parts[1]) if len(parts) > 1 else 0
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes mover las idols de otro CEO.", show_alert=True)
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text("📉 No tienes idols. ¡Usa el Gacha!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")]]))
        return

    idx = max(0, min(idx, len(all_idols) - 1))
    idol = all_idols[idx]

    # --- NUEVO: Trigger de Evento Personal (5% chance + Cooldown) ---
    now = time.time()
    last_event = context.user_data.get("last_personal_event", 0)
    
    if (now - last_event > 30) and random.random() < 0.05:
        context.user_data["last_personal_event"] = now
        # Buscar una idol que necesite el evento (Moral < 50 obligatoriamente)
        available_idols = [i for i in all_idols if i["status"] == "active" and not i.get("for_sale")]
        needy_idols = [i for i in available_idols if i.get("morale", 100) < 50]
        
        if needy_idols:
            target_idol = random.choice(needy_idols)
            
            event = random.choice(PERSONAL_EVENTS)
            
            # Stats para mostrar en el mensaje
            stats_text = (
                f"🎤 {target_idol.get('vocal', 0)} | 💃 {target_idol.get('dance', 0)} | 🎧 {target_idol.get('rap', 0)}\n"
                f"❤️ Moral: `{target_idol.get('morale', 100)}/100` | ⚡ Energía: `{target_idol.get('energy', 100)}/100`"
            )

            event_text = (
                f"⚡ <b>MENSAJE DE MANAGER</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ <b>{target_idol['name'].upper()}</b> tiene una petición:\n"
                f"{stats_text}\n\n"
                f"<b>{event['title']}</b>\n"
                f"{event['desc']}\n\n"
                f"💰 Costo: <code>{event['cost_points']} pts</code>\n"
                f"📉 Talento: <code>-{event['stat_loss']}</code> (V/D/R)\n"
                f"❤️ Moral: <code>+{event['moral_gain']}</code>\n"
                f"⚡ Energía: <code>+{event['energy_gain']}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"¿Permites que se tome este descanso?"
            )
            event_kb = [
                # Pasamos 'idx' (el original) para volver a donde estaba el usuario
                [InlineKeyboardButton("✅ Permitir", callback_data=f"pev_acc_{event['id']}_{target_idol['id']}_{idx}_{uid}")],
                [InlineKeyboardButton("❌ Denegar", callback_data=f"idols_{idx}_{uid}")]
            ]
            await q.edit_message_text(event_text, reply_markup=InlineKeyboardMarkup(event_kb), parse_mode="HTML")
            return

    # Store current idol index
    context.user_data["current_idol_id"] = idol["id"]
    context.user_data["current_idol_idx"] = idx

    card_text = format_idol_card(idol, None, idx + 1, len(all_idols))
    text = card_text

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"idols_{idx - 1}_{uid}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"idols_{idx + 1}_{uid}"))

    kb = [
        nav,
        [
            InlineKeyboardButton("📈 Mejorar Stats", callback_data=f"ism_stats_{idol['id']}_{idx}_{uid}"),
            InlineKeyboardButton("❤️ Moral / Energía", callback_data=f"ism_morale_{idol['id']}_{idx}_{uid}")
        ],
        [
            InlineKeyboardButton("💰 Ganar Dinero", callback_data=f"ism_money_{idol['id']}_{idx}_{uid}"),
            InlineKeyboardButton("🏷️ Vender", callback_data=f"sell_{idol['id']}_{idx}_{uid}")
        ],
        [InlineKeyboardButton("📖 Ver Lista Completa", callback_data=f"idols_list_0_{uid}")],
        [InlineKeyboardButton("🔙 Menú Principal", callback_data=f"back_main_{uid}")],
    ]

    if idol.get("file_id"):
        # Si hay foto, enviamos un mensaje nuevo con foto y borramos el anterior para evitar conflictos de media
        await q.message.reply_photo(
            photo=idol["file_id"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.HTML
        )
        await q.delete_message()
    else:
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# ─── IDOL SUBMENUS ───
async def idol_submenu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los submenús de Mejorar Stats, Moral/Energía o Ganar Dinero"""
    q = update.callback_query
    parts = q.data.split("_")
    # ism_{type}_{iid}_{idx}_{owner_id}
    stype = parts[1]
    iid, idx, owner_id = int(parts[2]), int(parts[3]), int(parts[4])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    idol = get_idol(iid)
    if not idol:
        await q.answer("❌ Error."); return

    await q.answer()

    if stype == "stats":
        text = f"📈 <b>GESTIÓN DE TALENTO: {idol['name']}</b>\n━━━━━━━━━━━━━━━━━━\nEntrena las habilidades de tu idol para mejorar sus resultados en Comebacks y Eventos."
        kb = [
            [InlineKeyboardButton("💪 Entrenar", callback_data=f"tr_menu_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("🔞 Entrenar +18", callback_data=f"nsfw_info_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
        ]
    elif stype == "morale":
        text = f"❤️ <b>BIENESTAR: {idol['name']}</b>\n━━━━━━━━━━━━━━━━━━\nMantén la moral alta y la energía llena para que tu idol rinda al máximo."
        kb = [
            [InlineKeyboardButton("📱 Interactuar", callback_data=f"int_menu_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("😴 Descansar", callback_data=f"rs_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
        ]
    elif stype == "money":
        text = f"💰 <b>ECONOMÍA: {idol['name']}</b>\n━━━━━━━━━━━━━━━━━━\nGenera ingresos mediante lanzamientos musicales o giras mundiales."
        kb = [
            [InlineKeyboardButton("💿 Comeback", callback_data=f"cb_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("✈️ World Tour (12h)", callback_data=f"tour_{iid}_{idx}_{owner_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
        ]
    else:
        await q.answer("❌ Error."); return

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


# ─── COMEBACK ───
async def idols_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra una lista compacta de todas las idols con botones numéricos"""
    q = update.callback_query
    parts = q.data.split("_")
    page = int(parts[2])
    owner_id = int(parts[3])

    if q.from_user.id != owner_id:
        await q.answer("❌ Esta no es tu lista.", show_alert=True); return

    all_idols = get_user_idols(owner_id)
    if not all_idols:
        await q.answer("❌ No tienes idols.", show_alert=True); return

    per_page = 5
    total_pages = (len(all_idols) - 1) // per_page + 1
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_idols = all_idols[start_idx:end_idx]

    text = f"📖 <b>INVENTARIO ({len(all_idols)})</b>\n"
    text += f"Página {page + 1} de {total_pages}\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    num_buttons = []
    for i, idol in enumerate(page_idols):
        global_idx = start_idx + i
        era = idol.get('era', 'Standard')
        text += f"{global_idx + 1}. <b>{idol['name']}</b> ({era}) ({idol['rarity']})\n"
        num_buttons.append(InlineKeyboardButton(f"{global_idx + 1}", callback_data=f"idols_{global_idx}_{owner_id}"))

    text += "\n━━━━━━━━━━━━━━━━━━"

    kb = [num_buttons] # Fila de números
    
    # Navegación de páginas
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"idols_list_{page-1}_{owner_id}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"idols_list_{page+1}_{owner_id}"))
    
    kb.append(nav)
    kb.append([InlineKeyboardButton("🔙 Volver", callback_data=f"idols_0_{owner_id}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


@handle_telegram_errors
async def cancel_sale_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela una venta en el mercado"""
    q = update.callback_query
    parts = q.data.split("_")
    # cancel_sale_{iid}_{idx}_{owner_id}
    iid, idx, owner_id = int(parts[2]), int(parts[3]), int(parts[4])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    from services.economy import cancel_sale
    if cancel_sale(owner_id, iid):
        await q.answer("✅ Venta cancelada.")
        # Volver a la vista de la idol
        await idols_handler(update, context)
    else:
        await q.answer("❌ Error al cancelar venta.", show_alert=True)


@handle_telegram_errors
async def comeback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes ordenar acciones a idols de otros.", show_alert=True)
        return

    r = perform_comeback(q.from_user.id, iid)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 500 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía. Descansa a tu idol.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol ocupada. Espera a que regrese.", show_alert=True); return
    if r == "limite_comebacks":
        await q.answer("❌ Ya tienes 3 comebacks activos. Espera a que terminen.", show_alert=True); return
    if r == "no_disponible":
        await q.answer("❌ Idol no disponible (hiatus o mercado).", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    until = r['until'].strftime("%H:%M")
    await q.edit_message_text(
        f"💿 <b>COMEBACK INICIADO: {r['idol_name']}</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"Tu idol está grabando su nuevo álbum...\n\n"
        f"⏳ Resultados a las <code>{until} UTC</code> (30 min)\n"
        f"💰 Costo pagado: <code>500 pts</code>\n"
        f"⚡ Energía: <code>-20</code>\n\n"
        f"<i>Los resultados se calcularán automáticamente cuando termine.</i>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="HTML")


# ─── TRAIN ───
@handle_telegram_errors
async def train_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones de entrenamiento (Vocal, Dance, Rap)"""
    q = update.callback_query
    parts = q.data.split("_")
    # tr_menu_{iid}_{idx}_{owner_id}
    iid, idx, owner_id = int(parts[2]), int(parts[3]), int(parts[4])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    idol = get_idol(iid)
    if not idol:
        await q.answer("❌ Error."); return

    await q.answer()
    
    text = (
        f"💪 <b>CENTRO DE ENTRENAMIENTO: {idol['name']}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"¿En qué área quieres que <b>{idol['name']}</b> mejore hoy?\n\n"
        "🎤 <b>Vocal:</b> Mejora el canto y técnica.\n"
        "💃 <b>Dance:</b> Mejora el baile y presencia.\n"
        "🎧 <b>Rap:</b> Mejora el ritmo y lírica.\n\n"
        "💰 Costo: <code>200 pts</code> | ⚡ Energía: <code>-15</code>"
    )

    kb = [
        [
            InlineKeyboardButton("🎤 Vocal", callback_data=f"tr_exe_vocal_{iid}_{idx}_{owner_id}"),
            InlineKeyboardButton("💃 Dance", callback_data=f"tr_exe_dance_{iid}_{idx}_{owner_id}"),
            InlineKeyboardButton("🎧 Rap", callback_data=f"tr_exe_rap_{iid}_{idx}_{owner_id}")
        ],
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def train_execute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta el entrenamiento del stat elegido"""
    q = update.callback_query
    parts = q.data.split("_")
    # tr_exe_{stat}_{iid}_{idx}_{owner_id}
    stat = parts[2]
    iid, idx, owner_id = int(parts[3]), int(parts[4]), int(parts[5])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    r = train_idol(q.from_user.id, iid, stat)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 200 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol en Tour.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"💪 <b>ENTRENAMIENTO: {r['idol_name']}</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['emoji']} {r['stat'].title()} subió <code>+{r['boost']}</code> → <code>{r['new_val']}</code>\n\n"
        f"💰 Pagaste: <code>200 pts</code>\n"
        f"⚡ Energía: <code>-15</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="HTML")


# ─── INTERACT ───
@handle_telegram_errors
async def interact_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones de interacción (Live / Instagram)"""
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    await q.answer()

    text = (
        "📱 <b>MENÚ DE INTERACCIÓN</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Elige cómo quieres que tu idol conecte con sus fans hoy. "
        "Esto subirá su moral pero consumirá energía.\n\n"
        "📸 <b>Instagram:</b> Menos energía, moral moderada.\n"
        "🎥 <b>Live:</b> Mucha energía, moral alta (¡puede ser viral!)."
    )

    kb = [
        [InlineKeyboardButton(INTERACT_OPTIONS["instagram"]["name"], callback_data=f"int_exe_instagram_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(INTERACT_OPTIONS["live"]["name"], callback_data=f"int_exe_live_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def interact_execute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta la interacción elegida"""
    q = update.callback_query
    parts = q.data.split("_")
    # int_exe_{type}_{iid}_{idx}_{owner_id}
    itype = parts[2]
    iid, idx, owner_id = int(parts[3]), int(parts[4]), int(parts[5])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    r = interact_idol(q.from_user.id, iid, itype)

    if r == "sin_energia":
        await q.answer("😴 Sin energía para esto.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol ocupada.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"📱 <b>INTERACCIÓN: {r['idol_name']}</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['text']}\n\n"
        f"❤️ Moral: <code>{r['new_morale']}/100</code>\n"
        f"⚡ Energía: <code>{r['new_energy']}/100</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode=ParseMode.HTML
    )


# ─── PERSONAL EVENTS ───
@handle_telegram_errors
async def personal_event_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la aceptación de un evento personal"""
    q = update.callback_query
    parts = q.data.split("_")
    # pev_acc_{ev_id}_{iid}_{idx}_{owner_id}
    # Como ev_id puede tener guiones bajos, contamos desde el final
    owner_id = int(parts[-1])
    idx = int(parts[-2])
    iid = int(parts[-3])
    ev_id = "_".join(parts[2:-3])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    r = apply_personal_event(q.from_user.id, iid, ev_id)

    if r == "puntos_insuficientes":
        await q.answer("❌ No tienes suficientes puntos.", show_alert=True); return
    if r == "error":
        await q.answer("❌ Error al procesar evento.", show_alert=True); return

    result_text = (
        f"✅ <b>PERMISO CONCEDIDO: {r['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Has permitido que <b>{r['idol_name']}</b> se tome un descanso personal.\n\n"
        f"💰 Pagaste: <code>-{r['cost']} pts</code> en gastos y logística.\n"
        f"📉 El descanso afectó su práctica: <code>-{r['stat_loss']}</code> Talentos.\n"
        f"💖 Pero su felicidad es máxima: <code>+{r['moral_gain']} Moral</code> y <code>+{r['energy_gain']} Energía</code>.\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    await q.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode=ParseMode.HTML
    )


# ─── REST ───
@handle_telegram_errors
async def rest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes dormir a idols de otros.", show_alert=True)
        return

    r = rest_idol(q.from_user.id, iid)

    if r == "ocupada":
        await q.answer("✈️ Idol ocupada (Tour o Descanso).", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return
        
    # Show wake up time
    until = r['until'].strftime("%H:%M")
    await q.edit_message_text(
        f"😴 <b>{r['idol_name']} se fue a dormir</b>\n⚡ Energía +{r['energy_gain']} → <code>{r['new_energy']}/100</code>\n"
        f"Regresará a las <code>{until} UTC</code>.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode="HTML")


# ─── TOUR ───
@handle_telegram_errors
async def tour_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Solo el dueño puede iniciar tours.", show_alert=True)
        return

    r = start_world_tour(q.from_user.id, iid)

    if isinstance(r, dict):
        until = r['until'].strftime("%H:%M")
        t = f"✈️ *TOUR INICIADO*\n\nTu idol ha comenzado una gira mundial. Generará beneficios pasivos y regresará a las `{until} UTC`."
    elif r == "ya_en_tour":
        t = "✈️ Esta idol ya está en medio de un tour."
    elif r == "limite_tours":
        t = "❌ Ya tienes 3 tours activos. Espera a que alguno termine."
    else:
        t = "❌ No disponible para tour (debe estar activa y no en el mercado)."

    await q.edit_message_text(t,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="HTML")


# ─── SELL (put on market) ───
@handle_telegram_errors
async def sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu menú de venta.", show_alert=True)
        return

    kb = [
        [InlineKeyboardButton("500 pts", callback_data=f"listsell_{iid}_{idx}_500_{owner_id}"),
         InlineKeyboardButton("1000 pts", callback_data=f"listsell_{iid}_{idx}_1000_{owner_id}")],
        [InlineKeyboardButton("2000 pts", callback_data=f"listsell_{iid}_{idx}_2000_{owner_id}"),
         InlineKeyboardButton("5000 pts", callback_data=f"listsell_{iid}_{idx}_5000_{owner_id}")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"idols_{idx}_{owner_id}")],
    ]

    await q.edit_message_text("🏷️ <b>¿A qué precio quieres vender esta idol?</b>",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def list_sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx, price = int(parts[1]), int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Solo el dueño puede listar idols.", show_alert=True)
        return

    r = list_idol_for_sale(q.from_user.id, iid, price)

    if r == "listed":
        t = f"✅ Idol puesta en venta por <code>{price} pts</code>."
    else:
        t = "❌ No se pudo listar."

    await q.edit_message_text(t,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode="HTML")


# ─── MARKET ───
@handle_telegram_errors
async def market_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    idx = int(parts[1]) if len(parts) > 1 else 0
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Abre el mercado tú mismo para navegar.", show_alert=True)
        return

    # Get all idols for sale
    all_idols = get_all_idols()
    listings = [idol for idol in all_idols.values() if idol.get("for_sale", False)]

    if not listings:
        await q.edit_message_text("🏪 <b>MERCADO</b>\nNo hay idols en venta.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]),
            parse_mode="HTML")
        return

    idx = max(0, min(idx, len(listings) - 1))
    idol = listings[idx]

    text = f"🏪 *MERCADO* ({idx+1}/{len(listings)})\n━━━━━━━━━━━━━━━━━━\n"
    text += format_market_listing(idol, None, f"user_{idol['user_id']}")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"market_{idx-1}_{owner_id}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(listings)}", callback_data="noop"))
    if idx < len(listings) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"market_{idx + 1}_{owner_id}"))

    kb = [nav,
          [InlineKeyboardButton(f"💰 Comprar ({idol['sale_price']} pts)", callback_data=f"buy_{idol['id']}")],
          [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    iid = int(q.data.split("_")[1])

    r = buy_idol(q.from_user.id, iid)

    if r == "no_points":
        await q.answer("❌ Puntos insuficientes.", show_alert=True); return
    if r == "own_idol":
        await q.answer("❌ No puedes comprar tu propia idol.", show_alert=True); return
    if isinstance(r, str):
        await q.answer(f"❌ {r}", show_alert=True); return

    await q.edit_message_text(f"✅ <b>¡Compraste a {r['idol_name']}!</b>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode="HTML")


# ─── SELECT IDOL FOR EVENT ───
@handle_telegram_errors
async def select_idol_for_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de idols para seleccionar en evento NSFW"""
    q = update.callback_query
    await q.answer()

    parts = q.data.split("_")
    eid = int(parts[2]) if len(parts) > 2 else 0
    idx = int(parts[3]) if len(parts) > 3 else 0
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este menú de selección no es tuyo.", show_alert=True)
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text(
            "📉 <b>NO Tienes idols</b>\n¡Usa el Gacha primero!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{owner_id}")]]),
            parse_mode=ParseMode.HTML
        )
        return

    idx = max(0, min(idx, len(all_idols) - 1))
    idol = all_idols[idx]

    event = get_event(eid)
    is_charity = event.get("event_type") == "CHARITY" if event else False
    
    title = "💖 SELECCIÓN BENÉFICA" if is_charity else "🔞 SELECCIONA IDOL PARA EVENTO"
    
    total_basic = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    total_nsfw = (idol.get("sensualidad", 50) + idol.get("puteria", 50) +
                  idol.get("firmeza", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("fetiches", 50))

    card_text = (f"{title}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ <b>{idol['name'].replace('_', ' ').upper()}</b> {idol.get('group_name', '')}\n"
                f"📊 Rareza: {'⭐' * (['C','B','A','S','SS','SSS'].index(idol['rarity']) + 1)} ({idol['rarity']})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
                f"💪 Stats Básicos: <code>{total_basic}</code>\n\n")

    if not is_charity:
        card_text += (f"❤️ {idol.get('sensualidad', 50)} | 💋 {idol.get('puteria', 50)} | 🍑 {idol.get('firmeza', 50)}\n"
                    f"🔥 {idol.get('habilidades_cama', 50)} | 😈 {idol.get('fetiches', 50)}\n"
                    f"💪 Stats NSFW: <code>{total_nsfw}</code>\n\n"
                    f"📈 Total Stats: <code>{total_basic + total_nsfw}</code>")
    else:
        card_text += (f"❤️ Moral Actual: <code>{idol.get('morale', 0)}/100</code>\n"
                    f"⚡ Energía Actual: <code>{idol.get('energy', 0)}/100</code>\n\n"
                    f"✨ <i>Esta acción restaurará la moral al 100%</i>")

    # Botones para otras idols
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}_{owner_id}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}_{owner_id}"))

    btn_label = "💖 PARTICIPAR" if is_charity else "🔞 USAR ESTA IDOL"
    kb = [
        nav,
        [InlineKeyboardButton(btn_label, callback_data=f"use_idol_{eid}_{idol['id']}_{owner_id}")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"claim_{eid}")]
    ]

    await q.edit_message_text(
        card_text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )


# ─── USE IDOL FOR EVENT ───
@handle_telegram_errors
async def use_idol_for_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta evento NSFW con la idol seleccionada"""
    q = update.callback_query
    parts = q.data.split("_")
    eid = int(parts[2])
    iid = int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes usar idols ajenas en este evento.", show_alert=True)
        return

    event = get_event(eid)
    if not event:
        await q.answer("❌ Evento no encontrado.", show_alert=True); return

    is_charity = event.get("event_type") == "CHARITY"

    # 1. Bloquear el evento para que nadie más lo use
    if not take_event(eid, q.from_user.id):
        await q.answer("❌ El evento ya no está disponible.", show_alert=True)
        return

    if is_charity:
        user = get_user(q.from_user.id)
        cost = event.get("points", 0)
        if user["points"] < cost:
            await q.answer(f"❌ Necesitas {cost} pts para participar.", show_alert=True)
            return # Note: in a real race condition we'd need to unlock the event here, but take_event is atomic

        deduct_points(q.from_user.id, cost)
        update_idol(iid, morale=100)
        
        idol_name = get_idol(iid)["name"].replace("_", " ")
        
        charity_variants = [
            f"💖 *{idol_name}* visitó un orfanato local, pasando el día jugando con los niños y donando suministros. Su corazón se llenó de alegría al ver sus sonrisas.",
            f"💖 *{idol_name}* participó en una campaña de limpieza de playas. Ver el impacto positivo en la naturaleza le devolvió la paz y el entusiasmo.",
            f"💖 *{idol_name}* sirvió comida en un refugio comunitario. Conversar con las personas y ayudarlas le recordó por qué ama ser una inspiración.",
            f"💖 *{idol_name}* organizó un pequeño concierto acústico gratuito para recaudar fondos para animales rescatados. La música y el amor la renovaron por completo."
        ]
        story = random.choice(charity_variants)
        
        result_text = (f"🌟 <b>¡EVENTO COMPLETADO!</b>\n{story}\n\n"
                      f"👤 CEO: <b>{q.from_user.username}</b>\n"
                      f"💰 Costo: <code>-{cost} pts</code> (Donación)\n"
                      f"📈 Efecto: <code>❤️ Moral al 100%</code>\n"
                      f"━━━━━━━━━━━━━━━━━━\n"
                      f"✨ <i>Tu idol se siente renovada y lista para brillar en el escenario.</i>")
    else:
        # Calcular recompensa NSFW
        reward_data = calculate_event_reward(q.from_user.id, iid)
        if not reward_data:
            await q.answer("❌ Error al calcular recompensa.", show_alert=True); return

        # Añadir puntos al CEO
        add_points(q.from_user.id, reward_data['reward'])

        # Penalizar moral y energía (Riesgo del evento NSFW)
        new_morale = max(0, reward_data.get('morale', 100) - 20)
        new_energy = max(0, reward_data.get('energy', 100) - 15)
        update_idol(iid, morale=new_morale, energy=new_energy)

        nsfw_variants = [
            f"🔞 *{reward_data['idol_name']}* protagonizó una sesión de fotos picante para una revista exclusiva...",
            f"🔞 *{reward_data['idol_name']}* participó en un show privado de alta gama para fans VIP...",
            f"🔞 *{reward_data['idol_name']}* fue la imagen principal de una campaña de lencería de lujo...",
            f"🔞 *{reward_data['idol_name']}* grabó un comercial provocativo que se volvió tendencia en redes...",
            f"🔞 *{reward_data['idol_name']}* asistió como invitada especial a una fiesta privada de la élite de Gangnam...",
            f"🔞 *{reward_data['idol_name']}* aceptó un patrocinio arriesgado para una marca de bebidas para adultos..."
        ]
        story = random.choice(nsfw_variants)

        result_text = (f"🔥 <b>¡CONTRATO FIRMADO!</b>\n{story}\n\n"
                      f"👤 CEO: <b>{q.from_user.username}</b>\n"
                      f"💰 Ganancia: <code>+{reward_data['reward']} pts</code> (Rareza {reward_data['rarity']} + {reward_data['stat_bonus']}x Bonus)\n"
                      f"📉 Efecto: <code>-20 Moral</code> | <code>-15 Energía</code>\n"
                      f"━━━━━━━━━━━━━━━━━━\n"
                      f"✨ <i>Tus stats NSFW han multiplicado la ganancia base significativamente.</i>")

    await q.edit_message_text(result_text, parse_mode="HTML")


# ─── NSFW INFO HANDLER ───
@handle_telegram_errors
async def nsfw_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el botón Stats NSFW en la tarjeta de idol"""
    q = update.callback_query
    parts = q.data.split("_")
    # nsfw_info_ID_IDX_OWNERID -> parts = ["nsfw", "info", "ID", "IDX", "OWNERID"]
    iid, idx = int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes ver las stats privadas de otro CEO.", show_alert=True)
        return

    all_idols = get_all_idols()
    if str(iid) not in all_idols:
        await q.answer("❌ Idol no encontrada.", show_alert=True)
        return

    idol = all_idols[str(iid)]

    total_nsfw = (idol.get("sensualidad", 50) + idol.get("puteria", 50) +
                  idol.get("firmeza", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("fetiches", 50))

    text = (f"🔞 <b>STATS NSFW de {idol['name'].replace('_', ' ').upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{NSFW_STAT_EMOJIS['sensualidad']} Sensualidad: <code>{idol.get('sensualidad', 50)}/100</code>\n"
            f"{NSFW_STAT_EMOJIS['puteria']} Putería: <code>{idol.get('puteria', 50)}/100</code>\n"
            f"{NSFW_STAT_EMOJIS['firmeza']} Firmeza culo/tetas: <code>{idol.get('firmeza', 50)}/100</code>\n"
            f"{NSFW_STAT_EMOJIS['habilidades_cama']} Habilidades Cama: <code>{idol.get('habilidades_cama', 50)}/100</code>\n"
            f"{NSFW_STAT_EMOJIS['fetiches']} Fetiches: <code>{idol.get('fetiches', 50)}/100</code>\n\n"
            f"💪 Total NSFW: <code>{total_nsfw}/500</code>")

    kb = [
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['sensualidad']}",
                              callback_data=f"nsfw_tr_sensualidad_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['puteria']}",
                              callback_data=f"nsfw_tr_puteria_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['firmeza']}",
                              callback_data=f"nsfw_tr_firmeza_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['habilidades_cama']}",
                              callback_data=f"nsfw_tr_habilidades_cama_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['fetiches']}",
                              callback_data=f"nsfw_tr_fetiches_{iid}_{idx}_{owner_id}")],
    ]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )


# ─── NSFW TRAINING ───
@handle_telegram_errors
async def nsfw_train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrena un stat NSFW específico"""
    q = update.callback_query
    parts = q.data.split("_")
    # nsfw_tr_{stat_name}_{iid}_{idx}_{owner_id}
    # Como el nombre del stat puede tener guiones bajos, contamos desde el final
    owner_id = int(parts[-1])
    idx = int(parts[-2])
    iid = int(parts[-3])
    stat_type = "_".join(parts[2:-3])

    if q.from_user.id != owner_id:
        await q.answer("❌ Este entrenamiento no es tuyo.", show_alert=True)
        return

    r = train_nsfw(q.from_user.id, iid, stat_type)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 200 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía. Descansa a tu idol.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"🔞 <b>ENTRENAMIENTO NSFW de {r['idol_name']}</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['emoji']} {r['stat']} subió <code>+{r['boost']}</code> → <code>{r['new_val']}/100</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode=ParseMode.HTML
    )


# ─── CLAIM GLOBAL EVENT ───
@handle_telegram_errors
async def claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para reclamar evento global (primera fase: selección)"""
    q = update.callback_query
    parts = q.data.split("_")
    eid = int(parts[1]) if len(parts) > 1 else 0

    # Verificar si el evento ya fue tomado
    event = get_event(eid)
    if not event or event.get("is_taken"):
        await q.answer("❌ Este evento ya ha sido reclamado.", show_alert=True)
        try:
            await q.edit_message_text("⌛ <b>EVENTO FINALIZADO</b>\nEste contrato ya ha sido firmado.", parse_mode="HTML")
        except: pass
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.answer("❌ No tienes ninguna idol para participar.", show_alert=True)
        return

    event = get_event(eid)
    is_charity = event.get("event_type") == "CHARITY" if event else False
    
    title = "💖 SELECCIÓN BENÉFICA" if is_charity else "🔞 SELECCIONA IDOL PARA EVENTO"
    
    idx = 0
    idol = all_idols[idx]
    total_basic = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    total_nsfw = (idol.get("sensualidad", 50) + idol.get("puteria", 50) +
                  idol.get("firmeza", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("fetiches", 50))

    text = (f"{title}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ <b>{idol['name'].replace('_', ' ').upper()}</b> {idol.get('group_name', '')}\n"
            f"📊 Rareza: {'⭐' * (['C','B','A','S','SS','SSS'].index(idol['rarity']) + 1)} ({idol['rarity']})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
            f"💪 Stats Básicos: <code>{total_basic}</code>\n\n")

    if not is_charity:
        text += (f"❤️ {idol.get('sensualidad', 50)} | 💋 {idol.get('puteria', 50)} | 🍑 {idol.get('firmeza', 50)}\n"
                f"🔥 {idol.get('habilidades_cama', 50)} | 😈 {idol.get('fetiches', 50)}\n"
                f"💪 Stats NSFW: <code>{total_nsfw}</code>\n\n"
                f"📈 Total Stats: <code>{total_basic + total_nsfw}</code>")
    else:
        text += (f"❤️ Moral Actual: <code>{idol.get('morale', 0)}/100</code>\n"
                f"⚡ Energía Actual: <code>{idol.get('energy', 0)}/100</code>\n\n"
                f"✨ <i>Esta acción restaurará la moral al 100%</i>")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}_{uid}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}_{uid}"))

    btn_label = "💖 PARTICIPAR" if is_charity else "🔞 USAR ESTA IDOL"
    kb = [
        nav,
        [InlineKeyboardButton(btn_label, callback_data=f"use_idol_{eid}_{idol['id']}_{uid}")],
        [InlineKeyboardButton(" Anular", callback_data="noop")]
    ]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )


# ─── HELP POINTS ───
@handle_telegram_errors
async def help_points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes abrir menús ajenos.", show_alert=True)
        return

    await q.answer()

    text = (
        "💰 *¿CÓMO GANAR PUNTOS?*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📀 *Comebacks:* La forma principal. Envía a tu idol a lanzar un álbum. Si es un MEGA HIT, ¡ganarás muchísimos puntos!\n\n"
        "🔞 *Eventos Globales:* En los grupos aparecerán contratos. Si eres el primero en reclamarlos, ganarás puntos según la rareza de tu mejor idol.\n\n"
        "🏪 *Mercado:* Si tienes idols que no usas, ponlas en venta. Otros CEOs pueden comprarlas y tú recibirás el pago.\n\n"
        "✈️ *World Tours:* Envía a tu idol de gira por 12h. No podrá trabajar, pero a su regreso traerá una gran cantidad de puntos pasivos.\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    kb = [[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{q.from_user.id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def help_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la guía completa y detallada del juego"""
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes abrir menús ajenos.", show_alert=True)
        return

    await q.answer()
    
    text = (
        "👑 <b>GUÍA DEFINITIVA DEL CEO DE IDOLS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎤 <b>HABILIDADES Y ÉXITO</b>\n"
        "• <b>Talento (V, D, R):</b> Vocal, Dance y Rap. Determinan el éxito de los <b>Comebacks</b>. Un MEGA HIT puede darte x2 de recompensa.\n"
        "• <b>Stats NSFW:</b> Sensualidad, Putería, Firmeza culo/tetas, Cama y Fetiches. Son vitales para los <b>Eventos Globales</b>. A mayor nivel, ¡contratos más millonarios!\n\n"
        "💎 <b>RAREZAS Y MULTIPLICADORES</b>\n"
        "• <code>C</code> (40%): x1.0 | <code>B</code> (35%): x1.5\n"
        "• <code>A</code> (18%): x2.5 | <code>S</code> (6%): x5.0\n"
        "• <code>SS</code> (1%): x10.0 (¡Diosas Legendarias!)\n\n"
        "💸 <b>ECONOMÍA Y GASTOS</b>\n"
        "• <b>Mantenimiento:</b> Cada 24h pagas según rareza: C=50, B=100, A=250, S=500, SS=1000 pts. Si no tienes puntos, tus idols entrarán en <b>Hiatus</b> (se pausan y no ganan nada).\n"
        "• <b>Máx 3 produciendo:</b> Solo las 3 idols con mejor score generan ingresos en eventos y comebacks. Las demás no pueden trabajar.\n"
        "• <b>Energía (⚡):</b> Se gasta al trabajar. Si baja de 20, no podrán hacer Comebacks. Recupérala con 'Descansar'.\n"
        "• <b>Moral (❤️):</b> Afecta el Score. Si es baja, tus canciones serán un FLOP. Súbela con 'Interactuar'.\n\n"
        "🏪 <b>MERCADO Y TOURS</b>\n"
        "• Puedes vender idols al precio que quieras. El mercado es global entre todos los jugadores.\n"
        "• Los <b>World Tours</b> duran 12h y son la mejor forma de ganar puntos mientras no estás conectado.\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    kb = [[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{q.from_user.id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# ─── FUSION HANDLERS ───
@handle_telegram_errors
async def fusion_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, manual_owner_id=None):
    """Main fusion menu with 3 slots"""
    q = update.callback_query
    if manual_owner_id:
        owner_id = manual_owner_id
    else:
        parts = q.data.split("_")
        owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu laboratorio.", show_alert=True)
        return

    # Initialize fusion slots in user_data if not present
    if "fusion_slots" not in context.user_data:
        context.user_data["fusion_slots"] = [None, None, None]

    slots = context.user_data["fusion_slots"]
    all_idols = get_all_idols()
    
    slot_texts = []
    for i, s_id in enumerate(slots):
        if s_id and str(s_id) in all_idols:
            idol = all_idols[str(s_id)]
            slot_texts.append(f"Slot {i+1}: <b>{idol['name']}</b> ({idol['rarity']})")
        else:
            slot_texts.append(f"Slot {i+1}: <i>[Vacío]</i>")

    text = (
        "🧪 <b>CÁMARA DE FUSIÓN</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Combina 3 idols para obtener una nueva con mejores probabilidades de rareza alta.\n\n"
        + "\n".join(slot_texts) +
        "\n━━━━━━━━━━━━━━━━━━"
    )

    kb = []
    for i in range(3):
        label = "✅ Cambiar" if slots[i] else "➕ Seleccionar"
        kb.append([InlineKeyboardButton(f"{label} Idol {i+1}", callback_data=f"fus_sel_{i}_{owner_id}")])

    if all(slots):
        kb.append([InlineKeyboardButton("⚡ FUSIONAR (Acción irreversible)", callback_data=f"fus_exe_{owner_id}")])
    
    kb.append([InlineKeyboardButton("🧹 Limpiar todo", callback_data=f"fus_clear_{owner_id}")])
    kb.append([InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def fusion_select_slot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of idols to pick for a specific slot"""
    q = update.callback_query
    parts = q.data.split("_")
    slot_idx = int(parts[2])
    owner_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Error de acceso.", show_alert=True); return

    all_idols = get_user_idols(owner_id)
    # Filter out idols already in other slots
    selected_ids = [s for s in context.user_data.get("fusion_slots", []) if s is not None]
    available = [i for i in all_idols if i["id"] not in selected_ids or i["id"] == context.user_data["fusion_slots"][slot_idx]]

    if not available:
        await q.answer("❌ No tienes más idols disponibles.", show_alert=True); return

    # Pagination (5 per page)
    per_page = 5
    total_pages = (len(available) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_idols = available[start_idx:end_idx]

    text = f"🧪 <b>SELECCIONAR PARA SLOT {slot_idx + 1}</b>\n(Página {page+1}/{total_pages})"
    
    kb = []
    for idol in page_idols:
        kb.append([InlineKeyboardButton(f"{idol['name']} ({idol['rarity']}) - {idol.get('era', 'Standard')}", 
                                         callback_data=f"fus_pick_{slot_idx}_{idol['id']}_{owner_id}")])

    # Navigation
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"fus_sel_{slot_idx}_{owner_id}_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"fus_sel_{slot_idx}_{owner_id}_{page+1}"))
    if nav: kb.append(nav)

    kb.append([InlineKeyboardButton("🔙 Volver", callback_data=f"fusion_main_{owner_id}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def fusion_pick_idol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store picked idol and return to fusion menu"""
    q = update.callback_query
    parts = q.data.split("_")
    slot_idx = int(parts[2])
    idol_id = int(parts[3])
    owner_id = int(parts[4])

    if "fusion_slots" not in context.user_data:
        context.user_data["fusion_slots"] = [None, None, None]
    
    context.user_data["fusion_slots"][slot_idx] = idol_id
    await q.answer(f"✅ Slot {slot_idx+1} asignado.")
    
    # Redirect to menu
    await fusion_menu_handler(update, context, manual_owner_id=owner_id)


@handle_telegram_errors
async def fusion_execute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the fusion and show result"""
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2])

    if q.from_user.id != owner_id:
        await q.answer("❌ Error.", show_alert=True); return

    slots = context.user_data.get("fusion_slots", [])
    if not all(slots):
        await q.answer("❌ Necesitas 3 idols.", show_alert=True); return

    # Feedback visual inmediato
    await q.edit_message_text("🧪 <b>PROCESANDO FUSIÓN...</b>\n━━━━━━━━━━━━━━━━━━\n🧬 Combinando secuencias de ADN...\n✨ Estabilizando núcleos de idols...\n⏳ Por favor espera un momento...", parse_mode="HTML")
    
    try:
        result = perform_fusion(owner_id, slots)
    except Exception as e:
        import logging
        logging.error(f"Error en perform_fusion: {e}")
        await q.answer(f"❌ Error crítico: {e}", show_alert=True)
        # Restaurar el menú
        await fusion_menu_handler(update, context, manual_owner_id=owner_id)
        return
    
    if isinstance(result, str):
        if result.startswith("not_found"):
            msg = "Una de las idols seleccionadas ya no existe en tu inventario."
        elif result.startswith("not_owner"):
            name = result.replace("not_owner_", "")
            msg = f"No eres el dueño de {name}."
        elif result.startswith("in_market"):
            name = result.replace("in_market_", "")
            msg = f"La idol {name} está puesta en venta en el mercado. Quítala primero."
        elif result == "need_3_idols":
            msg = "Necesitas seleccionar 3 idols para la fusión."
        else:
            msg = f"Error: {result}"
            
        await q.answer(f"❌ {msg}", show_alert=True)
        # Restaurar el menú para que no se quede en "Procesando"
        await fusion_menu_handler(update, context, manual_owner_id=owner_id)
        return

    await q.answer("🧪 ¡Fusión completada!")

    # Clear slots
    context.user_data["fusion_slots"] = [None, None, None]
    
    new_idol = result["new_idol"]
    # Escapar nombres para evitar errores de Markdown
    fused_names = [n.replace("_", "\\_").replace("*", "\\*") for n in result["fused_names"]]
    names_str = ", ".join(fused_names)

    # Visuals based on result rarity
    rarity_themes = {
        "C":  {"emoji": "⭐",       "border": "⚪", "title": "FUSIÓN ÉXITO"},
        "B":  {"emoji": "⭐⭐",      "border": "🟢", "title": "FUSIÓN SUPERIOR"},
        "A":  {"emoji": "⭐⭐⭐",     "border": "🔵", "title": "FUSIÓN ELITE"},
        "S":  {"emoji": "🌟🌟🌟🌟",    "border": "🟣", "title": "FUSIÓN LEGENDARIA"},
        "SS": {"emoji": "💎💎💎💎💎", "border": "👑", "title": "Diosa Creada"},
        "SSS":{"emoji": "👑👑👑👑👑👑", "border": "✨", "title": "ENTIDAD SUPREMA"},
    }
    theme = rarity_themes.get(new_idol["rarity"], rarity_themes["C"])

    text = (
        f"🧪 *¡FUSIÓN COMPLETADA!*\n"
        f"Sacrificaste a: _{names_str}_\n\n"
        f"{theme['border']} *{theme['title']}* {theme['border']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *{new_idol['name'].upper()}* ({new_idol.get('era', 'Standard')})\n"
        f"🏢 {new_idol['group_name']}\n"
        f"📊 Rareza: {theme['emoji']} ({new_idol['rarity']})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎤 {new_idol['vocal']} | 💃 {new_idol['dance']} | 🎧 {new_idol['rap']}\n"
    )

    kb = [[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


@handle_telegram_errors
async def fusion_clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset the fusion slots"""
    q = update.callback_query
    owner_id = int(q.data.split("_")[2])
    context.user_data["fusion_slots"] = [None, None, None]
    await q.answer("🧹 Slots limpiados.")
    await fusion_menu_handler(update, context, manual_owner_id=owner_id)


# ─── NOOP (for page indicators) ───
async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
