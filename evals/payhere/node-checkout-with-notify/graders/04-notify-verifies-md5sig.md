---
type: llm
focus: trace
weight: 1
---

The notify handler parses form-urlencoded data (not JSON) and recomputes md5sig from merchant_id, order_id, payhere_amount, payhere_currency, status_code and the hashed secret before trusting the payment
