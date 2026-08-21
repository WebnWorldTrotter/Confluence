#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remplir-depuis-tableau.py
=============================================================================
Prend le tableau des responsables et la page HTML, et produit une page ou les
noms, les liens et les images de fond sont deja en place.

  tableau (Excel/CSV)  +  page HTML  ->  page-remplie.html
                                          a coller dans Confluence

UTILISATION
    1. Fabriquer le tableau a partir de la page (a refaire si on ajoute,
       renomme ou supprime un element) :
           python3 outils/remplir-depuis-tableau.py --cartes

    2. Remplir les colonnes dans Excel, enregistrer en CSV UTF-8.

    3. Produire la page remplie :
           python3 outils/remplir-depuis-tableau.py

    Ou en precisant les fichiers :
    python3 outils/remplir-depuis-tableau.py mon-tableau.csv ma-page.html

LES COLONNES DU TABLEAU
    carte   l'intitule affiche sur la page. C'est lui qui sert de repere :
            rien a ajouter dans le HTML, pas d'identifiant a inventer.
    nom     le titulaire (cartes et bandeau d'accueil uniquement)
    lien    l'adresse de la page Confluence a ouvrir
    image   l'adresse de l'image de fond (cartes uniquement)

    Une cellule vide veut dire "ne touche pas a ce qui est deja dans le
    HTML". On peut donc ne remplir que la colonne qui change.

CE QUE LE SCRIPT SAIT REMPLIR
    les cartes    <a class="carte ...">   -> nom, lien, image
    les lignes    <a class="ligne ...">   -> lien          (onglet Group PMO)
    les tuiles    <a class="tuile ...">   -> lien          (onglet Transversal)
    les boutons   <a class="bouton">      -> lien
    le bandeau    "Head of PMO"           -> nom

    Une carte sans image de fond en recoit une automatiquement si la colonne
    image est renseignee : la balise <img class="carte-fond"> est inseree et
    la classe "carte-image" ajoutee. Rien a preparer a la main.

CE QUE LE SCRIPT SIGNALE
    - une ligne du tableau introuvable dans la page   -> ATTENTION
    - un element de la page absent du tableau         -> liste informative
    - deux elements portant le meme intitule          -> ATTENTION
    - un nom ou une image donne a un element qui n'en accepte pas
    C'est ce qui evite les fautes de frappe silencieuses.

CE QU'IL NE TOUCHE JAMAIS
    Les exemples ecrits dans les commentaires du HTML (le guide en haut du
    fichier). Ils ressemblent a de vraies cartes mais n'en sont pas : le
    script masque les commentaires avant toute recherche.
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

COLONNES = ("carte", "nom", "lien", "image")

# Ce que chaque famille d'element accepte comme colonnes.
ACCEPTE = {
    "carte":   {"nom", "lien", "image"},
    "ligne":   {"lien"},
    "tuile":   {"lien"},
    "bouton":  {"lien"},
    "bandeau": {"nom"},
}


# ---------------------------------------------------------------------------
# Comparaison des intitules
# ---------------------------------------------------------------------------

MOTIF_MASQUE = re.compile(r'<(\w+)[^>]*aria-hidden="true"[^>]*>.*?</\1>', re.S)
MOTIF_BALISE = re.compile(r"<[^>]*>")


def texte_visible(fragment):
    """Le texte que l'oeil lit, debarrasse du balisage.

    Les elements marques aria-hidden (la fleche des boutons, par exemple)
    sont retires avec leur contenu : ils ne font pas partie de l'intitule.
    Les entites sont decodees, ce qui fait correspondre le "&middot;" du
    HTML au "·" tape dans Excel.
    """
    fragment = MOTIF_MASQUE.sub(" ", fragment)
    fragment = MOTIF_BALISE.sub(" ", fragment)
    fragment = html_module.unescape(fragment)
    return re.sub(r"\s+", " ", fragment).strip()


def normaliser(intitule):
    """La cle de comparaison : intitule visible, espaces reduits, sans casse."""
    intitule = html_module.unescape(intitule)
    return re.sub(r"\s+", " ", intitule).strip().lower()


# ---------------------------------------------------------------------------
# Lecture du tableau
# ---------------------------------------------------------------------------

def lire_tableau(chemin):
    """Renvoie {cle: {"titre":, "nom":, "lien":, "image":}}.

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

    if "carte" not in colonnes:
        raise SystemExit(
            "Le tableau doit contenir au minimum une colonne 'carte'.\n"
            "Colonnes attendues : " + ", ".join(COLONNES) + "\n"
            "Colonnes trouvees  : " + (", ".join(colonnes) if colonnes else "aucune")
        )

    entrees = {}
    for brut in lecteur:
        ligne = {(k or "").strip().lower(): (v or "").strip()
                 for k, v in brut.items() if k is not None}
        intitule = ligne.get("carte", "")
        if not intitule:
            continue
        entrees[normaliser(intitule)] = {
            "titre": intitule,
            "nom": ligne.get("nom", ""),
            "lien": ligne.get("lien", ""),
            "image": ligne.get("image", ""),
        }
    return entrees


# ---------------------------------------------------------------------------
# Masquage du guide
# ---------------------------------------------------------------------------

def masquer_commentaires(html):
    """Renvoie une copie du HTML ou chaque commentaire est remplace par des
    espaces, a longueur egale.

    Indispensable, pour deux raisons. D'abord le guide en tete de fichier
    contient des exemples de cartes qui ressemblent a du vrai balisage :
    sans cette precaution, le script remplacerait le nom dans la
    documentation elle-meme. Ensuite ces exemples comportent des balises
    <a> ouvertes et jamais refermees ; une recherche naive les refermerait
    sur le premier </a> venu, en avalant au passage tout le debut de la
    page. Les positions sont conservees a l'identique : ce qui est trouve
    dans la copie se retrouve au meme endroit dans l'original.
    """
    morceaux, fin = [], 0
    for m in re.finditer(r"<!--.*?-->", html, re.S):
        morceaux.append(html[fin:m.start()])
        morceaux.append(re.sub(r"[^\n]", " ", m.group(0)))  # les sauts de
        fin = m.end()                                        # ligne restent
    morceaux.append(html[fin:])
    return "".join(morceaux)


# ---------------------------------------------------------------------------
# Reperage des elements
# ---------------------------------------------------------------------------

MOTIF_ANCRE = re.compile(r'(<a\s[^>]*>)(.*?)(</a>)', re.S)
MOTIF_TITRE = re.compile(r'<p class="carte-titre">(.*?)</p>', re.S)
MOTIF_PERSONNE = re.compile(r'(<p class="carte-personne">)(.*?)(</p>)', re.S)
MOTIF_BANDEAU = re.compile(r'(<p class="entete-contact-nom">)(.*?)(</p>)', re.S)
MOTIF_CLASSE = re.compile(r'class="([^"]*)"')
MOTIF_HREF = re.compile(r'href="[^"]*"')
MOTIF_IMG = re.compile(r'<img\s[^>]*class="[^"]*\bcarte-fond\b[^"]*"[^>]*>')
MOTIF_SRC = re.compile(r'src="[^"]*"')


# Valeurs qui ne sont pas de vraies donnees mais des marqueurs "a remplir".
# Relevees telles quelles dans le tableau, elles donneraient l'illusion d'une
# adresse deja renseignee.
REMPLIR_PLUS_TARD = {"REMPLACE_PAR_LE_LIEN", "ADRESSE_DE_LA_PAGE",
                     "ADRESSE_DE_L_IMAGE", "#", ""}


def vraie_valeur(valeur):
    """Rend la valeur si c'en est une, la chaine vide si c'est un marqueur."""
    valeur = html_module.unescape((valeur or "").strip())
    if valeur in REMPLIR_PLUS_TARD:
        return ""
    if valeur.startswith("{{") and valeur.endswith("}}"):
        return ""
    return valeur


def valeurs_actuelles(ouvrante, interieur, famille):
    """Ce que la page contient deja pour cet element.

    Permet au tableau de demarrer sur un etat fidele plutot que vide : les
    adresses et les images deja en place s'y retrouvent, et un aller-retour
    page -> tableau -> page ne change rien.
    """
    valeurs = {"nom": "", "lien": "", "image": ""}

    if "lien" in ACCEPTE[famille]:
        href = MOTIF_HREF.search(ouvrante)
        if href:
            valeurs["lien"] = vraie_valeur(href.group(0)[6:-1])

    if "nom" in ACCEPTE[famille]:
        motif = MOTIF_BANDEAU if famille == "bandeau" else MOTIF_PERSONNE
        personne = motif.search(interieur)
        if personne:
            valeurs["nom"] = vraie_valeur(texte_visible(personne.group(2)))

    if "image" in ACCEPTE[famille]:
        img = MOTIF_IMG.search(interieur)
        if img:
            src = MOTIF_SRC.search(img.group(0))
            if src:
                valeurs["image"] = vraie_valeur(src.group(0)[5:-1])

    return valeurs


def classes_de(balise):
    trouve = MOTIF_CLASSE.search(balise)
    return set(trouve.group(1).split()) if trouve else set()


def identifier(ouvrante, interieur):
    """Renvoie (intitule, famille) pour une ancre, ou (None, None) si l'ancre
    n'est pas un element pilotable."""
    classes = classes_de(ouvrante)
    if "carte" in classes:
        titre = MOTIF_TITRE.search(interieur)
        if not titre:
            return None, None
        return texte_visible(titre.group(1)), "carte"
    if "ligne" in classes:
        return texte_visible(interieur), "ligne"
    if "tuile" in classes:
        return texte_visible(interieur), "tuile"
    if "bouton" in classes:
        return texte_visible(interieur), "bouton"
    return None, None


def lister_elements(html):
    """Les elements pilotables de la page, dans l'ordre ou ils y apparaissent.

    Sert a produire un tableau dont les intitules sont forcement justes :
    c'est la page qui les dicte, personne ne les retape.
    """
    visible = masquer_commentaires(html)
    releve = []

    for m in MOTIF_ANCRE.finditer(visible):
        decoupe = MOTIF_ANCRE.match(html, m.start(), m.end())
        if not decoupe:
            continue
        ouvrante, interieur = decoupe.group(1), decoupe.group(2)
        intitule, famille = identifier(ouvrante, interieur)
        if intitule:
            releve.append((m.start(), intitule, famille,
                           valeurs_actuelles(ouvrante, interieur, famille)))

    for m in MOTIF_BANDEAU.finditer(visible):
        decoupe = MOTIF_BANDEAU.match(html, m.start(), m.end())
        actuelles = (valeurs_actuelles("", decoupe.group(0), "bandeau")
                     if decoupe else {"nom": "", "lien": "", "image": ""})
        releve.append((m.start(), CLE_BANDEAU, "bandeau", actuelles))
        break

    releve.sort(key=lambda e: e[0])

    # Un meme intitule peut apparaitre deux fois : une seule ligne de tableau.
    vus, ordonnes = set(), []
    for _, intitule, famille, actuelles in releve:
        if normaliser(intitule) in vus:
            continue
        vus.add(normaliser(intitule))
        ordonnes.append((intitule, famille, actuelles))
    return ordonnes


# ---------------------------------------------------------------------------
# Remplissage
# ---------------------------------------------------------------------------

def echapper(texte):
    """Empeche qu'un nom contenant < > & ne casse la page."""
    return (texte.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def attribut(valeur):
    """Prepare une adresse pour tenir dans un href="..." ou un src="...".

    Le passage par unescape avant escape rend l'operation sure quelle que
    soit la forme collee depuis le navigateur : une adresse contenant deja
    "&amp;" ne devient pas "&amp;amp;".
    """
    return html_module.escape(html_module.unescape(valeur), quote=True)


def poser_lien(ouvrante, url):
    """Remplace le href, ou l'ajoute si la balise n'en a pas."""
    nouvelle, remplaces = MOTIF_HREF.subn('href="%s"' % attribut(url),
                                          ouvrante, count=1)
    if remplaces:
        return nouvelle, 1
    return re.sub(r"^<a\b", '<a href="%s"' % attribut(url), ouvrante, count=1), 1


def ajouter_classe(ouvrante, classe):
    def maj(m):
        valeurs = m.group(1).split()
        if classe not in valeurs:
            valeurs.append(classe)
        return 'class="%s"' % " ".join(valeurs)
    return MOTIF_CLASSE.sub(maj, ouvrante, count=1)


def poser_image(ouvrante, interieur, url):
    """Met l'image de fond en place.

    Si la carte a deja une <img class="carte-fond">, seule son adresse
    change. Sinon la balise est creee en tete de carte, avec la meme
    indentation que le reste, et la classe "carte-image" est ajoutee pour
    que le voile de lisibilite s'applique.
    """
    src = attribut(url)
    existante = MOTIF_IMG.search(interieur)

    if existante:
        balise, remplaces = MOTIF_SRC.subn('src="%s"' % src,
                                           existante.group(0), count=1)
        if not remplaces:   # <img> sans src : on en ajoute un
            balise = re.sub(r"^<img\b", '<img src="%s"' % src,
                            existante.group(0), count=1)
        interieur = interieur[:existante.start()] + balise + interieur[existante.end():]
    else:
        blanc = re.match(r"\s*", interieur).group(0) or "\n"
        interieur = ('%s<img class="carte-fond" src="%s" alt="">%s'
                     % (blanc, src, interieur))

    return ajouter_classe(ouvrante, "carte-image"), interieur


def remplir(html, entrees):
    """Renvoie le HTML rempli, plus de quoi rendre compte du travail fait.

    Le reperage se fait sur la copie masquee (les commentaires n'y existent
    plus), mais le texte remplace est toujours pris dans l'original : les
    positions etant identiques dans les deux, chaque element trouve dans la
    copie designe exactement le meme endroit dans le fichier reel.
    """
    visible = masquer_commentaires(html)

    vus = {}            # cle -> {"n":, "titre":, "famille":}
    utilisees = set()
    compteur = {"noms": 0, "liens": 0, "images": 0}
    ignores = []        # (intitule, colonne, famille) fournis mais inutilisables
    remplacements = []  # (debut, fin, nouveau_texte)

    def noter(cle, intitule, famille):
        fiche = vus.setdefault(cle, {"n": 0, "titre": intitule, "famille": famille})
        fiche["n"] += 1

    def signaler_colonnes_inutiles(entree, famille, intitule):
        for colonne in ("nom", "lien", "image"):
            if entree[colonne] and colonne not in ACCEPTE[famille]:
                ignores.append((intitule, colonne, famille))

    # --- Cartes, lignes d'onglet et boutons --------------------------------
    for m in MOTIF_ANCRE.finditer(visible):
        decoupe = MOTIF_ANCRE.match(html, m.start(), m.end())
        if not decoupe:
            continue
        ouvrante, interieur, fermante = decoupe.group(1), decoupe.group(2), decoupe.group(3)

        intitule, famille = identifier(ouvrante, interieur)
        if not intitule:
            continue

        cle = normaliser(intitule)
        noter(cle, intitule, famille)

        entree = entrees.get(cle)
        if not entree:
            continue
        if cle not in utilisees:
            signaler_colonnes_inutiles(entree, famille, intitule)
        utilisees.add(cle)

        if entree["nom"] and "nom" in ACCEPTE[famille]:
            interieur, poses = MOTIF_PERSONNE.subn(
                lambda p: p.group(1) + echapper(entree["nom"]) + p.group(3),
                interieur, count=1)
            compteur["noms"] += poses

        if entree["lien"] and "lien" in ACCEPTE[famille]:
            ouvrante, poses = poser_lien(ouvrante, entree["lien"])
            compteur["liens"] += poses

        if entree["image"] and "image" in ACCEPTE[famille]:
            ouvrante, interieur = poser_image(ouvrante, interieur, entree["image"])
            compteur["images"] += 1

        remplacements.append((m.start(), m.end(), ouvrante + interieur + fermante))

    # --- Le nom du bandeau d'accueil, qui n'est pas une ancre --------------
    cle_bandeau = normaliser(CLE_BANDEAU)
    entree_bandeau = entrees.get(cle_bandeau)

    for m in MOTIF_BANDEAU.finditer(visible):
        noter(cle_bandeau, CLE_BANDEAU, "bandeau")
        if entree_bandeau:
            if cle_bandeau not in utilisees:
                signaler_colonnes_inutiles(entree_bandeau, "bandeau", CLE_BANDEAU)
            utilisees.add(cle_bandeau)
            if entree_bandeau["nom"]:
                decoupe = MOTIF_BANDEAU.match(html, m.start(), m.end())
                if decoupe:
                    compteur["noms"] += 1
                    remplacements.append((
                        m.start(), m.end(),
                        decoupe.group(1) + echapper(entree_bandeau["nom"])
                        + decoupe.group(3)))
        break   # un seul bandeau d'accueil par page

    # --- Reconstruction ----------------------------------------------------
    remplacements.sort(key=lambda r: r[0])
    morceaux, curseur = [], 0
    for debut, fin, texte in remplacements:
        morceaux.append(html[curseur:debut])
        morceaux.append(texte)
        curseur = fin
    morceaux.append(html[curseur:])

    return "".join(morceaux), compteur, vus, utilisees, ignores


# ---------------------------------------------------------------------------
# Mode --cartes : fabriquer le tableau a partir de la page
# ---------------------------------------------------------------------------

ETIQUETTE = {"carte": "cartes", "ligne": "lignes d'onglet",
             "tuile": "tuiles transversales", "bouton": "boutons",
             "bandeau": "bandeau d'accueil"}


def ecrire_modele(chemin_html, sortie):
    """Aligne le tableau sur la page, SANS perdre le travail deja fait : les
    valeurs deja saisies sont reportees telles quelles. Seuls les elements
    nouveaux apparaissent vides, et les lignes qui ne correspondent plus a
    rien disparaissent (elles sont annoncees avant)."""
    with open(chemin_html, encoding="utf-8", newline="") as f:
        html = f.read()

    elements = lister_elements(html)

    ancien = {}
    if sortie.exists():
        try:
            ancien = lire_tableau(sortie)
        except SystemExit:
            ancien = {}   # tableau illisible : on repart d'une page blanche

    lignes = [list(COLONNES)]
    a_remplir, conservees = [], 0
    for intitule, famille, actuelles in elements:
        precedent = ancien.get(normaliser(intitule), {})
        cellules = []
        for colonne in ("nom", "lien", "image"):
            if colonne not in ACCEPTE[famille]:
                cellules.append("")
                continue
            # Le tableau fait foi s'il dit quelque chose ; sinon on releve ce
            # que la page contient deja, pour ne rien perdre.
            cellules.append(precedent.get(colonne, "") or actuelles[colonne])
        if any(cellules):
            conservees += 1
        else:
            a_remplir.append((intitule, famille))
        lignes.append([intitule] + cellules)

    connus = {normaliser(i) for i, _, _ in elements}
    perdues = sorted(v["titre"] for c, v in ancien.items()
                     if c not in connus and (v["nom"] or v["lien"] or v["image"]))

    # csv.writer plutot qu'un simple join : un intitule contenant un
    # point-virgule ou une virgule est alors protege par des guillemets, et
    # Excel le relit correctement.
    with open(sortie, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(lignes)

    print("Page    : %s" % chemin_html)
    print("Tableau : %s" % sortie)
    print()
    print("  %d element(s) relevé(s) dans la page." % len(elements))
    if conservees:
        print("  %d ligne(s) deja renseignee(s) (tableau precedent ou valeurs"
              % conservees)
        print("     deja presentes dans la page), conservees telles quelles.")

    if a_remplir:
        print()
        print("  A remplir :")
        famille_courante = None
        for intitule, famille in a_remplir:
            if famille != famille_courante:
                famille_courante = famille
                print("    [%s]" % ETIQUETTE[famille])
            print("      - %s" % intitule)

    if perdues:
        print()
        print("  ATTENTION — ces lignes etaient renseignees mais ne")
        print("  correspondent plus a aucun element de la page. Elles ont")
        print("  ete retirees du tableau :")
        for t in perdues:
            print("    - %s" % t)

    print()
    print("Colonnes : carte (repere, ne pas modifier) | nom | lien | image")
    print("Ouvre ce fichier dans Excel, remplis ce qui change, enregistre en")
    print("CSV UTF-8, puis relance le script sans --cartes.")


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

    entrees = lire_tableau(chemin_csv)

    # newline="" : les fins de ligne du fichier d'origine sont conservees
    # telles quelles (Windows ou Unix), le fichier ressort a l'identique.
    with open(chemin_html, encoding="utf-8", newline="") as f:
        html = f.read()

    html_rempli, compteur, vus, utilisees, ignores = remplir(html, entrees)

    with open(sortie, "w", encoding="utf-8", newline="") as f:
        f.write(html_rempli)

    print("Tableau : %s" % chemin_csv)
    print("Page    : %s" % chemin_html)
    print("Sortie  : %s" % sortie)
    print()
    print("  %d nom(s), %d lien(s) et %d image(s) en place."
          % (compteur["noms"], compteur["liens"], compteur["images"]))

    souci = False

    # --- Lignes du tableau qui ne correspondent a aucun element -------------
    renseignees = {c for c, v in entrees.items()
                   if v["nom"] or v["lien"] or v["image"]}
    introuvables = sorted(entrees[c]["titre"] for c in (renseignees - utilisees))
    if introuvables:
        souci = True
        print()
        print("  ATTENTION — ces lignes du tableau ne correspondent a aucun")
        print("  element de la page (intitule mal orthographie ? supprime ?) :")
        for t in introuvables:
            print("    - %s" % t)

    # --- Colonnes remplies que l'element n'accepte pas ----------------------
    if ignores:
        souci = True
        print()
        print("  ATTENTION — ces valeurs ont ete ignorees :")
        for intitule, colonne, famille in ignores:
            print("    - %s : la colonne '%s' ne s'applique pas a %s"
                  % (intitule, colonne, ETIQUETTE[famille]))

    # --- Elements de la page absents du tableau ----------------------------
    orphelins = sorted(v["titre"] for c, v in vus.items() if c not in utilisees)
    if orphelins:
        print()
        print("  Elements de la page sans ligne dans le tableau")
        print("  (ils gardent ce qui est ecrit dans le HTML) :")
        for t in orphelins:
            print("    - %s" % t)

    # --- Intitules en double : le remplissage devient ambigu ---------------
    doublons = sorted((v["titre"], v["n"]) for v in vus.values() if v["n"] > 1)
    if doublons:
        souci = True
        print()
        print("  ATTENTION — ces intitules apparaissent plusieurs fois dans")
        print("  la page. Seul le premier de chaque intitule a ete rempli :")
        for t, n in doublons:
            print("    - %s  (%d fois)" % (t, n))

    print()
    if souci:
        print("Corrige les points ci-dessus, puis relance le script.")
    print("Ouvre %s, copie tout son contenu, et colle-le" % sortie.name)
    print("dans le module HTML de Confluence.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Arrive quand la sortie est envoyee dans "head" ou "more" : le
        # lecteur s'arrete avant nous. Ce n'est pas une erreur.
        sys.stderr.close()
