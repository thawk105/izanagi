## 変更面 (file:line の表)

| file:line | 変更 |
|---|---|
| [s8c_preregistration_evidence_contract.v1.json:399-412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:399) | C10 `cross_binding_verifier.field_paths` の `proposal.sha256` 直後へ exact に `"proposal.build_source_bindings"` を追加する。 |
| [s8c_preregistration_evidence.py:2222-2262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2222) | `_C10_FIELDS` へ `"proposal_build_source_bindings"` を追加し、C10 契約 field path の局所 drift 検査を追加する。 |
| [s8c_preregistration.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:51) | `DECIDER_VERSION` を `s8c-decider/v6` から `s8c-decider/v7` へ上げる。 |
| [test_s8c_preregistration_core.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:801) | 契約変更で動く 3 個の独立 hash pin を更新する。 |
| [test_s8c_preregistration_core.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:1195) | 現行 evidence contract の hash pin を更新する。 |
| [test_s8c_preregistration_core.py:2403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2403) | v6 固定のテスト名と期待値を v7 へ更新する。 |
| [test_s8c_preregistration_core.py:2439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2439) | invalid runtime decider テストの record 側期待値を v7 へ更新する。 |
| [test_s8c_preregistration_core.py:2460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2460) | hostile `str` subclass テストの record 側期待値を v7 へ更新する。 |
| [test_s8c_preregistration_predicates.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:856) | `TOKEN_ONLY_C10` の通る正例へ `"proposal_build_source_bindings"` を追加する。 |
| [test_s8c_preregistration_predicates.py:2818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:2818) | C10 の verifier literal と契約 field path の両方が load-bearing であることを検査する専用テストを近接追加する。 |
| `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g12.json:1` | `prepare-revision` CLI で canonical g12 を新規発行する。 |
| `docs/spool/worklog/2026-08-31-dev-wave-t1806-prereg-c10-fieldpaths-1.md:1` | T-1806 完了、D967、g12/v7、既存 campaign の E1-stale migration、実測結果を記録する。canonical 台帳は直接編集しない。 |

## 各変更の中身 (実際に書く差分の内容)

1. 契約 JSON

   追加文字列は exact に次である。

   ```json
   "proposal.build_source_bindings"
   ```

   挿入位置は `"proposal.sha256"` の直後、`"campaign_wal.build_records"` の直前とする。既存表記は、実装 literal の先頭 namespace を dot 接頭辞へ変換しており、例えば `proposal_path` が `proposal.path`、`provider_payload_sha256` が `provider.payload_sha256` である。[契約:400-411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:400) と [実装 field 集合:216-229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/autonomous_trial_completeness.py:216) の対応から、`proposal.build_source_bindings` が exact である。実際の receipt key も [autonomous_trial_completeness.py:4575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/autonomous_trial_completeness.py:4575) に存在する。

2. `_C10_FIELDS`

   `proposal_sha256` の次へ次を追加する。

   ```python
   "proposal_build_source_bindings",
   ```

   `_strings()` は対象関数 AST 内の全文字列定数を返す。[s8c_preregistration_evidence.py:373-378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:373) のため、`_C10_FIELDS <= _strings(verify)` は「`verify_s8c_cross_binding` の関数 AST に全 13 literal が存在する」という subset 検査である。新 literal は同関数内の [autonomous_trial_completeness.py:4575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/autonomous_trial_completeness.py:4575) にあるため現行実装は通る。

3. P2 の drift 検査

   C10 専用の `_C10_EXPECTED_FIELD_PATHS` を `_C10_FIELDS` の近くへ置き、C10 の `cross_binding_verifier` に属する全 13 個の契約表記を列挙する。`trial_registry` の別 evidence field は `_C10_FIELDS` の対応物ではないため、この局所検査へ混ぜない。

   ```python
   def _c10_field_paths_verdict(probe: _ConditionProbe) -> bool:
       # 契約記述と evaluator 期待値の整合だけを検査する。
       return all(
           field_path in probe.requirement(kind).field_paths
           for kind, field_path in _C10_EXPECTED_FIELD_PATHS
       )
   ```

   `_ConditionProbe.requirement()` は artifact kind が exact 1 件であることを要求する。[s8c_preregistration_evidence.py:732-736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:732) `field_paths` 自体も strict loader が重複なし tuple にする。[s8c_preregistration_evidence.py:184-190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:184)

   呼出位置は `_evaluate_c10` の最初の verifier guard、`verify is None` の直後、`_C10_FIELDS <= _strings(verify)` の前とする。[s8c_preregistration_evidence.py:2240-2249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2240) 失敗時は新 reason code を作らず、既存の `ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE` を返す。C06 が契約 drift と実装不備を既存の単一 reason へ畳む形と同型である。[s8c_preregistration_evidence.py:3513-3519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:3513)

4. C10 の終端

   現行 production の新 field は存在するため、追加後も第一 guard を通る。registry acceptance guard [s8c_preregistration_evidence.py:2250-2257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2250) も変更しない。したがって終端は引き続き:

   ```text
   EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable
   ```

   [s8c_preregistration_evidence.py:2258-2262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2258)

   新 literal または契約 field path が欠けた場合だけ、最初の分岐で `UNSATISFIED / cross-binding-verifier-incomplete` になる。`SATISFIABLE_CONDITION_IDS` は空集合のまま [s8c_preregistration_evidence.py:3075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:3075) であり、仮に evaluator が誤って `SATISFIED` を返しても [s8c_preregistration_evidence.py:3185-3193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:3185) が `ERROR` へ倒す。

5. version と hash pin

   契約の追加位置を上記で固定した場合の静的算出値は次である。

   - evidence contract: `26f7bd4776bff58753f7f1dc7ebecdc5a3d3f1e0f108e1fbc541fdd33dbc13e5`
   - protected: `ac26b828fefa02975ce44e4d281ee6f6b1f51d9d248b8ebfe5d05b2016ad8245`
   - non-path control `nul`: `32384037873e77965d97a175c60fe8197c094bf15ed4807f301f91d5229a4cdf`
   - non-path control `cr`: `23d2033d4870200472dfd9e0cc120b52f8bc61687a8b757c50123f045cc883e6`
   - non-path control `lf`: `c9885e599ad5e51dcbd566500fccab14dd49625fe555c4be9f5464094cc5bf90`

## 親の provisional への評価 (P1〜P4 それぞれに 賛成 / 反対 / 条件付き + 根拠 file:line)

| provisional | 評価 | 根拠 |
|---|---|---|
| P1 `_C10_FIELDS` も広げる | 賛成 | 契約 JSON は evaluator dispatch 時にロードされるが、C10 が実際の verifier field を要求する条件は `_C10_FIELDS <= _strings(verify)` である。[s8c_preregistration_evidence.py:2240-2249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2240) JSON だけの変更では正式 gate の検知集合が増えない。 |
| P2 drift 検査を入れる | 賛成 | `RequiredEvidence.field_paths` は既存の型と loader に既に存在する。[s8c_preregistration_evidence.py:94-99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:94) `_c06_reachable_from_verdict` の局所 membership idiom [s8c_preregistration_evidence.py:3279-3285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:3279) をC10の13 fieldだけへ適用すれば、新機構や一般化ではない。D967 の「契約を実装より弱い状態に残さない」を実行時にも束縛する本題の検査である。 |
| P3 phase doc は変更しない | 賛成 | 条件10の本文 [phase3-8c-preregistration.md:257-259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/docs/phase3-8c-preregistration.md:257) は field 名列挙ではない。個別 condition hash は markdown の条件文だけから算出される。[s8c_preregistration.py:1030-1050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:1030) JSON 変更は `evidence_contract_sha256` と、それを含む `protected_sha256` だけを動かす。[s8c_preregistration.py:203-211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:203) |
| P4 表記は `proposal.build_source_bindings` | 賛成 | `proposal_path` と `proposal_sha256` が `proposal.path` と `proposal.sha256` に対応する既存規約 [契約:405-406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:405) に従う。実 key は `proposal_build_source_bindings` [autonomous_trial_completeness.py:4575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/autonomous_trial_completeness.py:4575) なので exact な契約表記は `proposal.build_source_bindings` である。 |

## 凍結 g12 の発行手順

コード、契約、テストを編集したあと、まだそれらを commit する前に、手書きせず CLI を実行する。`prepare_revision()` は HEAD の既存 g11 を検証しつつ、worktree の新しい markdown と契約を読むためである。[s8c_preregistration.py:2035-2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:2035)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m orchestrator.campaign.s8c_preregistration \
  prepare-revision \
  --repo-root . \
  --commit HEAD \
  --ruling-reference D967 \
  --revision-reason 'T-1806/D967: C10 の field_paths に proposal.build_source_bindings を追加し evaluator と decider を追随'
```

`prepare_revision()` は `O_EXCL` で g12 を新規作成する。[s8c_preregistration.py:2097-2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:2097)

| g12 field | 値または算出元 |
|---|---|
| `schema_version` | `s8c-prereg-condition-freeze/v2` |
| `decider_version` | `s8c-decider/v7` |
| `normalization_version` | `s8c-prereg-markdown/v2` |
| `generation_number` | g11 の検証結果 `11 + 1 = 12` |
| `supersedes_sha256` | g11 file の raw canonical bytes の SHA-256。exact 値は `8fb7802e1866ea5ef4459a340512ae2080a93774af7e9795f1e6808082d8a307`。`protected_sha256` ではない。算出箇所は [s8c_preregistration.py:2071-2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:2071)。 |
| `source_path` | `docs/phase3-8c-preregistration.md` |
| `section5_field_names_sha256` | g11 と同じ `8ad36ad81439089be797c43133ce19b6082c0a9a3e21f6ead43b079f4c22107e` |
| `section6_conditions_sha256` | g11 と同じ `07439c4e5313b90f8be1920d1bbf977c77b4d47e0ed14de5a816b679a3e475c3` |
| `section6_condition_hashes` | 12件とも g11 と同一。特に condition 10 は `10f7e5f981b07b67e95a0aa35f4aa85f59260f2d556d2939f6765f5df169f783`。 |
| `normative_body_sha256` | g11 と同じ `6ba0b6dcf57d59f98b7659331b49277689a92bbbb8b5d66f0f38fa94cc838f1a` |
| `evidence_contract_sha256` | `26f7bd4776bff58753f7f1dc7ebecdc5a3d3f1e0f108e1fbc541fdd33dbc13e5` |
| `protected_sha256` | `ac26b828fefa02975ce44e4d281ee6f6b1f51d9d248b8ebfe5d05b2016ad8245` |
| `revision_reason` | 上記 CLI の exact 文字列 |
| `ruling_reference` | `D967` |

`section6_condition_hashes` は動かない。したがって `docs/phase3-8c-preregistration.md` の編集は不要である。動くのは契約 semantic hash と、それを preimage に含む protected hashだけである。[s8c_preregistration.py:2006-2032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:2006)

## 影響テストの完全列挙

既存テストで期待値または fixture の編集が必要なもの:

| test / file:line | 追随内容 |
|---|---|
| [test_evidence_contract_hash_accepts_non_path_controls:801-830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:801) | `nul`、`cr`、`lf` の3 hashを上記値へ更新。 |
| [test_current_evidence_contract_hash_is_frozen:1195-1198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:1195) | hashを `26f7bd...13e5` へ更新。 |
| [test_decider_version_binds_cross_module_semantics_to_v6:2403-2404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2403) | test名と literal を v7 へ更新。 |
| [test_invalid_running_decider_version_cannot_activate:2439-2457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2439) | line 2454 の record 側期待を v7 へ更新。 |
| [test_valid_hostile_str_subclass_cannot_fake_decider_version_match:2460-2480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2460) | line 2477 の record 側期待を v7 へ更新。 |
| [TOKEN_ONLY_C10:856-867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:856) / [test_noop_and_token_only_fixtures_never_satisfy:2818-2850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:2818) | 正例 fixture に新 literal を足す。既存 raw-response negative control の期待は変えない。 |

最終差分を動的に検証するが、テストソースの期待変更は不要なもの:

- [test_current_repository_snapshot_exactly_matches_head:243-249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:243)
- [test_current_repository_gap_reason_snapshot_requires_cross_wave_review:253-302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:253): C10 の終端が変わらないことを確認する。
- [test_satisfiable_predicate_requires_negative_control:2771-2792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:2771): 空の `SATISFIABLE_CONDITION_IDS` を維持する。
- [test_candidate_freeze_matches_contract_and_generation_chain:389-425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_invariant.py:389): g12 と新契約 hash の一致を確認する。
- [test_repository_tip_binds_current_decider_version_without_activation:449-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_invariant.py:449): tip g12 が v7 であることと、未発効のままであることを確認する。
- [test_candidate_is_not_effective_and_has_zero_satisfied_predicates:603-616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_invariant.py:603)

新設するテスト:

```python
@pytest.mark.parametrize(
    "mutation",
    ("verifier-literal", "contract-field-path"),
)
def test_c10_proposal_build_source_bindings_is_load_bearing(
    tmp_path: Path,
    mutation: str,
) -> None:
    ...
```

通る正例は、更新した `TOKEN_ONLY_C10` と `TOKEN_ONLY_C10_REGISTRY`、および新 field path を含む現契約を commit したもの。期待は:

```python
assert baseline.status is core.PredicateStatus.EVIDENCE_UNDEFINED
assert baseline.reason_code == "completion-proof-not-machine-checkable"
```

その後、パラメータごとに次の片側だけを壊す。

- verifier の `"proposal_build_source_bindings"` を別 literal へ置換する。
- 契約の `"proposal.build_source_bindings"` を削除する。

両方とも期待は `UNSATISFIED / cross-binding-verifier-incomplete` とする。

DECIDER_VERSION の全件確認について、親の4箇所には修正が1点ある。

- pytest で直接赤になる literal assertion は core の [2404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2404)、[2454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2454)、[2477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:2477) の3箇所。
- [test_s8c_gate_report.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_gate_report.py:84) は任意の synthetic source report を自己投影する fixtureで、production `DECIDER_VERSION` を参照しない。v6のままでもテストは赤にならず、更新不要。
- 親検索が落としていた実際の4件目は [test_repository_tip_binds_current_decider_version_without_activation:449-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_invariant.py:449)。v7へ上げてg12を発行しなければ動的比較が赤になる。g12で解消し、テストコードは変えない。
- g10とg11の `s8c-decider/v6` は歴史 record なので変更しない。

この段では pytest は実走しておらず、緑とは報告しない。

## 実装しないと決めたこと (と、その理由)

- `docs/phase3-8c-preregistration.md` は変更しない。条件10の散文は field 列挙ではなく、section 6 hash を動かす根拠がない。
- `SATISFIABLE_CONDITION_IDS` は変更しない。C10を `SATISFIED` にする分岐も追加しない。
- `CONTRACT_LOADER_RELATIVE_PATHS` の構成は変更しない。現行24 pathのうち core と evaluator は既に [campaign_lock.py:64-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/campaign_lock.py:64) に含まれるため、その bytes 変更による既存 campaign の E1-stale はD967どおり正直に記録する。契約 JSON を閉包へ追加しない。
- `autonomous_trial_completeness.py` は変更しない。必要な field は既に exact field 集合と receipt に存在する。
- 新しい reason code、汎用 drift framework、別 gate、台帳は作らない。
- `_strings()` を live-code解析へ一般化しない。本件は既存C10 idiomへ新 literal を追加する局所変更に留める。
- g10、g11は編集しない。g12を手書きしない。
- `test_s8c_gate_report.py:84` は更新しない。production版の pin ではない。
- skip、xfail、期待反転、述語緩和は行わない。

## 総括

実装単位は、契約へ exact に `proposal.build_source_bindings` を追加し、正式 gate の `_C10_FIELDS` へ `proposal_build_source_bindings` を追加し、13 field限定の契約 drift 検査を既存 reasonへ接続することになる。C10の正常終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままで、受理集合は広がらない。

同じ変更単位で decider v7、g12、hash pin、C10正負テスト、E1-stale migration の worklog fragmentを追随させる。`section6_condition_hashes` と規範 markdownは不変である。静的読解と hash算出のみ実施し、pytestは実走していない。