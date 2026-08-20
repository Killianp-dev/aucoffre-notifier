import os
import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from main import Product, get_products, main_function, send_alert, check_gold_price

# --- FAUSSES DONNÉES HTML POUR LES TESTS DES PRODUITS ---

HTML_LSP_CHEAP = """
<article class="product-card">
    <div class="ribbon">LSP</div>
    <p class="text-xlarge text-bolder">85,50 &nbsp;€</p>
</article>
"""

HTML_NO_LSP_EXPENSIVE = """
<article class="product-card">
    <p class="text-xlarge text-bolder">105.00 €</p>
</article>
"""

HTML_INVALID_PRICE = """
<article class="product-card">
    <p class="text-xlarge text-bolder">Prix sur demande</p>
</article>
"""

# --- FAUSSES DONNÉES HTML POUR LES TESTS DU COURS DE L'OR ---

HTML_GOLD_CHEAP = """
<table>
    <tr>
        <td class="cotation_name">Once d'or</td>
        <td class="cotation_amount">4 470,66 €</td>
    </tr>
</table>
"""

HTML_GOLD_EXPENSIVE = """
<table>
    <tr>
        <td class="cotation_name">Once d'or</td>
        <td class="cotation_amount">4 650,50 &nbsp;€</td>
    </tr>
</table>
"""

HTML_GOLD_NOT_FOUND = """
<table>
    <tr>
        <td class="cotation_name">Argent</td>
        <td class="cotation_amount">30,00 €</td>
    </tr>
</table>
"""


# --- TESTS UNITAIRES (PRODUITS) ---

def test_product_extraction_lsp_cheap():
    """Initialise une instance de Produit et teste l'extraction d'un badge LSP et d'un prix valide."""
    soup = BeautifulSoup(HTML_LSP_CHEAP, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price == 85.5
    assert product.lsp is True

def test_product_extraction_no_lsp_expensive():
    """Initialise une instance de Produit et teste l'extraction sans badge LSP."""
    soup = BeautifulSoup(HTML_NO_LSP_EXPENSIVE, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price == 105.0
    assert product.lsp is False

def test_product_extraction_invalid_price():
    """Initialise une instance de Produit et teste la robustesse de l'extraction si le prix n'est pas un nombre."""
    soup = BeautifulSoup(HTML_INVALID_PRICE, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price is None
    assert product.lsp is False

@patch("main.save_html_files")
@patch("main.requests.get")
def test_get_products(mock_get, mock_save):
    """Effectue une fausse requête sur l'URL ciblée et valide le retour d'une liste d'objets Product."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = HTML_LSP_CHEAP + HTML_NO_LSP_EXPENSIVE
    mock_get.return_value = mock_response

    products = get_products("http://url-de-test.com")
    
    assert len(products) == 2
    assert products[0].price == 85.5
    assert products[1].price == 105.0
    mock_save.assert_called_once()

@patch("main.get_products")
@patch("main.send_alert")
def test_main_function(mock_send_alert, mock_get_products):
    """Analyse la logique de main_function : l'alerte doit se déclencher uniquement si LSP=True ET Prix >= n."""
    p_trigger = MagicMock(price=95.0, lsp=True)     # Devrait déclencher (>= 90.0)
    p_cheap = MagicMock(price=85.0, lsp=True)       # Trop bas, ne doit pas déclencher (< 90.0)
    p_no_lsp = MagicMock(price=100.0, lsp=False)    # Pas de LSP, ne doit pas déclencher
    
    mock_get_products.return_value = [p_trigger, p_cheap, p_no_lsp]
    
    # Appel de la fonction avec un seuil n = 90.0
    main_function("http://url-de-test.com", 90.0)
    
    assert mock_send_alert.call_count == 1
    assert "95.0" in mock_send_alert.call_args[0][0]


# --- TESTS UNITAIRES (COURS DE L'OR) ---

@patch("main.send_alert")
@patch("main.requests.get")
def test_check_gold_price_below_threshold(mock_get, mock_send_alert):
    """Extrait le cours de l'once d'or simulé en deçà du palier limite n (aucune alerte attendue)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = HTML_GOLD_CHEAP
    mock_get.return_value = mock_response

    # Appel de la fonction avec un seuil n = 4500.0
    price = check_gold_price("http://url-de-test.com", 4500.0)
    
    assert price == 4470.66
    mock_send_alert.assert_not_called()

@patch("main.send_alert")
@patch("main.requests.get")
def test_check_gold_price_above_threshold(mock_get, mock_send_alert):
    """Extrait le cours de l'once d'or simulé au-delà du palier limite n (alerte attendue)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = HTML_GOLD_EXPENSIVE
    mock_get.return_value = mock_response

    # Appel de la fonction avec un seuil n = 4600.0
    price = check_gold_price("http://url-de-test.com", 4600.0)
    
    assert price == 4650.50
    mock_send_alert.assert_called_once()
    assert "4650.5" in mock_send_alert.call_args[0][0]
    assert "4600" in mock_send_alert.call_args[0][0]

@patch("main.send_alert")
@patch("main.requests.get")
def test_check_gold_price_not_found(mock_get, mock_send_alert):
    """Teste la robustesse si l'élément HTML 'Once d'or' est introuvable."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = HTML_GOLD_NOT_FOUND
    mock_get.return_value = mock_response

    price = check_gold_price("http://url-de-test.com", 4400.0)
    
    assert price is None
    mock_send_alert.assert_not_called()


# --- TEST D'INTÉGRATION RÉEL (RÉSEAU + API PUSHOVER) ---

@patch("main.logger.error")
@patch("main.logger.success")
def test_real_pushover_notification(mock_logger_success, mock_logger_error):
    """
    Transmet une notification de test sur l'API Pushover pour vérifier la validité des variables d'environnement.
    """
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    
    if not token or not user:
        pytest.skip("⚠️ Les variables PUSHOVER_TOKEN et PUSHOVER_USER ne sont pas définies.")
        
    message = "🧪 Ceci est un test automatisé depuis pytest pour vérifier la configuration de l'API."
    
    send_alert(message)
    
    assert not mock_logger_error.called, "❌ Erreur détectée dans les logs : la configuration de l'API Pushover semble invalide."
    assert mock_logger_success.called, "✅ Le message n'a pas pu être envoyé à Pushover."