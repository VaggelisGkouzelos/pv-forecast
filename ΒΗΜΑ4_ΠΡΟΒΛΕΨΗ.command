#!/bin/bash
# Διπλό κλικ: πρόβλεψη παραγωγής του πάρκου για αύριο και μεθαύριο.
# (Χρειάζεται να έχει τρέξει πρώτα το ΒΗΜΑ3.)

cd "$(dirname "$0")"
source .venv/bin/activate
echo ">> Τρέχω το 04_provlepsi.py"
echo ""
python3 04_provlepsi.py
echo ""
echo ">> Τέλος! Μπορείς να κλείσεις αυτό το παράθυρο."
