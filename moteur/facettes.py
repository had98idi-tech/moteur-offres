# facettes.py : les facettes sont decrites dans une liste (voir corpus.py), le code ci-dessous est le meme pour tous les corpus
# 3 types de facettes :
#   "champ"    : une case par valeur (ex : secteur)
#   "regulier" : intervalles de meme taille (ex : salaire par tranches de 10 000)
#   "perso"    : intervalles definis a la main (ex : experience 0-1 an / 2-5 ans / 6 ans et plus)
# + un pivot : un champ croise avec un autre (ex : secteur puis type de contrat)

import re
from collections import Counter


def etiquette(doc, f):
    # dans quelle case de la facette f tombe ce document ?
    v = doc.get(f["champ"])
    if v is None or v == "":
        return "Inconnu"
    if f["type"] == "champ":
        return str(v)
    if f["type"] == "regulier":
        pas, plafond = f["pas"], f.get("max")
        debut = int(v) // pas * pas
        if plafond is not None and debut >= plafond:
            return f"{plafond}+"
        return f"{debut}-{debut + pas}"
    for nom, (a, b) in f["tranches"].items():   # type "perso"
        if a <= v <= b:
            return nom
    return "Inconnu"


def ordre(label, f):
    # pour afficher les intervalles dans le bon ordre (pas par nombre d'offres)
    if f["type"] == "regulier":
        m = re.match(r"\d+", label)
        return int(m.group()) if m else 10 ** 9
    noms = list(f["tranches"])
    return noms.index(label) if label in noms else 10 ** 9


def garde(doc, filtres, defs):
    # le document respecte-t-il tous les filtres choisis ? (filtres = {nom_de_facette: case})
    return all(etiquette(doc, defs[nom]) == case for nom, case in filtres.items() if nom in defs)


def calculer(docs, config):
    res = {}
    for f in config["facettes"]:
        compte = Counter(etiquette(d, f) for d in docs)
        if f["type"] == "champ":
            res[f["nom"]] = sorted(compte.items(), key=lambda x: (-x[1], x[0]))
        else:
            res[f["nom"]] = sorted(compte.items(), key=lambda x: ordre(x[0], f))
    # pivot : [(case, total, [(sous-case, nb), ...]), ...]
    defs = {f["nom"]: f for f in config["facettes"]}
    a, b = config["pivot"]
    pivot = {}
    for d in docs:
        pivot.setdefault(etiquette(d, defs[a]), Counter())[etiquette(d, defs[b])] += 1
    res["pivot"] = [(k, sum(c.values()), c.most_common())
                    for k, c in sorted(pivot.items(), key=lambda x: -sum(x[1].values()))]
    return res
