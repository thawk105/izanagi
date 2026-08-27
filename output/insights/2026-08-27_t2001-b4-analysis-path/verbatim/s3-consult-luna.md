## 前提の確認

次の射影資料をすべて全文読めた。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-decisions.md`

repo は read-only で静的に調査した。書込み、pytest、build、Web 検索は実行していない。以下で「緑」とは報告しない。

## 所見

### F1. P2 の schema は、現時点では正式実走に対する到達不能な述語である

- **重大度:** blocker
- **対象:** [s1-brief.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md:98)、[s2-plan.md:219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:219)、[s2-plan.md:693](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:693)
- **根拠:** 現存 producer と到達値は次のとおり。

|入力|実 producer と値域|正式 B-4 入力への到達性|
|---|---|---|
|`whiteboard_result`|checkpoint writer は [p3_s4_loop.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:724)。静的値域は `success/fail/rejected` [同:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:735)。現存 3 checkpoint の実測は計7行すべて `success`、`delta_pct=null`。例は [loop_state.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json:5)。|到達可能。ただし block status ではない。|
|terminal、candidate throughput|WAL の wire field は `variant/stage/env_tag/ts/payload` [model.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/model.py:98)。bench 省略 COMMIT は `fitness_tps=None` [pipeline.py:1468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1468)、bench COMMIT は数値 [同:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/pipeline.py:1532)。現存 WAL の非 null COMMIT は426件、実測範囲 `274871.5` から `8493333.0`。端点は [sort WAL:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:6)、[S1 WAL:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2/runs/wal.jsonl:91)。|一部到達可能。祖先 reference の TPS ではない。|
|`execution_disposition`|永続 field はない。in-memory outcome は `rejected/certified/aborted/dry-pass` [p3_s4_loop.py:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1087)、commit duplicate は `duplicate` [同:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1048)、入口停止は `stopped-before` [同:1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_s4_loop.py:1519)。crash と terminal 不在は return されない。|durable artifact からは到達不能。|
|arm、campaign、model/prompt/projection、WAL/checkpoint hash|closed critic terminal receipt の writer に実在する [p3_b4_closed_critic.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_closed_critic.py:951)。live WAL/checkpoint との再照合もある [同:1713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_closed_critic.py:1713)。|利用可能だが、計画の raw exact key set は campaign、model、prompt、projection、WAL path/hash を受け取らない。|
|`treatment_fired`、B-4 `contaminated`、`protocol_ok`、`precursor_hash`、reference 2 hash、slot 順|該当する durable producer はない。|到達不能。|
|B-4 `block_id`、registry、manifest、seed receipt、contract binding|計画が新設する in-memory 型以外に authority producer はない。|現在は到達不能。|

`execution_disposition` などを必須化して欠落を拒否すること自体は、将来 producer の手前に置く負の関門としては正当である。しかし実成果物が必ず拒否される現状では、これは「raw な試行記録から入力型を作る経路」ではない。P2 は placeholder としてのみ成立し、S2 または §6 前提条件9の充足には数えられない。

- **成果物影響:** 現存する正式 artifact はすべて adapter で拒否され、B-4 verdict、certified 選択、全件報告を生成できない。
- **反証されうる形:** 現存 producer の file:line と実 artifact path を示し、raw exact key 全件が推定や手入力なしで生成され、その artifact が同じ public adapter を通ることを実測できれば反証される。

### F2. `evaluate_b4_artifacts()` は artifact-to-verdict ではなく、自己申告 mapping-to-verdict である

- **重大度:** blocker
- **対象:** [s2-plan.md:262](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:262)、[s2-plan.md:593](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:593)
- **根拠:** integration API は registry と manifest だけを bytes で受け、arm 記録は `raw_analysis_records: object` として受ける [s2-plan.md:601](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:601)。各 arm の `source_artifact_sha256` は path、artifact kind、issuer、raw bytes のいずれにも束縛されない [同:273](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:273)。したがって64桁文字列と整合する mapping を caller が同時に作ればよい。

  repo の formal consumer idiom はこれと異なる。実 raw bytes の sha256 を ledger member と一対一対応させ、余分な record も拒否する [reflux_formal_consumer.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/reflux_formal_consumer.py:466)。さらに `evidence_root` 下の実 artifact を解決する [同:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/reflux_formal_consumer.py:665)。この実在照合 idiom が計画にない。

- **成果物影響:** 将来 producer ができても、偽の `protocol_ok=True`、`contaminated=False`、TPS、hash を自己整合させた入力から成立 verdict を作れる。
- **反証されうる形:** integration API が raw artifact path/bytes と issuer-bound receipt を受け、各 hash を再計算し、WAL/checkpoint/closed critic receipt/manifest との一対一対応を検証する実コードを示せば反証される。

### F3. scheduled registry の「全件性」は caller が渡す同じ集合に相対化され、file-drawer を閉じない

- **重大度:** blocker
- **対象:** [s2-plan.md:486](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:486)、[s2-plan.md:538](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:538)、[s2-plan.md:696](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:696)
- **根拠:** `assert_scheduled_registry_complete()` は権威ある schedule artifact ではなく、caller の `scheduled_inputs` と caller の registry を比較する。計画自身も「権威ある scheduled attempt 全列」の producer 不在を認めている [s2-plan.md:697](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:697)。成功した201件だけを両方へ渡せば、比較は成立しうる。

  同様に `assert_manifest_unchanged_before_run(frozen_manifest_bytes, observed_manifest_bytes)` は2つとも caller 引数であり [同:524](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:524)、どちらが実走前 bytes だったかを証明しない。seed の一様性・事前性を証明する producer も不在と明記されている [同:558](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:558)。

- **成果物影響:** 不都合な attempt を schedule と registry の両方から落とす経路、および結果閲覧後に seed/manifest を選ぶ経路が残り、母集合と p 値を変更できる。
- **反証されうる形:** 最初の実走より前に発行・commit された issuer-bound schedule/seed/manifest receipt を起点とし、完全性検査が caller sequence を受けずその receipt から全 attempt を再導出すれば反証される。

### F4. prereg consumer は A の literal しか照合せず、C/D の実装と §5.1.1 の一致を検査できない

- **重大度:** blocker
- **対象:** [s2-plan.md:340](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:340)、[s2-plan.md:398](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:398)
- **根拠:** public API が受ける source は `contract_source_bytes` だけである [s2-plan.md:354](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:354)。AST 検査対象も contract module の定数と enum に限定される [同:400](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:400)。

  一方、次は C または D の責務で、consumer の照合対象に入っていない。

  - precursor の5適格条件
  - registry append 順、同着順、先頭201件
  - 201件未満の `design_not_feasible`
  - manifest exact 再生成
  - schedule 導出と遵守
  - artifact から violation count を導く順序
  - adapter/registry/manifest を verdict へ接続する D の呼出順

  さらに body の空白・強調・段落を正規化し「ラベル付き literal」だけを読む [s2-plan.md:388](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:388) ため、literal を残したまま「先頭 n」を「末尾 n」へ変えるような意味変更を検出できない。

- **成果物影響:** manifest 選択、file-drawer、schedule、artifact 接続が文面と異なっても一致 consumer が成功し、異なる母集合からレポートを作れる。
- **反証されうる形:** C の選択関数を「末尾201件」、D の violation count 導出を adapter 後へ変えた mutation が、A とテストを変更せず repository consumer 単体で拒否されれば反証される。

### F5. 新設5 module には sanctioned caller、artifact writer、source-closure receipt がない

- **重大度:** blocker
- **対象:** [s2-plan.md:649](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:649)、[s1-brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md:52)
- **根拠:** 所有対象は5 production file と5 test fileだけで、既存 launcher、driver、report、certified selector を1つも編集しない [s2-plan.md:655](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:655)。`evaluate_b4_artifacts()` に sanctioned CLI や production caller は計画されていない。

  また C の public API には registry loader はあるが、D が要求する manifest の strict loader、canonical serializer、artifact writer がない [s2-plan.md:448](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:448)。primary outcome 欄へ書ける transitive source closure の path/sha256 も生成しない。

- **成果物影響:** この wave 単独では certified 選択、実レポート、永続台帳の bytes は1 bit も変わらず、§6 前提条件9も充足しない。
- **反証されうる形:** sanctioned entrypoint から実 artifact loader、integration、canonical writer、report/selector までの production caller 鎖と、その exact caller inventory を示せば反証される。

### F6. append-only 順序規則と単件 append API が両立しない

- **重大度:** must-fix
- **対象:** [s2-plan.md:472](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:472)、[s2-plan.md:540](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:540)
- **根拠:** canonical 順序は physical append order としつつ、「同じ schedule batch ordinal は append 前に attempt id 辞書順」としている。しかし公開 API は `append_scheduled_attempt(... attempt)` の単件 append だけである。`b` を先に append した後で同着の `a` が来ても、append-only prefix を維持したまま辞書順へ戻せない。
- **成果物影響:** 同じ予定集合でも caller の到着順により先頭201件と manifest sha256 が変わり、分析対象が変わる。
- **反証されうる形:** batch 全体を一括受領して sort 後に seal する API、または append 時に同着逆順を拒否する契約を示し、全 permutation から同一 bytes を得れば反証される。

### F7. file 所有は素集合だが、意味上の依存グラフは A → B/C → D でも足りない

- **重大度:** must-fix
- **対象:** [s2-plan.md:649](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:649)
- **根拠:** path は実際に素集合で、共有 conftest、共有 fixture、共有 helper の編集も計画されていない。しかし完全な S3 consumer は F4 のとおり C と D を検査する必要があるため、B を C と並列に完了させられない。さらに C の「binding receipt」は配置予定にしか現れず [s2-plan.md:440](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:440)、公開生成 API がない。D はその代わり caller の `ContractBinding` を受ける。
- **成果物影響:** B と C が個別に成功しても、文面と ledger/schedule の一致や authoritative binding が成立した証拠にならない。
- **反証されうる形:** B consumer が C/D の実 source closure を入力に持ち、C/D mutation を拒否する形へ依存を `A → B/C → D → consumer` と固定すれば反証される。

### F8. D75 の同名二義と、親の実測1の事実誤認がある

- **重大度:** must-fix
- **対象:** [s1-brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md:20)、[s2-plan.md:464](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:464)
- **根拠:**
  - 親は `design_not_feasible` が Python/JSON に0件と断言するが、T-139 は既に同じ verdict を返す [stress_check_simulation.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:630)。`SimulationResult.verdict` も既存 wire field である [同:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:64)。
  - 計画の `class Arm(Enum)` と同名の `Arm = Literal["on", "off"]` が B-4 closed critic に既にある [p3_b4_closed_critic.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_closed_critic.py:70)。
- **成果物影響:** schema namespace を伴わない `design_not_feasible` を report/automation が T-139 と B-4 のどちらとして扱うか曖昧になり、異なる Arm 型の取り違えも起こる。
- **反証されうる形:** B-4 型を `B4DesignNotFeasible`、`B4AnalysisArm` などへ分離し、wire 値には schema version を必須化すれば反証される。

### F9. 焦点走の一覧閉包に4 node の列挙漏れがある

- **重大度:** nit
- **対象:** [s2-plan.md:719](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md:719)
- **根拠:** 詳細は次節の差分表。主な漏れは repository scan fixture を共有する2 node、新 test file を列挙する2 node である。
- **成果物影響:** 直接の成果物影響はない。初回焦点走と後続受入の検査集合が一致しない診断上の nit である。
- **反証されうる形:** 下記4 node を焦点走へ追加するか、各 node が新 file を列挙しないことをコードで示せば反証される。

### F10. 稼働 wave の「全 path 比較」は t1840 について未証明である

- **重大度:** must-fix
- **対象:** [s1-brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md:46)
- **根拠:** `t1769` の unique commit `5327d823f` は production/test の2 pathだけでなく、dogfood JSON と sidecar 6 pathも編集している。全8 pathとも本計画の10 pathとは直接重ならないので、結論自体は変わらない。

  `t1840` は調査時点で worktree clean、main に対する unique commit 0件だった。射影資料が示す既知 path は3 driver、事前登録 doc、名前未提示の新 launcher だけであり、新 launcher と test path の exact 所有一覧はない。したがって、現在の差分が0件であることは確認できても、将来編集面との「1件も重ならない」は独立証明できない。

- **成果物影響:** t1840 が raw producer、launcher、test helper を後から同名 path へ置いた場合、merge 衝突または二重 producer が初めて land 時に発覚する。
- **反証されうる形:** t1840 の production/test/helper/doc を含む exact path ownership manifest が提示され、本計画の10 pathとの積集合が空なら反証される。

## 一覧検査の閉包 (独立確認)

|母集合・検査|独立確認|プランとの差分|
|---|---|---|
|repo tracked/untracked source と docs の一括 parse/import 規則 [test_campaign_import_invariant.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_campaign_import_invariant.py:1001)|新 production 5 file は自動的に parse され、campaign import shape を検査される。|プランの3 nodeに加え、`test_repository_scan_set_is_nonempty_and_contains_sentinels` と `test_real_current_docs_have_no_legacy_module_command` も同じ session fixture を使うため追加。|
|production AST caller census|`test_campaign.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_ccbench_spawn_sites.py`、`test_p3_s4_loop.py`、`test_pegasus_dispatch_compute.py`、`test_t1286_commit_receipt.py`、`test_t338_submission_gate_unit5.py` を確認。|プラン列挙と一致。なお build-authority の母集合は `git ls-files` [test_p3_build_authority_cli.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_build_authority_cli.py:194) なので、untracked のままの初回走では新 file を含まない。|
|production 内容 scan|login headroom、subprocess bytecode、reflux golden、S1 golden、S8B build/floor/manifest/report/freeze、stage6 candidate、Pegasus policy、official perf、holdout repo scan を確認。|プラン列挙と一致。holdout scan は production だけでなく repo 全体を読む [s8b_holdout_freeze.py:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/s8b_holdout_freeze.py:591) ため、新 test fixture に三軸 holdout 実値を同居させても赤になる。|
|campaign module exact 集合|driver と判断された module のみ `_DRIVER_CONTRACTS` exact 集合に入る [test_p3_exploration_namespace.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_exploration_namespace.py:123)。|新5 module が campaign root creator 形を持たなければ plan どおり対象外。無条件の全 campaign module exact 集合や `__init__.py` export pin は見つからなかった。|
|新 `test_*.py` の file census|self-runner 検査は実在し、`pytest.main` は受理 signal である [test_plain_runner_coverage.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_plain_runner_coverage.py:25)。acceptance ledger coverage も全 collection を再列挙する [test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_acceptance_schedule_order.py:660)。|プランの2 nodeに加え、`test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` と `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` [test_pytest_collection_config.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_pytest_collection_config.py:423) が新 test file を列挙する。|
|docs 側 module 一覧|living docs の集合には B-4 doc がある [check_docs.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/tools/check_docs.py:146)。|新 campaign module 名を exact 集合で要求する docs 一覧は見つからなかった。|

焦点走へ追加すべき差分は次の4 nodeである。

- `orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command`
- `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

## 親 brief への所見

### 実測1〜7

- **実測1は誤り。** `design_not_feasible` は既存 T-139 Python に多数実在する。残る3語が現行 Python/JSON にないことは確認した。
- **実測2は主要部分を確認。** `reference_tps` は既存関数の引数にあるだけで、B-4 reference resolver ではない。ただし B-4 内にも既存 `Arm` 型があり、同名確認が不足していた。
- **実測3は確認。** static 値域は3値、現存 checkpoint の実測値は `success` のみ。throughput は whiteboard にない。
- **実測4、5は確認。** admission verifier は値セルの意味を検査しない [p3_b4_admission_record.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_admission_record.py:18)。B-4 doc は living で、B-4 source closure の frozen manifest はない。
- **実測6は確認。** ただし再利用判断は下表のとおり。
- **実測7は直接 path に限れば確認。** t1769 の全8 pathと本計画の10 pathは素集合。t1840 は現在差分0件だが、未来の新 launcher/test path が未提示なので全 path 比較は未完了。

### 既存機構との重複

|既存機構|判定|
|---|---|
|`attempt_registry_core`|full state machine を使わない判断は正当。core event は6種に閉じ [attempt_registry_core.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:35)、未知 event を拒否する [同:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/attempt_registry_core.py:741)。B-4 の global violation は attempt lifecycle と同型でない。`canonical_json_bytes` と `chained_event_row` の再利用は純減。ただし durability、strict JSONL、prefix authority まで再実装する理由は別途必要。|
|`_regularized_beta` / `_clopper_pearson_upper`|重複は正当。module は top-level で NumPy を import する [stress_check_simulation.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:26)。既存 CP は `DELTA_MC/CELL_COUNT` の片側上限 [同:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/preregistration/stress_check_simulation.py:415) で、B-4 の両側95%契約と異なる。|
|`observe_relative`|P4を支持する。既存関数は `floor=0` を拒否し、subject を reference の乗法境界と比較する片側 bit [contract.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/qualification/contract.py:332)。B-4 の `abs(on-off)/precursor_reference <= floor` と同値ではない。|
|`reflux_formal_consumer`|直接流用する型契約ではないが、実 artifact bytes、path、ledger、receipt、source closure を結ぶ idiom は流用すべき。計画はこの部分を落としているため純減になっていない。|

### P1〜P4

- **P1:** doc を今編集しない判断は維持できる。t1840 の同 file 編集と衝突し、かつ本計画後も§6.9は未充足だからである。ただし「第三者が充足を検証できる」状態にはならない。既存 admission verifierも§6.9を検査しない。
- **P2:** 正式 path の実装としては反証された。欠落時 fail-closed は正しいが、到達不能 field を必須化した placeholder を S2 完了と呼べない。
- **P3:** 反証された。日本語 parse の脆さより重い問題は、literal が同じままの意味変更と、C/D の実装変更を検出できないことである。凍結対象の §5.1.1 だけを別途 exact hash で束縛する方が明確である。
- **P4:** 支持する。`observe_relative` の合成では境界、分母、`floor=0` の契約を同時に満たせない。

### P1 後の path と sha256

現計画には、primary outcome 欄へ1つの path/sha256 として書ける安定した closure artifact がない。単独の `p3_b4_analysis_path.py` の sha256だけでは、contract、adapter、ledger、consumer、doc §5.1.1 を束縛しない。

必要なのは少なくとも次の repo-relative path と sha256 を canonical に列挙する closure receipt である。

- `p3_b4_analysis_contract.py`
- `p3_b4_analysis_adapter.py`
- `p3_b4_analysis_ledgers.py`
- `p3_b4_analysis_path.py`
- `p3_b4_analysis_prereg_consumer.py`
- 事前登録 §5.1.1 の exact section bytes
- schema version、source commit、consumer 実行結果

計画された registry/manifest は明示入力からは決定的にできる余地があるが、manifest serializer、artifact path、writer、seed authority が未定義なので、再生成時の byte 安定性はまだ立証できない。

## 裁定パッケージ候補

1. **この wave の完了意味**

   推奨は「純関数と schema の component wave」に縮退し、S2、S4、S5、§6.9を未充足のまま明記すること。正式実走 path まで要求するなら、現 scope は blocker である。

2. **raw producer の所有**

   `execution_disposition`、slot 順、treatment、contamination、protocol、precursor、reference を誰がどの artifact から導くかを exact path 付きで裁定する。t1840 へ暗黙に広げず、launcher land 後の専用 producer/consumer waveを推奨する。

3. **schedule と registry の authority**

   scheduled attempt 全列、seed、pre-run manifest の issuer、commit 時点、durable writer、lock/fsync、pre-run prefix と final registry の二段 sealを決める。caller の `scheduled_inputs` は authority にしない。

4. **prereg consumer の方式**

   §5.1.1 の隔離した exact section hashと、A/C/D の source closure、behavior mutationを組み合わせる案を推奨する。正規化日本語 literal parserだけでは採らない。

5. **成果物 closure と doc 更新**

   t1840 land 後に専用 doc waveを置き、analysis source closure receipt の path/sha256を primary outcome 欄へ記入する。それまではP1どおりdocを編集せず、§6.9未充足を維持する。

6. **scope 外の実効層**

   正式 producer、artifact resolver、永続 writer、pre-run authority、certified selector caller、全件 report generator、Holm family report、§5記入と admission record commitはすべて本計画の外である。未実装のまま残すなら、各層を後続 task として明示する。

## 総括

blocker は **5件**、must-fix は **4件**、nit は **1件**である。  
最も重いのは F3 の「registry 完全性が caller 自身の予定集合に相対化される」点で、file-drawer を閉じない。  
P2 は安全な拒否 placeholder ではあるが、正式 artifact から到達できる adapter ではない。  
P3 consumer は A の literal しか見ず、ledger・schedule・integration の一致を保証しない。  
既知 path の直接重複はないが、t1840 の未来の exact path は未提示で、producer 依存も未解決である。  
P4 と、既存 CP/full registry state machine を直接流用しない判断は支持する。