# index.py : nettoyage du texte, index inverse (mot -> documents) et score BM25

import math
import re
import unicodedata
from collections import Counter, defaultdict

# mots vides (francais + anglais, car les vraies offres sont en anglais)
MOTS_VIDES = set("le la les un une des de du d l et ou a au aux en dans pour par sur avec son sa ses est sont "
                 "ce cette h f the of and for to in at on an".split())


def normaliser(texte):
    # minuscules, accents enleves, mots vides enleves, pluriels enleves (vendeurs -> vendeur)
    texte = unicodedata.normalize("NFD", str(texte).lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    mots = re.findall(r"[a-z0-9+#]+", texte)
    return [m[:-1] if len(m) > 3 and m[-1] in "sx" else m for m in mots if m not in MOTS_VIDES]
  
class Index:
    def __init__(self, docs, texte):
        # texte(doc) = la fonction qui dit quel texte indexer pour un document
        self.mots = defaultdict(dict)   # self.mots["python"] = {numero_du_doc: nb_occurrences}
        self.longueur = []
        for i, d in enumerate(docs):
            tokens = normaliser(texte(d))
            self.longueur.append(len(tokens))
            for mot, nb in Counter(tokens).items():
                self.mots[mot][i] = nb
        self.nb_docs = len(docs)
        self.moyenne = sum(self.longueur) / max(self.nb_docs, 1)

    def scores(self, requete):
        # renvoie [(numero_du_doc, score BM25)] du meilleur au moins bon
        scores = Counter()
        for mot in set(normaliser(requete)):
            docs_du_mot = self.mots.get(mot, {})
            idf = math.log(1 + (self.nb_docs - len(docs_du_mot) + 0.5) / (len(docs_du_mot) + 0.5))
            for i, tf in docs_du_mot.items():
                scores[i] += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * self.longueur[i] / self.moyenne))
        return scores.most_common()
