# evaluation.py : compare les 3 modes de recherche (mots, semantique, hybride) sur le corpus fictif
# lancer : python evaluation.py      (pip install scikit-learn pour les modes semantique et hybride)
#
# principe : chaque requete est un mot ou une expression d'un secteur ("hygiène" -> Santé).
# une offre est "pertinente" si elle est du bon secteur, meme si elle ne contient pas le mot de la requete
# (les missions sont tirees au hasard : une offre de santé n'a pas forcement la mission "hygiène").
# mesures :
#   P@10          = part des 10 premiers resultats qui sont du bon secteur
#   R-precision   = part des R premiers resultats qui sont du bon secteur, R = nombre d'offres du secteur
#                   (1.0 = le moteur retrouve toutes les offres du secteur avant de se tromper)

from moteur import Moteur, charger

REQUETES = [
    ("hygiène", "Santé"), ("patients", "Santé"), ("laboratoire", "Santé"), ("pharmacie", "Santé"),
    ("caisse", "Vente"), ("clientèle", "Vente"), ("boutique", "Vente"), ("chiffre d'affaires", "Vente"),
    ("API", "Informatique"), ("données", "Informatique"), ("NLP", "Informatique"), ("tests automatiques", "Informatique"),
    ("terminologiques", "Traduction et langues"), ("traduire", "Traduction et langues"),
    ("annoter corpus", "Traduction et langues"), ("interprète", "Traduction et langues"),
    ("apprenants", "Éducation"), ("élèves", "Éducation"), ("supports numériques", "Éducation"), ("cours", "Éducation"),
    ("livraison", "Logistique"), ("cariste", "Logistique"), ("commandes", "Logistique"), ("marchandises", "Logistique"),
]


def evaluer(moteur, mode):
    p10, rprec = [], []
    for requete, secteur in REQUETES:
        R = sum(d["secteur"] == secteur for d in moteur.docs)               # nb d'offres pertinentes
        resultats = moteur.chercher(requete, mode=mode, limite=R)[:R]
        bons = [d["secteur"] == secteur for d in resultats]
        p10.append(sum(bons[:10]) / 10)
        rprec.append(sum(bons) / R)
    return sum(p10) / len(p10), sum(rprec) / len(rprec)


if __name__ == "__main__":
    moteur = Moteur(*charger("fictif"))
    print(f"{len(REQUETES)} requêtes sur {len(moteur.docs)} offres fictives\n")
    print(f"{'mode':12s} {'P@10':>6s} {'R-précision':>12s}")
    for mode in ("mots", "semantique", "hybride"):
        try:
            p, r = evaluer(moteur, mode)
        except ImportError:
            print(f"{mode:12s} (scikit-learn non installé)")
            continue
        print(f"{mode:12s} {p:6.2f} {r:12.2f}")
