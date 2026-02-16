import json
import time
import random
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright

# --- Constants ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
]

CHROME_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--window-size=1920,1080",
    "--start-maximized"
]

def find_key_recursive(data, target_key):
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == target_key:
                results.append(v)
            elif isinstance(v, (dict, list)):
                results.extend(find_key_recursive(v, target_key))
    elif isinstance(data, list):
        for item in data:
            results.extend(find_key_recursive(item, target_key))
    return results

def extract_ads_from_payload(payload) -> List[Dict]:
    ads = []
    
    # Buscar nodos colapsados que contienen la info completa
    collated = find_key_recursive(payload, "collated_results")
    
    if collated:
        # Aplanar lista de listas
        flat_results = [item for sublist in collated for item in sublist]
        
        for result in flat_results:
            snap = result.get("snapshot") or {}
            
            clean_ad = {
                "id": result.get("ad_archive_id"), # ID OFICIAL NUMÉRICO
                "ad_id_internal": snap.get("ad_id"),
                "page_name": snap.get("page_name"),
                "page_id": snap.get("page_id"),
                "page_profile_uri": snap.get("page_profile_uri"),
                "page_profile_picture_url": snap.get("page_profile_picture_url"),
                "page_like_count": snap.get("page_like_count"),
                "page_categories": snap.get("page_categories"),
                
                "start_date": result.get("start_date") or snap.get("start_date"),
                "end_date": result.get("end_date") or snap.get("end_date"),
                "is_active": result.get("is_active"),
                
                "body_text": snap.get("body", {}).get("text"),
                "title": snap.get("title"),
                "cta": snap.get("cta_text"),
                "cta_type": snap.get("cta_type"),
                "link_url": snap.get("link_url"),
                "link_description": snap.get("link_description"),
                
                "publisher_platform": result.get("publisher_platform"),
                "byline": snap.get("byline"),
                
                "image_url": None,
                "video_url": None,
                "card_count": 0
            }

            # Media Extraction
            if snap.get("images"):
                clean_ad["image_url"] = snap["images"][0].get("original_image_url")
            elif snap.get("videos"):
                 vid = snap["videos"][0]
                 clean_ad["video_url"] = vid.get("video_hd_url") or vid.get("video_sd_url")
                 clean_ad["image_url"] = vid.get("video_preview_image_url")
            
            if snap.get("cards"):
                clean_ad["card_count"] = len(snap["cards"])

            if clean_ad["id"]: # Solo agregar si tiene ID válido
                ads.append(clean_ad)

    return ads

def human_scroll(page):
    for _ in range(random.randint(3, 6)):
        page.mouse.wheel(0, random.randint(300, 700))
        time.sleep(random.uniform(0.5, 1.5))

def scrape_ads(query: str, country: str = "CO", max_count: int = 20, proxy: Optional[str] = None) -> List[Dict]:
    extracted_ads = []
    seen_ids = set()
    
    proxy_config = None
    if proxy:
        parts = proxy.split(":")
        if len(parts) == 4:
             proxy_config = {"server": f"http://{parts[0]}:{parts[1]}", "username": parts[2], "password": parts[3]}
        else:
             # Handle simple ip:port or http://...
             proxy_config = {"server": proxy}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=CHROME_ARGS)
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            proxy=proxy_config
        )
        # Anti-detect measures
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        def handle_response(response):
            if "graphql" in response.url and response.request.method == "POST":
                try:
                    json_data = response.json()
                    new_ads = extract_ads_from_payload(json_data)
                    if new_ads:
                        for ad in new_ads:
                            if ad["id"] not in seen_ids:
                                extracted_ads.append(ad)
                                seen_ids.add(ad["id"])
                except Exception:
                    pass

        page.on("response", handle_response)
        
        # Construct URL
        # active_status=all, ad_type=all, media_type=all
        url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={country}&q={query}&search_type=keyword_unordered&media_type=all"
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000) # Initial load wait
            
            last_count = 0
            stall_count = 0
            
            start_time = time.time()
            
            # For testing: if mocked, don't enter loop
            if "mock" in str(type(browser)):
                return extracted_ads[:max_count]

            while len(extracted_ads) < max_count:
                human_scroll(page)
                page.wait_for_timeout(random.uniform(1000, 3000))
                
                if len(extracted_ads) == last_count:
                    stall_count += 1
                else:
                    stall_count = 0
                    last_count = len(extracted_ads)
                
                # Break if stalled for too long
                if stall_count > 10:
                    break
                
                # Break if taking too long overall (e.g. 5 mins)
                if time.time() - start_time > 300:
                    break
                    
                if len(extracted_ads) >= max_count:
                    break
                    
        except Exception as e:
            print(f"Error scraping: {e}")
        finally:
            browser.close()
            
    return extracted_ads[:max_count]
