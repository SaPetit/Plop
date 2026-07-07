# selenium_review

Script Selenium qui ouvre une page de login, attend que tu te connectes
manuellement, puis parcourt une liste d'URLs pour soit prendre un screenshot
pleine page de chacune (rapport HTML), soit les visiter une par une en
attendant une validation manuelle (revue visuelle).

## Installation

```bash
./setup.sh
source .venv/bin/activate
```

`setup.sh` crée un environnement virtuel (`.venv`), installe les dépendances,
et vérifie que Chrome est bien installé. Ajoute `--dev` pour installer aussi
les dépendances de test (`./setup.sh --dev`).

Sans le script, une installation manuelle suffit aussi :

```bash
pip install -r requirements.txt
```

### À propos de chromedriver

Nécessite Google Chrome installé. Selenium 4.6+ embarque **Selenium
Manager** : il détecte la version de Chrome installée et télécharge/cache
automatiquement le chromedriver correspondant au premier lancement — aucune
installation ou gestion manuelle du driver n'est nécessaire.

Le seul piège possible : si un chromedriver est déjà présent ailleurs dans le
`PATH` (installé par un autre outil), Selenium peut l'utiliser à la place de
celui géré automatiquement et planter avec une erreur du type
`SessionNotCreatedException` si sa version ne correspond pas à celle de
Chrome. `setup.sh` détecte ce cas et affiche un avertissement ; si ça arrive,
retire ce chromedriver du `PATH` pour laisser Selenium Manager s'en occuper.

## Format de la liste d'URLs (YAML)

Voir `urls.example.yaml` :

```yaml
- url: https://example.com/page1
  message: "Vérifier que le bouton principal est bleu"
- url: https://example.com/page2
  message: "Vérifier le layout en mobile"
```

## Usage

### Mode screenshot (défaut)

```bash
python selenium_review.py <login_url> urls.yaml
```

1. Une fenêtre Chrome s'ouvre sur `login_url`.
2. Connecte-toi manuellement, puis appuie sur Entrée dans le terminal.
3. Le script visite chaque URL de la liste, attend le chargement complet de
   la page (+ un délai configurable via `--wait`), et capture un screenshot
   pleine page.
4. Un rapport HTML autonome est généré (images encodées en base64) avec pour
   chaque page : le numéro, l'URL, le screenshot et le message associé
   affiché en dessous. Ouvrable dans un navigateur, éditable dans un éditeur
   de texte.

Par défaut le rapport est écrit dans `output/report_<timestamp>.html`. Utilise
`--output chemin/vers/rapport.html` pour choisir l'emplacement.

### Mode revue manuelle

```bash
python selenium_review.py <login_url> urls.yaml --manual-review
```

Aucun screenshot n'est pris et aucun fichier n'est généré. Le script visite
chaque URL, affiche son message dans le terminal, puis attend que tu appuies
sur Entrée pour passer à la suivante.

## Options

| Option             | Description                                                              | Défaut                          |
|--------------------|---------------------------------------------------------------------------|----------------------------------|
| `--manual-review`  | Mode visite manuelle sans screenshot                                       | désactivé                        |
| `--output PATH`    | Chemin du rapport HTML (mode screenshot uniquement)                        | `output/report_<timestamp>.html` |
| `--wait SECONDS`   | Délai après chargement de page avant capture                               | `1.0`                            |

## Gestion des erreurs

Si une URL échoue à charger, le script logue l'erreur (terminal, et dans le
rapport HTML en mode screenshot) et continue avec l'URL suivante sans
s'arrêter.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Les tests couvrent le parsing YAML, la génération du rapport HTML
(échappement anti-XSS inclus) et la logique des modes screenshot/revue
manuelle, via un faux driver — ils ne lancent pas de vrai navigateur. Une CI
GitHub Actions (`.github/workflows/tests.yml`) exécute cette suite sur
Python 3.10/3.11/3.12 à chaque push/PR sur `main`.
