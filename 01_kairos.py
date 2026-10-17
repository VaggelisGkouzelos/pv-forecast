# ============================================================
# 01_kairos.py
# Κατεβάζει δεδομένα καιρού για τη Σοφιάδα Δομοκού από το Open-Meteo
# (δωρεάν, χωρίς κλειδί) και φτιάχνει ένα γράφημα ηλιακής ακτινοβολίας.
# ============================================================

import requests                  # για να ζητήσουμε δεδομένα από το internet
import pandas as pd              # για να τα βάλουμε σε πίνακα
import matplotlib.pyplot as plt  # για να φτιάξουμε γράφημα

# --- 1. Ρυθμίσεις: πού και τι θέλουμε ---
from config import LAT, LON  # θέση πάρκου (από config.py / .env)

# Η "διεύθυνση" της υπηρεσίας καιρού
url = "https://api.open-meteo.com/v1/forecast"

# Οι παράμετροι που στέλνουμε, σαν να συμπληρώνουμε μια φόρμα
params = {
    "latitude": LAT,
    "longitude": LON,
    # Ωριαία δεδομένα που μας ενδιαφέρουν για φωτοβολταϊκά:
    #   shortwave_radiation = ηλιακή ακτινοβολία (W/m²), το πιο σημαντικό!
    #   temperature_2m      = θερμοκρασία (τα πάνελ αποδίδουν λιγότερο στη ζέστη)
    #   cloud_cover         = νεφοκάλυψη (%)
    "hourly": "shortwave_radiation,temperature_2m,cloud_cover",
    "past_days": 30,       # τις τελευταίες 30 μέρες (ιστορικό)
    "forecast_days": 3,    # και πρόβλεψη για τις επόμενες 3
    "timezone": "Europe/Athens",
}

# --- 2. Στέλνουμε το αίτημα και παίρνουμε απάντηση ---
print("Κατεβάζω δεδομένα καιρού...")
response = requests.get(url, params=params, timeout=30)
data = response.json()   # η απάντηση έρχεται σε μορφή JSON (σαν λεξικό)

# --- 3. Τα βάζουμε σε πίνακα (DataFrame) ---
df = pd.DataFrame(data["hourly"])        # κάθε γραμμή = μία ώρα
df["time"] = pd.to_datetime(df["time"])  # μετατροπή κειμένου σε ημερομηνία

# Δείχνουμε τις πρώτες γραμμές και πόσες έχουμε συνολικά
print(df.head())
print(f"\nΣύνολο ωρών: {len(df)}")

# Αποθηκεύουμε σε αρχείο CSV για να το χρησιμοποιήσουμε αργότερα
df.to_csv("kairos_sofiada.csv", index=False)
print("Αποθηκεύτηκε στο kairos_sofiada.csv")

# --- 4. Γράφημα ---
plt.figure(figsize=(14, 5))
plt.plot(df["time"], df["shortwave_radiation"], color="orange")
plt.title("Ηλιακή ακτινοβολία - Σοφιάδα Δομοκού (30 μέρες + 3 μέρες πρόβλεψη)")
plt.xlabel("Ημερομηνία")
plt.ylabel("Ακτινοβολία (W/m²)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("aktinovolia.png", dpi=120)   # αποθηκεύουμε και ως εικόνα
print("Το γράφημα αποθηκεύτηκε στο aktinovolia.png")
plt.show()   # ανοίγει το παράθυρο με το γράφημα
