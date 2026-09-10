## 結論

(P1-b) の「小さい明示文法に適合する C++ テキスト」を採る。候補全文を閉じた文法で解析して 79 値の型付き IR のいずれかへ変換し、trusted evaluator が関係行列を生成する。JSON wire は採らない。

実 TU の compile / 実行は残すが、行列の権威にはしない。実行行列が trusted 行列と 1 cell でも異なれば `REJECT` とし、実行行列へフォールバックしない。

これは D39 の raw C++ 独立合成を別実験へ移す変更である。D344 を supersede したとは記録せず、D1451 に従い「別実験」と明記する。

## 受理権威の役割分離

| 機構 | 本 wave 後の位置づけ |
|---|---|
| IR admission | **(a) 受理権威として残る。** 候補 C++ テキストが 79 値の型付き IR に属するかを決める唯一の comparator-language authority。 |
| `_validate_single_sort_statement` | **(b) 恒真化する。** trusted renderer の出力にだけ適用する事後条件へ降格し、候補 gate として数えない。現行位置は [sort_swo_oracle.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:523)。 |
| `coder_effect_gate.DENY_TABLE` | **(c) 別の関心事として残る。** hole 全般の host-effect 防御であり、IR membership の権威ではない。[coder_effect_gate.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/coder_effect_gate.py:58) と [scan_host_effects:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/coder_effect_gate.py:576) は変更しない。 |
| SWO oracle 本体 | **(c) 別の関心事として残る。** admitted IR の trusted 行列に対する有限 corpus の公理確認と、実 TU 行列との conformance 確認を担う。候補言語を独立に受理しない。 |
| `sort_comparator_authority` | **(a) 別 domain の受理権威として残る。** certified `sort_best` の name↔comparator 15 組 exact binding 専用。[sort_comparator_authority.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_comparator_authority.py:54)-65 は触らない。 |

T-396 の失敗型には当たらない。破棄された設計では同じ hole property を二つの gate が独立に「受理済み」と主張していたが、本案では comparator-language membership を主張できるのは IR admission だけである。旧 validator は renderer assertion、effect gate は host effect、実行行列は conformance evidence、15 組 exact binding は certified freeze の別 domain に限定する。

ただし `_validate_single_sort_statement` や実行由来の SWO 判定を再び候補受理 gate として数える実装にすると、同じ失敗型へ戻る。その配線は禁止する。

## 候補提出形の択一

| 案 | file:line 単位の変更 | D344 の「任意 C++ からの字句抽出」か |
|---|---|---|
| **P1-b: 明示文法の C++ テキスト** | [CoderProposalSort:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop_sort.py:154)-162 の `implementation: str` を維持。[agent:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/coder-v4-autonomous-sort.md:58)-82 と [agent:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/coder-v4-autonomous-sort.md:118)-128 を新文法へ縮める。[check_materialized_sort_swo:2685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2685)-2700 で候補全文を IR admission へ渡す。S1 の comparator 文字列と呼出し [s1_direct_comparison.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s1_direct_comparison.py:842)-890 は形を維持する。 | **当たらない。** 任意 C++ から comparator を切り出さず、全文が閉じた production に一致しなければ固定理由で拒否する。D344 が却下した IR 方向そのものではあるが、D1451 が別実験として設計着手を許可済み。 |
| JSON wire | `CoderProposalSort.implementation` と agent 出力 schema を JSON/構造値へ変更し、[_quarantine_and_audit:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop_sort.py:180)-219 の materialization 前に admit/render が必要。S1 は [s1_direct_comparison.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s1_direct_comparison.py:843)-889 で依然 C++ comparator を持つため、15 literal の逆変換か freeze schema の二重表現が必要になる。 | **当たらない。** C++ 字句解析自体をしない。ただし autonomous JSON と certified C++ の二つの ingress を作りやすく、受理権威分離が複雑になる。 |

推奨は P1-b。backoff 軸は既に C++ テキストを提出形とし、判定順序、固定 rule/reason、候補 bytes 非射影、canonicalization を [backoff_hole_grammar.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/backoff_hole_grammar.py:9)-19、[同:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/backoff_hole_grammar.py:47)-50、[同:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/backoff_hole_grammar.py:80)-150、[同:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/backoff_hole_grammar.py:581)-742 に確立している。P1-b は S1 の D1357 exact comparator bytes もそのまま通せる。

## IR admission と renderer の実装

[sort_swo_oracle.py:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:494)-585 に、次の型と pure function 群を置く。

- `SortIrField`: `storage` / `key` / `pointer`
- `SortIrDirection`: `asc` / `desc`
- `SortComparatorIr`: 0〜3 個の相異なる `(field, direction)`。0 個だけが `const_false`
- `sort_ir_domain()`: `1 + 3*2 + 3P2*2² + 3P3*2³ = 79` 値
- `admit_sort_implementation(text)`: C++ 全文から型付き IR へ変換
- `render_sort_ir(ir)`: IR から正準 C++ statement を生成
- `trusted_relation_matrix(ir, corpus)`: trusted 行列を生成

文法は固定 envelope と次の expression だけを認める。

- `return false;`
- `a.f < b.f` または `b.f < a.f`
- `a.f != b.f ? cmp(f) : cmp(g)`
- 3 field の nested conditional
- field は `storage_` / `key_` / `rcdptr_`、各 field は一度だけ

判定順序は `input-type -> raw-size -> tokenize/resource -> envelope -> parameter-signature -> expression-shape -> field/direction -> duplicate-field -> eof` として固定する。各段に `sort-ir.<stage>.v1` の固定 rule ID と固定 reason を持たせ、候補文字列、token、位置、内部例外は結果や WAL に射影しない。これは [backoff_hole_grammar.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/backoff_hole_grammar.py:80)-150 と同じ規約である。

[check_materialized_sort_swo:2685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2685)-2700 は、marker 抽出後すぐ admission を行う。拒否は `OracleRejectKind.STRUCTURE` と固定 admission reason にする。admission 成功後に `render_sort_ir(ir)` を呼び、その renderer 出力だけを `_validate_single_sort_statement` へ渡す。候補 raw textを旧 validator へ渡してはならない。

[agent:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/coder-v4-autonomous-sort.md:58)-115 は、任意 C++ 合成の説明を上記 production の組合せへ変更する。出力 field は引き続き `implementation` の C++ テキストとし、JSON wire は追加しない。[agent:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/.claude/agents/coder-v4-autonomous-sort.md:139)-146 には D39 と別実験になることを明記する。

## pointer 意味論

trusted evaluator の `rcdptr_` 値は次の rank で決める。

- `pointer_kind == 0`: null、rank `0`
- `pointer_kind == 1`: `aliases[slot]`、rank `1 + slot`、slot 0〜3
- `pointer_kind == 2`: `separate[slot]`、rank `5 + slot`、slot 0〜5

根拠は実 TU の monotonic arena allocator [sort_swo_oracle.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:817)-827 と、`aliases = new Tuple[4]` の後に six `new Tuple()` を行う allocation 順 [同:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:1177)-1189、kind/slot を pointer へ解決する [同:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:1194)-1202 である。候補の `<` 生成は [s6_sort_sweep.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s6_sort_sweep.py:110)-129 と一致する。

これは portable C++ 全般の定理ではなく、contract-bound な現行 x86-64/compiler/TU 上の意味である。生死確認が 2 corpus × 3 order × 79 値で不一致 0、reversed rank で各 corpus 108 cell の不一致を実測済みなので、その命題を production 実装で再測する。

現行 `CORPUS_SHA256` は [sort_swo_oracle.py:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:679)-709 の element/tuple body serialization だけで、allocation 順を含まない。次を追加する。

- allocation sequence、kind/slot、rank 式を canonical JSON 化した `_POINTER_MAPPING`
- `POINTER_MAPPING_SHA256`
- `_ORACLE_CONTRACT_COMPONENTS["pointer_mapping_sha256"]`

evaluator はこの同じ `_POINTER_MAPPING` を参照する。実 TU の allocation 順だけが変わった場合も `TU_TEMPLATE_SHA256` が変わり、mapping だけが変わった場合も新 component が変わる。片側だけを変えた場合は実 TU / trusted 全件一致 test が落ちる。

## 関係行列の出所

compile / 実行は残す。[sort_swo_oracle.py:2754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2754)-2784 の trusted control と、[同:2786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2786)-2885 の候補 compile/run は維持する。

役割は次のように変える。

1. `trusted_relation_matrix(ir, corpus)` が権威行列を生成する。
2. `_run_matrix` [sort_swo_oracle.py:2122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2122)-2332 は、実型、実 ctor、実 allocator、broker、seccomp 上で候補 C++ の行列を観測する。
3. `_evaluate_executable` [同:2442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2442)-2483 は、各 corpus/order の実行行列を trusted 行列と byte exact で照合する。
4. `check_relation_matrix` [同:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:588)-626 へ渡すのは trusted 行列だけにする。

両者が食い違った場合は、どちらかを選んで続行せず `OracleRejectKind.MUTATION` と固定 reason `compiled-relation-differs-from-trusted-evaluator` で `REJECT` にする。実行行列を採用して PASS にする経路、trusted 行列だけを採用して不一致を無視する経路は、どちらも作らない。

trusted 行列自身が admitted IR の SWO invariant を破った場合は candidate rejection にせず、oracle implementation failure として `UNAVAILABLE` にする。79 IR は構造上 SWO なので、これは evaluator 故障の分類である。

## 契約 ID と campaign identity

[sort_swo_oracle.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:47)-51 は次のように更新する。

- `CONTRACT_VERSION`: 4 → 5
- `AXIOM_CHECKER_VERSION`: 3 → 4
- `GRAMMAR_VERSION`: 1 → 2
- `CORPUS_VERSION=2` と `PROTOCOL_VERSION=3` は不変
- `SORT_IR_GRAMMAR_VERSION=1` と component key `sort_ir_grammar_version` を追加

[_AXIOM_CHECKER_SOURCE_FUNCTIONS:2486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2486)-2500 へ admission、renderer、domain、trusted evaluator、pointer rank helper を列挙する。source digest の外へ判定ロジックを逃がさない。

[_ORACLE_CONTRACT_COMPONENTS:2546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2546)-2556 は schema を v3 にし、少なくとも以下を追加する。

- `sort_ir_grammar_version`
- `sort_ir_grammar_sha256`
- `pointer_mapping_sha256`

[ORACLE_CONTRACT_ID:2574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:2574)-2581 は、実装後に独立再計算した完全 digest へ更新する。推測値を手書きしない。

D345 により ID 変更は campaign identity を回転させる。[p3_s4_loop_sort.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop_sort.py:296)-303 と [s1_direct_comparison.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s1_direct_comparison.py:467)-478 が新 ID を `search_config` へ焼くため、導入前 campaign は新実装で再開できない。旧 v4 を current loader の legacy 扱いへ昇格させず、非 current として拒否する。

S8B portable receipt は [s8b_sort_swo_receipt.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:114)-130 と [同:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:159)-177 が新 current ID と boundary を要求する。旧 receipt は current として通さない。

## exact golden と ledger 波及

exact golden は次の 2 件を必ず更新する。

- [test_critic.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_critic.py:99)-103 の `_CURRENT_ORACLE_CONTRACT_ID_GOLDEN`
- [test_sort_swo_oracle.py:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:2055)-2059 の literal exact ID

[test_sort_swo_oracle.py:1962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:1962)-2031 の independent source bundle、components、schema、version tuple も production helperを使わず同じ新 ID を再構成するよう更新する。

[test_critic.py:1931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_critic.py:1931)-1940 の次の 2 param は golden 内容が nodeid に入るため nodeid 自体が変わる。

- current ID + `-suffix`
- current v5 の `sort-swo-v5` を `sort-swo-v4` に置換した値

したがって [acceptance_duration_ledger.json:6749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/acceptance_duration_ledger.json:6749)-6754 の旧展開済み key を、新しい exact nodeid と実測 duration へ置換する。新設する sort oracle test nodeid は [同:16657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/acceptance_duration_ledger.json:16657)-16725 の suite 部分へ反映する。

この suite は [update_acceptance_duration_ledger.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/tools/update_acceptance_duration_ledger.py:21)-30 で add-only 除外されている。値を合成せず、親の JUnit 実測から full ledger 更新を行い、[test_update_acceptance_duration_ledger.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_update_acceptance_duration_ledger.py:364)-388 の `test_critic.py` / `test_sort_swo_oracle.py` node 件数と exact set digest も同時更新する。

## guarantee boundary の更新

現行 boundary [sort_swo_oracle.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:89)-93 と module docstring [同:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:3)-16 は、「報告行列が真の関係であることを保証しない」という非保証を削除する。

新しい主張は、admitted IR、versioned corpus、contract-bound pointer mapping に限って、trusted evaluator が行列を生成し、実 TU の全観測行列との byte exact 一致を PASS 条件にする、という範囲に限定する。任意 C++ や corpus 外の全入力に対する SWO 証明とは書かない。

同じ旧非保証を持つ [s8b_sort_swo_receipt.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:1)-10、[同:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:140)-152、[同:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:224)-232 も更新する。[test_s8b_sort_swo_receipt.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_s8b_sort_swo_receipt.py:195)-204 は新しい限定保証の文言を固定する。

## 受理集合が狭まることの検査

[test_sort_swo_oracle.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:17)-20 に `coder_effect_gate` と `s6_sort_sweep` を import し、次の node を追加する。

- `test_sort_ir_domain_roundtrips_all_79_values`  
  79 値すべてについて `admit(render(ir)) == ir`、render bytes の一意性、domain size 79 を固定する。
- `test_all_79_rendered_ir_values_remain_inside_preexisting_gates`  
  全 render 値で `_validate_single_sort_statement(...) is None` かつ `scan_host_effects(...) == ()` を固定する。
- `test_sort_authority_15_is_byte_exact_subset_of_rendered_ir_domain`  
  [CANDIDATES:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s6_sort_sweep.py:144)-160 の 15 implementation が render 集合へ byte exact で含まれ、15 件であることを固定する。
- `test_public_oracle_rejects_non_ir_before_environment`  
  generic lambda、body call、未知 field、重複 field、追加 statement、JSON文字列を固定 admission reason で拒否し、environment/compile/evaluatorへ到達しないことを spy で固定する。
- `test_validate_single_sort_statement_is_renderer_postcondition_only`  
  whitespace差を持つ文法適合入力を admit し、旧 validator が候補 raw ではなく正準 renderer にだけ呼ばれることを固定する。
- `test_trusted_evaluator_matches_real_tu_for_all_79_ir_values`  
  79 値 × 2 corpus × 3 order × 324 cell の 153,576 cell を production renderer/evaluatorと実 TUで再測し、不一致 0 を要求する。
- `test_compiled_relation_mismatch_is_reject_not_pass`  
  `_run_matrix` の 1 cell を反転させ、trusted 行列と不一致なら exact `MUTATION` reason で `REJECT` になることを固定する。

既存 `_CLEAN_IMPL` [test_sort_swo_oracle.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:37)-40 は generic lambda から文法内の explicit `WriteElement<Tuple>` 正例へ変更する。低層 harness 用の generic/body comparator は `_evaluate_executable` の直接 fixture に限り残し、public oracle の正例としては使わない。

[test_sort_swo_oracle.py:1785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:1785)-1807 には `test_contract_digest_binds_sort_ir_grammar_and_pointer_mapping` を追加し、grammar version/mapping のどちらを変えても components digest が変わることを固定する。

## 変異事前登録候補

identity literal pin の失敗は観測 node に数えず、次だけを登録候補にする。

| 変異 | 落ちる機構固有 node |
|---|---|
| admission の duplicate-field 拒否を削除 | `test_public_oracle_rejects_non_ir_before_environment[duplicate-field]` |
| public flow の IR admission 呼出しを迂回 | `test_public_oracle_rejects_non_ir_before_environment[generic-lambda]` |
| renderer の asc/desc operand を反転 | `test_sort_ir_domain_roundtrips_all_79_values` |
| evaluator が `storage_` を signed 32bit と解釈 | `test_trusted_evaluator_matches_real_tu_for_all_79_ir_values` |
| pointer rank で aliases / separate の順序を反転 | `test_trusted_evaluator_matches_real_tu_for_all_79_ir_values` |
| `key_` を最初の NUL で切る | `test_trusted_evaluator_matches_real_tu_for_all_79_ir_values` |
| 実行行列との不一致チェックを削除、または実行行列を権威へ戻す | `test_compiled_relation_mismatch_is_reject_not_pass` |
| contract components から pointer mapping または grammar key を削除 | `test_contract_digest_binds_sort_ir_grammar_and_pointer_mapping` |
| `_validate_single_sort_statement` を候補 raw gate へ戻す | `test_validate_single_sort_statement_is_renderer_postcondition_only` |

`test_contract_manifest_hashes_and_literal_are_exact_snapshot` や `_CURRENT_ORACLE_CONTRACT_ID_GOLDEN` による失敗は、どの変異についても kill 根拠へ数えない。

## 実測手順

この plan 段では pytest、compile、実 TU 実行を行っていない。緑とは報告しない。

実装後は親が `tools/run_tests.py` 経由で、少なくとも以下を実測する。

- `test_sort_swo_oracle.py` の focus 走。受入全走から除外されるため別走必須
- `test_critic.py`
- `test_s8b_sort_swo_receipt.py`
- sort の P3/S1 呼出し境界
- ledger schema / exact node set test
- 79 値の実 TU 全件一致 node
- 機構固有 node を指定した変異走

## 総括

推奨設計: P1-b の C++ 全文文法 admissionを唯一の言語権威とし、trusted evaluator を行列の出所にする。実 TU は byte exact conformance 検査として残し、不一致は `REJECT`。

未解決の択一: 無し。JSON wire は S1 exact C++ binding と二重 ingress を作るため採らない。

新しい policy 選択が要る箇所: 無し。D1355、D1451、D1357、D344 の fail-closed 分類から導ける。