---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t940-ledger-count
seq: 3
---

## 新規

### {{F:codex-large-output-breaks-evidence}}. 子の大出力 command が evidence を全損させる [証拠破損] [工数喪失]

- 事象: 段 3 のレンズ B が 2 回連続で `evidence_status=invalid` となり、待ち手が rc=70
  (成果物欠落) で止まった。`codex_exit_code=0`、`validator_rc=0`、成果物 12 KB で子は正しく
  完走していたにもかかわらず、成果物が丸ごと破棄された。2 回で約 39 分と 78,000 output token を失った。
- 根本原因: 子が repo 全体に対して内容付きの `git grep -n` を無限定で流し、約 1 MB の
  `aggregated_output` を 1 件の event に載せた。events.jsonl の該当行が JSON として閉じず、
  `tools/codex_worker_launch.py` の `_drain_stdout` が `stdout_invalid` を立てて
  `_evidence_status` が `invalid` を返した。既知の「Web 検索で全損」とは別経路であり、
  親の prompt には出力量の制約が無かった。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O05` (read-only codex) へ、子 prompt に
  出力量上限 (200 行 / 20 KB) と `-l` / `-c` 先行の検索作法を書く定型を入れる。
  **その定型は「推奨であって停止条件ではない、超えたら絞り直して必ず成果物を出せ」と明記する** —
  本 wave の 3 回目の投入は、親が「超えると全損する」とだけ書いたために子が停止条件と解釈し、
  229 bytes の中止宣言だけ出して降りた (証拠経路は正常だったのに成果物ゼロ)。
- 再発検知: 待ち手 rc=70 を見たら receipt の `evidence_status` を先に読み、`invalid` なら
  events.jsonl の最大行長と JSON parse 失敗行を数える。本 wave で使った診断は
  1 行ずつ `parse_jsonl` に通して失敗行と byte 数を出すだけの 20 行スクリプトである。
