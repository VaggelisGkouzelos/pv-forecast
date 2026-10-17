# ============================================================
# config.py
# ΚΟΙΝΕΣ ΡΥΘΜΙΣΕΙΣ για όλα τα scripts.
#
# Η ΑΚΡΙΒΗΣ θέση του πάρκου ΔΕΝ γράφεται εδώ (ο κώδικας θα είναι δημόσιος στο GitHub).
# Διαβάζεται από το αρχείο ".env", που μένει ΜΟΝΟ στον υπολογιστή σου
# (το .gitignore το εμποδίζει να ανέβει).
# Αν δεν υπάρχει .env, χρησιμοποιούμε μια ΣΤΡΟΓΓΥΛΕΜΕΝΗ θέση (περιοχή Δομοκού),
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
