import json
import os
from pathlib import Path

# Nombres genéricos a eliminar
generic_names = [
    "Rookie A", "Rookie B", 
    "Rising A", "Rising B", 
    "Elite A", "Elite B", 
    "Superstar A", "Superstar B", 
    "Goddess A", "Goddess B"
]

def clean_idols():
    # El archivo está en la carpeta data relativa a la raíz
    data_dir = Path("data")
    idols_file = data_dir / "idols.json"
    
    if not idols_file.exists():
        print("No se encontró el archivo idols.json. Tal vez no hay idols creadas aún.")
        return

    with open(idols_file, 'r', encoding='utf-8') as f:
        idols = json.load(f)

    original_count = len(idols)
    
    # Filtrar idols: mantener solo las que NO tengan nombres genéricos
    # Nota: el JSON guarda las idols en un diccionario con ID como llave
    cleaned_idols = {
        iid: idol for iid, idol in idols.items() 
        if idol.get("name") not in generic_names
    }

    new_count = len(cleaned_idols)
    deleted = original_count - new_count

    with open(idols_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_idols, f, indent=4)

    print(f"Limpieza completada.")
    print(f"Idols originales: {original_count}")
    print(f"Idols eliminadas (genéricas): {deleted}")
    print(f"Idols restantes (reales): {new_count}")

if __name__ == "__main__":
    clean_idols()
