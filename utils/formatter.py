"""
Formateadores usando almacenamiento JSON (dicts).
"""

from datetime import datetime


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

    name = idol.get("name", "Unknown").replace("_", " ")
    group = idol.get("group_name", "Unknown Group").replace("_", " ")
    rarity = idol.get("rarity", "C")
    era = idol.get("era", "Standard")

    # NSFW Stats
    sens = idol.get("sensitivity", 50)
    coq = idol.get("coqueteo", 50)
    firm = idol.get("firmeza_culo", 50)
    hab = idol.get("habilidades_cama", 50)
    kin = idol.get("kinky", 50)

    return (
        f"{header}"
        f"🌟 *{name}* ({group}) \\[{era}] \\[{rarity}]\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{status_emoji} Estado: {status_text}\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"❤️ Moral: {morale_bars} {morale}/100\n"
        f"⚡ Energía: {energy_bars} {energy}/100\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔞 ❤️{sens} | 💕{coq} | 🍑{firm} | 🔥{hab} | 😈{kin}"
        f"{sale_text}"
    )


def format_user_profile(user, idols_count):
    """Format user profile - works with dict"""
    return (
        f"👤 *CEO: {user.get('username', 'Unknown')}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Puntos: `{user.get('points', 0)}`\n"
        f"🏆 Victorias: `{user.get('wins', 0)}`\n"
        f"👯 Idols: `{idols_count}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def format_market_listing(idol, template, owner_name):
    """Format market listing - works with dicts"""
    name = idol.get("name", "Unknown").replace("_", " ")
    group = idol.get("group_name", "Unknown Group").replace("_", " ")
    rarity = idol.get("rarity", "C")
    era = idol.get("era", "Standard")
    
    # Escape underscores in owner_name
    safe_owner = str(owner_name).replace("_", "\\_")

    return (
        f"🏷 *{name}* ({group}) \\[{era}] \\[{rarity}]\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"💰 Precio: {idol.get('sale_price', 0)} pts\n"
        f"👤 Vendedor: {safe_owner}"
    )
