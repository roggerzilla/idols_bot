"""
Formateadores usando almacenamiento JSON (dicts).
"""

from datetime import datetime
import html


def format_idol_card(idol, template, idx=None, total=None):
    """Compact idol card for the flat navigation UI - works with dicts"""

    # Status mapping
    status_map = {
        "active": ("✅", "Activa"),
        "hiatus": ("😴", "Hiatus"),
        "world_tour": ("✈️", "En Tour"),
        "resting": ("😴", "Descansando"),
    }

    status_emoji, status_text = status_map.get(idol.get("status", "active"), ("❓", "Desconocido"))

    # Check busy_until for tour/rest time remaining
    if idol.get("status") in ["world_tour", "resting"] and idol.get("busy_until"):
        try:
            busy_until = datetime.fromisoformat(idol["busy_until"])
            now = datetime.utcnow()
            if now < busy_until:
                rem = busy_until - now
                hours, remainder = divmod(rem.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                status_text = f"En Tour (Libre en {hours}h {minutes}m)"
        except (ValueError, TypeError):
            pass

    # Morale bar
    morale = idol.get("morale", 100)
    energy = idol.get("energy", 100)
    morale_bars = "█" * (morale // 10) + "░" * (10 - morale // 10)
    energy_bars = "█" * (energy // 10) + "░" * (10 - energy // 10)

    header = ""
    if idx is not None and total is not None:
        header = f"Idol {idx}/{total}\n"

    sale_text = ""
    if idol.get("for_sale", False):
        sale_text = f"\n🏷 EN VENTA: {idol.get('sale_price', 0)} pts"

    name = html.escape(idol.get("name", "Unknown").replace("_", " "))
    group = html.escape(idol.get("group_name", "Unknown Group").replace("_", " "))
    rarity = html.escape(idol.get("rarity", "C"))
    era = html.escape(idol.get("era", "Standard").replace("_", " "))

    # NSFW Stats
    sens = idol.get("sensualidad", 50)
    put = idol.get("puteria", 50)
    firm = idol.get("firmeza", 50)
    hab = idol.get("habilidades_cama", 50)
    fet = idol.get("fetiches", 50)

    return (
        f"{header}"
        f"🌟 <b>{name}</b> ({group}) [{era}] [{rarity}]\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{status_emoji} Estado: {status_text}\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"❤️ Moral: {morale}/100\n"
        f"⚡ Energía: {energy}/100\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔞 ❤️{sens} | 💋{put} | 🍑{firm} | 🔥{hab} | 😈{fet}"
        f"{sale_text}"
    )


def format_user_profile(user, idols_count):
    """Format user profile - works with dict"""
    safe_username = html.escape(user.get('username', 'Unknown').replace("_", " "))
    return (
        f"👤 <b>CEO: {safe_username}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Puntos: <code>{user.get('points', 0)}</code>\n"
        f"🏆 Victorias: <code>{user.get('wins', 0)}</code>\n"
        f"👯 Idols: <code>{idols_count}</code>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def format_market_listing(idol, template, owner_name):
    """Format market listing - works with dicts"""
    name = html.escape(idol.get("name", "Unknown").replace("_", " "))
    group = html.escape(idol.get("group_name", "Unknown Group").replace("_", " "))
    rarity = html.escape(idol.get("rarity", "C"))
    era = html.escape(idol.get("era", "Standard").replace("_", " "))
    
    # Escape underscores in owner_name
    safe_owner = html.escape(str(owner_name).replace("_", " "))

    return (
        f"🏷 <b>{name}</b> ({group}) [{era}] [{rarity}]\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"💰 Precio: <b>{idol.get('sale_price', 0)} pts</b>\n"
        f"👤 Vendedor: {safe_owner}"
    )
