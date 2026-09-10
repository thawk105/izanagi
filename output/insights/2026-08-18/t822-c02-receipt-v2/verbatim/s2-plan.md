## U1

以下の行番号は現 HEAD の編集アンカーである。

### 契約

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:46-72`

  - C02 を `machine_checkable: true` にする。
  - `consumer_requirement.entrypoints` を `bind_trial_arm` と `assert_trial_registry_acceptance` にする。
  - 古い宣言的 arm field を、`TrialArmExecutionBinding` の `input_schema_version`、`content_digest_sha256`、`arm_binding_digest_sha256`、report/run-start の `arm_execution`、cell descriptor、execution digest chain に置き換える。
  - `reachable_from` は次の実在経路へ置き換える。
    - `bind_trial_arm -> resolve_arm_input`
    - `assert_issued_trial_arm_execution -> assert_issued_resolved_arm_input`
    - `assert_rederived_trial_arm_execution -> assert_issued_trial_arm_execution -> bind_trial_arm`
    - `assert_trial_registry_acceptance -> _expected_registered_arm_execution_record`
    - `assert_trial_registry_acceptance -> validate_execution_input_descriptor -> assert_execution_digest_chain`
  - `static_only_note` は「静的 call edge のみを検査し、run bytes の証明は receipt v2 が担う」と明記する。

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:339-368`

  - C09 の field path、reachable root、consumer entrypoint にある全 `accept_trial` を `assert_trial_registry_acceptance` にする。

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:371-410`

  - C10 の両 evidence row、field path、consumer entrypointにある全 `accept_trial` を同じ実名へ置換する。
  - `verify_s8c_cross_binding` は未実装であることを表す proof target なので残す。

### C02 評価器の正確な述語

`orchestrator/campaign/s8c_preregistration_evidence.py:48-85` に `ARM_BINDING_CONSUMER_UNREACHABLE = "arm-binding-consumer-unreachable"` を追加し、`_evaluate_c01` の直後、現 `:1448` の前へ `_evaluate_c02` を置く。

`_functions` と `_called_names` (`:290-308`) を使い、次をすべて要求する。

| caller | 必須の直接 call | 現 HEAD |
|---|---|---|
| `bind_trial_arm` (`trial_registry.py:1220-1255`) | `assert_issued_trial_binding`, `resolve_arm_input` | 両方あり |
| `assert_issued_trial_arm_execution` (`:1258-1287`) | `assert_issued_trial_binding`, `assert_issued_resolved_arm_input` | 両方あり |
| `assert_rederived_trial_arm_execution` (`:1290-1307`) | `assert_issued_trial_arm_execution`, `bind_trial_arm` | 両方あり |
| `_expected_registered_arm_execution_record` (`:2490-2510`) | `resolve_arm_input` | あり |
| `assert_trial_registry_acceptance` (`:2556-2936`) | `_expected_registered_arm_execution_record`, `validate_execution_input_descriptor`, `assert_execution_digest_chain` | 3 本ともあり |

さらに binding 側に `input_schema_version`、`content_digest_sha256`、`arm_binding_digest_sha256`、acceptance 側に `arm_execution` の literal があることを要求する。

いずれかの関数または edge が欠けた場合は、コードを補うのではなく `UNSATISFIED/arm-binding-consumer-unreachable` を返す。現 HEAD はこの述語を満たすため、最終行は他の実装済み評価器と同じ `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable` とする。`assert_trial_registry_acceptance` から `assert_rederived_trial_arm_execution` への call は現 HEAD に存在せず、独立再導出は `_expected_registered_arm_execution_record` が担当しているため要求しない。

- `orchestrator/campaign/s8c_preregistration_evidence.py:1648-1659`

  - `_MACHINE_EVALUATORS` に `2: _evaluate_c02` を追加する。
  - `MACHINE_CHECKABLE_CONDITION_IDS` は自動的に 7 条件になる。
  - `SATISFIABLE_CONDITION_IDS = frozenset()` は一切変更しない。

- `orchestrator/campaign/s8c_preregistration_evidence.py:1662-1675`

  - `_evaluate_undefined` の C02 専用 `arm-binding-declared-only` 分岐を削除する。

実名化後も C09 の acceptance AST には `assert_campaign_layer3_chain` がないため、C09 は `UNSATISFIED/formal-acceptance-layer3-consumer-absent` のままである。C10 は `autonomous_trial_completeness.py` に `verify_s8c_cross_binding` 自体がなく、acceptance 検査より先に `UNSATISFIED/cross-binding-verifier-incomplete` となる。

### AST メタ検査

`orchestrator/tests/test_s8c_preregistration_invariant.py:239` 付近へ次の検査を追加する。

- 対象は `machine_checkable: true` の条件に限定する。非機械条件 C03/C07/C08 は未実装名を将来 proof として保持しているためである。
- `consumer_requirement.entrypoints` が consumer module の top-level `FunctionDef` または `AsyncFunctionDef` に全て実在すること。
- evidence path と consumer path が同一で、`reachable_from` の先頭 hop が Python identifier の場合、その関数が同 module の top-level AST に実在すること。
- 各 consumer entrypoint が少なくとも一つの `reachable_from` chain に exact hop として現れること。
- 正の検査に加え、C09 の entrypoint、field prefix、reachable root をメモリ上で `accept_trial` に戻した変異を作り、欠落 tuple が `("C09", "orchestrator/campaign/trial_registry.py", "accept_trial")` になることを assert する。

第二 hop 以降を無条件に検査してはならない。そうすると、欠落していること自体が C10 の UNSATISFIED 証拠である `verify_s8c_cross_binding` まで「契約不正」となり、評価器の負判定と矛盾する。

### テスト更新

- `orchestrator/tests/test_s8c_preregistration_predicates.py:152`  
  C02 snapshot を `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable` へ更新する。

- 同 `:373-393,594-670`  
  C02 の実関数と call edge を持つ最小 AST fixture、および `assert_execution_digest_chain` など一辺を消す負の fixture を追加する。負例は `UNSATISFIED/arm-binding-consumer-unreachable` を exact assert する。

- 同 `:1827-1846`  
  machine ID を `{1,2,4,9,10,11,12}`、件数を 7 にする。

- 同 `:1868-1875`  
  C02 の負理由を期待 map に追加する。

- 同 `:1948-1961`  
  「未登録 evaluator なのに machine=true」の対象を C02 から非機械条件 C03 へ移す。検査自体は緩和しない。

- 同 `:2055-2065`  
  evaluator/contract の全単射を 7 条件で確認する。

- `orchestrator/campaign/s8c_preregistration.py:50`  
  `DECIDER_VERSION = "s8c-decider/v3"`。

- `orchestrator/tests/test_s8c_preregistration_core.py:2016-2017,2067,2090`  
  hard-coded v2 を v3 へ更新する。

受理集合は広がらない。C02 は成功時にも SATISFIED を返さず、C09/C10 も UNSATISFIED のままであり、`SATISFIABLE_CONDITION_IDS` は空のままである。`test_candidate_is_not_effective_and_has_zero_satisfied_predicates` (`test_s8c_preregistration_invariant.py:276-288`) は期待値を変えない。

## U2

### receipt v2 schema

`orchestrator/campaign/s8c_acceptance_receipt.py:23-60` を次の形へ分離する。

- `LEGACY_SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v1"`
- `SCHEMA_VERSION = "p3-8c-trial-acceptance-receipt/v2"`
- v1 必須理由は従来の 2 件。
- v2 必須理由は `t468-approval-authority-absent` のみ。
- `_V1_TRIAL_KEYS` は現行集合、`_V2_TRIAL_KEYS` はそこへ必須の `arm_execution` を加えた集合。
- `arm_execution` の exact key は `input_schema_version`、`content_digest_sha256`、`arm_binding_digest_sha256`。

`orchestrator/campaign/s8c_acceptance_receipt.py:75-125` に frozen dataclass を追加し、v1 trial は `arm_execution=None`、v2 trial は値必須とする。両版とも `certifying` は構造的に `False` のままにする。

`parse_acceptance_receipt_bytes` (`:234-358`) は schema で分岐する。

- v1 は旧 key 集合と旧 2 理由を exact に要求する。
- v2 は六つの `(holdout, arm)` が `H1/H2 × on/off/swapped` と完全一致することを要求する。
- 各 binding digest を、T-1311 と同じ  
  `SHA256(ARM_BINDING_DOMAIN_SEPARATOR_V1 || holdout || arm || content_digest_sha256)`  
  で再計算する。
- 同一 holdout の三つの `content_digest_sha256` が pairwise distinct であることを要求する。
- `t468-approval-authority-absent` は常に必須とする。
- `c02-arm-binding-unproven` を省けるのは、v2 の六行全てが上記検査を通る場合だけとする。

`_assert_digest` (`:481-486`) は検証済み bytes を返す helper にし、`verify_acceptance_receipt` の trial loop (`:619-626`) で v2 のみ次を追加検証する。

- receipt row の `trial_id`、`arm`、`holdout`、`measurement_head`、`arm_execution` が、hash 済み report bytes の同値と一致する。
- hash 済み attempt journal に `run-start` が一つだけあり、その `arm_execution` が report と receipt の双方に一致する。

したがって理由を落とせる入力は「完全な v2 六行、正しい binding digest、holdout 内で異なる content digest、hash 参照先の report/run-start と exact 一致」のみである。v1、field 欠落、digest 衝突、report 不一致、binding digest 偽造のいずれも落とせない。

### producer

- `orchestrator/campaign/trial_registry.py:2-6`  
  「declared only」という説明を、receipt v2 は execution binding を投影するが approval authority は未解決、へ更新する。

- 同 `:239-246`  
  `AcceptanceSummary.arm_binding` を `"execution-bound"` にする。`certifying=False` は維持する。

- 同 `:2757-2841`  
  現在の report/run-start 一致、historical rederive、descriptor validation、execution digest chain の順序は変更しない。これが receipt 発行前の authority gate である。

- 同 `:2861-2900`  
  各 receipt trial に、既に検証済みの `item.report["arm_execution"]` を exact copy する。

- 同 `:2901-2924`  
  schema v2 と v2 必須理由集合を使う。発行理由は `["t468-approval-authority-absent"]` となるが、`"certifying": False` は literal のままにする。

### 負の対照 3 種

新規 `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` に self-run harness を付け、次の予定位置へ置く。

1. `:135-160` — 同一 holdout の二 arm を同じ content digest にする。両方の binding digest は正しく再計算して、単純な digest 不一致では逃げられない変異にする。  
   `parse_acceptance_receipt_bytes` に対する `pytest.raises` が、新 validator 挿入位置 `s8c_acceptance_receipt.py` の現 `:341` 直後で `[receipt-arm-binding] ... pairwise distinct` になることを assert する。

2. `:163-192` — receipt の一 trial の binding field のみ変更し、report bytes とその hash は変更しない。構造 parse は通す。  
   `verify_acceptance_receipt` に対する `pytest.raises` が、現 `s8c_acceptance_receipt.py:619-626` の report bytes 比較位置で `[receipt-arm-binding] trial report arm_execution differs from receipt` になることを assert する。

3. `:195-218` — v2 trial から `arm_execution` を削除し、同時に C02 理由を省く。  
   `parse_acceptance_receipt_bytes` に対する `pytest.raises` が、現 `s8c_acceptance_receipt.py:294` 相当の `_exact_keys(..., _V2_TRIAL_KEYS, ...)` で `[receipt-schema] trials[0] key set differs` になることを assert する。

同 file の `:105-132` には、実 JSON report と JSONL run-start を使い、v2 producer 相当の receipt が full verify を通り、C02 理由がなく、t468 があり、`certifying is False` である正例を置く。EOF に `pytest.main([__file__])` の self-run harness を置く。

### v1 と golden

- `orchestrator/tests/test_s8c_acceptance_receipt.py:62-121`  
  fixture を明示的に `LEGACY_SCHEMA_VERSION` と v1 必須理由で生成し、既存 v1 parse/verify テストを残す。

- `orchestrator/tests/test_layer3_report.py:249-345`  
  receipt fixture を同じ legacy constants へ固定する。`layer3_report.py:582-590` は schema にかかわらず `certifying=False` を拒否するため、本体変更は不要である。

- `orchestrator/tests/test_trial_registry.py:964-1029`  
  producer の exact receipt 期待値を v2、trial `arm_execution`、理由 t468 のみに更新し、summary を `"execution-bound"` とする。

- 同 `:2538-2566`  
  test 名を v2 にし、C02 理由がないこと、t468 があること、`certifying=False` しか発行しないことを exact assert する。

- 同 `:2657`  
  CLI 出力期待を `"execution-bound"` にする。

v1 parser を残すだけでは originless golden は保てない。`test_reflux_originless_compatibility.py:272-286,359-389,745-765` は全 dict の key 集合、list 長、非 volatile scalar を exact 比較するため、v2 producer による schema scalar、理由 list、trial key 集合の全てが差分になる。

そこで `test_reflux_originless_compatibility.py:567` の T-1311 projector より前に `_project_t822_receipt_v2_to_v1` を追加する。

- receipt が v2、`certifying=False`、理由が t468 のみであることを assert。
- trial ID で report と結び、receipt の `arm_execution` が report と exact 一致することを assert。
- receipt trial から field を消し、schema を v1、理由を旧 2 件へ戻す。
- その後に既存 `_project_t1311_arm_authority_to_pre_wave` を呼び、report/run-start 側の arm field を消す。
- 巨大 golden literal `:239` は編集しない。

`orchestrator/tests/README.md:174` に新規 v2 test file を追記する。`test_plain_runner_coverage.py` は自動発見するため本体変更不要だが、新規 file の self-run harness を検査対象に含める。

## U3

U1/U2 の source、tests、contract、docs の最終 bytes が確定した後、親が次の順で行う。

1. `docs/phase3-8c-preregistration.md:176-223` の §6 条件 2を、T-1311 の二層 digest、pairwise distinct、七つの sink、historical acceptance、receipt v2 へ更新する。静的 evaluator の終端は非充足であることも明記する。

2. 同 `:261-270` の「発効の判定と条件契約の凍結」現在地を、machine evaluator 7 条件、非機械 5 条件、SATISFIED 0 件、`DECIDER_VERSION=v3`、C02 の現終端へ更新する。

3. 同 `:305-307` の衝突 (d) を、「arm authority 自体は T-1311 と receipt v2 で解消したが、t468 の approval authority が残り certifying は false」と更新する。

4. 最終 contract bytes から新しい `evidence_contract_sha256` を計算し、`orchestrator/tests/test_s8c_preregistration_core.py:1158-1161` の現行 contract hash pin を更新する。`:1164-1172` の g1 historical pin は変更しない。

5. 実在する新しい裁定番号を使い、次を一度だけ実行する。  
   `python3 -m orchestrator.campaign.s8c_preregistration prepare-revision --repo-root . --commit HEAD --ruling-reference D<実番号> --revision-reason "T-822: C02 machine evaluator, receipt v2, and real acceptance entrypoint"`

6. `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json` が一件だけ増え、次を満たすことを検査する。
   - `generation_number == 6`
   - `schema_version == "s8c-prereg-condition-freeze/v2"`
   - `decider_version == "s8c-decider/v3"`
   - `supersedes_sha256` が g5 file bytes の SHA256
   - 新しい evidence hash、§6 condition hash、normative body hash、protected hash
   - g1からg5は byte 不変

7. decisions と worklog fragment は g6 の実 hash と実裁定番号が確定してから append-only で記録する。

凍結波及の全対象は以下である。

- contract本体、`evidence_contract_sha256` pin、g6 freeze record
- evaluator snapshot、machine ID 件数、C02 reason map、未登録 evaluator test
- `DECIDER_VERSION` と core の hard-coded v2 期待
- docs §6、現在地、衝突 (d) に由来する section/normative hashes
- receipt schema/reason constants、trial row key set、producer exact receipt、summary/CLI
- v1 receipt fixture、Layer 3 の legacy fixture、originless compatibility projector
- 新規 test indexとself-run coverage

正式な `output/s8c-trial-registry/` は存在しないため、移行または再発行すべき実 receipt artifact はない。歴史文書、旧 freeze g1からg5、巨大 originless golden literal は更新対象外である。

焦点テストと最終受入は親が `tools/run_tests.py` 経由で行い、直接 pytest を起動しない。その後 `tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の `tools/check_ai_provenance.py` を実行する。本起草ではいずれも実走していない。

## 反証

- **P1 はそのままでは成立しない。** v1 parser を残す additive schema でも、実 producer が v2 を出すため originless golden の exact key/scalar 比較は壊れる。上記の検証付き compatibility projector が必要である。

- **P2 は「receipt JSON 単体」なら成立しない。** 自己申告 field だけなら偽造できる。成立させるには、receipt が hash で名指す report と journal bytes を full verifier が読み、receipt/report/run-start の binding を一致させる必要がある。

- **P3 の g6 一回発行は成立するが、brief §6 の「g6 hash が U1/U2 双方の source bytes に依存する」は誤りである。** `s8c_preregistration.py:191-199` の protected preimage は evidence contract hash と docs の三 hashだけであり、receipt verifier や trial registry の source bytes は含まない。統合後に発行する順序は必要だが、U2 bytes への暗号学的束縛ではない。

- **メタ検査を「reachable_from に見える全 identifier」へ広げる案は成立しない。** C10 の `verify_s8c_cross_binding` は未実装であることが正しい UNSATISFIED 状態だからである。また非機械条件 C03/C07/C08 にも `accept_trial` が残る。したがって検査対象は machine 条件の consumer entrypoint と consumer module 上の実行 root に限定する。

- P4 は成立する。C02 evaluator は静的 AST だけ、実走 bytes は receipt verifier が担当する。

- P5 は指定された C02/C09/C10 の範囲では成立する。他条件の将来名まで無断で変更しない。

- P6 は、originless bundle が実 producer の v2 分岐を通り、projector がその field を report と照合してから旧 view へ落とすことで成立する。正式六 cell は発火条件にしない。

## 総括

- C02 は現 HEAD の実 AST 述語を満たすが、終端は `EVIDENCE_UNDEFINED` とし、SATISFIED 経路は作らない。
- receipt v2 が C02 理由を落とせるのは、六つの arm binding と hash 済み report/run-start が一致するときだけである。certifying は false、t468 は必須のまま。
- v1 parser は維持するが、originless golden には検証付き逆射影が必要である。
- U1 と U2 の編集集合は素集合である。ただし U2 は親 brief の列挙に加え、`test_s8c_acceptance_receipt.py`、`test_layer3_report.py`、`orchestrator/tests/README.md` も必要になる。交差 file はない。
- 反証対象は P1 の「additive だけで golden を保てる」という含意と、brief §6 の「g6 hash が U2 source bytes に依存する」という前提である。
- 本回答は read-only の静的起草であり、実装、pytest、受入検査は行っていない。