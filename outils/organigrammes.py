#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organigrammes.py
=============================================================================
Fabrique les deux organigrammes de l'onglet "JL Overview" a partir de deux
tableaux, et les pose directement dans la page.

  jl-organisation.csv  +  jl-programmes.csv  +  page HTML  ->  page HTML a jour

Les deux ne sont PAS dessines de la meme facon, parce qu'ils ne racontent
pas la meme chose :

  organisation   un ARBRE vertical, comme un organigramme classique. Ce qui
                 compte, c'est qui depend de qui.
  programmes     un FLUX horizontal, de gauche a droite. Ce qui compte, c'est
                 ou passe l'argent : l'epaisseur de chaque ruban est
                 proportionnelle a l'ETC, on voit donc du premier coup d'oeil
                 quel portefeuille pese, et comment il se repartit.

UTILISATION
    python3 outils/organigrammes.py

    La sortie commence par le CHEMIN DU SCRIPT et les intitules qu'il
    attend. Si ce chemin n'est pas celui du fichier ouvert dans l'editeur,
    c'est qu'une correction a ete faite dans un fichier et qu'un autre a
    ete lance : inutile de chercher plus loin.

    Ou en precisant la page :
    python3 outils/organigrammes.py ma-page.html

    Le script ecrit DANS la page (entre les reperes, voir plus bas). On peut
    le relancer autant de fois qu'on veut : il remplace a chaque fois ce
    qu'il avait ecrit la fois d'avant, jamais autre chose.

    Toujours ecrire "python" devant : sous Windows, taper un fichier .py
    tout seul ne l'execute pas, cela l'ouvre dans l'editeur associe.

OU POSER LES FICHIERS
    Peu importe. Le script fonctionne aussi bien dans l'arborescence du
    depot (blocks/, donnees/, outils/) que dans un dossier ou tout est pose
    a plat. S'il ne trouve rien, il dit ou il a cherche.

LES REPERES DANS LA PAGE
    Le script ne cherche pas a deviner ou poser les organigrammes : il
    remplace ce qui se trouve entre deux commentaires.

        <!-- ORGANIGRAMME : organisation -->
        ...tout ce qui est ici est refait a chaque passage...
        <!-- FIN ORGANIGRAMME : organisation -->

    Ne pas ecrire a la main entre ces deux lignes : le passage suivant
    effacerait le travail. Pour changer l'apparence, la feuille de style ;
    pour changer le contenu, le tableau.

LE TABLEAU DE L'ORGANISATION  (jl-organisation.csv)
    Une ligne par entite la plus fine. Les colonnes des niveaux au-dessus
    sont repetees a l'identique : c'est ce qui rattache l'entite a sa
    branche, exactement comme dans un tableau croise Excel.

    direction / acronyme                        le sommet (repete partout)
    sous-direction / acronyme sous-direction    le 2e niveau
    sous-sous-direction / acronyme ...          le 3e niveau
    place     ou se pose la sous-direction :
                  (vide)   une branche ordinaire, sous le sommet
                  support  a GAUCHE du trait, en retrait (fonction support)
                  adjoint  a DROITE du trait, en retrait
    mention   petite etiquette au-dessus du nom (exemple : Deputy)
    lien      l'adresse de la page Confluence a ouvrir

    Une entite qui n'a pas de sous-niveau : on laisse les colonnes du 3e
    niveau vides. Pour donner un lien a une sous-direction qui a des
    enfants, ajouter une ligne ou seuls les deux premiers niveaux sont
    remplis.

LE TABLEAU DES PROGRAMMES  (jl-programmes.csv)
    Meme principe, avec un montant a chaque niveau.

    Company Portfolio nv1 / ETC nv1     la boite de gauche
    Company Portfolio nv2 / ETC nv2     le 2e niveau
    Company Portfolio nv3 / ETC nv3     le 3e niveau
    Main Programs / ETC nv4             le 4e niveau
    lien      l'adresse de la page Confluence a ouvrir

    Ces intitules ne sont pas graves dans le marbre : ils sont ecrits une
    seule fois, dans le bloc ORGANIGRAMMES en tete de ce script. Les
    renommer la suffit. Casse, accents et tirets sont sans importance.

    Les ETC s'ecrivent en MILLIONS D'EUROS, en chiffres seulement : 752.
    Le script se charge de l'affichage (752 M€, 6 500 M€).

    Ici les chiffres ne servent pas qu'a etre lus : ils DESSINENT le
    diagramme. Un ETC absent ou illisible ramene le noeud a la hauteur
    minimale, et le script le signale.

L'ECHELLE DU DIAGRAMME DE FLUX
    L'epaisseur suit l'ETC, a une reserve pres : un noeud ne descend jamais
    sous un plancher de quelques pixels (reglage "plancher"). Sans lui, un
    programme a 1 M€ face a un portefeuille a 6 500 M€ ferait un trait
    invisible, impossible a survoler et impossible a lire. Les proportions
    sont donc exactes partout, sauf pour les plus petits montants, qui sont
    remontes au plancher. C'est le seul ecart, et il est volontaire.

CE QUE LE SCRIPT SIGNALE
    - un repere absent de la page                    -> ATTENTION
    - une colonne de niveau absente de l'entete      -> ATTENTION
    - une colonne que le script ne connait pas (souvent une faute de frappe)
    - un niveau vide alors qu'un niveau plus bas est rempli
    - deux sommets differents dans le meme tableau
    - un ETC manquant ou illisible dans les programmes

    Un tableau illisible n'empeche jamais l'autre d'etre refait : chaque
    organigramme est traite pour lui-meme, et celui qui echoue reste dans la
    page tel qu'il y etait.

SI UN ORGANIGRAMME NE SE FAIT PAS
    Le script dit ce qu'il a lu et ce qu'il attendait. Les trois causes qui
    reviennent, dans l'ordre :

    1. Le nom du sommet n'est rempli que sur la premiere ligne.
       Chaque ligne porte sa lignee COMPLETE, du sommet jusqu'a l'entite la
       plus fine : le nom du sommet se repete donc sur toutes les lignes.
       Ce n'est pas un titre, c'est ce qui rattache la ligne a son
       organigramme. Dans Excel : remplir la premiere cellule, puis tirer
       vers le bas.

    2. La ligne d'entete a ete modifiee.
       Les intitules sont libres de casse, d'accents et de tirets
       ("Sous-Direction", "sous direction" et "SOUS_DIRECTION" sont la meme
       colonne), mais les MOTS doivent y etre. Le script affiche l'entete
       qu'il a trouvee a cote de celle qu'il attendait : la comparaison
       saute aux yeux.

    3. Le fichier ne contient que son entete.
       Il faut au moins une ligne de donnees en dessous.

    Les colonnes facultatives (place, mention, lien) peuvent etre retirees
    sans rien casser : la fonction correspondante ne s'affiche simplement
    plus.
=============================================================================
"""

import csv
import html as html_module
import re
import sys
import difflib
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Ou sont les fichiers
# ---------------------------------------------------------------------------

DOSSIER = Path(__file__).resolve().parent        # ou vit ce script
RACINE = DOSSIER.parent                          # la racine du depot
TRAVAIL = Path.cwd()                             # d'ou la commande est lancee

# Les noms de page reconnus, dans l'ordre de preference. En ajouter un ne
# coute rien ; et de toute facon, si le dossier ne contient qu'une seule
# page .html, c'est celle-la qui est prise, quel que soit son nom.
NOMS_HTML = ("Espace JLS.html", "00-facile-a-modifier.html")
NOM_SORTIE = "page-remplie.html"

PISTES_HTML = [dossier / nom
               for nom in NOMS_HTML
               for dossier in (RACINE / "blocks",   # arborescence du depot
                               DOSSIER,             # a cote du script
                               TRAVAIL)]            # dans le dossier courant


# ---------------------------------------------------------------------------
# Les deux organigrammes
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# C'EST ICI, ET NULLE PART AILLEURS, QUE VIVENT LES NOMS DE COLONNES.
# Renommer une colonne dans Excel ? Reporter le nouvel intitule ci-dessous,
# et c'est tout : aucun autre endroit du script ne les cite.
#
# La casse, les accents, les tirets et les soulignes n'ont aucune importance
# de part et d'autre : "Compagnie Portfolio Niveau Un", "compagnie portfolio
# niveau un" et "COMPAGNIE_PORTFOLIO_NIVEAU_UN" designent la meme colonne.
# Seuls les mots comptent.
#
# Un niveau = le nom affiche, l'acronyme (facultatif) et le montant
# (facultatif). Ajouter un niveau, c'est ajouter une ligne ici et les
# colonnes correspondantes dans le tableau : le reste du script suit.
# L'ORDRE fait tout : le premier niveau est la boite du haut (ou de gauche
# pour le flux), le dernier est l'entite la plus fine.
# ---------------------------------------------------------------------------

ORGANIGRAMMES = [
    {
        "cle": "organisation",
        "csv": "jl-organisation.csv",
        "rendu": "arbre",
        "niveaux": [
            {"nom": "direction",           "acronyme": "acronyme"},
            {"nom": "sous-direction",      "acronyme": "acronyme sous-direction"},
            {"nom": "sous-sous-direction", "acronyme": "acronyme sous-sous-direction"},
        ],
        # Les colonnes attendues en plus des niveaux. Une colonne citee ici
        # et absente du tableau est signalee : c'est ce qui rattrape les
        # fautes de frappe dans la ligne d'entete.
        "extras": ["place", "mention", "lien"],
        "place": True,      # support / adjoint : le hors-hierarchie
    },
    {
        "cle": "programmes",
        "csv": "jl-programmes.csv",
        "rendu": "flux",
        "niveaux": [
            {"nom": "Company Portfolio nv1", "etc": "ETC nv1"},
            {"nom": "Company Portfolio nv2", "etc": "ETC nv2"},
            {"nom": "Company Portfolio nv3", "etc": "ETC nv3"},
            {"nom": "Main Programs",         "etc": "ETC nv4"},
        ],
        "extras": ["lien"],
        "place": False,
    },
]

PLACES = ("support", "adjoint")

# --- Reglages du diagramme de flux -----------------------------------------
# Tout le dessin decoule de ces sept valeurs. Les changer suffit a resserrer
# ou a etaler le diagramme ; il n'y a aucune coordonnee ecrite en dur plus
# bas.
FLUX = {
    "hauteur":     780,   # hauteur visee pour la colonne la plus chargee
    "colonne":     252,   # ecart entre deux colonnes, libelle compris
    "epaisseur":    13,   # largeur du rectangle d'un noeud
    "ecart":         7,   # espace vertical minimal entre deux noeuds
    "plancher":     17,   # hauteur minimale d'un noeud (voir le guide)
    "marge":        18,   # marge autour du dessin
    "marge_droite":174,   # place laissee aux libelles de la derniere colonne
    "teintes":       6,   # nombre de couleurs disponibles pour les branches
}


# ---------------------------------------------------------------------------
# Lecture des fichiers texte  (meme logique que remplir-depuis-tableau.py)
# ---------------------------------------------------------------------------

# Excel en francais enregistre par defaut en Windows-1252 : "CSV UTF-8" est
# une entree distincte du menu, souvent manquee. latin-1 en dernier ne peut
# jamais echouer, il accepte tout octet.
ENCODAGES = (("utf-8-sig", "UTF-8"),
             ("cp1252", "Windows-1252"),
             ("latin-1", "Latin-1"))

MARQUEUR_UTF8 = b"\xef\xbb\xbf"    # le "BOM" que Windows pose parfois en tete


def lire_texte(chemin):
    """Renvoie (contenu, encodage a utiliser pour reecrire, nom lisible).

    On decode les octets nous-memes plutot que de passer par read_text :
    cela evite toute traduction des fins de ligne, donc le CRLF de Windows
    ressort intact.
    """
    donnees = chemin.read_bytes()
    for encodage, etiquette in ENCODAGES:
        try:
            texte = donnees.decode(encodage)
        except UnicodeDecodeError:
            continue
        pour_reecrire = encodage
        if encodage == "utf-8-sig" and not donnees.startswith(MARQUEUR_UTF8):
            pour_reecrire = "utf-8"
        return texte, pour_reecrire, etiquette
    raise SystemExit("Impossible de lire %s : encodage non reconnu." % chemin)


def lire_tableau(chemin):
    """Renvoie (lignes, colonnes comparables, intitules tels qu'ecrits).

    Chaque ligne est un dictionnaire dont les cles sont les intitules de
    colonnes en minuscules, espaces reduits. Le separateur est detecte :
    Excel en francais enregistre avec des points-virgules, Excel en anglais
    avec des virgules.
    """
    texte, _, _ = lire_texte(chemin)
    brutes = texte.splitlines()
    if not brutes:
        raise SystemExit("Le tableau %s est vide." % chemin)

    premiere = brutes[0]
    separateur = ";" if premiere.count(";") > premiere.count(",") else ","

    lecteur = csv.DictReader(brutes, delimiter=separateur)
    entete = [c for c in (lecteur.fieldnames or []) if c is not None]
    colonnes = [nettoyer(c) for c in entete]

    lignes = []
    for brut in lecteur:
        lignes.append({nettoyer(k): (v or "").strip()
                       for k, v in brut.items() if k is not None})
    # Les intitules bruts servent au diagnostic : c'est eux que l'on relit
    # dans Excel, pas leur version normalisee.
    return lignes, colonnes, entete


def nettoyer(intitule):
    """La forme comparable d'un intitule de COLONNE.

    On ne se contente pas de la casse et des espaces surnumeraires : les
    tirets, les soulignes et les accents sont ramenes au meme rang.
    "Sous-Direction", "sous direction" et "SOUS_DIRECTION" designent donc la
    meme colonne. Personne ne devrait avoir a deviner la ponctuation exacte
    d'un intitule pour que son tableau soit lu.
    """
    texte = unicodedata.normalize("NFD", intitule or "")
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = re.sub(r"[-_/]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip().lower()


def cle_noeud(intitule):
    """La forme comparable d'un NOM d'entite.

    Volontairement moins souple que pour les colonnes : ici, deux libelles
    qui ne different que par un tiret ou un accent sont probablement deux
    entites differentes. Les confondre en fusionnerait deux branches.
    """
    return re.sub(r"\s+", " ", (intitule or "")).strip().lower()


# ---------------------------------------------------------------------------
# Construction de l'arbre
# ---------------------------------------------------------------------------

def resumer_lignes(numeros):
    """[3, 4, 5, 9] -> "3 a 5, 9".

    Une meme erreur repetee sur trente lignes ne se lit pas trente fois. On
    la dit une fois, et on donne les lignes en plages.
    """
    numeros = sorted(set(numeros))
    plages, debut, precedent = [], numeros[0], numeros[0]
    for numero in numeros[1:]:
        if numero == precedent + 1:
            precedent = numero
            continue
        plages.append((debut, precedent))
        debut = precedent = numero
    plages.append((debut, precedent))
    return ", ".join(str(a) if a == b else "%d a %d" % (a, b)
                     for a, b in plages)


def nouveau_noeud(nom, acronyme, etc):
    return {"nom": nom, "acronyme": acronyme, "etc": etc,
            "lien": "", "mention": "", "place": "",
            "enfants": [], "index": {}}


def rattacher(parent, nom, acronyme, etc):
    """Renvoie l'enfant de "parent" qui porte ce nom, en le creant au besoin.

    L'index rend la recherche immediate, et l'ordre d'apparition dans le
    tableau est conserve : ce qu'on lit dans Excel de haut en bas se
    retrouve de haut en bas sur la page.
    """
    cle = cle_noeud(nom) + "|" + cle_noeud(acronyme)
    if cle in parent["index"]:
        noeud = parent["index"][cle]
        if etc and not noeud["etc"]:
            noeud["etc"] = etc
        return noeud
    noeud = nouveau_noeud(nom, acronyme, etc)
    parent["index"][cle] = noeud
    parent["enfants"].append(noeud)
    return noeud


def construire_arbre(lignes, config, alertes):
    """Transforme les lignes du tableau en un arbre de noeuds.

    Chaque ligne decrit un chemin complet du sommet jusqu'a l'entite la plus
    fine. Les lignes qui partagent un debut de chemin partagent les memes
    noeuds : c'est ainsi qu'une sous-direction citee dix fois n'apparait
    qu'une seule fois sur la page.
    """
    niveaux = config["niveaux"]
    faux_parent = nouveau_noeud("", "", "")
    trous = {}      # colonne vide -> numeros de lignes concernees
    places = {}     # valeur inconnue -> numeros de lignes concernees

    for numero, ligne in enumerate(lignes, start=2):   # 2 : l'entete est en 1
        chaine = []
        parent = faux_parent
        arrete = False

        for rang, niveau in enumerate(niveaux):
            nom = ligne.get(nettoyer(niveau["nom"]), "")
            acronyme = ligne.get(nettoyer(niveau.get("acronyme", "")), "")
            etc = ligne.get(nettoyer(niveau.get("etc", "")), "")

            if not nom and not acronyme:
                arrete = True
                continue

            if arrete:
                # Un trou dans le chemin : impossible de savoir a quoi
                # rattacher cette entite. On le note plutot que de la poser
                # au hasard -- et on regroupe, car la meme maladresse se
                # repete en general sur tout le fichier.
                trous.setdefault(niveaux[rang - 1]["nom"], []).append(numero)
                break

            parent = rattacher(parent, nom, acronyme, etc)
            chaine.append(parent)

        if not chaine:
            continue    # ligne vide : Excel en laisse souvent en fin de fichier

        # --- Les colonnes qui ne decrivent pas un niveau ------------------
        # Elles se rapportent a l'entite la plus fine de la ligne : c'est
        # celle que la ligne decrit vraiment.
        feuille = chaine[-1]
        for colonne in ("lien", "mention"):
            valeur = ligne.get(colonne, "")
            if valeur and not feuille[colonne]:
                feuille[colonne] = valeur

        # "place" fait exception : elle dit ou se pose la BRANCHE, donc elle
        # se rapporte toujours au 2e niveau, quelle que soit la finesse de
        # la ligne.
        if config["place"] and len(chaine) > 1:
            place = nettoyer(ligne.get("place", ""))
            if place and not chaine[1]["place"]:
                if place in PLACES:
                    chaine[1]["place"] = place
                else:
                    places.setdefault(ligne.get("place", ""), []).append(numero)

    for colonne, numeros in trous.items():
        alertes.append(
            '%d ligne(s) ne sont rattachees a rien : la colonne "%s" y est '
            "vide alors qu'une colonne plus a droite est remplie.\n"
            "  Lignes concernees : %s\n"
            "  -> chaque ligne porte sa lignee COMPLETE, du sommet jusqu'a "
            "l'entite la plus fine. Le nom du niveau du dessus se repete "
            "donc sur CHAQUE ligne : ce n'est pas un titre a poser une "
            "seule fois en haut de la colonne."
            % (len(numeros), colonne, resumer_lignes(numeros)))

    for valeur, numeros in places.items():
        alertes.append(
            'place = "%s" inconnue (attendu : %s, ou rien du tout).\n'
            "  Lignes concernees : %s"
            % (valeur, " ou ".join(PLACES), resumer_lignes(numeros)))

    # Un tableau qui ne donne rien n'est pas une raison d'abandonner : les
    # AUTRES organigrammes, eux, sont peut-etre parfaitement lisibles. On
    # rend None, l'appelant expliquera et passera a la suite.
    if not faux_parent["enfants"]:
        return None

    if len(faux_parent["enfants"]) > 1:
        autres = ", ".join(n["nom"] for n in faux_parent["enfants"][1:])
        alertes.append(
            "plusieurs sommets differents dans le tableau (%s). Seul le "
            "premier est affiche : verifie l'orthographe de la colonne "
            "\"%s\"." % (autres, niveaux[0]["nom"]))

    return faux_parent["enfants"][0]


def colonnes_attendues(config):
    """Tous les intitules que le script sait exploiter, forme comparable."""
    attendues = []
    for niveau in config["niveaux"]:
        for role in ("nom", "acronyme", "etc"):
            if niveau.get(role):
                attendues.append(nettoyer(niveau[role]))
    return attendues + [nettoyer(c) for c in config["extras"]]


def controler_colonnes(config, colonnes, entete):
    """Renvoie (colonnes de niveau manquantes, colonnes inconnues).

    Deux controles, et deux seulement :

    - une colonne de NIVEAU absente est un vrai probleme : sans elle, tout
      un etage de l'organigramme disparait.
    - une colonne que le script ne connait pas est signalee sans drame :
      neuf fois sur dix c'est une faute de frappe dans l'entete (lein pour
      lien), une fois sur dix c'est une note personnelle, et le script la
      laisse tranquille.

    Les colonnes facultatives absentes ne sont PAS signalees : retirer
    "mention" parce qu'on n'a pas de Deputy a afficher est un choix
    legitime, pas une erreur.
    """
    manquantes = ['colonne de niveau "%s" absente de l\'entete.' % n["nom"]
                  for n in config["niveaux"]
                  if nettoyer(n["nom"]) not in colonnes]

    connues = colonnes_attendues(config)
    inconnues = [brut for brut, propre in zip(entete, colonnes)
                 if propre not in connues and propre]
    if inconnues:
        inconnues = ['colonne(s) non utilisee(s) par le script : %s.\n'
                     '  Si c\'est une faute de frappe dans l\'entete, la '
                     'corriger ; sinon, rien a faire.'
                     % ", ".join('"%s"' % c for c in inconnues)]
    return manquantes, inconnues


def plus_proche(attendu, entete):
    """L'intitule du fichier qui ressemble le plus a celui qu'on cherchait.

    Une faute de frappe dans une entete se voit mal a l'oeil quand la ligne
    fait quatre-vingts caracteres. Autant la montrer du doigt.
    """
    candidats = {nettoyer(c): c for c in entete}
    trouve = difflib.get_close_matches(nettoyer(attendu), list(candidats),
                                       n=1, cutoff=.6)
    return candidats[trouve[0]] if trouve else ""


def diagnostic_vide(config, lignes, entete):
    """Explique pourquoi un tableau n'a donne aucune boite.

    "Aucune donnee exploitable" tout court n'aide personne : il faut dire ce
    qui a ete lu, ce qui etait attendu, et ou regarder.
    """
    sommet = config["niveaux"][0]["nom"]
    propres = [nettoyer(c) for c in entete]

    detail = [
        "aucune boite n'a pu etre construite.",
        "  %d ligne(s) lue(s) apres l'entete." % len(lignes),
        '  Colonne du sommet attendue : "%s"' % sommet,
        "  Entete trouvee dans le fichier : %s"
        % (", ".join('"%s"' % c for c in entete) if entete else "vide"),
    ]

    if nettoyer(sommet) not in propres:
        detail.append(
            '  -> cette colonne manque. Verifie la PREMIERE ligne du '
            'fichier : elle doit porter les intitules %s.'
            % ", ".join('"%s"' % n["nom"] for n in config["niveaux"]))
        proche = plus_proche(sommet, entete)
        if proche:
            detail.append('     Le plus ressemblant dans ton fichier : "%s". '
                          "Est-ce celle-la ?" % proche)
        detail.append(
            "     Si tes colonnes portent volontairement d'autres noms, ce "
            "n'est pas le fichier qu'il faut changer mais le bloc "
            "ORGANIGRAMMES, en tete de ce script : les intitules attendus "
            "s'y trouvent, et nulle part ailleurs.")
    elif not lignes:
        detail.append(
            "  -> le fichier ne contient que son entete. Il faut au moins "
            "une ligne de donnees en dessous.")
    else:
        detail.append(
            '  -> la colonne existe mais elle est vide sur toutes les '
            'lignes. Le nom du sommet se repete sur CHAQUE ligne : ce '
            'n\'est pas un titre a mettre une fois en haut, c\'est ce qui '
            'rattache chaque ligne au meme organigramme.')

    detail.append("  Cet organigramme n'a pas ete refait : ce qui etait "
                  "dans la page reste en place.")
    return "\n".join(detail)


# ---------------------------------------------------------------------------
# Les montants
# ---------------------------------------------------------------------------

def nombre(valeur):
    """La valeur numerique d'une cellule d'ETC, ou None si ce n'en est pas une.

    L'espace insecable vient d'Excel, la virgule est la decimale francaise.
    """
    brut = (valeur or "").strip()
    if not brut:
        return None
    essai = brut.replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return abs(float(essai))
    except ValueError:
        return None


def montant(valeur):
    """"752" -> "752 M€".  "6500" -> "6 500 M€".

    Une valeur qui n'est pas un nombre ressort telle quelle : le tableau
    peut ainsi contenir "a consolider" sans que le script s'y oppose.
    """
    brut = (valeur or "").strip()
    if not brut:
        return ""
    valeur_lue = nombre(brut)
    if valeur_lue is None:
        return brut

    if valeur_lue == int(valeur_lue):
        chiffres = "{:,}".format(int(valeur_lue)).replace(",", " ")
    else:
        chiffres = "{:,.1f}".format(valeur_lue).replace(",", " ").replace(".", ",")
    return chiffres + " M€"


# ---------------------------------------------------------------------------
# Ecriture du HTML
# ---------------------------------------------------------------------------

def echapper(texte):
    """Empeche qu'un nom contenant < > & ne casse la page."""
    return (texte.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def attribut(valeur):
    """Prepare une adresse pour tenir dans un href="...".

    Le passage par unescape avant escape rend l'operation sure quelle que
    soit la forme collee depuis le navigateur : une adresse contenant deja
    "&amp;" ne devient pas "&amp;amp;".
    """
    return html_module.escape(html_module.unescape(valeur), quote=True)


# Valeurs qui ne sont pas de vraies adresses mais des marqueurs "a remplir".
REMPLIR_PLUS_TARD = {"REMPLACE_PAR_LE_LIEN", "ADRESSE_DE_LA_PAGE", "#", ""}


def lien_de(noeud):
    """L'adresse du noeud, ou la chaine vide si elle reste a renseigner."""
    lien = html_module.unescape(noeud["lien"].strip())
    return "" if lien in REMPLIR_PLUS_TARD else lien


def intitule(noeud):
    """Ce qu'on lit sur la boite : l'acronyme s'il existe, sinon le nom."""
    return noeud["acronyme"] or noeud["nom"]


# ===========================================================================
# RENDU 1 : L'ARBRE  (organigramme de l'organisation)
# ===========================================================================

def rendu_noeud(noeud, rang, marge):
    """Une boite de l'arbre.

    Avec un lien c'est un <a>, sans lien un <div> : une boite sur laquelle
    il n'y a rien a cliquer ne doit pas se comporter comme un lien.
    """
    classes = "orga-noeud orga-noeud-%d" % rang
    lien = lien_de(noeud)

    if lien:
        ouvrante = '<a class="%s" href="%s">' % (classes, attribut(lien))
        fermante = "</a>"
    else:
        ouvrante = '<div class="%s">' % classes
        fermante = "</div>"

    dedans = []
    if noeud["mention"]:
        dedans.append('<span class="orga-mention">%s</span>'
                      % echapper(noeud["mention"]))
    if noeud["acronyme"]:
        dedans.append('<span class="orga-acronyme">%s</span>'
                      % echapper(noeud["acronyme"]))
    if noeud["nom"]:
        dedans.append('<span class="orga-nom">%s</span>' % echapper(noeud["nom"]))
    somme = montant(noeud["etc"])
    if somme:
        dedans.append('<span class="orga-etc">ETC&nbsp;: %s</span>'
                      % echapper(somme))

    lignes = [marge + ouvrante]
    lignes += [marge + "  " + d for d in dedans]
    lignes.append(marge + fermante)
    return lignes


def rendu_enfants(noeuds, rang, marge):
    """La colonne d'entites accrochee sous une boite, avec son filet vertical.

    Se rappelle elle-meme : un enfant qui a lui-meme des enfants est rendu
    exactement de la meme facon, quel que soit le nombre de niveaux.
    """
    if not noeuds:
        return []
    lignes = [marge + '<div class="orga-enfants">']
    for noeud in noeuds:
        lignes.append(marge + '  <div class="orga-enfant">')
        # La boite est enfermee dans une "tige" : l'encoche horizontale vise
        # ainsi le milieu de la BOITE, et non le milieu de tout ce qui pend
        # en dessous d'elle.
        lignes.append(marge + '    <div class="orga-tige">')
        lignes += rendu_noeud(noeud, rang, marge + "      ")
        lignes.append(marge + "    </div>")
        lignes += rendu_enfants(noeud["enfants"], rang + 1, marge + "    ")
        lignes.append(marge + "  </div>")
    lignes.append(marge + "</div>")
    return lignes


def rendu_arbre(racine, marge, alertes):
    """L'organigramme en arbre, du sommet vers le bas."""
    # Le hors-hierarchie (support a gauche, adjoint a droite) est retire des
    # branches : il se pose de part et d'autre du trait, pas dans la rangee.
    branches = [n for n in racine["enfants"] if not n["place"]]
    cotes = {p: [n for n in racine["enfants"] if n["place"] == p] for p in PLACES}

    lignes = [marge + '<div class="organigramme" style="--branches: %d;">'
              % max(len(branches), 1)]
    m1 = marge + "  "

    lignes.append(m1 + '<div class="orga-sommet">')
    lignes += rendu_noeud(racine, 1, m1 + "  ")
    lignes.append(m1 + "</div>")

    if cotes["support"] or cotes["adjoint"]:
        lignes.append(m1 + '<div class="orga-adjoints">')
        for place in PLACES:
            lignes.append(m1 + '  <div class="orga-cote orga-cote-%s">' % place)
            for noeud in cotes[place]:
                lignes.append(m1 + '    <div class="orga-adjoint">')
                lignes += rendu_noeud(noeud, 2, m1 + "      ")
                lignes += rendu_enfants(noeud["enfants"], 3, m1 + "      ")
                lignes.append(m1 + "    </div>")
            lignes.append(m1 + "  </div>")
        lignes.append(m1 + "</div>")

    lignes.append(m1 + '<div class="orga-branches">')
    for noeud in branches:
        lignes.append(m1 + '  <div class="orga-branche">')
        lignes += rendu_noeud(noeud, 2, m1 + "    ")
        lignes += rendu_enfants(noeud["enfants"], 3, m1 + "    ")
        lignes.append(m1 + "  </div>")
    lignes.append(m1 + "</div>")

    lignes.append(marge + "</div>")
    return lignes


# ===========================================================================
# RENDU 2 : LE FLUX  (organigramme des programmes)
# ===========================================================================
#
# Le principe, en trois temps :
#
#   1. RANGER      chaque noeud rejoint la colonne de son niveau, dans
#                  l'ordre du tableau. Les freres restent groupes : c'est ce
#                  qui suffit a ce qu'aucun ruban n'en croise un autre.
#   2. MESURER     une echelle unique, en pixels par million d'euros, telle
#                  que la colonne la plus chargee remplisse exactement la
#                  hauteur voulue. On la cherche par dichotomie plutot que
#                  par une division : le plancher rend le calcul direct
#                  impossible, mais la hauteur d'une colonne ne fait que
#                  croitre avec l'echelle, donc la dichotomie tombe juste.
#   3. PLACER      les enfants se centrent sur leur parent, puis une passe
#                  de degagement ecarte ce qui se chevauche encore.
#
# Le dessin lui-meme est un SVG ecrit a la main : rien a heberger, rien que
# Confluence puisse bloquer, et le texte reste du vrai texte (donc
# selectionnable et cherchable).

def ranger_colonnes(racine):
    """Les noeuds regroupes par niveau, dans l'ordre du tableau."""
    colonnes = []

    def parcourir(noeud, profondeur):
        while len(colonnes) <= profondeur:
            colonnes.append([])
        colonnes[profondeur].append(noeud)
        for enfant in noeud["enfants"]:
            parcourir(enfant, profondeur + 1)

    parcourir(racine, 0)
    return colonnes


def hauteur_colonne(colonne, echelle):
    ecart, plancher = FLUX["ecart"], FLUX["plancher"]
    total = sum(max(plancher, n["_valeur"] * echelle) for n in colonne)
    return total + ecart * (len(colonne) - 1)


def chercher_echelle(colonnes):
    """Les pixels par million d'euros.

    Dichotomie : on encadre la reponse, puis on resserre. Quarante tours
    suffisent largement -- l'intervalle est divise par deux a chaque fois.
    """
    vise = FLUX["hauteur"]

    def trop_haut(echelle):
        return max(hauteur_colonne(c, echelle) for c in colonnes) >= vise

    if trop_haut(0.0):
        # Deja trop haut sans aucun montant : il y a tant de noeuds que les
        # planchers a eux seuls remplissent la colonne. Tout au plancher.
        return 0.0

    bas, haut = 0.0, 1.0
    while not trop_haut(haut) and haut < 1e6:
        haut *= 2
    for _ in range(40):
        milieu = (bas + haut) / 2
        if trop_haut(milieu):
            haut = milieu
        else:
            bas = milieu
    return bas


def degager(colonne):
    """Ecarte les noeuds d'une colonne qui se chevauchent encore.

    Deux passes : la premiere pousse vers le bas ce qui se marche dessus,
    la seconde remonte l'ensemble s'il a fini par deborder. L'ordre des
    noeuds n'est jamais modifie -- c'est lui qui garantit que les rubans ne
    se croisent pas.
    """
    ecart, vise = FLUX["ecart"], FLUX["hauteur"]

    bas = -1e9
    for noeud in colonne:
        if noeud["_y"] < bas:
            noeud["_y"] = bas
        bas = noeud["_y"] + noeud["_h"] + ecart

    debord = (bas - ecart) - vise
    if debord > 0:
        haut = vise
        for noeud in reversed(colonne):
            if noeud["_y"] + noeud["_h"] > haut:
                noeud["_y"] = haut - noeud["_h"]
            haut = noeud["_y"] - ecart


def disposer_flux(racine, alertes):
    """Donne a chaque noeud sa position et sa taille. Renvoie les colonnes."""
    colonnes = ranger_colonnes(racine)

    sans_etc = []
    for colonne in colonnes:
        for noeud in colonne:
            valeur = nombre(noeud["etc"])
            if valeur is None:
                sans_etc.append(intitule(noeud) or noeud["nom"])
                valeur = 0.0
            noeud["_valeur"] = valeur

    if sans_etc:
        alertes.append(
            "%d noeud(s) sans ETC exploitable, ramene(s) a la hauteur "
            "minimale : %s%s"
            % (len(sans_etc), ", ".join(sans_etc[:4]),
               ", ..." if len(sans_etc) > 4 else ""))

    echelle = chercher_echelle(colonnes)
    for colonne in colonnes:
        for noeud in colonne:
            noeud["_h"] = max(FLUX["plancher"], noeud["_valeur"] * echelle)

    # --- Le sommet, puis chaque colonne a partir de la precedente ----------
    racine["_y"] = (FLUX["hauteur"] - racine["_h"]) / 2

    for rang in range(1, len(colonnes)):
        for parent in colonnes[rang - 1]:
            enfants = parent["enfants"]
            if not enfants:
                continue
            total = (sum(e["_h"] for e in enfants)
                     + FLUX["ecart"] * (len(enfants) - 1))
            y = parent["_y"] + (parent["_h"] - total) / 2
            for enfant in enfants:
                enfant["_y"] = y
                y += enfant["_h"] + FLUX["ecart"]
        degager(colonnes[rang])

    # --- Les points de depart des rubans, chez le parent -------------------
    # Ils se touchent, sans espace : c'est ce qui fait lire la boite du
    # parent comme la somme de ce qui en sort.
    for colonne in colonnes:
        for parent in colonne:
            depart = (parent["_y"]
                      + (parent["_h"] - sum(e["_h"] for e in parent["enfants"])) / 2)
            for enfant in parent["enfants"]:
                enfant["_depart"] = depart
                depart += enfant["_h"]

    # --- Les couleurs : une par branche de premier niveau ------------------
    for rang, branche in enumerate(racine["enfants"]):
        teinte = rang % FLUX["teintes"] + 1

        def teinter(noeud, teinte=teinte):
            noeud["_teinte"] = teinte
            for enfant in noeud["enfants"]:
                teinter(enfant)

        teinter(branche)
    racine["_teinte"] = 0

    # --- Tout ramener dans le cadre ---------------------------------------
    # Le degagement a pu faire depasser vers le haut ; on redescend
    # l'ensemble d'un bloc plutot que de tronquer.
    tous = [n for colonne in colonnes for n in colonne]
    decalage = FLUX["marge"] - min(n["_y"] for n in tous)
    for noeud in tous:
        noeud["_y"] += decalage
        if "_depart" in noeud:
            noeud["_depart"] += decalage

    return colonnes


def abscisse(rang):
    return FLUX["marge"] + rang * FLUX["colonne"]


def arrondir(valeur):
    """Un chiffre apres la virgule suffit, et le fichier reste lisible."""
    return ("%.1f" % valeur).rstrip("0").rstrip(".")


def ruban(x0, y0, x1, y1, epaisseur):
    """Le chemin d'un ruban : deux courbes qui se rejoignent.

    Les poignees des courbes sont posees a mi-chemin en abscisse. C'est ce
    qui donne le depart et l'arrivee horizontaux, et donc le raccord net
    contre les boites.
    """
    milieu = (x0 + x1) / 2
    a, b = y0 + epaisseur, y1 + epaisseur
    r = arrondir
    return ("M%s,%s C%s,%s %s,%s %s,%s L%s,%s C%s,%s %s,%s %s,%s Z"
            % (r(x0), r(y0), r(milieu), r(y0), r(milieu), r(y1), r(x1), r(y1),
               r(x1), r(b), r(milieu), r(b), r(milieu), r(a), r(x0), r(a)))


def raccourcir(texte, limite):
    return texte if len(texte) <= limite else texte[:limite - 1].rstrip() + "…"


def rendu_libelle(noeud, x, marge):
    """Le texte pose a droite d'une boite.

    Trois formes selon la place disponible : deux lignes quand la boite est
    haute, une seule ligne quand elle est courte, et rien du tout quand elle
    est minuscule -- l'infobulle prend alors le relais. Ecrire un libelle
    qui chevauche son voisin serait pire que de ne pas l'ecrire.
    """
    milieu = noeud["_y"] + noeud["_h"] / 2
    nom = echapper(raccourcir(noeud["nom"] or noeud["acronyme"], 30))
    somme = montant(noeud["etc"])
    r = arrondir

    if noeud["_h"] >= 30:
        lignes = [
            '%s<text class="flux-nom" x="%s" y="%s">%s</text>'
            % (marge, r(x), r(milieu - 2), nom)]
        if somme:
            lignes.append(
                '%s<text class="flux-etc" x="%s" y="%s">%s</text>'
                % (marge, r(x), r(milieu + 12), echapper(somme)))
        return lignes

    if noeud["_h"] >= 13:
        texte = nom + ("  ·  " + somme if somme else "")
        return ['%s<text class="flux-nom flux-nom-court" x="%s" y="%s">%s</text>'
                % (marge, r(x), r(milieu + 4), echapper(texte))]

    return []


def rendu_flux(racine, marge, alertes):
    """Le diagramme de flux, de gauche a droite."""
    colonnes = disposer_flux(racine, alertes)

    largeur = (abscisse(len(colonnes) - 1) + FLUX["epaisseur"]
               + FLUX["marge_droite"])
    hauteur = (max(n["_y"] + n["_h"] for colonne in colonnes for n in colonne)
               + FLUX["marge"])
    r = arrondir

    m1 = marge + "  "
    m2 = marge + "    "

    lignes = [
        # tabindex : le cadre se prend au clavier, et les fleches le font
        # alors defiler comme n'importe quelle zone deroulante.
        marge + '<div class="flux-cadre" data-deplacable="oui" tabindex="0" '
                'role="group" aria-label="Diagramme de repartition de l\'ETC">',
        m1 + '<svg class="flux" role="img" viewBox="0 0 %s %s" '
             'width="%s" height="%s" aria-label="Repartition de l\'ETC, '
             'du sommet vers les projets">' % (r(largeur), r(hauteur),
                                               r(largeur), r(hauteur)),
    ]

    # --- Les rubans d'abord : ils passent SOUS les boites et les libelles --
    lignes.append(m2 + '<g class="flux-liens">')
    for rang, colonne in enumerate(colonnes[:-1]):
        x0 = abscisse(rang) + FLUX["epaisseur"]
        x1 = abscisse(rang + 1)
        for parent in colonne:
            for enfant in parent["enfants"]:
                somme = montant(enfant["etc"])
                lignes.append(
                    m2 + '  <path class="flux-lien flux-teinte-%d" d="%s">'
                         '<title>%s%s</title></path>'
                    % (enfant["_teinte"],
                       ruban(x0, enfant["_depart"], x1, enfant["_y"], enfant["_h"]),
                       echapper(enfant["nom"] or enfant["acronyme"]),
                       echapper("  ·  " + somme if somme else "")))
    lignes.append(m2 + "</g>")

    # --- Puis les boites et leurs libelles ---------------------------------
    lignes.append(m2 + '<g class="flux-noeuds">')
    for rang, colonne in enumerate(colonnes):
        x = abscisse(rang)
        for noeud in colonne:
            classes = "flux-noeud flux-teinte-%d" % noeud["_teinte"]
            if rang == 0:
                classes += " flux-noeud-sommet"
            somme = montant(noeud["etc"])
            lien = lien_de(noeud)

            lignes.append(m2 + '  <g class="flux-boite">')
            if lien:
                lignes.append(m2 + '    <a href="%s">' % attribut(lien))
            dedans = m2 + ("      " if lien else "    ")

            lignes.append(
                dedans + '<rect class="%s" x="%s" y="%s" width="%s" '
                         'height="%s" rx="3"><title>%s%s</title></rect>'
                % (classes, r(x), r(noeud["_y"]), FLUX["epaisseur"],
                   r(noeud["_h"]),
                   echapper(noeud["nom"] or noeud["acronyme"]),
                   echapper("  ·  " + somme if somme else "")))
            lignes += rendu_libelle(noeud, x + FLUX["epaisseur"] + 8, dedans)

            if lien:
                lignes.append(m2 + "    </a>")
            lignes.append(m2 + "  </g>")
    lignes.append(m2 + "</g>")

    lignes.append(m1 + "</svg>")
    lignes.append(marge + "</div>")
    return lignes


# ---------------------------------------------------------------------------

RENDUS = {"arbre": rendu_arbre, "flux": rendu_flux}


def compter(noeud):
    """Le nombre de boites, niveau par niveau. Sert au compte rendu."""
    par_rang = {}

    def parcourir(n, rang):
        par_rang[rang] = par_rang.get(rang, 0) + 1
        for enfant in n["enfants"]:
            parcourir(enfant, rang + 1)

    parcourir(noeud, 1)
    return [par_rang[r] for r in sorted(par_rang)]


# ---------------------------------------------------------------------------
# Pose dans la page
# ---------------------------------------------------------------------------

def motif_repere(cle):
    return re.compile(
        r'([ \t]*)(<!--\s*ORGANIGRAMME\s*:\s*%s\s*-->)(.*?)'
        r'([ \t]*)(<!--\s*FIN\s+ORGANIGRAMME\s*:\s*%s\s*-->)'
        % (re.escape(cle), re.escape(cle)), re.S | re.I)


def injecter(html, cle, fabriquer):
    """Remplace ce qui se trouve entre les deux reperes.

    L'indentation du repere d'ouverture est reprise pour le contenu : le
    fichier reste lisible quand on l'ouvre a la main.
    """
    motif = motif_repere(cle)
    trouve = motif.search(html)
    if not trouve:
        return html, False

    marge = trouve.group(1)
    corps = "\n".join(fabriquer(marge))
    nouveau = "%s%s\n%s\n%s%s" % (marge, trouve.group(2), corps,
                                  trouve.group(4), trouve.group(5))
    return html[:trouve.start()] + nouveau + html[trouve.end():], True


# ---------------------------------------------------------------------------

def chercher_page(arguments):
    if arguments:
        page = Path(arguments[0])
        if not page.exists():
            raise SystemExit("Fichier introuvable : %s" % page)
        return page

    for piste in PISTES_HTML:
        if piste.exists():
            return piste

    for dossier in (DOSSIER, TRAVAIL):
        candidats = sorted(p for p in dossier.glob("*.html")
                           if p.name.lower() != NOM_SORTIE)
        if len(candidats) == 1:
            return candidats[0]

    raise SystemExit(introuvable("la page HTML", PISTES_HTML))


def chercher_tableau(page, nom):
    """Le tableau est cherche pres de la page d'abord : dans le depot il vit
    dans donnees/, ailleurs il est pose a cote du reste."""
    pistes = [RACINE / "donnees" / nom,
              page.parent / nom,
              page.parent.parent / "donnees" / nom,
              DOSSIER / nom,
              TRAVAIL / nom]
    for piste in pistes:
        if piste.exists():
            return piste
    raise SystemExit(introuvable("le tableau %s" % nom, pistes))


def introuvable(quoi, pistes):
    """Message d'erreur qui dit OU le script a cherche, pas seulement qu'il
    n'a pas trouve : c'est ce qui permet de corriger sans deviner."""
    vues, uniques = set(), []
    for chemin in pistes:
        if str(chemin) not in vues:
            vues.add(str(chemin))
            uniques.append(chemin)

    lignes = ["Impossible de trouver %s." % quoi, "", "Cherche ici :"]
    lignes += ["    %s" % p for p in uniques]
    lignes += ["", "Indique la page directement :",
               "    python %s chemin\\vers\\ma-page.html"
               % Path(sys.argv[0]).name]
    return "\n".join(lignes)


def main():
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(sys.argv[1:]) != len(arguments):
        raise SystemExit("Ce script n'a pas d'option. Donne au plus le "
                         "chemin de la page.")

    page = chercher_page(arguments)
    html, encodage_page, _ = lire_texte(page)
    crlf = "\r\n" in html

    # Le chemin du script AVANT tout le reste. Editer un fichier et en
    # lancer un autre est l'erreur la plus couteuse qui soit : on cherche
    # pendant une heure une correction qui, en realite, n'a jamais tourne.
    # La premiere ligne de la sortie tranche la question.
    print("Script : %s" % Path(__file__).resolve())
    print("Page   : %s" % page)
    for config in ORGANIGRAMMES:
        print("  %-14s attend : %s"
              % (config["cle"],
                 ", ".join('"%s"' % n["nom"] for n in config["niveaux"])))
    print()

    alertes = []
    poses = 0
    for config in ORGANIGRAMMES:
        chemin = chercher_tableau(page, config["csv"])
        lignes, colonnes, entete = lire_tableau(chemin)

        manquantes, inconnues = controler_colonnes(config, colonnes, entete)
        soucis = list(inconnues)
        racine = construire_arbre(lignes, config, soucis)

        etat = "-"
        if racine is None:
            # Inutile d'egrener les colonnes manquantes : le diagnostic qui
            # suit redonne l'entete attendue en entier.
            # Un tableau illisible n'empeche pas les autres d'etre refaits :
            # on laisse simplement CET organigramme tel qu'il est dans la
            # page, et on dit pourquoi.
            soucis.append(diagnostic_vide(config, lignes, entete))
        else:
            soucis = manquantes + soucis
            dessiner = RENDUS[config["rendu"]]
            html, pose = injecter(
                html, config["cle"],
                lambda marge, r=racine, s=soucis: dessiner(r, marge, s))
            if pose:
                poses += 1
                etat = "  ->  ".join(
                    "%d au niveau %d" % (n, i + 1)
                    for i, n in enumerate(compter(racine)))
            else:
                soucis.append(
                    'repere "<!-- ORGANIGRAMME : %s -->" introuvable dans '
                    "la page : cet organigramme n'a pas ete pose."
                    % config["cle"])

        print("  %-14s %-7s %s"
              % (config["cle"], "(%s)" % config["rendu"], etat))
        print("  %-14s %-7s tableau : %s" % ("", "", chemin))
        alertes += ["%s : %s" % (config["csv"], s) for s in soucis]
        print()

    if crlf:
        # La page vient de Windows : on lui rend ses fins de ligne.
        html = html.replace("\r\n", "\n").replace("\n", "\r\n")

    with open(page, "w", encoding=encodage_page, newline="") as f:
        f.write(html)

    if alertes:
        print("  ATTENTION :")
        for alerte in alertes:
            morceaux = alerte.split("\n")
            print("    - %s" % morceaux[0])
            for suite in morceaux[1:]:
                print("    %s" % suite)
        print()

    if poses:
        print("Page mise a jour. Pour produire le fichier a coller dans")
        print("Confluence :  python %s"
              % (Path("outils") / "remplir-depuis-tableau.py"))
    else:
        print("Aucun organigramme n'a pu etre refait : la page est")
        print("inchangee. Corrige les points ci-dessus et relance.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Arrive quand la sortie est envoyee dans "head" ou "more" : le
        # lecteur s'arrete avant nous. Ce n'est pas une erreur.
        sys.stderr.close()
