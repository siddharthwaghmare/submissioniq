#!/usr/bin/env bash
# Temporary: finds which request shape the models endpoint accepts.
out=eval/results/diag.txt; mkdir -p eval/results; : > $out
try(){ name=$1; shift; echo "== $name" >> $out; curl -sS -L -m 60 -w '\n[http %{http_code} %{content_type}]\n' "$@" 2>&1 | head -c 600 >> $out; echo >> $out; }
B='{"messages":[{"role":"user","content":"Reply with the single word: pong"}],"model":"openai/gpt-4o-mini"}'
B2='{"messages":[{"role":"user","content":"Reply with the single word: pong"}],"model":"openai/gpt-4o"}'
B3='{"messages":[{"role":"user","content":"Reply with the single word: pong"}],"model":"gpt-4o-mini"}'
try "docs example, gpt-4o-mini" "https://models.github.ai/inference/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer $GITHUB_TOKEN" -d "$B"
try "docs example, gpt-4o" "https://models.github.ai/inference/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer $GITHUB_TOKEN" -d "$B2"
try "with api headers" "https://models.github.ai/inference/chat/completions" -H "Content-Type: application/json" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" -H "Authorization: Bearer $GITHUB_TOKEN" -d "$B"
try "azure endpoint" "https://models.inference.ai.azure.com/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer $GITHUB_TOKEN" -d "$B3"
try "catalog" "https://models.github.ai/catalog/models" -H "Authorization: Bearer $GITHUB_TOKEN"
echo "runner: $(uname -a | cut -c1-80) curl $(curl --version | head -1 | cut -c1-30)" >> $out
