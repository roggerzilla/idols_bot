
import re

file_path = r'c:\Users\josec\Documents\bot_idols_nuevo\scripts\seed_db.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Regex to find IdolTemplate(name="...", group_name="...", rarity="...", era="...")
pattern = r'IdolTemplate\(name="([^"]+)", group_name="([^"]+)", rarity="([^"]+)", era="([^"]+)"'
matches = re.findall(pattern, content)

rarity_map = {'C': [], 'B': [], 'A': [], 'S': [], 'SS': [], 'SSS': []}

excluded = ["Wendy", "Taeyeon"]

for name, group, rarity, era in matches:
    if name in excluded:
        continue
    if rarity in rarity_map:
        # Avoid exact duplicates (name, group) in the same rarity
        entry = (name, group, era)
        if entry not in rarity_map[rarity]:
            rarity_map[rarity].append(entry)

print("template_names = {")
for rarity in ['C', 'B', 'A', 'S', 'SS', 'SSS']:
    print(f"    '{rarity}': [")
    for name, group, era in rarity_map[rarity]:
        if era == "Standard":
            print(f"        (\"{name}\", \"{group}\"),")
        else:
            print(f"        (\"{name}\", \"{group}\", \"{era}\"),")
    print("    ],")
print("}")
