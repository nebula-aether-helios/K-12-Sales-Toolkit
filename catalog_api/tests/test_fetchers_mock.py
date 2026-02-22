import json
import pytest
from catalog_api.fetchers import arcgis_fetcher, github_fetcher, ckan_fetcher, socrata_fetcher


def test_arcgis_fetcher_service_and_layer(respx_mock):
    service = "https://example.com/arcgis/rest/services/TestService/FeatureServer"
    svc_json = {"layers": [{"id": 0}], "serviceName": "TestService"}
    layer_json = {"fields": [{"name": "OBJECTID", "type": "esriFieldTypeInteger"}], "name": "Layer0"}
    query_json = {"features": [{"attributes": {"OBJECTID": 1}}]}

    respx_mock.get(service + "?f=json").respond(200, json=svc_json)
    respx_mock.get(service + "/0?f=json").respond(200, json=layer_json)
    respx_mock.get(service + "/0/query").respond(200, json=query_json)

    meta = arcgis_fetcher.fetch_metadata(service)
    assert meta.get("title") in ("Layer0", "TestService")
    pv = arcgis_fetcher.fetch_preview(service, n=2)
    assert isinstance(pv, list)
    assert pv and pv[0].get("OBJECTID") == 1


def test_github_fetcher_org_and_contents(respx_mock):
    org_api = "https://api.github.com/orgs/OSHADataDoor/repos"
    repos = [{"full_name": "OSHADataDoor/RepoA"}, {"full_name": "OSHADataDoor/RepoB"}]
    respx_mock.get(org_api).respond(200, json=repos)

    repo_contents_api = "https://api.github.com/repos/OSHADataDoor/RepoA/contents/"
    contents = [{"name": "data.csv", "type": "file", "download_url": "https://raw.example/data.csv"}]
    respx_mock.get(repo_contents_api).respond(200, json=contents)

    raw_csv = "col1,col2\n1,2\n"
    respx_mock.get("https://raw.example/data.csv").respond(200, content=raw_csv)

    org_repos = github_fetcher.list_org_repos("https://github.com/OSHADataDoor")
    assert "OSHADataDoor/RepoA" in org_repos
    entries = github_fetcher.list_repo_files("OSHADataDoor/RepoA", path="")
    assert entries and entries[0]["name"] == "data.csv"


def test_ckan_fetcher_package_and_preview(respx_mock):
    site = "https://demo.ckan.org"
    api_pkg = site + "/api/3/action/package_show"
    pkg = {"result": {"title": "pkg", "notes": "desc", "resources": [{"name": "r1", "format": "CSV", "url": "https://raw.example/sample.csv"}]}}
    respx_mock.get(api_pkg).respond(200, json=pkg)
    respx_mock.get("https://raw.example/sample.csv").respond(200, content="a,b\n1,2\n3,4\n")

    meta = ckan_fetcher.fetch_metadata(site, "pkg")
    assert meta.get("title") == "pkg"
    pv = ckan_fetcher.fetch_preview(site, "pkg", n=2)
    assert pv


def test_socrata_fetcher_view_and_resource(respx_mock):
    site = "https://data.example.org"
    view_id = "abcd-1234"
    meta_url = site + "/api/views/" + view_id + ".json"
    respx_mock.get(meta_url).respond(200, json={"name": "Test View", "columns": []})
    resource_url = site + "/resource/" + view_id + ".json"
    respx_mock.get(resource_url).respond(200, json=[{"c": 1}, {"c": 2}])

    meta = socrata_fetcher.fetch_metadata(site, view_id)
    assert meta.get("title") == "Test View"
    pv = socrata_fetcher.fetch_preview(site, view_id, n=2)
    assert isinstance(pv, list) and len(pv) == 2
