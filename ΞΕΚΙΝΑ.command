#!/bin/bash
# Αυτό το αρχείο το ανοίγεις με διπλό κλικ.
# Στήνει το περιβάλλον Python (μόνο την πρώτη φορά) και τρέχει το script.

cd "$(dirname "$0")"          # πήγαινε στον φάκελο του project

if [ ! -d ".venv" ]; then
  echo ">> Πρώτη φορά: φτιάχνω το περιβάλλον Python..."
  python3 -m venv .venv
fi

source .venv/bin/activate     # μπες στο "κουτί"
echo ">> Εγκαθιστώ/ελέγχω τις βιβλιοθήκες..."
pip install -q -r requirements.txt

echo ">> Τρέχω το 01_kairos.py"
python3 01_kairos.py

echo ""
echo ">> Τέλος! Μπορείς να κλείσεις αυτό το παράθυρο."
