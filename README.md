# selenium_review

Script Selenium qui ouvre une page de login, attend que tu te connectes
manuellement, puis parcourt une liste d'URLs pour soit prendre un screenshot
pleine page de chacune (rapport HTML), soit les visiter une par une en
attendant une validation manuelle (revue visuelle).

## Installation

```bash
pip install -r requirements.txt
```

Nécessite Google Chrome installé. Selenium 4 télécharge et gère automatiquement
le chromedriver correspondant (Selenium Manager), aucune configuration
supplémentaire n'est nécessaire.

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
