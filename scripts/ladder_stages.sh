#!/bin/sh
# The preregistered stages (LADDER_PREREGISTRATION.md). MODE is --estimate (writes the frozen plan) or a spend cap.
# Usage: sh scripts/ladder_stages.sh <stage> [--estimate | --max-dollars N]
set -e
R="uv run python -m refundout.ladder_run"
S=$1; shift
case $S in
  flash-scope-cancel) $R --stage $S --model gemini-3.8-flash --tasks cancel --wordings SA SN W6 --clean 20 --repeats 1 --estimate-per-call 0.006 "$@";;
  flash-scope-comp)   $R --stage $S --model gemini-3.8-flash --tasks comp --wordings SA SN W6 --clean 23 --repeats 2 --estimate-per-call 0.006 "$@";;
  flash-ladder-cancel) $R --stage $S --model gemini-3.8-flash --tasks cancel --wordings W1 W2 W3 W4 W5 --corrupt 24 --clean 10 --estimate-per-call 0.006 "$@";;
  flash-ladder-comp)  $R --stage $S --model gemini-3.8-flash --tasks comp --wordings W0 W1 W2 W3 W4 W5 --clean 10 --estimate-per-call 0.006 "$@";;
  pro-scope-cancel)   $R --stage $S --model gemini-3.1-pro-preview --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.0125 "$@";;
  pro-scope-comp)     $R --stage $S --model gemini-3.1-pro-preview --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.0125 "$@";;
  gemma31-scope-cancel) $R --stage $S --model gemma-4-31b-it --tasks cancel --wordings SA SN W6 --clean 20 --repeats 1 --workers 2 --pace 14 "$@";;
  gemma31-scope-comp)   $R --stage $S --model gemma-4-31b-it --tasks comp --wordings SA SN W6 --clean 23 --repeats 2 --workers 2 --pace 14 "$@";;
  sonnet-scope-cancel) $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.011 "$@";;
  sonnet-scope-comp)   $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.011 "$@";;
  gpt-scope-cancel)  $R --stage $S --model openrouter/openai/gpt-6-sol --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.01 "$@";;
  gpt-scope-comp)    $R --stage $S --model openrouter/openai/gpt-6-sol --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.01 "$@";;
  gptluna-scope-cancel) $R --stage $S --model openrouter/openai/gpt-6-luna --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.001 "$@";;
  gptluna-scope-comp)   $R --stage $S --model openrouter/openai/gpt-6-luna --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.001 "$@";;
  opus-comp)         $R --stage $S --model openrouter/anthropic/claude-opus-5.5 --tasks comp --wordings W1 W3 SA SN --clean 0 --repeats 1 --estimate-per-call 0.027 "$@";;
  *) echo "unknown stage $S"; exit 1;;
esac
