#!/usr/bin/env python3
import sys, os, requests, json
sys.path.insert(0, '/opt/maxtorque')
from app.services.turn14 import get_turn14_token

token = get_turn14_token()
if not token:
    print("NO TOKEN"); sys.exit(1)

headers = {"Authorization": f"Bearer {token}"}
url = "https://apitest.turn14.com/v1/items/136317"
print(f"GET {url}")
resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print("Body:", resp.text[:500])
    sys.exit(1)

data = resp.json()
print("Keys:", list(data.keys()))
if 'data' in data:
    item = data['data']
    print("Item keys:", list(item.keys()))
    attrs = item.get('attributes', {})
    print("Attribute keys:", list(attrs.keys()))
    for k, v in attrs.items():
        print(f"{k} = {v}")
else:
    print("No 'data' in response")
    print(json.dumps(data, indent=2)[:1000])
