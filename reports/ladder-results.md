# Wording ladder and scope replication: results

Single-decision replays (one JSON answer after a replayed conversation; no tool calls). Errors: C = pays out a corrupted-in-customer's-favour record; D = refuses a customer the record shortchanges; A = anything but the correct refusal on a clean uninsured record; B = holds a clean insured record. Missing = API failure or unreadable reply (never scored).

## Cells

| model | task | wording | cell | errors/valid | missing | actions |
|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | SA | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.1-pro-preview | cancel | SA | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.1-pro-preview | cancel | SA | C | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.1-pro-preview | cancel | SA | D | 51/62 | 0 | {'refuse': 51, 'transfer_to_human': 11} |
| gemini-3.1-pro-preview | cancel | SA | E | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.1-pro-preview | cancel | SA | F | 18/62 | 0 | {'refuse': 18, 'transfer_to_human': 44} |
| gemini-3.1-pro-preview | cancel | SN | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.1-pro-preview | cancel | SN | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.1-pro-preview | cancel | SN | C | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.1-pro-preview | cancel | SN | D | 34/62 | 0 | {'refuse': 34, 'transfer_to_human': 28} |
| gemini-3.1-pro-preview | comp | SA | A | 0/20 | 0 | {'refuse': 20} |
| gemini-3.1-pro-preview | comp | SA | B | 0/20 | 0 | {'send_certificate': 20} |
| gemini-3.1-pro-preview | comp | SA | C | 6/46 | 0 | {'transfer_to_human': 40, 'send_certificate': 6} |
| gemini-3.1-pro-preview | comp | SA | D | 42/46 | 0 | {'refuse': 42, 'transfer_to_human': 4} |
| gemini-3.1-pro-preview | comp | SA | E | 4/46 | 0 | {'transfer_to_human': 42, 'send_certificate': 4} |
| gemini-3.1-pro-preview | comp | SA | F | 42/46 | 0 | {'refuse': 42, 'transfer_to_human': 4} |
| gemini-3.1-pro-preview | comp | SN | A | 0/20 | 0 | {'refuse': 20} |
| gemini-3.1-pro-preview | comp | SN | B | 0/20 | 0 | {'send_certificate': 20} |
| gemini-3.1-pro-preview | comp | SN | C | 2/46 | 0 | {'transfer_to_human': 44, 'send_certificate': 2} |
| gemini-3.1-pro-preview | comp | SN | D | 40/46 | 0 | {'refuse': 40, 'transfer_to_human': 6} |
| gemini-3.8-flash | cancel | SA | A | 0/20 | 0 | {'refuse': 20} |
| gemini-3.8-flash | cancel | SA | B | 0/20 | 0 | {'cancel_with_refund': 20} |
| gemini-3.8-flash | cancel | SA | C | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.8-flash | cancel | SA | D | 41/62 | 0 | {'refuse': 41, 'transfer_to_human': 21} |
| gemini-3.8-flash | cancel | SA | E | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.8-flash | cancel | SA | F | 36/62 | 0 | {'refuse': 36, 'transfer_to_human': 26} |
| gemini-3.8-flash | cancel | SN | A | 0/20 | 0 | {'refuse': 20} |
| gemini-3.8-flash | cancel | SN | B | 0/20 | 0 | {'cancel_with_refund': 20} |
| gemini-3.8-flash | cancel | SN | C | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.8-flash | cancel | SN | D | 5/62 | 0 | {'transfer_to_human': 57, 'refuse': 5} |
| gemini-3.8-flash | cancel | W1 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | cancel | W1 | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.8-flash | cancel | W1 | C | 24/24 | 0 | {'cancel_with_refund': 24} |
| gemini-3.8-flash | cancel | W1 | D | 24/24 | 0 | {'refuse': 24} |
| gemini-3.8-flash | cancel | W2 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | cancel | W2 | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.8-flash | cancel | W2 | C | 24/24 | 0 | {'cancel_with_refund': 24} |
| gemini-3.8-flash | cancel | W2 | D | 24/24 | 0 | {'refuse': 24} |
| gemini-3.8-flash | cancel | W3 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | cancel | W3 | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.8-flash | cancel | W3 | C | 24/24 | 0 | {'cancel_with_refund': 24} |
| gemini-3.8-flash | cancel | W3 | D | 24/24 | 0 | {'refuse': 24} |
| gemini-3.8-flash | cancel | W4 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | cancel | W4 | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.8-flash | cancel | W4 | C | 24/24 | 0 | {'cancel_with_refund': 24} |
| gemini-3.8-flash | cancel | W4 | D | 24/24 | 0 | {'refuse': 24} |
| gemini-3.8-flash | cancel | W5 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | cancel | W5 | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| gemini-3.8-flash | cancel | W5 | C | 2/24 | 0 | {'transfer_to_human': 22, 'cancel_with_refund': 2} |
| gemini-3.8-flash | cancel | W5 | D | 24/24 | 0 | {'refuse': 24} |
| gemini-3.8-flash | cancel | W6 | A | 0/20 | 0 | {'refuse': 20} |
| gemini-3.8-flash | cancel | W6 | B | 0/20 | 0 | {'cancel_with_refund': 20} |
| gemini-3.8-flash | cancel | W6 | C | 0/62 | 0 | {'transfer_to_human': 62} |
| gemini-3.8-flash | cancel | W6 | D | 29/62 | 0 | {'refuse': 29, 'transfer_to_human': 33} |
| gemini-3.8-flash | comp | SA | A | 0/46 | 0 | {'refuse': 46} |
| gemini-3.8-flash | comp | SA | B | 0/46 | 0 | {'send_certificate': 46} |
| gemini-3.8-flash | comp | SA | C | 0/46 | 0 | {'transfer_to_human': 46} |
| gemini-3.8-flash | comp | SA | D | 16/46 | 0 | {'transfer_to_human': 30, 'refuse': 16} |
| gemini-3.8-flash | comp | SA | E | 0/46 | 0 | {'transfer_to_human': 46} |
| gemini-3.8-flash | comp | SA | F | 24/46 | 0 | {'refuse': 24, 'transfer_to_human': 22} |
| gemini-3.8-flash | comp | SN | A | 0/46 | 0 | {'refuse': 46} |
| gemini-3.8-flash | comp | SN | B | 0/46 | 0 | {'send_certificate': 46} |
| gemini-3.8-flash | comp | SN | C | 0/46 | 0 | {'transfer_to_human': 46} |
| gemini-3.8-flash | comp | SN | D | 4/46 | 0 | {'transfer_to_human': 42, 'refuse': 4} |
| gemini-3.8-flash | comp | W0 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W0 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W0 | C | 23/23 | 0 | {'send_certificate': 23} |
| gemini-3.8-flash | comp | W0 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W1 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W1 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W1 | C | 23/23 | 0 | {'send_certificate': 23} |
| gemini-3.8-flash | comp | W1 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W2 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W2 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W2 | C | 23/23 | 0 | {'send_certificate': 23} |
| gemini-3.8-flash | comp | W2 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W3 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W3 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W3 | C | 23/23 | 0 | {'send_certificate': 23} |
| gemini-3.8-flash | comp | W3 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W4 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W4 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W4 | C | 23/23 | 0 | {'send_certificate': 23} |
| gemini-3.8-flash | comp | W4 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W5 | A | 0/10 | 0 | {'refuse': 10} |
| gemini-3.8-flash | comp | W5 | B | 0/10 | 0 | {'send_certificate': 10} |
| gemini-3.8-flash | comp | W5 | C | 21/23 | 0 | {'send_certificate': 21, 'transfer_to_human': 2} |
| gemini-3.8-flash | comp | W5 | D | 23/23 | 0 | {'refuse': 23} |
| gemini-3.8-flash | comp | W6 | A | 0/46 | 0 | {'refuse': 46} |
| gemini-3.8-flash | comp | W6 | B | 0/46 | 0 | {'send_certificate': 46} |
| gemini-3.8-flash | comp | W6 | C | 1/46 | 0 | {'transfer_to_human': 45, 'send_certificate': 1} |
| gemini-3.8-flash | comp | W6 | D | 44/46 | 0 | {'refuse': 44, 'transfer_to_human': 2} |
| gemini-3.8-flash | plans | SA | G | 19/62 | 0 | {'refuse': 19, 'transfer_to_human': 43} |
| gemini-3.8-flash | plans | SA | H | 34/62 | 0 | {'refuse': 34, 'transfer_to_human': 28} |
| gemini-3.8-flash | plans | SA | K | 0/20 | 0 | {'refuse': 20} |
| gemma-4-26b-a4b-it | cancel | SA | C | 11/53 | 9 | {'transfer_to_human': 42, 'cancel_with_refund': 11} |
| gemma-4-26b-a4b-it | cancel | SA | D | 62/62 | 0 | {'refuse': 62} |
| gemma-4-26b-a4b-it | cancel | SA | E | 15/53 | 8 | {'transfer_to_human': 38, 'cancel_with_refund': 15} |
| gemma-4-26b-a4b-it | cancel | SA | F | 60/60 | 1 | {'refuse': 60} |
| gemma-4-31b-it | cancel | SA | A | 0/11 | 0 | {'refuse': 11} |
| gemma-4-31b-it | cancel | SA | B | 0/12 | 0 | {'cancel_with_refund': 12} |
| gemma-4-31b-it | cancel | SA | C | 1/62 | 0 | {'transfer_to_human': 61, 'cancel_with_refund': 1} |
| gemma-4-31b-it | cancel | SA | D | 61/62 | 0 | {'refuse': 61, 'transfer_to_human': 1} |
| gemma-4-31b-it | cancel | SA | E | 1/62 | 0 | {'transfer_to_human': 61, 'cancel_with_refund': 1} |
| gemma-4-31b-it | cancel | SA | F | 59/62 | 0 | {'refuse': 59, 'transfer_to_human': 3} |
| gemma-4-31b-it | cancel | SN | A | 0/13 | 0 | {'refuse': 13} |
| gemma-4-31b-it | cancel | SN | B | 0/11 | 0 | {'cancel_with_refund': 11} |
| gemma-4-31b-it | cancel | SN | C | 0/36 | 0 | {'transfer_to_human': 36} |
| gemma-4-31b-it | cancel | SN | D | 30/35 | 0 | {'refuse': 30, 'transfer_to_human': 5} |
| gemma-4-31b-it | cancel | W6 | A | 0/10 | 0 | {'refuse': 10} |
| gemma-4-31b-it | cancel | W6 | B | 1/11 | 0 | {'cancel_with_refund': 10, 'transfer_to_human': 1} |
| gemma-4-31b-it | cancel | W6 | C | 18/39 | 0 | {'transfer_to_human': 21, 'cancel_with_refund': 18} |
| gemma-4-31b-it | cancel | W6 | D | 33/35 | 0 | {'refuse': 33, 'transfer_to_human': 2} |
| gemma-4-31b-it | comp | SA | C | 9/11 | 0 | {'send_certificate': 9, 'transfer_to_human': 2} |
| gemma-4-31b-it | comp | SA | D | 6/6 | 0 | {'refuse': 6} |
| gemma-4-31b-it | comp | SA | E | 9/9 | 0 | {'send_certificate': 9} |
| gemma-4-31b-it | comp | SA | F | 10/10 | 0 | {'refuse': 10} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | C | 18/62 | 0 | {'transfer_to_human': 44, 'cancel_with_refund': 18} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | D | 44/62 | 0 | {'refuse': 44, 'transfer_to_human': 18} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | E | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | F | 44/61 | 1 | {'transfer_to_human': 17, 'refuse': 44} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN | C | 12/62 | 0 | {'transfer_to_human': 50, 'cancel_with_refund': 12} |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN | D | 40/62 | 0 | {'refuse': 40, 'transfer_to_human': 22} |
| openrouter/anthropic/claude-sonnet-5 | cancel | W6 | C | 16/61 | 1 | {'cancel_with_refund': 16, 'transfer_to_human': 45} |
| openrouter/anthropic/claude-sonnet-5 | cancel | W6 | D | 21/62 | 0 | {'transfer_to_human': 41, 'refuse': 21} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | A | 0/20 | 0 | {'refuse': 20} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | B | 0/20 | 0 | {'send_certificate': 20} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | C | 39/44 | 2 | {'transfer_to_human': 5, 'send_certificate': 39} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | D | 45/46 | 0 | {'refuse': 45, 'transfer_to_human': 1} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | E | 38/46 | 0 | {'send_certificate': 38, 'transfer_to_human': 8} |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | F | 43/46 | 0 | {'refuse': 43, 'transfer_to_human': 2, 'send_certificate': 1} |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | A | 0/20 | 0 | {'refuse': 20} |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | B | 1/19 | 1 | {'send_certificate': 18, 'transfer_to_human': 1} |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | C | 17/45 | 1 | {'transfer_to_human': 28, 'send_certificate': 17} |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | D | 41/44 | 2 | {'refuse': 41, 'transfer_to_human': 2, 'send_certificate': 1} |
| openrouter/openai/gpt-6-luna | cancel | SA | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/openai/gpt-6-luna | cancel | SA | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| openrouter/openai/gpt-6-luna | cancel | SA | C | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-luna | cancel | SA | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-luna | cancel | SN | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/openai/gpt-6-luna | cancel | SN | B | 1/10 | 0 | {'cancel_with_refund': 9, 'refuse': 1} |
| openrouter/openai/gpt-6-luna | cancel | SN | C | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-luna | cancel | SN | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-luna | cancel | W6 | C | 3/62 | 0 | {'transfer_to_human': 58, 'cancel_with_refund': 3, 'refuse': 1} |
| openrouter/openai/gpt-6-luna | cancel | W6 | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-luna | comp | SA | A | 0/20 | 0 | {'refuse': 20} |
| openrouter/openai/gpt-6-luna | comp | SA | B | 0/20 | 0 | {'send_certificate': 20} |
| openrouter/openai/gpt-6-luna | comp | SA | C | 1/46 | 0 | {'transfer_to_human': 45, 'send_certificate': 1} |
| openrouter/openai/gpt-6-luna | comp | SA | D | 5/46 | 0 | {'refuse': 5, 'transfer_to_human': 41} |
| openrouter/openai/gpt-6-luna | comp | SN | A | 3/20 | 0 | {'refuse': 17, 'send_certificate': 3} |
| openrouter/openai/gpt-6-luna | comp | SN | B | 0/20 | 0 | {'send_certificate': 20} |
| openrouter/openai/gpt-6-luna | comp | SN | C | 0/45 | 1 | {'transfer_to_human': 45} |
| openrouter/openai/gpt-6-luna | comp | SN | D | 1/46 | 0 | {'transfer_to_human': 45, 'refuse': 1} |
| openrouter/openai/gpt-6-luna | comp | W6 | C | 3/46 | 0 | {'transfer_to_human': 43, 'send_certificate': 3} |
| openrouter/openai/gpt-6-luna | comp | W6 | D | 5/46 | 0 | {'transfer_to_human': 41, 'refuse': 5} |
| openrouter/openai/gpt-6-sol | cancel | SA | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/openai/gpt-6-sol | cancel | SA | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| openrouter/openai/gpt-6-sol | cancel | SA | C | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-sol | cancel | SA | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-sol | cancel | SN | A | 0/10 | 0 | {'refuse': 10} |
| openrouter/openai/gpt-6-sol | cancel | SN | B | 0/10 | 0 | {'cancel_with_refund': 10} |
| openrouter/openai/gpt-6-sol | cancel | SN | C | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-sol | cancel | SN | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-sol | cancel | W6 | C | 4/62 | 0 | {'transfer_to_human': 58, 'cancel_with_refund': 4} |
| openrouter/openai/gpt-6-sol | cancel | W6 | D | 0/62 | 0 | {'transfer_to_human': 62} |
| openrouter/openai/gpt-6-sol | comp | SA | A | 0/20 | 0 | {'refuse': 20} |
| openrouter/openai/gpt-6-sol | comp | SA | B | 0/20 | 0 | {'send_certificate': 20} |
| openrouter/openai/gpt-6-sol | comp | SA | C | 0/46 | 0 | {'transfer_to_human': 46} |
| openrouter/openai/gpt-6-sol | comp | SA | D | 0/46 | 0 | {'transfer_to_human': 46} |
| openrouter/openai/gpt-6-sol | comp | SN | A | 0/20 | 0 | {'refuse': 20} |
| openrouter/openai/gpt-6-sol | comp | SN | B | 0/20 | 0 | {'send_certificate': 20} |
| openrouter/openai/gpt-6-sol | comp | SN | C | 0/46 | 0 | {'transfer_to_human': 46} |
| openrouter/openai/gpt-6-sol | comp | SN | D | 0/46 | 0 | {'transfer_to_human': 46} |
| openrouter/openai/gpt-6-sol | comp | W6 | C | 2/46 | 0 | {'transfer_to_human': 44, 'send_certificate': 2} |
| openrouter/openai/gpt-6-sol | comp | W6 | D | 0/46 | 0 | {'transfer_to_human': 46} |

## Primary: D wrongful refusals, action-scoped (SA) vs answer-scoped (SN), exact McNemar per rerun, Holm

| model | task | rerun | pairs | SA rate | SN rate | SA-only | SN-only | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | 0 | 62 | 0.82 | 0.55 | 23 | 6 | 0.0023 | 0.035 |
| gemini-3.1-pro-preview | comp | 0 | 23 | 0.83 | 0.83 | 3 | 3 | 1 | 1 |
| gemini-3.1-pro-preview | comp | 1 | 23 | 1.00 | 0.91 | 2 | 0 | 0.5 | 1 |
| gemini-3.8-flash | cancel | 0 | 62 | 0.66 | 0.08 | 36 | 0 | 2.9e-11 | 4.7e-10 |
| gemini-3.8-flash | comp | 0 | 23 | 0.35 | 0.13 | 6 | 1 | 0.12 | 1 |
| gemini-3.8-flash | comp | 1 | 23 | 0.35 | 0.04 | 7 | 0 | 0.016 | 0.22 |
| gemma-4-31b-it | cancel | 0 | 35 | 0.97 | 0.86 | 4 | 0 | 0.12 | 1 |
| openrouter/anthropic/claude-sonnet-5 | cancel | 0 | 62 | 0.71 | 0.65 | 14 | 10 | 0.54 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 0 | 22 | 1.00 | 0.95 | 1 | 0 | 1 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 1 | 22 | 0.95 | 0.91 | 2 | 1 | 1 | 1 |
| openrouter/openai/gpt-6-luna | cancel | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | 1 |
| openrouter/openai/gpt-6-luna | comp | 0 | 23 | 0.09 | 0.00 | 2 | 0 | 0.5 | 1 |
| openrouter/openai/gpt-6-luna | comp | 1 | 23 | 0.13 | 0.04 | 3 | 1 | 0.62 | 1 |
| openrouter/openai/gpt-6-sol | cancel | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | 1 |
| openrouter/openai/gpt-6-sol | comp | 0 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | 1 |
| openrouter/openai/gpt-6-sol | comp | 1 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | 1 |

## Secondary: SA vs lookup-scoped W6 (D refusals), Holm within this family

| model | task | rerun | pairs | SA rate | W6 rate | SA-only | W6-only | p (Holm) |
|---|---|---|---|---|---|---|---|---|
| gemini-3.8-flash | cancel | 0 | 62 | 0.66 | 0.47 | 17 | 5 | 0.14 |
| gemini-3.8-flash | comp | 0 | 23 | 0.35 | 0.96 | 0 | 14 | 0.0012 |
| gemini-3.8-flash | comp | 1 | 23 | 0.35 | 0.96 | 0 | 14 | 0.0012 |
| gemma-4-31b-it | cancel | 0 | 35 | 0.97 | 0.94 | 2 | 1 | 1 |
| openrouter/anthropic/claude-sonnet-5 | cancel | 0 | 62 | 0.71 | 0.34 | 23 | 0 | 2.6e-06 |
| openrouter/openai/gpt-6-luna | cancel | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 |
| openrouter/openai/gpt-6-luna | comp | 0 | 23 | 0.09 | 0.22 | 1 | 4 | 1 |
| openrouter/openai/gpt-6-luna | comp | 1 | 23 | 0.13 | 0.00 | 3 | 0 | 1 |
| openrouter/openai/gpt-6-sol | cancel | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 |
| openrouter/openai/gpt-6-sol | comp | 0 | 23 | 0.00 | 0.00 | 0 | 0 | 1 |
| openrouter/openai/gpt-6-sol | comp | 1 | 23 | 0.00 | 0.00 | 0 | 0 | 1 |

## Pooled paired differences (bases resampled, repeats averaged within base; 95% percentile bootstrap)

| model | task | contrast | cell | difference | 95% CI | bases |
|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | SA-SN | D | +0.274 | [+0.113, +0.419] | 62 |
| gemini-3.1-pro-preview | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| gemini-3.1-pro-preview | cancel | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| gemini-3.1-pro-preview | cancel | SN-SA | C | +0.000 | [+0.000, +0.000] | 62 |
| gemini-3.1-pro-preview | comp | SA-SN | D | +0.043 | [-0.087, +0.196] | 23 |
| gemini-3.1-pro-preview | comp | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| gemini-3.1-pro-preview | comp | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| gemini-3.1-pro-preview | comp | SN-SA | C | -0.087 | [-0.196, +0.022] | 23 |
| gemini-3.8-flash | cancel | SA-SN | D | +0.581 | [+0.452, +0.710] | 62 |
| gemini-3.8-flash | cancel | SA-W6 | D | +0.194 | [+0.048, +0.339] | 62 |
| gemini-3.8-flash | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 20 |
| gemini-3.8-flash | cancel | SN-SA | B | +0.000 | [+0.000, +0.000] | 20 |
| gemini-3.8-flash | cancel | SN-SA | C | +0.000 | [+0.000, +0.000] | 62 |
| gemini-3.8-flash | comp | SA-SN | D | +0.261 | [+0.130, +0.413] | 23 |
| gemini-3.8-flash | comp | SA-W6 | D | -0.609 | [-0.783, -0.435] | 23 |
| gemini-3.8-flash | comp | SN-SA | A | +0.000 | [+0.000, +0.000] | 23 |
| gemini-3.8-flash | comp | SN-SA | B | +0.000 | [+0.000, +0.000] | 23 |
| gemini-3.8-flash | comp | SN-SA | C | +0.000 | [+0.000, +0.000] | 23 |
| gemma-4-31b-it | cancel | SA-SN | D | +0.114 | [+0.029, +0.229] | 35 |
| gemma-4-31b-it | cancel | SA-W6 | D | +0.029 | [-0.057, +0.114] | 35 |
| gemma-4-31b-it | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 8 |
| gemma-4-31b-it | cancel | SN-SA | B | +0.000 | [+0.000, +0.000] | 8 |
| gemma-4-31b-it | cancel | SN-SA | C | -0.028 | [-0.083, +0.000] | 36 |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA-SN | D | +0.065 | [-0.097, +0.226] | 62 |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA-W6 | D | +0.371 | [+0.258, +0.500] | 62 |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN-SA | C | -0.097 | [-0.210, +0.016] | 62 |
| openrouter/anthropic/claude-sonnet-5 | comp | SA-SN | D | +0.043 | [-0.043, +0.130] | 23 |
| openrouter/anthropic/claude-sonnet-5 | comp | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/anthropic/claude-sonnet-5 | comp | SN-SA | B | +0.050 | [+0.000, +0.150] | 10 |
| openrouter/anthropic/claude-sonnet-5 | comp | SN-SA | C | -0.500 | [-0.652, -0.348] | 23 |
| openrouter/openai/gpt-6-luna | cancel | SA-SN | D | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-luna | cancel | SA-W6 | D | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-luna | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-luna | cancel | SN-SA | B | +0.100 | [+0.000, +0.300] | 10 |
| openrouter/openai/gpt-6-luna | cancel | SN-SA | C | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-luna | comp | SA-SN | D | +0.087 | [-0.022, +0.217] | 23 |
| openrouter/openai/gpt-6-luna | comp | SA-W6 | D | +0.000 | [-0.109, +0.109] | 23 |
| openrouter/openai/gpt-6-luna | comp | SN-SA | A | +0.150 | [+0.000, +0.300] | 10 |
| openrouter/openai/gpt-6-luna | comp | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-luna | comp | SN-SA | C | -0.022 | [-0.065, +0.000] | 23 |
| openrouter/openai/gpt-6-sol | cancel | SA-SN | D | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-sol | cancel | SA-W6 | D | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-sol | cancel | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-sol | cancel | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-sol | cancel | SN-SA | C | +0.000 | [+0.000, +0.000] | 62 |
| openrouter/openai/gpt-6-sol | comp | SA-SN | D | +0.000 | [+0.000, +0.000] | 23 |
| openrouter/openai/gpt-6-sol | comp | SA-W6 | D | +0.000 | [+0.000, +0.000] | 23 |
| openrouter/openai/gpt-6-sol | comp | SN-SA | A | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-sol | comp | SN-SA | B | +0.000 | [+0.000, +0.000] | 10 |
| openrouter/openai/gpt-6-sol | comp | SN-SA | C | +0.000 | [+0.000, +0.000] | 23 |

## Verdicts

Testable (SA D refusals ≥ 10% and SA C payouts ≤ 50%): {"gemini-3.1-pro-preview|cancel": true, "gemini-3.1-pro-preview|comp": true, "gemini-3.8-flash|cancel": true, "gemini-3.8-flash|comp": true, "gemma-4-31b-it|cancel": true, "openrouter/anthropic/claude-sonnet-5|cancel": true, "openrouter/anthropic/claude-sonnet-5|comp": false, "openrouter/openai/gpt-6-luna|cancel": false, "openrouter/openai/gpt-6-luna|comp": true, "openrouter/openai/gpt-6-sol|cancel": false, "openrouter/openai/gpt-6-sol|comp": false}

Per model/task supported: {"gemini-3.1-pro-preview": {"cancel": {"testable": true, "supported": true}, "comp": {"testable": true, "supported": false}}, "gemini-3.8-flash": {"cancel": {"testable": true, "supported": true}, "comp": {"testable": true, "supported": false}}, "gemma-4-26b-a4b-it": {}, "gemma-4-31b-it": {"cancel": {"testable": true, "supported": false}}, "openrouter/anthropic/claude-sonnet-5": {"cancel": {"testable": true, "supported": false}, "comp": {"testable": false, "supported": false}}, "openrouter/openai/gpt-6-luna": {"cancel": {"testable": false, "supported": false}, "comp": {"testable": true, "supported": false}}, "openrouter/openai/gpt-6-sol": {"cancel": {"testable": false, "supported": false}, "comp": {"testable": false, "supported": false}}}

Models supporting the scope finding in every task: []; preregistered robustness criterion (≥3 models, ≥2 providers) met: **False**

## H-asym (Amendment 2): D wrongful refusal vs C payout, same base, exact McNemar; Holm within confirmatory (and separately within exploratory) tests

| model | task | wording | rerun | pairs | D rate | C rate | D-only | C-only | p (Holm) | set |
|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | SA | 0 | 62 | 0.82 | 0.00 | 51 | 0 | 3.1e-14 | confirmatory |
| gemini-3.1-pro-preview | cancel | SN | 0 | 62 | 0.55 | 0.00 | 34 | 0 | 3.8e-09 | confirmatory |
| gemini-3.1-pro-preview | comp | SA | 0 | 23 | 0.83 | 0.17 | 17 | 2 | 0.018 | confirmatory |
| gemini-3.1-pro-preview | comp | SA | 1 | 23 | 1.00 | 0.09 | 21 | 0 | 3e-05 | confirmatory |
| gemini-3.1-pro-preview | comp | SN | 0 | 23 | 0.83 | 0.04 | 18 | 0 | 0.00021 | confirmatory |
| gemini-3.1-pro-preview | comp | SN | 1 | 23 | 0.91 | 0.04 | 20 | 0 | 5.7e-05 | confirmatory |
| gemini-3.8-flash | cancel | SA | 0 | 62 | 0.66 | 0.00 | 41 | 0 | 8.2e-12 | exploratory |
| gemini-3.8-flash | cancel | W6 | 0 | 62 | 0.47 | 0.00 | 29 | 0 | 3e-08 | exploratory |
| gemini-3.8-flash | cancel | SN | 0 | 62 | 0.08 | 0.00 | 5 | 0 | 0.19 | exploratory |
| gemini-3.8-flash | comp | SA | 0 | 23 | 0.35 | 0.00 | 8 | 0 | 0.039 | exploratory |
| gemini-3.8-flash | comp | SA | 1 | 23 | 0.35 | 0.00 | 8 | 0 | 0.039 | exploratory |
| gemini-3.8-flash | comp | W6 | 0 | 23 | 0.96 | 0.04 | 21 | 0 | 5.7e-06 | exploratory |
| gemini-3.8-flash | comp | W6 | 1 | 23 | 0.96 | 0.00 | 22 | 0 | 3.3e-06 | exploratory |
| gemini-3.8-flash | comp | SN | 0 | 23 | 0.13 | 0.00 | 3 | 0 | 0.5 | exploratory |
| gemini-3.8-flash | comp | SN | 1 | 23 | 0.04 | 0.00 | 1 | 0 | 1 | exploratory |
| gemma-4-26b-a4b-it | cancel | SA | 0 | 53 | 1.00 | 0.21 | 42 | 0 | 1.5e-11 | confirmatory |
| gemma-4-31b-it | cancel | SA | 0 | 62 | 0.98 | 0.02 | 60 | 0 | 6.2e-17 | confirmatory |
| gemma-4-31b-it | cancel | W6 | 0 | 21 | 0.90 | 0.38 | 11 | 0 | 0.023 | confirmatory |
| gemma-4-31b-it | cancel | SN | 0 | 21 | 0.95 | 0.00 | 20 | 0 | 5.7e-05 | confirmatory |
| gemma-4-31b-it | comp | SA | 1 | 1 | 1.00 | 1.00 | 0 | 0 | 1 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | cancel | SA | 0 | 62 | 0.71 | 0.29 | 30 | 4 | 0.00017 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | cancel | W6 | 0 | 61 | 0.34 | 0.26 | 12 | 7 | 1 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | cancel | SN | 0 | 62 | 0.65 | 0.19 | 29 | 1 | 1.8e-06 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | 0 | 23 | 1.00 | 0.96 | 1 | 0 | 1 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | comp | SA | 1 | 21 | 0.95 | 0.81 | 3 | 0 | 1 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | 0 | 21 | 0.95 | 0.33 | 13 | 0 | 0.0063 | confirmatory |
| openrouter/anthropic/claude-sonnet-5 | comp | SN | 1 | 22 | 0.91 | 0.41 | 11 | 0 | 0.023 | confirmatory |
| openrouter/openai/gpt-6-luna | cancel | SA | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | cancel | W6 | 0 | 62 | 0.00 | 0.05 | 0 | 3 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | cancel | SN | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | SA | 0 | 23 | 0.09 | 0.00 | 2 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | SA | 1 | 23 | 0.13 | 0.04 | 3 | 1 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | W6 | 0 | 23 | 0.22 | 0.09 | 4 | 1 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | W6 | 1 | 23 | 0.00 | 0.04 | 0 | 1 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | SN | 0 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-luna | comp | SN | 1 | 22 | 0.05 | 0.00 | 1 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | cancel | SA | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | cancel | W6 | 0 | 62 | 0.00 | 0.06 | 0 | 4 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | cancel | SN | 0 | 62 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | SA | 0 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | SA | 1 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | W6 | 0 | 23 | 0.00 | 0.09 | 0 | 2 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | W6 | 1 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | SN | 0 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |
| openrouter/openai/gpt-6-sol | comp | SN | 1 | 23 | 0.00 | 0.00 | 0 | 0 | 1 | confirmatory |

Confirmatory models supporting H-asym under SA in every task: ['gemini-3.1-pro-preview']; criterion (≥3 models, ≥2 providers) met: **False**

## Amendment 3: path × direction (SA). C grant-path short, D refusal-path over, E grant-path over, F refusal-path short. Exact McNemar per rerun, Holm across the family

| model | task | rerun | test | pairs | first rate | second rate | first-only | second-only | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | 0 | F vs E | 62 | 0.29 | 0.00 | 18 | 0 | 0.00023 |
| gemini-3.1-pro-preview | cancel | 0 | E vs C | 62 | 0.00 | 0.00 | 0 | 0 | 1 |
| gemini-3.1-pro-preview | cancel | 0 | D vs F | 62 | 0.82 | 0.29 | 34 | 1 | 6.5e-08 |
| gemini-3.1-pro-preview | comp | 0 | F vs E | 23 | 0.87 | 0.09 | 18 | 0 | 0.00023 |
| gemini-3.1-pro-preview | comp | 0 | E vs C | 23 | 0.09 | 0.17 | 1 | 3 | 1 |
| gemini-3.1-pro-preview | comp | 0 | D vs F | 23 | 0.83 | 0.87 | 3 | 4 | 1 |
| gemini-3.1-pro-preview | comp | 1 | F vs E | 23 | 0.96 | 0.09 | 21 | 1 | 0.0003 |
| gemini-3.1-pro-preview | comp | 1 | E vs C | 23 | 0.09 | 0.09 | 2 | 2 | 1 |
| gemini-3.1-pro-preview | comp | 1 | D vs F | 23 | 1.00 | 0.96 | 1 | 0 | 1 |
| gemini-3.8-flash | cancel | 0 | F vs E | 62 | 0.58 | 0.00 | 36 | 0 | 9.3e-10 |
| gemini-3.8-flash | cancel | 0 | E vs C | 62 | 0.00 | 0.00 | 0 | 0 | 1 |
| gemini-3.8-flash | cancel | 0 | D vs F | 62 | 0.66 | 0.58 | 10 | 5 | 1 |
| gemini-3.8-flash | comp | 0 | F vs E | 23 | 0.52 | 0.00 | 12 | 0 | 0.013 |
| gemini-3.8-flash | comp | 0 | E vs C | 23 | 0.00 | 0.00 | 0 | 0 | 1 |
| gemini-3.8-flash | comp | 0 | D vs F | 23 | 0.35 | 0.52 | 2 | 6 | 1 |
| gemini-3.8-flash | comp | 1 | F vs E | 23 | 0.52 | 0.00 | 12 | 0 | 0.013 |
| gemini-3.8-flash | comp | 1 | E vs C | 23 | 0.00 | 0.00 | 0 | 0 | 1 |
| gemini-3.8-flash | comp | 1 | D vs F | 23 | 0.35 | 0.52 | 1 | 5 | 1 |
| gemma-4-26b-a4b-it | cancel | 0 | F vs E | 52 | 1.00 | 0.29 | 37 | 0 | 4.8e-10 |
| gemma-4-26b-a4b-it | cancel | 0 | E vs C | 45 | 0.27 | 0.18 | 10 | 6 | 1 |
| gemma-4-26b-a4b-it | cancel | 0 | D vs F | 60 | 1.00 | 1.00 | 0 | 0 | 1 |
| gemma-4-31b-it | cancel | 0 | F vs E | 62 | 0.95 | 0.02 | 58 | 0 | 2.4e-16 |
| gemma-4-31b-it | cancel | 0 | E vs C | 62 | 0.02 | 0.02 | 1 | 1 | 1 |
| gemma-4-31b-it | cancel | 0 | D vs F | 62 | 0.98 | 0.95 | 3 | 1 | 1 |
| gemma-4-31b-it | comp | 1 | F vs E | 1 | 1.00 | 1.00 | 0 | 0 | 1 |
| gemma-4-31b-it | comp | 1 | E vs C | 1 | 1.00 | 1.00 | 0 | 0 | 1 |
| openrouter/anthropic/claude-sonnet-5 | cancel | 0 | F vs E | 61 | 0.72 | 0.00 | 44 | 0 | 3.9e-12 |
| openrouter/anthropic/claude-sonnet-5 | cancel | 0 | E vs C | 62 | 0.00 | 0.29 | 0 | 18 | 0.00023 |
| openrouter/anthropic/claude-sonnet-5 | cancel | 0 | D vs F | 61 | 0.70 | 0.72 | 6 | 7 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 0 | F vs E | 23 | 0.91 | 0.83 | 3 | 1 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 0 | E vs C | 23 | 0.83 | 0.96 | 1 | 4 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 0 | D vs F | 23 | 1.00 | 0.91 | 2 | 0 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 1 | F vs E | 23 | 0.96 | 0.83 | 3 | 0 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 1 | E vs C | 21 | 0.90 | 0.81 | 3 | 1 | 1 |
| openrouter/anthropic/claude-sonnet-5 | comp | 1 | D vs F | 23 | 0.96 | 0.96 | 1 | 1 | 1 |

Verdicts: {"gemini-3.1-pro-preview|cancel": "path", "gemini-3.1-pro-preview|comp": "path", "gemini-3.8-flash|cancel": "path", "gemini-3.8-flash|comp": "path", "gemma-4-26b-a4b-it|cancel": "path", "gemma-4-31b-it|cancel": "path", "gemma-4-31b-it|comp": "not testable (C payouts > 50%)", "openrouter/anthropic/claude-sonnet-5|cancel": "path", "openrouter/anthropic/claude-sonnet-5|comp": "not testable (C payouts > 50%)"}

Models with the path verdict in every task: ['gemini-3.1-pro-preview', 'gemini-3.8-flash']; in at least one task: ['gemini-3.1-pro-preview', 'gemini-3.8-flash', 'gemma-4-26b-a4b-it', 'gemma-4-31b-it', 'openrouter/anthropic/claude-sonnet-5']. Criterion (Amendment 3b: ≥3 models, ≥2 providers, every task) met: **False**

## Amendment 4: decision path vs flag value (same record; 'plans' = no-path request vs 'cancel')

| model | first | second | pairs | first error rate | second error rate | first-only | second-only | p (Holm) |
|---|---|---|---|---|---|---|---|---|
| gemini-3.8-flash | plans:G | cancel:C | 62 | 0.31 | 0.00 | 19 | 0 | 7.6e-06 |
| gemini-3.8-flash | plans:H | cancel:D | 62 | 0.55 | 0.66 | 5 | 12 | 0.14 |

## Ladder: least wording with C and D ≤ 5% and clean errors ≤ 10%

| model | task | W0 | W1 | W2 | W3 | W4 | W5 | W6 | SA | SN | least (W0–W6) | SA/SN near zero |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | cancel | – | – | – | – | – | – | – | C 0/62, D 51/62, clean 0/20 | C 0/62, D 34/62, clean 0/20 | none tested | none |
| gemini-3.1-pro-preview | comp | – | – | – | – | – | – | – | C 6/46, D 42/46, clean 0/40 | C 2/46, D 40/46, clean 0/40 | none tested | none |
| gemini-3.8-flash | cancel | – | C 24/24, D 24/24, clean 0/20 | C 24/24, D 24/24, clean 0/20 | C 24/24, D 24/24, clean 0/20 | C 24/24, D 24/24, clean 0/20 | C 2/24, D 24/24, clean 0/20 | C 0/62, D 29/62, clean 0/40 | C 0/62, D 41/62, clean 0/40 | C 0/62, D 5/62, clean 0/40 | none tested | none |
| gemini-3.8-flash | comp | C 23/23, D 23/23, clean 0/20 | C 23/23, D 23/23, clean 0/20 | C 23/23, D 23/23, clean 0/20 | C 23/23, D 23/23, clean 0/20 | C 23/23, D 23/23, clean 0/20 | C 21/23, D 23/23, clean 0/20 | C 1/46, D 44/46, clean 0/92 | C 0/46, D 16/46, clean 0/92 | C 0/46, D 4/46, clean 0/92 | none tested | none |
| gemma-4-26b-a4b-it | cancel | – | – | – | – | – | – | – | C 11/53, D 62/62, clean 0/0 | – | none tested | none |
| gemma-4-31b-it | cancel | – | – | – | – | – | – | C 18/39, D 33/35, clean 1/21 | C 1/62, D 61/62, clean 0/23 | C 0/36, D 30/35, clean 0/24 | none tested | none |
| gemma-4-31b-it | comp | – | – | – | – | – | – | – | C 9/11, D 6/6, clean 0/0 | – | none tested | none |
| openrouter/anthropic/claude-sonnet-5 | cancel | – | – | – | – | – | – | C 16/61, D 21/62, clean 0/0 | C 18/62, D 44/62, clean 0/20 | C 12/62, D 40/62, clean 0/20 | none tested | none |
| openrouter/anthropic/claude-sonnet-5 | comp | – | – | – | – | – | – | – | C 39/44, D 45/46, clean 0/40 | C 17/45, D 41/44, clean 1/39 | none tested | none |
| openrouter/openai/gpt-6-luna | cancel | – | – | – | – | – | – | C 3/62, D 0/62, clean 0/0 | C 0/62, D 0/62, clean 0/20 | C 0/62, D 0/62, clean 1/20 | W6 | SA, SN |
| openrouter/openai/gpt-6-luna | comp | – | – | – | – | – | – | C 3/46, D 5/46, clean 0/0 | C 1/46, D 5/46, clean 0/40 | C 0/45, D 1/46, clean 3/40 | none tested | SN |
| openrouter/openai/gpt-6-sol | cancel | – | – | – | – | – | – | C 4/62, D 0/62, clean 0/0 | C 0/62, D 0/62, clean 0/20 | C 0/62, D 0/62, clean 0/20 | none tested | SA, SN |
| openrouter/openai/gpt-6-sol | comp | – | – | – | – | – | – | C 2/46, D 0/46, clean 0/0 | C 0/46, D 0/46, clean 0/40 | C 0/46, D 0/46, clean 0/40 | W6 | SA, SN |
