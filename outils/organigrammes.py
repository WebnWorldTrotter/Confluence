#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organigrammes.py
=============================================================================
Fabrique les deux organigrammes de l'onglet "JL Overview" a partir de deux
tableaux, et les pose directement dans la page.

  jl-organisation.csv  +  jl-programmes.csv  +  page HTML  ->  page HTML a jour

UTILISATION
    python3 outils/organigrammes.py

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

    racine / etc racine                         le sommet
    portefeuille nv1 / etc nv1                  le portefeuille
    programme nv2 / etc nv2                     le programme
    projet nv3 / etc nv3                        le projet
    revue     encadre le noeud en pointilles et l'ajoute a la legende
              (exemple : PMO/MPR reviews, MBR reviews)
    lien      l'adresse de la page Confluence a ouvrir

    Les ETC s'ecrivent en MILLIONS D'EUROS, en chiffres seulement : 752.
    Le script se charge de l'affichage (752 M€, 6 500 M€). Une valeur qui
    n'est pas un nombre est affichee telle quelle : on peut donc ecrire
    "9 G€" ou "a consolider" si besoin.

CE QUE LE SCRIPT SIGNALE
    - un repere absent de la page                    -> ATTENTION
    - une colonne attendue absente du tableau        -> ATTENTION
    - un niveau vide alors qu'un niveau plus bas est rempli
    - deux sommets differents dans le meme tableau
=============================================================================
"""

import csv
import html as html_module
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ou sont les fichiers
# ---------------------------------------------------------------------------

DOSSIER = Path(__file__).resolve().parent        # ou vit ce script
RACINE = DOSSIER.parent                          # la racine du depot
TRAVAIL = Path.cwd()                             # d'ou la commande est lancee

NOM_HTML = "00-facile-a-modifier.html"
NOM_SORTIE = "page-remplie.html"

PISTES_HTML = [
    RACINE / "blocks" / NOM_HTML,     # arborescence du depot
    DOSSIER / NOM_HTML,               # a cote du script
    TRAVAIL / NOM_HTML,               # dans le dossier courant
]


# ---------------------------------------------------------------------------
# Les deux organigrammes
# ---------------------------------------------------------------------------
# Un niveau = le nom affiche, l'acronyme (facultatif) et le montant
# (facultatif). Ajouter un niveau, c'est ajouter une ligne ici et les
# colonnes correspondantes dans le tableau : le reste du script suit.

ORGANIGRAMMES = [
    {
        "cle": "organisation",
        "csv": "jl-organisation.csv",
        "niveaux": [
            {"nom": "direction",           "acronyme": "acronyme"},
            {"nom": "sous-direction",      "acronyme": "acronyme sous-direction"},
            {"nom": "sous-sous-direction", "acronyme": "acronyme sous-sous-direction"},
        ],
        # Les colonnes qui ne decrivent pas un niveau.
        # Les colonnes attendues en plus des niveaux. Une colonne citee ici
        # et absente du tableau est signalee : c'est ce qui rattrape les
        # fautes de frappe dans la ligne d'entete.
        "extras": ["place", "mention", "lien"],
        "place": True,      # support / adjoint : le hors-hierarchie
        "legende": False,   # pas de revues dans cet organigramme
    },
    {
        "cle": "programmes",
        "csv": "jl-programmes.csv",
        "niveaux": [
            {"nom": "racine",           "etc": "etc racine"},
            {"nom": "portefeuille nv1", "etc": "etc nv1"},
            {"nom": "programme nv2",    "etc": "etc nv2"},
            {"nom": "projet nv3",       "etc": "etc nv3"},
        ],
        "extras": ["revue", "lien"],
        "place": False,
        "legende": True,
    },
]

PLACES = ("support", "adjoint")


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
    """Renvoie (liste de lignes, liste des colonnes trouvees).

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
    colonnes = [nettoyer(c) for c in (lecteur.fieldnames or [])]

    lignes = []
    for brut in lecteur:
        lignes.append({nettoyer(k): (v or "").strip()
                       for k, v in brut.items() if k is not None})
    return lignes, colonnes


def nettoyer(intitule):
    """La forme comparable d'un intitule de colonne : minuscules, un seul
    espace entre les mots. Excel ajoute volontiers des espaces invisibles."""
    return re.sub(r"\s+", " ", (intitule or "")).strip().lower()


# ---------------------------------------------------------------------------
# Construction de l'arbre
# ---------------------------------------------------------------------------

def nouveau_noeud(nom, acronyme, etc):
    return {"nom": nom, "acronyme": acronyme, "etc": etc,
            "lien": "", "mention": "", "revue": "", "place": "",
            "enfants": [], "index": {}}


def rattacher(parent, nom, acronyme, etc):
    """Renvoie l'enfant de "parent" qui porte ce nom, en le creant au besoin.

    L'index rend la recherche immediate, et l'ordre d'apparition dans le
    tableau est conserve : ce qu'on lit dans Excel de haut en bas se
    retrouve de gauche a droite sur la page.
    """
    cle = nettoyer(nom) + "|" + nettoyer(acronyme)
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

    for numero, ligne in enumerate(lignes, start=2):   # 2 : l'entete est en 1
        chaine = []
        parent = faux_parent
        arrete = False

        for rang, niveau in enumerate(niveaux):
            nom = ligne.get(niveau["nom"], "")
            acronyme = ligne.get(niveau.get("acronyme", ""), "")
            etc = ligne.get(niveau.get("etc", ""), "")

            if not nom and not acronyme:
                arrete = True
                continue

            if arrete:
                # Un trou dans le chemin : impossible de savoir a quoi
                # rattacher cette entite. On le dit plutot que de la poser
                # au hasard.
                alertes.append(
                    "ligne %d : \"%s\" est renseigne alors que le niveau "
                    "au-dessus (%s) est vide." % (numero, nom or acronyme,
                                                  niveaux[rang - 1]["nom"]))
                break

            parent = rattacher(parent, nom, acronyme, etc)
            chaine.append(parent)

        if not chaine:
            continue    # ligne vide : Excel en laisse souvent en fin de fichier

        # --- Les colonnes qui ne decrivent pas un niveau ------------------
        # Elles se rapportent a l'entite la plus fine de la ligne : c'est
        # celle que la ligne decrit vraiment.
        feuille = chaine[-1]
        for colonne in ("lien", "mention", "revue"):
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
                    alertes.append(
                        "ligne %d : place = \"%s\" inconnue (attendu : %s)."
                        % (numero, ligne.get("place", ""), " ou ".join(PLACES)))

    if not faux_parent["enfants"]:
        raise SystemExit("Aucune donnee exploitable dans le tableau.")

    if len(faux_parent["enfants"]) > 1:
        autres = ", ".join(n["nom"] for n in faux_parent["enfants"][1:])
        alertes.append(
            "plusieurs sommets differents dans le tableau (%s). Seul le "
            "premier est affiche : verifie l'orthographe de la colonne "
            "\"%s\"." % (autres, niveaux[0]["nom"]))

    return faux_parent["enfants"][0]


def colonnes_manquantes(config, colonnes):
    """Les colonnes attendues que le tableau ne contient pas."""
    attendues = []
    for niveau in config["niveaux"]:
        for role in ("nom", "acronyme", "etc"):
            if niveau.get(role):
                attendues.append(niveau[role])
    attendues += config["extras"]
    return [c for c in attendues if c not in colonnes]


# ---------------------------------------------------------------------------
# Mise en forme des montants
# ---------------------------------------------------------------------------

def montant(valeur):
    """"752" -> "752 M€".  "6500" -> "6 500 M€".

    Une valeur qui n'est pas un nombre ressort telle quelle : le tableau
    peut ainsi contenir "9 G€" ou "a consolider" sans que le script s'y
    oppose.
    """
    brut = (valeur or "").strip()
    if not brut:
        return ""

    # L'espace insecable vient d'Excel, la virgule est la decimale francaise.
    essai = brut.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        nombre = float(essai)
    except ValueError:
        return brut

    if nombre == int(nombre):
        chiffres = "{:,}".format(int(nombre)).replace(",", " ")
    else:
        chiffres = "{:,.1f}".format(nombre).replace(",", " ").replace(".", ",")
    return chiffres + " M€"


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


def rendu_noeud(noeud, rang, revues, marge):
    """Une boite de l'organigramme.

    Avec un lien c'est un <a>, sans lien un <div> : une boite sur laquelle
    il n'y a rien a cliquer ne doit pas se comporter comme un lien.
    """
    classes = ["orga-noeud", "orga-noeud-%d" % rang]
    if noeud["revue"] and noeud["revue"] in revues:
        classes.append("orga-revue-%d" % revues[noeud["revue"]])

    lien = noeud["lien"].strip()
    if lien in REMPLIR_PLUS_TARD:
        lien = ""

    if lien:
        ouvrante = '<a class="%s" href="%s">' % (" ".join(classes), attribut(lien))
        fermante = "</a>"
    else:
        ouvrante = '<div class="%s">' % " ".join(classes)
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


def rendu_enfants(noeuds, rang, revues, marge):
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
        lignes += rendu_noeud(noeud, rang, revues, marge + "      ")
        lignes.append(marge + "    </div>")
        lignes += rendu_enfants(noeud["enfants"], rang + 1, revues, marge + "    ")
        lignes.append(marge + "  </div>")
    lignes.append(marge + "</div>")
    return lignes


def rendu_legende(revues, marge):
    """Les pastilles qui rappellent ce que veut dire chaque encadre pointille."""
    if not revues:
        return []
    lignes = [marge + '<div class="orga-legende">']
    for libelle, numero in revues.items():
        lignes.append(marge + '  <span class="orga-legende-item orga-revue-%d">%s</span>'
                      % (numero, echapper(libelle)))
    lignes.append(marge + "</div>")
    return lignes


def relever_revues(noeud, revues):
    """Les valeurs de la colonne "revue", dans l'ordre ou elles apparaissent.

    L'ordre compte : c'est lui qui attribue sa couleur a chacune, et une
    couleur qui change d'un passage a l'autre rendrait la page instable.
    """
    if noeud["revue"] and noeud["revue"] not in revues:
        revues[noeud["revue"]] = len(revues) + 1
    for enfant in noeud["enfants"]:
        relever_revues(enfant, revues)
    return revues


def rendu(racine, config, marge):
    """L'organigramme complet."""
    revues = relever_revues(racine, {}) if config["legende"] else {}

    # Le hors-hierarchie (support a gauche, adjoint a droite) est retire des
    # branches : il se pose de part et d'autre du trait, pas dans la rangee.
    branches = [n for n in racine["enfants"] if not n["place"]]
    cotes = {p: [n for n in racine["enfants"] if n["place"] == p] for p in PLACES}

    lignes = [marge + '<div class="organigramme" style="--branches: %d;">'
              % max(len(branches), 1)]
    m1 = marge + "  "

    lignes += rendu_legende(revues, m1)

    lignes.append(m1 + '<div class="orga-sommet">')
    lignes += rendu_noeud(racine, 1, revues, m1 + "  ")
    lignes.append(m1 + "</div>")

    if cotes["support"] or cotes["adjoint"]:
        lignes.append(m1 + '<div class="orga-adjoints">')
        for place in PLACES:
            lignes.append(m1 + '  <div class="orga-cote orga-cote-%s">' % place)
            for noeud in cotes[place]:
                lignes.append(m1 + '    <div class="orga-adjoint">')
                lignes += rendu_noeud(noeud, 2, revues, m1 + "      ")
                lignes += rendu_enfants(noeud["enfants"], 3, revues, m1 + "      ")
                lignes.append(m1 + "    </div>")
            lignes.append(m1 + "  </div>")
        lignes.append(m1 + "</div>")

    lignes.append(m1 + '<div class="orga-branches">')
    for noeud in branches:
        lignes.append(m1 + '  <div class="orga-branche">')
        lignes += rendu_noeud(noeud, 2, revues, m1 + "    ")
        lignes += rendu_enfants(noeud["enfants"], 3, revues, m1 + "    ")
        lignes.append(m1 + "  </div>")
    lignes.append(m1 + "</div>")

    lignes.append(marge + "</div>")
    return lignes


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

    print("Page : %s" % page)
    print()

    alertes = []
    for config in ORGANIGRAMMES:
        chemin = chercher_tableau(page, config["csv"])
        lignes, colonnes = lire_tableau(chemin)

        absentes = colonnes_manquantes(config, colonnes)
        propres = []
        for c in absentes:
            alertes.append("%s : colonne \"%s\" absente du tableau."
                           % (config["csv"], c))

        racine = construire_arbre(lignes, config, propres)
        alertes += ["%s : %s" % (config["csv"], p) for p in propres]

        html, pose = injecter(html, config["cle"],
                              lambda marge, r=racine, c=config: rendu(r, c, marge))

        compte = compter(racine)
        print("  %-20s %s" % (config["cle"],
                              "  ->  ".join("%d au niveau %d" % (n, i + 1)
                                            for i, n in enumerate(compte))))
        print("  %-20s tableau : %s" % ("", chemin))
        if not pose:
            alertes.append(
                "repere \"<!-- ORGANIGRAMME : %s -->\" introuvable dans la "
                "page : cet organigramme n'a pas ete pose." % config["cle"])
        print()

    if crlf:
        # La page vient de Windows : on lui rend ses fins de ligne.
        html = html.replace("\r\n", "\n").replace("\n", "\r\n")

    with open(page, "w", encoding=encodage_page, newline="") as f:
        f.write(html)

    if alertes:
        print("  ATTENTION :")
        for a in alertes:
            print("    - %s" % a)
        print()

    print("Page mise a jour. Pour produire le fichier a coller dans")
    print("Confluence :  python %s"
          % (Path("outils") / "remplir-depuis-tableau.py"))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Arrive quand la sortie est envoyee dans "head" ou "more" : le
        # lecteur s'arrete avant nous. Ce n'est pas une erreur.
        sys.stderr.close()
