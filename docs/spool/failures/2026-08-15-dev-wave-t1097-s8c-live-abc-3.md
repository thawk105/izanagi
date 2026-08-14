---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t1097-s8c-live-abc
seq: 3
---

## supersede 追記

- F84 **supersede: 2026-08-15** — 直上の再発項が書く `[T-1097] wave` は誤引用である。`[T-1097]` は `check_ai_provenance.py --message-file` の診断に関する無関係な既存項で、当該 near miss を出したのは branch `worktree-dev-wave-t1097-s8c-live-abc` の wave (台帳上の identity は [T-1109] 〜 [T-1113]) である。branch 名の `t1097` は slug であって T 参照ではない。
- F97 **supersede: 2026-08-15** — 直上の再発項が書く `[T-1097] wave` は誤引用である。`[T-1097]` は無関係な既存項で、当該独立 2 例目を出したのは branch `worktree-dev-wave-t1097-s8c-live-abc` の wave であり、この再発が起票した裁定項目は [T-1109] (PBS_JOBID 受理文法) と [T-1111] (fail-closed admission 述語の族一般化) である。
