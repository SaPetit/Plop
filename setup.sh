#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
DEV=false

for arg in "$@"; do
  case "$arg" in
    --dev) DEV=true ;;
    *)
      echo "Usage: $0 [--dev]" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 introuvable. Installe Python 3.8+ avant de continuer." >&2
  exit 1
fi

echo "==> Création de l'environnement virtuel ($VENV_DIR)"
python3 -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Mise à jour de pip"
pip install --upgrade pip >/dev/null

if [ "$DEV" = true ]; then
  echo "==> Installation des dépendances (dev incluses)"
  pip install -r requirements-dev.txt
else
  echo "==> Installation des dépendances"
  pip install -r requirements.txt
fi

echo "==> Vérification de Chrome/Chromium"
CHROME_BIN=""
for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
  if command -v "$candidate" >/dev/null 2>&1; then
    CHROME_BIN="$candidate"
    break
  fi
done

if [ -z "$CHROME_BIN" ]; then
  echo "  /!\\ Aucun Chrome/Chromium détecté dans le PATH."
  echo "      Installe Google Chrome avant d'utiliser selenium_review.py :"
  echo "      https://www.google.com/chrome/"
else
  echo "  Détecté : $("$CHROME_BIN" --version)"
fi

echo "==> Vérification d'un chromedriver déjà présent dans le PATH"
if command -v chromedriver >/dev/null 2>&1; then
  echo "  /!\\ Un chromedriver a été trouvé dans le PATH : $(command -v chromedriver)"
  echo "      ($(chromedriver --version 2>/dev/null | head -1))"
  echo "      Selenium 4 gère normalement la version du chromedriver automatiquement"
  echo "      (Selenium Manager), mais un chromedriver déjà présent dans le PATH peut"
  echo "      être utilisé à sa place et provoquer une incompatibilité de version avec"
  echo "      Chrome. Si tu rencontres une erreur 'SessionNotCreatedException', retire"
  echo "      ce chromedriver du PATH pour laisser Selenium Manager s'en occuper."
else
  echo "  OK, aucun chromedriver externe détecté : Selenium Manager choisira la bonne"
  echo "  version automatiquement au premier lancement."
fi

echo
echo "==> Installation terminée."
echo "Active l'environnement avec : source $VENV_DIR/bin/activate"
echo "Puis lance : python selenium_review.py <login_url> urls.yaml"
