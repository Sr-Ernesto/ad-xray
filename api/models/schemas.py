from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import List, Optional, Any
from uuid import UUID

# --- Shared Models ---

class AdBase(BaseModel):
    id: int  # ad_archive_id
    page_name: str
    page_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    body_text: Optional[str] = None
    title: Optional[str] = None
    cta: Optional[str] = None
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    country: Optional[str] = None
    query: Optional[str] = None

class AdCreate(AdBase):
    job_id: Optional[UUID] = None
    ad_id_internal: Optional[str] = None
    page_profile_uri: Optional[str] = None
    page_profile_picture_url: Optional[str] = None
    page_like_count: Optional[int] = None
    page_categories: Optional[List[str]] = None
    cta_type: Optional[str] = None
    link_description: Optional[str] = None
    publisher_platform: Optional[List[str]] = None
    byline: Optional[str] = None
    card_count: int = 0
    s3_link: Optional[str] = None
    funnel_type: Optional[str] = None
    funnel_confidence: Optional[float] = None
    funnel_signals: Optional[dict] = None
    landing_page_url: Optional[str] = None
    ai_analysis: Optional[dict] = None

class AdResponse(AdCreate):
    scraped_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Job Models ---

class JobCreate(BaseModel):
    query: str
    country: str = "CO"
    max_count: int = 20

class JobResponse(JobCreate):
    id: UUID
    status: str
    ads_found: int
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
