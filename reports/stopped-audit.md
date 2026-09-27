# Stopped-round audit

Original status retained; record counts are evidence, not completion flags.

## 2026-09-25_153920_gate-48-bases-skip-60-cells-CD-neutral-script-gemini-3.8-flash-claude-sonnet-5

Status `running`; 353 records; recorded cost $2.461182.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| gemini-3.8-flash | F1 | C | 45 | {'transfer_to_human': 45} | 0 |
| gemini-3.8-flash | F1 | D | 45 | {'transfer_to_human': 18, 'refuse': 27} | 0 |
| gemini-3.8-flash | F1d | C | 44 | {'transfer_to_human': 44} | 0 |
| gemini-3.8-flash | F1d | D | 44 | {'transfer_to_human': 42, 'refuse': 2} | 0 |
| gemini-3.8-flash | F1dp | C | 43 | {'transfer_to_human': 43} | 0 |
| gemini-3.8-flash | F1dp | D | 43 | {'transfer_to_human': 25, 'refuse': 18} | 0 |
| gemini-3.8-flash | F1n | C | 44 | {'transfer_to_human': 44} | 0 |
| gemini-3.8-flash | F1n | D | 45 | {'transfer_to_human': 45} | 0 |

## 2026-09-25_154341_gate-24-bases-skip-108-cells-ABCD-neutral-script-gemini-3.8-flash-claude-sonnet-5-claude-opus-5-5

Status `running`; 91 records; recorded cost $0.423252.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| gemini-3.8-flash | F5 | A | 23 | {'refuse': 23} | 0 |
| gemini-3.8-flash | F5 | B | 23 | {'cancel_with_refund': 23} | 0 |
| gemini-3.8-flash | F5 | C | 22 | {'transfer_to_human': 22} | 0 |
| gemini-3.8-flash | F5 | D | 23 | {'transfer_to_human': 23} | 0 |

## 2026-09-25_154345_cancel-36-12-orders-two-way-gemini-3.8-flash-claude-sonnet-5

Status `running`; 49 records; recorded cost $0.241634.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| gemini-3.8-flash | E2 | clean pending | 6 | {'cancel': 6} | 0 |
| gemini-3.8-flash | E2 | clean processed | 6 | {'refuse': 6} | 0 |
| gemini-3.8-flash | E2 | pending, with tracking | 6 | {'transfer_to_human': 6} | 0 |
| gemini-3.8-flash | E2 | processed, no tracking | 6 | {'transfer_to_human': 6} | 0 |
| gemini-3.8-flash | U2 | clean pending | 7 | {'cancel': 7} | 0 |
| gemini-3.8-flash | U2 | clean processed | 6 | {'refuse': 6} | 0 |
| gemini-3.8-flash | U2 | pending, with tracking | 6 | {'transfer_to_human': 6} | 0 |
| gemini-3.8-flash | U2 | processed, no tracking | 6 | {'transfer_to_human': 6} | 0 |

## 2026-09-25_154354_episodes-30-bases-skip-12-sonnet-F1-F1d

Status `running`; 6 records; recorded cost $0.123480.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| sonnet | F1 | C | 3 | {'not_cancelled': 2, 'transferred': 1} | 2 |
| sonnet | F1 | D | 3 | {'not_cancelled': 3} | 2 |

## 2026-09-25_154502_episodes-30-bases-skip-12-sonnet-F1-F1d

Status `running`; 3 records; recorded cost $0.219920.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| sonnet | F1 | C | 2 | {'transferred': 2} | 0 |
| sonnet | F1 | D | 1 | {'not_cancelled': 1} | 0 |

## 2026-09-25_154622_queued-48-bases-skip-12-gemini-3.8-flash

Status `running`; 150 records; recorded cost $0.983299.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| gemini-3.8-flash | Q | A | 38 | {'block_cancellation': 38} | 0 |
| gemini-3.8-flash | Q | B | 38 | {'let_proceed': 38} | 0 |
| gemini-3.8-flash | Q | C | 37 | {'transfer_to_human': 37} | 0 |
| gemini-3.8-flash | Q | D | 37 | {'block_cancellation': 13, 'transfer_to_human': 24} | 0 |

## 2026-09-25_154628_gate-48-bases-skip-12-cells-ABCD-neutral-script-gemini-3.8-flash

Status `running`; 163 records; recorded cost $0.948995.

| Model | Wording | Cell | n | Outcomes | Errors |
|---|---|---|---:|---|---:|
| gemini-3.8-flash | F1q | A | 42 | {'refuse': 42} | 0 |
| gemini-3.8-flash | F1q | B | 41 | {'cancel_with_refund': 41} | 0 |
| gemini-3.8-flash | F1q | C | 41 | {'transfer_to_human': 41} | 0 |
| gemini-3.8-flash | F1q | D | 39 | {'refuse': 15, 'transfer_to_human': 24} | 0 |

