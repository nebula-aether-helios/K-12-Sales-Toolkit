import importlib
m = importlib.import_module('v3_enhanced_enrichment')
print('v3_enhanced_enrichment loaded, DCA_DATAFRAMES =', len(getattr(m, 'DCA_DATAFRAMES', [])))
for item in getattr(m, 'DCA_DATAFRAMES', []):
    print('-', item.get('path'))
