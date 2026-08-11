---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t783-toolchain-binding
seq: 3
---

## 新規

### {{F:redundant-gate-masks-authority-mutation}}. 冗長ゲートが authority 照合の変異を覆い隠した [テスト代表性]

- 事象: 床値 toolchain 束縛の変異 M03 (登録済み較正 ↔ 実測 cc の版数照合を「全文」から
  「本体の先頭行だけ」へ弱める) が **SURVIVED**。注入は実在していた
  (anchor 1 件一致、injection diff hash 記録あり) ので等価変異ではない。
- 根本原因: 既存 fixture が cc の版数の 2 行目だけをずらす形だったため、
  照合を先頭行比較へ弱めても、直後にある**別理由のゲート** (実測 cxx ↔ 実測 cc の
  版数本体の内部整合) が cc 側だけの変化を捉えて拒否していた。
  **2 つのゲートが同じ入力に対して過剰決定**で、authority 照合単独の検出力を測れていなかった。
  放置すると、将来この内部整合ゲートを外した時点で
  「登録済み較正の版数と実測を全文で突き合わせる」検出力を守るテストが 1 本も無くなる。
- 恒久対応: 内部整合ゲートを**通したまま** authority 照合だけを破る入力
  (実測 cc と cxx を同じ向きへずらし、受領記録側は元のまま) の単一理由テストを追加した
  — `orchestrator/tests/test_toolchain_binding.py::test_floor_predicate_rejects_receipt_body_drift_with_live_versions_aligned`。
  同テスト内で内部整合ゲートが実際に通っていることも assert しており、
  「片方だけを破れている」ことが後から読める。
- 再発検知: 同 nodeid を対象にした変異 M03 の再照準走が **KILLED**
  (実測 node は当該テスト 1 件のみで期待と完全一致)。
  手順は {{D:toolchain-binding-scope-narrowed}} と同 wave の変異台帳。
