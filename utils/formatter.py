import datetime
from models import IdolStatus

def format_idol_card(idol, template, idx=None, total=None):
    """Compact idol card for the flat navigation UI"""
    status_emoji = {
        "ACTIVE": "✅",
        "HIATUS": "😴",
        "WORLD_TOUR": "✈️"
    }.get(idol.status.name, "❓")
    
    status_text = idol.status.value.title()
    if idol.status == IdolStatus.WORLD_TOUR and idol.busy_until:
        now = datetime.datetime.utcnow()
        if now < idol.busy_until:
            rem = idol.busy_until - now
            hours, remainder = divmod(rem.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            status_text = f"En Tour (Libre en {hours}h {minutes}m)"
    
    # Morale bar
    morale_bars = "█" * (idol.morale // 10) + "░" * (10 - idol.morale // 10)
    energy_bars = "█" * (idol.energy // 10) + "░" * (10 - idol.energy // 10)
    
    header = ""
    if idx is not None and total is not None:
        header = f"📋 Idol {idx}/{total}\n"
    
    sale_text = ""
    if idol.for_sale:
        sale_text = f"\n🏷️ *EN VENTA:* `{idol.sale_price} pts`"
    
    return (
        f"{header}"
        f"🌟 *{template.name}* ({template.group_name}) [{template.rarity}]\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{status_emoji} Estado: {status_text}\n"
        f"🎤 `{idol.vocal}` | 💃 `{idol.dance}` | 🎧 `{idol.rap}`\n"
        f"❤️ Moral: [{morale_bars}] `{idol.morale}`\n"
        f"⚡ Energía: [{energy_bars}] `{idol.energy}`"
        f"{sale_text}"
    )

def format_user_profile(user, idols_count):
    return (
        f"👤 *CEO: {user.username}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Puntos: `{user.points}`\n"
        f"🏆 Victorias: `{user.wins}`\n"
        f"👯 Idols: `{idols_count}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def format_market_listing(idol, template, owner_name):
    return (
        f"🏷️ *{template.name}* ({template.group_name}) [{template.rarity}]\n"
        f"🎤 `{idol.vocal}` | 💃 `{idol.dance}` | 🎧 `{idol.rap}`\n"
        f"💰 Precio: `{idol.sale_price} pts`\n"
        f"👤 Vendedor: {owner_name}"
    )
