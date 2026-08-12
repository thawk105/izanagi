---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t904-hashobject-sep
seq: 2
---

## 新規

### {{F:codex-web-search-invalidates-evidence}}. codex 子の Web 検索が evidence 検証を invalid にして成果物を全損させる [コンテキスト浪費]

- 事象: 段 3 の敵対レンズ (sol) が 848 秒 · 43 model call を費やして完走したのに、
  `dev_wave_codex.py` が rc=1 で不受理となり、出力 8,323 bytes が捨てられた。
  `codex_exit_code=0`、`validator_rc=0`、成果物ファイルは健在で、NFC も正常だった。
  受理を止めていたのは receipt の `evidence_status=invalid` である。
- 根本原因: 子が `web_search` を使うと、Codex CLI 0.147.0 が `item.started` /
  `item.completed` の `item` object に `id` を 2 回持つ event 行を stdout へ出す
  (1 つ目は `item_40` のような item 番号、2 つ目は `exec-<uuid>` の実行 ID)。
  `orchestrator/codex_roles/events.py` の `parse_jsonl` は重複 JSON key を拒否するため
  `codex_worker_launch.py` の `_drain_stdout` が `stdout_invalid=True` を立て、
  `_evidence_status` が `invalid` を返して attempt が accepted にならない。
  本 wave では 99 行中 22 行が該当した。
- 恒久対応: dev-wave の子 prompt に「Web 検索を使わない。使うと成果物が全損する」を
  絶対制約として書く (本 wave の `prompt-s3-lensA2.md` / `prompt-s5-author.md` /
  `prompt-s6-*.md` が実例)。**検証側を緩めない** — 重複 key の拒否は evidence の
  健全性検査であり、これを甘くする回避は規律 2 に反する。
- 再発検知: 不受理時は receipt の `attempts[].evidence_status` を読む。
  `invalid` かつ `codex_exit_code=0` なら stdout の event 行を `parse_jsonl` へ通し直し、
  `web_search` 由来の重複 key 行を探す。
