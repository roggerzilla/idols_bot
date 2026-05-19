import json
from collections import Counter

with open('data/templates.json') as f:
    t = json.load(f)

rc = Counter(v['rarity'] for v in t.values())
print('Templates por rareza:')
for r in ['C','B','A','S','SS','SSS']:
    print(f'  {r}: {rc.get(r,0)}')
print(f'  Total: {len(t)}')

print()
print('Karina Waterbomb:')
for tid, v in sorted(t.items(), key=lambda x: int(x[0])):
    if v['name'] == 'Karina' and v['era'] == 'Waterbomb':
        print(f'  ID {tid}: {v["rarity"]} V:{v["base_vocal"]} D:{v["base_dance"]} R:{v["base_rap"]}')

print()
print('TWICE TT:')
for tid, v in sorted(t.items(), key=lambda x: int(x[0])):
    if v['era'] == 'TT' and v['group_name'] == 'TWICE':
        print(f'  ID {tid}: {v["name"]} {v["rarity"]} V:{v["base_vocal"]} D:{v["base_dance"]} R:{v["base_rap"]}')
