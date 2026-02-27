import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from bs4 import BeautifulSoup
import requests

# On importe les fonctions et classes depuis ton script principal (main.py)
from main import Product, save_html_files, get_products, send_alert, main_function

# --- TESTS POUR LA CLASSE Product ---

def test_product_extract_prime_with_comma():
    """Teste l'extraction d'une prime formatée avec une virgule."""
    html = '<article><span class="text-bold">Prime de 18,5% sur ce produit</span></article>'
    soup = BeautifulSoup(html, "html.parser").article
    product = Product(soup)
    assert product.prime == 18.5
    assert product.lsp is False

def test_product_extract_prime_with_dot():
    """Teste l'extraction d'une prime formatée avec un point."""
    html = '<article><span class="text-bold">Prime : 10.2%</span></article>'
    soup = BeautifulSoup(html, "html.parser").article
    product = Product(soup)
    assert product.prime == 10.2

def test_product_no_prime():
    """Teste le comportement si aucune prime n'est trouvée."""
    html = '<article><span class="text-bold">Pas de prime ici</span></article>'
    soup = BeautifulSoup(html, "html.parser").article
    product = Product(soup)
    assert product.prime is None

def test_product_has_lsp():
    """Teste la détection du tag LSP."""
    html = '<article><div class="ribbon">Produit LSP Exclusif</div></article>'
    soup = BeautifulSoup(html, "html.parser").article
    product = Product(soup)
    assert product.lsp is True

def test_product_no_lsp():
    """Teste le comportement si le tag LSP est absent."""
    html = '<article><div class="ribbon">Produit Standard</div></article>'
    soup = BeautifulSoup(html, "html.parser").article
    product = Product(soup)
    assert product.lsp is False


# --- TESTS POUR save_html_files ---

@patch("builtins.open", new_callable=mock_open)
def test_save_html_files(mock_file):
    """Teste que les fichiers sont bien créés et écrits sans écrire réellement sur le disque."""
    html_content = "<html><body>Test</body></html>"
    soup = BeautifulSoup(html_content, "html.parser")
    
    save_html_files(html_content, soup)
    
    # Vérifie que la fonction open a été appelée deux fois (pour RAW et FORMATE)
    assert mock_file.call_count == 2


# --- TESTS POUR get_products ---

@patch("main.requests.get")
@patch("main.save_html_files")
def test_get_products_success(mock_save, mock_get):
    """Teste la récupération réussie des produits."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = '''
        <article class="product-card">
            <span class="text-bold">15,0%</span>
            <div class="ribbon">LSP</div>
        </article>
    '''
    
    products = get_products("http://fake-url.com")
    
    assert len(products) == 1
    assert products[0].prime == 15.0
    assert products[0].lsp is True
    mock_save.assert_called_once() # Vérifie qu'on a bien sauvegardé les HTML

@patch("main.requests.get")
def test_get_products_failure(mock_get):
    """Teste le comportement en cas d'erreur HTTP (ex: 404 ou 500)."""
    mock_get.return_value.status_code = 404
    products = get_products("http://fake-url.com")
    assert products == []


# --- TESTS POUR send_alert (Pushover) ---

@patch.dict(os.environ, {"PUSHOVER_TOKEN": "fake_token", "PUSHOVER_USER": "fake_user"})
@patch("main.requests.post")
def test_send_alert_success(mock_post):
    """Teste l'envoi d'une alerte avec succès."""
    mock_response = MagicMock()
    mock_post.return_value = mock_response
    
    send_alert("Test Alert")
    
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()

@patch.dict(os.environ, {"PUSHOVER_TOKEN": "fake_token", "PUSHOVER_USER": "fake_user"})
@patch("main.requests.post")
def test_send_alert_params_check(mock_post):
    """Vérifie que les bons paramètres sont envoyés à l'API Pushover."""
    mock_post.return_value = MagicMock()
    message = "⚠️ Alerte : prime 15.0% LSP !"
    
    send_alert(message)
    
    # Vérification de l'URL et des paramètres postés
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.pushover.net/1/messages.json"
    assert kwargs["data"]["token"] == "fake_token"
    assert kwargs["data"]["user"] == "fake_user"
    assert kwargs["data"]["message"] == message

@patch.dict(os.environ, {"PUSHOVER_TOKEN": "fake_token", "PUSHOVER_USER": "fake_user"})
@patch("main.requests.post")
def test_send_alert_failure(mock_post):
    """Teste l'envoi d'une alerte qui échoue (lève une exception)."""
    mock_post.side_effect = requests.RequestException("API down")
    
    # La fonction gère l'exception via try/except, donc elle ne doit pas faire crasher le test
    send_alert("Test Alert")
    mock_post.assert_called_once()


# --- TESTS POUR main_function ---

@patch("main.get_products")
@patch("main.send_alert")
def test_main_function_triggers_alert(mock_alert, mock_get_products):
    """Teste que l'alerte est déclenchée pour un produit correspondant aux critères (LSP + Prime <= 18.9)."""
    # Création d'un mock de produit qui remplit les conditions
    mock_product = MagicMock()
    mock_product.prime = 18.5
    mock_product.lsp = True
    
    mock_get_products.return_value = [mock_product]
    
    main_function("http://fake-url.com")
    
    mock_alert.assert_called_once_with("⚠️ Alerte : prime 18.5% LSP !")

@patch("main.get_products")
@patch("main.send_alert")
def test_main_function_no_alert_prime_too_high(mock_alert, mock_get_products):
    """Teste que l'alerte n'est pas déclenchée si la prime est > 18.9."""
    mock_product = MagicMock()
    mock_product.prime = 19.0
    mock_product.lsp = True
    
    mock_get_products.return_value = [mock_product]
    
    main_function("http://fake-url.com")
    
    mock_alert.assert_not_called()

@patch("main.get_products")
@patch("main.send_alert")
def test_main_function_no_alert_no_lsp(mock_alert, mock_get_products):
    """Teste que l'alerte n'est pas déclenchée si ce n'est pas un produit LSP."""
    mock_product = MagicMock()
    mock_product.prime = 15.0
    mock_product.lsp = False
    
    mock_get_products.return_value = [mock_product]
    
    main_function("http://fake-url.com")
    
    mock_alert.assert_not_called()
