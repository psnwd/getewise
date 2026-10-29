# Gateway IDs and Bank MIDs

Use in `payment_gateway_id` (one) or `multiple_payment_gateway_ids` (`40|44|96`).

| ID | Gateway | ID | Gateway |
|---|---|---|---|
| 2 | eZ Cash (LKR) | 42 | Genie Visa/Master (LKR) |
| 3 | mCash (LKR) | 43 | Cargills Visa/Master (LKR) |
| 4 / 8 | NTB AMEX (LKR / USD) | 44 | Cargills Token (LKR) |
| 5 | Sampath Vishwa (LKR) | 45 | UPay (LKR) |
| 16 | DFCC Wallet (LKR) | 46 / 47 | HNB (LKR / USD) |
| 35 | FriMi (LKR) | 52 | Promotional (V/M, LKR) |
| 36 / 37 | Seylan (LKR / USD) | 96 | Lanka QR |
| 38 / 39 | Commercial Token (LKR / USD) | 40 / 41 | Commercial Bank MPGS (LKR / USD) |

EMI IDs (LKR): NTB AMEX 23-28 (3, 6, 12, 20, 24, 36 months); HNB 48-51 (3, 6, 12, 24); DFCC 53-56 and 66-72 (3, 6, 7, 9, 12, 15, 18, 24, 27, 36, 41); Commercial 57-65 (3, 6, 9, 12, 18, 24, 36, 48, 60); NDB 75-81 (6, 9, 12, 18, 24, 36, 60); Seylan 90-92 (6, 12, 24); Union Bank 97-102 (3, 6, 12, 18, 24, 36).
Gateways are enabled per merchant: an ID your account doesn't have gives error 414/415.

## Bank MIDs (Token V2 / bank-level)
| Integration | Staging | Live |
|---|---|---|
| Token | TESTWEBXPATOKLKR | WEBXPATOKLKR |
| Non-token | TESTWEBXPAYNOLKR | WEBXPAYNOLKR |
| CUP | DFCCPAYCORPTOKENLKR | DFCCPAYCORPTOKENLKR |
| Amex | TEST9170137012 | 9170137012 |
Which MID applies to your account is set at onboarding.
