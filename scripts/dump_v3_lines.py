import sys
p='v3_enhanced_enrichment.py'
with open(p,'rb') as f:
    data=f.read()
lines=data.splitlines()
for i,l in enumerate(lines[:200], start=1):
    print(f'{i:03d}: {l!r}')
