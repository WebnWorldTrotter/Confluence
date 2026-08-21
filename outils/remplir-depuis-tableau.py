#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remplir-depuis-tableau.py
=============================================================================
Prend le tableau des responsables (CSV) et le fichier HTML de la page, et
produit une page HTML avec les noms et les liens DEJA REMPLIS dedans.

A QUOI CA SERT
    Normalement la page lit le tableau toute seule a chaque affichage : tu
    n'as pas besoin de ce script. Il sert de solution de repli si Confluence
    empeche la page de lire le fichier CSV (politique de securite du site).
    Dans ce cas tu lances ce script apres chaque changement de responsable,
    et tu recolles le resultat dans le module HTML.

UTILISATION
    python3 outils/remplir-depuis-tableau.py

    Ou, pour preciser les fichiers :
    python3 outils/remplir-depuis-tableau.py mon-tableau.csv ma-page.html

    Le resultat est ecrit dans :  page-remplie.html

CE QUE LE SCRIPT VERIFIE
    - une cle du tableau qui n'existe pas dans la page  -> signale
    - une cle de la page absente du tableau             -> signale
    C'est ce qui evite les fautes de frappe silencieuses.
=============================================================================
"""

import csv
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CSV_PAR_DEFAUT = RACINE / "donnees" / "responsables.csv"
HTML_PAR_DEFAUT = RACINE / "blocks" / "00-facile-a-modifier.html"
SORTIE_PAR_DEFAUT = RACINE / "page-remplie.html"


def lire_tableau(chemin):
    """Lit le CSV et renvoie {cle: {"nom": ..., "lien": ...}}.

    Le separateur (point-virgule ou virgule) est detecte automatiquement :
    Excel en francais enregistre avec des points-virgules, Excel en anglais
    avec des virgules.
    """
    texte = chemin.read_text(encoding="utf-8-sig")  # -sig retire le marqueur Windows
    premiere = texte.splitlines()[0] if texte.splitlines() else ""
    separateur = ";" if premiere.count(";") > premiere.count(",") else ","

    lignes = {}
    lecteur = csv.DictReader(texte.splitlines(), delimiter=separateur)

    if not lecteur.fieldnames:
        raise SystemExit("Le tableau est vide.")

    colonnes = [c.strip().lower() for c in lecteur.fieldnames]
    if "cle" not in colonnes or "nom" not in colonnes:
        raise SystemExit(
            "Le tableau doit contenir au minimum les colonnes 'cle' et 'nom'.\n"
            "Colonnes trouvees : " + ", ".join(colonnes)
        )

    for brut in lecteur:
        ligne = {(k or "").strip().lower(): (v or "").strip()
                 for k, v in brut.items()}
        cle = ligne.get("cle", "")
        if not cle:
            continue
        lignes[cle] = {"nom": ligne.get("nom", ""), "lien": ligne.get("lien", "")}

    return lignes


def echapper_html(texte):
    """Empeche qu'un nom contenant < > & ne casse la page."""
    return (texte.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def remplir(html, tableau):
    """Remplace les noms (data-cle) et les liens (data-lien) dans le HTML."""
    noms_remplaces = 0
    liens_remplaces = 0
    cles_utilisees = set()

    # --- Les noms : <p ... data-cle="xxx">ancien texte</p> ------------------
    def remplacer_nom(m):
        nonlocal noms_remplaces
        avant, cle, apres = m.group(1), m.group(2), m.group(3)
        entree = tableau.get(cle)
        if not entree or not entree["nom"]:
            return m.group(0)
        cles_utilisees.add(cle)
        noms_remplaces += 1
        return avant + cle + apres.split(">", 1)[0] + ">" \
            + echapper_html(entree["nom"]) + "</p>"

    html = re.sub(
        r'(<p[^>]*data-cle=")([a-z0-9\-]+)("[^>]*>)[^<]*</p>',
        remplacer_nom, html)

    # --- Les liens : <a ... data-lien="xxx" ... href="..."> -----------------
    def remplacer_lien(m):
        nonlocal liens_remplaces
        balise, cle = m.group(0), m.group(1)
        entree = tableau.get(cle)
        if not entree or not entree["lien"]:
            return balise
        cles_utilisees.add(cle)
        liens_remplaces += 1
        return re.sub(r'href="[^"]*"', 'href="%s"' % entree["lien"], balise, count=1)

    html = re.sub(r'<a[^>]*data-lien="([a-z0-9\-]+)"[^>]*>',
                  remplacer_lien, html)

    return html, noms_remplaces, liens_remplaces, cles_utilisees


def main():
    chemin_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PAR_DEFAUT
    chemin_html = Path(sys.argv[2]) if len(sys.argv) > 2 else HTML_PAR_DEFAUT
    sortie = Path(sys.argv[3]) if len(sys.argv) > 3 else SORTIE_PAR_DEFAUT

    for f in (chemin_csv, chemin_html):
        if not f.exists():
            raise SystemExit("Fichier introuvable : %s" % f)

    tableau = lire_tableau(chemin_csv)
    html = chemin_html.read_text(encoding="utf-8")

    # Les cles reellement presentes dans la page
    cles_page = set(re.findall(r'data-(?:cle|lien)="([a-z0-9\-]+)"', html))

    html_rempli, noms, liens, utilisees = remplir(html, tableau)
    sortie.write_text(html_rempli, encoding="utf-8")

    print("Tableau : %s" % chemin_csv)
    print("Page    : %s" % chemin_html)
    print("Sortie  : %s" % sortie)
    print()
    print("  %d nom(s) et %d lien(s) remplis." % (noms, liens))

    # --- Signalements : c'est ce qui rattrape les fautes de frappe ----------
    renseignees = {c for c, v in tableau.items() if v["nom"] or v["lien"]}
    inconnues = sorted(renseignees - cles_page)
    if inconnues:
        print()
        print("  ATTENTION — cles du tableau absentes de la page")
        print("  (faute de frappe ? carte supprimee ?) :")
        for c in inconnues:
            print("    - %s" % c)

    non_remplies = sorted(cles_page - utilisees)
    if non_remplies:
        print()
        print("  Cles de la page encore sans valeur dans le tableau :")
        for c in non_remplies:
            print("    - %s" % c)

    print()
    print("Ouvre %s, copie tout son contenu, et colle-le dans le" % sortie.name)
    print("module HTML de Confluence.")


if __name__ == "__main__":
    main()
