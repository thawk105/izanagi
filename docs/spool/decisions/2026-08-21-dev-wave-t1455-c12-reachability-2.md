---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1455-c12-reachability
seq: 2
---

## {{D:c12-allocation-declared-call}}. C12 の allocation binding 判定を C05/C06 と同型の idiom へ揃える

**決定:** `_c12_allocation_binding_verdict` の supervisor 側 reachability 検査を、ad hoc な
`_reachable_calls` (呼び出し名の文字列一致のみ、import 束縛を検証しない) から
`_ReachabilityExplorer`+`_declared_call` (import 束縛を実解決したうえでの cross-module
reachability 検査、`_evaluate_c05`・`_evaluate_c06` と同型、`_evaluate_c12` 自身の
environment_contract/execution_guard 副検査とも同型) へ置換する。判定対象は
`read_binding`/`check_reservation` の到達判定のみとし、reason code は既存の
`ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT` を維持する。`field_paths`/`reachable_from` の
文字列契約検査、`_reachable_calls` 本体の変更・撤去は本 wave の scope に含めない。

**理由:**
- D599 (2026-08-20) が C06 について指摘した「呼び出し名の文字列一致だけで import 束縛を
  検証しない」弱点は、同ファイル内の C12 helper にも同型で存在すると、C06 強化 wave の段3
  敵対相談が独立に発見していた。同ファイル内の姉妹検査がすでに個別に持つ idiom をそのまま
  転用でき、新規機構の発明を要しなかった (規律5「盛らない」、既存 idiom の再利用)。
- 旧実装は decoy 関数・import alias・return 後の dead code の3経路すべてで fail-open することを
  実測で確認した (親の一時編集による直接実行、独立レンズによる追試の両方で再現)。
- 実装後の変異 matrix 本走で、この強化が契約の `negative_control_id`
  (`nc_c12_reservation_check_bypassed`) 専用テストが検出する範囲と直接重なることを実測で
  確認した — allocation binding の弱点は「reservation check bypass」という契約が名指しする
  攻撃面そのものであり、本強化はその検出力を機械的に裏付ける。
- 実 repo 現行状態への判定結果は変更しない (`EVIDENCE_UNDEFINED`/
  `completion-proof-not-machine-checkable` のまま)。C12 の `machine_checkable=true` 契約・
  `static_only_note` が明記する may-reach 検査の限界 (data-flow・支配関係・例外伝播・process
  exclusivity を証明しない) も変更しない。

**却下した選択肢:**
- `_reachable_calls`・`_ReachabilityExplorer`・`_declared_call` の本体を変更する、または
  C06/C05 など他条件の evaluator へ波及させる — 対象は C12 の allocation binding 判定
  1箇所のみで足り、規律5 に反する。
- `field_paths`/`reachable_from` の文字列契約検査を C12 へ新設する — C06 (D613) が持つ
  P1.4 相当の拡張だが、command が要求する scope を超え、C12 は現状どちらも未使用のため
  narrow scope を優先した。
- 変異事前登録の expected node を段4時点の推測のまま確定扱いにする — 実装後の正式
  `tools/mutation_harness.py` 本走で当初見落としていた追加 kill (cache-hit テスト、契約の
  `negative_control_id` 専用テスト) が2回判明したため、実測確定するまで「候補」として扱った。
