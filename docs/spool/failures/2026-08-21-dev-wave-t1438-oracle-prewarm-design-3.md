---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1438-oracle-prewarm-design
seq: 3
---

## 新規

### {{F:receipt-memo-completeness-check-assumption}}. 既存機構に完全性検査が無いという未確認の前提を brief/plan に書きかけた [手順漏れ]

- 事象: T-1438 の段1 brief・段2 plan は、`RECEIPT_MEMO_CONSUMER_NODES`
  (T-080 receipt 消費者 registry) が `REAL_REPO_SERIAL_NODES` 非加入で同種保護を達成する
  「既存稼働実績」とだけ書き、その完全性 (登録漏れの機械検出) を保証する検査が存在するかを
  未確認のまま設計を進めかけた。この前提のまま oracle 側の設計 (段2 plan 当初案) を確定すると、
  fixture 解除によって機械的完全性検査を失う欠陥を持ったまま実装が進みかねなかった。
- 根本原因: `test_real_repo_serialization.py` の `_assert_fixture_closure_complete`
  (fixture の scope/baseid で機械判定する closure gate) だけを探索し、
  `RECEIPT_MEMO_CONSUMER_NODES` 専用の AST inventory 検査 (同ファイル 1254-1340 行付近、
  fixture 経由ではなく関数呼び出し経由consumerの登録漏れを別の仕組みで検出する) を見落とした。
  fixture 経由の保護機構だけを探し、非 fixture 経由 (直接関数呼び出し) の保護機構の有無を
  別途確認しなかった。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S03` (段3 敵対相談は無条件・親 brief 自身の
  実測値と一般化を攻撃対象に含める) が構造的な fails-closed 検査として機能し、段3 敵対相談
  レンズC (規律2 適合レンズ) がこの前提を独立に検証して発見した。具体的な是正は
  {{D:oracle-environment-controller-prewarm}} — oracle 側にも同型の独立完全性検査を新設し、
  規律2 抵触を回避した。
- 再発検知: 「既存機構に安全網が無い」と前提して設計を進める前に、その機構の完全性検査の
  有無を実コードで確認する。fixture 経由と非 fixture 経由の両方の保護経路を個別に検索する。
