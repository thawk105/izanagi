---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: worktree-cleanup-stop-hook-ffonly
seq: 2
---

## 再発

### F452

- **再発: 2026-10-01** — md_6 (cleanup Stop hook) の段 5 author の prompt に、DW-O01 (D2335) が求める「委任 (spawn_agent) を使わない」を書き忘れた。
  ultra の子が委任し、起動器が `delegation_detected` で未受理にした (launcher rc=1、実装の残差は起動器が commit)。委任禁止を明記した 2 回目が残差を単独で監査して受理され、
  以後の review・fix の prompt には同じ禁止を入れた。損失は author 1 巡 (約 7 分) と、委任先の書込みが guard 未確認のまま残る面 (D2335 の残る限界) の監査 1 回。
  型は F452 と同じ (段ごとに手書きする prompt から一般規律の必須事項が落ちる)。

## supersede 追記

- F1081 **supersede: 2026-10-01** — 恒久対応の [T-2951] は md_6 で実施済み ({{D:cleanup-stop-ff-exemption}})。恒久対応が例示した「reflog に commit 由来の項が 1 つ以上ある」ではなく、免除する側を絞った: 作成項が最古項に残り、それ以外の全項が `merge main: Fast-forward` / `merge refs/heads/main: Fast-forward` で、各項の OID を main の reflog がその時刻以前に指していた木に限る。再発検知の負例は `test_cleanup_stop_allows_ff_main_with_zero_commits` ほか。
