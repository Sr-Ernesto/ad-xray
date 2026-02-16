import os
import boto3
import requests
import yt_dlp
from pathlib import Path
from celery.utils.log import get_task_logger
from api.workers.celery_app import celery_app
from api.config import settings
from api.database import SessionLocal
from sqlalchemy import text

logger = get_task_logger(__name__)

# MinIO Config
def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1"
    )

TEMP_DIR = Path("/tmp/ad-xray/creatives")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest_path: Path):
    ydl_opts = {
        'outtmpl': str(dest_path),
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }
    
    if "fbcdn" in url or "scontent" in url:
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except: pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.error(f"Download failed {url}: {e}")
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except:
            return False

@celery_app.task(name="api.workers.downloader.download_media_task")
def download_media_task(ad_id: int):
    logger.info(f"Downloading media for Ad {ad_id}")
    db = SessionLocal()
    
    try:
        result = db.execute(text("SELECT image_url, video_url FROM ads WHERE id = :id"), {"id": ad_id}).fetchone()
        if not result:
            return {"status": "not_found"}
            
        image_url, video_url = result
        media_url = video_url or image_url
        if not media_url:
            return {"status": "no_url"}
            
        is_video = bool(video_url)
        ext = "mp4" if is_video else "jpg"
        filename = f"{ad_id}.{ext}"
        local_path = TEMP_DIR / filename
        
        if download_file(media_url, local_path):
            s3 = get_s3_client()
            content_type = 'video/mp4' if is_video else 'image/jpeg'
            
            try:
                s3.upload_file(
                    str(local_path), 
                    settings.MINIO_BUCKET, 
                    filename,
                    ExtraArgs={'ContentType': content_type}
                )
                s3_link = f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{filename}"
                
                db.execute(text("UPDATE ads SET s3_link = :link WHERE id = :id"), {"link": s3_link, "id": ad_id})
                db.commit()
                
                if local_path.exists():
                    os.remove(local_path)
                
                return {"status": "success", "s3_link": s3_link}
            except Exception as e:
                logger.error(f"S3 Upload failed: {e}")
                return {"status": "upload_failed", "error": str(e)}
        else:
            return {"status": "download_failed"}
                    
    except Exception as e:
        logger.error(f"Media processing failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
