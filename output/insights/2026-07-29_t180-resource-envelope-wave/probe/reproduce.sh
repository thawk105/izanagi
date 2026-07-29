#!/bin/bash
# T-180 段 1 probe の再現手順。実 codex を 2 回呼ぶため token を消費する。
# 射程は README.md の「射程」節に従う (1 実走の観測であり一般性の証明ではない)。
set -u
W="${1:?usage: reproduce.sh <worktree-abs-path> <out-dir>}"
P="${2:?usage: reproduce.sh <worktree-abs-path> <out-dir>}"
mkdir -p "$P"

# 両 probe は同じ worktree と出力ディレクトリを共有する。
# probe1 — session 束縛 (stdout thread_id == rollout session_id == filename) の確認
bash -c "codex exec -m gpt-5.6-sol -c model_reasoning_effort=\"low\" -s read-only -C $W --json \
  -o $P/out.md \"\$(cat $P/prompt.txt)\" < /dev/null > $P/events.jsonl 2> $P/err.log; \
  echo \$? > $P/probe.done"

# probe2 — live 可読性。poller を並走させ 2 秒間隔で stdout/rollout/token_count を観測する。
# 観測列は 4 列 TSV (elapsed_s, stdout_lines, rollout_lines, token_count_events)。
# 注意: 件数取得に `grep -c ... || echo 0` を使うと 0 件時に単独行が混入して列契約が壊れる。
#       件数は必ず単一の値として取得すること (初回観測の混入は liveness-raw.tsv に保存)。
bash -c "codex exec -m gpt-5.6-sol -c model_reasoning_effort=\"low\" -s read-only -C $W --json \
  -o $P/out2.md \"\$(cat $P/prompt2.txt)\" < /dev/null > $P/events2.jsonl 2> $P/err2.log; \
  echo \$? > $P/probe2.done"

# rollout の突き合わせは rollout-digest.json の生成手順に従う
# (thread_id -> $CODEX_HOME/sessions 配下の rollout-*-<thread_id>.jsonl を探索し、
#  session_meta / token_count 時系列 / sha256 を記録する)。
echo "done: $P"
