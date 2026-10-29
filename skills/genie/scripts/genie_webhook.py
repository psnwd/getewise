#!/usr/bin/env python3
"""Compute or verify a Genie Business webhook signature.

Signature = hex(SHA-256(nonce + timestamp + api_key)), sent in X-Signature with
X-Signature-Nonce and X-Signature-Timestamp. The API key is read from the
GENIE_API_KEY environment variable (or --api-key; avoid that on shared shells).

  genie_webhook.py sign   --nonce N --timestamp T
  genie_webhook.py verify --nonce N --timestamp T --signature S
"""
import argparse, hashlib, hmac, os, sys


def sign(nonce: str, timestamp: str, api_key: str) -> str:
    return hashlib.sha256((nonce + timestamp + api_key).encode()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["sign", "verify"])
    p.add_argument("--nonce", required=True)
    p.add_argument("--timestamp", required=True)
    p.add_argument("--signature", help="received X-Signature (verify mode)")
    p.add_argument("--api-key", help="defaults to $GENIE_API_KEY")
    a = p.parse_args()
    key = a.api_key or os.environ.get("GENIE_API_KEY")
    if not key:
        print("set GENIE_API_KEY (or --api-key)", file=sys.stderr)
        return 2
    expected = sign(a.nonce, a.timestamp, key)
    if a.mode == "sign":
        print(expected)
        return 0
    if not a.signature:
        print("--signature is required for verify", file=sys.stderr)
        return 2
    ok = hmac.compare_digest(expected.lower(), a.signature.strip().lower())
    print("VALID" if ok else "INVALID")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
