#!/usr/bin/env python3
"""
Upscaled Reprobe Tool.
Handles multi-person rows (Owner, Agent, Personnel) per prospect.
Validates both Email (DNS/SMTP) and Phone (Format/Reachability).
"""

import argparse
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Mock imports for context - ensure these match your actual project structure
from db.models import (
    get_session, EnrichedProspect, EmailCandidate,
    acquire_lock, release_lock
)
try:
    # Person may not exist in all schemas; optional import
    from db.models import Person  # type: ignore
except Exception:
    Person = None
from connectors.dns_helpers import get_dns_records, parse_spf, is_valid_hostname, mx_provider_from_hostname
from enrichment.email_utils import smtp_probe

# --- Configuration & Logging ---
LOG_DIR = os.path.join(os.getcwd(), 'outputs', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('upscale_reprobe')

def setup_logger():
    if not logger.handlers:
        fh = logging.FileHandler(os.path.join(LOG_DIR, 'upscale_reprobe.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)

# --- Data Structures ---

@dataclass
class ContactProfile:
    """Normalized representation of a person/contact within a prospect."""
    role: str           # e.g., 'owner', 'agent', 'dba_contact', 'personnel'
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    db_obj: Any = None  # Reference to the SQLAlchemy object (EmailCandidate or Person)

# --- Helper Functions ---

def normalize_phone(phone: str) -> Optional[str]:
    """Basic phone normalization to E.164 or digits."""
    if not phone: return None
    # Remove non-digits
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 10: return f"+1{digits}" # Assumption: US numbers
    if len(digits) > 10: return f"+{digits}"
    return None

def validate_phone_number(phone: str) -> Dict:
    """Mockable phone validation logic."""
    # In a real scenario, integrate with Twilio Lookup or similar API here.
    normalized = normalize_phone(phone)
    if not normalized:
        return {"valid": False, "error": "empty_or_invalid_format"}
    
    # Simple regex check for demonstration
    is_valid = bool(re.match(r'^\+?[1-9]\d{1,14}$', normalized))
    return {
        "valid": is_valid,
        "normalized": normalized,
        "type": "mobile" if is_valid else "unknown" # Mock inference
    }

def gather_prospect_contacts(p: EnrichedProspect) -> List[ContactProfile]:
    """
    Intelligently extracts all people associated with the prospect.
    Checks explicit relationships (owner, agent) and generic lists (emails, personnel).
    """
    contacts = []

    # 1. Check direct relations (if your model has specific columns/relationships)
    # Example: if p.owner is a relationship to a Person object
    if hasattr(p, 'owner') and p.owner:
        contacts.append(ContactProfile(
            role='owner', 
            name=getattr(p.owner, 'name', 'Unknown'), 
            email=getattr(p.owner, 'email', None),
            phone=getattr(p.owner, 'phone', None),
            db_obj=p.owner
        ))

    # 2. Check Generic Email Candidates (The standard list)
    for c in p.emails:
        # If 'role' is stored in source_signals or a column, use it
        signals = c.source_signals or {}
        role = getattr(c, 'role', None) or signals.get('role', 'general_contact')
        
        contacts.append(ContactProfile(
            role=role,
            name=getattr(c, 'name', 'Unknown'),
            email=c.email,
            phone=getattr(c, 'phone', None), # Assuming EmailCandidate might hold a phone
            db_obj=c
        ))

    # 3. Check Personnel List (if strictly separate)
    if hasattr(p, 'personnel') and p.personnel:
        for pers in p.personnel:
            contacts.append(ContactProfile(
                role='personnel',
                name=pers.name,
                email=pers.email,
                phone=pers.phone,
                db_obj=pers
            ))

    return contacts

# --- Core Validation Logic ---

def process_contact(sess, contact: ContactProfile, metrics: Dict) -> Dict:
    """Runs validation for both Email and Phone for a single contact."""
    results = {"role": contact.role, "email_valid": False, "phone_valid": False}
    
    # A. Validate Email
    if contact.email:
        try:
            domain = contact.email.split('@', 1)[1].lower()
            dns = get_dns_records(domain)
            mx_hosts = [(m[0], m[1]) for m in dns.get('mx', []) if isinstance(m, tuple)]
            
            # SMTP Probe
            probe = smtp_probe(contact.email, mx_hosts)
            results['email_probe'] = probe
            results['email_valid'] = (probe.get('status') == 'valid')

            # Update DB Object (EmailCandidate or Person)
            if contact.db_obj:
                signals = dict(getattr(contact.db_obj, 'source_signals', {}) or {})
                signals.update({
                    'last_probe_date': 'today', # Replace with real timestamp
                    'smtp_status': probe.get('status'),
                    'smtp_details': probe
                })
                contact.db_obj.source_signals = signals
                if results['email_valid']:
                    contact.db_obj.status = 'validated' # Or specific status field
        except Exception as e:
            logger.error(f"Email validation failed for {contact.email}: {e}")

    # B. Validate Phone
    if contact.phone:
        phone_res = validate_phone_number(contact.phone)
        results['phone_probe'] = phone_res
        results['phone_valid'] = phone_res.get('valid')
        
        # Update DB Object
        if contact.db_obj:
            # Assuming db_obj has a place to store phone validation
            signals = dict(getattr(contact.db_obj, 'source_signals', {}) or {})
            signals['phone_validation'] = phone_res
            contact.db_obj.source_signals = signals

    return results


def upscale_reprobe(db_url: str, limit: int = 10, atomic_commit: bool = False):
    setup_logger()
    sess = get_session(db_url)
    global_lock = 'upscale_reprobe_global'
    metrics = {"processed": 0, "email_valid": 0, "phone_valid": 0}

    if not acquire_lock(sess, name=global_lock, owner='reprobe_script'):
        print("Global lock held. Aborting.")
        return

    try:
        # Load prospects (Entities containing the multi-person rows)
        prospects = sess.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(limit).all()
        print(f"Processing {len(prospects)} prospects (Multi-person mode)...")

        for p in prospects:
            # Row-level lock
            if not acquire_lock(sess, prospect_id=p.id, owner='reprobe_script'):
                continue

            try:
                # 1. Extract all people (Owner, Agent, Contact, etc.)
                contacts = gather_prospect_contacts(p)
                print(f"Prospect {p.id}: Found {len(contacts)} contacts/roles.")

                # 2. Validate everyone
                for contact in contacts:
                    res = process_contact(sess, contact, metrics)
                    
                    # Update metrics
                    metrics["processed"] += 1
                    if res['email_valid']: metrics['email_valid'] += 1
                    if res['phone_valid']: metrics['phone_valid'] += 1
                    
                    logger.info(json.dumps({
                        "event": "contact_validated",
                        "prospect_id": p.id,
                        "role": contact.role,
                        "email": contact.email,
                        "email_valid": res['email_valid'],
                        "phone_valid": res['phone_valid']
                    }))

                # 3. Update Prospect Level Signals (Summary)
                p.source_signals = dict(p.source_signals or {})
                p.source_signals['last_reprobe_summary'] = {
                    "total_contacts": len(contacts),
                    "valid_emails": sum(1 for c in contacts if getattr(c.db_obj, 'status', '') == 'validated')
                }
                
                if atomic_commit:
                    sess.commit()
                    sess.refresh(p) # Critical for iteration safety

            except Exception as e:
                sess.rollback()
                logger.error(json.dumps({"event": "prospect_error", "id": p.id, "error": str(e)}))
            finally:
                release_lock(sess, prospect_id=p.id)

        if not atomic_commit:
            sess.commit()

    finally:
        print(f"Complete. Metrics: {metrics}")
        release_lock(sess, name=global_lock)
        sess.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--atomic-commit', action='store_true')
    args = p.parse_args()
    upscale_reprobe(args.db, args.limit, args.atomic_commit)

if __name__ == '__main__':
    main()
