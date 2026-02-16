import asyncio
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from api.workers.celery_app import celery_app
from api.core.scraper import scrape_ads
from api.database import get_db_connection
from api.models.schemas import AdCreate
from datetime import datetime
from uuid import UUID

logger = get_task_logger(__name__)

async def save_ads(job_id: str, ads: list[dict]):
    async with get_db_connection() as conn:
        job_uuid = UUID(job_id)
        
        # Prepare batch insert
        # Simplification: Insert individually for MVP to handle conflicts easily
        # Production: Use executemany or copy_records_to_table
        
        saved_count = 0
        for ad_data in ads:
            # Add job_id reference
            ad_data["job_id"] = job_uuid
            
            # Convert date strings to objects if needed (scraper might return strings)
            # Assuming scraper returns strings like '2023-01-01' or None
            
            # Map Pydantic model to dict for validation
            try:
                # Basic cleanup
                if "id" in ad_data and isinstance(ad_data["id"], str):
                     ad_data["id"] = int(ad_data["id"])

                ad_obj = AdCreate(**ad_data)
                
                # Upsert
                await conn.execute("""
                    INSERT INTO ads (
                        id, ad_id_internal, page_name, page_id, page_profile_uri,
                        page_profile_picture_url, page_like_count, page_categories,
                        start_date, end_date, is_active,
                        body_text, title, cta, cta_type, link_url, link_description,
                        publisher_platform, byline,
                        image_url, video_url, card_count,
                        job_id, scraped_at
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8,
                        $9, $10, $11,
                        $12, $13, $14, $15, $16, $17,
                        $18, $19,
                        $20, $21, $22,
                        $23, NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        is_active = EXCLUDED.is_active,
                        end_date = EXCLUDED.end_date,
                        scraped_at = NOW(),
                        job_id = EXCLUDED.job_id
                """,
                ad_obj.id, ad_obj.ad_id_internal, ad_obj.page_name, ad_obj.page_id, ad_obj.page_profile_uri,
                ad_obj.page_profile_picture_url, ad_obj.page_like_count, ad_obj.page_categories,
                ad_obj.start_date, ad_obj.end_date, ad_obj.is_active,
                ad_obj.body_text, ad_obj.title, ad_obj.cta, ad_obj.cta_type, ad_obj.link_url, ad_obj.link_description,
                ad_obj.publisher_platform, ad_obj.byline,
                ad_obj.image_url, ad_obj.video_url, ad_obj.card_count,
                ad_obj.job_id
                )
                saved_count += 1
                
                # Trigger Inspector for this ad
                # Avoid circular import, import inside function if needed or rely on Celery name
                celery_app.send_task("api.workers.inspector.inspect_ad", args=[ad_obj.id, ad_obj.link_url])

            except Exception as e:
                logger.error(f"Error saving ad {ad_data.get('id')}: {e}")

        # Update Job status
        await conn.execute("""
            UPDATE scrape_jobs
            SET status = 'completed',
                ads_found = $1,
                completed_at = NOW()
            WHERE id = $2
        """, saved_count, job_uuid)

@celery_app.task(name="api.workers.harvester.run_search")
def run_search(job_id: str, query: str, country: str, max_count: int):
    logger.info(f"Starting search job {job_id} for '{query}' in {country}")
    
    try:
        # 1. Scrape
        ads = scrape_ads(query, country, max_count)
        logger.info(f"Scraped {len(ads)} ads")
        
        # 2. Save to DB (async wrapper)
        async_to_sync(save_ads)(job_id, ads)
        
        return {"status": "success", "count": len(ads)}
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        # Update Job status to failed
        async def mark_failed():
            async with get_db_connection() as conn:
                await conn.execute("""
                    UPDATE scrape_jobs
                    SET status = 'failed',
                        error = $1,
                        completed_at = NOW()
                    WHERE id = $2
                """, str(e), UUID(job_id))
        async_to_sync(mark_failed)()
        raise e
