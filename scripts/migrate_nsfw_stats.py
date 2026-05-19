"""
Migra las keys de stats NSFW en data/idols.json de los nombres viejos a los nuevos.

Viejo -> Nuevo:
  sensitivity   -> sensualidad
  coqueteo      -> puteria
  firmeza_culo  -> firmeza
  kinky         -> fetiches

Ejecutar UNA VEZ antes de desplegar el bot actualizado.
"""

import json
import os
from pathlib import Path

IDOLS_FILE = Path(__file__).parent.parent / "data" / "idols.json"

MAPPING = {
    "sensitivity": "sensualidad",
    "coqueteo": "puteria",
    "firmeza_culo": "firmeza",
    "kinky": "fetiches",
}


def migrate():
    if not IDOLS_FILE.exists():
        print(f"[WARN] {IDOLS_FILE} no encontrado. Nada que migrar.")
        return

    with open(IDOLS_FILE, "r", encoding="utf-8") as f:
        idols = json.load(f)

    migrated_count = 0

    for idol_id, idol in idols.items():
        changed = False
        for old_key, new_key in MAPPING.items():
            if old_key in idol:
                value = idol.pop(old_key)
                idol[new_key] = value
                changed = True
        if changed:
            migrated_count += 1

    if migrated_count == 0:
        print("[OK] Ya esta migrado. No se encontraron keys viejas.")
        return

    # Backup
    backup_path = IDOLS_FILE.with_suffix(".json.bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(idols, f, indent=2, ensure_ascii=False)
    print(f"[BACKUP] Backup creado: {backup_path}")

    # Guardar migrado
    with open(IDOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(idols, f, indent=2, ensure_ascii=False)

    print(f"[OK] Migradas {migrated_count} idols.")
    print("   sensitivity -> sensualidad")
    print("   coqueteo    -> puteria")
    print("   firmeza_culo -> firmeza")
    print("   kinky       -> fetiches")


if __name__ == "__main__":
    migrate()
