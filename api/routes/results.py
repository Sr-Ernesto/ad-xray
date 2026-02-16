from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import get_db
from api.models.schemas import AdBase, JobResponse
from typing import List, Optional

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM scrape_jobs ORDER BY created_at DESC OFFSET :skip LIMIT :limit"), {"skip": skip, "limit": limit}).mappings().all()
    return result

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM scrape_jobs WHERE id = :id"), {"id": job_id}).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result

@router.get("/ads", response_model=List[AdBase])
def list_ads(
    skip: int = 0, 
    limit: int = 20, 
    job_id: Optional[str] = None, 
    funnel_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = "SELECT * FROM ads"
    params = {"skip": skip, "limit": limit}
    conditions = []
    
    if job_id:
        conditions.append("job_id = :job_id")
        params["job_id"] = job_id
        
    if funnel_type:
        conditions.append("funnel_type = :funnel_type")
        params["funnel_type"] = funnel_type
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY scraped_at DESC OFFSET :skip LIMIT :limit"
    
    result = db.execute(text(query), params).mappings().all()
    return result

@router.get("/ads/{ad_id}", response_model=AdBase)
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM ads WHERE id = :id"), {"id": ad_id}).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Ad not found")
    return result
