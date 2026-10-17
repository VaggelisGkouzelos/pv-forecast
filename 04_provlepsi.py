# ============================================================
# 04_provlepsi.py
# ΒΗΜΑ 5: ΠΡΟΒΛΕΨΗ ΓΙΑ ΑΥΡΙΟ (και μεθαύριο)
#
# 1. Εκπαιδεύουμε το ΤΕΛΙΚΟ μοντέλο σε ΟΛΕΣ τις καθαρές ώρες (25 μέρες).
#    (Στα βήματα 2-3 κρατούσαμε μέρες στην άκρη για "εξετάσεις". Τώρα που ξέρουμε
#     ότι το μοντέλο δουλεύει, του δίνουμε ΟΛΑ τα δεδομένα για να μάθει όσο γίνεται καλύτερα.)
# 2. Κατεβάζουμε την ΠΡΟΓΝΩΣΗ καιρού για τις επόμενες μέρες.
# 3. Το μοντέλο λέει: "με αυτόν τον καιρό, το πάρκο θα βγάλει Χ kWh".
#
# Χρειάζεται να έχει τρέξει πρώτα το ΒΗΜΑ3 (διαβάζει ποιες ώρες ήταν "καθαρές").
# ============================================================

import pandas as pd
import requests
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor


# ------------------------------------------------------------
# ΡΥΘΜΙΣΕΙΣ
# ------------------------------------------------------------
from config import LAT, LON, TILT, AZIMUTH  # θέση πάρκου (από config.py / .env)
FEATURES = ["global_tilted_irradiance", "direct_radiation", "diffuse_radiation",
            "temperature_2m", "cloud_cover", "ora"]
TARGET = "kwh"


# ------------------------------------------------------------
# 1. ΤΕΛΙΚΟ ΜΟΝΤΕΛΟ: εκπαίδευση σε όλες τις καθαρές ώρες
# ------------------------------------------------------------
print("1) Εκπαιδεύω το τελικό μοντέλο...")
istoriko = pd.read_csv("data/apotelesmata_katharismou.csv", parse_dates=["time"])
kathara = istoriko[~istoriko["ypopti"]]          # πετάμε τις ώρες με περικοπή/βλάβη
montelo = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1)
montelo.fit(kathara[FEATURES], kathara[TARGET])
print(f"   εκπαιδεύτηκε σε {len(kathara)} καθαρές ώρες από {kathara['time'].dt.date.nunique()} μέρες")

# Για να ξέρουμε πόσο "εμπιστευόμαστε" την πρόβλεψη: τα δέντρα του δάσους δεν
# συμφωνούν πάντα. Αν διαφωνούν πολύ -> αβέβαιη πρόβλεψη. Κρατάμε το εύρος 10%-90%.
def provlepsi_me_evros(X):
    """Επιστρέφει (πρόβλεψη, κάτω όριο, πάνω όριο) από τις γνώμες των 300 δέντρων."""
    import numpy as np
    gnomes = np.stack([dentro.predict(X.values) for dentro in montelo.estimators_])
    return (gnomes.mean(axis=0).clip(min=0),
            np.percentile(gnomes, 10, axis=0).clip(min=0),
            np.percentile(gnomes, 90, axis=0).clip(min=0))


# ------------------------------------------------------------
# 2. ΠΡΟΓΝΩΣΗ ΚΑΙΡΟΥ για τις επόμενες μέρες
# ------------------------------------------------------------
print("2) Κατεβάζω την πρόγνωση καιρού για τη Σοφιάδα...")
apantisi = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": LAT, "longitude": LON,
        "hourly": "global_tilted_irradiance,direct_radiation,diffuse_radiation,temperature_2m,cloud_cover",
        "tilt": TILT, "azimuth": AZIMUTH,
        "forecast_days": 3,               # σήμερα + αύριο + μεθαύριο
        "timezone": "Europe/Athens",
    },
    timeout=60,
)
prognosi = pd.DataFrame(apantisi.json()["hourly"])
prognosi["time"] = pd.to_datetime(prognosi["time"]) - pd.Timedelta(hours=1)  # ίδια ευθυγράμμιση με το βήμα 2
prognosi["ora"] = prognosi["time"].dt.hour

# Κρατάμε μόνο από ΑΥΡΙΟ και μετά, και μόνο τις ώρες με φως
avrio = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
prognosi = prognosi[(prognosi["time"] >= avrio) & (prognosi["global_tilted_irradiance"] > 0)].copy()


# ------------------------------------------------------------
# 3. ΠΡΟΒΛΕΨΗ
# ------------------------------------------------------------
prognosi["kwh"], prognosi["kato"], prognosi["pano"] = provlepsi_me_evros(prognosi[FEATURES])
prognosi["mera"] = prognosi["time"].dt.date
MERES = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]  # για ελληνικά ονόματα ημερών

print("\n================ ΠΡΟΒΛΕΨΗ ΠΑΡΑΓΩΓΗΣ ================")
for mera, omada in prognosi.groupby("mera"):
    print(f"\n📅 {MERES[mera.weekday()]} {mera.strftime('%d/%m/%Y')}")
    print(f"   {'ώρα':>5} | {'ήλιος W/m²':>10} | {'σύννεφα':>7} | {'πρόβλεψη kWh':>12} | εύρος")
    for _, r in omada.iterrows():
        bara = "█" * int(r["kwh"] / 15)
        print(f"   {r['time'].strftime('%H:%M'):>5} | {r['global_tilted_irradiance']:10.0f} | "
              f"{r['cloud_cover']:6.0f}% | {r['kwh']:12.0f} | {r['kato']:.0f}-{r['pano']:.0f}  {bara}")
    print(f"   ΣΥΝΟΛΟ: ~{omada['kwh'].sum():,.0f} kWh  "
          f"(εύρος {omada['kato'].sum():,.0f} - {omada['pano'].sum():,.0f} kWh)")

prognosi[["time", "global_tilted_irradiance", "cloud_cover", "temperature_2m", "kwh", "kato", "pano"]] \
    .to_csv("data/provlepsi.csv", index=False)


# ------------------------------------------------------------
# 4. ΓΡΑΦΗΜΑ
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 5))
ax.fill_between(prognosi["time"], prognosi["kato"], prognosi["pano"],
                color="orange", alpha=0.25, label="Εύρος αβεβαιότητας (10%-90%)")
ax.plot(prognosi["time"], prognosi["kwh"], "o-", color="darkorange", lw=2, label="Πρόβλεψη (kWh/ώρα)")
for mera, omada in prognosi.groupby("mera"):
    mesi = omada["time"].iloc[len(omada) // 2]
    ax.annotate(f"{mera.strftime('%d/%m')}\n~{omada['kwh'].sum():,.0f} kWh",
                (mesi, omada["kwh"].max()), textcoords="offset points", xytext=(0, 12),
                ha="center", fontsize=11, fontweight="bold")
ax.set_title("Πρόβλεψη παραγωγής πάρκου Σοφιάδας - επόμενες μέρες")
ax.set_ylabel("kWh ανά ώρα")
ax.set_ylim(0, max(prognosi["pano"].max() * 1.25, 50))
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("provlepsi_avrio.png", dpi=120)
print("\nΤο γράφημα αποθηκεύτηκε στο provlepsi_avrio.png")
plt.show()
