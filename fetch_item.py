#!/usr/bin/env python3
import sys, os, requests
sys.path.insert(0, '/opt/maxtorque')
from app.services.turn14 import get_turn14_token

token = get_turn14_token()
if not token:
    print("Failed to get token")
    sys.exit(1)

headers = {"Authorization": f"Bearer {token}"}
# Fetch the specific item by Turn14 ID
resp = requests.get(f"https://apitest.turn14.com/v1/items/136317", headers=headers, timeout=10)
if resp.status_code != 200:
    print(f"Error: {resp.status_code}")
    print(resp.text)
    sys.exit(1)

data = resp.json()
attrs = data.get('attributes', {})
print("Attributes for item 136317 (ede41137):")
for k, v in attrs.items():
    print(f"  {k}: {v}")
