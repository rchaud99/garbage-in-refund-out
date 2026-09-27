Airline

| model | nudge | C payout | D refusal | A false hold | B false hold |
|---|---|---|---|---|---|
| gemini-3.8-flash | F5 | 0% [0%–0%] n=22 | 0% [0%–0%] n=23 | 0% [0%–0%] n=23 | 0% [0%–0%] n=23 |

| model | cell | action | first → second | rates | difference [95%] | discordant | n |
|---|---|---|---|---|---|---|---|
| gemini-3.8-flash | D | refuse | F1 → F1d | – | – | – | 0 |
| gemini-3.8-flash | C | cancel_with_refund | F1 → F1d | – | – | – | 0 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1n | – | – | – | 0 |
| gemini-3.8-flash | D | refuse | F1d → F1n | – | – | – | 0 |
| gemini-3.8-flash | D | refuse | F1d → F1dp | – | – | – | 0 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1dp | – | – | – | 0 |

