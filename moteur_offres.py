# moteur_offres.py : point d'entree (terminal ou page web)
#   python moteur_offres.py "ingénieur NLP"                       corpus fictif, recherche par mots
#   python moteur_offres.py "hygiène" --mode semantique           recherche semantique (pip install scikit-learn)
#   python moteur_offres.py "software engineer" --donnees reel    vraies offres (python telecharger_donnees.py avant)
#   python moteur_offres.py --web                                 page web sur http://localhost:8000

import argparse
import sys

from moteur import Moteur, charger
from moteur.web import creer_serveur


def afficher_terminal(moteur, requete, mode):
    docs = moteur.chercher(requete, mode=mode)
    print(f"{len(docs)} offre(s) pour « {requete} » (mode {mode})\n")
    for d in docs[:5]:
        print(f"[{d['id']}] {d['titre']}")
        print("   " + d["description"][:160])
    f = moteur.facettes(docs)
    print()
    for d in moteur.config["facettes"]:
        print(f"{d['titre']:40s}", ", ".join(f"{c}={n}" for c, n in f[d["nom"]][:8]))
    a, b = moteur.config["pivot"]
    print(f"\npivot {a} -> {b} :")
    for case, total, sous in f["pivot"][:6]:
        print(f"   {case} ({total}) : " + ", ".join(f"{c}={n}" for c, n in sous))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Moteur de recherche d'offres d'emploi")
    p.add_argument("requete", nargs="*", help="mots à chercher")
    p.add_argument("--donnees", choices=["fictif", "reel"], default="fictif")
    p.add_argument("--mode", choices=["mots", "semantique", "hybride"], default="mots")
    p.add_argument("--web", action="store_true", help="lancer la page web")
    p.add_argument("--port", type=int, default=8000)
    a = p.parse_args()

    try:
        moteur = Moteur(*charger(a.donnees))
    except FileNotFoundError as erreur:
        sys.exit(str(erreur))
    if a.web:
        print(f"ouvrir http://localhost:{a.port}  (Ctrl+C pour arrêter)")
        creer_serveur(moteur, a.port).serve_forever()
    else:
        try:
            afficher_terminal(moteur, " ".join(a.requete), a.mode)
        except ImportError:
            sys.exit("le mode sémantique demande scikit-learn : pip install -r requirements.txt")
