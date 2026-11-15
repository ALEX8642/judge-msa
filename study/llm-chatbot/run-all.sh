#!/bin/sh
# Arms A, B, C for each judge, one model at a time. Resumable: run it again after an interruption.
cd "$(dirname "$0")" || exit 1
for judge in phi4:14b mistral-small3.2:24b gemma3:27b; do
  for arm in A B C; do
    ./run.sh --llm-chatbot "${LLM_CHATBOT:-$HOME/LLM-chatbot}" --arm $arm --judge $judge --out data/trials-$arm.jsonl || exit 1
  done
done
echo ALL-DONE
