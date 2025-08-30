import os
import requests
import pandas as pd
import folium

# === CONFIG ===
PDF_CSV = "aerzte_extracted_structured.csv"
OUTPUT_HTML = "arztpraxen_berlin.html"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # set in shell 
# if you run the code like: GOOGLE_MAPS_API_KEY=<AIg...insertyourapikeyhere> python map_doctors.py
# the variable is set for the execution, otherwise you will get an API-key error
GEOCODE_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("No GOOGLE_MAPS_API_KEY found. Please export it first.")

# === Load Data ===
df = pd.read_csv(PDF_CSV)

# Build address string
df["Adresse"] = (
    df["Straße"].astype(str).str.strip()
    + ", "
    + df["PLZ"].astype(str).str.strip()
    + " "
    + df["Ort"].astype(str).str.strip()
    + ", Deutschland"
)

# === Helper ===
def get_geocode(address):
    """Query Google Maps Geocoding API for one address, return (lat, lon)."""
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    response = requests.get(GEOCODE_API_URL, params=params)
    data = response.json()

    if data["status"] == "OK":
        loc = data["results"][0]["geometry"]["location"]
        print(f"[OK] {address} -> ({loc['lat']}, {loc['lng']})")
        return loc["lat"], loc["lng"]
    else:
        print(f"[FAIL] {address} -> status: {data['status']}, error: {data.get('error_message')}")
        return None, None

# === Test API Key with one known good address ===
print("\n--- Testing API key with a known address ---")
test_lat, test_lon = get_geocode("Chariteplatz 1, 10117 Berlin, Deutschland")
print(f"Test result: lat={test_lat}, lon={test_lon}\n")

if not test_lat or not test_lon:
    raise RuntimeError("API key test failed. Please check your key and billing settings.")

# === Geocode all addresses (verbose) ===
latitudes, longitudes = [], []
for addr in df["Adresse"]:
    lat, lon = get_geocode(addr)
    latitudes.append(lat)
    longitudes.append(lon)

df["Latitude"] = latitudes
df["Longitude"] = longitudes

# Drop failed rows
df = df.dropna(subset=["Latitude", "Longitude"])

print(f"\nTotal geocoded successfully: {len(df)} rows")

# === Build map ===
m = folium.Map(location=[52.52, 13.405], zoom_start=11, tiles="OpenStreetMap")

for _, row in df.iterrows():
    popup_text = f"{row.get('Vorname','')} {row.get('Name','')}<br>{row['Adresse']}"
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=4,
        color="red",
        fill=True,
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(m)

m.save(OUTPUT_HTML)
print(f"Map saved to {OUTPUT_HTML}")
