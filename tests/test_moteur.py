# tests du moteur (depuis la racine du depot) :
#   python -m unittest discover -v
#   python -m unittest tests.test_moteur -v      (si la commande du dessus lance 0 test)
#   python tests/test_moteur.py

import os
import sys
import threading
import unittest
import urllib.request
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # racine du depot

from moteur import Moteur
from moteur.corpus import CONFIG_FICTIF, contrat_propre, fabriquer_corpus
from moteur.facettes import etiquette
from moteur.index import normaliser
from moteur.web import creer_serveur

try:
    import sklearn  # noqa: F401
    SKLEARN = True
except ImportError:
    SKLEARN = False

MOTEUR = Moteur(fabriquer_corpus(600), CONFIG_FICTIF)   # petit corpus : les tests vont vite


class TestTexte(unittest.TestCase):
    def test_accents_et_majuscules(self):
        self.assertEqual(normaliser("Éducation"), normaliser("education"))

    def test_pluriels(self):
        self.assertEqual(normaliser("vendeurs"), ["vendeur"])

    def test_mots_vides(self):
        self.assertEqual(normaliser("le chef de l'équipe"), ["chef", "equipe"])


class TestRecherche(unittest.TestCase):
    def test_trouve_les_bonnes_offres(self):
        res = MOTEUR.chercher("infirmier")
        self.assertGreater(len(res), 0)
        self.assertTrue(all("Infirmier" in d["titre"] for d in res))

    def test_sans_accent_meme_resultat(self):
        self.assertEqual(len(MOTEUR.chercher("éducation")), len(MOTEUR.chercher("education")))

    def test_requete_vide_renvoie_tout(self):
        self.assertEqual(len(MOTEUR.chercher("")), len(MOTEUR.docs))

    def test_mot_inconnu_renvoie_rien(self):
        self.assertEqual(MOTEUR.chercher("zzzzzz"), [])

    def test_le_meilleur_resultat_contient_le_mot(self):
        self.assertIn("cariste", MOTEUR.chercher("cariste")[0]["titre"].lower())


class TestFacettes(unittest.TestCase):
    def test_chaque_facette_compte_tous_les_documents(self):
        docs = MOTEUR.chercher("")
        f = MOTEUR.facettes(docs)
        for d in CONFIG_FICTIF["facettes"]:
            self.assertEqual(sum(n for _, n in f[d["nom"]]), len(docs), d["nom"])

    def test_le_pivot_est_coherent(self):
        f = MOTEUR.facettes(MOTEUR.chercher(""))
        self.assertEqual(sum(total for _, total, _ in f["pivot"]), len(MOTEUR.docs))
        for _, total, sous in f["pivot"]:
            self.assertEqual(sum(n for _, n in sous), total)

    def test_un_filtre_donne_le_nombre_affiche_dans_la_facette(self):
        f = MOTEUR.facettes(MOTEUR.chercher(""))
        for secteur, n in f["secteur"]:
            self.assertEqual(len(MOTEUR.chercher("", {"secteur": secteur})), n)

    def test_intervalles(self):
        d = {"salaire": 34500, "experience": 3}
        defs = {f["nom"]: f for f in CONFIG_FICTIF["facettes"]}
        self.assertEqual(etiquette(d, defs["salaire"]), "30000-40000")
        self.assertEqual(etiquette(d, defs["exp"]), "2-5 ans")

    def test_contrats_des_vraies_offres(self):
        self.assertEqual(contrat_propre("Full-Time"), "Temps plein")
        self.assertEqual(contrat_propre("Part time"), "Temps partiel")
        self.assertEqual(contrat_propre("Internship"), "Stage")
        self.assertEqual(contrat_propre(""), "Non renseigné")


@unittest.skipUnless(SKLEARN, "scikit-learn non installé")
class TestSemantique(unittest.TestCase):
    def test_trouve_plus_d_offres_du_secteur_que_les_mots(self):
        # "hygiène" n'est que dans une partie des offres de santé ; la recherche sémantique retrouve les autres
        mots = [d for d in MOTEUR.chercher("hygiène", mode="mots") if d["secteur"] == "Santé"]
        sem = [d for d in MOTEUR.chercher("hygiène", mode="semantique") if d["secteur"] == "Santé"]
        self.assertGreater(len(sem), len(mots))

    def test_les_premiers_resultats_sont_du_bon_secteur(self):
        top = MOTEUR.chercher("hygiène", mode="hybride")[:10]
        self.assertTrue(all(d["secteur"] == "Santé" for d in top))


class TestWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = creer_serveur(MOTEUR, port=0)          # port 0 = un port libre
        cls.port = cls.serveur.server_address[1]
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def lire(self, chemin):
        with urllib.request.urlopen(f"http://localhost:{self.port}/{chemin}") as r:
            return r.status, r.read().decode("utf-8")

    def test_page_d_accueil(self):
        statut, html = self.lire("")
        self.assertEqual(statut, 200)
        self.assertIn("offre(s)", html)

    def test_recherche_et_filtre(self):
        statut, html = self.lire("?q=infirmier&secteur=" + quote("Santé"))
        self.assertEqual(statut, 200)
        self.assertIn("Infirmier", html)

    def test_valeurs_bizarres_ne_cassent_pas_la_page(self):
        statut, html = self.lire("?q=%3Cscript%3E&mode=nimporte&salaire=abc&inconnu=1")
        self.assertEqual(statut, 200)
        self.assertNotIn("<script>", html)                    # le texte tapé est bien échappé


if __name__ == "__main__":
    unittest.main()

