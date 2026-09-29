"""Per-model × per-wording D (wrongful refusal) and C (payout) counts for one task, from ladder-results.json."""
import json, sys
res = json.load(open(sys.argv[1])); task = sys.argv[2] if len(sys.argv) > 2 else "cancel"
NAMES = {"gemini-3.8-flash": "Gemini 3.8 Flash", "gemini-3.1-pro-preview": "Gemini 3.1 Pro", "gemma-4-31b-it": "Gemma 4 31B",
         "gemma-4-26b-a4b-it": "Gemma 4 26B-A4B", "openrouter/anthropic/claude-sonnet-5": "Claude Sonnet 5",
         "openrouter/openai/gpt-6-sol": "GPT-6 Sol", "openrouter/openai/gpt-6-luna": "GPT-6 Luna"}
W = ["SA", "W6", "SN"]
print("| Model | " + " | ".join(f"{w}: D refused / C paid" for w in W) + " |")
print("|---" * (len(W) + 1) + "|")
for m, name in NAMES.items():
    cells = []
    for w in W:
        d, c = res["cells"].get(f"{m}|{task}|{w}|D"), res["cells"].get(f"{m}|{task}|{w}|C")
        cells.append(f"{d['bad']}/{d['n']} / {c['bad']}/{c['n']}" if d and c and d["n"] else "–")
    if any(x != "–" for x in cells):
        print(f"| {name} | " + " | ".join(cells) + " |")
