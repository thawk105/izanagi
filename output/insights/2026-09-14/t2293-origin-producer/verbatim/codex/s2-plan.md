## 総括

**実装位置は特定できるが、現 scope だけで完了判定を満たせるとは判断できない。** 先行する 2 本の生死確認には、静的に確認できる障害がある。

- 探索 runner が渡す `ExplorationCampaignLayout` を、証拠 producer の exact-type gate が拒否する。
- production の v2 provenance は content-addressed path に書かれ、brief が要求する `reports/execution-provenance.json` には書かれない。
- 33 件の証拠ができても、consumer が要求する sealed batch を作る production FSM は本 scope 外である。

したがって、親はまず生死確認を実施し、失敗なら brief どおり executor 本体を書く前に停止すべきである。以下は、障害と条件付き実装案を分けたプランである。**ファイル変更・テスト実行・commit は行っていない。**

参照を短くするため、以下では `A:4022` を「A の 4022 行」の意味で用いる。行番号は今回読んだ checkout のもの。

| 略記 | ファイル |
|---|---|
| A | [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/p3_autonomous_workload_trial.py) |
| E | [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/reflux_result_evidence.py) |
| C | [reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/reflux_formal_consumer.py) |
| L | [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/loop.py) |
| T | [reflux_origin_topology.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/reflux_origin_topology.py) |
| H | [p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/p3_s4_loop_trigger_gating.py) |
| P | [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/tests/test_p3_autonomous_workload_trial.py) |
| F | [reflux_origin_fixture_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/tests/reflux_origin_fixture_builder.py) |
| I | [test_reflux_campaign_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/tests/test_reflux_campaign_issuer.py) |
| D | [phase3-8c-wiring-design.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/docs/phase3-8c-wiring-design.md) |

## 実行順の設計

**分岐は `_run_workload` 内、executor 本体は別関数とする。**

1. **分岐位置は A:4021 の直後、A:4022 の直前。**  
   A:3951–3991 の exact runtime・run-scope seal・admission・capability 同一性・workload binding 検査を通し、A:3995–4021 の site、contract、shared build context、論理 cfg/perf の解決を済ませる。その後、origin runtime があれば新設 `_execute_origin_topology(...)` を呼び、その結果を `return` する。論理単一 layout を作る A:4022–4028、generation 状態を作る A:4029–4060、loop 本体 A:4062 に到達させない。

2. **本体は A:3938 の `_run_workload` 定義直前に新設する。**  
   origin 用の実行済み結果保持は `OriginTrialRuntime` の A:486–491 付近へ追加する。`campaign_runs` は計画として残し、実行済み結果と兼用しない。保持する値は少なくとも q、`summary.campaign_id`、`summary.layout_root`、回収 record の digest。外部 callback を executor 引数に加えず、既存 `drive` 注入からも実行経路を選ばせない。

3. **R1 の順序は維持する。**  
   cfg_q 導出 A:4895 → envelope 作成 A:4901 → create-only write A:4913 → read-back digest A:4920 → lifecycle start A:4942 → observation A:5087 → sealed scope A:5156 → workload、の順を変えない。executor 開始前にも同じ `origin/recovery-envelope.json` を読み、digest と canonical envelope が一致することを確認する。既存の照合仕様は C:393–415。

4. **各 q の順序を固定する。**

   - `run_plan.members` と `runtime.campaign_runs` がともに exact 33 件、q=0..32 順であることを検査する。
   - cfg_q の preimage・identity を再計算し、導出結果と envelope の planned identity に一致させる。既存導出検査は A:1311–1332。
   - 保持した `ReservationCheck.ensure_remaining` と supervisor の残時間を、**次の run を開始する前**に検査する。
   - `exploration_campaign_layout(identity_q, str(runtime.campaign_output_root))` → A:551 `_assert_fresh_campaign_state` → H:475 `_assert_resume_allowed`。
   - q の wire を実 source に適用する origin 専用物理 entry point → 本物の `run_campaign(..., result_evidence_context=ctx_q)`。
   - `CampaignSummary.campaign_id` と planned identity、`layout_root` と事前計算 root を照合する。summary の実値の生成位置は L:605–608。
   - record を disk から回収・検証してから次 q へ進む。

5. **完了時に全件を再照合する。**  
   q の順序、件数、actual identity/root の相異、planned identity との全件一致を要求する。単なる `zip` による短い側への切捨て、集合比較による順序喪失、plan から actual を作る処理を置かない。欠落・例外・予算不足を成功扱いせず、現在の失敗境界へ返す。tombstone の台帳遷移は scope 外である。

`ReservationCheck` は A:4840 の戻り値が現在捨てられているため、origin runtime に保持する配線が必要。ただし **各 q の保守的 `required_s` と margin の実在する供給元はない**。A:3027–3041 は trial 全体の `max_wall_s` しか受けない。374〜908 秒の観測値を、そのまま保守的上限と決めてはならない。

また、source 適用を伴う origin 専用 entry point は未存在である。既存 H:781–818 は template 適用、検疫・auditor veto、condition gate を経由する。この責務を単なる `run_campaign` 直呼びで脱落させないことが実装前提となる。

## ctx_q の構成

**現物の field 数は 15 ではなく 14 個**である。定義は E:240–254。15 個目は存在しない。

| field | q ごとの出所 |
|---|---|
| `origin_capability` | `runtime.capability`。発行は A:1739、runtime への保持は A:1786。 |
| `evidence_root` | `runtime.campaign_output_root`。production の設定元は A:4837 の `run_root`。envelope と物理 root と同じ基底を使い、`producer_inputs.evidence_root` へ戻らない。 |
| `batch_id` | 計画値は `run_plan.reserve_attempts[0].batch_id`（T:435–441）。**実際に予約・commit 済みの batch を選んだ結果は runtime にない。** これを予約済み事実として扱えない。retry 選択も推測しない。 |
| `query_ordinal` | `run_plan.members[q].query_ordinal`（T:150–151）。対応する `OriginCampaignRun.query_ordinal` と一致を確認する。 |
| `iteration_index` | `run_plan.members[q].iteration_index`。現在の topology は 0（T:400–402）。 |
| `replicate_ordinal` | 同 member の値。source は 0、source と同 mask の validation だけ 1（T:403–405）。 |
| `p6_plan` | `purpose=member.purpose`、`hypothesis_sha256=run_plan.hypothesis_sha256`、`validation_plan_sha256=run_plan.validation_plan_sha256`。T:264–265、406。元入力は A:452–453、envelope 配線は A:1394–1395。 |
| `trial_binding` | exact 3 key：`launch_admission_record_sha256=runtime.launch_admission_record_sha256`、`campaign_id=capability.campaign_id`、`workload=capability.trial_workload`。digest の生成は A:1782–1792、consumer の照合は C:778–799。registry binding 全体を `asdict` しない。 |
| `origin_binding` | capability から E:1070–1078 の exact 8 key を射影する。workload は `trial_workload` を `workload` key へ写す。 |
| `ordered_verifiers` | `producer_inputs.verifier_policy_bytes`（A:468）。C:1113–1130 と同じ canonical parse・capability digest 照合を通した `ordered_passes` の tuple。`("legacy","s2")` の直接埋込みを正本にしない。共通 leaf へ抽出する場合も現述語を維持する。 |
| `expected_record_path` | `member.evidence_path`（T:158）。E:959–968 の決定的 path と一致する必要があり、producer が E:1379–1385 で照合する。 |
| `env_tag` | `_run_workload` が解決した `contract.env_tag`（A:4002）。 |
| `attestation_mode` | 同じ `contract.attestation_mode`。E:1230–1243 の照合を維持する。 |
| `verified_calibration` | **現 runtime に保持値はない。** 実在する loader は L:186 の `env_attestation.load_verified_calibration(contract, repo_root)`。同 contract から executor 側でも取得して ctx に渡す配線が必要。required 時の `None` は E:1238–1243 が拒否する。 |

`batch_id` の計画値と実予約、calibration loader の存在と現在の配線を区別する必要がある。これらを fixture 値で埋めた正例を production 初期化の証明にはできない。

## run_campaign への引数

現在 `_run_workload` は直接 `run_campaign` を呼ばない。

`A:4361 _drive_s8c_generation` → `A:2352 drive(...)` → `H:1005 drive_iteration` → `H:734 _run_one_iteration_resolved` → `H:811 run_campaign` である。

| 引数 | origin executor で使う値・既存の出所 |
|---|---|
| `cfg_q` | `runtime.campaign_runs[q].campaign`。A:1271–1287 で論理 cfg に slot digest/q を加えて導出済み。 |
| `genomes` | `[Genome("silo", dict(_BASE))]`。既存は H:768。q ごとの違いは genome ではなく wire/binding/source に反映する。 |
| `perf` | A:4021 の `prepared.perf`。生成元 A:842–854、1234。 |
| `env_tag`, `clocks_per_us` | 同一 contract の属性。既存呼出し H:812。 |
| `numactl` | `list(contract.numactl)`。H:813。 |
| `authorization_contract` | `env_contract.authorize(contract.env_tag)`。H:815。 |
| `env_contract` | 既存は Pegasus compute のとき `contract` を追加（H:802–806）。その条件を踏襲する。issuer に届く authorized contract は L:531、834。 |
| `build_context` | trial の共有 instance。A:4822、5022、5183、4003。q ごとに作り直さない。 |
| `ccbench_dir` | `sub`。A:4369 → H:813。CLI 側の checkout は A:5472–5475。 |
| `cache_root` | `_run_workload` の引数。A:4372 → H:814。CLI の生成元は A:5473。 |
| `output_root` | **新たに明示する必要がある** `str(runtime.campaign_output_root)`。既存 H:811–820 は未指定で、L:350 の既定値を使っている。layout_q と同じ値を渡す。 |
| `declared_use_class` | `"exploration"`。H:102、817。official へ変更して型 gate を回避しない。 |
| `trigger_gate_binding` | `parse_wire(member.candidate_wire)` から mask を取り、`expected_predicate_sha256(mask)`、`new_nonce()`、`source=None` で構築。既存構築は H:769–775。実 source も同じ predicate にする。 |
| `result_evidence_context` | 上節の `ctx_q`。origin 分岐だけで渡す。 |
| `log` | 既存 H:739、813 の logger。 |
| `do_bench` | 既存 H:811 は省略し、L:350 の `True`。生死確認では `False` を明示して性能測定を避けられる。 |
| その他 | `dependency_prefix` は H:805–806 の非空時のみ。現在の A:2334–2361 は供給していない。`capability_resolver`、toolchain/fetchcontent 引数、holdout admission も A の通常呼出しには供給元がないため、既定値を維持する。 |

`run_campaign` に `do_build` 引数はない。`do_bench=False` でも build/verify は走る。`do_build=False` の trial から物理 executor を黙って起動する設計にはできない。

## 証拠の回収

**record の所在は envelope の `member.evidence_path` で知る。provenance の所在は record の ref で知る。**

- E:959–968 の record path は、evidence root 相対の  
  `reports/reflux-result-evidence/<origin_id>/<batch_id>/<q>.json`。
- `issue_campaign_result_evidence` は Path を返すが、L:335–344 の wrapper は返値を捨てる。L を変更せず、`ctx_q.expected_record_path` を使って回収できる。
- glob の辞書順を使わず、q=0..32 の member 順に読む。各 record の ordinal、batch、path を対応する member/context と照合する。
- symlink を追わない regular-file read は E:1421–1470 の既存処理を使う。必要なら E に小さい公開 loader を追加し、canonical parse と `result_evidence_relative_path(record) == member.evidence_path` を一緒に行う。
- executor 直後に読んだ raw digest を実行結果へ保持し、A:1840 `_complete_origin_runtime` でも disk を再読する。回収済み全 33 件との一致を確認して C:1364 へ渡す。caller bytes、fixture root、欠落時の代替値への fallback は置かない。

**fsync/read-back は必要だが、writer 側には実装済み。** E:1185、1025 が使う [reflux_origin_artifacts.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/campaign/reflux_origin_artifacts.py:224) は file fsync、同:244 は親 directory fsync、同:250 は read-back 一致検査を行う。reader が同じ内容を書き直す必要はない。

v2 provenance の実際の配置は E:1157–1171、1353–1364、1398–1401 の  
`<physical-root>/reports/reflux-result-evidence-content/v1/execution-provenance/<sha256>.json`。固定 basename の存在を production 発行の判定に使うことはできない。

## result_record_bytes の廃止

**`OriginProducerInputs` の field を削除し、formal consumer の bytes 引数は残す**のが最小差分である。consumer に渡す bytes の生成責任を production executor／disk loader へ移す。

直接参照は次のとおり。

| 区分 | 参照・変更対象 |
|---|---|
| production field | A:466。削除する。 |
| production 入力検査 | A:1689–1692。削除する。 |
| production forwarding | A:1882。実行済み結果に束縛した disk 回収値へ置換する。A:1883 の root も runtime 所有値にする。 |
| test constructor | P:10933–10937。caller bytes を渡さない構築へ移行する。 |
| test 中間値・replace | P:10995–11005、11015–11018。fixture evidence の注入を除く。 |
| test ledger helper | P:10703、10707。これは dataclass field ではなく helper のローカル引数。production が書いた raw bytes を受ける形で残せる。 |
| consumer 内部 | C:633、638、1376、1413。別 API の引数なので field 削除では壊れない。 |
| consumer 単体 test | `test_reflux_formal_consumer.py:350`、`:703`。同じく `OriginProducerInputs` を使わず、変更不要。 |

共通 helper `_origin_public_inputs` の変更が波及する test は、P の次の関数である。

- `test_registered_slot_is_reserved_before_first_performance_observation` — P:8996
- `test_origin_public_path_preserves_capability_identity_and_projects_terminal` — P:11053
- `test_origin_client_omission_is_typed_preflight_before_production_resolution` — P:11207
- `test_origin_producer_arm_must_match_issued_capability_and_closed_arm_set` — P:11233
- `test_origin_arguments_are_all_or_none_before_artifact_creation` — P:11270
- `test_origin_request_rejects_unregistered_exploratory_admission` — P:11290
- `test_origin_public_result_distinguishes_partial_from_completed` — P:11315
- `test_origin_envelope_create_failure_is_preflight_and_pre_observation` — P:11335
- `test_origin_post_lifecycle_observation_failure_returns_reported_partial` — P:11382

別ファイルでは、[test_reflux_originless_compatibility.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer/orchestrator/tests/test_reflux_originless_compatibility.py:134) の `_origin_enabled_bundle` と、それを使う同:1252 の比較 test に波及する。P:10520 の API 形検査には、当該 field 不在の検査を追加できる。

段階移行は、内部の連続した編集として「disk 回収を接続 → fixture 注入を撤去 → field 削除」とできる。ただし **旧 bytes への fallback を持つ互換期間は設けない**。既存正例の `complete` や `P6Unavailable` の期待値を反転して移行完了扱いにもしない。後述する completion／ledger の不足を解かなければ、公開正例の維持まで完了できない。

## fixture builder と凍結 baseline への影響

**共有 builder と凍結 baseline は変更不要。変更 entry はない。**

F:688–742 は synthetic WAL/provenance/record、F:745–784 はその fixture tree を生成する独立 fixture である。production executor の新設や caller field の削除は、その出力仕様を変更しない。baseline の 7 entry と、`test_reflux_result_evidence.py:36–39` の 4 literal を再生成する理由はない。brief の「24–27 行」は現 checkout では古い。

実際に campaign root、lock、固定名 provenance を作っているのは **共有 builder 本体ではなく P:10634 `_materialize_origin_physical_evidence`**。新しい正例ではこれを使わず、P:11009–11032 の materialize-before-complete 注入も使わない。

入力材料だけの fixture 使用は可能だが、P:10364 の `evidence_path` は凍結 origin ID を含む。そのまま新 capability に使わず、新しい test setup で実際の origin ID/batch/q に対応する path を **envelope 作成前**に用意する。共有 builder を変更する必要はない。

新規 test 関数の `acceptance_duration_ledger.json` 登録は、親が正本 producer で行う。今回の静的読解から duration を捏造して登録しない。

## 生死確認の最小 test

**本物の `run_campaign` を使う。runner、issuer、WAL、verifier を stub にしない。**

既存の参考は I:543 `test_real_run_campaign_issues_rejected_record_and_originless_is_inert`。これは実 build/verify/issuer を通す構成だが、I:433 が `"official"` のため、今回必要な探索 layout の正例にはなっていない。

新しい 2-run test は次の構成にする。

1. 新規の空 evidence/output root と、一つの論理 cfg、一つの slot digest を用意する。
2. A:1238 の本物の導出 helper で q=0,1 の cfg を作る。別 suffix や別 logical cfg で identity を分けない。
3. source mask を 0 にすれば q0 と q1 は同 wire になるため、ordinal による物理分離を強く検証できる。source はその wire の canonical predicate を持つ小さい buildable checkout とする。既存構成例は I:112–217。
4. 同じ root、同じ shared build context から、`declared_use_class="exploration"`、`do_bench=False`、各 ctx を渡して `run_campaign` を 2 回呼ぶ。
5. 異なる actual identity/root、各 run の一件の評価、lock、native WAL、record、record の ref が指す v2 provenance を確認する。plan と actual、build attempt、trigger binding を照合する。

stub／fixture の範囲は限定する。

| 対象 | 扱い |
|---|---|
| `run_campaign`、`pipeline.evaluate`、source identity、claim/lock、WAL、issuer、resolver | 本物のまま。 |
| build | I:112 のような小さい synthetic checkout を実際に build。 |
| trace の生成 | I:348–374 と同じく trace runner だけ差し替える。wrapper は本物の `_execute_verification_repetition` を呼び、typed `VerifyResult` を本物の verifier で作る。 |
| attestation 観測 | I:319–345 のように観測値だけ固定し、本物の receipt builder と照合を通す。 |
| authority／ledger 初期化 | fixture scope と明記する。これで本番 provisioning を名乗らない。 |
| toolchain 不在 | 実行不能として親へ返す。新しい skip で生死確認を成立させない。 |

**現コードでは、issuer 到達時に E:1213–1214 が探索 layout を拒否する。** そこだけ直しても E:447–448 に同じ exact-type gate がある。前段で別の失敗が起きる可能性もあるため、これは実走結果ではなく静的な到達障害である。

さらに、固定名 `reports/execution-provenance.json` の正例は現 writer では成立しない。期待値を密かに変更せず、親 brief の path 要件と production の content-addressed 配置のどちらを採るかを明示してから検証する。

2 本が成立した後の 33 本の integration test では、fixture builder の evidence tree を使わず、production 出力を consumer に渡す。ただし sealed batch の生成を test helper に任せるなら、名乗れる範囲は **fixture ledger 上の実行証拠連携**までである。

## 段 5 の所有分割

**親案の意味単位 A/B のままでは編集 path を素集合にできない。**

executor 側は A:475、4022、4840 を変更し、証拠移行側も A:462、1689、1840 を変更する。両者とも P の共通 fixture／公開正例に触れる。

path 排他を優先するなら、所有を次のように組み替える。

| 単位 | 排他所有 |
|---|---|
| A：supervisor と実行経路 | `p3_autonomous_workload_trial.py`、必要な origin 物理 entry point を置く `p3_s4_loop_trigger_gating.py`、`test_p3_autonomous_workload_trial.py`、`test_reflux_originless_compatibility.py` |
| B：証拠 leaf と検証機構 | `reflux_result_evidence.py`、共通 policy/loader 抽出が必要な場合の `reflux_formal_consumer.py`、`test_reflux_campaign_issuer.py`、対応する evidence/consumer test |
| 親の統合所有 | duration ledger の正本 producer 更新、検証結果の集約 |

この分割では、**caller field 削除と `_complete_origin_runtime` の移行も A が担当する**。B に同じファイルを編集させない。生死確認と必要な leaf の契約を先に確定する依存関係は残る。

L、`pipeline.py` は変更・変異登録の対象にせず、brief の他の変更禁止ファイルも維持する。

## 結線できない部分

| 未接続箇所 | 何がないため届かないか／根拠 |
|---|---|
| 探索 layout → issuer | L:451–452、542 は `ExplorationCampaignLayout` を生成する。E:1213 と447 は exact `CampaignLayout` のみ受理する。 |
| 固定名 provenance | E:1355–1364 は content-addressed ref を生成する。固定名 writer は P:10681–10683 の test helper にある。 |
| 予約済み batch の選択 | runtime の全 field A:475–491 に active batch／reservation receipt がない。T:435–448 は予約計画にすぎない。 |
| disk record → sealed batch | A:1859–1860 は台帳を読むだけ。C:668–682 は sealed member の evidence digest と record の一致を要求する。reserve〜seal を実行する現 test helper は P:10754–10804。 |
| 33 run の残時間保証 | A:4840 は preflight 戻り値を捨てる。各 q の保守的所要時間は `OriginRunPlanInput` A:449–458、runtime A:475–491 のどちらにもない。 |
| q の wire →実 source | T:154 は wire を保持するだけ。既存の source 適用は H:781–797。origin 用 entry point と、その経路で既存の検疫・mandatory veto を維持する入力配線がない。planner/auditor の出所を架空値で補えない。 |
| required attestation → ctx | verified calibration は L:186 のローカル値で、summary が返すのは receipt（L:605–608）。executor への loader 配線が必要。optional 契約では L:184–198 が receipt を作らず、E:1245–1253 の必須照合を満たせない。 |
| production CLI → origin | A:5475–5498 は origin 引数なしの `run_trial`。fixture real build は A:5408–5410 が拒否し、no-build は A:5458–5461。 |
| generation metadata → origin 実行 | A:1520 は manifest の generations と一致を要求する。物理本数を33へ読み替えられない。D:811–813 は「2 は admission metadata」と明記する。 |
| origin 実行 → completion/report | A:3051 は単数 `campaign_root` 必須。A:3772–3777 は positive cell admission、A:3902–3927 は既存 completeness／Layer-3 chain を要求する。R2・要件18を除外したまま公開 `complete` を保証できない。 |
| P6 判定そのもの | C:3–8 に記された未実装境界で、現 consumer の到達上限は C:1480 の `P6Unavailable`。 |
| 本番 authority、FSM、renderer、33 本の実測 | 本 wave の scope 外。D:572–586、645–647、903–904 と親 brief の名乗り上限を維持する。 |

## 親 brief への反論

1. **「欠けているのは executor だけ」は不十分。**  
   探索 layout の exact-type 不整合があり、単なる ctx 配線では issuer が動かない。修正候補は E:447、1213 での探索 layout の明示対応だが、これは producer の受理型集合を変えるため、現 brief に黙って含めず、**scope 外の前提修正候補**として返す。

2. **生死確認の固定 path は現 production 契約と一致しない。**  
   production writer が書く ref 先を検証する要件への明示的訂正、または固定名 writer の追加方針が必要。test の期待値だけ変えて解消扱いにしない。

3. **「production 証拠だけで P6Unavailable」と「ledger FSM は scope 外」は、production 全経路の完了条件として両立しない。**  
   fixture ledger の遷移を許せば evidence producer→consumer の integration test は設計できる。production 台帳まで含む完了を意味するなら追加 scope が必要である。

4. **既存 test の偽装位置を訂正する必要がある。**  
   P:11085–11089 の `_run_workload` monkeypatch は本物へ委譲する観測 wrapper。物理 evidence の後付けは P:11009–11032、campaign root の生成は P:10634–10696 である。

5. **ctx は14 fieldであり、必要な値も全部は配線されていない。**  
   active batch、per-q 時間上限、verified calibration の保持が欠ける。「API が実在する」ことと「executor が使える実値がある」ことは別である。

発行3条件0/3、本番 authority0件、certified 選択・材料レポート・台帳の現在値を進めたとは扱わない。今回返せるのは、以上の静的な実装配置案と、先に解くべき接続障害である。