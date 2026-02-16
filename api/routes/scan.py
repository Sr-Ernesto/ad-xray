from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.models.schemas import JobCreate, JobResponse
from api.database import get_db_connection
from api.workers.celery_app import celery_app
from uuid import uuid4

router = APIRouter()

@router.post("/scan", response_model=JobResponse, status_code=201)
async def create_scan_job(job_in: JobCreate, background_tasks: BackgroundTasks):
    job_id = uuid4()
    
    query = "INSERT INTO scrape_jobs (id, query, country, max_count, status) VALUES ($1, $2, $3, $4, 'pending') RETURNING *"
    
    async with get_db_connection() as conn:
        row = await conn.fetchrow(query, job_id, job_in.query, job_in.country, job_in.max_count)
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create job")
            
        # Dispatch Celery Task
        celery_app.send_task(
            "api.workers.harvester.run_search",
            args=[str(job_id), job_in.query, job_in.country, job_in.max_count]
        )
        
        return JobResponse(**dict(row))
