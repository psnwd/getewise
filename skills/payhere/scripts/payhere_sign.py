#!/usr/bin/env python3
"""PayHere signing helper (stdlib only).

Generate the request `hash` for Checkout / Recurring / Preapproval / Authorize forms,
or verify the `md5sig` of a notify_url callback.

Examples
  # request hash for a checkout form
  python payhere_sign.py hash --merchant-id 1211149 --order-id ItemNo12345 \
      --amount 1000 --currency LKR --secret "$PAYHERE_SECRET"

  # preapproval without an amount (uses the documented placeholder amount)
  python payhere_sign.py hash --merchant-id 1211149 --order-id P1 --currency LKR \
      --secret "$PAYHERE_SECRET" --preapproval

  # recurring with a future recurring_start_date (documented hash-amount override)
  python payhere_sign.py hash --merchant-id 1211149 --order-id R1 --amount 2500 \
      --currency LKR --secret "$PAYHERE_SECRET" --future-start

  # verify a notification (pass values exactly as received)
  python payhere_sign.py verify --merchant-id 1211149 --order-id ItemNo12345 \
      --amount 1000.00 --currency LKR --status-code 2 --md5sig ABCD... \
      --secret "$PAYHERE_SECRET"

Prefer the PAYHERE_SECRET environment variable over --secret so the secret does
not land in shell history.
"""
import argparse
import hashlib
import hmac
import os
import sys
from decimal import ROUND_HALF_UP, Decimal


def md5_upper(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest().upper()


def fmt_amount(amount) -> str:
    """Two decimals, no thousands separator (what PayHere expects in the request hash)."""
    return str(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def request_hash(merchant_id, order_id, amount, currency, secret) -> str:
    return md5_upper(f"{merchant_id}{order_id}{fmt_amount(amount)}{currency}{md5_upper(secret)}")


def notify_sig(merchant_id, order_id, payhere_amount, payhere_currency, status_code, secret) -> str:
    # payhere_amount etc. are used verbatim as received; do NOT reformat them.
    return md5_upper(
        f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{md5_upper(secret)}"
    )


def verify(md5sig, **kw) -> bool:
    return hmac.compare_digest(notify_sig(**kw), (md5sig or "").upper())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("hash", help="generate request hash")
    h.add_argument("--merchant-id", required=True)
    h.add_argument("--order-id", required=True)
    h.add_argument("--amount")
    h.add_argument("--currency", required=True)
    h.add_argument("--secret", default=os.environ.get("PAYHERE_SECRET"))
    h.add_argument("--preapproval", action="store_true",
                   help="no amount sent: use 10.00 (LKR) or 0.51 (other currencies)")
    h.add_argument("--future-start", action="store_true",
                   help="recurring with future recurring_start_date: hash uses 10.00 (LKR) or 0.50 (other)")

    v = sub.add_parser("verify", help="verify notification md5sig")
    v.add_argument("--merchant-id", required=True)
    v.add_argument("--order-id", required=True)
    v.add_argument("--amount", required=True, help="payhere_amount exactly as received")
    v.add_argument("--currency", required=True, help="payhere_currency")
    v.add_argument("--status-code", required=True)
    v.add_argument("--md5sig", required=True)
    v.add_argument("--secret", default=os.environ.get("PAYHERE_SECRET"))

    a = p.parse_args(argv)
    if not a.secret:
        p.error("provide the merchant secret via PAYHERE_SECRET or --secret")

    if a.cmd == "hash":
        amount = a.amount
        if a.preapproval and amount is None:
            amount = "10.00" if a.currency.upper() == "LKR" else "0.51"
        elif a.future_start:
            amount = "10.00" if a.currency.upper() == "LKR" else "0.50"
        if amount is None:
            p.error("--amount is required (or use --preapproval)")
        print(request_hash(a.merchant_id, a.order_id, amount, a.currency, a.secret))
        return 0

    ok = verify(
        a.md5sig,
        merchant_id=a.merchant_id, order_id=a.order_id, payhere_amount=a.amount,
        payhere_currency=a.currency, status_code=a.status_code, secret=a.secret,
    )
    print("VALID" if ok else "INVALID")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
