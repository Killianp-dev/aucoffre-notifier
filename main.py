import os
import random
import re
from pathlib import Path
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

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
        """Initialise une instance de Produit à partir de sa structure HTML."""
        self.article = article
        self.price = self._extract_price()
        self.lsp = self._check_lsp()

    def _extract_price(self):
        """Extrait et formate le prix du produit en ciblant la balise spécifique."""
        price_element = self.article.find("p", class_=re.compile(r"text-xlarge.*text-bolder"))
        if price_element:
            text = price_element.get_text(strip=True).replace("\xa0", " ")
            if match := re.search(r"(\d+(?:[.,]\d+)?)", text):
                return float(match.group(1).replace(",", "."))
        return None

    def _check_lsp(self):
        """Détermine si le produit bénéficie de l'option LSP dans le DOM."""
        return bool(self.article.find("div", class_="ribbon", string=re.compile("LSP", re.IGNORECASE)))


def save_html_files(response_text, soup):
    """Sauvegarde les requêtes HTML au format brut et indenté pour l'analyse locale."""
    with open(FILE_RAW, "w", encoding="utf-8") as f:
        f.write(response_text)
    with open(FILE_FORMATE, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


def get_products(url):
    """Effectue une requête sur l'URL ciblée, parse le HTML et retourne une liste d'objets Product."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
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
    except Exception as e:
        logger.error(f"❌ Erreur lors de la requête : {e}")
        return []


def send_alert(message):
    """Transmet une notification sur mobile via le service Pushover."""
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


def check_gold_price(url, n):
    """Extrait le cours de l'once d'or en temps réel et notifie si le palier limite n est franchi."""
    logger.info("▶️ Vérification du cours de l'or...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            once_cell = soup.find("td", class_="cotation_name", string=re.compile("Once d'or", re.IGNORECASE))
            
            if once_cell:
                price_cell = once_cell.find_next_sibling("td", class_="cotation_amount")
                
                if price_cell:
                    text = price_cell.get_text(strip=True).replace("\xa0", "").replace(" ", "").replace("€", "")
                    
                    if match := re.search(r"(\d+(?:[.,]\d+)?)", text):
                        price = float(match.group(1).replace(",", "."))
                        logger.success(f"💰 Cours de l'or actuel : {price}€")
                        
                        if price > n:
                            send_alert(f"🚀 Alerte Or : Le cours de l'once a dépassé 4400€ ! (Actuel : {price}€)")
                        return price
            logger.warning("⚠️ Impossible de trouver l'élément 'Once d'or' ou 'cotation_amount' dans la page.")
        else:
            logger.error(f"❌ Erreur {response.status_code}: Impossible de récupérer la page du cours de l'or")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la requête du cours de l'or : {e}")
        
    return None


def main_function(url, n):
    """Analyse les produits d'une page donnée et déclenche des alertes si le prix avantageux est inférieur ou égal au seuil n."""
    logger.info("▶️ Début de l'exécution de main_function")
    products = get_products(url)
    for product in products:
        logger.success(f"Produit analysé - Prix : {product.price}€ | LSP : {product.lsp}")
        
        if product.price is not None and product.lsp is True and product.price >= n:
            send_alert(f"⚠️ Alerte : prix avantageux {product.price}€ sur produit LSP !")
            
    logger.info("✅ Fin de l'exécution de main_function")


url_target_1 = "https://www.aucoffre.com/recherche/metal-3/marketing_list-4/stype-171/produit?page="
url_target_2 = "https://www.aucoffre.com/recherche/metal-1/marketing_list-5/stype-1/produit"
url_gold_course = "https://www.aucoffre.com/cours-or"

if __name__ == "__main__":
    check_gold_price(url_gold_course, 4400.0)
    
    time.sleep(random.uniform(1.5, 3.0))
    
    for page in range(1, 3):
        logger.info(f"🔍 Traitement de la page {page} (Cible 1)")
        main_function(f"{url_target_1}{page}", 90.0)        
        
        delai = random.uniform(3.0, 6.0)
        logger.info(f"⏳ Temporisation de {delai:.2f} secondes...")
        time.sleep(delai)
        
        logger.info(f"🔍 Traitement de la page {page} (Cible 2)")
        main_function(f"{url_target_2}", 900.0)
        
        delai_fin_boucle = random.uniform(4.0, 7.0)
        logger.info(f"⏳ Fin de cycle, temporisation de {delai_fin_boucle:.2f} secondes...")
        time.sleep(delai_fin_boucle)
        