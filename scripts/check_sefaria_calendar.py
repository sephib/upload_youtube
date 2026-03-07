#!/usr/bin/env python3
# Quick script to check Sefaria calendar API for Torah readings
import httpx
import json

url = "https://www.sefaria.org/api/calendars"
response = httpx.get(url, timeout=30.0)
data = response.json()

print("Calendar Items:")
print(json.dumps(data.get('calendar_items', [])[:3], indent=2))
