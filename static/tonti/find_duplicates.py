import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver toutes les définitions de routes
routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", content)
endpoints = re.findall(r"def (\w+)\(\):", content)

print("=" * 60)
print("ROUTES TROUVÉES:")
print("=" * 60)
for route in routes:
    print(f"  {route}")

print("\n" + "=" * 60)
print("FONCTIONS TROUVÉES:")
print("=" * 60)
for endpoint in endpoints:
    print(f"  {endpoint}")

# Trouver les doublons
from collections import Counter
route_counts = Counter(routes)
endpoint_counts = Counter(endpoints)

print("\n" + "=" * 60)
print("DOUBLONS DE ROUTES:")
print("=" * 60)
for route, count in route_counts.items():
    if count > 1:
        print(f"  {route}: {count} fois")

print("\n" + "=" * 60)
print("DOUBLONS DE FONCTIONS:")
print("=" * 60)
for endpoint, count in endpoint_counts.items():
    if count > 1:
        print(f"  {endpoint}: {count} fois")