import pytest
from api.workers.inspector import inspect_ad

def test_inspector_cod(mocker):
    # Mock Playwright
    mock_playwright = mocker.patch('api.workers.inspector.sync_playwright')
    mock_page = mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value.new_page.return_value
    mock_page.content.return_value = "<html><body><h1>Pago Contra Entrega</h1></body></html>"
    mock_page.url = "https://example.com/product"
    
    # Mock DB update
    mock_update = mocker.patch('api.workers.inspector.update_ad_inspection')
    mock_update.return_value = None

    res = inspect_ad(123, "http://ad.url")
    
    assert res["funnel_type"] == "cod"
    assert res["confidence"] >= 0.5
    mock_update.assert_called_once()

def test_inspector_hotmart(mocker):
    # Mock Playwright
    mock_playwright = mocker.patch('api.workers.inspector.sync_playwright')
    mock_page = mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value.new_page.return_value
    mock_page.content.return_value = "<html><body><h1>Curso Online</h1></body></html>"
    mock_page.url = "https://pay.hotmart.com/XYZ"
    
    # Mock DB update
    mock_update = mocker.patch('api.workers.inspector.update_ad_inspection')
    mock_update.return_value = None

    res = inspect_ad(123, "http://ad.url")
    
    assert res["funnel_type"] == "hotmart"
    assert res["confidence"] >= 0.9
    mock_update.assert_called_once()
