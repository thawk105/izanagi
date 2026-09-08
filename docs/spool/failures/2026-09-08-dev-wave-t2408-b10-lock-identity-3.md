---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2408-b10-lock-identity
seq: 3
---

## 再発

### F81

- **再発: 2026-09-08** — B-10 の report が読む campaign lock の検査 test が、`schema_version` を持たない
  旧 v1 形式の合成 lock を正例にしていた。`decode_campaign_lock` は `schema_version` が無ければ
  authority を一切検査しないため、この fixture は緑のまま、現物 3 本 (v2 + pre-T733 24 path) は
  同じ経路で必ず拒否される状態が続いていた。現物 3 本を snapshot として収載し、
  raw bytes のまま decoder へ通す正例と v1 / 現行 grammar の負例へ置き換えた。

### F457

- **再発: 2026-09-08** — login node の焦点走で
  `test_b10_backoff_shape_sweep.py::test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy`
  が赤になった。原因は別ユーザー (`makiart`) が 2026-09-07 に作った空の `/tmp/.git` で、
  `/tmp` 配下の一時 root が repository 内と判定されるため。同じ commit を計算ノードで走らせると
  `190 passed` で緑になり、変更へ帰属しないことを確認した。
