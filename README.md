# Moteur de recherche d'offres d'emploi

![capture](capture.png)

*English version below.*

Un moteur de recherche écrit en Python pour des offres d'emploi : recherche par mots-clés (BM25), recherche
sémantique (TF-IDF + LSA), facettes et page web. Le cœur n'a besoin d'aucune librairie ; scikit-learn n'est utile
que pour la recherche sémantique.

## Démarrage rapide

```bash
python moteur_offres.py "ingénieur NLP"                     # 1 500 offres fictives, résultats dans le terminal
python moteur_offres.py --web                               # page web sur http://localhost:8000

pip install -r requirements.txt                             # pour la recherche sémantique et l'évaluation
python moteur_offres.py "hygiène" --mode semantique

python telecharger_donnees.py                               # télécharge ~38 000 vraies offres (9 Mo)
python moteur_offres.py "backend developer" --donnees reel --mode hybride
python moteur_offres.py --web --donnees reel
```

Testé avec Python 3.11.

## Les deux corpus

| | Fictif (par défaut) | Réel (`--donnees reel`) |
| --- | --- | --- |
| Taille | 1 500 offres | environ 38 000 offres |
| Langue | français | anglais |
| Contenu | titre, description, ville, secteur, contrat, salaire, expérience, date | titre, entreprise, lieu, plateforme, contrat, télétravail, date, lien |
| Source | généré par `moteur/corpus.py` (graine fixe) | [open-jobs-data](https://github.com/ConorsCode/open-jobs-data) |

Les vraies offres ne sont **pas** dans ce dépôt : le code de la source est sous licence MIT, mais les offres
appartiennent aux entreprises. `telecharger_donnees.py` les récupère dans `data/` (ignoré par git).
Le fichier n'a pas de description ni de salaire : on n'indexe que le titre, l'entreprise, le lieu et le département.

## Trois modes de recherche

- **mots** : index inversé et score BM25. Le texte est mis en minuscules, sans accents, sans mots vides ni pluriels
  (« Éducation » = « education », « vendeurs » = « vendeur »). Le titre compte double.
- **semantique** : TF-IDF puis LSA (SVD). Les mots qui apparaissent dans les mêmes offres se retrouvent proches,
  donc « hygiène » ramène aussi des offres de santé qui ne contiennent pas ce mot. Sur les vraies offres,
  « nurse » ramène aussi « Nurse Practitioner or Physician Assistant », et « backend developer » ramène
  « Backend Engineer ».
- **hybride** : fusion des deux classements (Reciprocal Rank Fusion).

## Facettes

Les facettes sont décrites dans une liste (`CONFIG_FICTIF` et `CONFIG_REEL` dans `moteur/corpus.py`) et recalculées
sur les résultats de chaque recherche. Chaque case est cliquable sur la page web et ajoute un filtre.

| Type | Corpus fictif | Corpus réel |
| --- | --- | --- |
| Champ | secteur, type de contrat | plateforme, type de contrat, télétravail |
| Intervalles réguliers | salaire (tranches de 10 000 €) | ancienneté de l'offre (tranches de 30 jours) |
| Intervalles sur mesure | expérience (0-1 an, 2-5 ans, 6 ans et plus) | taille de l'entreprise (selon son nombre d'offres) |
| Pivot | secteur, puis contrat | plateforme, puis contrat |

Le pivot révèle un défaut des vraies données : sur Greenhouse (24 844 offres sur 37 996), le type de contrat n'est
jamais renseigné. Dans le fichier, le contrat s'écrit aussi de 25 façons (`FullTime`, `Full-time`, `Full time`…) :
`contrat_propre()` les regroupe.

## Évaluation

`python evaluation.py` compare les trois modes sur le corpus fictif. Chaque requête est un mot d'un secteur
(« hygiène » pour la santé, « caisse » pour la vente…), 24 requêtes au total. Une offre est pertinente si elle est du
bon secteur, même sans le mot de la requête.

| Mode | P@10 | R-précision |
| --- | --- | --- |
| mots | 1,00 | 0,64 |
| sémantique | 1,00 | 0,94 |
| hybride | 1,00 | 0,94 |

*P@10* : part des 10 premiers résultats qui sont du bon secteur. *R-précision* : même mesure sur les R premiers
résultats, où R est le nombre d'offres du secteur ; 1,00 veut dire que le moteur retrouve toutes les offres du secteur.

À lire avec prudence : le corpus est fictif et construit par secteur, ce qui avantage la recherche sémantique.
Le nombre de thèmes de LSA compte beaucoup : avec 100 thèmes sur un vocabulaire de 150 mots, la sémantique ne
généralise plus (R-précision 0,43 avec le seuil de similarité d'origine, 0,71 sans). La valeur retenue (un dixième
du vocabulaire, entre 10 et 100) a été choisie après avoir essayé plusieurs valeurs sur ces mêmes requêtes :
le chiffre est donc optimiste. Il n'y a pas d'évaluation sur les vraies offres, faute de réponses attendues.

## Tests

```bash
python -m unittest discover -v
```
18 tests : nettoyage du texte, recherche, cohérence des facettes (la somme des cases égale le nombre de résultats,
un filtre donne le nombre affiché), recherche sémantique (si scikit-learn est installé) et page web.

## Organisation

```
moteur_offres.py         point d'entrée (terminal ou page web)
telecharger_donnees.py   télécharge les vraies offres dans data/
evaluation.py            compare mots, sémantique et hybride
moteur/
  corpus.py              les deux corpus et leur configuration
  index.py               nettoyage du texte, index inversé, BM25
  semantique.py          TF-IDF + LSA (scikit-learn)
  facettes.py            facettes de champ, d'intervalles et pivot
  recherche.py           classe Moteur : recherche, modes, filtres
  web.py                 page web (serveur http de la librairie standard)
tests/test_moteur.py
```

## Limites

- Le corpus fictif sert à tester le moteur, pas à analyser le marché de l'emploi.
- La recherche par mots est un « ou » entre les mots : « machine learning engineer » ramène aussi tous les
  « engineer ». Les offres qui contiennent les trois mots passent en premier.
- La recherche sémantique ne traduit pas (une requête française ne trouve pas une offre anglaise) et ne connaît que
  les mots du corpus. Elle garde au plus 200 résultats.
- Pas de correction de fautes de frappe, pas de sauvegarde de l'index : il est reconstruit à chaque lancement
  (une seconde pour 38 000 offres, trois secondes de plus pour le modèle sémantique).

---

# Job search engine

A job-offer search engine in Python: keyword search (BM25), semantic search (TF-IDF + LSA), facets and a small web
page. The core has no dependencies; scikit-learn is only needed for semantic search and the evaluation.

```bash
python moteur_offres.py "software engineer"                          # 1,500 fictional offers (in French)
python moteur_offres.py --web                                        # web page on http://localhost:8000

pip install -r requirements.txt                                      # semantic search + evaluation
python telecharger_donnees.py                                        # downloads ~38,000 real offers (9 MB)
python moteur_offres.py "backend developer" --donnees reel --mode hybride
python moteur_offres.py --web --donnees reel
python -m unittest discover -v                                       # 18 tests
```

- **Data**: a fictional French corpus (default) or ~38,000 real, English-language offers from
  [open-jobs-data](https://github.com/ConorsCode/open-jobs-data). The real data is downloaded, not stored in this
  repository: the source's code is MIT-licensed but the offers belong to the employers. It has no description or
  salary, so only title, company, location and department are indexed.
- **Search modes**: `mots` (BM25), `semantique` (LSA: finds related offers that do not contain the query word, e.g.
  "nurse" also returns "Nurse Practitioner or Physician Assistant"), `hybride` (rank fusion of both).
- **Facets**: field facets, regular intervals, custom intervals and a pivot, all described in a config list and
  recomputed on each result set. On the real data the pivot shows that Greenhouse (24,844 of 37,996 offers) never
  fills in the contract type.
- **Evaluation** (`python evaluation.py`, 24 queries on the fictional corpus): R-precision 0.64 for keywords vs 0.94
  for semantic and hybrid. Read with caution: the corpus is synthetic and built by sector, which favours semantic
  search, and the number of LSA topics was chosen after trying several values on the same queries, so the figure
  is optimistic. There is no evaluation on the real offers.
- **Limits**: no translation (a French query does not find an English offer), no typo correction, the index is
  rebuilt at every start.

Tested with Python 3.11.
