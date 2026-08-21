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

## Mettre à jour les responsables depuis un tableau

Les noms affichés sur la page sont pilotés par un fichier tableur, pour ne plus
avoir à éditer le HTML à chaque changement de titulaire.

```
donnees/responsables.csv              ← le tableau, à ouvrir dans Excel
outils/remplir-depuis-tableau.py      ← le script qui fabrique la page remplie
```

### Principe

Le script reconnaît chaque carte par **le titre affiché dessus**. Il n'y a donc
rien à ajouter dans le HTML — pas d'identifiant, pas d'étiquette invisible :

```html
<p class="carte-titre">A6 Dev</p>        <!-- repère -->
<p class="carte-personne">…</p>          <!-- ligne remplacée -->
```

```csv
carte;nom;lien
A6 Dev;Prenom Nom;https://atlas.fr.space.corp/confluence/display/JLS/A6+Dev
```

La colonne `lien` est facultative : laissée vide, la carte garde le `href`
écrit dans le HTML. Le nom du bandeau d'accueil se pilote avec la ligne
`Head of PMO`.

### Utilisation

```bash
# 1. fabriquer le tableau à partir de la page
#    (les titres sont relevés dans le HTML : aucun n'est retapé à la main)
python3 outils/remplir-depuis-tableau.py --cartes

# 2. remplir les colonnes « nom » et « lien » dans Excel,
#    puis « Enregistrer sous » → CSV UTF-8

# 3. produire la page remplie
python3 outils/remplir-depuis-tableau.py
```

Le second appel écrit `page-remplie.html` : on l'ouvre, on copie tout, on colle
dans le module HTML de Confluence.

Le séparateur (`;` ou `,`) est détecté automatiquement — Excel français
enregistre avec des points-virgules, Excel anglais avec des virgules. Les fins
de ligne du fichier d'origine sont conservées.

Refaire l'étape 1 après avoir ajouté, supprimé ou renommé une carte : le
tableau se resynchronise sur la page. **Les noms déjà saisis sont conservés** —
seules les cartes nouvelles apparaissent vides, et les lignes devenues sans
objet sont annoncées avant d'être retirées.

### Ce que le script signale

| Situation | Sortie |
|---|---|
| Ligne du tableau qui ne correspond à aucune carte | `ATTENTION` + le titre fautif |
| Carte de la page absente du tableau | liste informative (la carte garde son texte) |
| Deux cartes portant le même titre | `ATTENTION` — seule la première est remplie |

C'est ce qui évite les fautes de frappe silencieuses : un titre mal orthographié
dans Excel ne passe pas inaperçu.

Les exemples de cartes écrits dans le **guide en commentaire**, en tête du
fichier HTML, ne sont jamais touchés : le script repère les zones de
commentaire et les exclut.

### Où va chaque fichier

| Fichier | Où il vit | Qui s'en sert |
|---|---|---|
| `blocks/00-facile-a-modifier.html` | la source, dans ce dépôt | qui modifie la structure |
| `donnees/responsables.csv` | sur le poste, ouvert dans Excel | qui met à jour les titulaires |
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
