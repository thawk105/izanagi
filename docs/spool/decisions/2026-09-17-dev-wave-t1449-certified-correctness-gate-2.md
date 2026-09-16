---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t1449-certified-correctness-gate
seq: 2
---

## {{D:certified-gate-raw-success-definition}}. D1272 の条件付き gate は「性能 completed かつ検証割当ての失敗が未記録」の受領証にだけ 6 対を要求し、性能 completed だけを条件にする案は却下する

**決定:** 受領証 semantic validator の `_validate_reason_branches` に、D1272 の条件付き最小 gate を次の 1 条件で入れる。
既存の raw 検査 (marker・allocation・failure_evidence・36-run 双射) を通過した completed 性能 attempt が 1 件以上あり、かつ
検証割当て (`cluster_slot_or_null == null`) の非 completed な attempt が 1 件も無い受領証は、`correctness_evidence` が
(stock, mode1, modeX) × (W1, W2) の 6 対を各 1 件・計 6 件で覆わない限り `correctness` で拒否する。
「成功・certified な受領証」の raw 定義はこの条件 (性能 completed かつ検証割当ての失敗が未記録) とし、
`declared_use_class` と `reason_code` の申告だけを受理の正の根拠にしない。凍結 schema の `minItems:0`、
凍結事前登録 §7.1(1) の失敗記録 (検証 attempt が失敗を申告した stage の 0〜5 件)、凍結 conformance vector は変えない。

**理由:**

- 既存検証器は「検証 attempt completed ⇒ 6 対」を持つが、検証 attempt の帰結が受領証に無いまま性能が completed した受領証を
  受理していた。これが D1272 の名指す「成功まで三者比較 0 回」の穴であり、本条件はこの形だけを閉じる。
- 検証割当ての失敗は正規運用上 `pre_performance_infra_failure` に写り、追補 A a10 で study は `design_not_feasible` 終端になる。
  その stage 受領証を §7.1(1) は 0〜5 件で受理すると凍結しており、D1272 も「失敗途中の受領証の空配列は維持」「受理集合を
  必要以上に狭めない」を要求する。検証割当ての失敗が記録された受領証は gate の外に置く。
- `correctness_evidence` の各 entry には `_validate_correctness_builds` の三者比較 (D574 決定 3) と raw 出力の anomaly 検査が
  無条件に走るので、6 対の完全被覆を要求すれば「必要な三者比較あり」が帰着する。

**却下した選択肢:**

- 性能 completed があれば無条件に 6 対を要求する (段 2 plan の P1-b) — §7.1(1) が受理すると凍結した失敗記録を過剰拒否する。
  段 3 レンズ A の所見で不採用。
- 性能 completed があれば検証 attempt の存在を要求する (親 brief の P1-a) — D1272 の「非空」から導けない履歴条件を足す。
- study 入口 (`_validate_study_receipts_inner`) だけに置く — 単票 validator と private writer の 0 件経路が残る。
- 既存正例 fixture `_full_receipt` を検証 completed へ改修する — それ自体が §7.1(1) の正規失敗記録で過剰拒否の対照になり、
  凍結 vector 46 本の基底でもあるので不変とし、成功用の派生 fixture を別に足した。

本 gate が保証しないこと: 検証失敗を記録した受領証が下流の認証 (追補 A a10/a11、単位 6 以降) で certified 採用されないことは
認証実装の責務である。evidence を持つ検証割当てに attempt が無い受領証の参照整合、correctness compile の TU / arm 束縛、
検証 attempt の両 stage 再掲の契約は本決定の範囲外で、裁定パッケージ候補として worklog に残す。
