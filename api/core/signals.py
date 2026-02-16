
class Signals:
    COD_KEYWORDS = [
        "pago contra entrega", "contraentrega", "pago al recibir",
        "paga cuando recibas", "COD", "cash on delivery",
        "envío gratis", "sin tarjeta", "pago en efectivo",
        "recibe y paga", "paga al recibir tu pedido",
        "pagar na entrega", "frete grátis", "pagamento na entrega"
    ]
    
    COD_TECH = [
        "tiendanube.com", "vtex.com", "shopify.com",
        "woocommerce", "dropi.co", "lojadoafiliado"
    ]
    
    HOTMART_URLS = [
        "hotmart.com", "go.hotmart.com", "pay.hotmart.com",
        "kiwify.com", "eduzz.com", "monetizze.com"
    ]
    
    HOTMART_KEYWORDS = [
        "comprar agora", "inscríbete", "acceso inmediato",
        "garantía de", "días de garantía", "curso online",
        "método comprobado", "clase gratis", "masterclass",
        "webinar", "oferta limitada", "cupos limitados"
    ]
    
    WHATSAPP_PATTERNS = [
        "wa.me/", "api.whatsapp.com", "whatsapp.com/send",
        "wa.link/", "bit.ly/" # Often redirects to WA
    ]

    @classmethod
    def check_cod(cls, text: str, html: str = "") -> dict:
        found = []
        text_lower = text.lower()
        html_lower = html.lower()
        
        for kw in cls.COD_KEYWORDS:
            if kw in text_lower or kw in html_lower:
                found.append(kw)
        
        return {"found": bool(found), "keywords": found}

    @classmethod
    def check_hotmart(cls, url: str, text: str, html: str = "") -> dict:
        found_url = any(u in url for u in cls.HOTMART_URLS)
        found_kws = []
        text_lower = text.lower()
        html_lower = html.lower()

        for kw in cls.HOTMART_KEYWORDS:
            if kw in text_lower or kw in html_lower:
                found_kws.append(kw)
        
        return {"found": found_url or bool(found_kws), "url_match": found_url, "keywords": found_kws}

    @classmethod
    def check_whatsapp(cls, url: str, html: str = "") -> dict:
        found = any(p in url for p in cls.WHATSAPP_PATTERNS) or "whatsapp" in html.lower()
        return {"found": found}
