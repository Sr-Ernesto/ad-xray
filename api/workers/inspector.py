import asyncio
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from api.workers.celery_app import celery_app
from api.core.signals import Signals
from api.database import get_db_connection
from playwright.sync_api import sync_playwright

logger = get_task_logger(__name__)

async def update_ad_inspection(ad_id: int, funnel_type: str, confidence: float, signals: dict, final_url: str):
    async with get_db_connection() as conn:
        await conn.execute("""
            UPDATE ads
            SET funnel_type = $1,
                funnel_confidence = $2,
                funnel_signals = $3,
                landing_page_url = $4
            WHERE id = $5
        """, funnel_type, confidence, signals, final_url, ad_id)

@celery_app.task(name="api.workers.inspector.inspect_ad")
def inspect_ad(ad_id: int, url: str):
    if not url:
        return {"status": "skipped", "reason": "no_url"}
    
    logger.info(f"Inspecting Ad {ad_id}: {url}")
    
    final_url = url
    html_content = ""
    
    # 1. Navigate with Playwright to get final URL and HTML
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                final_url = page.url
                html_content = page.content()
            except Exception as e:
                logger.warning(f"Navigation error for {url}: {e}")
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return {"status": "failed", "error": str(e)}

    # 2. Analyze Signals
    cod_res = Signals.check_cod(html_content, html_content) # Check both text and html
    hotmart_res = Signals.check_hotmart(final_url, html_content, html_content)
    whatsapp_res = Signals.check_whatsapp(final_url, html_content)
    
    # 3. Determine Funnel Type & Confidence
    funnel_type = "unknown"
    confidence = 0.0
    signals_found = {
        "cod": cod_res,
        "hotmart": hotmart_res,
        "whatsapp": whatsapp_res
    }
    
    if hotmart_res["found"]:
        funnel_type = "hotmart"
        confidence = 0.9 if hotmart_res["url_match"] else 0.6
    elif cod_res["found"]:
        funnel_type = "cod"
        confidence = 0.8 if len(cod_res["keywords"]) > 1 else 0.5
    elif whatsapp_res["found"]:
        funnel_type = "whatsapp"
        confidence = 0.9
    elif "shopify" in html_content.lower():
        funnel_type = "shopify"
        confidence = 0.7

    # 4. Save results
    async_to_sync(update_ad_inspection)(ad_id, funnel_type, confidence, signals_found, final_url)
    
    return {
        "ad_id": ad_id,
        "funnel_type": funnel_type,
        "confidence": confidence,
        "final_url": final_url
    }
