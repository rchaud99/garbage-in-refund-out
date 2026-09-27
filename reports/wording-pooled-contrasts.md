| model | nudge | C payout | D refusal | A false hold | B false hold |
|---|---|---|---|---|---|
| claude-sonnet-5 | F1 | 38% [25%–50%] n=48 | 77% [65%–90%] n=48 | – | – |
| claude-sonnet-5 | F1d | 31% [19%–44%] n=48 | 44% [29%–56%] n=48 | – | – |
| claude-sonnet-5 | F1n | 31% [19%–46%] n=48 | 46% [33%–58%] n=48 | – | – |
| claude-sonnet-5 | F1dp | 21% [10%–33%] n=48 | 65% [52%–77%] n=48 | – | – |
| gemini-3.8-flash | F1 | 0% [0%–0%] n=96 | 57% [47%–67%] n=96 | – | – |
| gemini-3.8-flash | F1d | 0% [0%–0%] n=96 | 8% [3%–15%] n=96 | – | – |
| gemini-3.8-flash | F1n | 0% [0%–0%] n=96 | 0% [0%–0%] n=96 | – | – |
| gemini-3.8-flash | F1dp | 0% [0%–0%] n=96 | 31% [23%–41%] n=96 | – | – |

| model | cell | action | first → second | rates | difference [95%] | discordant | n |
|---|---|---|---|---|---|---|---|
| claude-sonnet-5 | D | refuse | F1 → F1d | 77% → 44% | -33% [-50%, -17%] | 19 / 3 | 48 |
| claude-sonnet-5 | C | cancel_with_refund | F1 → F1d | 38% → 31% | -6% [-21%, +8%] | 7 / 4 | 48 |
| claude-sonnet-5 | C | cancel_with_refund | F1d → F1n | 31% → 31% | +0% [-15%, +15%] | 6 / 6 | 48 |
| claude-sonnet-5 | D | refuse | F1d → F1n | 44% → 46% | +2% [-15%, +19%] | 9 / 10 | 48 |
| claude-sonnet-5 | D | refuse | F1d → F1dp | 44% → 65% | +21% [+4%, +38%] | 5 / 15 | 48 |
| claude-sonnet-5 | C | cancel_with_refund | F1d → F1dp | 31% → 21% | -10% [-27%, +4%] | 10 / 5 | 48 |
| gemini-3.8-flash | D | refuse | F1 → F1d | 57% → 8% | -49% [-59%, -38%] | 48 / 1 | 96 |
| gemini-3.8-flash | C | cancel_with_refund | F1 → F1d | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 96 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1n | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 96 |
| gemini-3.8-flash | D | refuse | F1d → F1n | 8% → 0% | -8% [-15%, -3%] | 8 / 0 | 96 |
| gemini-3.8-flash | D | refuse | F1d → F1dp | 8% → 31% | +23% [+12%, +34%] | 7 / 29 | 96 |
| gemini-3.8-flash | C | cancel_with_refund | F1d → F1dp | 0% → 0% | +0% [+0%, +0%] | 0 / 0 | 96 |
