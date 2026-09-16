---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t1789-empty-cell-descriptor-proof
seq: 1
---

## {{D:complete-trial-needs-descriptor-proof}}. 受領証の complete trial は descriptor 証明を欠くと拒否し、部分 report の C02 保持は変えない

**決定:** `orchestrator/campaign/s8c_acceptance_receipt.py` の `verify_acceptance_receipt` は、
v2〜v5 の受領証について、`status` が `complete` の trial の report に実行 descriptor が無い
(cells が空) 場合、`c02-arm-binding-unproven` の有無にかかわらず
`[receipt-arm-binding] complete trial lacks descriptor proof` で拒否する。判定は既存の
mandatory-reasons 判定の直後に置き、C02 を落とした形では従来の mandatory-reasons 文言が先に出る。
`status` が `partial` の report が cells を持たず C02 を保持する形 (D519 の部分 report) は
引き続き受理し、v5 の capability にも届く。

**理由:**
- 修正前の検証器は、report の cells を空にして C02 を残すだけで verified を返し、v5 では
  `require_current_verified_receipt` まで通していた (login node の実走で再現、v2 と v5)。
  期待と食い違う descriptor を持つ report は拒否されるのに、その cells を消して C02 を足すと
  受理へ変わることも実測した。
- D519 が descriptor 不在に例外を与えたのは「部分 report」であって、complete を名乗る report ではない。
  本番 driver は complete を「全 workload の cell がそろい fatal_error なし」のときだけ付け、
  登録 trial の workload は 1 件に束縛されるので、正規 producer は complete + cells 空を出さない。
- v5 の status は attempt registry の最終 terminal と `complete⇔observed` / `partial⇔terminal-failure`
  で束縛されるため、complete を partial に書き換えて逃げるには登録簿側も terminal-failure である
  必要があり、その受領証は完了・観測成功を名乗らない。この保証は「完了・観測成功を名乗らない」
  までであり、実行が始まらなかったことや証拠を消した過去が無いことまでは証明しない。
- 新しい条件は既存 gate の含意ではない (D949)。期待 digest の一致と descriptor の不在は両立し、
  修正前に verified を実測している。
- v5 に限らず v2〜v5 共通にしたのは、legacy v2 でも反例を実測しており、D1757 が legacy への拡張を
  退けた理由 (失われた campaign 現物の追加要求) を本件は伴わないため。v3 / v4 への効果は共通経路の
  読解であって実測ではない。legacy の受理集合は complete + cells 空 + C02 の分だけ狭まる。

**却下した選択肢:**
- v5 限定にする — legacy v2 の実測反例を残す。版分岐の削減が理由ではない。
- partial + cells 空 + C02 も拒否する — D519 の部分 report 許容と、producer が正規に発行する形
  (`test_p6_one_cell_partial_terminal_outcome_passes_acceptance`) を拒否する。
- legacy の任意の非空 status に値域 gate を足す — 静的には受理されるが、その形の実在・被害は
  再現していない。仮想リスク向けの gate は本件の scope 外。
- `require_current_verified_receipt` で C02 を一律拒否する — capability の意味を変える別仕様であり、
  再現した欠陥の修正ではない。
