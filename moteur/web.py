# web.py : petite page web (serveur http de python, aucune librairie)

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

MODES = {"mots": "Mots-clés (BM25)", "semantique": "Sémantique (LSA)", "hybride": "Hybride"}
STYLE = ("body{font-family:Arial;margin:0;background:#f4f6f8}header{background:#1f4e79;color:#fff;padding:12px 24px}"
         ".page{display:flex;gap:24px;padding:16px 24px}.g{width:280px;flex-shrink:0}.d{flex:1;min-width:0}"
         ".b{background:#fff;border-radius:6px;padding:10px 14px;margin-bottom:12px}h4{margin:0 0 6px;color:#1f4e79}"
         "ul{list-style:none;margin:0;padding:0;font-size:13px}ul ul{margin-left:14px}a{color:#1f4e79;text-decoration:none}"
         "input[type=text]{width:50%;padding:7px}details{font-size:12px;color:#444;margin-top:6px}")


def lien(q, mode, filtres, **nouveau):
    return "?" + urlencode({"q": q, "mode": mode, **filtres, **nouveau})


def page_html(moteur, q, mode, filtres):
    try:
        docs = moteur.chercher(q, filtres, mode)
    except ImportError:
        mode, docs = "mots", moteur.chercher(q, filtres, "mots")
    f = moteur.facettes(docs)
    L = lambda **kw: escape(lien(q, mode, filtres, **kw))     # raccourci pour les liens des facettes
    h = [f"<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'><title>Offres d'emploi</title><style>{STYLE}</style></head>"
         "<body><header><h2 style='margin:0'>Moteur de recherche d'offres d'emploi</h2></header><div class='page'><div class='g'>"]
    # colonne de gauche : une boite par facette
    for d in moteur.config["facettes"]:
        h.append(f"<div class='b'><h4>{escape(d['titre'])}</h4><ul>" + "".join(
            f"<li><a href='{L(**{d['nom']: case})}'>{escape(case)}</a> ({n})</li>" for case, n in f[d["nom"]]) + "</ul></div>")
    a, b = moteur.config["pivot"]
    h.append("<div class='b'><h4>Pivot : " + escape(a) + " &rarr; " + escape(b) + "</h4><ul>")
    for case, total, sous in f["pivot"][:15]:
        h.append(f"<li><a href='{L(**{a: case})}'>{escape(case)}</a> ({total})<ul>" + "".join(
            f"<li><a href='{L(**{a: case, b: sc})}'>{escape(sc)}</a> ({n})</li>" for sc, n in sous) + "</ul></li>")
    h.append("</ul></div></div><div class='d'>")
    # formulaire (avec le choix du mode) + filtres actifs
    options = "".join(f"<option value='{m}'{' selected' if m == mode else ''}>{t}</option>" for m, t in MODES.items())
    caches = "".join(f"<input type='hidden' name='{escape(k)}' value='{escape(v)}'>" for k, v in filtres.items())
    h.append(f"<form class='b'><input type='text' name='q' value='{escape(q)}' placeholder='ex : ingénieur NLP'> "
             f"<select name='mode'>{options}</select>{caches} <button>Rechercher</button></form>")
    if filtres:
        h.append("<div class='b'>Filtres : " + " ".join(
            f"<a href='{escape(lien(q, mode, {x: y for x, y in filtres.items() if x != k}))}'>{escape(v)} &times;</a>"
            for k, v in filtres.items()) + "</div>")
    h.append(f"<p><b>{len(docs)}</b> offre(s) (les 20 premières affichées)</p>")
    for d in docs[:20]:
        meta = " · ".join(escape(str(d[c])) for c in moteur.config["meta"] if d.get(c) not in (None, ""))
        champs = "".join(f"<li><b>{escape(k)}</b> : {escape(str(v))}</li>" for k, v in d.items())
        url = d.get("url", "")
        postuler = f" <a href='{escape(url, quote=True)}'>voir l'offre</a>" if url.startswith(("http://", "https://")) else ""
        h.append(f"<div class='b'><h3 style='margin:0 0 4px'>{escape(d['titre'])}</h3>"
                 f"<div style='font-size:13px;color:#555'>{meta}{postuler}</div><p>{escape(d['description'])}</p>"
                 f"<details><summary>Voir tous les champs</summary><ul>{champs}</ul></details></div>")
    h.append("</div></div></body></html>")
    return "".join(h)


def creer_serveur(moteur, port=8000):
    class Page(BaseHTTPRequestHandler):
        def do_GET(self):
            p = parse_qs(urlparse(self.path).query)
            q = p.get("q", [""])[0]
            mode = p.get("mode", ["mots"])[0]
            if mode not in MODES:
                mode = "mots"
            filtres = {k: v[0] for k, v in p.items() if k in moteur.defs}   # seuls les noms de facettes connus
            corps = page_html(moteur, q, mode, filtres).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(corps)

        def log_message(self, *args):   # pas de logs dans le terminal
            pass

    return HTTPServer(("localhost", port), Page)
