# telecharger_donnees.py : telecharge les vraies offres d'emploi (~38 000) dans data/jobs_github.csv
# source : https://github.com/ConorsCode/open-jobs-data (code sous licence MIT ; les offres appartiennent aux entreprises)
# le fichier n'est pas dans le depot (voir .gitignore) : on le telecharge soi-meme

import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/data/jobs.csv"
DESTINATION = Path(__file__).resolve().parent / "data" / "jobs_github.csv"

DESTINATION.parent.mkdir(exist_ok=True)
print("téléchargement...")
urllib.request.urlretrieve(URL, DESTINATION)
print(f"ok : {DESTINATION} ({DESTINATION.stat().st_size / 1e6:.1f} Mo)")
