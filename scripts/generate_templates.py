"""
Generador de templates para todas las rarezas.

Lee data/templates.json, agrupa por (name, era), y genera versiones
C, B, A, S, SS escalando las stats proporcionalmente.

Las idols SSS se quedan exclusivas y no se generan en otras rarezas.
"""

import json
import math
import shutil
from pathlib import Path

TEMPLATES_FILE = Path(__file__).parent.parent / "data" / "templates.json"
BACKUP_FILE = Path(__file__).parent.parent / "data" / "templates.json.bak"

# Multipliers para escalar stats desde SS (0.90) hacia abajo
RARITY_MULTIPLIERS = {
    'C': 0.30,
    'B': 0.45,
    'A': 0.60,
    'S': 0.75,
    'SS': 0.90,
}

# Rango mínimo/máximo de stats por rareza
STAT_RANGES = {
    'C': (10, 40),
    'B': (15, 55),
    'A': (25, 70),
    'S': (40, 85),
    'SS': (60, 95),
}

# Rarezas a generar (SSS se queda exclusivo)
RATINGS = ['C', 'B', 'A', 'S', 'SS']


def load_templates():
    with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_templates(templates):
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)


def backup():
    shutil.copy2(TEMPLATES_FILE, BACKUP_FILE)
    print(f"[BACKUP] {BACKUP_FILE}")


def scale_stat(value, multiplier, min_val, max_val):
    """Escala una stat aplicando el multiplier y respetando el rango."""
    scaled = round(value * multiplier)
    return max(min_val, min(max_val, scaled))


def main():
    print("[LOAD] Cargando templates...")
    templates = load_templates()
    print(f"[INFO] {len(templates)} templates actuales")

    # Separar SSS (exclusivos) del resto
    sss_templates = {}
    other_templates = {}

    for tid, t in templates.items():
        if t.get("rarity") == "SSS":
            sss_templates[tid] = t
        else:
            other_templates[tid] = t

    print(f"[INFO] {len(sss_templates)} templates SSS (exclusivos)")
    print(f"[INFO] {len(other_templates)} templates no-SSS")

    # Agrupar por (name, era)
    groups = {}
    for tid, t in other_templates.items():
        key = (t["name"], t.get("era", "Standard"))
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    print(f"[INFO] {len(groups)} grupos únicos (name + era)")

    # Para cada grupo, generar C, B, A, S, SS
    new_templates = {}
    next_id = max(int(tid) for tid in templates.keys()) + 1

    generated_count = 0
    skipped_count = 0

    for (name, era), group in groups.items():
        # Encontrar la versión con mayor total de stats como referencia
        best = max(group, key=lambda t: t.get("base_vocal", 0) + t.get("base_dance", 0) + t.get("base_rap", 0))
        group_name = best.get("group_name", "Unknown")

        # Para cada rareza, generar template con stats escaladas
        for rarity in RATINGS:
            mult = RARITY_MULTIPLIERS[rarity]
            min_stat, max_stat = STAT_RANGES[rarity]

            vocal = scale_stat(best.get("base_vocal", 10), mult, min_stat, max_stat)
            dance = scale_stat(best.get("base_dance", 10), mult, min_stat, max_stat)
            rap = scale_stat(best.get("base_rap", 10), mult, min_stat, max_stat)

            # Verificar si ya existe un template con este (name, era, rarity)
            existing = None
            for tid, t in other_templates.items():
                if (t["name"] == name and
                    t.get("era", "Standard") == era and
                    t.get("rarity") == rarity):
                    existing = t
                    break

            if existing:
                # Ya existe, actualizar stats pero mantener file_id y can_gacha
                existing["base_vocal"] = vocal
                existing["base_dance"] = dance
                existing["base_rap"] = rap
                existing["can_gacha"] = True
                new_templates[existing["id"]] = existing
                skipped_count += 1
            else:
                # Crear nuevo template
                new_id = next_id
                next_id += 1

                new_templates[new_id] = {
                    "id": new_id,
                    "name": name,
                    "group_name": group_name,
                    "rarity": rarity,
                    "era": era,
                    "base_vocal": vocal,
                    "base_dance": dance,
                    "base_rap": rap,
                    "can_gacha": True,
                    "file_id": None,
                }
                generated_count += 1

    # Combinar: nuevos + SSS exclusivos
    final_templates = {}
    for tid, t in new_templates.items():
        final_templates[str(tid)] = t

    for tid, t in sss_templates.items():
        final_templates[str(tid)] = t

    # Backup y guardar
    backup()
    save_templates(final_templates)

    print(f"\n[RESULT]")
    print(f"  Templates generados: {generated_count}")
    print(f"  Templates existentes actualizados: {skipped_count}")
    print(f"  Templates SSS (exclusivos): {len(sss_templates)}")
    print(f"  Total templates: {len(final_templates)}")
    print(f"\n[OK] Templates guardados en {TEMPLATES_FILE}")
    print(f"[OK] Backup en {BACKUP_FILE}")


if __name__ == "__main__":
    main()
