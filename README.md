# Page Confluence JLS / JL

La page qui vit dans le module HTML de Confluence, et les deux outils qui
la remplissent depuis Excel.

## Ce qu'il y a dans le depot

    blocks/00-facile-a-modifier.html   LA page. Style + contenu, un seul fichier.
    donnees/responsables.csv           qui tient quoi, et vers quelle page
    donnees/jl-organisation.csv        l'organigramme des directions
    donnees/jl-programmes.csv          l'organigramme des programmes et leurs ETC
    outils/remplir-depuis-tableau.py   pose les noms, les liens et les images
    outils/organigrammes.py            dessine les deux organigrammes

Chaque fichier porte son mode d'emploi en tete. Ce qui suit n'est que
l'enchainement.

## Les deux commandes

Toujours ecrire `python` devant : sous Windows, taper un fichier `.py` tout
seul ne l'execute pas, cela l'ouvre dans l'editeur associe.

    python outils/organigrammes.py
        lit les deux tableaux d'organigrammes et REECRIT la page entre ses
        reperes. A relancer apres chaque modification de ces tableaux.

    python outils/remplir-depuis-tableau.py --cartes
        fabrique / met a jour donnees/responsables.csv a partir de la page.
        Les intitules sont releves dans la page : on n'en tape aucun.

    python outils/remplir-depuis-tableau.py
        produit page-remplie.html, le fichier a copier-coller dans le module
        HTML de Confluence.

Dans l'ordre, quand tout a change :

    python outils/organigrammes.py
    python outils/remplir-depuis-tableau.py --cartes
    (remplir le tableau dans Excel, enregistrer en CSV UTF-8)
    python outils/remplir-depuis-tableau.py

## Ce qui se modifie ou

| Ce qu'on veut changer                    | Ou                                  |
|------------------------------------------|-------------------------------------|
| un nom, un lien, une image de carte       | `donnees/responsables.csv`          |
| une direction, une entite, un acronyme    | `donnees/jl-organisation.csv`       |
| un portefeuille, un programme, un ETC     | `donnees/jl-programmes.csv`         |
| **le nom d'une colonne** de ces tableaux  | bloc `ORGANIGRAMMES`, en tete de `outils/organigrammes.py` |
| un titre, un texte d'accueil, une couleur | `blocks/00-facile-a-modifier.html`  |

Une seule zone de la page ne se modifie **jamais a la main** : ce qui se
trouve entre les lignes

    <!-- ORGANIGRAMME : ... -->        et        <!-- FIN ORGANIGRAMME : ... -->

`organigrammes.py` y reecrit tout a chaque passage. Le contenu vient des
tableaux, l'apparence de la feuille de style (section 11, ORGANIGRAMMES).

## Les organigrammes, en deux mots

Une ligne de tableau = une entite, avec toute sa lignee repetee dans les
colonnes de gauche, comme dans un tableau croise. Les lignes qui partagent
un debut de chemin partagent les memes boites : une sous-direction citee
dix fois n'apparait qu'une fois sur la page, avec ses dix entites dessous.

Les deux ne sont pas dessines de la meme facon, parce qu'ils ne repondent
pas a la meme question :

- **l'organisation** est un ARBRE vertical. La question est "qui depend de
  qui". La colonne `place` sort une sous-direction de la rangee pour la
  poser a cote du trait : `support` a gauche, `adjoint` a droite.
- **les programmes** sont un FLUX horizontal, de gauche a droite. La
  question est "ou passe l'argent" : l'epaisseur de chaque ruban suit
  l'ETC, on voit donc du premier coup d'oeil quel portefeuille pese et
  comment il se repartit. Le diagramme est plus large que l'ecran, et c'est
  voulu : on le deplace au curseur (cliquer-glisser) ou a la molette.

Les ETC s'ecrivent en millions d'euros, en chiffres seulement (`752`) :
l'affichage (`752 M€`, `6 500 M€`) est du ressort du script.

Une reserve sur l'echelle du flux : un noeud ne descend jamais sous un
plancher de quelques pixels. Sans lui, un programme a 1 M€ face a un
portefeuille a 6 500 M€ ferait un trait invisible, impossible a survoler et
impossible a lire. Les proportions sont donc exactes partout, sauf pour les
plus petits montants, remontes au plancher. Le reglage se trouve en tete de
`outils/organigrammes.py`, dans `FLUX`.

## Si un organigramme ne se fait pas

Le script dit ce qu'il a lu et ce qu'il attendait ; il ne s'arrete plus au
premier probleme, l'autre organigramme est refait normalement et celui qui
echoue reste dans la page tel qu'il y etait.

La sortie commence par le **chemin du script** et les intitules qu'il
attend. Si ce chemin n'est pas celui du fichier ouvert dans l'editeur, la
correction a ete faite dans un fichier et un autre a ete lance : inutile de
chercher ailleurs. Meme chose pour les intitules : ils disent ce que le
script cherchera, avant meme d'ouvrir les tableaux.

Trois causes reviennent, dans l'ordre :

1. **Le nom du sommet n'est rempli que sur la premiere ligne.** Chaque ligne
   porte sa lignee complete : le nom du sommet se repete sur *toutes* les
   lignes. Ce n'est pas un titre, c'est ce qui rattache la ligne a son
   organigramme. Dans Excel : remplir la premiere cellule, puis tirer vers
   le bas.
2. **La ligne d'entete ne correspond pas a ce que le script attend.** La
   casse, les accents, les tirets et les soulignes sont libres
   (`Sous-Direction`, `sous direction` et `SOUS_DIRECTION` sont la meme
   colonne), mais les mots doivent y etre. Le script affiche l'entete
   trouvee a cote de celle qu'il attendait, et designe l'intitule le plus
   ressemblant quand il y a une faute de frappe.

   Si les colonnes portent volontairement d'autres noms, ce n'est pas le
   tableau qu'il faut changer mais le bloc `ORGANIGRAMMES` en tete de
   `outils/organigrammes.py` : les intitules attendus y sont ecrits une
   seule fois, et nulle part ailleurs.
3. **Le fichier ne contient que son entete.** Il faut au moins une ligne de
   donnees en dessous.

Les colonnes facultatives (`place`, `mention`, `lien`) peuvent etre retirees
sans rien casser : la fonction correspondante ne s'affiche simplement plus.
Une colonne en trop est signalee mais ignoree -- c'est ce qui rattrape les
fautes de frappe dans l'entete.

## Bon a savoir

- Les tableaux se relisent en UTF-8, en Windows-1252 ou en Latin-1, avec
  des points-virgules ou des virgules : l'enregistrement Excel par defaut
  passe, quel que soit le poste.
- Les fins de ligne de la page sont conservees telles quelles. A tableaux
  inchanges, les scripts produisent un fichier identique a l'original :
  toute difference est donc une vraie difference.
- `page-remplie.html` n'est pas suivi par git : c'est un resultat, il se
  refabrique en une commande.
