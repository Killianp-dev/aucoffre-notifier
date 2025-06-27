import os
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger

load_dotenv()  # Chargement des variables d'environnement

# Définition des chemins
CURRENT_DIR = Path(__file__).resolve().parent
FILE_RAW = CURRENT_DIR / "page_content_raw.html"
FILE_FORMATE = CURRENT_DIR / "page_content_formate.html"

logger.add(
    CURRENT_DIR / "aucoffre.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {message}",
    level="INFO", 
    rotation="10 KB",
    retention=3,
    compression="zip"
)


class Product:
    def __init__(self, article):
        self.article = article
        self.prime = self._extract_prime()
        self.lsp = self._check_lsp()

    def _extract_prime(self):
        prime_elements = self.article.find_all("span", class_="text-bold")
        prime_values = [
            float(match.group(1).replace(",", "."))
            for prime_element in prime_elements
            if (match := re.search(r"(\d+(?:[.,]\d+)?)%", prime_element.text.strip()))
        ]
        return prime_values[0] if prime_values else None

    def _check_lsp(self):
        return bool(self.article.find("div", class_="ribbon", string=re.compile("LSP", re.IGNORECASE)))


def save_html_files(response_text, soup):
    with open(FILE_RAW, "w", encoding="utf-8") as f:
        f.write(response_text)
    with open(FILE_FORMATE, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


def get_products(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        save_html_files(response.text, soup)

        articles = soup.find_all("article", class_="product-card")
        products = [Product(article) for article in articles]
        return products
    else:
        logger.error(f"❌ Erreur {response.status_code}: Impossible de récupérer la page")
        return []


def send_alert(message):
    try:
        response = requests.post("https://api.pushover.net/1/messages.json",
                                 data={
                                     "token": os.environ["PUSHOVER_TOKEN"],
                                     "user": os.environ["PUSHOVER_USER"],
                                     "message": message
                                 })
        response.raise_for_status()
        logger.success("✅ Alerte envoyée avec succès.")
    except requests.RequestException as e:
        logger.error(f"❌ Impossible d'envoyer l'alerte : {str(e)}")


def main_function(url):
    logger.info("▶️ Début de l'exécution de main_function")
    products = get_products(url)
    for product in products:
        logger.success(f"Produit analysé - Prime : {product.prime}% | LSP : {product.lsp}")
        if product.prime is not None and product.lsp is True and product.prime <= 3.0:
            send_alert(f"⚠️ Alerte : prime {product.prime}% LSP !")
    logger.info("✅ Fin de l'exécution de main_function")


url_target = "https://www.aucoffre.com/recherche/metal-1/marketing_list-5/stype-1/produit?page="


if __name__ == "__main__":
    for page in range (1, 5):
        logger.info(f"🔍 Traitement de la page {page}")
        main_function(f"{url_target}{page}")
