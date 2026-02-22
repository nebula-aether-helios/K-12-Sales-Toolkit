"""Check availability of enrichment sources and connectors in the repo.
Prints simple yes/no and key details.
"""
import importlib
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# load local .env if present
env_path = repo_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))

def safe_import(name):
    try:
        m = importlib.import_module(name)
        return True, m
    except Exception as e:
        return False, e

checks = []

# v3 enhanced enrichment
ok, mod = safe_import('v3_enhanced_enrichment')
checks.append(('v3_enhanced_enrichment', ok))
if ok:
    print('v3_enhanced_enrichment loaded')
    print('  GOOGLE_PLACES_API_KEY set:', bool(os.getenv('GOOGLE_PLACES_API_KEY')))
    print('  DCA_API set:', bool(os.getenv('DCA_API') or os.getenv('US_DEPT_OF_LABOR_API')))
    print('  WAYBACK_BASE:', os.getenv('WAYBACK_BASE'))
    try:
        print('  DNS_AVAILABLE:', getattr(mod, 'DNS_AVAILABLE', False))
        print('  PHONE_AVAILABLE:', getattr(mod, 'PHONE_AVAILABLE', False))
    except Exception:
        pass

# ferengi enricher
ok, mod = safe_import('ferengi_full_enrichment')
checks.append(('ferengi_full_enrichment', ok))
if ok:
    print('ferengi_full_enrichment will use v3_enrich_google_places:' , hasattr(mod, 'v3_enrich_google_places') and mod.v3_enrich_google_places is not None)
    print('ferengi_full_enrichment will use v3_enrich_osha:' , hasattr(mod, 'v3_enrich_osha') and mod.v3_enrich_osha is not None)

# connectors
for name in ('connectors.recondon_craigslist','connectors.dns_mx','connectors.wayback'):
    ok, m = safe_import(name)
    checks.append((name, ok))
    print(f'{name}:', 'OK' if ok else f'FAILED ({m})')

# check catalog_api sources folder
src_dir = repo_root / 'catalog_api' / 'sources'
print('catalog_api sources present:', src_dir.exists() and any(src_dir.iterdir()))

# summary
print('\nSummary:')
for k,v in checks:
    print(f' - {k}:', 'OK' if v else 'MISSING')

print('\nIf critical modules are missing, install requirements from requirements.txt and re-run.')
