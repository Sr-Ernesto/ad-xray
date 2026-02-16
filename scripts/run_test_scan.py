from api.workers.celery_app import celery_app
from uuid import uuid4
import asyncio
from api.database import init_db_pool, close_db_pool, get_db_connection
import sys

async def run_test_scan(query: str, country: str = "CO", max_count: int = 5):
    job_id = uuid4()
    print(f"🚀 Creating test scan job: ID={job_id}, Query='{query}', Country='{country}'")

    await init_db_pool()
    try:
        async with get_db_connection() as conn:
            insert_query = """
                INSERT INTO scrape_jobs (id, query, country, max_count, status) 
                VALUES ($1, $2, $3, $4, 'pending') 
                RETURNING *
            """
            row = await conn.fetchrow(insert_query, job_id, query, country, max_count)
            
            if not row:
                print("❌ Failed to create job in database.")
                return

            print(f"✅ Job created in database. Status: {row['status']}")
            
            # Dispatch Celery Task
            task_name = "api.workers.harvester.run_search"
            print(f"📡 Sending task to Celery: {task_name}...")
            
            res = celery_app.send_task(
                task_name,
                args=[str(job_id), query, country, max_count]
            )
            
            print(f"✅ Task dispatched. Celery Task ID: {res.id}")
            print(f"💡 Monitor workers or check DB for results.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await close_db_pool()

if __name__ == "__main__":
    query_param = sys.argv[1] if len(sys.argv) > 1 else "dropshipping"
    asyncio.run(run_test_scan(query_param))
