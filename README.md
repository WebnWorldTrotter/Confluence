# JLS — Program Management Office · habillage d'espace Confluence

Habillage complet d'un espace **Confluence Data Center / Server** (thème Linchpin
Enterprise News) reproduisant l'architecture du PowerPoint `confluence jls` :
hero d'accueil, organigramme PMO, points focaux JL Board, synthèse
multi-programmes et panneau à onglets *Group PMO / Transversal*.

---

## Pourquoi ne pas garder les modules Navigation Cards

Le prototype actuel empile *Navigation Highlight* + trois *Navigation Cards*.
Ces modules savent afficher une **grille de tuiles uniformes** — ils ne savent pas
rendre une hiérarchie. D'où les symptômes visibles sur la capture du prototype :

| Symptôme | Cause |
|---|---|
| La même image de montagne répétée 8 fois | `Background image` est le seul levier visuel du module |
| Cartes désalignées, hauteurs inégales | chaque module gère sa propre grille, sans gouttière commune |
| Aucun lien visible entre SYSTEM et ses sous-sujets | le module n'a pas de notion de niveau |
| Boutons « Button Label » empilés | l'onglet Aura ne sait afficher qu'une liste plate |

La structure entière passe donc dans des **HTML Modules**, et la mise en forme
dans le **Space Stylesheet**. Les modules Navigation ne sont plus utilisés.

---

## Arborescence

```
stylesheet/
  space-stylesheet.css                 ← à coller dans Look and Feel > Stylesheet
blocks/
  01-hero.html                         ← HTML Module 1
  02-organisation.html                 ← HTML Module 2 (Chief of PMO + Program PMO)
  03-programmes-et-synthese.html       ← HTML Module 3 (JL Board + Multi-Programme)
  04-onglets.html                      ← HTML Module 4 (Group PMO / Transversal)
  05-enhancement.js.html               ← HTML Module 5 (optionnel, en dernier)
  00-portail-complet-standalone.html   ← GÉNÉRÉ · variante tout-en-un
  00-facile-a-modifier.html            ← variante tout-en-un, écrite pour être
                                          reprise à la main (voir plus bas)
donnees/
  responsables.csv                     ← les titulaires, à ouvrir dans Excel
outils/
  remplir-depuis-tableau.py            ← injecte le tableau dans la page
preview/
  index.html                           ← GÉNÉRÉ · aperçu navigateur
build.sh                               ← régénère les deux fichiers GÉNÉRÉS
```

> Les fichiers marqués **GÉNÉRÉ** ne s'éditent pas à la main.
> Modifier la source puis lancer `./build.sh`.

---

## Installation

### 1. Le stylesheet (une seule fois pour tout l'espace)

`Space tools` → `Look and Feel` → `Stylesheet` → `Edit`, coller le contenu de
`stylesheet/space-stylesheet.css`, puis `Save`.

Il contient deux parties :

- **Partie A** — habillage du chrome Confluence : fond de page texturé, panneau
  de contenu surélevé, titres, liens, tableaux, panels, boutons AUI, barre
  latérale. Ciblée sur `body#com-atlassian-confluence` et sur le mode lecture,
  pour ne pas perturber l'éditeur.
- **Partie B** — la bibliothèque de composants `.jls-*` utilisée par les blocs.
  Tout est préfixé et scopé sous `.jls` : aucune règle ne peut fuir vers l'UI
  Confluence.

### 2. Les blocs

Dans la Content Layout Macro, supprimer les modules *Navigation Highlight* et
*Navigation Cards*, puis `+ Add Module` → **HTML Module** pour chacun des blocs
`01` à `04`, chacun dans son propre module. Les quatre sont indépendants et se
positionnent librement dans la macro (par exemple `01` et `02` côte à côte en
haut, `03` et `04` côte à côte en dessous) — voir *Personnalisation* ci-dessous
pour la logique de ce découpage.

### 3. Le script (optionnel)

`05-enhancement.js.html` va dans un dernier HTML Module, **en bas de page**.
Il n'est jamais indispensable : sans lui les onglets fonctionnent (CSS pur), les
cartes flottent, la page est complète. Il n'ajoute que l'apparition au
défilement, la navigation clavier des onglets et les attributs ARIA.

### Variante : pas d'accès au stylesheet

Si tu n'es pas admin de l'espace, ou si le HTML Module rend son contenu dans une
iframe (le Space Stylesheet n'y pénètre pas), colle
`blocks/00-portail-complet-standalone.html` dans **un seul** HTML Module : il
embarque son propre CSS.

---

## Personnalisation

### Pourquoi 4 blocs plutôt que 3

Chaque bloc est un module HTML indépendant que tu places où tu veux dans la
Content Layout Macro — typiquement deux quadrants en haut (`01` hero, `02`
organisation) et deux en dessous (`03` JL Board + synthèse, `04` onglets).
Le bloc `04` ne dépend plus d'un autre bloc pour sa largeur : les onglets
occupent tout l'espace de leur propre module, quel que soit le quadrant qui
les accueille.

### Contenu

Les valeurs à remplacer sont marquées `{{ }}` :

| Placeholder | Où | Remplacer par |
|---|---|---|
| `{{Prenom Nom}}` | cartes, hero | le titulaire |
| `NN` | attribut des `.jls-avatar` | ses initiales, 2 lettres |
| `{{Sujet transversal N}}` | onglet Transversal | le contenu réel |
| `href="#"` | partout | l'URL de la page cible |

> Les noms des personnes ne sont **pas** committés : le PowerPoint source est
> classifié `AG-TLP:AMBER`. Renseigne-les directement côté Confluence.

### Couleurs

Un seul endroit à modifier, le bloc `:root` en tête du stylesheet :

```css
--jls-ink:         #2D3142;   /* encre, fonds profonds        */
--jls-slate:       #4F5D75;   /* texte secondaire             */
--jls-silver:      #BFC0C0;   /* filets, séparateurs          */
--jls-paper:       #FFFFFF;   /* surfaces                     */
--jls-accent:      #EF8354;   /* accent, focus, états actifs  */
--jls-accent-deep: #B8501C;   /* accent pour le TEXTE         */
```

**Sur `--jls-accent-deep`** : le corail `#EF8354` plafonne à 2,6:1 sur blanc,
sous le seuil WCAG AA de 4,5:1. Il reste donc réservé aux **aplats, lueurs et
bordures**. Dès qu'il y a du texte (lien, libellé), c'est `--jls-accent-deep`
(5,0:1 avec du blanc) qui est utilisé. Si tu changes l'accent, recalcule sa
variante foncée.

### Ajouter une carte / un onglet

- **Carte** : dupliquer un bloc `<a class="jls-node">`. La grille se réorganise
  seule, aucune largeur à calculer.

> **Ce qui espace les cartes, c'est leur conteneur, jamais la carte.** Une carte
> ne porte aucune marge : `.grille` répartit sur autant de colonnes que la place
> le permet, `.pile` garde une colonne unique, et des cartes posées directement
> dans un `<div>` ordinaire se touchent.
- **Onglet** : ajouter un `<input class="jls-tabs__radio">`, son `<label>` et sa
  `<section class="jls-tabs__panel">`, puis passer `--jls-tab-n` à la nouvelle
  valeur. Le CSS gère jusqu'à 4 onglets ; au-delà, prolonger les sélecteurs
  `:nth-of-type` de la section B.7. **Les `id` doivent rester uniques sur la
  page** — si tu dupliques le bloc, change aussi l'attribut `name`.

---

## Contraintes Confluence prises en compte

- **Aucune ressource externe** : textures en SVG data-URI et dégradés CSS,
  polices système. Rien à héberger, compatible avec une CSP stricte.
- **Dégradation sans JavaScript** : les onglets reposent sur
  `input[type=radio]` + CSS. Si le module HTML filtre les `<script>`, la page
  reste entièrement navigable.
- **Le contenu ne peut jamais rester invisible** : l'apparition au défilement
  est doublée d'un garde-fou à 2,5 s et d'un `beforeprint`. Un saut d'ancre ou
  une restauration de scroll ne peuvent pas masquer une section.
- **Le script ne peut pas casser la page** : IIFE + `try/catch`, aucune
  dépendance à jQuery ni à AJS.
- **`prefers-reduced-motion`** : flottaisons, glissements et apparitions
  désactivés.
- **Impression** : ombres et textures retirées, tous les panneaux d'onglets
  dépliés.

---

## Aperçu

`preview/index.html` s'ouvre directement dans un navigateur (simulation du fond
de page Confluence). Il sert à valider les blocs avant de les coller.
Vérifié sous Chromium en 1280 px et 390 px : aucune erreur console, aucun
débordement horizontal.

Pour régénérer l'aperçu et la version autonome après une modification :

```bash
./build.sh
```

---

## Piloter la page depuis un tableau

Les noms, les liens et les images de fond sont pilotés par un fichier tableur,
pour ne plus avoir à éditer le HTML à chaque changement.

```
donnees/responsables.csv              ← le tableau, à ouvrir dans Excel
outils/remplir-depuis-tableau.py      ← le script qui fabrique la page remplie
```

### Principe

Le script reconnaît chaque élément par **son intitulé affiché**. Il n'y a donc
rien à ajouter dans le HTML — pas d'identifiant, pas d'étiquette invisible.

| Colonne | Rôle |
|---|---|
| `carte` | l'intitulé affiché sur la page — c'est le repère, ne pas le modifier |
| `nom` | le titulaire |
| `lien` | l'adresse de la page Confluence à ouvrir |
| `image` | l'adresse de l'image de fond |

```csv
carte;nom;lien;image
A6 Dev;Prenom Nom;https://…/A6+Dev;https://…/A6%20dev%20image.png?api=v2
JLV;Prenom Nom;https://…/JLV;
SYSTEM;;https://…/System;
```

**Une cellule vide veut dire « ne change rien »** : on ne remplit que ce qui
bouge, le reste garde ce qui est écrit dans le HTML.

Le tableau couvre tout ce qui est cliquable ou nominatif :

| Élément | `nom` | `lien` | `image` |
|---|:-:|:-:|:-:|
| cartes (`<a class="carte">`) | ✓ | ✓ | ✓ |
| lignes de l'onglet Group PMO (`<a class="ligne">`) | | ✓ | |
| tuiles de l'onglet Transversal (`<a class="tuile">`) | | ✓ | |
| bouton du bandeau (`<a class="bouton">`) | | ✓ | |
| bandeau d'accueil (`Head of PMO`) | ✓ | | |

Une valeur donnée à un élément qui ne l'accepte pas est signalée, pas ignorée
en silence.

### Les images

Une carte qui n'a **pas encore** d'image de fond en reçoit une automatiquement
dès que la colonne `image` est renseignée : la balise `<img class="carte-fond">`
est insérée et la classe `carte-image` ajoutée, ce qui applique le voile de
lisibilité. Rien à préparer à la main dans le HTML.

L'adresse doit commencer par `https://` ou `/confluence/…`. Une adresse en
`data:` est bloquée par Confluence.

### Utilisation

> **Sous Windows, toujours écrire `python` devant.** Taper un fichier `.py`
> tout seul ne l'exécute pas : Windows l'ouvre dans l'éditeur associé (VSCode,
> le plus souvent). C'est la confusion la plus fréquente.

> **Le rangement des fichiers est libre.** Le script fonctionne dans
> l'arborescence du dépôt comme dans un dossier où tout est posé à plat : il
> prend alors la page `.html` qu'il trouve à côté de lui et écrit le tableau au
> même endroit. S'il ne trouve rien, il affiche la liste des endroits où il a
> cherché.

```bash
# 1. fabriquer le tableau à partir de la page
python3 outils/remplir-depuis-tableau.py --cartes

# 2. remplir ce qui change dans Excel,
#    puis « Enregistrer sous » → CSV UTF-8

# 3. produire la page remplie
python3 outils/remplir-depuis-tableau.py
```

Le second appel écrit `page-remplie.html` : on l'ouvre, on copie tout, on colle
dans le module HTML de Confluence.

`--cartes` relève les intitulés **dans la page** — aucun n'est retapé, ce qui
supprime la faute de frappe à la source. Il reporte aussi les adresses et les
images déjà en place, et conserve ce que tu avais déjà saisi. Le refaire après
avoir ajouté, supprimé ou renommé un élément : les lignes devenues sans objet
sont annoncées avant d'être retirées.

Le séparateur (`;` ou `,`) est détecté automatiquement — Excel français
enregistre avec des points-virgules, Excel anglais avec des virgules. Les fins
de ligne du fichier d'origine sont conservées.

### Ce que le script signale

| Situation | Sortie |
|---|---|
| Ligne du tableau qui ne correspond à aucun élément | `ATTENTION` + l'intitulé fautif |
| Valeur donnée à un élément qui ne l'accepte pas | `ATTENTION` + la colonne en cause |
| Élément de la page absent du tableau | liste informative (il garde son texte) |
| Deux éléments portant le même intitulé | `ATTENTION` — seul le premier est rempli |

Le guide en commentaire, en tête du fichier HTML, n'est jamais touché : le
script masque les commentaires avant toute recherche. Cela vaut pour les
exemples de cartes qu'il contient, mais aussi pour ses balises `<a>` ouvertes
et jamais refermées, qui sinon happeraient le début de la page.

### Vérification

Un aller-retour *page → tableau → page* sans rien modifier dans Excel rend un
fichier **identique au bit près** à l'original. C'est le contrôle le plus
simple pour s'assurer que le tableau reflète bien la page :

```bash
python3 outils/remplir-depuis-tableau.py --cartes
python3 outils/remplir-depuis-tableau.py
diff blocks/00-facile-a-modifier.html page-remplie.html && echo identique
```

### Où va chaque fichier

| Fichier | Où il vit | Qui s'en sert |
|---|---|---|
| `blocks/00-facile-a-modifier.html` | la source, dans ce dépôt | qui modifie la structure |
| `donnees/responsables.csv` | sur le poste, ouvert dans Excel | qui met à jour les données |
| `outils/remplir-depuis-tableau.py` | ce dépôt, lancé depuis le poste | idem |
| `page-remplie.html` | GÉNÉRÉ, à copier-coller dans Confluence | — |

Le dépôt n'est pas nécessaire au quotidien : une fois le dossier récupéré sur
le poste (`Code` → `Download ZIP`), tout le cycle *Excel → script → coller dans
Confluence* se fait en local, sans passer par GitHub.

Python 3 suffit — aucune bibliothèque à installer.

---

## Reste à faire

- Contenu réel de l'onglet **Transversal** (illisible sur la source).
- URLs de destination des cartes et des lignes.
- Vérification des intitulés d'entités relevés sur photo (`SPRO / ESR`,
  `LIOD, Kourou Focal Point & Ground Industrialists`).
