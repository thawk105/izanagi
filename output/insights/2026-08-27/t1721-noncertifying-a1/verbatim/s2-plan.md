結論は「現行の編集禁止条件では非認証成果物型を作れない」です。`campaign_lock.py` と `artifact_admission.py` を編集しない限り、v1/E0 の非認証 lock を v2 authority で包み直す昇格経路が残ります。D1038 に従い実装は停止対象で、D1028 により A-1 投入器だけを先行させることもできません。

以下は静的検査結果と、所有解除後にそのまま使える実装計画です。

## 1. 非認証成果物型

### 4 層の必要実装と停止理由

| 層 | 必要な固定 | file:line | 現在の制約 |
|---|---|---|---|
| 鍵 | `CampaignConfig` に exact enum の authority class を持たせ、非認証 class だけを campaign identity に焼く。certified の既定値は serialize せず既存 ID を保存する | `orchestrator/campaign/model.py:66-84`, `orchestrator/campaign/ident.py:150-189` | ここだけでは v2 再包装を防げない |
| 記録 | 非認証 terminal を `STAGE_COMMIT` と別型にし、certified `contract_sha256` と certified commit receipt を発行しない。環境契約 hash と live 25-path binding は非認証記録の必須値にする | `model.py:23-36`, `pipeline.py:1453-1563`, および `orchestrator/campaign/wal.py:290-341,1102-1308` | marker を現行 COMMIT payload に足すだけでは、field 除去・stage 置換で昇格できる |
| schema | `campaign-lock/v1` と `campaign-lock/v2` のどちらでもない `campaign-lock/noncertifying-v1` を新設し、環境契約と live source binding を必須、`authority` を構造的に禁止する | `orchestrator/campaign/campaign_lock.py:15-26,154-166,216-275` | **編集禁止 file** |
| consumer | 新 schema を historical/noncertifying view としてだけ発行し、`CERTIFIED_ACCEPTANCE`、lock-only epoch gate、`CertifiedCampaignView` 発行を無条件拒否する | `orchestrator/campaign/artifact_admission.py:755-891,904-1116,1141-1203` | **編集禁止 file** |

したがって必要なプランが禁止 file の編集を要求します。ここが停止条件です。

### 実在する未閉鎖の昇格経路

次の再包装は現行コードで構造的に可能です。

1. 非認証宣言を `search_config` に入れた v1 inner identity を作る。
2. `campaign_lock.encode_campaign_lock_v2()` で同じ inner identity に v2 authority を付ける。
   - `campaign_lock.py:154-166` は top-level identity の 5 key だけを検査し、`search_config` 内の authority class を拒否しません。
   - `campaign_lock.py:255-275` はその identity を通常の v2 envelope に包めます。
3. `artifact_admission.py:987-1116` は v2 activation、build admission、WAL topology を検査しますが、非認証 marker を拒否しません。
4. `artifact_admission.py:843-865` で current 25-path map と一致すれば E1 になります。
5. `artifact_admission.py:1164-1172` が `CertifiedCampaignView` を発行します。

これは「authority の付け替えだけで昇格」に該当します。

現行 pipeline のままならさらに容易です。`pipeline.py:1481-1488,1547-1556` が COMMIT に `contract_sha256` と verifier receipt を残すため、WAL を変えず v2 envelope だけ付け直せます。

非認証 COMMIT から `contract_sha256` を省けば、v2 包装直後は `wal.py:1116-1147` が拒否します。しかし同 field の付け戻しで通るため、D1038 の「field の除去や付け替えで昇格できる作り」に該当します。別 terminal stage だけにしても、stage の置換経路が残ります。

### certified consumer の全経路

本番コードの certified 読取口は次の4系統です。

#### A. campaign path から `CertifiedCampaignView` を得る経路

直接または `replay.discover_campaign_dir()` 経由の全 call site は以下です。

- `autonomous_trial_completeness.py:4419-4427,4890-4898,4937-4946`
- `backoff_extended_sweep_report.py:457-464`
- `backoff_overthrottle.py:141-151`
- `backoff_sweep_report.py:52-65`
- `layer3_report.py:657-675`
- `p3_autonomous_workload_trial.py:3088-3095`
- `p3_b4_closed_critic.py:727-740,1732-1741`
- `p3_s4_loop.py:1510-1518,1718-1726`
- `p3_s4_loop_sort.py:502-510,691-699`
- `p3_s4_loop_trigger_gating.py:1032-1040`
- `p3_s4_red.py:187-196`
- `replay.py:115-151,179-211`
- `s6_sort_sweep.py:472-482`
- `s8a_trigger_sweep.py:574-584`
- `critic/digest.py:1576-1585`

共通述語は次です。

- admission status: `artifact_admission.py:1148-1157`
- certified purpose の E1/current-map 要求: `artifact_admission.py:843-865`
- sealed constructor token: `artifact_admission.py:333-361,1164-1172`
- exact view type: `artifact_admission.py:1197-1203`

ただし前述の v2 再包装で中央 gate 自体が view を発行するため、全 call site が同じ未閉鎖経路を共有します。

#### B. lock-only certified epoch 経路

- `s1_report.py:379-395`
- `s8b_oracle_report.py:548-564`

述語は `artifact_admission.py:843-865,868-891` です。v1/E0 は拒否しますが、非認証 identity の v2 再包装は拒否しません。

#### C. 既発行 view を受け取る経路

- `p3_s4_loop.py:482-489,558-578`
- `s6_sort_sweep.py:438-445`
- `s8a_trigger_sweep.py:540-547`
- `artifact_admission.py:1197-1203`

exact `CertifiedCampaignView` 以外は拒否する点は閉じています。しかし中央 gate が再包装 artifact に対して正規 view を発行できるため、入口全体としては閉じません。

#### D. verifier receipt まで再検証する経路

- `replay.py:184-211`
- `verifier/commit_receipt.py:368-419`

ここは exact view、view 内の exact COMMIT record、lock hash、WAL hash、variant、terminal payload を束縛します。v2 再包装で lock hash が変われば receipt 検証は失敗します。

ただし他の certified consumer は必ずしも `admit_replay_evidence()` を呼びません。例えば `s6_sort_sweep.py:438-469` と `s8a_trigger_sweep.py:540-571` は view 内の stage payload を直接射影します。したがって D 系統だけが閉じても全数閉鎖にはなりません。

### historical consumer は昇格経路ではない

次は明示的な `HISTORICAL_RAW` consumer です。

- `layer3_report.py:472-503`
- `critic/digest.py:684-706`
- `critic/online_digest.py:42`
- `tools/plotting/plot_backoff.py:269`
- `tools/plotting/plot_s1_9pair.py:557`
- `p2_2_report.py`

Layer 3 を certifying use にする際は `layer3_report.py:657-675` で certified admission を再実行します。ただし、その再実行も上記 v2 再包装の穴を共有します。

### campaign ID への影響

現行計算は次の通りです。

- `ident.py:150-177`: exact 5 key の canonical JSON
- `ident.py:180-189`: SHA-256 先頭8桁
- `campaign_lock.py:16-18,154-166`: lock identity も同じ exact 5 key

したがって以下は確定です。

- authority class を top-level 6 key 目として足すと、既存 campaign ID はすべて変わり、現行 lock codecにも拒否されます。
- `search_config` へ全 campaign 共通で足しても、既存 campaign ID はすべて変わります。
- 変わらない代替は、`CampaignConfig` に default=`certified` を追加し、既定値は canonical preimage へ serialize せず、非認証 class だけ reserved `search_config` entry として serialize する方式です。

この代替なら既存 certified campaign の ID は不変です。ただし非認証化する現行 A-1 の ID は変わります。現行コードから得た A-1 ID は次です。

- write-heavy: `paper-story-a1-write-heavy-paired-fb4d1867`
- balanced: `paper-story-a1-balanced-paired-38177551`
- read-heavy: `paper-story-a1-read-heavy-paired-e8aab893`

2026-08-26 study の durable measurement base は現在存在せず、repo 内にも同 study の測定 campaign はありません。2026-08-24 の v2 result は別 study、別 schema、別 ID です。

よって「既存 artifact の ID を変えない」は条件付き serialization で満たせますが、昇格不能性は満たせません。

### `declared_use_class` との関係

再利用すべきという反論は成立しません。

- `paper_story_a1_paired.py:65` は `"exploration"`。
- `loop.py:249-262` は official/exploration の path selector と明記しています。
- `layout.py:450-458,589-597` も出力 root を選ぶだけです。
- `pipeline.py:1071-1099` では build materializer と official toolchain 要求に使います。
- `test_campaign.py:9661-9685` は official と exploration で campaign ID が同一になることを固定しています。
- `CampaignLayout` と `ExplorationCampaignLayout` が別型でも、`artifact_admission.py:563-568` は任意の path を `CampaignLayout` に戻して読めます。

したがって `declared_use_class` を `"noncertifying"` に拡張しても、文字列の付け替えで official にでき、consumer authority にはなりません。保存先の選択には再利用可能ですが、昇格不能性の根拠にはできません。

## 2. A-1 acquisition receipt の完全契約

### top-level field

`paper_story_a1_paired.py:916-1050` と job body `paper_story_a1_paired.sh:107-284` の合成です。

| field | 必須述語 |
|---|---|
| `schema_version` | exact `paper-story-a1-paired-submission/v1` |
| `route` | exact `"direct-qsub"` |
| `study_id` | exact `paper-story-a1-20260826-sized-v1` |
| `source_commit` | submit 時の clean HEAD。job の `IZANAGI_EXPECTED_HEAD` と一致。qsub 前に full 40 lowercase hex を要求 |
| `attempt_root` | canonical absolute、policy の durable base の直下1 child、安全な basename。repo 外、`/scr` 外。job の最初の検証時には未存在、driver 検証時には real directory かつ非 symlink |
| `request_id` | qsub stdout から NQSV sentence 優先、単一 token fallback で抽出。末尾 `.` と先頭 `0:` を正規化し、安全 regex に一致。`PBS_JOBID` と一致 |
| `submission_receipt_path` | `<base>/<attempt>.submission.json` と exact 一致 |
| `completion_receipt_path` | `<base>/<attempt>.completion.json` と exact 一致 |
| `qsub_argv` | `_canonical_qsub_contract()` が返す完全一致の argv |
| `qsub_options` | `v`, `variables`, `o`, `e` の値を含め canonical contract と object equality |
| `submit_observation` | 下表の exact 6 field |

`qsub_argv` の形は `paper_story_a1_paired.py:846-879` で固定されています。

```text
qsub -v <variable_text>
     -o <base>/<attempt>.stdout
     -e <base>/<attempt>.stderr
     <repo>/tools/pegasus/paper_story_a1_paired.sh
```

`qsub_options.variables` の exact 6 field と値は次です。

| variable | 値 |
|---|---|
| `IZANAGI_EXPECTED_HEAD` | clean source HEAD |
| `IZANAGI_A1_STUDY_ID` | `STUDY_ID` |
| `IZANAGI_A1_ATTEMPT_ROOT` | durable base 直下の nonce child |
| `IZANAGI_A1_ACQUISITION_RECEIPT` | sibling `.submission.json` |
| `IZANAGI_A1_COMPLETION_RECEIPT` | sibling `.completion.json` |
| `IZANAGI_SUBMISSION_NONCE` | `attempt_root.name` |

`v` は上記順序の `key=value` を comma join した exact string です。`o/e` は sibling stdout/stderr path です。

### `submit_observation`

| field | 必須述語 |
|---|---|
| `submit_host` | non-empty exact str、制御文字なし。job の `PBS_O_HOST` と一致 |
| `qsub_stdout` | UTF-8 str。request ID が NQSV sentence または単一 token として一意に抽出可能 |
| `qsub_stdout_sha256` | `qsub_stdout.encode("utf-8")` の SHA-256 |
| `qsub_stderr` | exact empty string |
| `qsub_stderr_sha256` | empty bytes の SHA-256 |
| `qstat_visibility` | 下表の exact 5 field |

### `qstat_visibility`

| field | 必須述語 |
|---|---|
| `request_id` | receipt request ID と正規化後に一致 |
| `visible` | exact `True` |
| `state` | exact str かつ `ARR/WAI/QUE/PRR/RUN/POR/EXT/HLD/HOL/SUS/MIG/STG` のいずれか |
| `queue` | exact `"gen_S"` |
| `observed_epoch` | bool でない正の exact int |

さらに job 側 PBS observation は exact 3 fieldです。

- `pbs_jobid`
- `pbs_o_host`
- `pbs_o_workdir`

`paper_story_a1_paired.py:882-913` により、request ID、submit host、repo realpath と交差束縛されます。

## 3. job body が要求する環境変数

### qsub/PBS から入る必須値

| 変数 | 作り方 |
|---|---|
| `PBS_JOBID` | scheduler。安全な NQSV request ID |
| `PBS_O_HOST` | scheduler。submit login host |
| `PBS_O_WORKDIR` | scheduler。submitter が `cd "$REPO_ROOT"` して qsub した cwd |
| `IZANAGI_A1_STUDY_ID` | fixed `STUDY_ID` |
| `IZANAGI_EXPECTED_HEAD` | qsub 前の clean full HEAD |
| `IZANAGI_A1_ATTEMPT_ROOT` | policy durable base / unique nonce |
| `IZANAGI_A1_ACQUISITION_RECEIPT` | sibling `<nonce>.submission.json` |
| `IZANAGI_A1_COMPLETION_RECEIPT` | sibling `<nonce>.completion.json` |
| `IZANAGI_SUBMISSION_NONCE` | attempt child basename |

`TMPDIR` は `/scr` が存在しない場合だけ dependency scratch parent の fallback として必要です。receipt 検証後は job が `attempt/raw/tmp` に上書きします。

### job が内部で導出して export する値

- `TMPDIR = <attempt>/raw/tmp`
- `IZANAGI_EXPLORATION_OUTPUT_ROOT = <attempt>/raw/campaign-output`
- `IZANAGI_RESERVATION_JOB_ID = PBS_JOBID`
- `IZANAGI_RESERVATION_REQUESTED_S` = job body の唯一の `#PBS ... elapstim_req=HH:MM:SS` から秒換算
- `IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH` = `qstat -f` の start 値
- `IZANAGI_RESERVATION_DEADLINE_EPOCH` = start + requested seconds
- `IZANAGI_RESERVATION_HOST` = qstat assigned host と `hostname`/`hostname -f` の exact 一致値
- `IZANAGI_RESERVATION_BOOT_ID` = `/proc/sys/kernel/random/boot_id`
- `IZANAGI_RESERVATION_SCRIPT_SHA256` = tracked job body SHA-256
- `IZANAGI_RESERVATION_NONCE` = submission nonce

terminal writer の Python blockだけに渡す一時環境変数は次の4つです。

- `IZANAGI_A1_TERMINAL_DRIVER_RELATIVE`
- `IZANAGI_A1_TERMINAL_POLICY_RELATIVE`
- `IZANAGI_A1_TERMINAL_PIPELINE_RELATIVE`
- `IZANAGI_A1_TERMINAL_JOB_RELATIVE`

また `PATH` から `qstat`, `timeout`, `git`, `sha256sum`, `hostname`, Python 3.10+、`cmake`, `gcc`, `g++` を解決できる必要があります。

## 4. 既存 submitter 8 本との比較

| submitter | qsub の cwd | request ID | qstat | fail-closed 特性 |
|---|---|---|---|---|
| `submit_b10_backoff_grid.sh:163-182` | caller cwd、absolute job path | command substitution、non-empty のみ | なし | qsub rc を failed event に残す。fan-out 途中失敗では先行 job は残る |
| `submit_b10_backoff_shape.sh:213-294` | `REPO_ROOT` | NQSV regex / single-token | 3回、exact ID | receipt を `"x"` で作成。A-1 の通常系に最も近い |
| `submit_certify.sh:175-242` | caller cwd | NQSV regex / single-token | なし | qsub rc を記録し、非zeroなら receipt を書かない |
| `submit_floor.sh:627-718` | `REPO_ROOT` | NQSV regex / single-token | なし | create-only receipt。後段 evidence index 失敗は警告のみ |
| `submit_mocc_trace.sh:264-414` | caller cwd、absolute job path | NQSV regex / single-token | なし | qsub rc 非zeroで停止、receipt `"x"` |
| `submit_oracle_n_pilot.sh:334-346` | `REPO_ROOT` | 解析しない | なし | qsub stdout/stderr を保存する診断 wrapper。A-1 receipt producer の先例には弱い |
| `submit_silo_ladder_rung1.sh:403-510` | `REPO_ROOT` | NQSV regex / single-token | rc を確認 | campaign root receipt と submit receipt を create-only publication |
| `submit_t126_qualification.sh:450-805` | `REPO_ROOT` | strict qsub binding producer | exact ID | qsub 前 invocation claim、crash boundary、再送禁止、atomic publicationを持つ最強の先例 |

A-1 用は `submit_b10_backoff_shape.sh` の immediate qstat と、`submit_t126_qualification.sh` の invocation claim/crash fail-closed を組み合わせるべきです。相違点は、qsub 後60秒以内に job-consumed acquisition receipt を公開しなければ job が自律拒否することです。

### 所有解除後の A-1 投入器 plan

- 新規 `tools/pegasus/submit_paper_story_a1_paired.sh`
  - repo realpath、Pegasus login site、clean HEAD、job/driver/policy tracked bytesを qsub 前に検査。
  - policy の durable base を安全に provision。
  - nonce と attempt topology を決め、attempt root、receipt、completion、stdout、stderr が全て未存在であることを確認。
  - 4 preflight (`qstat -Q`, `pegasusinfo`, `rbudgetcheck`, `check_quota`) を生 capture。1件でも非zeroなら qsub しない。
  - qsub invocation claim を receipt より先に create-only 作成し、同 nonce の自動再送を禁止。
  - `(cd "$REPO_ROOT" && qsub ...)` を1回だけ行う。
  - qsub rc、stdout、stderrを保存。rc 非zero、stderr 非空、request ID 不定なら acquisition receipt を作らない。
  - `qstat -f` で exact request ID、state、queueを確認。
  - `paper_story_a1_paired.py` の producer API で receipt object を再構築し、atomic create-only publish。
- `paper_story_a1_paired.py:316-357,835-1050`
  - qsub出力とqstat出力の producer parserを追加。
  - `_canonical_qsub_contract()` を producer/validatorの単一正本として共有。
  - receipt builder は exact field closureを組み立てる。
  - CLI は submitterから capture fileを受け、receiptだけを発行する。qsub自体はしない。
- `test_paper_story_a1_job_contract.py:124-635,881-1045`
  - producerとjob validatorの round-trip。
  - qsub rc、stderr、request parser、qstat state/queue、cwd、host、path topology、既存 receipt raceの負例。
  - job bodyが qsubを含まない既存検査は維持。
- `test_paper_story_a1_paired.py:585-652,2019-2087`
  - estimand、policy、arm/workload、凍結値を変えていないことを維持。

## 5. create-only の実装上の意味

`paper_story_a1_paired.py:431-466` の現在の helper は最終 path を次で直接 open します。

```text
O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW
mode 0600
```

これは上書き防止にはなりますが、A-1 acquisition receipt には不十分です。job は path の出現直後に読むため、writer が書込途中の final file を読んで拒否する race が残ります。

A-1 producer は次の方式にすべきです。

1. durable parent を `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` で開く。
2. sibling temp を `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0600` で開く。
3. write loop、`fsync(temp_fd)`、close。
4. 同じ parent dir fd 内で `link(temp_name, final_name, follow_symlinks=False)`。
5. temp を unlink、parent dirを `fsync`。

race の意味は次の通りです。

- final が regular file、symlink、その他何であれ既に存在すれば `link` は `EEXIST`。既存 bytes は不変。
- 同じ final に2 writerが競合すると1 writerだけが link に成功し、敗者は `EEXIST`。
- write/fsync 前の失敗では final は出現しないため、job は60秒後に拒否。
- link 後の reader は完成済み bytes だけを読む。
- link 後、temp unlink 前に crash しても final は完成済み。temp hard link が残るだけである。
- `os.replace()`、`rename()` の上書き可能経路、最終 path の直接 truncate open は create-only と呼ばない。

## 6. B-057 変異候補

非認証型は現在の所有条件では実装不可なので、schema/consumer の仮想 mutant は候補に挙げません。現コードと上記 submitter設計から、前後に同じ入力を拒否する層がないものだけを残すと次です。

| ID | 位置 / operator | 前後に重複 gate がない根拠 | 第一失敗 assert |
|---|---|---|---|
| M-CERT-OVERALLOW | `ident.py:239` の `verify_ratified_contract_loader_binding()` を除去 | capture/live check は批准集合を見ず、その後は lock 作成へ進む。`ratified_enforcement_source` fixture は opt-in (`conftest.py:194-236`) | 未批准 certified lock 作成が `IdentityMismatch` にならない。**承認外の過剰許容を検出する必須負例** |
| M-SUB-QSUB-RC | 新 submitter の qsub rc gateを無効化 | submission receipt schemaには qsub rc fieldがなく、後段は非zero qsubを再判定できない | qsub stub rc=23で qstat/qsub receipt writer が呼ばれる |
| M-SUB-PREFLIGHT | 4 preflightのどれかの失敗を無視 | acquisition receiptに preflight fieldはなく、job bodyも login側budget/quota失敗を再判定しない | 対象 capture rc非zeroなのに qsub call countが1 |
| M-SUB-NOREPLACE | final publicationを `link` から `os.replace` に変更 | 既存 final が新しい有効 receiptに置換されればjob validatorは受理し、後段拒否はない | preexisting sentinel bytesが変化、または publishが成功 |
| M-SUB-DUPLICATE-QSUB | invocation claimの `O_EXCL` を除去 | receiptは request IDを1件しか束縛せず、二重qsub全体を検出する後段台帳がない | 同 nonce の2回目実行で qsub counterが2 |

次は候補から除外します。

- qstat state/queue gateの弱化
- qsub stderr gateの弱化
- canonical argv/options gateの弱化
- request ID normalizationの弱化
- source HEAD/clean gateの弱化

いずれも job body または `validate_acquisition_receipt()` が同じ入力を再拒否するため、赤理由を1つに帰属できません。

## 7. 編集面の所有分割

親 brief の明示 production file は字面上は素集合です。しかし「対応 test」が未指定で、A-1 identity integration は既存 `test_paper_story_a1_paired.py` に集中しているため、現在の記述だけでは所有が素集合と証明されていません。

さらに4層を本当に閉じるには単位Aへ次を追加する必要があります。

- `campaign_lock.py`
- `wal.py`
- `artifact_admission.py`

このうち前二者の一部、特に `campaign_lock.py` と `artifact_admission.py` は現在の禁止面です。

所有解除後の正しい分割は次です。

- 単位 A: `model.py`, `ident.py`, `campaign_lock.py`, `wal.py`, `artifact_admission.py`, `pipeline.py`, 新規 `test_noncertifying_campaign.py`, `test_campaign.py` の identity回帰
- 単位 B: `paper_story_a1_paired.py`, 新規 submit script, `test_paper_story_a1_job_contract.py`, `test_paper_story_a1_paired.py`
- 実行順: Aをland可能な形にしてからB。BはAの型を使用するが、file ownershipは重ならない。

現在は単位Aが禁止面と衝突するため開始不可です。D1028 により単位Bだけの先行も不可です。

## 静的検査

Web検索、pytest、書込みは行っていません。

実施した読取専用検査は以下です。

- 必読10 Python fileの `ast.parse`: 終了コード0
- job bodyと既存 submitter 8本の `bash -n`: 終了コード0
- `CONTRACT_LOADER_RELATIVE_PATHS`: 25件、重複なし
- 現行A-1 campaign IDの純粋計算
- 2026-08-26 durable measurement baseの不在確認

テスト実走結果は報告していません。

## 総括

型は作れない。`campaign_lock.py` と `artifact_admission.py` の編集禁止を解除しない限り昇格経路が1本残るため、D1038/D1028に従いA-1投入器を含めて作らない。