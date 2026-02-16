import pytest
from api.workers.harvester import run_search
from api.core.scraper import scrape_ads

def test_scraper_mocked(mocker):
    mock_playwright = mocker.patch('api.core.scraper.sync_playwright')
    mock_browser = mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value

    # Mock response
    mock_page.goto.return_value = None
    
    # We can't easily mock the response event listener logic without refactoring scraper to use a class or injection
    # For now, we test that it attempts to navigate
    
    ads = scrape_ads("test", "CO", 10)
    assert isinstance(ads, list)
    # Since we mocked navigation and no ads were "extracted" from network logs
    assert len(ads) == 0

def test_harvester_task(mocker):
    # Mock scrape_ads
    mocker.patch('api.workers.harvester.scrape_ads', return_value=[{"id": 123, "page_name": "Test"}])
    
    # Mock save_ads (async)
    mock_save = mocker.patch('api.workers.harvester.save_ads')
    mock_save.return_value = None # it's async but called via async_to_sync

    res = run_search("job-id", "query", "CO", 20)
    assert res["status"] == "success"
    assert res["count"] == 1
    mock_save.assert_called_once()
