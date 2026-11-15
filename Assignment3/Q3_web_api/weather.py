import sys, json, urllib.request
lat, lon = sys.argv[1], sys.argv[2]
url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
print("REQUEST:", url)
with urllib.request.urlopen(url, timeout=10) as r:
    print("STATUS:", r.status)
    data = json.load(r)
print("RESPONSE:", json.dumps(data, indent=2))
cw = data["current_weather"]
print(f"Temperature {cw['temperature']} C, wind {cw['windspeed']} km/h")
