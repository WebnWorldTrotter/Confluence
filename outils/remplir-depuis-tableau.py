#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remplir-depuis-tableau.py
=============================================================================
Prend le tableau des responsables et la page HTML, et produit une page avec
les noms (et eventuellement les liens) deja remplis dedans.

  tableau (Excel/CSV)  +  page HTML  ->  page-remplie.html
                                          a coller dans Confluence

UTILISATION
    1. Fabriquer le tableau a partir de la page (une seule fois, et a refaire
       si on ajoute ou renomme des cartes) :
           python3 outils/remplir-depuis-tableau.py --cartes

    2. Remplir les colonnes 'nom' et 'lien' dans Excel, enregistrer en
       CSV UTF-8.

    3. Produire la page remplie :
           python3 outils/remplir-depuis-tableau.py

    Ou en precisant les fichiers :
    python3 outils/remplir-depuis-tableau.py mon-tableau.csv ma-page.html

COMMENT LE SCRIPT RECONNAIT LES CARTES
    Par leur TITRE, celui qui s'affiche sur la carte. Rien a ajouter dans le
    HTML : le tableau utilise directement les intitules visibles.

        <p class="carte-titre">A6 Dev</p>          <- reconnu par "A6 Dev"
        <p class="carte-personne">...</p>          <- c'est cette ligne qui
                                                      est remplacee

    Le nom du bandeau d'accueil se pilote avec la cle "Head of PMO"
    (l'intitule affiche au-dessus du nom).

CE QUE LE SCRIPT SIGNALE
    - une carte du tableau introuvable dans la page  -> signale
    - une carte de la page absente du tableau        -> signale
    - deux cartes portant le meme titre              -> signale
    C'est ce qui evite les fautes de frappe silencieuses.

CE QU'IL NE TOUCHE JAMAIS
    Les exemples ecrits dans les commentaires du HTML (le guide en haut du
    fichier). Ils ressemblent a de vraies cartes mais n'en sont pas : le
    script les ignore explicitement.
=============================================================================
"""

import csv
import html as html_module
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CSV_PAR_DEFAUT = RACINE / "donnees" / "responsables.csv"
HTML_PAR_DEFAUT = RACINE / "blocks" / "00-facile-a-modifier.html"
SORTIE_PAR_DEFAUT = RACINE / "page-remplie.html"

CLE_BANDEAU = "Head of PMO"


# ---------------------------------------------------------------------------
# Lecture du tableau
# ---------------------------------------------------------------------------

def lire_tableau(chemin):
    """Renvoie {titre_de_carte: {"nom": ..., "lien": ...}} et l'ordre de lecture.

    Le separateur est detecte automatiquement : Excel en francais enregistre
    avec des points-virgules, Excel en anglais avec des virgules.
    """
    texte = chemin.read_text(encoding="utf-8-sig")  # -sig retire le marqueur Windows
    lignes_brutes = texte.splitlines()
    if not lignes_brutes:
        raise SystemExit("Le tableau est vide.")

    premiere = lignes_brutes[0]
    separateur = ";" if premiere.count(";") > premiere.count(",") else ","

    lecteur = csv.DictReader(lignes_brutes, delimiter=separateur)
    colonnes = [(c or "").strip().lower() for c in (lecteur.fieldnames or [])]

    if "carte" not in colonnes or "nom" not in colonnes:
        raise SystemExit(
            "Le tableau doit contenir au minimum les colonnes 'carte' et 'nom'.\n"
            "Colonnes trouvees : " + (", ".join(colonnes) if colonnes else "aucune")
        )

    entrees = {}
    ordre = []
    for brut in lecteur:
        ligne = {(k or "").strip().lower(): (v or "").strip()
                 for k, v in brut.items()}
        carte = ligne.get("carte", "")
        if not carte:
            continue
        entrees[normaliser(carte)] = {
            "titre": carte,
            "nom": ligne.get("nom", ""),
            "lien": ligne.get("lien", ""),
        }
        ordre.append(carte)
    return entrees, ordre


def normaliser(titre):
    """Rend la comparaison des titres tolerante.

    Le HTML ecrit "Promethee &middot; Maia" la ou l'utilisateur tape
    "Promethee · Maia" dans Excel. On decode donc les entites HTML, on
    ramene les espaces multiples a un seul, et on ignore la casse.
    """
    titre = html_module.unescape(titre)
    titre = re.sub(r"\s+", " ", titre).strip()
    return titre.lower()


# ---------------------------------------------------------------------------
# Reperage des zones de commentaire
# ---------------------------------------------------------------------------

def zones_de_commentaire(html):
    """Renvoie la liste des (debut, fin) des commentaires HTML.

    Indispensable : le guide en tete de fichier contient des exemples de
    cartes qui ressemblent a du vrai balisage. Sans cette precaution, le
    script remplacerait le nom dans la documentation elle-meme.
    """
    return [(m.start(), m.end()) for m in re.finditer(r"<!--.*?-->", html, re.S)]


def dans_un_commentaire(position, zones):
    return any(debut <= position < fin for debut, fin in zones)


# ---------------------------------------------------------------------------
# Remplissage
# ---------------------------------------------------------------------------

MOTIF_CARTE = re.compile(
    r'(<a\s[^>]*class="[^"]*\bcarte\b[^"]*"[^>]*>)(.*?)(</a>)', re.S)
MOTIF_TITRE = re.compile(r'<p class="carte-titre">(.*?)</p>', re.S)
MOTIF_PERSONNE = re.compile(r'(<p class="carte-personne">)(.*?)(</p>)', re.S)
MOTIF_HREF = re.compile(r'href="[^"]*"')


def echapper(texte):
    """Empeche qu'un nom contenant < > & ne casse la page."""
    return (texte.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def remplir(html, entrees):
    zones = zones_de_commentaire(html)

    # titre normalise -> {"n": occurrences dans la page, "titre": intitule affiche}
    titres_vus = {}
    utilisees = set()
    compteur = {"noms": 0, "liens": 0}

    def traiter_carte(m):
        # Les exemples du guide sont dans des commentaires : on les laisse.
        if dans_un_commentaire(m.start(), zones):
            return m.group(0)

        ouvrante, interieur, fermante = m.group(1), m.group(2), m.group(3)

        titre_trouve = MOTIF_TITRE.search(interieur)
        if not titre_trouve:
            return m.group(0)

        affiche = re.sub(r"\s+", " ", html_module.unescape(titre_trouve.group(1))).strip()
        cle = normaliser(titre_trouve.group(1))
        vu = titres_vus.setdefault(cle, {"n": 0, "titre": affiche})
        vu["n"] += 1

        entree = entrees.get(cle)
        if not entree:
            return m.group(0)
        utilisees.add(cle)

        if entree["nom"]:
            def poser_nom(p):
                compteur["noms"] += 1
                return p.group(1) + echapper(entree["nom"]) + p.group(3)
            interieur = MOTIF_PERSONNE.sub(poser_nom, interieur, count=1)

        if entree["lien"]:
            ouvrante, remplace = MOTIF_HREF.subn(
                'href="%s"' % entree["lien"], ouvrante, count=1)
            compteur["liens"] += remplace

        return ouvrante + interieur + fermante

    html = MOTIF_CARTE.sub(traiter_carte, html)

    # --- Le nom du bandeau d'accueil, qui n'est pas une carte ---------------
    entree_bandeau = entrees.get(normaliser(CLE_BANDEAU))
    if entree_bandeau and entree_bandeau["nom"]:
        def poser_bandeau(m):
            if dans_un_commentaire(m.start(), zones):
                return m.group(0)
            compteur["noms"] += 1
            return m.group(1) + echapper(entree_bandeau["nom"]) + m.group(3)

        html, n = re.subn(r'(<p class="entete-contact-nom">)(.*?)(</p>)',
                          poser_bandeau, html, count=1, flags=re.S)
        if n:
            utilisees.add(normaliser(CLE_BANDEAU))
            titres_vus[normaliser(CLE_BANDEAU)] = {"n": 1, "titre": CLE_BANDEAU}

    return html, compteur, titres_vus, utilisees


# ---------------------------------------------------------------------------
# Mode --cartes : fabriquer le tableau a partir de la page
# ---------------------------------------------------------------------------

def lister_cartes(html):
    """Renvoie les intitules des cartes, dans l'ordre de la page.

    Sert a produire un tableau dont les titres sont forcement justes : c'est
    la page qui les dicte, personne ne les retape.
    """
    zones = zones_de_commentaire(html)
    titres = []
    for m in MOTIF_CARTE.finditer(html):
        if dans_un_commentaire(m.start(), zones):
            continue
        t = MOTIF_TITRE.search(m.group(2))
        if not t:
            continue
        affiche = re.sub(r"\s+", " ", html_module.unescape(t.group(1))).strip()
        if affiche not in titres:
            titres.append(affiche)
    return titres


def ecrire_modele(chemin_html, sortie):
    """Aligne le tableau sur les cartes de la page, SANS perdre le travail deja
    fait : les noms et liens deja saisis sont reportes tels quels. Seules les
    cartes nouvelles apparaissent vides, et les lignes qui ne correspondent
    plus a aucune carte disparaissent (elles sont annoncees avant)."""
    with open(chemin_html, encoding="utf-8", newline="") as f:
        html = f.read()

    titres = lister_cartes(html)
    if re.search(r'<p class="entete-contact-nom">', html):
        titres.insert(0, CLE_BANDEAU)

    ancien = {}
    if sortie.exists():
        try:
            ancien, _ = lire_tableau(sortie)
        except SystemExit:
            ancien = {}   # tableau illisible : on repart d'une page blanche

    lignes = ["carte;nom;lien"]
    nouvelles, conservees = [], []
    for t in titres:
        precedent = ancien.get(normaliser(t), {})
        nom = precedent.get("nom", "")
        lien = precedent.get("lien", "")
        if nom or lien:
            conservees.append(t)
        else:
            nouvelles.append(t)
        lignes.append("%s;%s;%s" % (t, nom, lien))

    connus = {normaliser(t) for t in titres}
    perdues = sorted(v["titre"] for c, v in ancien.items()
                     if c not in connus and (v["nom"] or v["lien"]))

    sortie.write_text("\n".join(lignes) + "\n", encoding="utf-8-sig")

    print("Page    : %s" % chemin_html)
    print("Tableau : %s" % sortie)
    print()
    print("  %d carte(s) relevees dans la page." % len(titres))
    if conservees:
        print("  %d ligne(s) deja renseignee(s), conservees telles quelles."
              % len(conservees))
    if nouvelles:
        print()
        print("  A remplir :")
        for t in nouvelles:
            print("    - %s" % t)
    if perdues:
        print()
        print("  ATTENTION — ces lignes etaient renseignees mais ne")
        print("  correspondent plus a aucune carte de la page. Elles ont ete")
        print("  retirees du tableau :")
        for t in perdues:
            print("    - %s" % t)
    print()
    print("Ouvre ce fichier dans Excel, remplis les colonnes 'nom' et 'lien',")
    print("enregistre en CSV UTF-8, puis relance le script sans --cartes.")


# ---------------------------------------------------------------------------

def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    options = {a for a in sys.argv[1:] if a.startswith("--")}

    if options - {"--cartes"}:
        raise SystemExit("Option inconnue. Seule --cartes existe.")

    if "--cartes" in options:
        chemin_html = Path(arguments[0]) if arguments else HTML_PAR_DEFAUT
        sortie = Path(arguments[1]) if len(arguments) > 1 else CSV_PAR_DEFAUT
        if not chemin_html.exists():
            raise SystemExit("Fichier introuvable : %s" % chemin_html)
        ecrire_modele(chemin_html, sortie)
        return

    chemin_csv = Path(arguments[0]) if arguments else CSV_PAR_DEFAUT
    chemin_html = Path(arguments[1]) if len(arguments) > 1 else HTML_PAR_DEFAUT
    sortie = Path(arguments[2]) if len(arguments) > 2 else SORTIE_PAR_DEFAUT

    for f in (chemin_csv, chemin_html):
        if not f.exists():
            raise SystemExit("Fichier introuvable : %s" % f)

    entrees, _ordre = lire_tableau(chemin_csv)
    # newline="" : les fins de ligne du fichier d'origine sont conservees
    # telles quelles (Windows ou Unix), le fichier ressort a l'identique.
    with open(chemin_html, encoding="utf-8", newline="") as f:
        html = f.read()

    html_rempli, compteur, titres_vus, utilisees = remplir(html, entrees)

    with open(sortie, "w", encoding="utf-8", newline="") as f:
        f.write(html_rempli)

    print("Tableau : %s" % chemin_csv)
    print("Page    : %s" % chemin_html)
    print("Sortie  : %s" % sortie)
    print()
    print("  %d nom(s) et %d lien(s) remplis." % (compteur["noms"], compteur["liens"]))

    souci = False

    # --- Lignes du tableau qui ne correspondent a aucune carte -------------
    renseignees = {c for c, v in entrees.items() if v["nom"] or v["lien"]}
    introuvables = sorted(entrees[c]["titre"] for c in (renseignees - utilisees))
    if introuvables:
        souci = True
        print()
        print("  ATTENTION — ces lignes du tableau ne correspondent a aucune")
        print("  carte de la page (titre mal orthographie ? carte supprimee ?) :")
        for t in introuvables:
            print("    - %s" % t)

    # --- Cartes de la page absentes du tableau -----------------------------
    orphelines = sorted(v["titre"] for c, v in titres_vus.items() if c not in utilisees)
    if orphelines:
        print()
        print("  Cartes de la page sans ligne dans le tableau")
        print("  (elles gardent le texte ecrit dans le HTML) :")
        for t in orphelines:
            print("    - %s" % t)

    # --- Titres en double : le remplissage devient ambigu ------------------
    doublons = sorted((v["titre"], v["n"]) for v in titres_vus.values() if v["n"] > 1)
    if doublons:
        souci = True
        print()
        print("  ATTENTION — ces titres apparaissent plusieurs fois dans la")
        print("  page. Seule la premiere carte de chaque titre a ete remplie :")
        for t, n in doublons:
            print("    - %s  (%d fois)" % (t, n))

    print()
    if souci:
        print("Corrige les points ci-dessus, puis relance le script.")
    print("Ouvre %s, copie tout son contenu, et colle-le" % sortie.name)
    print("dans le module HTML de Confluence.")


if __name__ == "__main__":
    main()
