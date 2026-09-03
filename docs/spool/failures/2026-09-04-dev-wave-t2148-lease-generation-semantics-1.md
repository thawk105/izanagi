---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-t2148-lease-generation-semantics
seq: 1
---

## 再発

### F391

- **再発: 2026-09-04** — 同じ上流障害が第 3 の表層症状で出た。23:54 と 23:57 JST の段 5 実装子が
  `wss://chatgpt.com/backend-api/codex/responses` と HTTPS fallback の
  `https://chatgpt.com/backend-api/codex/responses` の両方で 404、
  `backend-api/codex/models?client_version=0.152.1` も 404 で `turn.failed` になり、
  rc=1・出力 0 bytes で終わった。401 でも usage limit メッセージでもないので、症状の一覧に
  404 を足す。同 wave の段 2 が 22:11 JST に stderr 完全空で成功していたことが、
  repo 外の状態変化だという切り分けの根拠になった (子の成否だけでは切り分けられない)。
  13 分待って 00:18 JST に投入した 3 回目は rc=0 で成功し、F391 の「数分待てば回復する」
  性質も再確認された。**再投入は prompt 本文を変えずに `--job-id` を明示して行った** —
  F391 の恒久対応は「新しい prompt bytes で」と書いているが、prompt は契約なので変えたくない。
  `tools/dev_wave_codex.py --job-id <slug>` が同じ切り分けを prompt 不変で行える。
