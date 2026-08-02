結論は、旧 rung を 3 arm 化するのではなく、独立した新 patch で `stock / mode1(degraded) / mode2(X)` を作り、8 個の独立 PBS allocation をまとめた正例 artifact を新設する案です。既存 rung・ledger・evidence・producer の bytes は変更しません。

親 brief の「表面上の不足は 4 点」は確認できました。ただし「実装差分も 4 点」は不正確です。裸マクロ patch の新規登録、答え露出防止、独立 session orchestration も必要です。

## 確認結果と設計境界

- 既存 evidence が CCBench pin、attestation、事前凍結 24-run schedule を持つ点は正しいです。
- 3 arm、`env_tag`、測定 checkout が無い点も正しいです。[brief.md:14–28](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:14)
- 既存 6 rep は 1 allocation 内の within-window interleave で、between-run floor ではありません。[silo_ladder_rung1-permanent.md:29–40](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md:29)
- `patches/ledger.json` は entry が一件で、旧 rung の eligibility を false に固定しています。[ledger.json:5–21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/patches/ledger.json:5)
- 旧 contract は ledger 一件・closed schema・false 値を exact に要求します。[silo_ladder_rung1_contract.py:454–564](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1_contract.py:454)
- 旧 evidence test は ledger、patch、driver、scripts、shared policy、runtime modules の現物 bytes を再束縛します。[test_silo_ladder_rung1_evidence.py:1172–1234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1172)
- `Genome.cmake_defines()` は `-DCCBENCH_*` しか生成しません。[model.py:57–59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/model.py:57)
- 新しい裸 `IZANAGI_*` patch は現行登録テストにも拒否されます。[test_p3_s4_loop.py:943–978](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_p3_s4_loop.py:943)

したがって、旧 rung を別 policy から「baseline 扱い」に変えるのではなく、patch identity から新しい独立 control を作る必要があります。これは D120 決定 2 の禁止を回避する案ではなく、禁止対象である旧 composition をそもそも消費しない案です。[decisions.md:5746–5756](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/decisions.md:5746)

## 1. arm X と新 patch

新規 `patches/silo_recovery_positive_control.patch` を一枚作り、同じ stock CAS に対する二つの mode を持たせます。

予定行帯は次のとおりです。

| 予定位置 | 内容 |
|---|---|
| `:1–12` | `transaction.cc` diff、`<array>` / `<mutex>` |
| `:13–36` | mode 相互排他、mutex、activation symbol |
| `:37–70` | CAS を囲む mode1/mode2 分岐と stock 逐語 branch |
| `:71–95` | `ycsb_silo.cc` の trace-disabled t48 liveness report |

マクロと symbol は中立名にします。

- `IZANAGI_SILO_RECOVERY_PC_MODE1`
- `IZANAGI_SILO_RECOVERY_PC_MODE2`
- `IZANAGI_SILO_RECOVERY_PC_REPORT`
- `izanagi_silo_recovery_pc_mode1_identity`
- `izanagi_silo_recovery_pc_mode2_identity`

役割は manifest 内でのみ次のように束縛します。

| build id | patch | macro | 意味 |
|---|---|---|---|
| `stock` | 非適用 | なし | stock |
| `mode1` | 適用 | `MODE1` | degraded |
| `mode2` | 適用 | `MODE2` | arm X |

`mode1` は旧 rung と同型の単一 global mutex です。`mode2` は mutex を二本にし、YCSB の非空 key の末尾 byte の parityで選ぶ二 stripe gateとします。CAS の lvalue、`expected`、`desired`、呼出回数は stock と同一に保ち、wrapper 関数にはしません。

概念形は次です。

```cpp
#if defined(MODE1) && defined(MODE2)
#error mutually exclusive modes
#endif

#if MODE1
std::mutex gate;
#elif MODE2
std::array<std::mutex, 2> gates;
#endif

#if MODE1
  std::lock_guard<std::mutex> guard(gate);
#elif MODE2
  const auto stripe = key.empty() ? 0U
      : static_cast<unsigned char>(key.back()) & 1U;
  std::lock_guard<std::mutex> guard(gates[stripe]);
#endif
acquired = compareExchange(same_lvalue, expected.obj_, desired.obj_);
```

既存一 mutex rung は stock の約 4.4% / 10.7% まで落ちているため、二 stripe は「mode1 より回復するが、48 thread の stock には届かない」候補として実装可能性があります。[silo_ladder_rung1-permanent.md:31–36](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md:31) ただし性能順序は未実測なので保証しません。

受理条件は両 workload で `degraded < X < stock` が between-run margin を伴って成立することです。成立しなければ正例 artifact を生成せず、stripe 数の事後変更もしません。四 stripe等を試す場合は、新 schedule・新 campaign ID を持つ後続 wave にします。

### build 注入

新 driver の planned `configure_argv()`（`orchestrator/campaign/silo_recovery_positive_control.py:430–500`）で、既存専用 driver と同じく次を渡します。

```text
-DCMAKE_CXX_FLAGS=-DIZANAGI_SILO_RECOVERY_PC_MODE1=1
```

または `MODE2=1`。report build のみ、同じ文字列へ `REPORT=1` を加えます。既存経路の先例は [silo_ladder_rung1.py:2002–2026](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1.py:2002) です。

各 binary について以下を同時に検査します。

- `compile_commands.json` の対象 TU に mode macro が exactly one。
- 他 mode macro はゼロ。
- perf build では report macro ゼロ、`TRACE=0`。
- `nm --defined-only` で当該 identity symbol が一個、他 mode symbol がゼロ。
- perf binary の `izanagi_trace` symbol はゼロ。
- stock は patch 非適用 treeからbuildし、mode/report macroもsymbolもゼロ。

patch 適用・マクロ OFF の tree を stock と呼びません。行追加で `__LINE__` 等の binary bytes が変わり得ることは既に確認されています。[t139-silo-degradation-ladder-design.md:132–148](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:132)

## 2. artifact の置き場と適格性宣言

最終成果物は新規 path とします。

```text
output/env/pegasus/silo_recovery_positive_control/
  silo_recovery_positive_control.json
  job-staging/...
```

適格性の正本は ledger の追記ではなく、新 patch だけを所有する閉じた qualification manifest とします。

```text
orchestrator/qualification/silo_recovery_positive_control_v1.json
```

予定 schema は以下です。

| 予定行帯 | 内容 |
|---|---|
| `:1–20` | schema、独立 ID、authority |
| `:21–45` | classification |
| `:46–80` | patch、mode、macro、symbol |
| `:81–115` | projection policy |
| `:116–170` | workload、session、schedule、floor protocol |
| `:171–200` | producer、task policy、artifact path |

classification は exact に次を持たせます。

```json
{
  "evaluation_role": "ability_probe",
  "ability_probe": true,
  "artifact_role": "positive-control",
  "research_goal_eligible": false,
  "recovery_measurement_eligibility": true,
  "pipeline_eligible": false,
  "composition": "dedicated-positive-control-only"
}
```

この `true` は新 ID・新 patch・新 artifact の qualification input にだけ作用します。旧 `silo_ladder_rung1`、旧 patch、旧 evidence path、`supersedes`、baseline override の参照は manifest 全階層で禁止します。将来の loop 接続権限も与えません。

新規 `orchestrator/campaign/silo_recovery_positive_control_contract.py` で、manifest と patch を一体で検査します。

| 予定行帯 | 検査 |
|---|---|
| `:1–90` | exact schema、reason code |
| `:91–270` | unified diff、source file allowlist |
| `:271–440` | mutex、guard lifetime、CAS同値、symbol |
| `:441–590` | manifest classification、独立 identity |
| `:591–660` | projection、公開 `validate()` |

### projection guard

新 patch は裸マクロを持つため、manifest を作るだけでは既存の登録検査に拒否されます。また設計台帳 §6-5 の答え露出防止も必要です。

- [projection_guard.py:17–22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/projection_guard.py:17): 旧 ledger の readerはそのまま残し、新 manifest の default pathと別 closed schemaを追加。
- [projection_guard.py:111–212](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/projection_guard.py:111): production の引数なし呼出しでは、旧 ledger と新 manifest の projection policy を fail-closed に集約。
- [test_p3_s4_loop.py:912–978](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_p3_s4_loop.py:912): 登録済み裸マクロ patch 集合を「旧 ledger entry ∪ 新 qualification manifest」に変更し、新 mode token/path の3 loop拒否を追加。

これは拒否集合を強める変更であり、旧 eligibility の上書きではありません。

## 3. 新 artifact の schema

`output/.../silo_recovery_positive_control.json` は旧 artifact schemaを拡張せず、専用 `silo-recovery-positive-control/v1` にします。

予定 top-level は次です。

```text
schema_version
artifact_id
classification
measurement_context
bindings
protocol
certification_leg
performance_leg
between_run_floor
qualification
raw_bundle
limitations
all_pass
```

### `env_tag`

次の exact field に持たせます。

```text
measurement_context.env_tag = "pegasus"
measurement_context.env_contract
```

`env_contract` には以下を保存します。

- `contract_sha256`
- 登録 calibration の `path` / `sha256`
- `clocks_per_us`
- `numactl`
- `attestation_mode`
- `isolation_policy`

値は既存 registry の Pegasus entryへ再束縛します。[env_contract.py:180–193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/env_contract.py:180) 各 session job の attestation が同じ contract hash・calibration hashを持たなければ全体を拒否します。

### 測定 checkout

次の field に固定します。

```text
measurement_context.measurement_checkout
```

exact subfields は次です。

```text
checkout_kind
repo_root_realpath
git_dir_realpath
git_common_dir_realpath
source_commit_full
source_tree_full
tracked_clean
source_surface_status_sha256
ignored_input_receipt {path, sha256, count}
input_surface_manifest_sha256
```

さらに各 PBS receipt に同じ構造を入れ、最終 collector が root receipt と全 session receipt の exact equality を要求します。

`ignored_input_receipt` は F41 の原因だった ignored 内容を記録するものです。ただし build 入力は fresh `/scr` CCBench worktree、pinned third-party、hash済み runtime modules に限定し、checkout の ignored `output/` 等を CMake sourceへ入れません。[failures.md:803–825](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/failures.md:803)

bindings は最低限、次を現物 SHA256 に束縛します。

- qualification manifest
- patch
- contract
- driver
- PBS job / submitter
- task-specific reservation policy
- shared site policy
- runtime modules
- verifier modules
- registered calibration
- CCBench full pin
- global frozen schedule

## 4. between-run floor と識別可能性

既存の 1 allocation 内 6 rep は使用しません。D19 の実装先例に合わせ、1 session は5 repのmedian、between-run は8 session-median のCVとします。[between_run_floor.py:53–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/between_run_floor.py:53)

ただし同 driver 自身が、back-to-back 8 session は楽観的下限と明記しています。[between_run_floor.py:85–107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/between_run_floor.py:85) そのため本 artifact では次の構成にします。

1. 8個の別 PBS allocation、別 job ID、fresh build。
2. 各 allocation が1 sessionのみ所有。
3. session間に最低1,800秒。queue待ちがそれ以上なら追加待機不要。
4. 各 session は2 workload × 5 rep × 3 arm、計30 perf process。
5. 全240 perf processをtrace-disabledで実行。
6. 欠測・非zero・競合検出後の値は補完しない。performance observation開始後のretryは禁止。
7. sessionごとに `stock/mode1/mode2` の5 rep medianを作り、8 median間のCVを計算。

workload `w`、arm `a` について、

```text
m[a,w,j] = session j の5 rep median
S[a,w]   = 8個の m の median
CV[a,w]  = sample_stdev(m) / mean(m)
F[a,w]   = S[a,w] × CV[a,w]
```

と記録します。

分母の artifact-local witness は、

```text
D = S[stock,w] - S[mode1,w]
F_delta = F[stock,w] + F[mode1,w]
```

として、以下を両 workload で要求します。

```text
D > F_delta > 0
min_j m[stock,w,j] > max_j m[mode1,w,j]
```

arm X についても、同じpairwise floorで次を要求します。

```text
S[mode1,w] < S[mode2,w] < S[stock,w]
min(mode2) > max(mode1)
min(stock) > max(mode2)
各pairのmedian gap > 対応する F[a]+F[b]
```

これは「この正例入力では分母と中間armが観測floorを越えて識別できた」という局所資格判定です。RF値、p値、信頼区間、多重比較、clamp、`RF<0` / `RF>1` の帰属規則は実装しません。JSON全階層で `rf` / `recovery_fraction` keyを禁止するテストを置きます。

5 rep はRFの検定力根拠とは主張しません。D19 の「実 campaign 1 session と同形」の取得単位として採用し、足りなければ artifact は不成立にします。事後的に6や10へ増やしません。

## 5. Pegasus 実行計画

新規ファイルは次です。

```text
orchestrator/campaign/silo_recovery_positive_control.py
tools/pegasus/silo_recovery_positive_control.sh
tools/pegasus/submit_silo_recovery_positive_control.sh
tools/pegasus/policies/silo_recovery_positive_control_v1.json
```

policy registry [registry_v1.json:3–8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/tools/pegasus/policies/registry_v1.json:3) へ新 task policy pathを追加します。共有 `tools/pegasus/policy.json` は変更せず、project/queue/node/dependency pin等のsite値だけを読みます。

### job 構成

- certification job × 1
  - mode1/mode2 のtrace-enabled correctness build
  - verifier certified、anomaly/integrity zero
  - mode1/mode2 のtrace-disabled report build
  - t48 × 2 workload × 2 run の全worker `commits>0`
- performance session job × 8
  - stock/mode1/mode2 のfresh trace-disabled build
  - 30 perf process
  - 30回すべての直前にsolo check
  - session medianとraw receiptをcreate-only publish
- collector × 1
  - 8 session receiptとcertification receiptをrawから再計算
  - 全条件成立時だけ最終正例 JSON を生成

Pegasus の `single_process=True / allow_resume=False` は各 session job 内で守ります。最終 collector は別々の完結済み session artifactを読むだけで、途中再開するcampaign processではありません。

### schedule 凍結

submitter の予定 `:200–330` で、最初の `qsub` より前にglobal scheduleをcreate-only生成します。

- 8 session slot
- workload-first順は4対4
- 各 workload/sessionに5個の3-arm permutation
- workloadごとの40 permutation全体で各armのposition出現数差を最大1
- seed、生成algorithm version、全240 ordinal、1,800秒gapを保存
- schedule SHAをcampaign IDと全submit receiptへ束縛

次 session は前 session のsealed success、PBS accounting、gap経過を確認してから投入します。同じcontrol jobを二本同時には走らせません。

### 単独性とattestation

既存 [silo_ladder_rung1.py:1890–1999](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1.py:1890) を仕様の雛形にし、各jobで以下を取ります。

- CPU model、clock、cpuset、HT、NUMA
- `qstat -f` のwalltime/remaining
- performance sample直前の `pgrep -a -f 'ycsb_.*\.exe'`
- load1とpolicy threshold
- job前後のuptime/process receipt
- PBS job ID、node、会計epilogue

割当自体を専有証明とは扱いません。[pegasus-runbook.md:399–405](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/pegasus-runbook.md:399)

### 所要時間

1 sessionは既存28 sample jobとほぼ同じで、新規は30 sampleです。既存raw command receiptでは各benchが約3.4秒で、三buildも数秒から十数秒でした。ただしdependency、attestation、queueを含まないため、次の保守的予約にします。

```text
dependencies <= 180
attestation <= 180
configure/build/replay(3) <= 2700
run group(30) <= 900
collection <= 300
finalize <= 600
合計 4860 < 7200 秒
```

全jobを2時間requestとします。

- request上限: 9 jobs × 2h = 18 allocation-hours
- 想定active compute: 約1.5～3時間
- session間gap: 最低3.5時間
- queueが軽い場合のend-to-end目安: 5～8時間
- queue待ちは別

このwaveでは実時間を測っていないため、以上は既存receiptからの見積りです。

### 既存 producer の再利用可否

再利用するもの:

- env contract / attestation
- verifier
- patchharnessによるpinned clean worktree
- third-party offline staging
- create-only receipt、qstat、walltime、source witnessの設計
- `CMAKE_CXX_FLAGS`による裸マクロ注入方式

直接再利用しないもの:

- 旧schedule generator: 2 arm・6 rep固定。
- 旧gap/collect schema: 1 allocation・24 run固定。
- 旧PBS scripts: path、schema、build数、run数、retry policyが旧rung専用。
- 4,843行の旧driverのprivate helper import: command receipt schemaやpolicy lookupが旧stemへ固定され、新artifact identityに不要な依存を持ち込む。

したがって旧driver/scriptsはbytes不変の参照雛形とし、新しい兄弟producerを作ります。

## 6. pytest 設計

予定ファイルは次です。

| 新規test | 主な検査 |
|---|---|
| `orchestrator/tests/test_silo_recovery_positive_control_contract.py:1–500` | patch semantics、manifest closed schema、D120 isolation |
| `orchestrator/tests/test_silo_recovery_positive_control_driver.py:1–900` | schedule、build、checkout、env、floor、retry |
| `orchestrator/tests/test_silo_recovery_positive_control_pegasus.py:1–350` | `bash -n`、PBS header、policy、qstat、scrub、順次投入 |
| `orchestrator/tests/test_silo_recovery_positive_control_evidence.py:1–1000` | committed artifactとraw bundleの独立再束縛 |

重要nodeは以下です。

- patchの二mode相互排他。
- mode1はnamespace-scope非thread-local mutex一個。
- mode2は二stripeで、keyによる選択。
- lock guard lifetimeがstock CASを包含。
- CASのlvalue/`expected`/`desired`/回数がstockと同一。
- stockはpatch非適用。
- compile argvとnm symbolのexactly-one matrix。
- 8 session × 2 workload × 5 rep × 3 arm = 240。
- job IDが8個別、各sessionがfresh build receiptを持つ。
- `env_tag` / checkout / pin / attestationが全session一致。
- perf buildが全てtrace-disabled。
- floorとorderingをraw session medianから再計算。
- performance観測後のretry拒否。
- RF key不在。
- 新manifestが旧rung ID/pathを一切参照しない。
- 旧ledgerのfalse値と旧evidence bytesが不変。

既存 evidence testは変更しません。

## 7. 変異事前登録候補

段4で実装後の一意なanchorへ確定し、`tools/mutation_harness.py` 用specへ登録します。候補pathは次です。

```text
output/insights/2026-08-02_t139-positive-control-wave/mutation-spec.json
```

| ID | 一行変異 | 単一理由fixture / killer |
|---|---|---|
| M1 | macro count `== 1` → `>= 1` | duplicate mode macroだけを持つ `test_compile_argv_rejects_duplicate_mode_macro_only` |
| M2 | identity symbol count `== 1` → `>= 0` | symbolだけ欠く `test_nm_rejects_missing_mode2_identity_only` |
| M3 | env-tag equality → 恒真 | `env_tag`だけ違う `test_measurement_context_rejects_env_tag_mismatch_only` |
| M4 | session checkout equality → 恒真 | 一jobのHEADだけ違う `test_session_receipt_rejects_checkout_head_mismatch_only` |
| M5 | arm vocabulary検査 → 恒真 | arm tokenだけ未知の `test_schedule_rejects_unknown_arm_only` |
| M6 | denominator `gap > floor` → `>=` | gapがfloorとexact equalityの `test_denominator_rejects_gap_equal_to_floor_only` |
| M7 | perf `trace is False` → 恒真 | 一buildだけtrace=trueの `test_performance_build_rejects_trace_enabled_only` |
| M8 | observation後retry拒否 → 恒真 | 一sample後のattempt 2だけを持つ `test_retry_after_observation_is_rejected_only` |
| M9 | projection集約から新manifestを一行削除 | 新mode tokenだけをproposalへ入れる `test_projection_rejects_positive_control_token_only` |
| M10 | mode2 mutex数 `== 2` → `>= 1` | 一stripeだけへ縮退したpatch fixtureの `test_mode2_requires_exactly_two_stripes_only` |

各fixtureはpure validatorを直接呼び、期待reason codeを一件に限定します。他層が先に同じ入力を拒否するものは段4で登録せず、実効gateへ再照準します。

## 8. 段5の編集所有分割

次の4集合を素集合として凍結します。

| 所有者 | 編集ファイル |
|---|---|
| A: patch/contract | 新patch、新qualification manifest、新contract、contract test/fixtures |
| B: projection | `projection_guard.py`、`test_p3_s4_loop.py` |
| C: Python producer | 新driver、新task policy、policy registry、新driver test |
| D: Pegasus wrapper | 新job/submit scripts、新Pegasus script test |

親だけが統合後に以下を所有します。

- 変異spec
- `output/env/pegasus/silo_recovery_positive_control/**`
- committed evidence testの最終fixture合わせ
- 実測、collect、commit

Aがmanifestとcontract APIを先に凍結した後、B/C/Dはその読み取りだけで並列実装できます。既存 rung のpatch、ledger、driver、contract、scripts、evidence、shared policyは全員の編集禁止集合にします。

## 検査状態

このturnでは実装、build、pytest、benchmark、Pegasus投入を行っていません。ホストは `pegasus02` であり、runbook上pytestを含む重い処理は計算ノード限定です。read-only確認後のworktreeはcleanでした。

## 総括

(a) 推奨プランは、独立した一枚の二mode patch、ledger外の閉じたqualification manifest、1 certification job＋8独立session job、5 rep/session、trace-disabled 240 runから一つの正例artifactを作る案です。旧rungを一切再分類しません。

(b) 却下した代案は、旧ledger/evidenceの更新、旧falseを別policyで上書き、旧rungを新artifactのdegraded armとして再利用、patch適用マクロOFFをstock扱い、stockコピーをXにする案、固定sleep、同一allocation内back-to-back floor、6 rep踏襲、測定後のstripe数調整です。それぞれpin閉包、D120、OFF-inert、退化control、人工遅延、between-run不成立、根拠不足、選択的調整に反します。

(c) provisional裁定への評価:

- P1: 条件付き賛成。二stripe gateは実装可能で、既存一mutexの大幅劣化から部分回復を期待できる。ただし実測保証はなく、順序不成立ならartifact不成立とする。
- P2: 賛成。ただし「ledger新entry」は旧contractのexact-oneに反するため却下し、独立qualification manifestを採る。
- P3: 強く賛成。既存6 repはwithin allocationであり、8個の別allocation・fresh build・5 rep session medianで取り直す。

(d) 確認できなかった前提:

- 二stripeが両workloadで実際に `degraded < X < stock` になること。
- 新patchの実compile、nm、verifier、t48 liveness。
- 新pytestと変異候補の実kill。
- Pegasusの投入時queue、割当node、他利用者負荷。
- 5 rep × 8 sessionが将来のRF規範に十分な統計的検定力を持つこと。本案はそれを主張しない。
- 所要時間見積りの実測値。既存receiptからの推定に留まる。