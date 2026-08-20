# aucoffre-notifier

Outil Python qui surveille [AuCoffre.com](https://www.aucoffre.com) : extraction du **prix** et du badge **LSP**, suivi du cours de l’once d’or, et alerte **Pushover** quand un seuil est franchi.

## Fonctionnalités

- Télécharge les pages cibles avec un User-Agent navigateur.
- Sauvegarde le HTML brut et une version indentée :
  - `page_content_raw.html`
  - `page_content_formate.html`
- Extrait le prix affiché et détecte le label LSP.
- Alerte Pushover si un produit LSP a un prix **supérieur ou égal** au seuil `n`.
- Optionnel : alerte si le cours de l’once d’or dépasse le seuil `n`.
- Journaux Loguru avec rotation dans `log/aucoffre.log`.
- Temporisations aléatoires entre les requêtes pour limiter la charge.

## Prérequis

- Python 3.8 ou supérieur
- [pip](https://pip.pypa.io/)

## Installation

```bash
git clone https://github.com/Killianp-dev/aucoffre-notifier.git
cd aucoffre-notifier
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Configuration

Créez un fichier `.env` à la racine du projet :

```ini
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user
```

Les seuils et les URLs cibles se règlent dans `main.py` (`if __name__ == "__main__"`).

## Utilisation

```bash
python main.py
```

## Tests

```bash
pytest test_notifier.py -v
```

## Fichiers générés

- `page_content_raw.html` — HTML brut de la dernière page récupérée
- `page_content_formate.html` — même contenu, indenté
- `log/aucoffre.log` — journal d’exécution

## Licence

Ce projet est sous licence MIT.
