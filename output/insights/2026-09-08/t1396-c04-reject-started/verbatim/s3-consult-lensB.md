## 総括

最大の取り残しは焦点走の列挙である。実検索では production module 名を参照する test file は 1 件でなく 4 件あり、さらに 1 metadata file と間接 consumer がある。  
変異を追加負例 node だけで走らせれば帰属は成立するが、repo-wide 走では enforcement-source drift により無関係な fixture が先に落ち得る。  
一方、`TOKEN_ONLY_C04` 自体の既存 consumer 列挙、C04 reason 据え置き、既存 negative-control ID の再利用は静的に破れなかった。  
registry の `_functions` 拡張は、先行する到達検査から論理的に含意される冗長検査であり、D1292 の最小変更には不要である。

## 所見

### 焦点走を 1 test file とする列挙は不完全

- file:line: `s2-plan.md:168`, `s2-plan.md:175`
- 実際の `rg -l 's8c_preregistration_evidence' orchestrator/tests` は次の 5 path を返す。

  - `orchestrator/tests/test_s8c_preregistration_predicates.py:24`
  - `orchestrator/tests/test_s8c_preregistration_core.py:2554`
  - `orchestrator/tests/test_t671_source_binding.py:53`
  - `orchestrator/tests/test_artifact_admission.py:62`
  - `orchestrator/tests/acceptance_duration_ledger.json:18437`（test file ではなく metadata）

- プランは predicates file だけを「確定」としており、今回の射影に `campaign_lock.py` と tests 全体が含まれる事実とも食い違う。
- 成果物影響: evaluator は `campaign_lock.py:65` の enforcement-source closure に含まれるため、commit 後の campaign lock は新しい evaluator blob hash を記録する。この consumer 群を外すと、certified artifact が参照する source-binding 系の回帰検査を焦点走から落とす。
- 重さ: **must-fix**

### C04 の広義 reader／metadata inventory に取り残しがある

- file:line: `orchestrator/tests/test_s8c_preregistration_invariant.py:70`, `:78`, `:357`
- `MACHINE_CONTRACT_FUNCTION_CHECKS` は C04 の `main`、`run_trial`、`mark_experiment_indeterminate`、`forbid_trial_restart`、`reject_started_trial` を既に exact-set 化し、`test_s8c_preregistration_invariant.py:482` がその集合を検査する。これはプランの波及一覧にない。
- `test_s8c_preregistration_predicates.py:4007` の全 machine evaluator 表、同 `:4223` の contract/evaluator bijection も広義の C04 reader だが列挙されていない。
- `acceptance_duration_ledger.json:16215` 以下には既存 C04 node が並ぶが、追加予定 node は当然まだ存在しない。
- 成果物影響: invariant の期待は既に正しく値変更不要。duration ledger では新 node が未知 duration になり、acceptance scheduling の参照だけが変わる。certified 選択・predicate report 値は変わらない。
- 重さ: **nit**

### registry 存在検査は到達検査に対して冗長

- file:line: `s2-plan.md:32`, `s2-plan.md:35`
- resolver は対象名が target module の関数集合にある場合だけ target を返す（`s8c_preregistration_evidence.py:1045`）。その target だけが `graph.calls` に追加される（同 `:1393`, `:1396`）。さらに `_declared_call` は target が `graph.calls` にあることを要求する（同 `:1486`）。
- したがって新しい `(registry_path, "reject_started_trial")` の `_declared_call` が真なら、後段の `reject_started_trial in _functions(registry)` も真である。定義欠落は先に `crash-policy-cell-partial` へ落ち、追加した後段から `restart-guard-absent` を返す経路は作れない。
- 成果物影響: 受理集合と report reason を狭めるのは 3 件目の target 追加だけで、後段検査は certified 選択・report・台帳の値を変えない。
- 重さ: **nit**

### 変異帰属は owner node 単独なら成立、広い走では mask 候補がある

- file:line: `s2-plan.md:98`, `s2-plan.md:116`
- 固有 node は  
  `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c04_rejects_missing_started_trial_preflight`
- 3 件目の target だけを evaluator から落とすと、新テストの mutation 後 source は旧 2 target を満たし、registry 定義も残るため `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ進む。予定された `UNSATISFIED` assertion が固有に赤くなる。
- 一方、repo-wide mutant では `test_p3_b4_raw_record_producer.py:107` が実 repository に対して `capture_contract_loader_binding` と live verify を実行する。その呼出しは同 `:153`、`:351` から evidence fixture 全体へ波及する。静的に確認できる mask 候補は次の群。

  - 直接 fixture 構築: `test_certified_evidence_fixture_scope_holds_both_modes_through_yield`（`:1496`）、`test_m09...`（`:2131`）、`test_m10_empty...`（`:2150`）、`test_m11...`（`:2167`）、`test_abort_reason...`（`:2179`）、`test_m14...`（`:2232`）、`test_m15...`（`:2255`）、checkpoint/absence/auxiliary の 3 test（`:2389`, `:2414`, `:2446`）。
  - `certified_evidence*` fixture 利用群: `:1989–2114`, `:2139`, `:2187`, `:2223`, `:2272–2354`, `:2470–2480`, `:2631`, `:2668`。

- fixture の共有・xdist 配置・cache により実際に何 node が mask になるかは静的には確定しない。ここは **probe で観測が要る**。
- 成果物影響: mask 側は `contract-loader-drift` で campaign.lock/WAL 作成前に止まり、owner の C04 report 差ではなく「成果物未生成」という別原因の赤を増やす。
- 重さ: **must-fix**

### 親 probe の一般化限界

- file:line: `s8c_preregistration_evidence.py:2061`, `:2065`, `:2073`
- 実測した同一 commit について、実 resolver による 3 件目の `_declared_call=True` が確認済みなら、上記の含意により追加予定の `_functions` 検査も通る。したがって「その commit の C04 reason は据え置き」という限定結論は妥当。
- 食い違う条件は、wrapper が実 graph membership を使わず 3 件目を合成して真にした場合、実装が異なる path/name を検査した場合、または probe と実装後評価で commit が変わった場合である。実 `_declared_call=True` の同一 probe/commit について、存在検査だけが偽になる通常経路はない。
- この 1 回から token-only fixture、過去 commit、将来の production source、activation/source-binding の結果、他 reason snapshot まで一般化してはいけない。
- 成果物影響: 過剰一般化すると、別 commit で C04 が `crash-policy-cell-partial` へ変わる report 差や、dirty evaluator による source-binding rejection を見落とす。
- 重さ: **must-fix**

### brief に 2-file scope 外の記録が混ざる

- file:line: `s1-brief.md:10`, `s1-brief.md:58`
- line 10 は編集面を 2 file に固定する一方、line 58 は「docs 記録は spool fragment」とし、第三の書込みを成果物の形へ含めている。D1292 の実装そのものには不要。
- プラン本体には仮想リスク向け gate・検査・台帳・一般化の新設は見当たらない。source-binding の説明は既存 gate の実行時注意であり、production scope 拡張ではない。
- 成果物影響: predicate の受理集合・report・certified 選択には影響しないが、2-file scope と実 commit の構成が不一致になる。
- 重さ: **nit**

## 焦点走に含める test file 集合

`rg -l 's8c_preregistration_evidence' orchestrator/tests` の test file 全件:

| test file | 分類 |
|---|---|
| `orchestrator/tests/test_s8c_preregistration_predicates.py` | 今回の実期待変更を所有する。fixture/stub bytes と新 node が変わる。既存 reason 期待は据え置き。未 commit drift だけの赤ではない。 |
| `orchestrator/tests/test_s8c_preregistration_core.py` | `:2554`, `:2581`, `:2604`, `:2626` で live evaluator bytes を temp commit へコピーする。hash も実 bytes から計算するため既存期待変更なし。dirty だけの赤は予測しない。 |
| `orchestrator/tests/test_t671_source_binding.py` | evaluator path を closure/parametrize に含む。`_assert_pre_t1287...` は temp repo へコピー・commit 後に意図的 drift を作る（`:356–384`）ため、今回の bytes 内容による期待変更なし。 |
| `orchestrator/tests/test_artifact_admission.py` | evaluator path は exact closure 表（`:62`, `:88`）。共有 lock helper は live disk でなく recorded HEAD blob を読むため、内容固有の期待変更なし。full-file の未 commit mask 有無は実走での確認対象。 |

test file ではない検索結果:

- `orchestrator/tests/acceptance_duration_ledger.json` — 新 node は未登録。テスト結果ではなく scheduling metadata の差。

追加する間接 consumer（推測ではなくコードで実証）:

- `[間接] orchestrator/tests/test_campaign_lock_codec.py` — `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` を parametrize するため、`:272–285` が evaluator path の node を生成する。期待変更なし。
- `[間接] orchestrator/tests/test_s8c_preregistration_invariant.py` — C04 の contract target exact-set に `reject_started_trial` を既に含む（`:70–78`）。期待変更なし。

## scope 外の real 所見

- `orchestrator/tests/test_p3_b4_raw_record_producer.py:107–109` は repo-wide mutant での実在する `contract-loader-drift` mask 面である。2-file 実装 scope 外だが、段 6 の帰属資料では分離が必要。
- `orchestrator/tests/acceptance_duration_ledger.json` には追加 node の duration がない。これは test scheduling metadata の更新問題であり、今回の 2-file production/test 変更へ混ぜる根拠はない。
- production の preflight 自体は `p3_autonomous_workload_trial.py:4598–4602`、helper は同 `:1430–1436`。さらに runtime 順序は `test_p3_autonomous_workload_trial.py:8913–8959` が既に観測している。今回その test の期待値は変わらない。

## プランと brief への同意点

- `TOKEN_ONLY_C04` の literal reader は定義と `_negative_control_case` の C04 branch だけであり（`test_s8c_preregistration_predicates.py:784`, `:1203`）、既存の間接 C04 baseline consumer 6 系統はプランの一覧で覆われている。
- C04 branch は呼出しごとに新しい `sources` dict を返す（`:1203–1209`）。他 condition の branch や registry stub と共有しない。stub 拡張の副作用は C04 parametrized baseline 群に限定され、既存期待値は変わらない。
- `NEGATIVE_CONTROL_CASES` は契約 ID の一対一表（`:1309–1320`）であり、新 ID を増やさず別 mutation axis とする判断は exact-set 検査（`:2910–2931`）と整合する。
- DW-M08 の新旧差は、同じ固有 node  
  `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c04_rejects_missing_started_trial_preflight`  
  で示せる。旧 evaluator＋新 test/fixture では赤、新 evaluator では通る、という差になる。
- 現 production の `main → run_trial → _reject_registered_lifecycle_duplicate → reject_started_trial` は `p3_autonomous_workload_trial.py:5201`, `:4598–4602`, `:1430–1436` にあり、同一 HEAD に限定した C04 reason 据え置き判断は妥当である。