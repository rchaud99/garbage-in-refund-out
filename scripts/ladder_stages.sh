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
  sonnet-scope-cancel) $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.011 --workers 10 --pace 3.3 "$@";;
  sonnet-scope-comp)   $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.011 --workers 10 --pace 3.3 "$@";;
  gpt-scope-cancel)  $R --stage $S --model openrouter/openai/gpt-6-sol --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.01 --workers 10 --pace 3.3 "$@";;
  gpt-scope-comp)    $R --stage $S --model openrouter/openai/gpt-6-sol --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.01 --workers 10 --pace 3.3 "$@";;
  gptluna-scope-cancel) $R --stage $S --model openrouter/openai/gpt-6-luna --tasks cancel --wordings SA SN --clean 10 --repeats 1 --estimate-per-call 0.001 --workers 10 --pace 3.3 "$@";;
  gptluna-scope-comp)   $R --stage $S --model openrouter/openai/gpt-6-luna --tasks comp --wordings SA SN --clean 10 --repeats 2 --estimate-per-call 0.001 --workers 10 --pace 3.3 "$@";;
  opus-comp)         $R --stage $S --model openrouter/anthropic/claude-opus-5.5 --tasks comp --wordings W1 W3 SA SN --clean 0 --repeats 1 --estimate-per-call 0.027 --workers 10 --pace 3.3 "$@";;
  w6-sonnet-cancel) $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks cancel --wordings W6 --clean 0 --repeats 1 --estimate-per-call 0.013 --workers 10 --pace 3.3 "$@";;
  w6-sonnet-comp)   $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks comp --wordings W6 --clean 0 --repeats 2 --estimate-per-call 0.013 --workers 10 --pace 3.3 "$@";;
  w6-gpt-cancel)    $R --stage $S --model openrouter/openai/gpt-6-sol --tasks cancel --wordings W6 --clean 0 --repeats 1 --estimate-per-call 0.005 --workers 10 --pace 3.3 "$@";;
  w6-gpt-comp)      $R --stage $S --model openrouter/openai/gpt-6-sol --tasks comp --wordings W6 --clean 0 --repeats 2 --estimate-per-call 0.005 --workers 10 --pace 3.3 "$@";;
  w6-gptluna-cancel) $R --stage $S --model openrouter/openai/gpt-6-luna --tasks cancel --wordings W6 --clean 0 --repeats 1 --estimate-per-call 0.0005 --workers 10 --pace 3.3 "$@";;
  w6-gptluna-comp)  $R --stage $S --model openrouter/openai/gpt-6-luna --tasks comp --wordings W6 --clean 0 --repeats 2 --estimate-per-call 0.0005 --workers 10 --pace 3.3 "$@";;
  ef-flash-cancel) $R --stage $S --model gemini-3.8-flash --tasks cancel --wordings SA --corrupt-cells EF --clean 0 --repeats 1 --estimate-per-call 0.0065 --workers 8 "$@";;
  ef-flash-comp)   $R --stage $S --model gemini-3.8-flash --tasks comp --wordings SA --corrupt-cells EF --clean 0 --repeats 2 --estimate-per-call 0.0065 --workers 8 "$@";;
  ef-pro-cancel)   $R --stage $S --model gemini-3.1-pro-preview --tasks cancel --wordings SA --corrupt-cells EF --clean 0 --repeats 1 --estimate-per-call 0.0125 --workers 8 "$@";;
  ef-pro-comp)     $R --stage $S --model gemini-3.1-pro-preview --tasks comp --wordings SA --corrupt-cells EF --clean 0 --repeats 2 --estimate-per-call 0.0125 --workers 8 "$@";;
  ef-sonnet-cancel) $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks cancel --wordings SA --corrupt-cells EF --clean 0 --repeats 1 --estimate-per-call 0.013 --workers 10 --pace 3.3 "$@";;
  ef-sonnet-comp)  $R --stage $S --model openrouter/anthropic/claude-sonnet-5 --tasks comp --wordings SA --corrupt-cells EF --clean 0 --repeats 2 --estimate-per-call 0.013 --workers 10 --pace 3.3 "$@";;
  plans-flash) $R --stage $S --model gemini-3.8-flash --tasks plans --wordings SA --corrupt-cells GH --clean-cells K --clean 20 --repeats 1 --estimate-per-call 0.0065 --workers 8 "$@";;
  plans-pro)   $R --stage $S --model gemini-3.1-pro-preview --tasks plans --wordings SA --corrupt-cells GH --clean-cells K --clean 20 --repeats 1 --estimate-per-call 0.0125 --workers 8 "$@";;
  path-gemma31-cancel) $R --stage $S --model gemma-4-31b-it --tasks cancel --wordings SA --corrupt-cells CDEF --clean 0 --repeats 1 --workers 2 --pace 14 "$@";;
  path-gemma31-comp)   $R --stage $S --model gemma-4-31b-it --tasks comp --wordings SA --corrupt-cells CDEF --clean 0 --repeats 2 --workers 2 --pace 14 "$@";;
  path-gemma26-cancel) $R --stage $S --model gemma-4-26b-a4b-it --tasks cancel --wordings SA --corrupt-cells CDEF --clean 0 --repeats 1 --workers 2 --pace 14 "$@";;
  path-gemma26-comp)   $R --stage $S --model gemma-4-26b-a4b-it --tasks comp --wordings SA --corrupt-cells CDEF --clean 0 --repeats 2 --workers 2 --pace 14 "$@";;
  *) echo "unknown stage $S"; exit 1;;
esac
