# semantique.py : recherche "semantique" avec TF-IDF + LSA (needs : pip install scikit-learn)
# idee : LSA regroupe les mots qui apparaissent dans les memes documents. Une requete avec le mot "hygiene"
# ramene aussi des offres de sante qui ne contiennent pas ce mot, mais qui parlent des memes choses.
# limite : un mot absent du corpus ne donne rien, et il n'y a pas de traduction (francais <-> anglais).

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .index import normaliser

SEUIL = 0.1    # en dessous de cette similarite (cosinus), on ne garde pas le document


class Semantique:
    def __init__(self, docs, texte, composantes=None):
        self.vec = TfidfVectorizer(analyzer=normaliser, sublinear_tf=True)
        X = self.vec.fit_transform([texte(d) for d in docs])
        # nombre de "themes" retenus : il doit rester bien plus petit que le vocabulaire, sinon LSA ne generalise plus
        # (regle simple : un dixieme du vocabulaire, entre 10 et 100)
        k = composantes or min(100, max(10, X.shape[1] // 10))
        k = max(1, min(k, X.shape[1] - 1, X.shape[0] - 1))
        self.svd = TruncatedSVD(n_components=k, random_state=0)
        self.matrice = normalize(self.svd.fit_transform(X))   # un vecteur par document

    def scores(self, requete, limite=200):
        # renvoie [(numero_du_doc, similarite)] du plus proche au moins proche
        q = self.vec.transform([requete])
        if q.nnz == 0:                      # aucun mot de la requete n'existe dans le corpus
            return []
        v = normalize(self.svd.transform(q))
        s = (self.matrice @ v.T).ravel()
        meilleurs = np.argsort(-s)[:limite]
        return [(int(i), float(s[i])) for i in meilleurs if s[i] >= SEUIL]
