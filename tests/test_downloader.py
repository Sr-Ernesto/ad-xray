import pytest
from api.workers.downloader import download_media_task
from unittest.mock import MagicMock, patch
from pathlib import Path

def test_downloader_task(mocker):
    # Mock DB
    mock_db = mocker.patch('api.workers.downloader.SessionLocal')
    mock_session = mock_db.return_value
    mock_session.execute.return_value.fetchone.return_value = ("http://img.url", "http://vid.url")
    
    # Mock download_file
    mocker.patch('api.workers.downloader.download_file', return_value=True)
    
    # Mock S3
    mock_s3 = mocker.patch('api.workers.downloader.get_s3_client')
    mock_s3_instance = mock_s3.return_value
    
    # Mock os.remove and Path.exists
    mocker.patch('os.remove')
    mocker.patch('api.workers.downloader.Path.exists', return_value=True)

    # Note: Call .run() to bypass celery wrapper during testing
    download_media_task.run(123)
    
    assert mock_session.execute.called
    assert mock_s3_instance.upload_file.called
    mock_session.commit.assert_called_once()

def test_downloader_no_media(mocker):
    mock_db = mocker.patch('api.workers.downloader.SessionLocal')
    mock_session = mock_db.return_value
    mock_session.execute.return_value.fetchone.return_value = (None, None)
    
    res = download_media_task.run(456)
    
    assert res["status"] == "no_url"
