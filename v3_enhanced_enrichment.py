# v3_enhanced_enrichment.py
# V3 MVP Enhanced Enrichment - Monetizable Truth Data
# Preserves v3 working enrichment + adds v2 API integrations
# Created: 2026-02-04

import pandas as pd
import numpy as np
import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# load local .env if present
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))

# optional HTTP recorder for auditing API calls
try:
    import http_logger
    RECORD_HTTP = bool(os.getenv('RECORD_HTTP'))
except Exception:
    http_logger = None
    RECORD_HTTP = False

# Try to import optional dependencies
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("⚠️ dnspython not installed - DNS enrichment disabled")

try:
    import phonenumbers
    PHONE_AVAILABLE = True
except ImportError:
    PHONE_AVAILABLE = False
    print("⚠️ phonenumbers not installed - phone validation disabled")

# ═══════════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION (from .env.v3mvp)
# ═══════════════════════════════════════════════════════════════════════════════════════
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
# Support DCA (replacement for legacy DOL) while preserving backward compatibility
# Prefer DCA_API if present, otherwise fall back to US_DEPT_OF_LABOR_API
DCA_API = os.getenv('DCA_API', '') or os.getenv('US_DEPT_OF_LABOR_API', '')
ARCGIS_USERNAME = os.getenv('ARCGIS_USERNAME', '')
ARCGIS_PASSWORD = os.getenv('ARCGIS_PASSWORD', '')

# Ensure WAYBACK base is set to a sensible default when not configured
if not os.getenv('WAYBACK_BASE'):
    os.environ['WAYBACK_BASE'] = 'https://web.archive.org'

# Load DCA physical datasets from manifests in catalog_api/sources if present
DCA_DATAFRAMES = []

def load_local_dca_datasets():
    """Lightweight loader for local DCA datasets referenced in catalog manifests.
    This simplified loader is intentionally defensive to avoid import-time failures.
    """
    src_dir = Path('catalog_api') / 'sources'
    if not src_dir.exists():
        return

    for p in src_dir.glob('*.json'):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        ef = j.get('example_files') or []
        for fp in ef:
            try:
                fp_path = Path(fp)
                if not fp_path.exists():
                    fp_path = Path(fp.lstrip('/'))
                if fp_path.exists() and fp_path.suffix.lower() in ('.csv', '.json'):
                    try:
                        if fp_path.suffix.lower() == '.csv':
                            df = pd.read_csv(fp_path, low_memory=False)
                        else:
                            df = pd.read_json(fp_path)
                        DCA_DATAFRAMES.append({'path': str(fp_path), 'df': df, 'manifest': str(p)})
                    except Exception:
                        # skip problematic example file
                        continue
            except Exception:
                continue

# attempt to load local DCA datasets on import (defensive)
try:
    load_local_dca_datasets()
except Exception:
    pass


# Defensive numeric helpers
def safe_float(value, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    if isinstance(value, str):
        v = value.strip().replace('$', '').replace(',', '')
        if v == '' or v.lower() in ('none', 'null'):
            return default
        try:
            return float(v)
        except Exception:
            return default
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return default


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 1: DNS/MX VALIDATION (v3 Working - Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_dns_mx(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    DNS/MX validation using dnspython (FREE - no API key needed).
    Populates: derived_domain, domain_has_a, domain_has_mx, mx_records, dns_score
    """
    if not DNS_AVAILABLE:
        return row
        
    if pd.notna(row.get('osint_email_discovered')):
        return row  # Already enriched
    
    try:
        # Derive domain from business name or website
        website = row.get('gp_website', '')
        business_name = row.get('business_name', '')
        
        domain = None
        if pd.notna(website) and website:
            domain = website.replace('http://', '').replace('https://', '').split('/')[0]
        elif pd.notna(business_name):
            # Generate likely domain from business name
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', business_name.lower())[:20]
            domain = f"{clean_name}.com"
        
        if domain:
            row['derived_domain'] = domain
            
            # Check A record (website exists)
            try:
                dns.resolver.resolve(domain, 'A')
                row['domain_has_a'] = True
            except:
                row['domain_has_a'] = False
            
            # Check MX record (email capable)
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                row['domain_has_mx'] = True
                row['mx_records'] = ','.join([str(r.exchange) for r in mx_records][:3])
            except:
                row['domain_has_mx'] = False
                row['mx_records'] = None
            
            # Calculate DNS score
            score = 0
            if row.get('domain_has_a'):
                score += 40
            if row.get('domain_has_mx'):
                score += 45
            if row.get('mx_records') and 'google' in row['mx_records'].lower():
                score += 15
            row['dns_score'] = min(score, 100)
            
            # Generate email if MX exists
            if row.get('domain_has_mx'):
                row['osint_email_discovered'] = f"info@{domain}"
                row['osint_email_verified'] = False  # Needs MX validation
        
        row['enrich_osint_done'] = True
        row['osint_enriched_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"DNS enrichment error for {row.get('license_number')}: {e}")
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 2: PHONE VALIDATION (v3 Working - Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_phone(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phone validation using phonenumbers library (FREE - no API key needed).
    Populates: phone_valid, phone_carrier, phone_type, phone_region
    """
    if not PHONE_AVAILABLE:
        return row
        
    try:
        phone = row.get('phone_business', '')
        if pd.notna(phone) and phone:
            # Parse phone number
            parsed = phonenumbers.parse(str(phone), 'US')
            
            row['phone_valid'] = phonenumbers.is_valid_number(parsed)
            row['phone_region'] = phonenumbers.region_code_for_number(parsed)
            
            # Get number type
            number_type = phonenumbers.number_type(parsed)
            type_map = {
                0: 'FIXED_LINE',
                1: 'MOBILE',
                2: 'FIXED_OR_MOBILE',
                3: 'TOLL_FREE',
                4: 'PREMIUM_RATE'
            }
            row['phone_type'] = type_map.get(number_type, 'UNKNOWN')
            
    except Exception as e:
        row['phone_valid'] = False
        row['phone_type'] = 'INVALID'
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 3: CRAIGSLIST/RECONDON (v3 Working - Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════════════
async def enrich_craigslist_recondon(row: Dict[str, Any], regions: list = None) -> Dict[str, Any]:
    """
    Craigslist crawler using RECONDON async (v3 working implementation).
    Populates: cl_ad_found, cl_ad_url, cl_license_displayed, cl_down_payment_violation
    Triggers: trigger_fear_craigslist_violation, report_craigslist_competitor
    """
    if regions is None:
        regions = ['sacramento']
        
    try:
        import aiohttp
    except ImportError:
        print("⚠️ aiohttp not installed - Craigslist enrichment disabled")
        return row
    
    if pd.notna(row.get('cl_ad_found')):
        return row  # Already enriched
    
    try:
        license_num = str(row.get('license_number', ''))
        business_name = row.get('business_name', '').lower() if pd.notna(row.get('business_name')) else ''
        
        # Search Craigslist services section
        for region in regions:
            search_url = f"https://{region}.craigslist.org/search/bbb?query=contractor"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Check for license number in ads
                        if license_num in html:
                            row['cl_ad_found'] = True
                            row['cl_license_displayed'] = True
                        
                        # Check for business name
                        if business_name and business_name in html.lower():
                            row['cl_ad_found'] = True
                        
                        # Check for violation patterns
                        violation_patterns = [
                            r'\$\d{4,}\s*(down|deposit)',  # Large down payment
                            r'cash\s*only',
                            r'no\s*permit',
                            r'handyman\s*special'
                        ]
                        for pattern in violation_patterns:
                            if re.search(pattern, html, re.IGNORECASE):
                                row['cl_down_payment_violation'] = True
                                break
        
        # Apply trigger logic (v2 foundation)
        if row.get('cl_down_payment_violation'):
            row['trigger_fear_craigslist_violation'] = True
            row['report_craigslist_competitor'] = True  # PRIMARY REPORT eligible
        
        if row.get('cl_ad_found') and not row.get('cl_license_displayed'):
            row['trigger_fear_craigslist_violation'] = True
            row['report_craigslist_competitor'] = True
        
        row['enrich_craigslist_done'] = True
        row['cl_enriched_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"Craigslist enrichment error for {row.get('license_number')}: {e}")
        row['cl_ad_found'] = False
        row['enrich_craigslist_done'] = True
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 4: OSHA (v2 API Integration - Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_osha_dol_api(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    OSHA enrichment using US DOL API (v2 integration).
    Populates: osha_inspection_count, osha_violation_count, osha_penalty_total
    Triggers: trigger_fear_osha_investigation, report_osha_risk
    """
    if pd.notna(row.get('osha_inspection_count')):
        return row  # Already enriched
    
    try:
        business_name = row.get('business_name', '')
        if not pd.notna(business_name) or len(business_name) < 3:
            row['osha_inspection_count'] = 0
            row['osha_violation_count'] = 0
            row['osha_penalty_total'] = 0
            row['enrich_osha_done'] = True
            return row
        
        # Query DCA / US DOL API if a DCA_API URL or legacy key is provided
        # Otherwise, prefer local physical datasets discovered via the master catalog manifests
        if DCA_API and (DCA_API.startswith('http') or DCA_API.startswith('https')):
            try:
                api_url = DCA_API
                params = {"q": business_name[:50]}
                response = requests.get(api_url, params=params, timeout=10)
                # record HTTP evidence if requested
                if RECORD_HTTP and http_logger:
                    try:
                        http_logger.record_http('osha_dol_api', response.url, params, response.status_code, response.text)
                    except Exception:
                        pass
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception:
                        data = {}
                    results = data.get('results') or data.get('d', {}).get('results', [])
                    row['osha_inspection_count'] = len(results)
                    row['osha_violation_count'] = sum(1 for r in results if r.get('violation'))
                    row['osha_penalty_total'] = sum(float(r.get('penalty', 0)) for r in results)
            except Exception:
                # fall through to local datasets
                pass
        # If no remote API used or it failed, try local DCA datasets loaded from manifests
        if row.get('osha_inspection_count', None) is None or row.get('osha_inspection_count') == 0:
            found = False
            try:
                for item in DCA_DATAFRAMES:
                    df = item.get('df')
                    # try common column names
                    col_candidates = [c for c in df.columns if 'name' in c.lower() or 'estab' in c.lower() or 'business' in c.lower()]
                    if not col_candidates:
                        continue
                    mask = False
                    for col in col_candidates:
                        try:
                            mask = df[col].astype(str).str.upper().str.contains(business_name.upper()[:30], na=False)
                            if mask.any():
                                matches = df[mask]
                                row['osha_inspection_count'] = len(matches)
                                # guess violation and penalty columns
                                if 'nr_violations' in matches.columns:
                                    row['osha_violation_count'] = int(matches['nr_violations'].sum())
                                elif 'violations' in matches.columns:
                                    row['osha_violation_count'] = int(matches['violations'].sum()) if matches['violations'].dtype.kind in 'if' else len(matches)
                                else:
                                    row['osha_violation_count'] = len(matches)
                                if 'total_current_penalty' in matches.columns:
                                    row['osha_penalty_total'] = float(matches['total_current_penalty'].sum())
                                elif 'penalty' in matches.columns:
                                    row['osha_penalty_total'] = float(matches['penalty'].sum())
                                else:
                                    row['osha_penalty_total'] = 0
                                found = True
                                break
                        except Exception:
                            continue
                    if found:
                        break
            except Exception:
                pass
            # final fallback to FinalDB path if still nothing
            if not found:
                osha_path = os.path.expanduser('~/FinalDB/22_OSHA_Citations.csv')
                if os.path.exists(osha_path):
                    df_osha = pd.read_csv(osha_path, low_memory=False)
                    matches = df_osha[df_osha['estab_name'].str.upper().str.contains(business_name.upper()[:20], na=False)]
                    row['osha_inspection_count'] = len(matches)
                    row['osha_violation_count'] = matches['nr_violations'].sum() if 'nr_violations' in matches.columns else 0
                    row['osha_penalty_total'] = matches['total_current_penalty'].sum() if 'total_current_penalty' in matches.columns else 0
                else:
                    row['osha_inspection_count'] = row.get('osha_inspection_count', 0) or 0
                    row['osha_violation_count'] = row.get('osha_violation_count', 0) or 0
                    row['osha_penalty_total'] = row.get('osha_penalty_total', 0) or 0
        
        # Apply trigger logic (v2 foundation)
        if row.get('osha_violation_count', 0) > 0:
            row['trigger_fear_osha_investigation'] = True
            row['report_osha_risk'] = True  # PRIMARY REPORT eligible
        
        row['enrich_osha_done'] = True
        row['osha_enriched_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"OSHA enrichment error for {row.get('license_number')}: {e}")
        row['osha_inspection_count'] = 0
        row['enrich_osha_done'] = True
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 5: ARCGIS PERMITS (v2 API Integration - Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_arcgis_permits(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Permit enrichment using ArcGIS REST API (v2 integration).
    Populates: permit_active_count, permit_total_value, permit_last_issued_date
    Triggers: trigger_envy_competitor_permits, report_competitor_permit_tracker
    """
    if pd.notna(row.get('permit_active_count')):
        return row  # Already enriched
    
    try:
        license_num = str(row.get('license_number', ''))
        business_name = row.get('business_name', '')
        
        # ArcGIS REST API query
        arcgis_url = "https://services1.arcgis.com/5NARefyPVtAeuJPU/arcgis/rest/services/BldgPermitIssued/FeatureServer/0/query"
        params = {
            "where": f"ContractorLicense LIKE '%{license_num}%' OR Contractor LIKE '%{business_name[:20] if business_name else ''}%'",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        response = requests.get(arcgis_url, params=params, timeout=15)
        # record HTTP evidence if requested
        if RECORD_HTTP and http_logger:
            try:
                http_logger.record_http('arcgis_permits', response.url, params, response.status_code, response.text)
            except Exception:
                pass
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            row['permit_active_count'] = len(features)
            row['permit_total_value'] = sum(f.get('attributes', {}).get('EstProjectCost', 0) or 0 for f in features)
            
            if features:
                dates = [f.get('attributes', {}).get('IssueDate') for f in features if f.get('attributes', {}).get('IssueDate')]
                if dates:
                    row['permit_last_issued_date'] = max(dates)
        else:
            # Fallback: Use local permit data
            permit_path = os.path.expanduser('~/FinalDB/BldgPermitIssued_Archive_7996043217366564700.csv')
            if os.path.exists(permit_path):
                df_permits = pd.read_csv(permit_path, low_memory=False, nrows=100000)
                matches = df_permits[
                    (df_permits['ContractorLicense'].astype(str).str.contains(license_num, na=False)) |
                    (df_permits['Contractor'].str.upper().str.contains(business_name.upper()[:20] if business_name else '', na=False))
                ]
                row['permit_active_count'] = len(matches)
                row['permit_total_value'] = matches['EstProjectCost'].sum() if 'EstProjectCost' in matches.columns else 0
            else:
                row['permit_active_count'] = 0
                row['permit_total_value'] = 0
        
        # Apply trigger logic (v2 foundation)
        if row.get('permit_active_count', 0) > 0:
            row['trigger_envy_competitor_permits'] = True
            row['report_competitor_permit_tracker'] = True  # PRIMARY REPORT eligible
        
        row['enrich_permits_done'] = True
        row['permit_enriched_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"Permit enrichment error for {row.get('license_number')}: {e}")
        row['permit_active_count'] = 0
        row['enrich_permits_done'] = True
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# ENRICHMENT MODULE 6: GOOGLE PLACES (v2 API Integration)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_google_places(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Google Places enrichment (v2 integration).
    Populates: gp_place_id, gp_website, gp_rating, gp_review_count, gp_lat, gp_lng
    """
    if pd.notna(row.get('gp_place_id')):
        return row  # Already enriched
    
    if not GOOGLE_PLACES_API_KEY:
        # Skip if no valid API key
        return row
    
    try:
        business_name = row.get('business_name', '')
        city = row.get('address_city', '')
        
        if not pd.notna(business_name):
            return row
        
        # Find Place API
        search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": f"{business_name} {city} CA",
            "inputtype": "textquery",
            "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total",
            "key": GOOGLE_PLACES_API_KEY
        }

        # perform request and optionally record HTTP evidence
        try:
            response = requests.get(search_url, params=params, timeout=10)
            if RECORD_HTTP and http_logger:
                try:
                    http_logger.record_http('places_find', response.url, params, response.status_code, response.text)
                except Exception:
                    pass
        except Exception as e:
            # network/requests failure; bail out gracefully
            if RECORD_HTTP and http_logger:
                try:
                    http_logger.record_http('places_find_error', search_url, params, getattr(e, 'errno', 'err'), str(e))
                except Exception:
                    pass
            return row

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                data = {}
            if data.get('status') == 'OK' and data.get('candidates'):
                place = data['candidates'][0]

                row['gp_place_id'] = place.get('place_id')
                # sanitize numeric outputs
                row['gp_rating'] = safe_float(place.get('rating'), None)
                try:
                    row['gp_review_count'] = safe_int(place.get('user_ratings_total'), 0)
                except Exception:
                    row['gp_review_count'] = 0
                row['gp_lat'] = place.get('geometry', {}).get('location', {}).get('lat')
                row['gp_lng'] = place.get('geometry', {}).get('location', {}).get('lng')
                
                # Get website from Place Details
                if row['gp_place_id']:
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        "place_id": row['gp_place_id'],
                        "fields": "website,formatted_phone_number",
                        "key": GOOGLE_PLACES_API_KEY
                    }
                    details_response = requests.get(details_url, params=details_params, timeout=10)
                    if RECORD_HTTP and http_logger:
                        try:
                            http_logger.record_http('places_details', details_response.url, details_params, details_response.status_code, details_response.text)
                        except Exception:
                            pass
                    if details_response.status_code == 200:
                        try:
                            details_data = details_response.json()
                        except Exception:
                            details_data = {}
                        result = details_data.get('result', {})
                        row['gp_website'] = result.get('website')
                        row['gp_phone_verified'] = result.get('formatted_phone_number') == row.get('phone_business')
        
        row['enrich_google_places_done'] = True
        row['gp_enriched_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"Google Places enrichment error for {row.get('license_number')}: {e}")
    
    return row


# ═══════════════════════════════════════════════════════════════════════════════════════
# MASTER ENRICHMENT FUNCTION (v3 + v2 Combined)
# ═══════════════════════════════════════════════════════════════════════════════════════
def enrich_for_monetization(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master enrichment function that runs all modules and applies trigger logic.
    Preserves v3 working enrichment + adds v2 API integrations.
    """
    # Module 1: DNS/MX (v3 working)
    row = enrich_dns_mx(row)
    
    # Module 2: Phone (v3 working)
    row = enrich_phone(row)
    
    # Module 3: OSHA (v2 enhanced)
    row = enrich_osha_dol_api(row)
    
    # Module 4: Permits (v2 enhanced)
    row = enrich_arcgis_permits(row)
    
    # Module 5: Google Places (v2 integration)
    row = enrich_google_places(row)
    
    # Module 6: Craigslist is async, run separately
    # row = await enrich_craigslist_recondon(row)
    
    # Update enrichment status
    modules_done = [
        row.get('enrich_google_places_done', False),
        row.get('enrich_osha_done', False),
        row.get('enrich_permits_done', False),
        row.get('enrich_craigslist_done', False),
        row.get('enrich_osint_done', False),
        row.get('enrich_court_records_done', False)
    ]
    
    completed = sum(bool(m) for m in modules_done)
    if completed == 0:
        row['enrich_status'] = 'pending'
    elif completed == 6:
        row['enrich_status'] = 'complete'
    else:
        row['enrich_status'] = 'partial'
    
    row['record_updated_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return row


# Export
__all__ = [
    'enrich_dns_mx',
    'enrich_phone',
    'enrich_craigslist_recondon',
    'enrich_osha_dol_api',
    'enrich_arcgis_permits',
    'enrich_google_places',
    'enrich_for_monetization'
]
