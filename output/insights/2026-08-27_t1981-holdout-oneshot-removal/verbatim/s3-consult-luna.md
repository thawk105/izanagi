## 総括

- 判定は「要修正」。現プランのままでは、旧 96 floor marker の読み込みで最初の attempt が止まる可能性が残る。
- 最重要択一は、A: 新世代を別 namespace に隔離し旧 bytes を opaque な履歴として読めるようにする、B: 旧 field 名を持つ dual-schema parser を残す、のどちらか。identifier 撤去と整合する A を推奨する。
- 珌在の wave worktree は third-party staging が欠落しており、そのままでは qsub 前に停止する。
- 2026-08-24 の 12 cell は「途中死」ではなく、96 attempt 全件 valid で完走済みである。親 brief の成果物影響と deadlock 証拠は誤っている。
- P4 は予約通過だけでは不十分。最終的に `driver_rc=0`、terminal completed、96 session、`result.json` まで確認すべきである。
- テスト、qsub、scheduler 状態確認は実行していない。以下は静的検査と既存 evidence の照合結果である。

## 所見

### 1 旧 floor 台帳を新世代処理から隔離しない限り、最初の attempt で再停止する

- 成立条件: plan の新 claim/marker schema が旧 field を読めなくなる一方、現行と同じ `consumed/`、`ledger.jsonl`、全 marker 走査を残す場合。
- 一次証拠: `orchestrator/campaign/s8b_holdout_admission.py:3905-3925` は claim/ledger の exact key に承認 field を含め、`:3989-4080` は旧 claim と floor ledger row を exact 再導出し、`:4109-4143` は対象外を含む全 `consumed/` を走査する。実台帳の floor marker は `attempt-ledger.jsonl:133-228` の 96 行である。
- 影響: 新 cell reservation が通っても `consume_attempt_ticket()` が `orchestrator/campaign/s8b_holdout_admission.py:3838-3868` で旧 marker を読んだ時点で失敗し、新しい値、result、追加 attempt row は出ない。旧 result の live inspection も exact schema 不一致で読めなくなる。
- 反証: 実在する旧 claim 12、floor marker 96、旧 ledger 12 行を byte-for-byte 配置し、新世代の予約、finalize、最初の planned consume、旧 result の read-only inspection が全て通る統合テスト。plan `s2-plan.md:211` は前半を要求しているが、namespace または dual-reader の実装方法を確定していない。

### 2 消費済み 12 cell は失敗 run ではなく完走済み pilot の台帳である

- 成立条件: campaign ID `20260824T205358Z-2c8cf9be` が claim、ledger、外部 evidence bundle で同一 run を指すこと。
- 一次証拠: `output/insights/2026-08-25_t1431-floor-pilot-values/README.md:1-7,30-69` は request 945229 の完走、床値、96 attempt 全件 valid を記録する。外部 `.../run-dir/20260824T205358Z-2c8cf9be/result.json:2568,2631-2632,2693-2694` に値と `eligible_for_refreeze=false`、同 `journal.jsonl:212` に terminal completed が実在する。共有 ledger の同 campaign は `ledger.jsonl:25-36`、attempt は `attempt-ledger.jsonl:133-228`。
- 影響: brief `:32-34` の「floor 値が 1 つも出ない」は偽である。再測定の直接成果は新しい pilot 観測と台帳行の追加であり、既存の certified 選択や freeze 値を自動更新しない。
- 反証: 外部 result/manifest/journal の hash または campaign identity が共有台帳と不一致である証拠。現資料にはなく、D811 も `docs/decisions.md:30932-30956` で同 run の完走を認定している。

### 3 現在の wave worktree から P4 を実行すると third-party staging 欠落で qsub 前に止まる

- 成立条件: 現在の静的観測どおり `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/{masstree,mimalloc,googletest}` が欠落したまま投入する場合。
- 一次証拠: `tools/pegasus/submit_floor.sh:414-421,485-505,514-521` は同 root と pin-clean な 3 repo を必須とし、欠落時は qsub しない。標準準備は `tools/pegasus/README.md:273-287` と `tools/pegasus/fetch_third_party.py:605-679` の cache verify/hydrate である。
- 影響: submission receipt、PBS job、driver、台帳追加、再測定は全て発生しない。消費済み 12 cell とは無関係な別 blocker である。
- 反証: 同じ wave worktree で `/work/1/SFC/tanab/izanagi-thirdparty-cache` を verify し、`fetch_third_party.py hydrate --repo-root <wave> --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache` 後に 3 staging repo の pin-clean 検査が通ること。hydrate は `output/` 配下なので clean gate の対象外である。

### 4 P4 の `run-linked` または `already consumed` 不在だけでは予約通過も再測定完了も証明しない

- 成立条件: checkpoint の `floor-driver/run-linked`、または失敗文言の不在だけを P4 合格条件にする場合。
- 一次証拠: `orchestrator/campaign/s8b_floor_campaign.py:7391-7406` の `run-linked` は build と holdout reservation より前で、実予約は `:7660-7685`。予約後の陽性証拠は runner が書く `campaign-start` (`:6276-6299`)。完走判定は `tools/pegasus/floor_campaign.sh:1245-1365,1368-1413` の result 検査、`driver_rc`、job-result まで必要である。
- 影響: 予約前の別 gate で止まった job を誤受理したり、予約だけ通って最初の consume や後半 session で止まった jobを「再測定成功」と誤認する。成果物の受理集合が実測未完了 job まで広がる。
- 反証: 新 journal に `campaign-start`、新 generation の attempt row、96 件の `session`、terminal completed があり、`job-result.json.driver_rc=0` と finite な `result.json.floors` が一致すること。過去 run は約48分だった (`output/insights/2026-08-25_t1431-floor-pilot-values/README.md:27-28`)。350秒は予約失敗までの job 内時間であり、queue 待ちや完走時間ではない。

### 5 submitter と job wrapper には一回性以外の停止点が多数残るが、旧 12 cell 自体では発火しない

- 成立条件: policy、repository、scheduler、依存 source、receipt、nonce、job 環境のいずれかが現在値と不一致の場合。
- 一次証拠: submitter は script/output identity `tools/pegasus/submit_floor.sh:15-103`、policy `:151-200`、tracked/index/untracked clean `:201-280`、nonce/create-only `:282-322`、`qstat -Q` 等 `:340-400`、third-party `:402-523`、claims/evidence root `:525-625`、qsub/receipt `:627-718` を検査する。job は static admission `tools/pegasus/floor_campaign.sh:19-263`、scratch/Python `:264-463`、policy/nonce/receipt exact schema `:464-699`、payload/source bytes/clean `:701-800`、qstat allocation/host/elapse `:804-1002`、gflags/glog pin-clean と protocol resolver `:1015-1212` を検査する。
- 影響: 発火地点に応じ qsub なし、driver 未到達、または result なしとなる。いずれも certified 選択は変わらず、submission/job diagnostic だけが増える。
- 反証: 各 submission capture の rc=0、job checkpoint が各 stage へ順に到達し、source/job hash と receipt が一致すること。evidence root の login 可読性は `submit_floor.sh:614-624` で警告のみの fail-open なので、それ単独では停止しない。

### 6 driver 側の budget、freeze、calibration、reservation、build gate のうち旧 12 cell に反応するのは admission と attempt namespace だけである

- 成立条件: fresh pilot を標準 floor wrapper から実行し、plan が cell と attempt の世代分離を正しく実装した場合。
- 一次証拠: current protocol/calibration/execution receipt は `orchestrator/campaign/s8b_floor_campaign.py:7119-7153`、freeze type/hash/schema と cell/schedule は `:7098-7099,7160-7176`、scheduler reservation と submit receipt は `:7199-7237`、durable root/live campaign claim は `:7239-7286`、perf/build/ccbench/manifest は `:7312-7455,7653-7658`。cell reservation はその後の `:7660-7685`。`s8b_budget.py` は floor driverから import されず、oracle driverだけが `orchestrator/campaign/s8b_oracle_driver.py:1431,1584-1608` で使う。ratified freeze も floor pilot では使わず、`s8b_freeze_io.load_verified_freeze` を `s8b_floor_campaign.py:8415-8416` で使う。
- 影響: calibration、freeze、walltime、ccbench、build が壊れれば新 result は出ないが、旧 12 claim の存在はそれらの入力ではない。official budget approval と ratified freeze は pilot P4 では発火しない。
- 反証: 旧 claim/marker の存在が calibration、`s8b_budget`、ratified freeze、scheduler reservation の入力へ流れる call edge。現ソースにはない。attempt registry/profile/scheduler accounting は retry recoveryだけで、planned start は `s8b_holdout_admission.py:3809-3816` で registry 前に戻り、registry 欠落は `:4217-4238,4292-4298` で空候補となる。

### 7 承認 identifier の列挙は概ね揃っているが、exact schema 更新と旧 bytes の扱いを一つの判断にしてはならない

- 成立条件: CLI/env/Python field を削除し、claim/ledger/result schema からも field を削除する場合。
- 一次証拠: shell dataflow は `submit_floor.sh:33,44-45,627-630` と `floor_campaign.sh:541-555,1230-1238`、floor Python は `s8b_floor_campaign.py:6954-7007,7021-7083,7675,8195-8198,8423-8425`。exact claim/ledger keys は `s8b_holdout_admission.py:3905-3925`、oracle/n-pilot result identity は `s8b_oracle_n_pilot.py:2293-2324,2553-2564,2592-2700`、fixture は `orchestrator/tests/s8b_floor_evidence_fixture.py:187-273`。floor submit receipt と portable admission receiptには元から承認 field がない (`floor_submit_receipt.py:15-19,51-64`、`s8b_floor_contract.py:66-70,357-390`)。
- 影響: field 除去を新 schema だけへ限定すれば新 result の受理集合が正しく変わる。旧 schema constantを単純置換すると、36 ledger 行、12 floor v2 claim、228 markerの読取集合が縮み、履歴と既存 pilot result の live 検証が失われる。
- 反証: active code/shell/README に CLI、env、Python、shell local identifier がゼロで、R33 successor protocol が新 driver/job bytes を pinし、旧 bytes は別 namespaceの read-only historical readerで canonical/hash 検査できること。R33 の現 pin は `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json:9-15` と runtime `s8b_oracle_n_pilot.py:590-595`。

### 8 実装子 A/B は file 重複はないが API 依存が強く、独立実装にはなっていない

- 成立条件: 2 子が別々に変更を完成させ、それぞれ単独で testable な差分を返す運用の場合。
- 一次証拠: A 所有の reservation API は `s8b_holdout_admission.py:1205-1233,3098-3124`、B 所有の呼出しは `s8b_floor_campaign.py:7667-7676` と `s8b_oracle_n_pilot.py:2943-2953,2979-3006`。承認引数の削除と generation receipt の返却規約が両側を同時に変える。
- 影響: A 単独では既存 caller が壊れ、B 単独では旧 callee へ不正な呼出しとなる。中間 commit や子別テスト結果を受入に数えると、実際には統合不能な差分を採用し得る。
- 反証: 先に共通 API contractを固定して両子が同じ署名へ実装する、または A→B の順で直列化し、統合後だけを受入単位にすること。

### 9 plan の source anchor は概ね実在するが、末尾が未完で数値と件数に drift がある

- 成立条件: 現 `s2-plan.md` をそのまま author の完全な実装仕様として使う場合。
- 一次証拠: sampled anchor `s8b_holdout_admission.py:1391-1448,1553-1599`、`submit_floor.sh:201-280,627-645`、`floor_campaign.sh:804-976` は主張と一致した。一方、plan は `/outputs/s2-plan.md:358` の `P2 の維持可否` 見出しだけで終わる。current budget は shared dependency 1800秒を加える `s8b_floor_campaign.py:1568-1576` ため required=30000、margin込み30600だが、shell/README は28200/28800のまま (`floor_campaign.sh:9-14`、`tools/pegasus/README.md:233-235`)。
- 影響: P2 の最終裁定が欠落し、P4 の walltime margin、診断、文書値が実コードとずれる。直接 certified 値は変わらないが、予約 gate の説明と受入判定を誤る。
- 反証: plan の欠落末尾が別 artifact に存在し、current protocolで `_floor_reservation_budget()` が28200を返す証拠。現コードと過去成功 journal `journal.jsonl:1` は30000を示す。

## 親 brief への所見

- P1 は不成立。`:1391-1394` だけ外すと旧 claim identity `:1411-1448`、ledger reuse `:1553-1599`、その後の旧 attempt markerで止まる。新しい reservation generation が必要である。
- P2 も不成立。共有 `attempt-ledger.jsonl:133-228` は同じ `cell_id::seqN` の96件を既に持つため、現 marker path `s8b_holdout_admission.py:3960-3970` と衝突する。D893 を世代内一回性として残す plan の方向は妥当である。
- P3 の承認 closure は妥当だが、brief は oracle/n-pilot の「承認削除」しか明記していない。D1124 の一般則を満たすには、それらの cell/attempt 反復拒否も plan のとおり世代内へ限定する必要がある。
- P4 は現状では不成立。wave worktreeの third-party staging が欠落し、positive proof も弱い。commit 済み clean worktreeで hydrateし、同 worktreeの実 scriptを optionなしで起動し、worktreeを job 完了まで残す必要がある。`SCRIPT_PATH == $REPO_ROOT/tools/pegasus/submit_floor.sh` は `submit_floor.sh:15-29,89-93` によりこの起動なら通る。
- 「evidence root が `/work/1/SFC/tanab/izanagi-job-evidence` だから main repo の worktree」という `evidence-failed-resubmit.md:34-39` の推論は誤り。同じ親 directory直下の独立 cloneでも `dirname(dirname(<clone>/.git))` は同じ値になる (`submit_floor.sh:557-560`)。P4 は実際の `git rev-parse --git-common-dir` で `/work/1/SFC/tanab/izanagi/.git` を記録すべきである。
- `evidence-deadlock.md:30-33` の「成果物なし」も誤り。検索は basename `s8b-floor-pilot` だけで、外部 bundle の `run-dir/20260824T205358Z-2c8cf9be/{result,manifest,journal}` を見落としている。run は完走済みなので resume 対象ではないが、「途中死して成果物が無い」という一般化は成立しない。
- `evidence-consumed-cells.md:7-23` の「D1124 の12件 = floor_campaign」は正しい。共有 ledger `:25-36` と campaign ID が一致する。一方、n_pilot 12件は別 run `t1142-run-1` で marker 132件、oracle 12件は `s8b-oracle-fixture-b0`、`fixture-pin` であり、後者を科学的実測対象と一般化する根拠はない。
- 成果物影響は「値が空欄」ではなく、「追加の pilot 測定を作れない」が正しい。既存 pilot 値はあるが D811 により official/freezeへ発効しない。新しい run も proof chain が明示採用しない限り certified 選択やレポート値を変更しない。
- 不変条件は plan 上は維持する方向だが、実装前なので未証明。特に旧 namespace を避けるために global integrity scanを雑に削ると、別の正しさ gate を弱める。namespace分離と世代内 exact scanで実装すべきである。
- brief の anchor 表は base identifier の行番号は概ね正しいが、oracle shell の別名 env を除外して `3/3`、oracle testを `25` と数えている。実際は別名を含め `submit_oracle_n_pilot.sh` 4行、`oracle_n_pilot.sh` 7行、test 28行で、plan `:24,35` がこの不足を補っている。

## 判定できなかった点

- 将来の実装が旧 bytes を dual-readするか、新 namespaceから完全に隔離するかは未確定。このため「撤去後に最初の attempt が通る」は現時点では未確認。
- `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の現在状態は確認していない。
- 2026-08-27 の checkout が本当に linked worktreeだったかは、削除済みで `.git` 実体がなく判定不能。projected checkpointだけでは証明できない。
- 2026-08-27 の exact driver error は残存 checkpointに保存されず、generic `pilot floor driver returned nonzero` だけである。exact 文言は worklogとD1124の記録に依存する。
- pytest、shell実走、driver実走、qsubは行っていないため、テスト緑やP4成功とは判定していない。