結論として、Pegasus では rr50 の1点だけを、8本の独立 PBS request ×各5 rep で測る設計を採ります。各 request は fresh build と1セッションだけを所有します。ただし8本を同時投入する1ジョブ束は「事前登録済み時間窓」が1つなので、得られる aggregate CV は時間ドリフトを含まない下限です。新規 registered artifact には登録できますが、Pegasus の compare 用 between-run floor としては自動採用せず、`lower-bound-only` を刻みます。

静的読取りのみを行いました。ファイル編集・pytest・ジョブ投入はしていません。

## 確認済みの訂正

- brief の D138(f) 参照は現 HEAD では誤りです。`docs/decisions.md:6718-6803` の D138 は P6 帰納契約で、独立性規則を含みません。該当規則は D134(f) の `docs/decisions.md:6542-6544` です。以下は D19 と D134(f) を正本として設計します。
- 登録済み calibration は「飽和を観測した」のではなく、`saturated=false` のまま 4×L3 下限規則で 1M を選んでいます。`lower_bound_selected=true`、`records=1,000,000` は確認済みです（`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1603-1634`）。
- γ-16 の実際の対象一覧は `orchestrator/tests/test_env_contract.py:61-75` です。現状 `between_run_floor.py` は入っていません。
- 現行 driver の「high-abort ほど drift が大きい」という理由（`between_run_floor.py:14-19`）は、D134(b) の実測反証（`docs/decisions.md:6532-6536`）後は使えません。

## 1. `between_run_floor.py` の env パラメタ化

### 変更内容

`orchestrator/campaign/between_run_floor.py` を次の単位で組み替えます。

- `:1-29`
  - 「8個の独立セッション」という表現を削除し、sampling unit を PBS subcampaign、rep をセッション内反復と明記します。
  - same-window CV を真の floor と呼ばず、`same-submission-cohort lower bound` とします。
  - high-abort 単調性と rr95/D48 由来の説明を削除します。

- `:38-49`
  - `campaign.p2_2` からの `ENV_TAG/CLK/NUMA/RECORDS/THREADS/EXTIME/_assert_single_tenant` import を全廃します。
  - `campaign.env_contract.lookup`、`campaign.env_attestation.load_verified_calibration`、`campaign.execution_guard`、`calibrator.runner.composite_competing_probe` を使います。
  - certified Pegasus mode では shell が作った binary を受け取り、`:159-168` の driver 内 build は行いません。

- `:55-63`
  - 3点の catalog 自体は legacy 診断用に残せますが、certified profile が受理する点は rr50/skew0.9/rmw0 の1点だけにします。
  - `SESSIONS=8`、`SESSION_REPS=5`、`EXTIME=3` は env 定数にせず、hash 固定された測定 policy の値として検証します。
  - driver CLI から `records`、`threads`、`clocks_per_us`、`numactl` を上書きする引数は設けません。

- `:71-110`
  - `run_subcampaign(...)` は1回の PBS allocation で5 repだけを実行します。
  - `contract.clocks_per_us` と `contract.numactl` を使います。
  - `records` と `threads` は `contract.calibration_ref` の hash 検証済み calibration から取得します。Pegasus では `CalibrationV2.threads` と `saturation.records`、すなわち 48/1M です。
  - `measure_point(..., require_all_reps=True, require_complete_metrics=True)` を使用し、5件すべての throughput・return code を残します。
  - driver は raw throughput を出すだけにし、CV、中央値、利用可否は登録側 validator が再計算します。

- `:113-149`
  - 現行の `open(..., "w")` による上書きを廃止します。
  - legacy 出力も `"x"`/`O_EXCL` の create-only とし、Pegasus member は固有の bundle/member staging にだけ出力します。

- `:152-189`
  - CLI を `subcampaign` と `legacy-same-window` に分けます。
  - `--env-tag`、`--policy-json`、`--bundle-plan`、`--member-index`、`--member-nonce`、`--binary`、`--binary-sha256`、`--receipt-json` を必須にします。
  - env 未指定の暗黙な linux-baremetal fallback は置きません。未登録 env は `lookup()` で fail-closed にします。

### `RECORDS/THREADS/EXTIME` の所有

- `RECORDS/THREADS`: CLI 値ではなく、env ごとの hash-bound calibration が所有します。これは `env_contract.py:11-14` の「contract 自体は records/threads を持たない」という設計を維持します。
- `CLK/NUMA`: `lookup(env_tag)` の contract が所有します（`env_contract.py:168-193`）。
- `EXTIME=3`: calibration でも env contract でもなく、今回の測定 protocol policy が所有します。任意 CLI override は禁止します。

### linux-baremetal artifact の保護

既存 JSON は source commit や binary digest を内包していません。したがって完全な producer provenance は既存 schema からは確認不能です。一方、歴史 pin `dff0f1e` は `between_run_floor.py:21-25` と `p2_2.py:37-39` に記録されています。これを遡及的に補うため既存 bytes を変えてはいけません。

`orchestrator/tests/test_between_run_floor.py` で次の6 bytesを golden pin します。

- rr50 JSON `4040eda140572ea0f79d1b16854fc1db84ed18b2de13d7eacdde25ce45971dc8`
- rr50 MD `6490c7f13cf35ddceecef5ee005e8021bd1552c559fb87d30fe951c6df666d36`
- rr5 JSON `200ab13614344769bbceaa4f7efe8c4411c4f6d764b3a5c036b77036498b9a11`
- rr5 MD `07143b78e2835fd7424b75a3d0c75475a4b2ef113e4cc9fdbeae7d67f1e8cc31`
- rr95 JSON `a6d1657885b2c855a797b71b8565e6c21d282bfb62c94395884b4ba1eac555c5`
- rr95 MD `9b9e69e44944d3b9ba674482fed1798854c88f273c99a8a2864b876e438f617b`

### γ-16

`orchestrator/tests/test_env_contract.py:61-75` の `V2_ENV_NEUTRAL_MODULES` に以下を追加します。

- `orchestrator/campaign/between_run_floor.py`
- 新規 `orchestrator/campaign/between_run_floor_registry.py`

両ファイルには `"pegasus"`、`"linux-baremetal"`、1800、2100、`--interleave=all` を直接書かず、contract/policy から受けます。`env_contract.py:212-257` 自体は変更しません。

## 2. 動作点

採る点は1点です。

```text
baseline = silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,
           NO_WAIT_OF_TICTOC=0,WAL=0
workload = skew=0.9 / rratio=50 / rmw=0
records  = 1,000,000
threads  = 48
```

根拠は以下です。

- 登録済み calibration が binding を持つ唯一の workload です（登録 artifact `:1685-1690`）。
- current CCBench pin は `pin.py:28` の `d706650` で、登録 artifact の full head `:40` と現在の gitlinkが一致しています。
- rr5 の追加理由だった high-abort 単調性は D134(b) により反証済みです。
- rr95 は別目的の D48 reconnaissance 由来で、Pegasus には records=1M の workload-specific calibration 証拠がありません。

現行 driver は1点あたり `10 + 8×5 = 50` rep、3点で150 repです。新設計は8 request ×5 rep = 40 repだけで、各5 repから within-run CV と session median の双方を算出します。3点化はレコード数そのものの規律4違反ではありませんが、calibration binding と利用目的のないまま測定量を3倍にするため、brief の bounded wave と規律4の趣旨に反します。

## 3. Pegasus 実行資材

兄弟 job script は作らず、既存の `certify_calibration.sh` を exact profile 分岐で再利用します。新設する兄弟はログイン側の bundle submitterだけです。

### `tools/pegasus/certify_calibration.sh`

- `:35-45`
  - `IZANAGI_MEASUREMENT_PROFILE` を `calibration` / `between-run-floor` の閉じた enum として検証します。
  - default は既存 `calibration`。任意 argv や任意 driver path は受け付けません。
  - floor profile では bundle/member 固有 staging root を選びます。

- `:168-215`
  - submit receipt の既存 commit/script/request binding に、`profile`、`bundle_id`、`bundle_plan_sha256`、`member_index`、`member_nonce`、`policy_sha256` の一致検査を追加します。

- `:495-525`
  - fresh worktree、`-DCCBENCH_TRACE=0`、`nm` trace-symbol 検査は変更せず再利用します。
  - request ごとに fresh buildするため、8 sampling unitは別 buildを持ちます。

- `:589-620`
  - calibration の既存 walltime 式はそのまま残します。
  - floor profile は `cooldown_max + 5×bench_timeout + build_cap + finalize_reserve` の別式を policy から検証します。

- `:718-744`
  - calibration profile の現行 `calibrate_argv` は byte-for-byte同じ要素列を維持します。
  - floor profileだけ次の exact arrayを生成します。

```text
python3 orchestrator/campaign/between_run_floor.py subcampaign
  --env-tag <policy.env_tag>
  --policy-json ...
  --bundle-plan ...
  --member-index ...
  --member-nonce ...
  --binary ...
  --binary-sha256 ...
  --receipt-json ...
```

`tools/pegasus/exec_calibrate.py:12-44` は任意の文字列配列を exec できるため、外部入力から argv JSON を渡さず、この shell 内の閉じた profile 分岐だけが配列を構築します。同ファイルは変更しません。

- `:746-769`
  - floor profile用の `driver_rc`、member artifact hash、pre/post probe hashを job-result に追加します。
  - calibration profile の `pegasus-job-result/v1` は維持します。

### `tools/pegasus/submit_certify.sh`

- `:5-30`: `--profile`、bundle/member binding を追加。default calibrationは維持。
- `:50-80`: profile ごとの policy と walltimeを選択。
- `:82-103`: clean source、job script hashに加えて policy・bundle plan hashを固定。
- `:110-170`: pre-submit receiptへ profile/bundle/memberを追加。
- `:177-244`: qsub exportへ同じbindingを渡し、submit receiptへ保存。

### 新規 bundle submitter

`tools/pegasus/submit_between_run_floor.sh`（新規・予定行）:

- `:1-55`: clean source、policy、script、submitter、`exec_calibrate.py` の hashを取得し、bundle nonceと8個のmember nonceを事前生成。
- `:56-95`: canonical bundle planを create-only で書き、全8 memberの index/nonceを qsub 前に凍結。
- `:96-155`: `submit_certify.sh --profile between-run-floor` を index 0〜7について1回ずつ呼ぶ。
- `:156-205`: 成功した request ID、失敗 index、submit時刻を bundle submission receiptへ create-only で書く。
- 途中の qsub 失敗時は replacement/job 9を投入せず、partial bundleとして終了します。

`tools/pegasus/policies/between_run_floor_v1.json`（新規・予定 `:1-18`）には env tag、rr50 workload、member_count=8、reps=5、extime=3、within CV threshold=0.05、walltimeだけを置きます。records/threads/clock/NUMAは置きません。

### script bytes pin の検索結果

現 HEAD の SHA-256 は次の通りです。

- `certify_calibration.sh`: `7e5c1394921b9f335b9924b464bfbad2d5c44e73893d6a213468248c2ef916b0`
- `submit_certify.sh`: `d759a5955dff165ad6dcea362ed8eee5a7a4a6dc6583931a6662601a88390603`
- `exec_calibrate.py`: `6cd7baf94929d6960618653d566b83c14e5ac0174fbc0af7d5b1533f94cc3990`

現在の script digestを literal goldenとして固定するテストは見つかりませんでした。生産・消費経路は次の通りです。

- producer: `submit_certify.sh:92,134-170,215-240`
- job-side consumer/check: `certify_calibration.sh:181-215`
- acquisitionへの伝播: `certify_calibration.sh:563-632`
- schema consumer: `orchestrator/calibrator/schema_v2.py:392-416,508,558-573`
- 既存登録 artifact は当時の script hash `4b50b998…0911` を `:43` に保持

したがって script変更は既存登録 bytesを変えません。ただし旧bytesで投入済み・未開始のrequestは job-side照合で失敗します。実装を land する時点に in-flight certify request がないことは実行前停止条件です。

### `submit_floor.sh` 系

`tools/pegasus/floor_campaign.sh:894-897` と `tools/pegasus/submit_floor.sh` は S8b official floor用なので使いません。`orchestrator/campaign/s8b_floor_campaign.py:197-214,3472-3479` は無変更です。

## 4. 独立性の設計

### 独立単位

1本の PBS requestを1 subcampaignとし、以下をその単位に閉じます。

```text
1 PBS request
  └─ 1 fresh allocation
      └─ 1 fresh trace-disabled build
          └─ rr50 の5 rep
              ├─ 5 throughput → within-run CV
              └─ median 1値 → aggregate用 session median
```

したがって規模は以下です。

- allocation/subcampaign候補: 8
- session median: 8
- rep: 40
- repを独立単位として数えない
- 単一allocation内で8セッションを回さない

### cluster の数え方

D134(f) に従い、artifactには別々に次を記録します。

- allocation count: 完了・検証済み PBS request数
- node cluster: `(hostname_observed, boot_id)` の一意数
- time-window cluster: 事前登録した submission cohort数
- joint cluster: `(node_cluster, time_window_cluster)` の一意数

今回の bundle planは「8 requestを一度に投入する1 cohort」なので、time-window clusterは事前に `1` と固定します。schedulerの遅延で開始時刻が偶然離れても、結果を見て後から別時間窓へ昇格させません。

D134 `:6552-6554` は、必要 cluster数は効果量と検出力なしには決められないとしています。今回それらは裁定されていないため、8 requestを「十分な n」とは認定できません。

### artifactへ残す独立性証拠

各 member receipt に次を必須化します。

- bundle ID、member index/nonce
- qsub request ID、PBS_JOBID
- submit epoch
- qstatが返したscheduler開始時刻とraw qstat hash
- driver測定開始・終了のUTCとepoch
- assigned host、observed hostname、`/proc/sys/kernel/random/boot_id`
- source commit、CCBench head、job script/policy/binary/calibration hash
- pre/post strict attestation receipt
- pre/post composite pgrep receipt
- 5 throughput、return code、session median、within-run CV
- scheduler stdout/stderr/accountingのpath・size・SHA-256

`tools/pegasus/collect_receipt.py:107-206` に profile別の厳密な floor branchを追加し、submit/acquisition/job-result/member/scheduler logのID・hashを突き合わせます。既存 calibration branchは変更しません。CLI `:209-235` に `--profile` を追加します。

### 得られる量の名乗り

全8 memberが汚染なく完了した場合でも、登録 artifact は次のように記録します。

```json
{
  "estimand": "same-submission-cohort allocation-session-median CV",
  "evidence_class": "lower-bound-only",
  "independence": {
    "allocation_units": 8,
    "time_window_clusters": 1,
    "repetitions_are_independent_units": false
  },
  "assessment": {
    "between_run_compare_floor": {
      "status": "not-established",
      "reason": "single-precommitted-time-window-cluster"
    }
  }
}
```

CVそのものは `raw_session_median_cv` とし、compare用 `noise_cv` には配線しません。実際の複数時間窓を取るには2束目以降と標本数裁定が必要なので、brief の「足りなければ拡大しない」に従い裁定へ返します。

member欠落、pgrep失敗、attestation失敗、rep欠落がある場合は final registered artifactを作りません。raw partial bundleだけを残し、同じwave内で補充しません。

## 5. 登録経路

calibration/v2 は `orchestrator/calibrator/schema_v2.py:623-634` で within-run noise schemaを持つため、between-run artifactを詰め込みません。

### 新規 registry module

`orchestrator/campaign/between_run_floor_registry.py`（新規・予定行）:

- `:1-85`: `between-run-floor/v1`、bundle plan、member、assessmentのexact-key schema
- `:86-205`: calibration/env/workload/records/threads/job ID/hash/node/timeのcross-validation
- `:206-295`: raw throughputから各median/CV、aggregate CV、cluster数、2用途のassessmentを独立再計算
- `:296-365`: canonical serialization、digest、atomic create-only publish
- `:366-410`: `validate` / `register` CLI

producerが書いた `usable` や `cluster_count` を信用せず、raw receiptからvalidatorが再計算します。これは `docs/decisions.md:6518-6521` の自己申告禁止に従います。

### ファイル名とdigest

登録先:

```text
output/env/<env-tag>/calibration/registered/
  between-run-floor-<sha256先頭16桁>.json
```

bytesは次の一意な形式にします。

```python
json.dumps(
    artifact,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8") + b"\n"
```

この最終bytes全体のSHA-256を取り、先頭16桁を名前に使います。完全digest、target名、publish methodはbundle staging側の `publish.json` に保存します。artifact内への自己参照hashは置きません。

publishは `orchestrator/calibrator/cli.py:271-316,613-639` と同じく、一時ファイルの `O_EXCL`、fsync、`renameat2(RENAME_NOREPLACE)`、非対応時のみhardlink fallbackとします。既存targetがあれば同一bytesでもcollisionとして停止します。`latest`、symlink、mutable indexは作りません。

### 既存 calibration の不可侵

以下は変更しません。

- `env_contract.py:189,191`
- `test_env_contract.py:231-243`
- `test_env_contract.py:640-653`
- `test_s8b_floor_campaign.py:3231-3243`
- `calibration-753f535a8d024727.json` の全bytes
- `p2_2.py:50-62` の既存 floor値とそのconsumer

新prefixは `calibration-*.json` と衝突せず、`env_contract.calibration_ref` も動きません。

## 6. 単独性確認

`p2_2._assert_single_tenant` の下位実装は正しいです。

- strict pgrep分類: `orchestrator/calibrator/runner.py:116-168`
- path非依存パターン `ycsb_.*\.exe`: `:171-203`
- visibility canary込みの composite probe: `:221-297`
- 登録済みPegasus profileも `hidepid=0`、host PID namespace共有を確認済み: calibration artifact `:1562-1566`

ただし現在の driver の呼出し位置は不十分です。

- `between_run_floor.py:159` はbuild前なので、測定直前確認ではありません。
- `stability.between_run_noise_floor:121-124` は2セッション目以降だけ settle/probeを呼びます。
- `measure_point:396-500` 自身はpgrepしません。

各 subcampaignでは次の順序を固定します。

1. static attestation
2. `calibrator.cli.cooldown_gate`（現行 certified path `cli.py:521-533` と同じ）
3. `execution_guard.attest_and_build_receipt` による strict pre-attestation
4. `composite_competing_probe`を実行し、canary visibilityと競合なしを記録
5. 5 repを連続測定
6. composite pgrep post-probe
7. strict post-attestation
8. member artifactをcreate-onlyで確定

これで裁定の「計測前にノード上で pgrep」を満たします。pre/post間だけ出現して消えた一過性プロセスまでは検出できないため、その限界もschema reasonとして記録します。

## 7. テスト

| ファイル | pinする内容 |
|---|---|
| `orchestrator/tests/test_between_run_floor.py:1-97` を拡張 | env lookup、calibration由来の1M/48、CLI override不在、certified rr50のみ、pre-probe→5rep→post-probe順、trace/binary hash検査、legacy 6 artifact hash、create-only |
| `orchestrator/tests/test_env_contract.py:61-75,691-704` | driverとregistryをγ-16対象へ追加し、env literal注入mutationを殺す。既存Pegasus golden値は不変 |
| 新規 `orchestrator/tests/test_between_run_floor_registry.py` | exact schema、8 member集約、重複/missing/mixed env・calibration・binary拒否、repをclusterに数えないこと、lower-bound判定、canonical digest、create-only collision |
| `orchestrator/tests/test_pegasus_tools.py:953-1087` 付近を拡張 | calibration default argvの回帰、floor profileの閉じたargv、bundle/member binding、8 qsub dry-run、partial qsub失敗で補充しないこと、script hash chain、S8b driverを呼ばないこと |
| `tools/pegasus/collect_receipt.py` 対応テストを同上へ追加 | floor job-result/member/scheduler receiptのID・hash cross-check、calibration branch不変 |
| 既存 `orchestrator/tests/test_s8b_floor_campaign.py` | 変更しない。既存calibration hashとofficial guardの回帰テストをそのまま利用 |

実装後の静的確認は `bash -n`、`python3 -m py_compile`、旧artifactの `sha256sum` 比較を先に行います。pytestは親が `tools/run_tests.py` 経由で計算ノードにdispatchします。完了時は関連テストに加えて `tools/check_codex_agents.py`、`tools/check_docs.py`、commit後の provenance監査が必要ですが、ここでは緑を主張しません。

## 8. 段取りと所有分割

最初に親が schema、CLI、policy、bundle/member receipt interfaceを短い設計メモとして凍結し、その後だけ並列化します。

| 実装子 | 排他的に所有するファイル |
|---|---|
| A: driver/env | `orchestrator/campaign/between_run_floor.py`、`orchestrator/tests/test_between_run_floor.py`、`orchestrator/tests/test_env_contract.py` |
| B: schema/登録 | 新規 `orchestrator/campaign/between_run_floor_registry.py`、新規 `orchestrator/tests/test_between_run_floor_registry.py` |
| C: Pegasus transport | `tools/pegasus/certify_calibration.sh`、`tools/pegasus/submit_certify.sh`、新規 `submit_between_run_floor.sh`、新規policy、`tools/pegasus/collect_receipt.py`、`orchestrator/tests/test_pegasus_tools.py`、`tools/pegasus/README.md` |
| 親/integration | `docs/pegasus-runbook.md:443-521`、台帳spool fragment、実測artifact、registered publish、必要なphase完了チェック |

実行順は次です。

1. A/B/Cを静的統合し、旧bytes・official guard・calibration default branchを確認。
2. `submit_between_run_floor.sh --dry-run` で8 member planとargvを検証。
3. in-flight certify jobなし、clean source、quota/preflightを確認。
4. bundle submitterを1回だけ実行し、8 requestを投入。
5. 全request終了後、8 final receiptを収集。
6. 全memberが構造的に有効なら lower-bound artifactをcreate-only登録。欠落なら登録せず裁定返し。
7. 「使用規模」「within-run品質用途」「between-run採否用途」「node/time cluster数」をspool fragmentへ記録。

未確認事項は、実際に割り当てられるnode数、開始時刻の分散、投入時点のquota、各jobでのpgrep/attestation通過です。現行 policy上の要求上限は1 node ×2時間 ×8 request = 16 node-hoursですが、Pegasusポイントへの換算単位と投入時残高は静的コードだけでは確定できません。

## 総括

採る設計は、Pegasus登録済みcalibrationと完全一致するrr50の1点を、8本のPBS requestへ1セッションずつ分け、各requestでfresh trace-disabled buildと5 repを行うものです。records/threadsはhash検証済みcalibration、clock/NUMAはenv contract、extime/reps/member数はhash固定policyから取得します。8 session medianのCVは同時投入cohortの下限として新schema・新prefixでcreate-only登録し、時間分離されたcompare用floorとしては配線しません。

1ジョブ束への判定は、機械的な計測規模としては収まります。40 rep、最大要求16 node-hoursです。ただしquota通過は投入時まで未確認です。統計的に使える真正なbetween-run floorは収まりません。溢れるのは複数の事前登録時間窓、cold-boot/長時間ドリフト、および効果量・検出力から決める追加cluster数です。これらは2束目へ自動拡大せず裁定へ返します。

- (P1) 同意。層CはS8b official guardとは別track。ただしclean source/revision hash bindingはprovenanceとして維持する。
- (P2) 一部同意。複数PBS requestを1束で投入することには同意するが、それだけで独立性は成立せず、1 cohortは時間窓cluster 1なのでusable floorにはならない。
- (P3) 同意。新prefixのregistered artifactを追加し、`env_contract.calibration_ref`は変更しない。
- (P4) 同意。5 rep内CVを測定品質、session median間CVを採否床候補として別々に判定する。
- (P5) 同意。既存argv seamと前段を再利用し、job scriptを複製しない。
- (P6) 同意。実装資材の整備は1束制約と両立するが、実測は1束で停止し、不足を自動補充しない。