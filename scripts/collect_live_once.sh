#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

query="${QUERY:-}"
db_path="${APP_DB:-$repo_root/data/upwork.sqlite}"
max_pages="${MAX_PAGES:-1}"
page_size="${PAGE_SIZE:-50}"

tmp_jsonl="$(mktemp /tmp/upwork-live.XXXXXX.jsonl)"
cleanup() {
  rm -f "$tmp_jsonl"
}
trap cleanup EXIT

mkdir -p "$(dirname "$db_path")"

collect_args=(--live --max-pages "$max_pages" --page-size "$page_size")
if [[ -n "$query" ]]; then
  collect_args+=(--query "$query")
fi

echo "[upwork] collecting live jobs" >&2
echo "[upwork] db=$db_path query=${query:-<none>} max_pages=$max_pages page_size=$page_size" >&2

UPWORK_COLLECTOR_LIVE=1 uv run --extra dev upwork-app-collect "${collect_args[@]}" > "$tmp_jsonl"

line_count="$(wc -l < "$tmp_jsonl" | tr -d ' ')"
echo "[upwork] collected_records=$line_count" >&2

ingest_args=(--db "$db_path" --input "$tmp_jsonl")
if [[ -n "$query" ]]; then
  ingest_args+=(--query "$query")
fi

uv run --extra dev upwork-app-ingest "${ingest_args[@]}"
