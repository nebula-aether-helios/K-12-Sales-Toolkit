import os
import pytest
from catalog_api.fetchers import arcgis_fetcher, github_fetcher


@pytest.mark.skipif(os.getenv('RUN_LIVE_TESTS') != '1', reason='Live tests disabled')
def test_arcgis_live_sample():
    # use a known LA County service from the repo CSV
    url = 'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer'
    meta = arcgis_fetcher.fetch_metadata(url)
    assert meta.get('title') is not None
    pv = arcgis_fetcher.fetch_preview(url, n=3)
    assert isinstance(pv, list)


@pytest.mark.skipif(os.getenv('RUN_LIVE_TESTS') != '1', reason='Live tests disabled')
def test_github_live_sample():
    repos = github_fetcher.list_org_repos('https://github.com/OSHADataDoor')
    assert isinstance(repos, list)
