# corpus.py : les deux corpus + leur configuration (facettes, texte a indexer, champs a afficher)
#   "fictif" : 1500 offres inventees en francais (marche tout de suite)
#   "reel"   : ~38 000 vraies offres en anglais (a telecharger avec telecharger_donnees.py)

import csv
import random
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FICHIER_REEL = Path(__file__).resolve().parent.parent / "data" / "jobs_github.csv"

# ---------------------------------------------------------------- corpus fictif
SECTEURS = {
    "Informatique": {
        "metiers": ["Développeur Python", "Ingénieur NLP", "Data Scientist", "Développeur web", "Ingénieur DevOps"],
        "missions": ["développer des modèles de traitement automatique des langues", "concevoir des API",
                     "analyser de grands volumes de données", "mettre en place des tests automatiques"],
        "salaire": (34000, 58000)},
    "Vente": {
        "metiers": ["Conseiller de vente", "Vendeur en boutique", "Responsable de magasin", "Assistant commercial"],
        "missions": ["accueillir et conseiller les clients", "gérer la caisse et les stocks",
                     "atteindre les objectifs de chiffre d'affaires", "fidéliser la clientèle"],
        "salaire": (21000, 34000)},
    "Santé": {
        "metiers": ["Infirmier", "Aide-soignant", "Préparateur en pharmacie", "Technicien de laboratoire"],
        "missions": ["assurer les soins quotidiens des patients", "tenir à jour les dossiers médicaux",
                     "respecter les protocoles d'hygiène", "accueillir les familles"],
        "salaire": (24000, 42000)},
    "Traduction et langues": {
        "metiers": ["Traducteur", "Interprète", "Réviseur linguistique", "Linguiste computationnel"],
        "missions": ["traduire des documents techniques", "relire et réviser des traductions",
                     "constituer des bases terminologiques", "annoter des corpus pour le traitement des langues"],
        "salaire": (26000, 48000)},
    "Éducation": {
        "metiers": ["Enseignant de français", "Formateur en entreprise", "Professeur d'anglais", "Concepteur pédagogique"],
        "missions": ["préparer et animer des cours", "évaluer les acquis des apprenants",
                     "concevoir des supports numériques", "accompagner les élèves en difficulté"],
        "salaire": (22000, 40000)},
    "Logistique": {
        "metiers": ["Préparateur de commandes", "Cariste", "Responsable logistique", "Chauffeur-livreur"],
        "missions": ["préparer et expédier les commandes", "organiser les tournées de livraison",
                     "contrôler les marchandises à la réception", "respecter les règles de sécurité"],
        "salaire": (20000, 38000)},
}
VILLES = ["Paris", "Lyon", "Marseille", "Toulouse", "Lille", "Bordeaux", "Nantes"]
CONTRATS = ["CDI", "CDI", "CDD", "Stage", "Alternance", "Freelance"]   # CDI deux fois = plus frequent
ENTREPRISES = ["Novalis", "Altéa", "Brisvent", "Cormoran", "Ecolys", "Fluxia", "Granit", "Horizon", "Lumen", "Océane"]

CONFIG_FICTIF = {
    "texte": lambda d: f"{d['titre']} {d['titre']} {d['description']} {d['secteur']}",   # le titre compte double
    "meta": ["ville", "secteur", "type_contrat", "salaire", "date"],                     # ligne sous le titre
    "facettes": [
        {"nom": "secteur", "titre": "Secteur", "type": "champ", "champ": "secteur"},
        {"nom": "contrat", "titre": "Type de contrat", "type": "champ", "champ": "type_contrat"},
        {"nom": "salaire", "titre": "Salaire annuel (€)", "type": "regulier", "champ": "salaire", "pas": 10000},
        {"nom": "exp", "titre": "Expérience", "type": "perso", "champ": "experience",
         "tranches": {"0-1 an": (0, 1), "2-5 ans": (2, 5), "6 ans et plus": (6, 99)}},
    ],
    "pivot": ("secteur", "contrat"),
}


def fabriquer_corpus(n=1500, graine=1):
    alea = random.Random(graine)   # meme graine = meme corpus
    docs = []
    for i in range(1, n + 1):
        secteur = alea.choice(list(SECTEURS))
        s = SECTEURS[secteur]
        metier, contrat, ville = alea.choice(s["metiers"]), alea.choice(CONTRATS), alea.choice(VILLES)
        exp = 0 if contrat in ("Stage", "Alternance") else alea.choice([0, 1, 2, 3, 4, 5, 7, 10])
        if contrat == "Stage":
            salaire = alea.randrange(7000, 11000, 100)
        elif contrat == "Alternance":
            salaire = alea.randrange(12000, 20000, 100)
        else:
            salaire = alea.randrange(s["salaire"][0], s["salaire"][1], 500) + exp * 900
        m = alea.sample(s["missions"], 3)
        docs.append({
            "id": f"OFF-{i:04d}",
            "titre": f"{metier} (H/F)",
            "description": f"{alea.choice(ENTREPRISES)} recrute à {ville} un(e) {metier}. "
                           f"Missions : {m[0]}, {m[1]} et {m[2]}. Contrat : {contrat}. "
                           f"{exp} an(s) d'expérience demandé(s).",
            "ville": ville, "secteur": secteur, "type_contrat": contrat,
            "salaire": salaire, "experience": exp,
            "date": (date(2026, 1, 1) + timedelta(days=alea.randint(0, 270))).isoformat(),
        })
    return docs


# ---------------------------------------------------------------- corpus reel
CONFIG_REEL = {
    "texte": lambda d: f"{d['titre']} {d['titre']} {d['entreprise']} {d['lieu']} {d['departement']}",
    "meta": ["entreprise", "lieu", "plateforme", "contrat"],
    "facettes": [
        {"nom": "plateforme", "titre": "Plateforme de recrutement", "type": "champ", "champ": "plateforme"},
        {"nom": "contrat", "titre": "Type de contrat", "type": "champ", "champ": "contrat"},
        {"nom": "teletravail", "titre": "Télétravail", "type": "champ", "champ": "teletravail"},
        {"nom": "anciennete", "titre": "Ancienneté de l'offre (jours)", "type": "regulier",
         "champ": "anciennete_jours", "pas": 30, "max": 180},
        {"nom": "taille", "titre": "Taille de l'entreprise (nb d'offres)", "type": "perso", "champ": "nb_offres_entreprise",
         "tranches": {"1-10 offres": (1, 10), "11-100 offres": (11, 100), "plus de 100 offres": (101, 10 ** 9)}},
    ],
    "pivot": ("plateforme", "contrat"),
}


def contrat_propre(brut):
    # les offres ecrivent le contrat de 25 facons (FullTime, Full-time, Full time...) : on regroupe
    t = brut.lower()
    if not t:
        return "Non renseigné"
    if "intern" in t:
        return "Stage"
    if "part" in t:
        return "Temps partiel"
    if any(m in t for m in ("contract", "freelance", "temp", "fixed")):
        return "Contrat ou temporaire"
    if any(m in t for m in ("full", "permanent", "employee")):
        return "Temps plein"
    return "Autre"


def lire_date(texte):
    # "2026-09-03T13:32:53-04:00" ou "2026-10-04T11:34:59.761Z" -> date avec fuseau (UTC si absent)
    texte = texte.replace("Z", "+00:00").replace(" UTC", "+00:00")      # le fichier melange plusieurs formats
    d = datetime.fromisoformat(texte)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def charger_reel(chemin=FICHIER_REEL):
    if not Path(chemin).exists():
        raise FileNotFoundError("data/jobs_github.csv introuvable : lancer d'abord  python telecharger_donnees.py")
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    # "aujourd'hui" = la date du dernier relevé du fichier (pour que l'ancienneté ne change pas d'un jour à l'autre)
    reference = max(lire_date(r["scrapedAt"]) for r in lignes)
    nb_offres = Counter(r["company"] for r in lignes)
    docs, vus = [], set()
    for r in lignes:
        cle = (r["platform"], r["jobId"])
        if cle in vus:          # le fichier contient quelques doublons
            continue
        vus.add(cle)
        anciennete = None
        if r["postedAt"]:
            publie = lire_date(r["postedAt"])
            anciennete = max(0, (reference - publie).days)
        docs.append({
            "id": f"{r['platform']}-{r['jobId']}",
            "titre": r["title"], "entreprise": r["company"], "lieu": r["locations"],
            "departement": r["department"], "plateforme": r["platform"],
            "contrat": contrat_propre(r["employmentType"]),
            "teletravail": {"true": "Oui", "false": "Non"}.get(r["isRemote"], "Non renseigné"),
            "anciennete_jours": anciennete, "nb_offres_entreprise": nb_offres[r["company"]],
            "url": r["applyUrl"],
            "description": " | ".join(x for x in (r["company"], r["locations"], r["department"]) if x),
        })
    return docs


def charger(donnees):
    # renvoie (documents, configuration) pour "fictif" ou "reel"
    if donnees == "reel":
        return charger_reel(), CONFIG_REEL
    return fabriquer_corpus(), CONFIG_FICTIF
