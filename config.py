# ============================================================
# config.py
# ΚΟΙΝΕΣ ΡΥΘΜΙΣΕΙΣ για όλα τα scripts.
#
# Η ΑΚΡΙΒΗΣ θέση του πάρκου ΔΕΝ γράφεται εδώ (ο κώδικας θα είναι δημόσιος στο GitHub).
# Διαβάζεται από το αρχείο ".env", που μένει ΜΟΝΟ στον υπολογιστή σου
# (το .gitignore το εμποδίζει να ανέβει).
# Αν δεν υπάρχει .env, χρησιμοποιούμε μια ΣΤΡΟΓΓΥΛΕΜΕΝΗ θέση (περιοχή Σοφιάδας),
# ώστε όποιος κατεβάσει το project να μπορεί να το τρέξει.
# ============================================================
import os


def _diavase_env(arxeio=".env"):
    """Διαβάζει γραμμές τύπου ΚΛΕΙΔΙ=τιμή από το .env και τις βάζει στο περιβάλλον."""
    if not os.path.exists(arxeio):
        return
    with open(arxeio, encoding="utf-8") as f:
        for grammi in f:
            grammi = grammi.strip()
            if grammi and not grammi.startswith("#") and "=" in grammi:
                kleidi, timi = grammi.split("=", 1)
                os.environ.setdefault(kleidi.strip(), timi.strip())


_diavase_env()

LAT = float(os.environ.get("PV_LAT", "39.2"))    # γεωγραφικό πλάτος
LON = float(os.environ.get("PV_LON", "22.3"))    # γεωγραφικό μήκος
TILT = float(os.environ.get("PV_TILT", "25"))    # κλίση πάνελ (μοίρες)
AZIMUTH = float(os.environ.get("PV_AZIMUTH", "0"))  # προσανατολισμός (0 = Νότος)

# Έλεγχος ασφαλείας: αν κάποιος γράψει λάθος τιμή στο .env (π.χ. μπερδέψει πλάτος/μήκος),
# σταματάμε αμέσως με καθαρό μήνυμα, αντί να κατεβάσουμε καιρό για λάθος σημείο του πλανήτη.
if not (-90 <= LAT <= 90 and -180 <= LON <= 180):
    raise ValueError(f"Λάθος συντεταγμένες στο .env: PV_LAT={LAT}, PV_LON={LON}")
if not (0 <= TILT <= 90):
    raise ValueError(f"Η κλίση των πάνελ πρέπει να είναι 0-90 μοίρες (δόθηκε {TILT})")
