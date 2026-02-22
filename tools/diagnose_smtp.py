#!/usr/bin/env python3
"""Diagnostic helper: check dnspython, extract sample domains from CSV, run MX lookups (nslookup and dnspython if available), and test TCP port 25 connectivity to MX hosts.

Usage:
  python tools/diagnose_smtp.py --csv outputs/sacramento_contractors_cslb_sac_osint.csv --limit 10
"""
import argparse
import csv
import subprocess
import socket
import sys
import time


def check_dnspython():
    try:
        import dns.resolver
        return True, getattr(dns, '__file__', 'dns')
    except Exception as e:
        return False, str(e)


def get_sample_domains(csv_path, limit=10):
    cols = ('derived_domain', 'osint_email_domain', 'gp_website', 'website', 'domain')
    domains = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                found = set()
                for c in cols:
                    v = (row.get(c) or '').strip()
                    if v:
                        found.add(v)
                domains.append({'row': i+1, 'domains': list(found)})
    except FileNotFoundError:
        print(f"CSV not found: {csv_path}")
        sys.exit(2)
    return domains


def nslookup_mx(domain):
    try:
        out = subprocess.check_output(['nslookup', '-type=mx', domain], stderr=subprocess.STDOUT, timeout=15, universal_newlines=True)
        return True, out
    except Exception as e:
        return False, str(e)


def parse_mx_from_nslookup(output):
    hosts = []
    for line in output.splitlines():
        line = line.strip()
        # lines like: example.com    mail exchanger = 10 smtp.example.com.
        if 'mail exchanger' in line.lower() or 'mx preference' in line.lower() or 'exchange' in line.lower():
            parts = line.split()
            if parts:
                host = parts[-1].rstrip('.')
                if host and host != '':
                    hosts.append(host)
    return hosts


def try_connect(host, port=25, timeout=6):
    try:
        start = time.time()
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True, round(time.time() - start, 2), None
    except Exception as e:
        return False, None, str(e)


def dnsresolver_mx(domain):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'MX', lifetime=10)
        hosts = [str(r.exchange).rstrip('.') for r in answers]
        return True, hosts
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()

    print('Diagnose SMTP / DNS connectivity')
    print('Checking dnspython availability...')
    ok, info = check_dnspython()
    print('dnspython:', 'present' if ok else 'missing/error', info)

    print('\nReading sample domains from CSV: %s (limit=%d)' % (args.csv, args.limit))
    samples = get_sample_domains(args.csv, args.limit)
    for s in samples:
        print(f"\nRow {s['row']}: domains -> {s['domains']}")
        for d in s['domains']:
            print(f"  Domain: {d}")
            print('   - nslookup MX...')
            ok_ns, out = nslookup_mx(d)
            if ok_ns:
                hosts = parse_mx_from_nslookup(out)
                print('     nslookup success, mx hosts:', hosts)
            else:
                print('     nslookup failed:', out)

            if ok:
                print('   - dnspython MX...')
                ok_dn, res = dnsresolver_mx(d)
                if ok_dn:
                    print('     dns.resolver MX:', res)
                else:
                    print('     dns.resolver failed:', res)

            # attempt to connect to any MX hosts found (prefer dnspython hosts then nslookup hosts)
            mx_candidates = []
            if ok and ok_dn:
                mx_candidates = res
            elif ok_ns and hosts:
                mx_candidates = hosts

            if mx_candidates:
                for h in mx_candidates:
                    print(f'   - try connect {h}:25 ...')
                    conn_ok, latency, err = try_connect(h, 25)
                    if conn_ok:
                        print(f'     CONNECT OK (latency={latency}s)')
                    else:
                        print(f'     CONNECT FAIL: {err}')
            else:
                print('   - no MX hosts discovered; skipping port 25 connect')

    print('\nSummary: Review rows above for MX presence and port 25 connectivity. If MX hosts exist but TCP connects fail, machine egress to port 25 may be blocked.')


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Diagnostic helper: check dnspython, extract sample domains from CSV, run MX lookups (nslookup and dnspython if available), and test TCP port 25 connectivity to MX hosts.

Usage:
  python tools/diagnose_smtp.py --csv outputs/sacramento_contractors_cslb_sac_osint.csv --limit 10
"""
import argparse
import csv
import subprocess
import socket
import sys
import time


def check_dnspython():
    try:
        import dns.resolver
        return True, getattr(dns, '__file__', 'dns')
    except Exception as e:
        return False, str(e)


def get_sample_domains(csv_path, limit=10):
    cols = ('derived_domain', 'osint_email_domain', 'gp_website', 'website', 'domain')
    domains = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                found = set()
                for c in cols:
                    v = (row.get(c) or '').strip()
                    if v:
                        found.add(v)
                domains.append({'row': i+1, 'domains': list(found)})
    except FileNotFoundError:
        print(f"CSV not found: {csv_path}")
        sys.exit(2)
    return domains


def nslookup_mx(domain):
    try:
        out = subprocess.check_output(['nslookup', '-type=mx', domain], stderr=subprocess.STDOUT, timeout=15, universal_newlines=True)
        return True, out
    except Exception as e:
        return False, str(e)


def parse_mx_from_nslookup(output):
    hosts = []
    for line in output.splitlines():
        line = line.strip()
        # lines like: example.com    mail exchanger = 10 smtp.example.com.
        if 'mail exchanger' in line.lower() or 'mx preference' in line.lower() or 'exchange' in line.lower():
            parts = line.split()
            if parts:
                host = parts[-1].rstrip('.')
                if host and host != '':
                    hosts.append(host)
    return hosts


def try_connect(host, port=25, timeout=6):
    try:
        start = time.time()
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True, round(time.time() - start, 2), None
    except Exception as e:
        return False, None, str(e)


def dnsresolver_mx(domain):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'MX', lifetime=10)
        hosts = [str(r.exchange).rstrip('.') for r in answers]
        return True, hosts
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()

    print('Diagnose SMTP / DNS connectivity')
    print('Checking dnspython availability...')
    ok, info = check_dnspython()
    print('dnspython:', 'present' if ok else 'missing/error', info)

    print('\nReading sample domains from CSV: %s (limit=%d)' % (args.csv, args.limit))
    samples = get_sample_domains(args.csv, args.limit)
    for s in samples:
        print(f"\nRow {s['row']}: domains -> {s['domains']}")
        for d in s['domains']:
            print(f"  Domain: {d}")
            print('   - nslookup MX...')
            ok_ns, out = nslookup_mx(d)
            if ok_ns:
                hosts = parse_mx_from_nslookup(out)
                print('     nslookup success, mx hosts:', hosts)
            else:
                print('     nslookup failed:', out)

            if ok:
                print('   - dnspython MX...')
                ok_dn, res = dnsresolver_mx(d)
                if ok_dn:
                    print('     dns.resolver MX:', res)
                else:
                    print('     dns.resolver failed:', res)

            # attempt to connect to any MX hosts found (prefer dnspython hosts then nslookup hosts)
            mx_candidates = []
            if ok and ok_dn:
                mx_candidates = res
            elif ok_ns and hosts:
                mx_candidates = hosts

            if mx_candidates:
                for h in mx_candidates:
                    print(f'   - try connect {h}:25 ...')
                    conn_ok, latency, err = try_connect(h, 25)
                    if conn_ok:
                        print(f'     CONNECT OK (latency={latency}s)')
                    else:
                        print(f'     CONNECT FAIL: {err}')
            else:
                print('   - no MX hosts discovered; skipping port 25 connect')

    print('\nSummary: Review rows above for MX presence and port 25 connectivity. If MX hosts exist but TCP connects fail, machine egress to port 25 may be blocked.')


if __name__ == '__main__':
    main()
