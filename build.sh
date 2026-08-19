#!/usr/bin/env bash
# =============================================================================
# build.sh — genere les livrables derives depuis les sources
# -----------------------------------------------------------------------------
#   Source de verite : stylesheet/space-stylesheet.css + blocks/*.html
#   Genere :
#     blocks/00-portail-complet-standalone.html  (CSS inline, 1 seul module)
#     preview/index.html                          (apercu navigateur)
#
#   Usage : ./build.sh
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CSS="$ROOT/stylesheet/space-stylesheet.css"

# --- Extraction ---------------------------------------------------------------
# 1. le bloc :root des jetons de design
# 2. toute la PARTIE B (bibliotheque .jls-*), qui commence a la regle ".jls,"
#
# La PARTIE A (chrome Confluence) est volontairement EXCLUE : elle n'a de sens
# que chargee globalement via le Space Stylesheet, et ses selecteurs
# body#com-atlassian-confluence ne s'appliqueraient pas dans un apercu.
#
# `:root` est reecrit en `.jls` pour que la version autonome ne declare aucune
# variable au niveau global de la page Confluence.
extract_lib() {
  awk '
    /^:root \{/      { intok = 1 }
    intok            { print; if (/^\}/) intok = 0; next }
    /^\.jls,$/       { inlib = 1 }
    inlib            { print }
  ' "$CSS" | sed 's/^:root {/.jls {/'
}

# Retire l'en-tete de commentaire d'un bloc HTML (le commentaire d'installation
# n'a pas d'interet dans un fichier assemble).
strip_header() {
  sed '1{/^<!-- =\+$/!q}; /^<!-- =\+$/,/^ \+=\+ -->$/d' "$1"
}

LIB="$(extract_lib)"

# --- 1. Version autonome ------------------------------------------------------
{
  cat <<'HEADER'
<!-- ==========================================================================
     JLS PMO — PORTAIL COMPLET, VERSION AUTONOME
     --------------------------------------------------------------------------
     FICHIER GENERE — ne pas editer a la main.
     Source : stylesheet/space-stylesheet.css + blocks/01..04
     Regenerer avec : ./build.sh
     --------------------------------------------------------------------------
     QUAND UTILISER CE FICHIER
     Colle-le dans UN SEUL "HTML Module" de la Content Layout Macro. Il porte
     son propre CSS et ne depend pas du Space Stylesheet. A privilegier si :
       - tu n'as pas les droits d'admin sur le space, ou
       - le HTML Module rend le contenu dans une iframe (le Space Stylesheet
         n'y penetre pas).
     Sinon, prefere les blocs 01 a 04 + le Space Stylesheet : le CSS est alors
     charge une seule fois pour tout le space, et partage par toutes les pages.
     ========================================================================== -->

<style>
/* Bibliotheque de composants .jls-* — copie generee, scope sous .jls */
HEADER
  printf '%s\n' "$LIB"
  echo "</style>"
  echo
  for f in 01-hero 02-organisation 03-programmes-et-synthese 04-onglets; do
    echo "<!-- ---------- $f ---------- -->"
    strip_header "$ROOT/blocks/$f.html"
    echo
  done
  strip_header "$ROOT/blocks/05-enhancement.js.html"
} > "$ROOT/blocks/00-portail-complet-standalone.html"

# --- 2. Apercu navigateur -----------------------------------------------------
{
  cat <<'HEADER'
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JLS PMO — apercu</title>
<!-- FICHIER GENERE — regenerer avec ./build.sh -->
<style>
  /* Simulation grossiere du fond de page Confluence, pour juger les blocs
     dans leur contexte reel plutot que sur du blanc. */
  body {
    margin: 0;
    padding: 34px 22px 80px;
    background-color: #F4F5F7;
    background-image:
      radial-gradient(900px 500px at 88% -6%, rgba(239,131,84,.07), transparent 60%),
      radial-gradient(700px 500px at 4% 4%, rgba(79,93,117,.08), transparent 55%);
    background-attachment: fixed;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  .page {
    max-width: 1180px;
    margin: 0 auto;
    padding: 30px;
    background: #fff;
    border: 1px solid rgba(45,49,66,.12);
    border-radius: 20px;
    box-shadow: 0 4px 8px rgba(45,49,66,.07), 0 14px 32px rgba(45,49,66,.13);
  }
</style>
<style>
HEADER
  printf '%s\n' "$LIB"
  cat <<'MID'
</style>
</head>
<body>
<div class="page">
MID
  for f in 01-hero 02-organisation 03-programmes-et-synthese 04-onglets; do
    strip_header "$ROOT/blocks/$f.html"
    echo
  done
  echo "</div>"
  strip_header "$ROOT/blocks/05-enhancement.js.html"
  echo "</body>"
  echo "</html>"
} > "$ROOT/preview/index.html"

echo "genere :"
wc -l "$ROOT/blocks/00-portail-complet-standalone.html" "$ROOT/preview/index.html"
