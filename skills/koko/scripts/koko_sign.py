#!/usr/bin/env python3
"""Koko helper (needs: pip install cryptography).

  python koko_sign.py order --key merchant_private.pem --mid M --amount 300.00 --currency LKR \
      --plugin-name customapi --plugin-version 1.0.1 --return-url R --cancel-url C --order-id 53 \
      --reference 53 --first-name John --last-name Doe --email j@x.lk --description "2 products" \
      --api-key K --response-url U
  python koko_sign.py view   --key merchant_private.pem --mid M --plugin-name customapi --plugin-version 1 --order-id 53 --api-key K
  python koko_sign.py verify --key koko_public.pem --order-id 53 --trn-id T --status SUCCESS --signature <b64>

order/view : prints the dataString and base64(RSA-SHA256-PKCS1v15 signature) for the form fields.
verify     : checks Koko's signature over orderId + trnId + status (response URL / order view response).
"""
import argparse, base64, sys

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    sys.exit("pip install cryptography")


def order_string(a):  # order is fixed by Koko, not alphabetical
    return "".join([a.mid, a.amount, a.currency, a.plugin_name, a.plugin_version, a.return_url, a.cancel_url,
                    a.order_id, a.reference, a.first_name, a.last_name, a.email, a.description, a.api_key, a.response_url])


def view_string(a):
    return a.mid + a.plugin_name + a.plugin_version + a.order_id + a.api_key


def sign(pem, s):
    k = serialization.load_pem_private_key(open(pem, "rb").read(), None)
    return base64.b64encode(k.sign(s.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["order", "view", "verify"])
    p.add_argument("--key", required=True)
    for f in ["mid", "amount", "currency", "plugin-name", "plugin-version", "return-url", "cancel-url", "order-id",
              "reference", "first-name", "last-name", "email", "description", "api-key", "response-url",
              "trn-id", "status", "signature"]:
        p.add_argument("--" + f)
    a = p.parse_args()
    need = {"order": ["mid", "amount", "currency", "plugin_name", "plugin_version", "return_url", "cancel_url",
                      "order_id", "reference", "first_name", "last_name", "email", "description", "api_key", "response_url"],
            "view": ["mid", "plugin_name", "plugin_version", "order_id", "api_key"],
            "verify": ["order_id", "trn_id", "status", "signature"]}[a.cmd]
    miss = [n for n in need if getattr(a, n) is None]
    if miss:
        sys.exit("missing: " + ", ".join("--" + m.replace("_", "-") for m in miss))
    if a.cmd == "verify":
        pub = serialization.load_pem_public_key(open(a.key, "rb").read())
        try:
            pub.verify(base64.b64decode(a.signature), (a.order_id + a.trn_id + a.status).encode(),
                       padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature:
            print("INVALID: signature does not match orderId+trnId+status"); sys.exit(1)
        print("VALID"); return
    s = order_string(a) if a.cmd == "order" else view_string(a)
    print("dataString:", s); print("signature :", sign(a.key, s))


if __name__ == "__main__":
    main()
