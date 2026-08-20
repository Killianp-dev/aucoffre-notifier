# aucoffre-notifier

Outil Python personnel pour surveiller [AuCoffre.com](https://www.aucoffre.com) : il lit le prix affiché, détecte le badge **LSP**, et envoie une notification [Pushover](https://pushover.net) quand un seuil est atteint. Il peut aussi suivre le cours de l’once d’or.

Ce n’est **pas** un projet affilié à AuCoffre. Le HTML du site peut changer à tout moment : si le parseur casse, commencez par inspecter les fichiers HTML sauvegardés (voir ci-dessous).

## Fonctionnalités

- Récupération des fiches produit (`article.product-card`) avec un User-Agent navigateur
- Extraction du prix et détection du ruban LSP
- Alerte Pushover si un produit **LSP** a un prix **supérieur ou égal** au seuil `n`
- Optionnel : alerte si le cours de l’once d’or dépasse un seuil
- Journaux [Loguru](https://github.com/Delgan/loguru) avec rotation dans `log/aucoffre.log`
- Pause aléatoire entre les requêtes pour limiter la charge
- Sauvegarde locale du dernier HTML récupéré (`page_content_raw.html` et `page_content_formate.html`)

## Prérequis

- Python 3.10+ (3.8 devrait fonctionner)
- Un compte [Pushover](https://pushover.net) (application + utilisateur)

## Installation

```bash
git clone https://github.com/Killianp-dev/aucoffre-notifier.git
cd aucoffre-notifier
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Pour les tests :

```bash
pip install pytest
```

## Configuration

Créez un fichier `.env` à la racine (ne le commitez jamais) :

```env
PUSHOVER_TOKEN=votre_app_token
PUSHOVER_USER=votre_user_key
```

Les URLs cibles et les seuils se règlent dans `main.py`, dans le bloc `if __name__ == "__main__"`.

Exemple actuel :

| Paramètre | Rôle |
| --- | --- |
| `url_target_1` | Liste de produits paginée |
| `url_gold_course` | Page du cours de l’or |
| `main_function(..., 79.0)` | Alerte LSP si prix ≥ 79 € |
| `check_gold_price(..., 4400.0)` | Alerte or si cours > 4400 € (commentaire par défaut) |

Pour activer le suivi de l’once d’or, décommentez l’appel à `check_gold_price` dans `main.py`.

## Utilisation

```bash
python main.py
```

Le script parcourt les pages 1 et 2 de la cible configurée, avec des temporisations aléatoires entre chaque requête.

### Planification (cron)

Exemple : toutes les heures, entre 8 h et 20 h :

```cron
0 8-20 * * * /chemin/vers/.venv/bin/python /chemin/vers/aucoffre-notifier/main.py
```

## Tests

Les tests unitaires mockent le réseau. Ils ne frappent pas AuCoffre.

```bash
pytest test_notifier.py -v
```

Un test optionnel envoie une vraie notification Pushover si `PUSHOVER_TOKEN` et `PUSHOVER_USER` sont définis. Sans ces variables, il est ignoré (`pytest.skip`).

## Fichiers générés

| Fichier | Contenu |
| --- | --- |
| `page_content_raw.html` | HTML brut de la dernière page |
| `page_content_formate.html` | Même contenu, indenté |
| `log/aucoffre.log` | Journal d’exécution (rotation + compression) |

Ces fichiers sont ignorés par Git.

## Limites

- Le parseur dépend des classes CSS actuelles du site (`product-card`, `ribbon`, `cotation_name`, etc.).
- Respectez les conditions d’utilisation du site et évitez les fréquences trop élevées.
- Les clés Pushover donnent accès à vos notifications : gardez-les hors du dépôt.

## Licence

MIT.
