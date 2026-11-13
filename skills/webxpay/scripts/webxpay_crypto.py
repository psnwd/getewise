#!/usr/bin/env python3
"""WebXPay helper (needs: pip install cryptography).

  python webxpay_crypto.py build  --key pub.pem --order 12001 --amount 2567.5
  python webxpay_crypto.py verify --key pub.pem --payment <b64> --signature <b64>

build  : prints base64(RSA-PKCS1v15(public_key, "order|amount")) for the `payment` form field.
verify : base64-decodes both fields and checks the signature against the decoded payment.
         Primary scheme is RSA-PSS / SHA-1 (20-byte salt), which two official samples use and
         which a captured staging response verifies against. The older PHP docs describe
         PKCS#1 v1.5 signature recovery; that is kept as a fallback so legacy captures still pass.
"""
import argparse, base64, hmac, sys

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    sys.exit("pip install cryptography")

FIELDS = ["order_id", "order_ref", "datetime", "status_code", "comment",
          "gateway_id", "requested_amount", "transaction_amount"]


def load(path):
    return serialization.load_pem_public_key(open(path, "rb").read())


def build(pub, order, amount):
    return base64.b64encode(pub.encrypt(f"{order}|{float(amount):.2f}".encode(), padding.PKCS1v15())).decode()


def public_decrypt(pub, sig: bytes) -> bytes:
    """Legacy PKCS#1 v1.5 type-1 signature recovery (EM = 00 01 FF.. 00 || data)."""
    n = pub.public_numbers()
    k = (n.n.bit_length() + 7) // 8
    em = pow(int.from_bytes(sig, "big"), n.e, n.n).to_bytes(k, "big")
    if em[:2] != b"\x00\x01":
        raise ValueError("bad PKCS#1 padding (wrong key or not a signature)")
    return em[em.index(b"\x00", 2) + 1:]


def check(pub, pay: bytes, sig: bytes):
    """Return the scheme name on success, raise ValueError otherwise."""
    try:
        pub.verify(sig, pay, padding.PSS(mgf=padding.MGF1(hashes.SHA1()), salt_length=20), hashes.SHA1())
        return "pss-sha1"
    except InvalidSignature:
        pass
    try:
        if hmac.compare_digest(public_decrypt(pub, sig), pay):
            return "pkcs1v15-recovery (legacy)"
    except Exception:
        pass
    raise ValueError("signature does not match payment")


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
        scheme = check(pub, pay, base64.b64decode(a.signature))
    except Exception as e:
        print("INVALID:", e); sys.exit(1)
    f = [x.strip() for x in pay.decode().split("|")]
    print(f"VALID ({scheme})")
    for k, v in zip(FIELDS, f):
        print(f"{k:18}: {v}")
    if len(f) > len(FIELDS):
        print(f"{'extra_fields':18}: {'|'.join(f[len(FIELDS):])}")


if __name__ == "__main__":
    main()
