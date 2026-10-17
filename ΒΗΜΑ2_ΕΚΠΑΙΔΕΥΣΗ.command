#!/bin/bash
# Διπλό κλικ: εκπαιδεύει το μοντέλο Machine Learning με τα δεδομένα του πάρκου.

cd "$(dirname "$0")"            # πήγαινε στον φάκελο του project
source .venv/bin/activate       # μπες στο "κουτί" της Python

echo ">> Ελέγχω/εγκαθιστώ τις βιβλιοθήκες (την πρώτη φορά παίρνει 1-2 λεπτά)..."
pip install -q -r requirements.txt

echo ">> Τρέχω το 02_ekpaideusi.py"
echo ""
python3 02_ekpaideusi.py

echo ""
echo ">> Τέλος! Μπορείς να κλείσεις αυτό το παράθυρο."
