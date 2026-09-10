結論は、plan のままの実装は不可です。中心案の `official = fresh-only` は provenance の欠落を直さず、正常な cache hit を拒否して pilot・official・resume を壊します。採るべき裁定は「fresh 必須」ではなく「検証可能な producer receipt 必須」です。

指定の `brief.md` と `plan.md` は最初に全文確認済みです。以下は read-only の静的検査結果であり、pytest・build・mutation・qsub は実行しておらず、緑も主張しません。編集もしていません。

### 段2事実の独立再構成

| 事実 | 裁定 | 根拠 |
|---|---|---|
| v2 fresh の実 argv は staging、返却値は final path | **real** | `_run` は staging を使う [buildcache.py:487](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:487)。返却は `_v2_result` が final `bdir` から再構成する同:557-560、354-367。 |
| cache hit から過去の jobs/実 argv を復元不能 | **real** | completion exact keys に argv/jobs がない同:288-332,527-541。v1 は completion 自体がない同:564-626。 |
| FROZEN_MANIFEST=23、active v2 なし、official issuer の現受理集合は空 | **real、ただし現在時点限定** | 23件 literal と exact length は [test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_frozen_artifacts.py:38), :139-153。`active/generations/approvals` は実 filesystem 上不在。public official は [s8b_floor_campaign.py:193](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:193) と :2639-2668 で無条件拒否。 |

ただし「official issuer が空」と「ratified validator の受理集合が空」は別です。`launch_validate` の正常 fixture は現に受理される設計です（[test_s8b_ratified_verify.py:1138](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_ratified_verify.py:1138)）。後者へ新しい cached 拒否を加えるなら D96 の対象です。

## 所見

### 1. `[real / Critical]` BuildResult の同一 field を実行事実と再現表示に二義化している

現行閉包は次です。

```text
v2 fresh:
  _v2_commands(staging, jobs=16) → _run(actual)
  → completion(binary/source/toolchain/contractのみ)
  → stagingをfinalへrename
  → _v2_result(final, jobs=16)を返す

v2 hit:
  completion/binary検証
  → _v2_result(final, jobs=16)を再構成して返す
```

- v1 key は genome/commit/trace/src/compiler名で、jobs はありません（[buildcache.py:121](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:121)）。fresh の argv は final path で実 argv と一致しますが、hit では今回要求された jobs から再現コマンドを作るだけです（同:584-605）。
- v2 identity は source、toolchain manifest、contract namespace を持ちますが jobs はありません（同:219-234,440-454）。
- `BuildResult.cached` は「今回 rebuild を省いたか」であり、producer の品質や ratifiability ではありません（同:138-155）。
- `configure_argv/build_argv` の現行契約は「実験再現用」です。floor 側も「表示・照合専用、再実行禁止」と明記します（[s8b_floor_campaign.py:1048](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:1048), :1126-1131）。

plan の「fresh なら actual、hit なら reproduction」は DW-O13 が禁じる二義化です。

攻撃入力: jobs=7 で producer を作り、次に jobs=48 で hit させる。
誤成果物: 同じ `build_argv` が fresh では `-j7` の歴史、hit では実行されていない `-j48` を表し、manifest から両者を区別できません。
最小修正: 現行 argv fields は一貫して reproduction のまま維持し、別の `producer_receipt.executed_*_argv` を導入すること。

### 2. `[real / Critical]` fresh-only は cache の通常運用を障害化する

plan は [plan.md:171](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-freeze/plan.md:171)-178、248-257 で official の `cached=true` を一律拒否します。しかし floor の pilot/official/oracle は同じ `out_root/s8b-build-cache` を使います（`s8b_floor_campaign.py:962-978`, `s8b_oracle_driver.py:1328`）。

攻撃入力A:

1. pilot が同じ12セルを正常 build。
2. official guard 解禁後、同じ protocol で official を開始。
3. launch certificate と `launch-start` が発行される（`s8b_floor_campaign.py:2894-2922`）。
4. 最初のセルが正常な cache hit。
5. fresh-only gate が拒否。

誤成果物: certificate と journal だけが durable に残り、manifest/result は不在です。現在の frozen protocol は Pegasus で `allow_resume=False`（[env_contract.py:180](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/env_contract.py:180)-185）なので、この official run は回復不能です。

攻撃入力B: official fresh が6セル publish 後に7セル目で失敗し、別 run で再試行。先頭6セルが hit となり、再試行も即拒否されます。cache が成功履歴ではなく poison になります。

攻撃入力C: `allow_resume=True` の linux-baremetal official が厳密 L 状態で再入。L は `build_cells` を再実行します（`s8b_floor_campaign.py:2986-3020`）。直前 run が publish 済みなら hit となり拒否されます。既存テストも「launch-start 後の build failure から build を再構築」を固定しています（[test_s8b_floor_campaign.py:4023](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_floor_campaign.py:4023)-4055）。

なお「現在の Pegasus protocol の resume を壊す」は **refuted** です。Pegasus は既に resume 不可です。しかし generic official 実装、pilot→official、失敗後の新 run は確実に壊れます。

最小修正: `cached` ではなく、検証済み producer receipt の有無・整合性を eligibility 条件にすること。

### 3. `[real / High]` login gate は brief より過剰で、brief 自身も矛盾している

[brief.md:14](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-freeze/brief.md:14)-15 は「実 build を拒否」ですが、同:33 は「任意 campaign/build call を拒否」と書きます。plan は entry 先頭で cache hit まで拒否し、pipeline も source/WAL 前に全面拒否します（[plan.md:160](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-freeze/plan.md:160)-165）。

攻撃入力: Pegasus login 上で、完全に検証可能な既存 v2 entry を読む。
誤結果: `_run`、configure、build が一件も不要なのに拒否されます。cache の read-only 利用と診断まで失われます。

build-only の正しい順序は次です。

1. site observation と不整合検査は entry 最初。
2. source/toolchain/identity を read-only で解決し、cache hit を検証。
3. hit なら返す。破損 entry は rebuild fallback せず停止。
4. miss かつ login なら、次より前に拒否:
   - v2 `os.makedirs(parent)`（現行 `buildcache.py:458-461`）
   - claim/staging（同:487-498）
   - v1 `_clear_stale_build_dir`（同:607）
   - `_run`
   - pipeline の `wal.log(build_start)`（[pipeline.py:435](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/pipeline.py:435)-458）

このため pipeline には「read-only build lookup/plan」が必要です。source resolve 前に最終拒否すると hit/miss を区別できません。

campaign の benchmark/test 自体も login で禁止するなら、それは別の heavy-execution gate です。buildcache miss gate に偽装せず、全 campaign entry の別 caller closure として裁定すべきです。

### 4. `[real / High]` jobs を key から外すこと自体は成立するが、hit の意味が未定義

jobs を key/contract へ入れない裁定は、「並列度は binary の意味を変えない producer execution metadata」と明記するなら整合します。

攻撃入力: producer は explicit jobs=7、後続 caller は compute default=48。
正しい意味:

- binary identity は同一なので hit。
- producer の actual jobs は7。
- 今回の jobs=48 は実行されておらず、invocation request にしか属さない。
- official provenance は producer=7、`cache_disposition=hit` と記録する。

誤った意味は、hit の `build_argv` を `-j48` に再生成して producer history と呼ぶことです。

最小修正:

- explicit 正整数を miss 時だけ最優先。
- compute default は affinity 全数、other default は16。
- bool、0、負数は拒否。
- explicit は login miss 拒否を bypass しない。
- jobs は key 外のまま、producer receipt に `effective_jobs` と `jobs_source` を残す。
- 「official は現在割当の jobs で作られた binary だけ受理」という別要件なら、jobs を identity に入れる必要があります。両方は同時に主張できません。

v1 は過去 jobs を永続化できないため、legacy binary reuse 用に限定し、ratifiable provenance には使わないのが妥当です。

### 5. `[real / Critical]` 現在の proof chain は binary bytes を束縛するが build argv/jobs を束縛しない

| 成果物 | write path | read/保証 |
|---|---|---|
| `completion.json` | `buildcache.py:527-545` | v2 hit が source/toolchain/contract/binary SHA を検証。floor/ratified は読まない。 |
| launch certificate | `s8b_floor_campaign.py:1642-1728,2894-2922` | protocol/freeze/clean scan の開始前証拠。build 後事実は持てない。 |
| binary store | 同:1759-1805 | resume は binary SHA を再検証する同:1807-1827。 |
| manifest/result | 同:1175-1197,2316-2447 | `binaries` を mirror。 |
| journal | 同:2204-2216 | execution receipt と、session ごとの `binary_sha256_at_measure` を記録。 |
| result.md | 同:2561-2591 | human projection。ratified の `_RUN_BASENAMES` に含まれず、proof anchor ではない（`s8b_ratified_freeze.py:257-262`）。 |
| ratified validator | `s8b_ratified_freeze.py:1624-1785,2094-2112,2138-2252,2870-3035` | binary SHA、source binding、protocol/cert/manifest/result/journal equality は強い。argv は list 型、cached は bool 型しか検証しない。 |

攻撃入力: manifest と result の同一セルの `build_argv` を双方 `-j48` から `-j1` へ整合して変更し、manifest/result の raw hash chain も再発行する。
誤成果物: `result.binaries == manifest.binaries` は維持され、`build_argv` を独立値と比較する辺がありません（`s8b_ratified_freeze.py:1655-1667,2967-2968,3032-3035`）。binary receipt は同じ SHA のため通ります。

したがって plan の「build_argv drift 拒否」テストは、独立 producer receipt を追加しない限り実装追随の弱い期待値です。validator が argv を自己解釈して `-j48` を要求しても、build 時 affinity や producer site の独立証拠がありません。

最小修正: completion receipt の raw bytes を floor の content-addressed receipt store へコピーし、manifest→result→generation measurement closure から path+SHA で束縛すること。

### 6. coverage closure

#### `[refuted / Info]` s8a_trigger_freq の見落とし

plan は `s8a_trigger_coverage._build` の間接 consumer である `s8a_trigger_freq.py:60,145` を実際に列挙しています（plan:169-170,219）。ここは omission ではありません。

#### `[real / High]` buildcache caller closure の記載不足

中央 gate の影響を受ける production caller は少なくとも以下です。

- `backoff_overthrottle.py:68`
- `backoff_profile.py:133`
- `between_run_floor.py:159`
- `p3_kickoff.py:93`
- `s1_verify_extime_calibration.py:340`
- `s2_verify_calibration.py:273-274`
- `s3_lock_coverage.py:164`
- `s5_permutation_coverage.py:160`
- `pipeline.py:476-502`
- `s8b_floor_campaign.py:965`
- `s8b_oracle_driver.py:944-958`

中央 miss gate なら個別編集は不要ですが、login 上で hit 後に benchmark を走らせる caller もあります。したがって「build miss を防ぐ保証」と「campaign の高負荷実行を防ぐ保証」を分ける必要があります。

#### `[scope外real / High]` global「Pegasus login で build なし」は未達

- `t152_write_intent_coverage.py` は direct CMake、default/max jobs=8（[t152_write_intent_coverage.py:328](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/t152_write_intent_coverage.py:328)-387）で、成果物自身が `platform=pegasus, host_role=login-node` と宣言します（同:684-706）。これは親の全体宣言に対する明白な残存 login build です。
- `silo_ladder_rung1.py:2111-2142,3786-3816` は direct CMake `-j48`。正規 job seam は PBS-only ですが、U3 policy の対象ではありません。
- `certify_calibration.sh`、`floor_campaign.sh`、`silo_ladder_rung1.sh`、`t141_region_profile.sh` は PBS identity を要求し、既に `-j48`。今回の resolver で得る新保証ではなく、既存 submitter 契約による保証です。
- calibrator は CCBench を build せず `--binary` を消費しますが、`calibrator/tsc.py:65-79` は小さな TSC helper を直接 compile します。
- `calibration_report.py` の CMake 行は表示のみです。

最小修正: wave の保証文を「buildcache miss + 指定4 direct coverage helper」に狭めるか、t152 等を別裁定パッケージとして明記すること。

#### `[scope外real / High]` coverage ENV tag 汚染

4 driver と `s8a_trigger_freq` は `ENV_TAG="linux-baremetal"` を固定し、`output/env/linux-baremetal/...` を `"w"` で更新します。例は `s2_verify_calibration.py:55-59,336-341`、`s3_lock_coverage.py:45-47,220-224`、`s5_permutation_coverage.py:42-44,210-214`、`s8a_trigger_coverage.py:59-60,255-259`。

攻撃入力: Pegasus compute で実 driver を受入実走。
誤成果物: Pegasus の測定値が linux-baremetal calibration を上書きします。
最小修正: この wave では argv/site の mock/unit test だけを compute で実行し、4 driver の実走を受入条件にしない。実走するなら env contract/output namespace を先に別裁定すること。

### 7. `[real / High]` D96 と「accepted set empty」の過大一般化

ratified validator の `cached=true` 拒否は、現在 bool 型なら受理していた入力を拒否する変更です。D96 は新しい D と同一変更単位の境界テストを要求し、既存 D の追記では代用不可です（[decisions.md:4269](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/decisions.md:4269)-4279）。

plan の「docs/decisions.md を親が更新」だけでは不足します。

また、

- public official issuer の受理集合は空
- active generation はない
- ratified validator の意味的受理集合も空

の3つ目は成立しません。正常 synthetic artifact は validator に到達して受理されます。したがって D96 を回避できません。

最小修正: cache-hit semantics、legacy handling、output schema split、official receipt requirement、却下案を新 D とし、exact cause を持つ境界テストを同梱すること。

### 8. freeze/no-reissue

#### `[refuted / Info]` 23件 literal pin と active 不在

親実測は正しいです。`FROZEN_MANIFEST` には future official manifest/result/journal/certificate は含まれません。既存23件、protocol、selector、v1、歴史 JSON を変更せず新挙動を検査できます。

#### `[real / High, conditional]` 「従って schema/version 裁定不要」は誤り

現行 `s8b_floor_contract.py:25-31` は protocol/result/manifest/journal の版を一括 v2 としています。既存 `build_argv` の意味を同じ v2 のまま reproduction から actual へ変えれば、bytes を直接変更しなくても出力契約を silently repurpose します。

最小修正:

- frozen protocol v2 と freeze v1 は不変。
- manifest/result の provenance envelope だけを v3 に分離。
- この decoupling を新 D で明記。
- legacy v2 pilot resume は旧 validator で維持。
- official v3 に既存成果物はないため、再発行対象はゼロ。

もし「protocol v2 は manifest/result v2 まで不可分」と解釈し続けるなら、protocol 再発行なしの schema 変更はできません。その場合、親の no-reissue 前提を撤回する必要があります。

### 9. `[real / High]` plan の tests/mutations は target validator へ届かないか、弱い

- `test_buildcache_v2.py:79-86` の fake `_run` は argv を保存せず binary を置くだけです。現状のままでは staging/final/jobs の exact provenance を検査できません。
- floor fake build は常に `cached=False`、final-path argv、receipt なしです（[test_s8b_floor_campaign.py:199](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_floor_campaign.py:199)-225）。
- ratified fixture は常に synthetic argv と `cached=False`（[test_s8b_ratified_verify.py:266](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_ratified_verify.py:266)-284）。
- official public wrapper は無条件拒否されるため、floor negative test は `_run_campaign_core` の明示 seam を使わないと build validator に届きません。
- manifest だけ、または result だけを変える `build_argv` test は mirror gate に捕まり、目的の provenance validator を試していません。
- v3 fixture を作らず field だけ追加すると、前段の exact-key/schema gate で落ちます。

必要な境界テストは次です。

- fresh→hit の2回呼出しで、2回目の requested jobs を変更しても producer receipt が不変。
- fresh の executed argv は staging、reproduction argv は final。
- valid v3 hit は official で受理、legacy v2 hit は `producer-receipt-missing` で拒否。
- pilot→official の hit を受理。
- L resume が直前 producer receipt を hit して完遂。
- login hit は受理、login miss は WAL/mkdir/claim/_run が全て0。
- manifest/result/receipt sidecar を coherent に変え、独立 receipt edge が exact cause で拒否。
- receipt の source/contract/toolchain/binary SHA/site/jobs の各一辺 mutation。
- schema v3 positive control を先に成立させ、前段 gate の赤を target test と数えない。

plan の mutation「official cached を許可」を殺す、は逆です。代わりに「legacy receipt 無しを許可」「hit 時に producer jobs を現在値で上書き」「actual/reproduction を交換」「receipt sidecar edge を外す」「valid hit を拒否」を殺すべきです。

### 10. `[real / High]` U1/U3 の所有と file closure が不足

妥当な分割は次です。

- U1: site observation、分類、jobs precedence の純関数のみ。cache・write・receipt semantics を持たない。
- U3: read-only cache plan、miss gate、v3 completion、BuildResult、coverage propagation、floor receipt store、manifest/result、ratified validator。
- 親: 新 D、runbook、legacy/version/freeze 裁定。

現 plan の U3 list には少なくとも以下が不足します。

- `orchestrator/campaign/s8b_floor_contract.py:25-31` — manifest/result schema の分離。
- `orchestrator/campaign/s8b_oracle_driver.py:944-958,1328` — v2 build API の live wrapper/caller。
- `orchestrator/tests/test_s8b_ratified_freeze.py:360-362` — ratified verify が共用する production-emitter fixture。
- producer receipt sidecar/store の新 module または floor campaign 内の明示 ownership。
- pipeline の pre-WAL read-only lookup seam。

docs は単なる追随ではなく、D96 の新 D として次を固定する必要があります。

- `cached` は invocation-local。
- jobs は binary identity 外。
- actual argv と reproduction argv は別 field。
- official は receipt-required、fresh-required ではない。
- legacy v1/v2 は非 ratifiable。
- protocol v2 と output provenance v3 の版分離。

## 採るべき provenance schema と cache-hit semantics

推奨は一案に絞ると、次の `receipt-required v3` です。

### Build cache

新 namespace `buildcache/v3` を作り、既存 v2 digest directory と衝突させません。completion の exact schema に以下を追加します。

```text
producer_receipt:
  schema
  full_build_digest
  contract_sha256
  src_token / ccbench_commit
  toolchain_manifest_sha256
  binary_sha256
  site_observation:
    site_kind / hostname / pbs_jobid / affinity_cpus
  jobs:
    effective_jobs
    source = explicit | compute-affinity | other-default
  executed_configure_argv
  executed_build_argv
  reproduction_configure_argv
  reproduction_build_argv
producer_receipt_sha256
```

receipt は binary と同じ staging 内で completion に hash-bound し、rename 前に fsyncします。別 write の unbound receipt は認めません。

`BuildResult` は次の意味に固定します。

- `cached`: 今回の invocation が rebuild を省略したか。互換維持。
- `configure_argv/build_argv`: 常に reproduction。
- `producer_receipt`: fresh/hit の双方で同じ歴史的 producer 事実。
- `invocation`: requested jobs、site、`cache_disposition=fresh|hit`。hit の executed argv は空。

### Floor / ratified

- manifest/result を provenance envelope v3 にする。
- cache completion の canonical raw bytes を content-addressed `build-receipts/<sha>.json` へコピー。
- 各 binary record は receipt `{path,sha256}`、portable producer execution、reproduction argv、`cache_disposition` を持つ。
- receipt file を generation `measurement_closure` に含める。
- validator は receipt→source/contract/toolchain/binary SHA→manifest→result→journal session SHA の全辺を照合。
- `result.md` は同じ意味を表示するが trust anchor にはしない。
- official eligibility は `cache_disposition` ではなく receipt validity で判定。

### Cache hit の最終意味

- valid v3 hit: official/pilot とも受理可能。
- current requested jobs は実行されない。producer jobs を上書きしない。
- legacy v1/v2 hit: binary reuse は可、official ratification は `producer-receipt-missing` で拒否。
- corrupt v3 hit: rebuild fallback せず停止。
- Pegasus login: valid hit は read-only 受理、miss は producer write/WAL 前に拒否。
- jobs は cache key 外。producer metadata として receipt に残す。

案の比較は以下です。

| 案 | 裁定 |
|---|---|
| jobs を記録せず official fresh-only | **却下**。cache/pilot/retryを壊し、provenance gapを隠すだけ。 |
| v2 completion に additive field | **却下**。現 validator は exact keys、既存 immutable entry と衝突。 |
| completion schema/namespace を v3 | **採用**。receipt 必須性と legacy を機械的に分離できる。 |
| fresh receipt を別保存 | 単独では**却下**。completion と atomic/hash-bound にし、floor proof chainへ参照する場合だけ v3案の一部として採用。 |

検査はすべて静的です。pytest、build、mutation、qsub は未実走であり、既存23件の SHA 一致もこの turn では実行確認していません。

## 総括

plan の最大の誤りは、`cached` を provenance の良否へ昇格させたことです。`cached` は今回の呼出し属性にすぎません。実装すべきなのは cache hit の排除ではなく、producer receipt の永続化・versioning・proof-chain 結線です。`buildcache/v3 + manifest/result provenance v3 + valid receipt hit受理 + legacy official拒否` へ計画を書き換え、新 D と target 到達型テストを先に確定するのが最小で整合した修正です。