# ============================================================
# 05_anafora.py
# ΒΗΜΑ 6: ΗΜΕΡΗΣΙΑ ΑΝΑΦΟΡΑ
#
# Διαβάζει τα αποτελέσματα των προηγούμενων βημάτων και γράφει ένα ΣΥΝΤΟΜΟ
# μήνυμα στα ελληνικά, που το n8n θα σου στέλνει κάθε πρωί:
#   1. ΠΡΟΒΛΕΨΗ: πόσο θα παράγει το πάρκο αύριο/μεθαύριο με βάση τον καιρό (το κύριο)
#   2. ΧΘΕΣ: πόσα έβγαλε vs πόσα πρόβλεψε το μοντέλο (έλεγχος ακρίβειας)
#
# Το μήνυμα τυπώνεται στην οθόνη (stdout). Το n8n "πιάνει" ό,τι τυπώνεται
# και το στέλνει όπου θέλουμε (Telegram, email κ.λπ.).
# ============================================================

import pandas as pd

MERES = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]


def onoma_meras(mera):
    """π.χ. 2026-10-17 -> 'Σάββατο 17/10'"""
    return f"{MERES[mera.weekday()]} {mera.strftime('%d/%m')}"


# ------------------------------------------------------------
# 1. ΧΘΕΣ: η πιο πρόσφατη μέρα που έχουμε πραγματικά δεδομένα
# ------------------------------------------------------------
istoriko = pd.read_csv("data/apotelesmata_katharismou.csv", parse_dates=["time"])
istoriko["mera"] = istoriko["time"].dt.date
teleftaia = istoriko["mera"].max()                      # η πιο πρόσφατη μέρα
xthes = istoriko[istoriko["mera"] == teleftaia]

pragmatiko = xthes["kwh"].sum()                         # τι έβγαλε
anamenomeno = xthes["anamenomeno"].sum()                # τι "έπρεπε" (κατά το μοντέλο)
ypoptes = xthes[xthes["ypopti"]]                        # ώρες με περικοπή/βλάβη
xamenes = (ypoptes["anamenomeno"] - ypoptes["kwh"]).clip(lower=0).sum()
pososto = pragmatiko / anamenomeno * 100 if anamenomeno > 0 else 0

grammes = [""]
grammes.append(f"📊 Τελευταία μέρα με δεδομένα · {onoma_meras(teleftaia)}")
grammes.append(f"   Παραγωγή: {pragmatiko:,.0f} kWh (αναμενόμενο ~{anamenomeno:,.0f}, {pososto:.0f}%)")

if len(ypoptes) == 0:
    grammes.append("   ✅ Κανονική λειτουργία.")
else:
    # Ομαδοποιούμε συνεχόμενες ύποπτες ώρες σε διαστήματα, π.χ. "11:00-14:00"
    ores = sorted(ypoptes["time"].dt.hour.tolist())
    diastimata, arxi, prohgoumeni = [], ores[0], ores[0]
    for o in ores[1:] + [None]:
        if o is None or o != prohgoumeni + 1:
            diastimata.append(f"{arxi:02d}:00-{prohgoumeni + 1:02d}:00")
            if o is not None:
                arxi = o
        if o is not None:
            prohgoumeni = o
    grammes.append(f"   ⚠️ Μη κανονική λειτουργία {', '.join(diastimata)} (ήλιος αλλά ~0 παραγωγή, ~{xamenes:,.0f} kWh)")


# ------------------------------------------------------------
# 2. ΠΡΟΒΛΕΨΗ για τις επόμενες μέρες (από το 04_provlepsi.py)
# ------------------------------------------------------------
provlepsi = pd.read_csv("data/provlepsi.csv", parse_dates=["time"])
provlepsi["mera"] = provlepsi["time"].dt.date
prov = ["☀️ Πάρκο Σοφιάδας · πρόβλεψη παραγωγής", ""]
for mera, omada in provlepsi.groupby("mera"):
    korifi = omada.loc[omada["kwh"].idxmax()]           # η ώρα με τη μεγαλύτερη παραγωγή
    synnefa = omada["cloud_cover"].mean()
    kairos = "☀️" if synnefa < 30 else ("⛅" if synnefa < 70 else "☁️")
    prov.append(f"{kairos} {onoma_meras(mera)}: ~{omada['kwh'].sum():,.0f} kWh "
                   f"(εύρος {omada['kato'].sum():,.0f}-{omada['pano'].sum():,.0f}), "
                   f"κορυφή {korifi['time'].strftime('%H:%M')}")

# Πρώτα η πρόβλεψη (το κύριο), μετά το "χθες"
print("\n".join(prov + grammes))
