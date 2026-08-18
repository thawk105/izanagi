# 親の実測 (段 1〜2 並行、worktree dev-wave-t822-c02-receipt-v2、起点 main a160f4aa)

## M1. HEAD の 12 条件 (library 経路。`-m` の CLI は使わない)

```
C01 UNSATISFIED        workload-projection-mismatch
C02 EVIDENCE_UNDEFINED arm-binding-declared-only
C03 EVIDENCE_UNDEFINED manifest-registry-proof-undefined
C04 UNSATISFIED        crash-policy-cell-partial
C05 EVIDENCE_UNDEFINED schedule-schema-absent
C06 EVIDENCE_UNDEFINED budget-consumer-contract-undefined
C07 EVIDENCE_UNDEFINED floor-judge-contract-undefined
C08 EVIDENCE_UNDEFINED prereg-binding-proof-undefined
C09 UNSATISFIED        formal-acceptance-layer3-consumer-absent
C10 UNSATISFIED        cross-binding-verifier-incomplete
C11 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C12 UNSATISFIED        allocation-enforcement-consumer-absent
```

## M2. 問 3 の実名整備は判定結果を 1 bit も変えない

`trial_registry.py` の AST を HEAD blob から読んで実測した。

- `accept_trial` は不在。実名は `assert_trial_registry_acceptance`。
- `assert_campaign_layer3_chain` の `trial_registry.py` 内出現数 = **0**。
- `verify_s8c_cross_binding` の同出現数 = **0**。
- したがって実名へ直しても C09 は同じ理由で UNSATISFIED のまま。C10 は verifier 側で先に落ちるため
  acceptance の名前検査へ到達すらしない。

**含意**: 実名整備は受理集合を広げない潜在バグ修正である。「(i) を閉じても自動追随しない」という
[T-822] 問 3 の記述はこの実測と整合する。

## M3. acceptance が直接呼ぶ arm 機構 (T-1311 由来)

`assert_trial_registry_acceptance` の直接 call に次が実在する。

- `assert_execution_digest_chain`
- `validate_execution_input_descriptor`
- `_expected_registered_arm_execution_record`

`bind_trial_arm` (1220)、`assert_issued_trial_arm_execution` (1258)、
`assert_rederived_trial_arm_execution` (1290) も実在。C02 の gate 入力は実在する (`DW-O13` 充足)。

## M4. (P1) は字義どおりでは**反証**され、既存の射影機構が救う

`test_reflux_originless_compatibility.py` の凍結 golden `_PRE_WAVE_ORIGINLESS_BASELINE` は

- `acceptance` の **dict_keys 集合を exact に** pin する (14 key)
- `acceptance/schema_version` を `p3-8c-trial-acceptance-receipt/v1` に exact pin する
- `acceptance/non_certifying_reason_codes` を `list_length: 2` と 2 語の exact 値に pin する
- `acceptance/trials/*` の dict_keys 集合 (10 key) も exact pin する

ので、producer が v2 を出せば **additive でも golden は割れる**。v1 verifier を残しても救われない
(golden が捉えるのは producer の出力であって verifier の受理形ではない)。

**ただし救済の正規経路が既に在る。** `_project_t244_additions_to_pre_wave` (646 行) は、
過去の裁定済み追加を pre-wave の形へ射影して golden と突き合わせる関数であり、
`_project_t1185_generation_binding_to_generation_one` と
`_project_t1311_arm_authority_to_pre_wave` を段階的に適用している。
その射影は**盲目的な strip ではない** — 追加された各 field を
`assert event.pop("x") == <期待値>` の形で**値ごと消費**してから落とす。

**含意**: receipt v2 の正しい形は、この射影へ `_project_t822_receipt_v2_to_pre_wave` を足し、
v2 の新 field を期待値付きで消費してから v1 の形 (schema_version と 2 語の理由) へ戻すことである。
golden の逐語 bytes は 1 文字も書き換えない。これは「既存テストの期待値を変更する」に当たらない。

## M5. 凍結世代の発行器

`s8c_preregistration.prepare_revision` が canonical record を exclusive-create する。

- `ruling_reference` は `D[1-9][0-9]*` 必須 (g2 以降は省略不可)
- `protected_sha256` が前世代と同一なら `spurious-revision` で拒否 (= 空改訂の負の対照が既にある)
- `MAX_GENERATIONS = 1024`、現行 tip は g5 なので g6 に余裕あり
- record は `DECIDER_VERSION` を焼く。評価器の受理意味・拒否理由が変わるなら bump が必須 (D458)

## M6. 正式 receipt の凍結 bytes は 1 件も無い

`output/s8c-trial-registry/` は不在。producer が書く種類は
`receipts/<manifest_sha256>.json` / `registry.jsonl` / `lifecycle.jsonl` の 3 種で、
現在は fixture repository の中にしか生まれない (`DW-O10` の対象は fixture 経路のみ)。

## M7. 契約の名前と実装の実名を突き合わせる既存テストは 0 件

`consumer_requirement.entrypoints` / `reachable_from` の hop 名が、宣言された `path` の module に
実在するかを検査する test は repo に存在しない (`test_s8c_preregistration_predicates.py` の
`consumer_requirement` 参照は path 差し替えの schema 検査のみ)。本 wave の新設メタ検査の
純増検出力はここである。

## M8. DECIDER_VERSION bump と g6 発行は既存不変検査で結合済み

- `test_s8c_preregistration_invariant.py:188` は repo tip の世代 record の `decider_version` が
  module 定数 `DECIDER_VERSION` と一致することを要求する。したがって **bump だけして世代を
  発行しない形は既に赤になる** (逆に世代を出さずに bump できない)。
- `test_s8c_preregistration_invariant.py:142` は tip 世代番号を `generation_numbers[-1]` で
  動的に取るので、g6 の追加自体では赤にならない。
- 逐語 pin は `test_s8c_preregistration_core.py:2017` の
  `assert M.DECIDER_VERSION == "s8c-decider/v2"` の 1 箇所。U1 がここを v3 へ更新する。
- `prepare_revision` の `spurious-revision` 拒否と併せて、「世代だけ増やす空改訂」と
  「bump だけして世代を出さない」の両方向が既存機構で塞がっている。**本 wave は新しい
  negative control をこの面へ足す必要は無い** (足すと過剰決定になり単一理由性を壊す)。

## M9. `accept_trial` は 6 条件・20 箇所にある (段 2 プランの裏取り)

契約 JSON 全体の `accept_trial` 出現は 20。条件別: C02(2) C03(4) C07(2) C08(4) C09(4) C10(4)。
machine_checkable=true はうち C09/C10 だけ。

非機械条件の consumer entrypoint を実測した。

- C03: `['load_manifest', 'accept_trial']` — 実名は `load_trial_manifest` と
  `assert_trial_registry_acceptance`。**両方とも実在する関数の誤名である。**
- C08: `['admit_preregistration', 'accept_trial']` — `admit_preregistration` は**不在**
  (未実装機構の将来名)、`accept_trial` は誤名。
- C07: path が `s8c_result_judge.py` なので `accept_trial` は entrypoint ではない。

**含意**: 「実在する機構の誤名」と「未実装機構の将来名」は 1 条件の中に混在する。
段 2 プランがメタ検査を machine 条件へ限定したのは正しい (C10 の `verify_s8c_cross_binding` 不在は
正しい UNSATISFIED 証拠であり契約不正ではない)。ただし C03/C08 の `accept_trial` は
C09/C10 と同型の誤名であり、契約 bytes はどのみち動くので改名の追加費用はゼロである。
scope 判断は段 4 で行う。

## M10. 段 2 プランの主張の裏取り (親)

- `resolve_arm_input` (`s8c_arm_inputs.py:434`)、`assert_issued_resolved_arm_input` (:497)、
  `ARM_BINDING_DOMAIN_SEPARATOR_V1` (:34)、`_expected_registered_arm_execution_record`
  (`trial_registry.py:2490`) — **すべて実在**。
- `verify_s8c_cross_binding` は `autonomous_trial_completeness.py` に**不在** —
  C10 の `cross-binding-verifier-incomplete` はこれが原因という主張は正しい。

## M11. C02 の負の対照は「宣言済み ID」に合わせて設計できる (レンズ B 所見 3 の解)

`test_satisfiable_predicate_requires_negative_control` (`test_s8c_preregistration_predicates.py:1827`)
は machine 条件の `negative_control_id` 集合と `NEGATIVE_CONTROL_CASES` の**完全一致**を要求する。
C02 を machine へ載せる以上、`nc_c02_proposal_path_arm_collision` を実装せねばならない。

既存対照の作り方 (`_negative_control_case`, :594-661) は
「token-only の合成 source + 1 token の変異」であり、C02 でも同じ形が取れる。

- `arm-{arm}.exec-{digest}` の invocation namespace 構成子が
  `p3_autonomous_workload_trial.py:767` に実在する。
- したがって変異 = その f-string から arm と digest を落として 2 arm を同じ proposal path へ
  衝突させる形にでき、**宣言済み ID の字義どおり**になる。

**含意**: C02 の `required_evidence` に producer module の行を足し、`_evaluate_c02` が
namespace 構成子の digest 消費を要求すれば、事前登録された対照名が恒真でなくなる。
段 2 プランの「call edge 削除」だけの変異は宣言 ID と一致せず、採用しない。

## M12. 並行 wave の衝突 (レンズ B 所見 6/7 の裏取り、13:35 JST)

- `dev-wave-t1336-t1337-t1347-refreeze` の段 1 brief は成果物に
  `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json` と
  `docs/phase3-8c-preregistration.md` (§3/§4/§5/§6 前提条件 4・7) を明記する。**g6 が正面衝突する。**
  同 wave は実装差分ゼロ (docs-only) なので `DECIDER_VERSION` は bump しない。
- `t1333-t1310-workload-profile` の段 2 プランは
  `test_s8c_preregistration_predicates.py` (C01 snapshot 151 行)、`test_layer3_report.py`、
  `test_reflux_originless_compatibility.py`、`test_trial_registry.py` の 4 本を編集面に挙げる。
  **私の U1/U2 所有と全面的に重なる。**

## M13. 焦点走の推移 (親実測)

| 走行 | 対象 | 結果 |
|---|---|---|
| focus1 (13:41 JST, dispatch 920975) | prereg 3 file (U1 のみ) | 8 failed |
| focus2 (14:04 JST) | 11 file (U1+U2、DECIDER_VERSION consumer 込み) | **8 failed — U2 は新規の赤ゼロ** |
| focus3 (14:21 JST) | prereg 3 file (fix1 後) | **3 failed** |

focus3 の残り 3 件はすべて事前帰属済みの期待赤:
- `test_candidate_freeze_matches_contract_and_generation_chain` (U3 の世代発行で解消)
- `test_repository_tip_binds_current_decider_version_without_activation` (同上)
- `test_current_repository_snapshot_exactly_matches_head` (commit で解消)

focus2 で緑だったもの: `test_trial_registry.py`、`test_layer3_report.py`、
`test_reflux_originless_compatibility.py` (凍結 golden 互換)、`test_s8c_acceptance_receipt.py`、
新規 `test_s8c_acceptance_receipt_v2.py`、`test_plain_runner_coverage.py`、
`test_p3_autonomous_workload_trial.py`、`test_reflux_origin_binding.py`。

## M14. 親の argv ミス 1 件 (自己申告)

段 6 レビューの初回投入で `--stage review` に `--lane` を渡し、両子とも rc=2 で即死した
(`--lane は --stage consult でだけ指定できる`)。token 消費ゼロ。
新しい artifact 名 (`s6-revA` / `s6-revB`) で再投入した。既存 `.done` は再利用していない。
