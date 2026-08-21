---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1461-masstree-staging
seq: 2
---

## 再発

### F1

- **再発: 2026-08-21** — [T-1461] の command 起票文が、D399/[T-1431] insight が指した
  意図された consumer (`sort_swo_oracle.resolve_oracle_environment()`、
  `IZANAGI_SORT_SWO_MASSTREE_ROOT` を読む関数) を、floor campaign の実際の実行経路が
  消費する機構だと転写した。現物確認 (file:line) では、floor 実行
  (`orchestrator/campaign/s8b_floor_campaign.py`) はこの関数を import も呼出しもせず、
  別の独立した masstree 依存解決経路 (`build_cells()` の `fetchcontent_base_dir`) を
  通っていた。関数自体の実在確認だけでは不十分で、意図した呼出し元から対象関数への
  実際の到達性 (呼出しグラフ) まで確認する必要があるという、F1 既存記述の適用範囲が
  さらに広がったことを示す。段1 brief 時点で検出し実装前に是正 (実害なし)。段2 codex
  読取専用プラン起草・段3 敵対相談 3 レンズが独立に追認した。詳細は
  `output/insights/2026-08-21_t1461-masstree-staging-scope-finding/README.md` 参照。
