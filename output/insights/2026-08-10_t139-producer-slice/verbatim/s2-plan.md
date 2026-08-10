# 実装プラン案

指定された必須資料はすべて読めた。`orchestrator/qualification/` についても、指定されたファイルに加えて `__init__.py` と `retry_index.py` を含む全ファイルを確認した。

本回答は静的読解によるプランだけであり、コード変更・pytest・build・qsub は実行していない。したがってテストが緑とは主張しない。

## 実装前に解消する硬いゲート

### N1 — approval manifest と `approval_fold_commit` の循環

同じ commit に、その commit 自身の SHA を literal として含む manifest は作れない。親 brief P5 を文字どおり「本 producer wave の land fold と同時に作る」と実装してはならない。

次の二段階にする。

1. 先行する docs-only activation wave

   `docs/spool/decisions/2026-08-09-dev-wave-t139-stage2-approval-1.md:1-55` を新設し、§51 が承認した exact payload を canonical JSON fence として decision fragment に収める。land/fold によって初めて `F_e` を得る。この payload 自体には `F_e` を書かない。

2. `F_e` の子孫で producer wave を実装

   `docs/approvals/t139-stage2-v1.json:1-70` を新設し、前段 payload、payload digest、literal な `approval_fold_commit=F_e` を収める。resolver はさらに、`F_e` 時点の `docs/decisions.md` に payload がちょうど一度あり、`F_e` の親には無いことを Git blob から検査する。JSON file の自己申告だけは信頼しない。

先行 fold が無い状態では real-repo resolver を必ず fail-closed にする。hermetic 正例は「approval payload を加えた commit `F_e` → manifest を加えた子 commit」の二 commit を合成して作る。

Manifest の `approval_payload.approved_blobs` は次の exact 4 件とする。

| role | commit | SHA-256 |
|---|---|---|
| `addendum_a` | `622bd786191d40bda388596fa2adbf119ee84c9a` | `f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec` |
| `derivation_map` | `7ec088163dee920f0b8e1e9783faa6e36b22b730` | `bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025` |
| `erratum` | `1d235e0e455020cf54e66cf83304961910c369d8` | `a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3` |
| `record_items` | `1d235e0e455020cf54e66cf83304961910c369d8` | `1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3` |

Manifest はさらに次を固定する。

- target core: `88d68f9127b31df5aafc3d59607896626a1652e8`、canonical path、SHA-256 `ac939a…60e9`
- `erratum_application_order`: 配列。現在は 1 件だが、実装に `len == 1` は置かない
- 全 erratum 適用後の `composed_sha256`: `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82`
- manifest と全 nested object の exact key

### N2 — 追補 A を名乗る blob が二つある

旧版の SHA-256 は `1f561258…46bdd`、承認済み再発行版は `f7db96ce…8cfec` である。resolver は caller の `core_ref` 一致だけを見ず、`addendum_a` の path・commit・SHA-256 が manifest の承認値と完全一致することを要求する。これにより、同じ `core_ref` を本文に持つ旧版は必ず拒否される。

### 記録項目と追補 A の未解決な衝突

次の二要求は、そのままでは同時充足できない。

- `record-items.md:130-132`: `post_performance_failure` は marker または性能 run の raw 痕跡を要求
- `addendum-a-reissue.md:266-280`: preflight の最初の a03 観測不成立も、marker 作成前かつ run 0 件のまま `post_performance_failure` へ写す

推奨は、`post_performance_failure` の第三分岐として「a03 failure evidence と対応する `environment_observations[]`」を認めること。ただしこれは record-items の literal 条件追加なので、schema digest を固定する前に裁定が要る。黙って marker を先に作る案は追補 A の順序違反、`pre_performance_infra_failure` へ写す案は a04 違反なので採らない。

## 公開 API

公開署名は §15 の表記を逐語で維持する。

```text
resolve_effective_preregistration(
    repository_root, *,
    core_ref     = (commit, path, sha256),
    addendum_a   = (commit, path, sha256),
    addendum_b   = (commit, path, sha256) | None,
) -> PreregBinding        # measurement_head は repository_root の実 checkout から導出して binding に含める

submit_pilot(*, binding: PreregBinding) -> submission_id

verify_receipt(*, binding: PreregBinding, receipt) -> None
```

- `measurement_head` を公開・内部 helper の caller 引数にも置かない。
- `submit_main` は追補 B が無い本 slice の scope 外。stub も作らない。
- `PreregBinding` は `init=False`、module-private seal 付きの immutable capability とし、通常の dataclass constructor から生成できないようにする。
- binding は core/A/B、ordered errata、approval fold、manifest、schema、producer protocol、`measurement_head`、repository root identity を保持する。
- sink の署名は次とする。

```python
def publish_raw_receipt(
    receipt,
    *,
    binding: PreregBinding,
) -> Path:
```

出力先と intent ledger は binding・`series_id` から canonical path を導出する。呼び手だけでなく、永続化関数自身が keyword-only binding を要求し、同一 byte buffer を `verify_receipt` と ledger coverage 検査へ渡した後にだけ publish する。

## 単位 A — 参照束縛層

新規ファイルの line は予定レイアウトであり、実装後は関数アンカーを正とする。

| path:line | 変更内容 |
|---|---|
| `docs/approvals/t139-stage2-v1.json:1-70` | `F_e` の子孫で作る one-off manifest。exact 4 blobs、ordered errata、composed digest、approval payload digest を固定 |
| `orchestrator/qualification/t139_contract.py:1-210` | canonical path/digest、`BlobRef`、`ErratumRef`、opaque `PreregBinding`、schema/protocol digest literal、binding seal |
| `orchestrator/qualification/t139_preregistration.py:1-520` | manifest reader、追補 envelope parser、erratum parser/applicator、公開 resolver |
| `orchestrator/campaign/trial_registry.py:787-812` | `_blob_at_commit()` の直後に public `read_committed_regular_blob(...)` を追加。private helper を T-139 から直接 import しない |
| `orchestrator/qualification/__init__.py:20` | 現在の `.contract` import block の直後に `PreregBinding` と `resolve_effective_preregistration` を import |
| `orchestrator/qualification/__init__.py:33` | 現在の `__all__` 終端直前に上記二名を追加 |
| `orchestrator/tests/test_t139_preregistration.py:1-720` | hermetic Git、parser、manifest、erratum、ancestry、N1/N2 の検査 |

### 追補 A envelope parser

`t139_preregistration.py:150-225` に次の byte grammar を実装する。

1. UTF-8/LF を正規化せず、Git blob の exact bytes を行末込みで分割する。
2. exact line `b"## fields\n"` が一つだけ存在することを要求する。
3. field 範囲はその次の行から、次に exact prefix `b"## "` を持つ行の直前まで。終端見出しが無い場合も失敗。
4. 範囲内で exact prefix `b"### "` を持つ各行について、直後の最初の ASCII whitespace までを key とする。
5. key は `a[0-9]{2}`、重複なし、最終期待集合 `{a01,…,a13}` と完全一致。
6. metadata fence、`core_ref` fence、fields 範囲は別々に解析する。metadata や disclaimer に現れる `aNN` は field と数えない。
7. 文書全体を grep/regex scan して `aNN` を集める実装は禁止する。

### Erratum resolver

`t139_preregistration.py:227-390` は次を行う。

- §3 の唯一の YAML fence を exact shape で解析する。operation は `index`、`locator`、`old_sha256`、`old_text`、`new_text` の exact object。
- 現 erratum 自体については operation 数 `== 2`。
- 各 locator の対象行を LF 込みで hash し、次と一致させる。

  - `6e87b981…5681e`
  - `b5e2c7b2…b7d1`

- core 全体で literal `a01`〜`a12` の出現がちょうど二行であり、その二行が operation の対象であることを確認する。
- `new_text == old_text` の一個の `a12` token だけを `a13` に置換した bytes であることを確認する。
- manifest の errata array を順にすべて解決する。errata 数に singleton 条件を置かない。
- 複数 errata では locator の原 core 上の byte span が非重複であること、順次適用後 digest が manifest の `composed_sha256` と一致することを要求する。
- manifest の集合と解決済み集合を path・commit・SHA-256 の exact set で比較する。
- core、A、全 errata、approval fold、承認済み補助 blob の commit が `measurement_head` の祖先であることを確認する。
- 一検査でも失敗したら `{a01,…,a13}` へフォールバックせず resolver 全体を失敗させる。

## 単位 B — 受領証層

| path:line | 変更内容 |
|---|---|
| `orchestrator/qualification/t139_receipt_schema.json:1-1100` | 唯一の受領証 schema blob |
| `orchestrator/qualification/t139_receipt.py:1-540` | schema loader、mandatory cross-constraint executor、`verify_receipt`、binding-required sink |
| `orchestrator/qualification/artifacts.py:2-5` | docstring を T-126 専用 root から登録済み qualification root へ訂正 |
| `orchestrator/qualification/artifacts.py:34-39` | exact namespace tableへ `t126` と `t139` を追加 |
| `orchestrator/qualification/artifacts.py:230-243` | `QualificationRoot.__init__()` に keyword-only lineage を追加。default は T-126 のまま、T-139 は exact `output/env/pegasus/t139` のみ |
| `orchestrator/qualification/__init__.py:21` | `verify_receipt` を import |
| `orchestrator/qualification/__init__.py:34` | `verify_receipt` を `__all__` に追加 |
| `orchestrator/tests/test_t139_receipt.py:1-950` | schema closure、cross-field、sink、ledger coverage、binary 分離 |
| `orchestrator/tests/test_t139_authority_boundary.py:1-240` | producer 申告値を受理入力にする consumer mutant の否定検査 |

### Schema の形式と digest

- Draft-07 の構造 keywordを使う。現環境の `jsonschema` に `Draft202012Validator` が無いためである。
- 標準 JSON Schema では異なる field の値比較ができないため、同じ一枚の blob に必須 extension `x-izanagi-crossConstraints` を置く。
- `t139_receipt.py` は extension を annotation として無視してはならず、標準検査後に全 operation を実行する。extension の欠落・未知 operation・余剰 key は schema 自体の不正として拒否する。
- schema digest は `t139_contract.py:42-45` の `T139_RECEIPT_SCHEMA_SHA256` に literal 固定する。resolver は `measurement_head` の Git blobを読み、その digest と照合して `PreregBinding.receipt_schema` に三つ組として含める。
- schema 自身に自己 digest は書かない。二枚目の schema/meta-schema は作らない。

### Top-level 18 key と nested 設計

Top-level `required` は次の18件だけとし、`additionalProperties:false` を置く。

```text
schema_version study_id declared_use_class study_stage
series_id parent_series_id
preregistration environment measurement_checkout dependency_pins
arms allocations planned_execution actual_runs
correctness_evidence liveness admission_telemetry attempts
```

全 `$defs` の object は「`required == properties の全 key`」か明示した nullable unionとし、必ず `additionalProperties:false` を持たせる。可変 map は作らず、`translation_units` 等は closed item の array にする。

| top-level | exact nested shape |
|---|---|
| `schema_version` | const `t139-raw-receipt/v1` |
| `study_id` | const `t139-rf-partial-recovery` |
| `declared_use_class` | `official/exploration/qualification/dry`。`x-izanagi-acceptance-input:false` |
| `study_stage` | pilot receipt では const `pilot` |
| `series_id` | lowercase SHA-256 |
| `parent_series_id` | lowercase SHA-256 または `null` |
| `preregistration` | `{core,addendum_a,addendum_b,fold_commit,approval_manifest,errata,receipt_schema,producer_protocol}`。blob ref は `{commit,path,sha256}`、erratum は `{path,commit,sha256,approval_fold_commit}` |
| `environment` | `{env_tag,attestation_mode,attestations}`。attestation item は `{kind,artifact}`、artifact は `{path,size,sha256}` |
| `measurement_checkout` | `{repository_head,ccbench_head}`。repository head は binding の `measurement_head` |
| `dependency_pins` | fixed-order array。item `{name,commit,tree}`、gflags/glog/masstree/mimalloc/googletest の exact 5件 |
| `arms` | exact `{stock,mode1,modeX}`。各 arm は `{compile,binary,built_outside_allocation,toolchain}` |
| `allocations` | item `{allocation_id,attempt_id,cluster_slot,allocation_role,path_choice,path_choice_intent,requested_walltime_s,internal_deadline_s,phase_caps,phase_events,pbs_job_id,node,wall_started_at,wall_finished_at,accounting_raw,exclusivity,binary_rehash}` |
| `planned_execution` | `{workloads,schedule_seed,schedule_algorithm,schedule_sha256,cluster_slots,runs}` |
| `actual_runs` | 下記の exact run object |
| `correctness_evidence` | item `{arm,run_scope,build,outputs}`。outputs は file pointer のみ |
| `liveness` | item `{arm,run_scope,outputs}`。pass/verdict boolean は持たない |
| `admission_telemetry` | derivation receipt または alpha reservation の tagged union |
| `attempts` | intent・qsub raw・marker・環境観測・失敗証拠を持つ exact attempt object |

主要な `$defs` は次とする。

- `compile`

  `{source,mode_macro,configure_argv,translation_units,identity_sha256,trace_enabled,analysis_enabled,cmake_cache,compile_commands}`。source は `{repo_commit,ccbench_pin,base_tree_sha,patch_path,patch_sha256}`、TU item は `{source_path,normalized_argv}`、cache は `{trace,add_analysis}`。性能 arm の trace/analysis/cache はすべて 0/false。

- `toolchain`

  `{compiler_path,compiler_version,compiler_sha256,link_argv,dynamic_deps,elf_interpreter}`。dynamic dependency item は `{soname,resolved_path,sha256}`。

- `phase_cap`

  `{phase,cap_s,term_at_s,kill_at_s}`。`term_at_s == cap_s-10`、`kill_at_s == cap_s` を mandatory cross constraint にする。

- `exclusivity`

  `{qstat_request_raw,qstat_node_raw,process_snapshot_raw}`。boolean/pass/status は持たない。

- `planned_run`

  record-items の指定どおり `{run_id,cluster_slot,workload,block_index,permutation,planned_ordinal,position,predecessor_arm,arm,preceding_wait}`。wait は `{kind,required_s}`。

- `actual_run`

  `{run_id,attempt_id,allocation_id,cluster_slot,workload,block_index,permutation,actual_ordinal,position,predecessor_arm,arm,preceding_wait,monotonic_start_ns,monotonic_end_ns,raw_tps,binary_sha256,exec_witness,argv_sha256,argv_raw,run_log}`。actual wait は `{kind,required_s,monotonic_start_ns,monotonic_end_ns}` で `satisfied` を持たない。exec witness は `{path,inode,size,sha256,monotonic_ns}`。

- `correctness_build`

  `{source,compile,binary}`。compile は `{identity_sha256,argv,trace_enabled:true,analysis_enabled:true,cmake_cache:{trace:1,add_analysis:1},compile_commands}`。

- `environment_observation`

  指定どおり `{ordinal,scope,run_id_or_null,stat_before_raw,stat_after_raw,stat_before,stat_after,monotonic_start_ns,monotonic_end_ns,load1_diagnostic,malformed_reason_or_null}`。`recovered` boolean は存在しない。counter array は可変長で、8列未満を zero-fill しない。

- `admission_telemetry`

  a10/a11/a12 item は `{kind,receipt,returncode,B,seed,input_sha256}`。a13 item は `{kind:"alpha_reservation",ledger_path,family_root,ordinal,reservation_entry_sha256,reservation_commit}`。

- `attempt`

  `{attempt_id,cluster_slot,submission_intent,qsub,allocation_id,replaces_attempt_id,reason_code,performance_started_marker,environment_observations,preflight_evidence,failure_evidence}`。qsub は `{invocation_sha256,returncode,stdout_raw,stderr_raw,job_id}`。失敗 qsub では job/allocation を `null` にできるが attempt row は必須。

Mandatory cross constraints は次を同じ schema blob に置く。

1. ID 一意性と全 foreign key。
2. completed attempt は slot ごとに planned/actual 36 run 完全双射。
3. failure attempt は planned schedule の厳密 prefixかつ failure evidence 必須。
4. canonical intent ledger と `attempts[]` の exact coverage。
5. actual の順序、position、predecessor、wait kind/required 値が planned と一致。
6. actual wait の単調時計差が required 秒以上。
7. correctness binary SHA が同じ arm の性能 binary SHA と非同一。
8. correctness allocation/run と performance allocation/run の非同一。
9. `argv_raw.sha256 == argv_sha256`、binary witness と arm binary の参照整合。
10. reason/marker/replacement の条件分岐。a03 preflight failure 分岐だけは前述の裁定後に確定する。

`verify_receipt` はこれらの構造・参照整合性だけを検査し、pairing、cluster 間順序均衡、cluster eligibility、accept/reject の判定は実装しない。

## 単位 C — 投入・測定層

| path:line | 変更内容 |
|---|---|
| `tools/pegasus/policies/t139_pilot_v1.json:1-360` | 追補 A a01〜a13 の producer 用機械可読 projection。approved addendum triple を先頭に束縛 |
| `tools/pegasus/policies/registry_v1.json:4` | T-126 policy の直後へ T-139 policy path を追加 |
| `orchestrator/qualification/t139_schedule.py:1-240` | a09 schedule、36 run、wait 列、W1/W2 argv の純関数 |
| `orchestrator/qualification/t139_ledger.py:1-560` | study-wide binding、alpha reservation、submission intent、qsub/result、attempt closure の create-only ledger |
| `orchestrator/qualification/t139_submission.py:1-610` | committed source closure、静的 admission、qsub 前 intent、公開 `submit_pilot` |
| `orchestrator/qualification/t139_driver.py:1-980` | verification allocation、performance allocation、phase cap、環境観測、marker、36-run loop |
| `orchestrator/qualification/t139_collector.py:1-590` | failed qsub、job preflight reject、成功 prefixを全回収し、binding-required sink を呼ぶ |
| `tools/pegasus/t139_pilot.pbs:1-150` | thin PBS bootstrap。staged committed codeだけを `python -I -B` で実行 |
| `tools/pegasus/submit_t139_pilot.py:1-130` | manifest の approved refs で resolver を呼ぶ CLI。`--admission-only` と明示 `--submit` |
| `tools/pegasus/collect_t139_pilot.py:1-100` | collector CLI。qsub は呼ばない |
| `orchestrator/qualification/__init__.py:22` | `t139_submission` から `submit_pilot` を import。単位 C 完了前には追加しない |
| `orchestrator/qualification/__init__.py:35` | `submit_pilot` を `__all__` に追加 |
| `tools/pegasus/admission_registry.json:16-28,178-195` | collector、submitter、PBS body の entry を辞書順で追加 |
| `tools/pegasus/README.md:25-33,262-310` | site table と「admission-only、実 qsub 未実施」の手順を追加 |
| `orchestrator/tests/test_t139_producer.py:1-1450` | ledger、source closure、schedule、driver、collector、qsub stub |
| `orchestrator/tests/test_t139_vertical_slice.py:1-380` | hermetic two-commit approval + stub driver の schema-valid e2e 正例 |

### Alpha reservation

caller が path を選べない固定 Git ref `refs/izanagi/t139-primary-alpha-ledger` を canonical ledger とする案を採る。

- entry path は `reservations/<family_root>/000001.json`。
- entry は binding digest・study/series identityを持つ create-only object。
- plumbing で reservation commit を作り、`git update-ref <ref> <new> <old>` の CAS で原子的に予約する。
- CAS競合後は、同一 entry の exact replayだけを冪等成功とし、別 studyによる同じ `(family_root,1)` は拒否する。
- 失敗・中断後も ref/entry を削除しない。
- receipt の `ledger_path` は固定 ref 名、`reservation_commit` は entry を初めて追加した commit。
- push は行わない。将来の validator はこの ref history を読み直す。

非-main ref の永続運用が許されない場合は専用外部台帳が必要なので、これは最終設計択一として残す。

### Submission と source closure

`submit_pilot` は次の順序を固定する。

1. opaque binding の seal、HEAD、schema/protocol/manifest blobを再検査。
2. study-wide `binding.json` を create-only publish。既存 bytes が異なれば停止。
3. alpha ordinal を予約または exact replay。
4. ledger から次の allocation role/slot を一意に導出。caller は slot や role を渡せない。
5. `measurement_head` の Git blobから transitive code closureを canonical staging へ展開し、全 path/size/SHAを intent に記録。
6. `submission-intent.json` と ledger event を qsub より先に fsync/create-only publish。
7. qsub invocation claim を create-only publishしてからだけ qsub を実行。
8. stdout/stderr/returncode を結果に関係なく保存。非0なら attemptを残して例外終了し、自動再投入しない。
9. 成功時だけ既存 `job_id_from_qsub_stdout()` で job ID を導出し、binding eventを追加して submission IDを返す。

テストでは qsub runnerを差し替え、実 `qsub` executableが呼ばれていないことを明示検査する。本 wave 自体では `--submit` を実行しない。

### Driver

- 最初の allocation は verification role。性能3 armを trace/analysis 0、correctness/liveness 3 armを1で別 buildする。性能 binary の唯一生成元をここに置く。
- correctness/liveness run は verification allocationだけで実行する。
- performance allocationは immutable performance binaryをstageし、3点 rehashする。
- a09 の key grammarを逐語実装し、slotごとに2 workload × 6 permutation × 3 arm = 36 runを生成する。
- workload先行は奇数slot=W2、偶数slot=W1。置換時も元slotを使う。
- waitは block内30秒、block間60秒、workload切替は同じ60秒一回、総量1380秒。
- 最初のa03観測はpreflight、残り35件はwait末尾10秒。観測からexecは5秒以内。
- `performance_started` markerはpreflight観測の後、最初のexec前にcreate-onlyで作る。
- `/proc/stat` は実 readerを二回呼び、raw lineと時刻を先に保存する。`recovered` booleanは書かない。
- 各phaseは `cap-10` で owned process groupへTERM、`cap` でKILL。T-126のWmax controllerとは異なるので専用実装にする。
- TPS、arm、残run数を失敗写像の入力にしない。
- pairing、cluster間均衡、eligibility、consumer verdictは計算しない。

### Collector

collector は canonical ledger の全 intent を起点に列挙するため、成果物側だけを走査して失敗 attemptを見落とさない。

- qsub非0: stdout/stderr/rc pointerを持ち、allocationはnull。
- qsub成功・job preflight reject: job-stagingのnonce/job ID/source closureに束縛されたraw rejectを回収。
- run途中失敗: actualはplanned strict prefix、failure pointer必須。
- completed: 36 run exact coverage。
- 全attemptを組み立てた後、`publish_raw_receipt(receipt, binding=binding)` だけを通して永続化。
- unguardedな `write_receipt`、`Path.write_text()`、collector直の`publish_bytes()`経路は作らない。

## 既存機構の再利用マップ

| 既存関数・型 | 方針 |
|---|---|
| `artifacts.read_regular_file_with_identity()` | そのまま使用。hashとparseを同じfd snapshotに束縛 |
| `artifacts.sha256_bytes()` / `file_record()` | そのまま使用 |
| `artifacts.create_bytes()` / `create_or_verify_bytes()` / `create_json()` | intent、ledger event、marker、receiptのcreate-only publicationに使用 |
| `QualificationWriteCapability` / `QualificationRoot` | rootのexact namespace tableだけ一般化し、T-139でも同じsymlink/owner/inode防御を使用 |
| `atomic_publish.publish_bytes()` | PBS bootstrapの既存parent配下に残す最小terminal artifactで使用可能。final receipt sinkには直接使わない |
| `contract.canonical_json_bytes()` | そのまま使用 |
| `trial_registry.resolve_measurement_commit()` | そのまま使用。resolver冒頭で一度だけ呼ぶ |
| `trial_registry.assert_prereg_ancestor()` | core/A/errata/approval foldのancestry検査にそのまま使用 |
| `trial_registry._blob_at_commit()` | private importは禁止。public wrapperを一つ追加して再利用 |
| `qsub_binding.job_id_from_qsub_stdout()` | qsub stdout grammarだけ再利用 |
| `tools/pegasus/probes/t139_r4_env_probe.py` の `parse_aggregate_cpu_line()`、`analyze_window()`、compile argv/cache helper | committed closureから純関数だけ再利用。probe metadataと`derive_decision()`は使わない |
| `attempt_ledger.SeriesAttemptLedger` | 直接流用しない。T-126 schema、retry 0/1、event enum、namespaceに固定されている |
| `series.SeriesFSM` | 流用しない。T-126 SPRT、subject/reference、round state machine専用 |
| `contract.validate_protocol()` / `t126_control_v1.json` | 流用不可。authority、workload、SPRT、timing、artifact namespaceがT-126 literal |
| `t126_*_schema.json` | 構造上の参考のみ。T-139の18 key/a01〜a13/36 run/conditionalを表現できない |
| `collector.collect()` | 実装パターンとfailure recoveryを参照するが直接呼ばない。入力schema・job result・retryがT-126専用 |
| `submission.prepare_toolchain()` | compiler hashingの考え方だけ参照。T-126のperf候補、依存集合、policy/schemaを返すため直接流用しない |
| `identity.verify_recorded_series_identity()` | T-126 required path set固定のため直接流用しない。T-139は独自exact closureを持つ |
| `t126_driver.py` | process group封じ込めの設計を参照するが、T-139のphase cap・36 run・a03順序とは契約が異なるため直接流用しない |
| `retry_index.py` | T-139はordinal/cluster slotとR7規則を持つため流用しない |

したがって「T-126 contractをT-139へ流用する」は不可。一方、fd snapshot、canonical JSON、create-only capability、Git ancestry、qsub stdout parserはcontract非依存なので再利用する。

## テスト計画

### §13 の必須 mutation

| 要件 | nodeid案 | killする変更 |
|---|---|---|
| 1 | `orchestrator/tests/test_t139_producer.py::test_s13_1_failed_qsub_remains_in_ledger_and_receipt` | qsub失敗をledger/receipt双方から削除 |
| 1 | `orchestrator/tests/test_t139_producer.py::test_s13_1_job_preflight_reject_is_collected_from_intent` | job側preflight rejectを無視 |
| 1 | `orchestrator/tests/test_t139_receipt.py::test_attempts_exactly_cover_canonical_submission_intents` | intent集合の部分被覆 |
| 4 | `orchestrator/tests/test_t139_receipt.py::test_s13_4_forbidden_eligibility_fields_are_unknown` | `qualification_status`、`pairing_passed`、`accepted`、validator identity/resultを任意階層へ追加 |
| 6 | `orchestrator/tests/test_t139_producer.py::test_s13_6_actual_run_swap_is_rejected_against_planned_order` | actual二runの入替え |
| 6 | `orchestrator/tests/test_t139_producer.py::test_s13_6_wait_shortfall_is_rejected_from_monotonic_endpoints` | required値だけ残して実待機を短縮 |
| 7 | `orchestrator/tests/test_t139_preregistration.py::test_s13_7_caller_self_consistency_cannot_replace_approved_core` | caller指定blob/digestだけ自己整合 |
| 7 | `orchestrator/tests/test_t139_preregistration.py::test_s13_7_addendum_envelope_rejects_missing_extra_and_duplicate_fields` | a13欠落、a14追加、aNN重複 |
| 7/N2 | `orchestrator/tests/test_t139_preregistration.py::test_legacy_addendum_with_same_core_ref_is_rejected_by_manifest_digest` | 旧追補Aへの差替え |
| 8 | `orchestrator/tests/test_t139_producer.py::test_s13_8_environment_probe_reads_and_records_two_real_snapshots` | `/proc/stat` readerを呼ばず定数を返す |
| 8 | `orchestrator/tests/test_t139_producer.py::test_s13_8_a03_failure_never_maps_to_pre_performance_or_replacement` | a03不成立を開始前infraへ写す |
| 8 | `orchestrator/tests/test_t139_producer.py::test_s13_8_raw_counter_and_malformed_reason_cannot_be_replaced_by_recovered_boolean` | rawを捨てbooleanだけ保存 |

環境恒真化について本 wave が killできるのは「現在のproducer実装を定数化するmutation」である。任意の偽producerを独立再計算で検出する保証は段C validatorまで主張しない。

### §2(e) consumer authority

次をparameterizeする。

`orchestrator/tests/test_t139_authority_boundary.py::test_declared_receipt_values_cannot_be_acceptance_dependencies`

対象は次の4 JSON pointer。

- `/declared_use_class`
- `/admission_telemetry/*/returncode`
- `/attempts/*/reason_code`
- `/allocations/*/exclusivity`

テストは schema の `x-izanagi-acceptance-input:false` とAST guardを使い、各値を acceptance predicateへ入力する合成consumer mutantが拒否されることを確認する。同時にrepository内のT-139 consumer候補をscanする。ただし実際のconsumerや受理判定は作らない。

### Binding・schema・e2e

追加nodeid案:

- `test_t139_preregistration.py::test_erratum_resolver_consumes_every_member_of_exact_set_in_manifest_order`
- `test_t139_preregistration.py::test_overlapping_errata_and_wrong_composed_digest_fail_closed`
- `test_t139_preregistration.py::test_measurement_head_is_derived_and_absent_from_public_signature`
- `test_t139_receipt.py::test_top_level_is_exactly_18_and_every_nested_object_schema_is_closed`
- `test_t139_receipt.py::test_correctness_binary_must_differ_from_same_arm_performance_binary`
- `test_t139_receipt.py::test_correctness_and_performance_run_scopes_are_disjoint`
- `test_t139_receipt.py::test_publish_raw_receipt_requires_keyword_only_binding`
- `test_t139_receipt.py::test_forged_or_stale_binding_is_rejected_before_receipt_creation`
- `test_t139_producer.py::test_committed_source_closure_has_no_live_worktree_import`
- `test_t139_producer.py::test_phase_cap_terms_at_cap_minus_ten_and_kills_at_cap`
- `test_t139_vertical_slice.py::test_hermetic_stub_produces_one_schema_valid_receipt_without_qsub`

最後の正例は合成Git repo、stub qsub、stub verification/performance driverを使う。実 `qsub` が呼ばれたら失敗するtrapも置く。

実装後の実行は直接pytestではなく、すべて `python3 tools/run_tests.py ...` 経由とする。関連T-126 regression、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、commit後の `python3 tools/check_ai_provenance.py` も完了条件に含める。

## 規模見積りと分割

| 単位 | production/schema新規 | tests新規 | 判断 |
|---|---:|---:|---|
| A | 約650〜800行 | 約550〜700行 | manifest/Markdown/Git adversarialケースが多い |
| B | 約1,350〜1,700行 | 約800〜1,000行 | schema一枚だけで約900〜1,100行 |
| C | 約2,800〜3,400行 | 約1,200〜1,500行 | build二系統、ledger、PBS、collectorを含む |
| 共通docs/registry | 約100行 | 既存検査へ吸収 | |
| 合計 | 約4,900〜6,000行 | 約2,550〜3,200行 | 通常の1 waveには大きすぎる |

率直には、N1の先行foldを含めて1 waveには収まらない。安全な切断点は次の三つ。

1. activation wave: §51 approval payloadだけをcanonical foldし、`F_e`を確定。producer codeはゼロ。
2. contract wave: A+Bを実装するが `submit_pilot`、PBS、production callerを一切追加しない。「producer完成」と記録しないため、pilotは依然不可能。
3. producer wave: C、public export、schema-valid e2eを同じland単位で追加。この時点で初めてproducer完成とする。

A/Bの途中で空の `submit_pilot` や恒真deny stubを公開する分割、ledgerだけを先行landする分割は採らない。

## 総括

中核3行:

- manifestは自己参照させず、先行canonical fold `F_e` と、その子孫に置くexact mirrorを照合してtrust rootを作る。
- resolverはapproved digest・exact errata set・a01〜a13 envelope・ancestryをfail-closedで束縛し、sink自身がkeyword-only bindingを要求する。
- receiptはtop-level 18 keyの一枚schemaで閉じ、trace-off性能とtrace-on correctnessのbinary/run非同一性までmandatory cross constraintにする。

1 wave判断:

- 約7,500〜9,200行規模かつ先行fold必須なので、通常の1 waveには収まらない。activation → 非実行可能なA+B → C+e2e activationの三切りが、半実装を実行可能にしない最小分割である。

未解決の設計択一:

- preflight a03不成立を表す `post_performance_failure` に、marker/run raw以外の第三分岐を認めるか。推奨はenvironment observation backed failure evidenceの追加。
- canonical alpha ledgerを固定Git refに置くか、別の外部永続台帳に置くか。推奨はCAS可能で`reservation_commit`を自然に持てる固定Git ref。
- N1を先行activation waveで解くことを許すか。同一fold内のliteral自己参照は不可能なので、許さない場合はreal-repo正例とproducer完成を成立させられない。