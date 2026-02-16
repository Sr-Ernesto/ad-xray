import pytest
from api.core.signals import Signals

def test_cod_signals():
    html = "<html><body><p>Enviamos con pago contra entrega</p></body></html>"
    res = Signals.check_cod(html)
    assert res["found"] is True
    assert "pago contra entrega" in res["keywords"]

def test_hotmart_signals():
    url = "https://pay.hotmart.com/checkout"
    html = "<html><body></body></html>"
    res = Signals.check_hotmart(url, html)
    assert res["found"] is True
    assert res["url_match"] is True

def test_whatsapp_signals():
    url = "https://wa.me/573001234567"
    res = Signals.check_whatsapp(url)
    assert res["found"] is True

def test_whatsapp_link_in_html():
    html = "<html><body>Contact us on <a href='wa.link/abc'>WhatsApp</a></body></html>"
    res = Signals.check_whatsapp("http://mysite.com", html)
    assert res["found"] is True

def test_cod_multiline_text():
    text = "Oferta especial\nEnviamos gratis\nPago contra entrega disponible"
    res = Signals.check_cod(text)
    assert res["found"] is True
    assert "pago contra entrega" in res["keywords"]

def test_hotmart_affiliate_pattern():
    url = "https://go.hotmart.com/A1234567Z"
    res = Signals.check_hotmart(url, "")
    assert res["found"] is True
    assert res["url_match"] is True

def test_no_signals():
    html = "<html><body><p>Blog post about cats</p></body></html>"
    res_cod = Signals.check_cod(html)
    res_hm = Signals.check_hotmart("http://blog.com", html)
    
    assert res_cod["found"] is False
    assert res_hm["found"] is False
