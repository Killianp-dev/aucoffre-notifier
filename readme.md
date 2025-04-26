# AuCoffre Scraper

Un outil Python pour récupérer la liste de produits sur **AuCoffre.com**, extraire la **prime** (%) et détecter le label **LSP**, puis envoyer une alerte via **Pushover** si certaines conditions sont remplies.

---

## Caractéristiques

- 💻 Téléchargement de la page cible avec un en-tête User-Agent.
- 📄 Sauvegarde du contenu HTML brut et du contenu HTML formaté :
  - `page_content_raw.html`
  - `page_content_formate.html`
- 🔍 Extraction de la **prime** (pourcentage) à partir des éléments HTML.
- 🏷️ Vérification de la présence du label **LSP**.
- 🔔 Envoi d’alertes via Pushover lorsque la prime est inférieure ou égale à 5% et que le produit a le label LSP.
- 🗒️ Journalisation détaillée avec **Loguru** dans `aucoffre.log`.

## Prérequis

- Python 3.8 ou supérieur
- [pip](https://pip.pypa.io/) (ou un autre gestionnaire de paquets Python)

## Installation

1. Clonez ce dépôt :

```bash
git clone https://github.com/votre-utilisateur/aucoffre-scraper.git
cd aucoffre-scraper
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

1. Dupliquez le fichier exemple `.env.example` ou créez un fichier `.env` à la racine du projet.
2. Ajoutez vos identifiants Pushover :

```ini
PUSHOVER_TOKEN=votre_pushover_token
PUSHOVER_USER=votre_pushover_user
```

## Usage

Lancez simplement le script principal en fournissant l’URL cible (par défaut, c’est déjà l’URL du site AuCoffre) :

```bash
python main.py
```

Pour utiliser une autre URL :

```bash
python main.py "https://votre-site-cible.com"
```

## Fichiers générés

- `page_content_raw.html` : contenu brut de la page récupérée.
- `page_content_formate.html` : même contenu, mais mis en forme (prettified).
- `aucoffre.log` : journal d’exécution avec logs d’information, d’erreur et de succès.

## Personnalisation

- Modifiez les seuils ou la logique dans `main.py` selon vos besoins :
- Seuil de **prime** (5%)
- Présence ou non du label **LSP**

## Licence

Ce projet est sous licence MIT. 


