# ============================================================
# 02_ekpaideusi.py
# ΒΗΜΑ 2 + 3: Ενώνουμε την παραγωγή του πάρκου με τον καιρό
# και ΕΚΠΑΙΔΕΥΟΥΜΕ ένα μοντέλο Machine Learning που μαθαίνει:
#
#        καιρός (ήλιος, σύννεφα, θερμοκρασία)  -->  kWh που βγάζει το πάρκο
#
# Μετά ελέγχουμε πόσο καλά προβλέπει σε μέρες που ΔΕΝ έχει δει.
# ============================================================

import glob                      # για να βρούμε όλα τα Excel του φακέλου
import requests                  # για να κατεβάσουμε τον καιρό
import pandas as pd              # πίνακες δεδομένων
import matplotlib.pyplot as plt  # γραφήματα

# Από τη βιβλιοθήκη scikit-learn (η πιο γνωστή βιβλιοθήκη ML στην Python):
from sklearn.linear_model import LinearRegression      # απλό μοντέλο: ευθεία γραμμή
from sklearn.ensemble import RandomForestRegressor     # πιο έξυπνο: "δάσος" από δέντρα αποφάσεων
from sklearn.metrics import mean_absolute_error, r2_score  # μετρικές: πόσο καλά τα πήγε


# ------------------------------------------------------------
# ΡΥΘΜΙΣΕΙΣ
# ------------------------------------------------------------
from config import LAT, LON, TILT, AZIMUTH  # θέση πάρκου (από config.py / .env)
                                 # -> αν ξέρεις τα ακριβή του πάρκου, άλλαξέ τα εδώ
TEST_APO = "2026-10-08"          # από αυτή τη μέρα και μετά = "εξετάσεις" του μοντέλου


# ------------------------------------------------------------
# 1. ΔΙΑΒΑΖΟΥΜΕ ΤΗΝ ΠΑΡΑΓΩΓΗ ΤΟΥ ΠΑΡΚΟΥ (τα 25 Excel)
# ------------------------------------------------------------
print("1) Διαβάζω τα Excel του FusionSolar...")
kommatia = []
for arxeio in glob.glob("data/fusionsolar/*.xlsx"):
    # header=1: οι τίτλοι των στηλών είναι στη 2η γραμμή του Excel
    df = pd.read_excel(arxeio, header=1)
    # Κρατάμε μόνο 2 στήλες: την ώρα και την παραγωγή (kWh)
    df = df[["Statistical Period", "PV Yield (kWh)"]]
    df.columns = ["time", "kwh"]
    kommatia.append(df)

paragogi = pd.concat(kommatia)    # ενώνουμε όλες τις μέρες σε έναν πίνακα
# Η ώρα γράφεται "2026-10-14 07:00:00 DST" -> βγάζουμε το " DST" και τη μετατρέπουμε σε ημερομηνία
paragogi["time"] = pd.to_datetime(paragogi["time"].str.replace(" DST", "", regex=False))
paragogi["kwh"] = paragogi["kwh"].fillna(0)   # κενά = νύχτα = 0 kWh
paragogi = paragogi.sort_values("time")
print(f"   {paragogi['time'].dt.date.nunique()} μέρες, {len(paragogi)} ώρες")


# ------------------------------------------------------------
# 2. ΚΑΤΕΒΑΖΟΥΜΕ ΤΟΝ ΚΑΙΡΟ ΓΙΑ ΤΙΣ ΙΔΙΕΣ ΩΡΕΣ
# ------------------------------------------------------------
print("2) Κατεβάζω τον καιρό της Σοφιάδας από το Open-Meteo...")
# Πόσες μέρες πίσω χρειαζόμαστε; Από την ΠΡΩΤΗ μέρα των Excel μέχρι σήμερα (+2 για σιγουριά).
# Έτσι, όσο μαζεύονται νέες μέρες, ο καιρός καλύπτει πάντα ΟΛΟ το ιστορικό
# (αλλιώς οι παλιότερες μέρες θα "χάνονταν" σιγά σιγά από την εκπαίδευση).
# Το Open-Meteo δίνει έως 92 μέρες πίσω με αυτόν τον τρόπο.
meres_piso = (pd.Timestamp.now().normalize() - paragogi["time"].min().normalize()).days + 2
meres_piso = min(meres_piso, 92)
print(f"   χρειάζομαι καιρό για {meres_piso} μέρες πίσω")
apantisi = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": LAT, "longitude": LON,
        "hourly": ",".join([
            "global_tilted_irradiance",  # ακτινοβολία ΠΑΝΩ στο κεκλιμένο πάνελ (W/m²) - η πιο σημαντική!
            "direct_radiation",          # άμεσος ήλιος
            "diffuse_radiation",         # διάχυτο φως (μέσα από σύννεφα)
            "temperature_2m",            # θερμοκρασία
            "cloud_cover",               # νεφοκάλυψη %
        ]),
        "tilt": TILT, "azimuth": AZIMUTH,
        "past_days": meres_piso,         # όσες μέρες χρειάζονται (υπολογίστηκε παραπάνω)
        "forecast_days": 1,
        "timezone": "Europe/Athens",
    },
    timeout=60,
)
kairos = pd.DataFrame(apantisi.json()["hourly"])
kairos["time"] = pd.to_datetime(kairos["time"])

# ΣΗΜΑΝΤΙΚΗ ΛΕΠΤΟΜΕΡΕΙΑ: "ευθυγράμμιση" ωρών.
# Στο Open-Meteo η τιμή των 08:00 είναι ο μέσος όρος 07:00-08:00.
# Στο FusionSolar η γραμμή 07:00 είναι η παραγωγή 07:00-08:00.
# Άρα μετακινούμε τον καιρό 1 ώρα πίσω για να "μιλάνε" για το ίδιο διάστημα.
kairos["time"] = kairos["time"] - pd.Timedelta(hours=1)
kairos.to_csv("data/kairos_sofiada_wriaios.csv", index=False)


# ------------------------------------------------------------
# 3. ΕΝΩΝΟΥΜΕ ΠΑΡΑΓΩΓΗ + ΚΑΙΡΟ (σαν VLOOKUP στο Excel)
# ------------------------------------------------------------
dedomena = paragogi.merge(kairos, on="time", how="inner")
dedomena["ora"] = dedomena["time"].dt.hour            # η ώρα της μέρας (0-23)
dedomena["mera"] = dedomena["time"].dt.date

# Κρατάμε μόνο τις ώρες με φως (τη νύχτα δεν έχει τίποτα να μάθει)
dedomena = dedomena[(dedomena["global_tilted_irradiance"] > 0) | (dedomena["kwh"] > 0)]
dedomena.to_csv("data/dedomena_ekpaideusis.csv", index=False)
print(f"3) Ενωμένος πίνακας: {len(dedomena)} ώρες με φως")


# ------------------------------------------------------------
# 4. ΧΩΡΙΖΟΥΜΕ: "ΜΑΘΗΜΑΤΑ" (train) και "ΕΞΕΤΑΣΕΙΣ" (test)
# ------------------------------------------------------------
# features (X) = αυτά που ξέρουμε από πριν (ο καιρός + η ώρα)
# target   (y) = αυτό που θέλουμε να μαντέψει (οι kWh)
FEATURES = ["global_tilted_irradiance", "direct_radiation", "diffuse_radiation",
            "temperature_2m", "cloud_cover", "ora"]
TARGET = "kwh"

train = dedomena[dedomena["time"] < TEST_APO]    # οι πρώτες μέρες: το μοντέλο μαθαίνει από αυτές
test = dedomena[dedomena["time"] >= TEST_APO]    # οι τελευταίες: δεν τις βλέπει ποτέ στην εκπαίδευση
print(f"4) Εκπαίδευση: {train['mera'].nunique()} μέρες | Εξέταση: {test['mera'].nunique()} μέρες")


# ------------------------------------------------------------
# 5. ΕΚΠΑΙΔΕΥΣΗ ΔΥΟ ΜΟΝΤΕΛΩΝ
# ------------------------------------------------------------
print("5) Εκπαιδεύω τα μοντέλα...")

# Μοντέλο Α: Γραμμική παλινδρόμηση με ΜΟΝΟ την ακτινοβολία.
# Μαθαίνει την ευθεία:  kWh = a * ακτινοβολία + b
modelo_A = LinearRegression()
modelo_A.fit(train[["global_tilted_irradiance"]], train[TARGET])   # <-- ΕΔΩ γίνεται η "μάθηση"

# Μοντέλο Β: Random Forest με ΟΛΑ τα features.
# 300 δέντρα αποφάσεων, το καθένα μαθαίνει κανόνες τύπου
# "αν ακτινοβολία > 500 και ώρα 11-14 τότε περίπου 300 kWh", και βγάζουμε τον μέσο όρο τους.
modelo_B = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=42)
modelo_B.fit(train[FEATURES], train[TARGET])                       # <-- ΕΔΩ γίνεται η "μάθηση"


# ------------------------------------------------------------
# 6. ΑΞΙΟΛΟΓΗΣΗ στις μέρες-"εξετάσεις"
# ------------------------------------------------------------
test = test.copy()
test["pred_A"] = modelo_A.predict(test[["global_tilted_irradiance"]]).clip(min=0)
test["pred_B"] = modelo_B.predict(test[FEATURES]).clip(min=0)

print("\n================ ΑΠΟΤΕΛΕΣΜΑΤΑ (μέρες που δεν είδε) ================")
for onoma, stili in [("Α: Γραμμική (μόνο ήλιος)", "pred_A"), ("Β: Random Forest (όλα)", "pred_B")]:
    mae = mean_absolute_error(test[TARGET], test[stili])   # μέσο λάθος σε kWh ανά ώρα
    r2 = r2_score(test[TARGET], test[stili])                # 1.0 = τέλειο, 0 = άχρηστο
    print(f"{onoma:28s} | Μέσο λάθος: {mae:6.1f} kWh/ώρα | R²: {r2:5.2f}")

# Τι "έμαθε" η γραμμική; (τα a και b της ευθείας)
print(f"\nΗ γραμμική έμαθε: kWh ≈ {modelo_A.coef_[0]:.3f} × ακτινοβολία + {modelo_A.intercept_:.1f}")

# Ποια features θεώρησε πιο σημαντικά το Random Forest;
print("\nΠόσο σημαντικό είναι κάθε feature για το Random Forest:")
for f, s in sorted(zip(FEATURES, modelo_B.feature_importances_), key=lambda x: -x[1]):
    print(f"   {f:26s} {s*100:5.1f}%  " + "█" * int(s * 40))


# ------------------------------------------------------------
# 7. ΣΥΓΚΡΙΣΗ ΑΝΑ ΜΕΡΑ: πραγματικό vs αναμενόμενο
#    (αν το πάρκο έβγαλε ΠΟΛΥ λιγότερα από όσα "επέτρεπε" ο ήλιος -> ύποπτο)
# ------------------------------------------------------------
dedomena["anamenomeno"] = modelo_B.predict(dedomena[FEATURES]).clip(min=0)
ana_mera = dedomena.groupby("mera")[["kwh", "anamenomeno"]].sum().round(0)
ana_mera["%"] = (ana_mera["kwh"] / ana_mera["anamenomeno"] * 100).round(0)
ana_mera["σημείωση"] = ""
ana_mera.loc[ana_mera["%"] < 70, "σημείωση"] = "⚠️ πιθανή περικοπή/βλάβη"
ana_mera.loc[ana_mera.index >= pd.to_datetime(TEST_APO).date(), "σημείωση"] += " (test)"
print("\n================ ΑΝΑ ΜΕΡΑ: πραγματικό vs αναμενόμενο ================")
print(ana_mera.to_string())


# ------------------------------------------------------------
# 8. ΓΡΑΦΗΜΑ
# ------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

# Πάνω: ώρα-ώρα στις μέρες-εξετάσεις
ax1.plot(test["time"], test[TARGET], "o-", color="black", ms=3, label="Πραγματικό (FusionSolar)")
ax1.plot(test["time"], test["pred_B"], color="orange", lw=2, label="Πρόβλεψη Random Forest")
ax1.plot(test["time"], test["pred_A"], color="steelblue", ls="--", label="Πρόβλεψη Γραμμικής")
ax1.set_title("Πρόβλεψη σε μέρες που το μοντέλο ΔΕΝ είχε δει (test)")
ax1.set_ylabel("kWh ανά ώρα")
ax1.legend()
ax1.grid(alpha=0.3)

# Κάτω: σύνολο ανά μέρα, όλες οι μέρες
x = range(len(ana_mera))
ax2.bar([i - 0.2 for i in x], ana_mera["anamenomeno"], width=0.4, color="orange", label="Αναμενόμενο (μοντέλο)")
ax2.bar([i + 0.2 for i in x], ana_mera["kwh"], width=0.4, color="black", label="Πραγματικό")
ax2.set_xticks(list(x))
ax2.set_xticklabels([d.strftime("%d/%m") for d in ana_mera.index], rotation=45)
ax2.set_title("Παραγωγή ανά μέρα: τι έβγαλε vs τι 'έπρεπε' να βγάλει")
ax2.set_ylabel("kWh ανά μέρα")
ax2.legend()
ax2.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("apotelesmata_montelou.png", dpi=120)
print("\nΤο γράφημα αποθηκεύτηκε στο apotelesmata_montelou.png")
plt.show()
