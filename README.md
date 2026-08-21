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

Deux colonnes sortent de la hierarchie :

- `place` (organisation) pose une sous-direction a cote du trait plutot que
  dans la rangee : `support` a gauche, `adjoint` a droite.
- `revue` (programmes) entoure la boite de pointilles et l'ajoute a la
  legende. Chaque boite porte son propre encadre ; des boites voisines qui
  partagent la meme valeur se lisent comme un groupe.

Les ETC s'ecrivent en millions d'euros, en chiffres seulement (`752`) :
l'affichage (`752 M€`, `6 500 M€`) est du ressort du script.

## Bon a savoir

- Les tableaux se relisent en UTF-8, en Windows-1252 ou en Latin-1, avec
  des points-virgules ou des virgules : l'enregistrement Excel par defaut
  passe, quel que soit le poste.
- Les fins de ligne de la page sont conservees telles quelles. A tableaux
  inchanges, les scripts produisent un fichier identique a l'original :
  toute difference est donc une vraie difference.
- `page-remplie.html` n'est pas suivi par git : c'est un resultat, il se
  refabrique en une commande.
