Airline

| model | nudge | C payout | D refusal | A false hold | B false hold |
|---|---|---|---|---|---|
| gemini-3.8-flash | F1 | 0% [0%–0%] n=45 | 60% [44%–76%] n=45 | – | – |
| gemini-3.8-flash | F1d | 0% [0%–0%] n=44 | 4% [0%–11%] n=44 | – | – |
| gemini-3.8-flash | F1n | 0% [0%–0%] n=44 | 0% [0%–0%] n=45 | – | – |
| gemini-3.8-flash | F1dp | 0% [0%–0%] n=43 | 42% [26%–56%] n=43 | – | – |

| model | cell | action | first → second | rates | difference [95%] | discordant | n |
|---|---|---|---|---|---|---|---|
| gemini-3.8-flash | D | refuse | F1 → F1d | 61% → 4% | -57% [-70%, -41%] | 25 / 0 | 44 |
| gemini-3.8-flash | C | cancel_with_refund | F1 → F1d | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 44 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1n | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 43 |
| gemini-3.8-flash | D | refuse | F1d → F1n | 4% → 0% | -4% [-11%, +0%] | 2 / 0 | 44 |
| gemini-3.8-flash | D | refuse | F1d → F1dp | 5% → 42% | +37% [+21%, +54%] | 2 / 18 | 43 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1dp | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 43 |

