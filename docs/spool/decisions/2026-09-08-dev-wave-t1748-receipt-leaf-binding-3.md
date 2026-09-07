---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t1748-receipt-leaf-binding
seq: 3
---

## {{D:receipt-leaf-rederivation-scope}}. 受領証の cross-binding leaf の耐久検査は current v5 に限り、legacy v3/v4 は aggregate のみのままとする

**決定:** `orchestrator/campaign/s8c_acceptance_receipt.py` の `verify_acceptance_receipt` は、
`schema_version` が current (`p3-8c-trial-acceptance-receipt/v5`) の受領証についてのみ、各 trial の
`cross_binding_receipt_sha256` を現物から再導出して照合する。legacy の v3 / v4 は従来どおり
top-level aggregate だけを検査する。この射程は docstring と worklog に明記し、
「`verify_acceptance_receipt` 全体で任意 leaf が通らなくなった」とは書かない。

再導出は `verify_s8c_cross_binding` を発行時と同じ引数で呼び直す形とする。引数はすべて
追跡済み受領証から復元する — `report` と `events` は受領証が名指しし verifier が既に再読・
再ハッシュしている bytes、`run_root` は `attempt_journal_path` の解決済み path の親、
`output_root` は build のとき `run_root.parent.parent`。**受領証の leaf 値は再導出の入力に
一切渡さない。** 既存の aggregate 検査は削除も代用もせず残す。

**理由:**
- 発行時の保証が受領証の耐久保証になっていなかった。leaf を任意の値へ差し替え aggregate を
  その値から作り直した受領証が検証を通っていた (既存 v5 fixture が合成文字列の leaf で
  検証を通していたことが現行 main での実在証拠)。
- 照合が恒真にならないのは、左辺が現物から導かれ右辺が受領証の宣言値だからである。
  同じ走行側が書いた値どうしの照合 (D920 が禁じた型) にはならない。
- legacy へ広げないのは、(a) 唯一の production consumer `layer3_report.build_accepted_report` が
  `require_current_verified_receipt` を通し、同関数が current 以外を無条件拒否するため legacy は
  下流のどの capability にも到達しない、(b) legacy の再導出には当時の campaign 現物が要り、
  失われていれば読めなくなる — readable compatibility の不当な縮小になる、の 2 点による。
- 発行済み受領証は 0 件であり、既存の凍結成果物を invalidate しない。

**却下した選択肢:**
- **leaf を report / journal だけから作れる別 digest へ置き換える** — build mode の leaf が現在
  束縛している 6 field (build_records、bench_records、artifact_refs、source_refs、
  admission_decision、proposal_build_source_bindings) を耐久保証から落とす。
- **leaf の preimage を sidecar 成果物として発行時に永続化し、verifier がそれを再読する** —
  sidecar の元になった campaign 現物を再検査しない限り同一走行側の値どうしの照合になり、
  かつ新しい durable path の規約と発行処理が要る。最小変更を超える。
- **legacy v3/v4 へも同じ再導出を広げる** — 到達不能な経路への防壁追加であり、
  現物が失われた legacy 受領証を新たに読めなくする過剰拒否になる。
