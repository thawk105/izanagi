---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2655-prov-incremental
seq: 2
---

## 再発

### F35

- **再発: 2026-09-16** — [T-2655] (差分 provenance 監査) を entry (1529) が実装・記録しながら、
  次の一手差分で自 task ID を `完了` 節へ明示しなかったため、暗黙 carry が `- [T-2655] (N)` を
  (1528) から (1543) まで送り続けた。2026-08-18 型 (記録 commit 自身が未消化 carry を残す) の
  再発である。新しい面は**起票側の不在確認が 3 つとも「正しいが不在証明でない」形をしていた**こと。
  ユーザーは (a) `git log main --grep=T-2655` = 0 件、(b) 関連 2 branch の `main..branch` = 0、
  (c) 中身の無い worktree 残骸、の 3 点を未着手の根拠として提示したが、(a) は着地 commit の題が
  英文で task ID を含まないため、(b) は land 後の ff-only の結果であるため、(c) は撤去漏れの
  land 済み残骸であるため、いずれも不在を示さない。**着地判定の一次は commit 題でも branch の
  ahead 数でもなく成果物そのものの実在**であり、本 wave は `tools/check_ai_provenance.py` の
  `_receipt_bindings` / `_receipt_prefix` / `_publish_audit_receipt` の実在を読んで初めて済を
  確定した。恒久対応 1 (`DW-S01` の brief 前照合) は今回も投入前に機能し、実装子は 1 本も
  走らなかった。機械防壁は無いままである。
