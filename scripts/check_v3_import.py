#!/usr/bin/env python3
import traceback
try:
    import v3_enhanced_enrichment as v3
    print('v3_enhanced_enrichment imported successfully')
    print('Has enrich_google_places:', hasattr(v3, 'enrich_google_places'))
    print('Has enrich_osha_dol_api:', hasattr(v3, 'enrich_osha_dol_api'))
except Exception:
    print('Import failed:')
    traceback.print_exc()
