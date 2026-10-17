# ============================================================
# 03_katharismos.py
# ΒΗΜΑ 4: ΚΑΘΑΡΙΣΜΟΣ ΔΕΔΟΜΕΝΩΝ + ΞΑΝΑ-ΕΚΠΑΙΔΕΥΣΗ
#
# Πρόβλημα: στα δεδομένα εκπαίδευσης υπάρχουν ώρες με περικοπή/βλάβη.
# Εκεί είχε ήλιο αλλά το πάρκο ΔΕΝ παρήγαγε -> το μοντέλο "μπερδεύεται"
# και μαθαίνει ότι "μερικές φορές ο ήλιος δεν φέρνει ρεύμα".
#
# Λύση (iterative cleaning):
#   1. εκπαιδεύουμε μοντέλο
#   2. βρίσκουμε τις ώρες που το πάρκο έβγαλε ΠΟΛΥ λιγότερα από την πρόβλεψη
#   3. τις πετάμε και ξαναεκπαιδεύουμε
#   4. επαναλαμβάνουμε μέχρι να μη βρίσκει νέες ύποπτες ώρες
#
# Διαβάζει τον πίνακα που έφτιαξε το 02 (data/dedomena_ekpaideusis.csv),
# άρα ΔΕΝ χρειάζεται internet.
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score


# ------------------------------------------------------------
# ΡΥΘΜΙΣΕΙΣ
# ------------------------------------------------------------
TEST_APO = "2026-10-08"     # από εδώ και μετά = μέρες-"εξετάσεις"
# Πόσο "αυστηροί" είμαστε. Δοκιμάσαμε πολλές τιμές:
#   60% -> πετούσε το 30% των ωρών: μπέρδευε και ΛΑΘΗ ΤΟΥ ΚΑΙΡΟΥ (σύννεφο που η πρόγνωση
#          δεν είδε) με περικοπές. Πολύ επιθετικό.
#   20% -> πιάνει μόνο ώρες με παραγωγή ΣΧΕΔΟΝ ΜΗΔΕΝ ενώ είχε ήλιο = σίγουρο σταμάτημα
#          (περικοπή ΔΕΔΔΗΕ ή βλάβη). Η συννεφιά δεν ρίχνει ποτέ την παραγωγή τόσο απότομα.
ORIO_POSOSTOU = 0.20        # αν έβγαλε < 20% της πρόβλεψης -> ύποπτη ώρα
ELAXISTI_PROVLEPSI = 50     # ...αλλά μόνο αν περιμέναμε > 50 kWh (δηλ. είχε πραγματικά ήλιο)
MEGISTES_EPANALIPSEIS = 5   # πόσους γύρους καθαρισμού να κάνει το πολύ

FEATURES = ["global_tilted_irradiance", "direct_radiation", "diffuse_radiation",
            "temperature_2m", "cloud_cover", "ora"]
TARGET = "kwh"


def neo_montelo():
    """Φτιάχνει ένα 'φρέσκο' Random Forest (ίδιες ρυθμίσεις με το βήμα 2)."""
    return RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1)


def ypopto(pragmatiko, provlepsi):
    """True για τις ώρες που μοιάζουν με περικοπή/βλάβη."""
    return (provlepsi > ELAXISTI_PROVLEPSI) & (pragmatiko < ORIO_POSOSTOU * provlepsi)


# ------------------------------------------------------------
# 1. ΦΟΡΤΩΝΟΥΜΕ ΤΑ ΔΕΔΟΜΕΝΑ
# ------------------------------------------------------------
dedomena = pd.read_csv("data/dedomena_ekpaideusis.csv", parse_dates=["time"])
dedomena["mera"] = dedomena["time"].dt.date
train = dedomena[dedomena["time"] < TEST_APO].copy()
test = dedomena[dedomena["time"] >= TEST_APO].copy()
print(f"Δεδομένα: {len(train)} ώρες εκπαίδευσης, {len(test)} ώρες εξέτασης\n")


# ------------------------------------------------------------
# 2. ΕΠΑΝΑΛΗΠΤΙΚΟΣ ΚΑΘΑΡΙΣΜΟΣ (μόνο στις μέρες εκπαίδευσης)
# ------------------------------------------------------------
# ΓΙΑΤΙ "cross_val_predict" και όχι απλό predict;
# Αν ρωτήσουμε το μοντέλο για ώρες που ΕΧΕΙ ΗΔΗ ΔΕΙ, θα "θυμάται" την απάντηση
# και δεν θα βρει τίποτα ύποπτο (σαν να διορθώνει ο μαθητής το δικό του διαγώνισμα).
# Γι' αυτό: χωρίζουμε τις μέρες σε 5 ομάδες. Για κάθε ομάδα εκπαιδεύουμε στις
# άλλες 4 και προβλέπουμε αυτήν -> κάθε ώρα παίρνει πρόβλεψη από μοντέλο που ΔΕΝ την είδε.
# (Ομαδοποιούμε ανά ΜΕΡΑ ώστε ώρες της ίδιας μέρας να μη "βοηθάνε" η μία την άλλη.)
train["ypopti"] = False
print("Καθαρισμός δεδομένων εκπαίδευσης:")
for gyros in range(1, MEGISTES_EPANALIPSEIS + 1):
    kathara = train[~train["ypopti"]]                       # μόνο οι "καθαρές" ώρες
    provlepsi = cross_val_predict(neo_montelo(), kathara[FEATURES], kathara[TARGET],
                                  groups=kathara["mera"], cv=GroupKFold(n_splits=5))
    nees = ypopto(kathara[TARGET].values, provlepsi)        # ποιες βγήκαν ύποπτες τώρα
    train.loc[kathara.index[nees], "ypopti"] = True
    print(f"   γύρος {gyros}: βρέθηκαν {nees.sum():3d} νέες ύποπτες ώρες "
          f"(σύνολο {train['ypopti'].sum()})")
    if nees.sum() == 0:                                     # τίποτα καινούργιο -> σταματάμε
        break


# ------------------------------------------------------------
# 3. ΔΥΟ ΜΟΝΤΕΛΑ για σύγκριση
# ------------------------------------------------------------
# "Πριν":  εκπαίδευση σε ΟΛΕΣ τις ώρες (όπως στο βήμα 2)
# "Μετά":  εκπαίδευση ΜΟΝΟ στις καθαρές ώρες
montelo_prin = neo_montelo().fit(train[FEATURES], train[TARGET])
kathara = train[~train["ypopti"]]
montelo_meta = neo_montelo().fit(kathara[FEATURES], kathara[TARGET])

test["pred_prin"] = montelo_prin.predict(test[FEATURES]).clip(min=0)
test["pred_meta"] = montelo_meta.predict(test[FEATURES]).clip(min=0)
# Στις μέρες-εξετάσεις σημειώνουμε τις ύποπτες ώρες με το ΚΑΘΑΡΟ μοντέλο
test["ypopti"] = ypopto(test[TARGET].values, test["pred_meta"].values)


# ------------------------------------------------------------
# 4. ΑΞΙΟΛΟΓΗΣΗ
# ------------------------------------------------------------
# Βαθμολογούμε στις ΚΑΝΟΝΙΚΕΣ ώρες των εξετάσεων: ο στόχος του μοντέλου είναι να
# ξέρει πόσα βγάζει το πάρκο ΟΤΑΝ ΛΕΙΤΟΥΡΓΕΙ ΣΩΣΤΑ. Τις ανωμαλίες τις "πιάνει" χωριστά.
kanonikes = test[~test["ypopti"]]
print("\n================ ΑΠΟΤΕΛΕΣΜΑΤΑ (κανονικές ώρες των εξετάσεων) ================")
for onoma, stili in [("ΠΡΙΝ τον καθαρισμό", "pred_prin"), ("ΜΕΤΑ τον καθαρισμό", "pred_meta")]:
    mae = mean_absolute_error(kanonikes[TARGET], kanonikes[stili])
    r2 = r2_score(kanonikes[TARGET], kanonikes[stili])
    print(f"{onoma:22s} | Μέσο λάθος: {mae:5.1f} kWh/ώρα | R²: {r2:5.3f}")

# Σε όλες τις ηλιόλουστες ώρες: υποτιμά ακόμα;
eksodos = kanonikes[TARGET].sum()
print(f"\nΣύνολο κανονικών ωρών: πραγματικό {eksodos:,.0f} kWh | "
      f"πρόβλεψη ΠΡΙΝ {kanonikes['pred_prin'].sum():,.0f} | ΜΕΤΑ {kanonikes['pred_meta'].sum():,.0f}")


# ------------------------------------------------------------
# 5. ΑΝΑΦΟΡΑ ΑΝΑ ΜΕΡΑ: πόσες kWh "χάθηκαν"
# ------------------------------------------------------------
# Για τις μέρες εκπαίδευσης θέλουμε "αναμενόμενο" από μοντέλο που ΔΕΝ είδε εκείνη τη μέρα
# (πάλι 5 ομάδες ημερών) και που εκπαιδεύτηκε ΜΟΝΟ σε καθαρές ώρες.
anamenomeno = pd.Series(0.0, index=train.index)
for train_idx, val_idx in GroupKFold(n_splits=5).split(train, groups=train["mera"]):
    meros = train.iloc[train_idx]
    m = neo_montelo().fit(meros.loc[~meros["ypopti"], FEATURES], meros.loc[~meros["ypopti"], TARGET])
    anamenomeno.iloc[val_idx] = m.predict(train.iloc[val_idx][FEATURES]).clip(min=0)
train["anamenomeno"] = anamenomeno
test["anamenomeno"] = test["pred_meta"]

ola = pd.concat([train, test])
ola["xamenes_kwh"] = (ola["anamenomeno"] - ola[TARGET]).where(ola["ypopti"], 0).clip(lower=0)
ana_mera = ola.groupby("mera").agg(
    pragmatiko=(TARGET, "sum"),
    anamenomeno=("anamenomeno", "sum"),
    ypoptes_ores=("ypopti", "sum"),
    xamenes_kwh=("xamenes_kwh", "sum"),
).round(0)
ana_mera["%"] = (ana_mera["pragmatiko"] / ana_mera["anamenomeno"] * 100).round(0)
ana_mera["σημείωση"] = ""
ana_mera.loc[ana_mera["ypoptes_ores"] > 0, "σημείωση"] = "⚠️ περικοπή/βλάβη"
ana_mera.loc[ana_mera.index >= pd.to_datetime(TEST_APO).date(), "σημείωση"] += " (test)"
print("\n================ ΑΝΑ ΜΕΡΑ ================")
print(ana_mera.to_string())
print(f"\nΣυνολικά χαμένες kWh σε {len(ana_mera)} μέρες: {ana_mera['xamenes_kwh'].sum():,.0f} kWh "
      f"({ana_mera['xamenes_kwh'].sum() / ana_mera['pragmatiko'].sum() * 100:.1f}% της παραγωγής)")
ola.to_csv("data/apotelesmata_katharismou.csv", index=False)


# ------------------------------------------------------------
# 6. ΓΡΑΦΗΜΑ
# ------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

ax1.plot(test["time"], test[TARGET], "o-", color="black", ms=3, label="Πραγματικό")
ax1.plot(test["time"], test["pred_prin"], color="steelblue", ls="--", label="Πρόβλεψη ΠΡΙΝ τον καθαρισμό")
ax1.plot(test["time"], test["pred_meta"], color="orange", lw=2, label="Πρόβλεψη ΜΕΤΑ τον καθαρισμό")
yp = test[test["ypopti"]]
ax1.scatter(yp["time"], yp[TARGET], color="red", s=40, zorder=5, label="Ύποπτη ώρα (περικοπή/βλάβη)")
ax1.set_title("Μέρες-εξετάσεις: πρόβλεψη πριν και μετά τον καθαρισμό")
ax1.set_ylabel("kWh ανά ώρα")
ax1.legend()
ax1.grid(alpha=0.3)

x = range(len(ana_mera))
ax2.bar(x, ana_mera["pragmatiko"], color="black", label="Πραγματικό")
ax2.bar(x, ana_mera["xamenes_kwh"], bottom=ana_mera["pragmatiko"], color="red", label="Χαμένες kWh (περικοπή/βλάβη)")
ax2.plot(x, ana_mera["anamenomeno"], "o", color="orange", label="Αναμενόμενο (καθαρό μοντέλο)")
ax2.set_xticks(list(x))
ax2.set_xticklabels([d.strftime("%d/%m") for d in ana_mera.index], rotation=45)
ax2.set_title("Ανά μέρα: τι έβγαλε το πάρκο και τι χάθηκε")
ax2.set_ylabel("kWh ανά μέρα")
ax2.legend()
ax2.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("apotelesmata_katharismou.png", dpi=120)
print("\nΤο γράφημα αποθηκεύτηκε στο apotelesmata_katharismou.png")
plt.show()
