"""
Sistema de almacenamiento en JSON para el bot de idols.
Reemplaza a SQLAlchemy para facilitar edición manual en PythonAnywhere.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Rutas de archivos JSON
DATA_DIR = Path(__file__).parent / "data"
USERS_FILE = DATA_DIR / "users.json"
IDOLS_FILE = DATA_DIR / "idols.json"
TEMPLATES_FILE = DATA_DIR / "templates.json"
EVENTS_FILE = DATA_DIR / "events.json"
GROUPS_FILE = DATA_DIR / "groups.json"

# Asegurar que el directorio existe
DATA_DIR.mkdir(exist_ok=True)


def load_json(filepath: Path, default: Any = None) -> Any:
    """Carga un archivo JSON o devuelve el valor por defecto si no existe."""
    if not filepath.exists():
        return default if default is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}


def save_json(filepath: Path, data: Any) -> None:
    """Guarda datos en un archivo JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── USERS ──────────────────────────────────────────────────────

def get_all_users() -> Dict[int, dict]:
    """Obtiene todos los usuarios."""
    return load_json(USERS_FILE, {})


def get_user(user_id: int) -> Optional[dict]:
    """Obtiene un usuario por ID."""
    users = get_all_users()
    return users.get(str(user_id))


def process_maintenance(user_id: int) -> dict:
    """Deduce fees de mantenimiento (por rareza); pone idols en hiatus si broke"""
    from config import MAINTENANCE_COST_BY_RARITY

    user = get_user(user_id)
    if not user:
        return {"success": False, "error": "user_not_found"}

    idols = get_user_idols(user_id)
    total_fee = sum(MAINTENANCE_COST_BY_RARITY.get(idol.get("rarity", "C"), 50) for idol in idols)

    if user["points"] >= total_fee:
        deduct_points(user_id, total_fee)
        return {"success": True, "fee_paid": total_fee}
    else:
        for idol in idols:
            update_idol(idol["id"], status="hiatus")

        for idol in idols:
            idol["energy"] = min(100, idol["energy"] + 10)
            update_idol(idol["id"], **{"energy": idol["energy"]})

        return {"success": True, "fee_paid": total_fee, "hiatus_applied": True}


def create_user(user_id: int, username: str = None) -> dict:
    """Crea un nuevo usuario."""
    users = get_all_users()

    # Verificar si ya existe
    if user_id in users:
        return users[user_id]

    new_user = {
        "id": user_id,
        "username": username or f"user_{user_id}",
        "points": 1000,
        "wins": 0,
        "last_maintenance_check": datetime.utcnow().isoformat(),
        "idols": []
    }

    users[str(user_id)] = new_user
    save_json(USERS_FILE, users)

    # Verificar que se guardó correctamente
    saved_user = get_user(user_id)
    return saved_user if saved_user else new_user


def update_user(user_id: int, **kwargs) -> Optional[dict]:
    """Actualiza un usuario."""
    users = get_all_users()
    key = str(user_id)
    if key not in users:
        return None

    for k, value in kwargs.items():
        users[key][k] = value

    save_json(USERS_FILE, users)
    return users[key]


def add_points(user_id: int, amount: int) -> Optional[dict]:
    """Añade puntos a un usuario."""
    user = get_user(user_id)
    if not user:
        create_user(user_id)
        user = get_user(user_id)

    user["points"] += amount
    all_users = get_all_users()
    all_users[str(user_id)] = user
    save_json(USERS_FILE, all_users)
    return user


def deduct_points(user_id: int, amount: int) -> Optional[dict]:
    """Dedica puntos a un usuario."""
    user = get_user(user_id)
    if not user:
        create_user(user_id)
        user = get_user(user_id)

    user["points"] -= amount
    all_users = get_all_users()
    all_users[str(user_id)] = user
    save_json(USERS_FILE, all_users)
    return user


# ─── IDOLS ──────────────────────────────────────────────────────

def get_all_idols() -> Dict[int, dict]:
    """Obtiene todas las idols."""
    return load_json(IDOLS_FILE, {})


def get_user_idols(user_id: int) -> List[dict]:
    """Obtiene todas las idols de un usuario y sincroniza fotos si es necesario."""
    all_idols = get_all_idols()
    user_idols = [idol for idol in all_idols.values() if idol.get("user_id") == user_id]
    
    # Auto-parche: Sincronizar file_id desde la plantilla si es distinto
    templates = get_all_templates()
    for idol in user_idols:
        tid = str(idol.get("template_id"))
        if tid in templates:
            t_file_id = templates[tid].get("file_id")
            if t_file_id:
                t_file_id = t_file_id.strip() # Limpiar espacios por si acaso
                if idol.get("file_id") != t_file_id:
                    idol["file_id"] = t_file_id
                    update_idol(idol["id"], file_id=t_file_id)
            
    return user_idols


def create_idol(
    user_id: int,
    template_id: int,
    name: str,
    group_name: str,
    rarity: str,
    base_vocal: int,
    base_dance: int,
    base_rap: int,
    era: str = "Standard",
    file_id: str = None
) -> dict:
    """Crea una nueva idol."""
    idols = get_all_idols()
    
    # Si no hay file_id, buscarlo en la plantilla
    if not file_id:
        templates = get_all_templates()
        if str(template_id) in templates:
            file_id = templates[str(template_id)].get("file_id")
    # Usar timestamp para evitar colisiones de IDs al borrar/crear rápidamente
    import time
    idol_id = int(time.time() * 1000)
    while str(idol_id) in idols:
        idol_id += 1

    now = datetime.utcnow()
    expiry = now + timedelta(days=7)

    idol = {
        "id": idol_id,
        "user_id": user_id,
        "template_id": template_id,
        "name": name,
        "group_name": group_name,
        "rarity": rarity,
        "era": era,
        "vocal": base_vocal,
        "dance": base_dance,
        "rap": base_rap,
        "file_id": file_id,
        "morale": 100,
        "energy": 100,
        "sensualidad": 50,
        "puteria": 50,
        "firmeza": 50,
        "habilidades_cama": 50,
        "fetiches": 50,
        "status": "active",
        "busy_until": None,
        "contract_expiry": expiry.isoformat(),
        "for_sale": False,
        "sale_price": 0
    }

    idols[str(idol_id)] = idol
    save_json(IDOLS_FILE, idols)

    # Actualizar lista de idols del usuario
    user = get_user(user_id)
    if user:
        user["idols"].append(idol_id)
        update_user(user_id, **{"idols": user["idols"]})

    return idol


def get_idol(idol_id: int) -> Optional[dict]:
    """Obtiene una idol por ID."""
    idols = get_all_idols()
    return idols.get(str(idol_id))


def update_idol(idol_id: int, **kwargs) -> Optional[dict]:
    """Actualiza una idol."""
    idols = get_all_idols()
    key = str(idol_id)
    if key not in idols:
        return None

    for k, value in kwargs.items():
        idols[key][k] = value

    save_json(IDOLS_FILE, idols)
    return idols[key]


def delete_idol(idol_id: int) -> bool:
    """Elimina una idol."""
    idols = get_all_idols()
    key = str(idol_id)
    if key not in idols:
        return False

    user_id = idols[key]["user_id"]
    del idols[key]
    save_json(IDOLS_FILE, idols)

    # Actualizar lista de idols del usuario
    user = get_user(user_id)
    if user:
        # Manejar tanto int como str en la lista de IDs del usuario
        original_len = len(user["idols"])
        user["idols"] = [i for i in user["idols"] if str(i) != str(idol_id)]
        if len(user["idols"]) != original_len:
            update_user(user_id, **{"idols": user["idols"]})

    return True


def delete_idols_bulk(idol_ids: List[int]) -> bool:
    """Elimina múltiples idols en una sola operación de guardado."""
    idols = get_all_idols()
    users_to_update = {} # user_id -> set of idol_ids to remove

    for iid in idol_ids:
        key = str(iid)
        if key in idols:
            u_id = idols[key]["user_id"]
            if u_id not in users_to_update:
                users_to_update[u_id] = []
            users_to_update[u_id].append(iid)
            del idols[key]

    if not users_to_update:
        return False

    save_json(IDOLS_FILE, idols)

    # Actualizar usuarios
    all_users = get_all_users()
    for u_id, iids_to_del in users_to_update.items():
        u_key = str(u_id)
        if u_key in all_users:
            user = all_users[u_key]
            # Convertir todos a str para comparar
            str_iids_to_del = [str(i) for i in iids_to_del]
            user["idols"] = [i for i in user["idols"] if str(i) not in str_iids_to_del]
            all_users[u_key] = user
    
    save_json(USERS_FILE, all_users)
    return True


# ─── GLOBAL EVENTS ──────────────────────────────────────────────

def get_all_events() -> Dict[int, dict]:
    """Obtiene todos los eventos globales."""
    return load_json(EVENTS_FILE, {})


def create_event(
    event_type: str,
    description: str,
    points: int,
) -> Optional[dict]:
    """Crea un nuevo evento global."""
    events = get_all_events()
    event_id = len(events) + 1

    now = datetime.utcnow()

    event = {
        "id": event_id,
        "event_type": event_type,
        "description": description,
        "points": points,
        "is_taken": False,
        "taken_by_user_id": None,
        "chat_id": None,
        "message_id": None,
        "created_at": now.isoformat()
    }

    events[str(event_id)] = event
    save_json(EVENTS_FILE, events)
    return event


def get_event(event_id: int) -> Optional[dict]:
    """Obtiene un evento por ID."""
    events = get_all_events()
    return events.get(str(event_id))


def take_event(event_id: int, user_id: int) -> bool:
    """Marca un evento como tomado por un usuario."""
    events = get_all_events()
    key = str(event_id)
    if key not in events:
        return False

    events[key]["is_taken"] = True
    events[key]["taken_by_user_id"] = user_id
    save_json(EVENTS_FILE, events)
    return True


# ─── BOT GROUPS ─────────────────────────────────────────────────

def get_all_groups() -> Dict[int, dict]:
    """Obtiene todos los grupos."""
    return load_json(GROUPS_FILE, {})


def add_group(chat_id: int, title: str = "") -> Optional[dict]:
    """Añade un grupo."""
    groups = get_all_groups()

    if str(chat_id) in groups:
        return groups[str(chat_id)]

    now = datetime.utcnow()

    groups[str(chat_id)] = {
        "chat_id": chat_id,
        "title": title or f"Group_{chat_id}",
        "added_at": now.isoformat()
    }
    save_json(GROUPS_FILE, groups)
    return groups[str(chat_id)]


def get_group(chat_id: int) -> Optional[dict]:
    """Obtiene un grupo por chat_id."""
    groups = get_all_groups()
    return groups.get(str(chat_id))


# ─── EVENT REWARD CALCULATION ──────────────────────────────────

def calculate_event_reward(user_id: int, idol_id: int) -> dict | None:
    """Calcula recompensa basada en rareza + stats totales (básicos + NSFW)"""
    idols = get_all_idols()
    key = str(idol_id)
    if key not in idols:
        return None

    idol = idols[key]
    if idol["user_id"] != user_id:
        return None

    from config import RARITY_CONFIG

    # Stats básicos + NSFW
    basic_stats = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    nsfw_stats = (idol.get("sensualidad", 50) + idol.get("puteria", 50) +
                  idol.get("firmeza", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("fetiches", 50))
    total_stats = basic_stats + nsfw_stats

    # Base points según rareza
    rarity_mult = RARITY_CONFIG[idol["rarity"]]["mult"]
    base_points = int(1000 * rarity_mult)

    # Bonus por stats (cada 100 stats da +10% de bonus)
    stat_bonus = 1 + (total_stats / 1000)

    reward = int(base_points * stat_bonus)

    return {
        "reward": reward,
        "base_points": base_points,
        "rarity_mult": rarity_mult,
        "stat_bonus": round(stat_bonus, 2),
        "total_stats": total_stats,
        "basic_stats": basic_stats,
        "nsfw_stats": nsfw_stats,
        "idol_name": idol["name"],
        "rarity": idol["rarity"]
    }


# ─── MIGRATION FROM SQLITE ─────────────────────────────────────

def migrate_from_sqlite(sqlite_db_path: str = "idols_bot.db") -> bool:
    """
    Migra datos desde SQLite a JSON.
    Ejecutar una vez para migrar datos existentes.
    """
    import sqlite3

    if not os.path.exists(sqlite_db_path):
        print(f"⚠️  {sqlite_db_path} no encontrado")
        return False

    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()

    try:
        # Migrar usuarios
        cursor.execute("SELECT id, username, points, wins FROM users")
        rows = cursor.fetchall()
        users = {}
        for row in rows:
            user_id, username, points, wins = row
            users[user_id] = {
                "id": user_id,
                "username": username or f"user_{user_id}",
                "points": points,
                "wins": wins,
                "last_maintenance_check": datetime.utcnow().isoformat(),
                "idols": []
            }
        save_json(USERS_FILE, users)
        print(f"✅ Migrados {len(users)} usuarios")

        # Migrar idols
        cursor.execute("""
            SELECT id, user_id, template_id, vocal, dance, rap, morale, energy,
                   status, busy_until, contract_expiry, for_sale, sale_price
            FROM user_idols
        """)
        rows = cursor.fetchall()
        idols = {}

        # Obtener templates para nombre y grupo
        cursor.execute("SELECT id, name, group_name, rarity, era, base_vocal, base_dance, base_rap FROM idol_templates")
        templates = {row[0]: row for row in cursor.fetchall()}

        for row in rows:
            idol_id, user_id, template_id, vocal, dance, rap, morale, energy, \
                status, busy_until, contract_expiry, for_sale, sale_price = row

            tmpl = templates.get(template_id, ("Unknown", "Unknown Group", "C", "Standard", 10, 10, 10))
            name, group_name, rarity, era, base_vocal, base_dance, base_rap = tmpl

            idols[idol_id] = {
                "id": idol_id,
                "user_id": user_id,
                "template_id": template_id,
                "name": name.replace("_", " "),
                "group_name": group_name.replace("_", " "),
                "rarity": rarity,
                "era": era or "Standard",
                "vocal": vocal or base_vocal,
                "dance": dance or base_dance,
                "rap": rap or base_rap,
                "morale": morale or 100,
                "energy": energy or 100,
                "sensualidad": 50,
                "puteria": 50,
                "firmeza": 50,
                "habilidades_cama": 50,
                "fetiches": 50,
                "status": status or "active",
                "busy_until": busy_until,
                "contract_expiry": contract_expiry,
                "for_sale": for_sale or False,
                "sale_price": sale_price or 0
            }

        save_json(IDOLS_FILE, idols)
        print(f"✅ Migrados {len(idols)} idols")

        # Actualizar lista de idols en usuarios
        updated_users = {}
        for user_id in users:
            user = users[user_id].copy()
            user["idols"] = [iid for iid, idol in idols.items() if idol["user_id"] == user_id]
            updated_users[user_id] = user
        save_json(USERS_FILE, updated_users)

        # Migrar eventos globales
        cursor.execute("SELECT id, event_type, description, points, is_taken, taken_by_user_id, chat_id, message_id, created_at FROM global_events")
        rows = cursor.fetchall()
        events = {}
        for row in rows:
            event_id, event_type, description, points, is_taken, taken_by_user_id, \
                chat_id, message_id, created_at = row

            events[event_id] = {
                "id": event_id,
                "event_type": event_type,
                "description": description or "",
                "points": points,
                "is_taken": is_taken or False,
                "taken_by_user_id": taken_by_user_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "created_at": created_at or datetime.utcnow().isoformat()
            }
        save_json(EVENTS_FILE, events)
        print(f"✅ Migrados {len(events)} eventos")

        # Migrar grupos
        cursor.execute("SELECT chat_id, title, added_at FROM bot_groups")
        rows = cursor.fetchall()
        groups = {}
        for row in rows:
            chat_id, title, added_at = row
            groups[chat_id] = {
                "chat_id": chat_id,
                "title": title or f"Group_{chat_id}",
                "added_at": added_at or datetime.utcnow().isoformat()
            }
        save_json(GROUPS_FILE, groups)
        print(f"✅ Migrados {len(groups)} grupos")

        conn.close()
        print("\n🎉 ¡Migración completada!")
        return True

    except Exception as e:
        print(f"❌ Error en migración: {e}")
        conn.close()
        return False


# ─── PRODUCING IDOLS (SEPARATE LIMITS) ─────────────────────────

def get_active_comeback_idols(user_id: int) -> List[dict]:
    """Devuelve idols que están haciendo comeback ahora mismo."""
    from datetime import datetime
    idols = get_user_idols(user_id)
    result = []
    for idol in idols:
        if idol.get("status") == "comeback" and idol.get("busy_until"):
            try:
                busy_until = datetime.fromisoformat(idol["busy_until"])
                if datetime.utcnow() < busy_until:
                    result.append(idol)
            except (ValueError, TypeError):
                pass
    return result


def get_active_tour_idols(user_id: int) -> List[dict]:
    """Devuelve idols que están en tour ahora mismo."""
    from datetime import datetime
    idols = get_user_idols(user_id)
    result = []
    for idol in idols:
        if idol.get("status") == "world_tour" and idol.get("busy_until"):
            try:
                busy_until = datetime.fromisoformat(idol["busy_until"])
                if datetime.utcnow() < busy_until:
                    result.append(idol)
            except (ValueError, TypeError):
                pass
    return result


def can_start_comeback(user_id: int) -> bool:
    """True si el usuario tiene menos de 3 comebacks activos."""
    from config import MAX_COMEBACK_IDOLS
    return len(get_active_comeback_idols(user_id)) < MAX_COMEBACK_IDOLS


def can_start_tour(user_id: int) -> bool:
    """True si el usuario tiene menos de 3 tours activos."""
    from config import MAX_TOUR_IDOLS
    return len(get_active_tour_idols(user_id)) < MAX_TOUR_IDOLS


# ─── TEMPLATES ──────────────────────────────────────────────────

def get_all_templates() -> Dict[str, dict]:
    """Obtiene todas las plantillas de idols."""
    return load_json(TEMPLATES_FILE, {})


def get_template(template_id: int) -> Optional[dict]:
    """Obtiene una plantilla por ID."""
    templates = get_all_templates()
    return templates.get(str(template_id))


# ─── INIT ──────────────────────────────────────────────────────

def init_storage():
    """Inicializa los archivos JSON si no existen."""
    if not USERS_FILE.exists():
        save_json(USERS_FILE, {})
    if not IDOLS_FILE.exists():
        save_json(IDOLS_FILE, {})
    if not TEMPLATES_FILE.exists():
        save_json(TEMPLATES_FILE, {})
    if not EVENTS_FILE.exists():
        save_json(EVENTS_FILE, {})
    if not GROUPS_FILE.exists():
        save_json(GROUPS_FILE, {})
