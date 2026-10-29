#!/usr/bin/env python3
"""WebXPay helper (needs: pip install cryptography).

  python webxpay_crypto.py build  --key pub.pem --order 12001 --amount 2567.5
  python webxpay_crypto.py verify --key pub.pem --payment <b64> --signature <b64>

build  : prints base64(RSA-PKCS1v15(public_key, "order|amount")) for the `payment` form field.
verify : base64-decodes both fields, RSA public-decrypts the signature (PKCS#1 v1.5 recovery),
         compares with the decoded payment and prints the parsed fields.
"""
import argparse, base64, hmac, sys

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    sys.exit("pip install cryptography")


def load(path):
    return serialization.load_pem_public_key(open(path, "rb").read())


def build(pub, order, amount):
    return base64.b64encode(pub.encrypt(f"{order}|{float(amount):.2f}".encode(), padding.PKCS1v15())).decode()


def public_decrypt(pub, sig: bytes) -> bytes:
    n = pub.public_numbers()
    k = (n.n.bit_length() + 7) // 8
    em = pow(int.from_bytes(sig, "big"), n.e, n.n).to_bytes(k, "big")
    if em[:2] != b"\x00\x01":
        raise ValueError("bad PKCS#1 padding (wrong key or not a signature)")
    return em[em.index(b"\x00", 2) + 1:]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["build", "verify"])
    p.add_argument("--key", required=True)
    p.add_argument("--order"); p.add_argument("--amount")
    p.add_argument("--payment"); p.add_argument("--signature")
    a = p.parse_args()
    pub = load(a.key)
    if a.cmd == "build":
        if not (a.order and a.amount):
            sys.exit("--order and --amount required")
        print(build(pub, a.order, a.amount)); return
    if not (a.payment and a.signature):
        sys.exit("--payment and --signature required")
    pay = base64.b64decode(a.payment)
    try:
        rec = public_decrypt(pub, base64.b64decode(a.signature))
    except Exception as e:
        print("INVALID:", e); sys.exit(1)
    if not hmac.compare_digest(rec, pay):
        print("INVALID: signature does not match payment"); sys.exit(1)
    f = [x.strip() for x in pay.decode().split("|")]
    names = ["order_id", "order_ref", "datetime", "status_code", "comment", "gateway_id"]
    print("VALID"); [print(f"{k:12}: {v}") for k, v in zip(names, f)]


if __name__ == "__main__":
    main()
