import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import create_idol, get_all_templates

def give_idol(user_id, identifier, era_filter=None):
    templates = get_all_templates()
    found_template = None

    # 1. Intentar buscar por ID si el identificador es un número
    if identifier.isdigit():
        if identifier in templates:
            found_template = templates[identifier]
        else:
            print(f"❌ No existe la plantilla con ID {identifier}")
            return

    # 2. Si no es ID, buscar por nombre y opcionalmente Era
    if not found_template:
        matches = []
        for tid, t in templates.items():
            if t["name"].lower() == identifier.lower():
                # Si se especificó una Era, filtrar por ella
                if era_filter:
                    if t.get("era", "").lower() == era_filter.lower():
                        matches.append(t)
                else:
                    matches.append(t)
        
        if len(matches) == 0:
            print(f"❌ No se encontró ninguna idol llamada '{identifier}'" + (f" en la era '{era_filter}'" if era_filter else ""))
            return
        elif len(matches) > 1:
            print(f"⚠️ Se encontraron {len(matches)} versiones de '{identifier}':")
            for m in matches:
                print(f"   - ID: {m['id']} | Era: {m.get('era', 'Standard')} | Rareza: {m['rarity']}")
            print("\n💡 Por favor, usa el ID o especifica la Era así: python scripts/give_idol.py <user_id> <nombre> <era>")
            return
        else:
            found_template = matches[0]

    # Crear la idol para el usuario
    new_idol = create_idol(
        user_id=int(user_id),
        template_id=found_template["id"],
        name=found_template["name"],
        group_name=found_template["group_name"],
        rarity=found_template["rarity"],
        base_vocal=found_template["base_vocal"],
        base_dance=found_template["base_dance"],
        base_rap=found_template["base_rap"],
        era=found_template.get("era", "Standard")
    )
    
    print(f"✅ ¡Éxito! Se ha asignado {found_template['name']} ({found_template['rarity']}) - Era: {found_template.get('era', 'Standard')} al usuario {user_id}.")
    print(f"🆔 ID de la nueva idol en el inventario: {new_idol['id']}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print("  Por ID:     python give_idol.py <user_id> <template_id>")
        print("  Por Nombre: python give_idol.py <user_id> <nombre> [era]")
    else:
        user_id = sys.argv[1]
        identifier = sys.argv[2]
        era_filter = sys.argv[3] if len(sys.argv) > 3 else None
        give_idol(user_id, identifier, era_filter)
