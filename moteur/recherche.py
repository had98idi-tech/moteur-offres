# recherche.py : la classe Moteur (recherche par mots, semantique ou hybride + facettes)

from . import facettes as fac
from .index import Index, normaliser


def fusion(listes, k=60):
    # fusion de plusieurs classements (Reciprocal Rank Fusion) : un doc bien classe dans les deux passe en premier
    score = {}
    for liste in listes:
        for rang, i in enumerate(liste):
            score[i] = score.get(i, 0) + 1 / (k + rang + 1)
    return sorted(score, key=lambda i: -score[i])


class Moteur:
    def __init__(self, docs, config):
        self.docs, self.config = docs, config
        self.index = Index(docs, config["texte"])
        self.defs = {f["nom"]: f for f in config["facettes"]}
        self._semantique = None

    def semantique(self):
        # construit le modele LSA la premiere fois qu'on en a besoin (quelques secondes)
        if self._semantique is None:
            from .semantique import Semantique     # import ici : scikit-learn est optionnel
            self._semantique = Semantique(self.docs, self.config["texte"])
        return self._semantique

    def chercher(self, requete, filtres=None, mode="mots", limite=200):
        # mode : "mots" (BM25), "semantique" (LSA) ou "hybride" (les deux fusionnes)
        # renvoie la liste des documents, du meilleur au moins bon
        if not normaliser(requete):
            numeros = list(range(len(self.docs)))              # pas de requete = toutes les offres
        else:
            mots = [i for i, _ in self.index.scores(requete)]
            if mode == "mots":
                numeros = mots
            else:
                sem = [i for i, _ in self.semantique().scores(requete, limite)]
                numeros = sem if mode == "semantique" else fusion([mots[:limite], sem])[:limite]
        docs = [self.docs[i] for i in numeros]
        return [d for d in docs if fac.garde(d, filtres or {}, self.defs)]

    def facettes(self, docs):
        return fac.calculer(docs, self.config)
