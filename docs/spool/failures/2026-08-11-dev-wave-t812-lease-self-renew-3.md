---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t812-lease-self-renew
seq: 3
---

## 新規

### {{F:codex-observation-cap-kills-lens}}. codex 子の観測トークン上限が完了直前の子を SIGTERM し、出力 0 byte にする [コンテキスト浪費] [手順漏れ]

- 事象: 段 3 の敵対レンズ 1 本 (`consult`, `reasoning=max`, read-only) が 17 分走った末に
  `codex_exit_code=-15` で終了し、`output_bytes=0`、成果物ファイルは未作成。receipt の
  `limit_trigger=max_cli_reported_tokens`、実測 `cli_reported=1,017,768` に対し
  `--max-cli-reported-tokens` の既定は 1,000,000。**1.8% の超過でレンズ 1 本が丸ごと失われた。**
  待ち手は `.done` と成果物の不一致を検出して `stage=producer-files rc=70` で正しく止まった
  (待ち手側の欠陥ではない)。
- 事象 (二次): 同じ prompt ファイルのまま再投入すると `NG: 既存の完全な receipt は上書きできない`
  で rc=2 になる。`job_id` は prompt 内容の digest を含むため、**prompt を変えない限り再投入
  できない**。log は 1 行だけで、原因は receipt を開くまで分からない。
- 根本原因: `--max-cli-reported-tokens` は「非権威の運用既定」として `--help` に書かれているが、
  読み込み量の多い段 (大きなソース + 大きなテストファイルを跨ぐレビュー・相談) では既定が
  実消費に足りない。上限超過は**打ち切りではなく破棄**であり、部分出力も保存されない。
  起動側に「読む量に応じて上限を見積もる」手順が無かった。
- 恒久対応: 起動 script (`run_*.sh`) の argv に `--max-cli-reported-tokens` を明示する運用へ変更し、
  本 wave では 3,000,000 で 4 本すべて完走した。**reference 節 (`DW-O01`) への規則追記は
  `docs/dev-wave/**` の L1.5 予算に余白 0 のため入らず、予算の扱いを裁定パッケージへ返した**
  (`output/insights/2026-08-11_t812-lease-self-renew/package.md` の Q7)。
- 再発検知: receipt の `attempts[].limit_trigger` が非 null かつ `output_bytes=0` の組合せ。
  待ち手の `stage=producer-files` はこの型の症状として現れる (原因は receipt を見るまで確定しない)。
