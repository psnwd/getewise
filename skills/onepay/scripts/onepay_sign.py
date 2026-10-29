#!/usr/bin/env python3
"""OnePay request hash helper (stdlib only).

hash = SHA256(app_id + currency + amount + HASH_SALT)  (lowercase hex)

  ONEPAY_SALT=... python onepay_sign.py hash --app-id APP --currency LKR --amount 100
  ONEPAY_SALT=... python onepay_sign.py check --app-id APP --currency LKR --amount 100.00 --hash <value>

Amount is normalised to 2 decimals. The salt is read from ONEPAY_SALT (never pass it on the command line).
"""
import argparse, hashlib, hmac, os, sys
from decimal import Decimal, ROUND_HALF_UP


def fmt_amount(a: str) -> str:
    return str(Decimal(a).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def make_hash(app_id: str, currency: str, amount: str, salt: str) -> str:
    return hashlib.sha256(f"{app_id}{currency}{fmt_amount(amount)}{salt}".encode()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["hash", "check"])
    p.add_argument("--app-id", required=True)
    p.add_argument("--currency", required=True)
    p.add_argument("--amount", required=True)
    p.add_argument("--hash")
    a = p.parse_args()
    salt = os.environ.get("ONEPAY_SALT")
    if not salt:
        print("Set ONEPAY_SALT in the environment", file=sys.stderr)
        return 2
    h = make_hash(a.app_id, a.currency.upper(), a.amount, salt)
    if a.cmd == "hash":
        print(f"amount : {fmt_amount(a.amount)}\nhash   : {h}")
        return 0
    if not a.hash:
        print("--hash required for check", file=sys.stderr)
        return 2
    ok = hmac.compare_digest(h, a.hash.strip().lower())
    print("MATCH" if ok else f"MISMATCH (expected {h})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
