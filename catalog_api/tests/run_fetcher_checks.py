from pathlib import Path
from catalog_api.fetchers import arcgis_fetcher, github_fetcher, ckan_fetcher
import csv
import sys


def get_first_arcgis(csv_path: Path):
    if not csv_path.exists():
        return None
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url') or row.get('URL') or row.get('link')
            if url and ('arcgis' in url.lower() or 'featureserver' in url.lower() or 'services' in url.lower()):
                return url
    return None


def sample_csv(csv_path: Path, n=5):
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = []
        for i, r in enumerate(reader):
            rows.append(r)
            if i >= n:
                break
    print(f"Sampled {len(rows)} rows from {csv_path} (first row headers shown):")
    if rows:
        print(rows[0])


def main():
    repo_root = Path(__file__).resolve().parent.parent

    # LA City ArcGIS
    la_csv = repo_root / 'City of Los Angeles Geohub.csv'
    la_url = get_first_arcgis(la_csv)
    print('LA City ArcGIS URL:', la_url)
    if la_url:
        meta = arcgis_fetcher.fetch_metadata(la_url)
        pv = arcgis_fetcher.fetch_preview(la_url, n=5)
        print(' LA title:', meta.get('title'))
        print(' LA preview rows:', len(pv))
        if pv:
            print('  sample row keys:', list(pv[0].keys())[:10])

    # County ArcGIS
    county_csv = repo_root / 'County of Los Angeles Open Data.csv'
    county_url = get_first_arcgis(county_csv)
    print('\nCounty ArcGIS URL:', county_url)
    if county_url:
        meta = arcgis_fetcher.fetch_metadata(county_url)
        pv = arcgis_fetcher.fetch_preview(county_url, n=5)
        print(' County title:', meta.get('title'))
        print(' County preview rows:', len(pv))
        if pv:
            print('  sample row keys:', list(pv[0].keys())[:10])

    # Sacramento CSV sampling
    sac_csv = repo_root / 'sacramento_contractors_cslb_sac.csv'
    print('\nSacramento CSV:')
    sample_csv(sac_csv, n=3)

    # OSHA GitHub org
    print('\nOSHA GitHub org repos:')
    repos = github_fetcher.list_org_repos('https://github.com/OSHADataDoor')
    print(' Found repos count:', len(repos))
    print(' Sample repos:', repos[:8])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error during fetcher checks:', e)
        sys.exit(2)
