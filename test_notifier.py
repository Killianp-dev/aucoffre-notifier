import os
import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

# Assure-toi que ton script principal s'appelle bien "main.py"
from main import Product, get_products, main_function, send_alert

# --- FAUSSES DONNÉES HTML POUR LES TESTS ---

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

# --- TESTS UNITAIRES (SANS RÉSEAU) ---

def test_product_extraction_lsp_cheap():
    """Teste l'extraction d'un produit qui a le badge LSP et un prix valide."""
    soup = BeautifulSoup(HTML_LSP_CHEAP, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price == 85.5
    assert product.lsp is True

def test_product_extraction_no_lsp_expensive():
    """Teste l'extraction d'un produit sans badge LSP."""
    soup = BeautifulSoup(HTML_NO_LSP_EXPENSIVE, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price == 105.0
    assert product.lsp is False

def test_product_extraction_invalid_price():
    """Teste la robustesse si le prix n'est pas un nombre."""
    soup = BeautifulSoup(HTML_INVALID_PRICE, "html.parser")
    product = Product(soup.find("article"))
    
    assert product.price is None
    assert product.lsp is False

@patch("main.save_html_files")  # On empêche l'écriture de fichiers pendant les tests
@patch("main.requests.get")     # On simule la requête HTTP
def test_get_products(mock_get, mock_save):
    """Teste la fonction de récupération des produits en simulant le site web."""
    # Configuration de la fausse réponse
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = HTML_LSP_CHEAP + HTML_NO_LSP_EXPENSIVE
    mock_get.return_value = mock_response

    products = get_products("http://url-de-test.com")
    
    assert len(products) == 2
    assert products[0].price == 85.5
    assert products[1].price == 105.0
    mock_save.assert_called_once() # Vérifie qu'on a bien tenté de sauvegarder les fichiers HTML

@patch("main.get_products")
@patch("main.send_alert")
def test_main_function(mock_send_alert, mock_get_products):
    """Teste la logique d'alerte : on ne doit alerter QUE si LSP=True ET Prix <= 90."""
    # Création de faux produits
    p_trigger = MagicMock(price=85.0, lsp=True)     # Devrait déclencher
    p_expensive = MagicMock(price=95.0, lsp=True)   # Trop cher, ne doit pas déclencher
    p_no_lsp = MagicMock(price=80.0, lsp=False)     # Pas de LSP, ne doit pas déclencher
    
    mock_get_products.return_value = [p_trigger, p_expensive, p_no_lsp]
    
    main_function("http://url-de-test.com")
    
    # Vérification : send_alert ne doit avoir été appelée qu'une seule fois
    assert mock_send_alert.call_count == 1
    # Vérifie que le message d'alerte contenait bien le prix de 85.0€
    assert "85.0" in mock_send_alert.call_args[0][0]

# --- TEST D'INTÉGRATION RÉEL (RÉSEAU + API PUSHOVER) ---

@patch("main.logger.error")
@patch("main.logger.success")
def test_real_pushover_notification(mock_logger_success, mock_logger_error):
    """
    Test RÉEL qui envoie une notification Pushover.
    Vérifie si le .env est bien configuré et si l'API accepte les credentials.
    """
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    
    # Si les variables ne sont pas là, on ignore le test plutôt que de le faire planter
    if not token or not user:
        pytest.skip("⚠️ Les variables PUSHOVER_TOKEN et PUSHOVER_USER ne sont pas définies.")
        
    message = "🧪 Ceci est un test automatisé depuis pytest pour vérifier la configuration de l'API."
    
    # On exécute la vraie fonction
    send_alert(message)
    
    # Comme ta fonction `send_alert` attrape les exceptions avec un try/except et fait un logger.error,
    # on vérifie qu'aucun logger.error n'a été appelé et que logger.success l'a été.
    assert not mock_logger_error.called, "❌ Erreur détectée dans les logs : la configuration de l'API Pushover semble invalide."
    assert mock_logger_success.called, "✅ Le message n'a pas pu être envoyé à Pushover."