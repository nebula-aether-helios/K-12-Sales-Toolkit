from db.models import get_session, ProviderMetric
import json

s = get_session('sqlite:///enrichment.db')
rows = s.query(ProviderMetric).order_by(ProviderMetric.probes.desc()).all()
out = []
for r in rows:
    out.append({
        "provider": r.provider,
        "probes": r.probes,
        "valid": r.valid,
        "invalid": r.invalid,
        "codes": r.codes or {}
    })
print(json.dumps({"count": len(out), "metrics": out}, indent=2))
