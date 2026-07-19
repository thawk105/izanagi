# 2026-07-18 Pegasus env_contract 登録段 wave — codex 敵対相談 逐語・裁定

wave 正本: plan-env-contract-pegasus.md (worktree 直下) → 完了時に worklog へ吸収。
相談: codex gpt-5.6-sol reasoning=max ×3 並列 (C1 attestation/machine-pin、C2 enforcement、C3 calibration job)。
プロンプト原文: 本ファイル末尾 §P。逐語は到着順に追記 (F20 教訓: 進行中凍結)。

## C2 逐語 (enforcement 4 点)

## 所見

現プラン v1 のまま U2 実装へ進むのは止めるべきです。4 enforcement の leaf は作れても、実走経路で発火しない構造と G12 の未強制が残ります。

### {severity: Critical / 配線・依存関係, U2 は閉じた実装単位ではなく、登録前 calibration では contract-driven enforcement が発火不能}

攻撃シナリオ: `layout.py`、`buildcache.py`、walltime leaf、`runner.py` の単体テストをすべて通す。しかし floor/oracle は walltime leaf を呼ばず、`buildcache.build()` に contract を渡さない。さらに Pegasus entry は較正後の U4 まで存在しないため、較正ジョブが `env_contract.lookup("pegasus")` に基づいて enforcement を選ぶ設計は必ず循環する。結果、最初の登録用 calibration だけが無防備になる。

根拠:

- U2 の想定に floor/oracle/pipeline 配線がない: `plan-env-contract-pegasus.md:84-97`
- `execution_guard` 自身が walltime/allowlist/process 同一性を未強制と明記: `orchestrator/campaign/execution_guard.py:13-16`
- floor の build 呼び出しに contract 次元なし: `orchestrator/campaign/s8b_floor_campaign.py:765-782`
- oracle から到達する trace/perf build にも contract 次元なし: `orchestrator/campaign/pipeline.py:423-429`
- calibration は registry lookup なしで直接実行される: `orchestrator/calibrator/cli.py:130-150`
- 現 registry は較正前には `linux-baremetal` しか持たない: `orchestrator/campaign/env_contract.py:147-164`

提案（最小修正）:

- U2 を「leaf 実装」と「実走結線」に分け、結線側に `s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`pipeline.py`、`calibrator/sweep.py`、`calibrator/cli.py`、`execution_guard.py` を含める。
- 登録前 calibration は contract ではなく、U3 の追跡済みジョブスクリプトが生成する exact-schema の `RegistrationLaunchReceipt` を消費する。deadline、job ID、durable root、script hash、PID visibility 結果を束縛する。
- U4 は enforcement receipt のない calibration artifact を registry 参照先として拒否する。暫定 Pegasus entry を較正前に置いて循環を解く案は、プラン §0 に違反する。

### {severity: Critical / walltime・G12, deadline env var と現行予算からは有限の完走見積りを証明できない}

攻撃シナリオ: `required_s=0` または小さい値を渡し、遠い未来の deadline を export すれば常に通る。正常値でも、cmake、pgrep、git、preprocess 等に timeout がないため、一度 pass した後に allocation 終了までぶら下がれる。`extime × reps` や oracle の bench reservation だけを見積りに使えば、build・verify・retry・fsync・finalize が丸ごと漏れる。

根拠:

- プラン候補は deadline と「見積り」の真実源を未定義: `plan-env-contract-pegasus.md:66-69`
- build subprocess に timeout がない: `orchestrator/campaign/buildcache.py:323-327`
- pgrep にも timeout がない: `orchestrator/calibrator/runner.py:170-181`
- oracle の予約は bench 秒だけ: `orchestrator/campaign/s8b_oracle_driver.py:736-755`
- `MAX_WALLTIME_S` は p3 loop の内部停止条件で、iteration 境界でしか評価されない: `orchestrator/campaign/p3_s4_loop.py:75-78,287-305`
- floor の `PBS_JOBID` は nullable で、欠落しても受理される: `orchestrator/campaign/s8b_floor_campaign.py:613-621,645-663`

提案（最小修正）:

- 見積りは caller/env から受け取らず、validated schedule から leaf が導出する。

  - floor: `len(schedule) + len(cells) × retry_slots_per_cell`
  - oracle: schedule 行数 × 最大 attempt 数 × build/verify/bench cap
  - calibration: sweep 点数、sweep/noise/scale reps から導出

- build、probe、materialization、各 run、finalize の全 blocking 操作に hard timeout を置く。有限 cap を置けない工程が一つでもあれば「完走所要の上限」は算出不能として拒否する。
- `required_s` は正整数・非ゼロ、`required_s + safety_margin <= remaining_s` を要求する。開始時に realtime deadline から monotonic deadline も導出し、時計の後退でも延命しない。
- deadline 単独ではなく `{job_id, requested_s, scheduler_started_epoch, deadline_epoch, host, boot_id, script_sha256, nonce}` を束縛し、現在の `PBS_JOBID` と不一致・欠落・未来過ぎる開始時刻・別 boot は拒否する。
- 途中で余裕を失った場合は campaign-level terminal を残し、全数値を不採用にする。評価固有の retryable abort へ翻訳して続行してはいけない。

`qstat -f "$PBS_JOBID"` は、成功すれば raw env より強い第二情報源になる一方、現 runbook が確認しているのはログインノードでの利用だけです (`docs/pegasus-runbook.md:124-131`)。計算ノードからの executable 存在、認証、対象 field 名、時刻意味論を U3 の smoke job で実測するまでは前提に数えられません。実測に失敗するなら、追跡済み submission spec＋job script を trust root とする弱い方式だと明記すべきです。

linux-baremetal の no-op は `if env_tag == "linux-baremetal"` ではなく、登録後実走なら既存 `IsolationPolicy` から型で導出できます。現値 `single_process=False / allow_resume=True` は `NotRequired`、Pegasus の `True / False` は `Required` とする。ただし登録前 calibration だけは上記 launch receipt が必要です。

### {severity: Critical / G12・全数値不採用, `single_process=True` は宣言だけで、二重投入と partial 数値採用が残る}

攻撃シナリオ:

1. 同じ floor protocol を数秒ずらして二つ qsub する。
2. 各 process は別 timestamp の run directory を作るため、双方が fresh run として進む。
3. 一方が walltime kill されても、もう一方の実行を止める campaign-wide claim はない。
4. oracle が途中 kill された場合、既に完了した行は report 上 `completed` と bench 数値を持ち、未実行行だけ `not-started` になり得る。G12 の「途中 kill は全数値不採用」にならない。

根拠:

- `single_process` は dataclass 定義以外に consumer がない: `orchestrator/campaign/env_contract.py:47-60`
- floor が消費するのは `allow_resume` だけ: `orchestrator/campaign/s8b_floor_campaign.py:2137-2141`
- floor run ID は秒単位 timestamp＋protocol hashで、異なる秒なら別 directory: `orchestrator/campaign/s8b_floor_campaign.py:2362-2375`
- generic WAL append に process 排他はない: `orchestrator/campaign/wal.py:41-60`
- oracle driver は campaign-completed terminal を WAL に書いていない: `orchestrator/campaign/s8b_oracle_driver.py:721-963`
- report は campaign 全体の terminal を要求せず、各 trial を個別に completed 化する: `orchestrator/campaign/s8b_oracle_report.py:455-471,585-625`

提案（最小修正）:

- `single_process=True` の実 consumer として、immutable campaign identity をキーにした one-shot claim を persistent・全 clone 共通の場所へ `O_EXCL` で作る。job ID、hostname、boot ID、PID、proc starttime を記録する。
- `allow_resume=False` では crash 後も claim を消さない。再実行は新しい campaign identity／amendment を要求する。
- oracle WAL に exact-one の `campaign-terminal {status, scheduled_rows, completed_rows, execution_identity}` を追加する。
- report は terminal completed が一意で全 schedule を覆う場合だけ数値を公開する。それ以外は完了済み行も含め、全行を `campaign-incomplete`、`bench_values=[]` にする。
- oracle の現行 marker/atomic lock は同じ freeze root 内では有効だが、別 clone は別 marker rootになる (`orchestrator/campaign/s8b_oracle_driver.py:520-564,680-684`)。job-wide claim の代替にはならない。

### {severity: High / 永続領域・TOCTOU, `resolve()` 一回の allowlist は symlink 以外を防げず、書込み面も被覆不足}

攻撃シナリオ:

- `/work/allowed/x` を `/scr/x` の bind mount にすると、lexical path と realpath は allowlist 内に見える。
- 検査後に output root の symlink／親 directory を差し替えると、WAL open は再び文字列 path を辿って `/scr` へ書く。
- output root だけ `/work` にしても、oracle budget と run marker が `/scr` 上の repo に残る。
- calibration の `--out-root` は `layout.py` を通らず、検査を完全回避する。

根拠:

- layout は現在文字列 root を返すだけ: `orchestrator/campaign/layout.py:27-33,76-90`
- WAL は毎回文字列 path を再 open する: `orchestrator/campaign/wal.py:41-48`
- floor journal も同様: `orchestrator/campaign/s8b_floor_campaign.py:510-515`
- calibrator は独自 `_output_root` と直接 open を使う: `orchestrator/calibrator/cli.py:75-76,97-103,152-163`
- oracle budget は repo 固定 path: `orchestrator/campaign/s8b_oracle_driver.py:45-46,1040-1044`
- marker は freeze parent: `orchestrator/campaign/s8b_oracle_driver.py:680-684`
- `/scr` 等の機械固有事実を横断コードへ焼かない裁定: `docs/decisions.md:2282-2288`

提案（最小修正）:

- `layout.py` に `/scr` や `/work` を直書きしない。Pegasus 固有 root は U3 script/runbook が launch receipt に載せ、横断コードは generic な `DurableRootPolicy` を消費する。
- resolved path だけでなく mount ID を取得し、approved root から candidate までの mount crossing／bind mount を拒否する。
- 検査済み root directory を FD と `(st_dev, st_ino, mount_id)` で保持し、相対 `openat`＋`O_NOFOLLOW` で書く。少なくとも各 WAL/artifact open 直前の identity 再照合が必要。
- allowlist は campaign WAL だけでなく calibration JSON/MD、floor binary store、oracle budget、run marker、result/report の全 durable write root に適用する。
- repo が `/scr` 上なら、source/build は許しても output は永続 root へ分離する。現 floor CLI は出力先固定なので、ジョブを `/work` clone から走らせるか、追跡済み launcher だけが使える narrow output-root 面が必要。
- read-only report/replay にまで layout 構築時の write allowlist を強制しない。書込み capability を取得する時点で検査する。

### {severity: High / PID 可視性, 自 PID／自 child canary は他 UID・他 PID namespace の不可視性を証明しない}

攻撃シナリオ: `/proc` が `hidepid=2` の環境では、自分と自分の child は見えるため canary が成功する一方、別ユーザーの ycsb は見えない。コンテナ／PID namespace でも同じで、canary は見えるが host 側の competitor は不可視になる。その後の通常 probe は `rc==1 + 空` を正常な無競合として返す。

根拠:

- 現分類器は `rc==1`＋両 stream 空を無競合とする: `orchestrator/calibrator/runner.py:94-146`
- 実 probe は同分類器をそのまま使用: `orchestrator/calibrator/runner.py:149-181`
- floor も同じ分類器へ委譲する: `orchestrator/campaign/s8b_floor_campaign.py:548-579`
- Pegasus は node allocation を専有保証とみなせない: `docs/pegasus-runbook.md:247-250`

提案（最小修正）:

- canary は通常 probe と同じ `ycsb_.*\.exe` に一致する unique nonce 付き blocking child とする。
- child の起動完了を pipe 等で同期し、生存中に同じ pgrep を一回実行する。exact PID＋nonce が存在することを要求し、その一行だけ除外する。他の canary も competitor として残す。
- `rc==1 + 空` という低水準 classifier 契約は変更しない。composite wrapper が「canary 生存中の rc==1」を visibility failure に反転する。
- `finally` で terminate/kill/wait、pgrep 自体にも timeout を付け、PID reuse は `/proc/<pid>/stat` starttime と nonce で防ぐ。
- それでも own-UID visibility しか証明できないため、`/proc` mount option に `hidepid` がないことと、host PID namespace であることを別 attestation として必須化する。host visibility を証明できない環境では登録を拒否する。

### {severity: High / F3・calibration, U3 の一回限り pre/post probe では長時間 calibration の汚染を防げない}

攻撃シナリオ: global pre-probe 後に competitor が起動し、sweep の一部と重なって post-probe 前に終了する。両 probe は成功する。また開始時 load が静定しなくても現在実装は note を付けて続行し、登録候補 JSON を通常 path に公開する。

根拠:

- U3 候補は `pre-probe → calibrate → post-probe`: `plan-env-contract-pegasus.md:91-93`
- calibration 本体は pgrep を呼ばず、開始時 settle のみ: `orchestrator/calibrator/sweep.py:132-180`
- `settled=False` は停止でなく note: `orchestrator/calibrator/sweep.py:156-165`
- 結果は CLI 終了前に通常 path へ直接書かれる: `orchestrator/calibrator/cli.py:152-165`

提案（最小修正）:

- registration mode では各 `measure_point` を canary付き pre/post probe で囲む。どれか一回でも不可視・競合・probe error が出たら calibration 全体を invalid にする。
- 開始時 `settled=False` は Pegasus registration では fatal にする。
- JSON/MD は `.pending`／quarantine に書き、最終 post-probe、walltime、attestation、script hash 検収後にだけ atomic publishする。
- U4 は `terminal=completed` の enforcement receipt がない artifact を拒否する。単なるファイル存在＋sha256一致では足りない。

### {severity: High / buildcache identity, contract SHA 追加だけでは過剰分離かつ不十分で、旧 cache 誤ヒットも残る}

攻撃シナリオ:

- 同じ hardware/toolchain/source で env tag または calibration_ref だけ変わると、バイナリ意味論は同じでも全 rebuild になる。
- 逆に同じ contract のまま module が更新され、`g++-13` が別実体・別 versionになっても現 key は同じで旧 binary に hit する。
- contract SHA を40-bitの既存 hash pre-imageへ足すだけでは、旧 entryとの衝突時に pre-image照合がなく誤 hit する。既定 env だけ contract を省略する「後方互換」を入れれば旧 cache を確実に再利用してしまう。

根拠:

- contract SHA は env tag、clocks、numactl、isolation、calibration ref を含むが toolchain は含まない: `orchestrator/campaign/env_contract.py:83-144`
- cache key は compiler の指定文字列しか含まず、digest は10 hex: `orchestrator/campaign/buildcache.py:105-119`
- stock/default toolchain は旧 key 温存のため省略する先例がある: `orchestrator/campaign/buildcache.py:108-116`
- hit 判定は binary の存在から始まり、完全 pre-image manifest を照合しない: `orchestrator/campaign/buildcache.py:176-189`

提案（最小修正）:

- runbook 裁定どおり contract SHA は exact 64 hex の directory namespaceにする。例: `contracts/<contract_sha256>/<full_build_digest>/`。10 hex は表示用途に降格する。
- namespace内に exact pre-image＋full digest＋binary hash＋completion marker を保存し、hit ごとに全照合する。
- toolchain manifest hash（compiler realpath/version、CMake version、関連 flags/module provenance）も build digest に含める。
- v2 経路では contract SHA を必須引数とし、空／optional fallbackを禁止する。legacy caller は別 wrapper／legacy namespaceへ明示的に隔離する。
- 同一 build input の env 間再利用はバイナリ意味論上は可能だが、今回の裁定は contract namespace 分離を要求している。まず rebuild を受容するのが最小で安全。後日最適化するなら、contract namespace内の検証済み pointer から immutable CAS を共有する。
- trace bit は現行どおり独立 pre-image に残し、2 contract × trace on/off の4通りがすべて別 namespace/keyになることを固定する。

### {severity: High / buildcache 並行性, 複数ノードが同一 key を同時 build すると CMake tree を破損する}

攻撃シナリオ: 二つの Pegasus job が同じ contract/genomeを同じ共有 cache rootでbuildする。双方が binary 不在を確認し、同じ directoryでconfigure/buildする。一方の failure cleanup が他方の build directory を削除することもできる。contract namespaceを追加しても、同じ contract内の競合なので解決しない。

根拠:

- default cache root は submodule内共有 directory: `orchestrator/campaign/buildcache.py:157-164`
- hit確認後、同じ bdir を直接 clear/configure/buildする: `orchestrator/campaign/buildcache.py:176-205`
- build失敗時は directory破棄経路がある: `orchestrator/campaign/buildcache.py:223-240`
- v2 floor/oracle も `<out_root>/s8b-build-cache` を共有する: `orchestrator/campaign/s8b_floor_campaign.py:765-770`, `orchestrator/campaign/s8b_oracle_driver.py:818-844`
- p3 worktree 経路も固定 submodule cacheへ戻す: `orchestrator/campaign/p3_s4_loop.py:790-799`

提案（最小修正）:

- keyごとに共有 filesystem 上で atomic `mkdir`／`O_EXCL` claim を取る。NFS上の `flock` semanticsを未検証のまま使わない。
- unique staging directoryでbuildし、full manifestとbinaryをfsync後にatomic publishする。
- readerは binary存在ではなくcompletion manifestをhit条件にする。
- stale claimは自動削除せず fail-closed＋手動回収にする。途中 kill 後の未完成entryを正当cacheとして再利用してはいけない。
- 少なくとも二つの実 subprocess をbarrierで同時起動する競合テストが必要。

### {severity: Medium / F9・F14・F15・F19, 現在のテスト案では leaf の健全性と production 発火を取り違える}

攻撃シナリオ: walltime leaf、allowlist predicate、canary parser、cache key unit testは通るが、production entryからcallを一行削除しても全テストが緑になる。新 leaf に `pegasus` や `/scr` を直書きしても、現AST検査対象外なので検出されない。

根拠:

- mutation gate は抽象記述のみ: `plan-env-contract-pegasus.md:101-106`
- AST対象は現在 `env_contract.py` と floorだけ: `orchestrator/tests/test_env_contract.py:44-54`
- between-run test自身が実pgrep検知を試していないと明記: `orchestrator/tests/test_between_run_floor.py:32-43`
- 実pgrepテストは利用不能環境で黙ってreturnする: `orchestrator/tests/test_calibrator.py:666-671`
- F19 real-build canaryはbuildcacheを直接呼び、v2 contract配線を通らない: `orchestrator/tests/test_s8b_floor_campaign.py:1680-1707`

提案（最小修正）:

- 負例は必ず public production entry を通し、measure/build/WAL publish の副作用がゼロであることまで確認する。
- 必須負例:

  - walltime: 欠落、0、stale、別job ID、残時間不足、clock後退
  - storage: `..`、symlink、検査後差替え、mount ID crossing、volatile repo＋persistent output
  - PID: canary不可視、rc1、早期終了、hidepid fixture、PID namespace不明
  - cache: 旧entry、別contract、別toolchain、trace4象限、二process同時build
  - G12: 二つのCLI processを同時起動し一方だけclaim成功、partial WALから全数値不採用

- AST中立性検査へ新walltime/layout/buildcache/execution_guard/oracle/calibrator配線を追加し、`pegasus`、`/scr`、Pegasus固有rootが横断コードへ漏れたら赤にする。
- Pegasus launch certificationではlive pgrep/qstat/build testをskip成功扱いにしない。前提未充足として登録を止める。

## 付帯確認への直接回答

### U1 と U2 のファイル衝突

衝突します。現想定のまま並列実装してはいけません。

- U1 の attestation host拡張とU2のcalibration admissionは、双方とも `calibrator/sweep.py` を触る。
- U1のmachine-pin置換とU2のwalltime/process/storage gateは、floorの `orchestrator/campaign/s8b_floor_campaign.py:2121-2141` とoracleの `orchestrator/campaign/s8b_oracle_driver.py:447-490` の同じpreflightへ入る。
- contract SHAをbuildへ渡すにはfloor、oracle、`pipeline.py`の変更が必要で、U2の現ファイル素集合には収まらない。
- execution receiptへjob/deadline/durable-root証拠を載せるなら `execution_guard.py` も共有編集面になる。

最小の分割は、先に共有 `LaunchContext/ExecutionReceipt` interfaceを確定し、U1をland、その後U2をrebaseして実走結線することです。あるいはU1/U2のleafを並行作成し、同じcommit前の専用integration unitでfloor/oracle/calibratorへ結線します。

### output_root 上書き・影響利用箇所

書込み経路:

- generic campaign: `orchestrator/campaign/loop.py:38-47`
- S1: `orchestrator/campaign/s1_direct_comparison.py:227-229,592-607`
- screening: `orchestrator/campaign/screening_driver.py:72-90`
- floor: `orchestrator/campaign/s8b_floor_campaign.py:2089-2094,2172,2226,2366-2375`
- oracle＋CLI override: `orchestrator/campaign/s8b_oracle_driver.py:567-569,680-697,994-1005`
- `env_scope_dir` default利用: `orchestrator/campaign/between_run_floor.py:111-117`、`orchestrator/campaign/backoff_profile.py:184`
- layoutを通らない独立override: `orchestrator/calibrator/cli.py:75-76,97-103,152-163`

read-only consumerまでlayout構築時に拒否すると壊れる箇所:

- `orchestrator/campaign/replay.py:88-113`
- `orchestrator/campaign/s1_report.py:951-973`
- `orchestrator/campaign/s8b_oracle_report.py:511-524`
- `orchestrator/campaign/layer3_report.py:296-311`

`tmp_path`／任意rootを使う主なテスト群:

- `test_campaign.py`
- `test_layer3_report.py`
- `test_s1_direct_comparison.py`
- `test_s1_report.py`
- `test_s8b_binding_driftguards.py`
- `test_s8b_floor_campaign.py`
- `test_s8b_freeze_io.py`
- `test_s8b_materialization.py`
- `test_s8b_oracle_driver.py`
- `test_s8b_oracle_report.py`
- `test_s8b_ratified_freeze.py`
- `test_screening_driver.py`
- `test_screening_opt_in.py`

したがって、`campaign_layout()`／`env_scope_dir()` の無条件拒否ではなく、mutating entryが取得する write capability に policyを注入すべきです。テストは `tmp_path` 自体を一時的なapproved rootとして注入できます。

### failures.md 型タグ

- F3: own-child canaryによる他UID不可視、calibrationの`settled=False`続行、global pre/postだけの時間窓で再発。
- F9/F14: optional deadline、`contract_sha256=""` fallback、未結線leaf、未消費`single_process`、AST対象漏れが恒真面。
- F15: mock pgrepだけ、実pgrep skip、bind mount/NFS/二node buildを含まない母集団が該当。
- F19: buildcache leaf直呼びだけでproduction floor/oracle materialization・namespace・publishまで通さない場合に再発。

### プラン §0 不変条件からの逸脱

現案で特に危険なのは次です。

- 較正前に暫定Pegasus registry entryを置く: 「登録は計算ノード較正実測が前提」に違反。
- 横断コードへ`pegasus`、`/scr`、`/work/SFC/...`を直書き: D59違反。
- default envだけ旧cache namespaceへfallback: contract SHA分離要件違反。
- contract namespace追加時にtrace bitを落とす／共有する: 絶対規律1違反。
-途中kill後のoracle完了行を数値として残す: G12違反。
- unsettled／canary不明のcalibration artifactをregistry参照に採る: 実測照合必須条件と規律4違反。

official mode拒否、正式計測正本`linux-baremetal`据え置き、異env throughput非混合はU2で変更する必要がありません。

## 確認済み事項

- `classify_competing_probe` の低水準rc契約自体は堅いです。`rc==1`でもstdout/stderr付随、`rc==0`空、`rc>1`をfail-closedにしており、own PID以外を落としません (`orchestrator/calibrator/runner.py:103-146`)。
- floorのpost-probeはmeasure例外後にも実行され、probe不能時はterminal aborted、result未発行になります (`orchestrator/campaign/s8b_floor_campaign.py:1494-1505,2324-2330`)。
- `campaign_id` のpath traversalは既にslug関所で拒否されます (`orchestrator/campaign/layout.py:76-84`)。
- oracleの同一freeze root・同一campaignに対するmarker＋`O_EXCL` lockは、同じclone内の並行／output-root付替えを防げています (`orchestrator/campaign/s8b_oracle_driver.py:520-564`)。
- 現buildcacheはtrace bitをpre-imageとdirectory suffixの双方へ残し、perf hit時にもtrace symbol検査を行います (`orchestrator/campaign/buildcache.py:105-119,176-184`)。
- `contract_sha256` は全contract fieldのcanonical JSONから得るfull SHA-256で、namespace材料として十分強いです (`orchestrator/campaign/env_contract.py:129-144`)。
- floorのcontent-addressed binary storeはunique temp＋hard link＋書込後full hash照合を行っており、buildcacheより強い並行publish構造です (`orchestrator/campaign/s8b_floor_campaign.py:1226-1265`)。
- floorは完走前にpublic resultを出さないため、途中killからresult数値を採る正規経路は確認できませんでした。問題は主にoracle report側です。

## C1 逐語 (attestation / machine-pin 格上げ)

## 所見

### {severity: Critical / 契約・fail-open, 素の A2 では「Pegasus だけ必須」を表現できない}

攻撃シナリオ: 実装を「calibration JSON に profile があれば照合、なければ既存 machine-pin」とする。Pegasus JSON が生成不備・schema drift・誤登録で profile を欠くと legacy 分岐へ落ちる。そこで CLI・環境変数・設定ファイルが `pegasus` を返せば、CPU 等を一項目も照合せず受理する。これは `docs/pegasus-runbook.md:268-272` とプラン §0 の必須条件への直接違反。

既存 linux JSON は実際に attestation field を持たないため、この非対称は避けて通れない (`output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:1-16`)。また、env 固有分岐を新 leaf に `if env_tag == "pegasus"` と書いても、AST 検査対象は現在 `env_contract.py` と floor driver の二つだけであり、新 leaf・`execution_guard.py`・oracle driver は検査されない (`orchestrator/tests/test_env_contract.py:51-54,383-388`)。

最小修正:

- A2 を採るなら、profile の単なる「存在」ではなく、hash 束縛された `calibration/v2` schema 自体に `attestation.mode=required` を必須化する。v2 で field 欠落・未知 mode は拒否する。
- schema 無しの既存 linux JSON は、任意の欠落 artifact ではなく、現在の正確な legacy `contract_sha256` だけを grandfather する。
- より明快なのは、契約に小さい `attestation_mode` だけを追加し、値は A2 に置く hybrid。現在は hash 移行コストがまだ小さい。
- `test_env_contract.py` は AST 対象外なので (`:15-17`)、U4 で `pegasus` が必ず v2/required artifact を参照する env 固有 invariant を置ける。
- 新 `env_attestation.py`、`execution_guard.py`、floor、oracle を AST 対象へ追加する。`isolation_policy` を required 判定の代理にしてはいけない。

候補別には、A1 は明示性が高いが calibration との値重複、A2 は同一ジョブの値を同居できるが上記 versioning が必須、A3 は二つの artifact が別ノード・別時刻で採取される整合性リスクを増やす。純 A2 は reject、versioned A2 または hybrid が妥当。

### {severity: Critical / 束縛・TOCTOU, A2 が前提とする calibration sha256 は本番経路で検証されていない}

攻撃シナリオ: 登録後に同じ calibration path を cygnus 上の再校正結果へ差し替える。registry の SHA と protocol/receipt の `contract_sha256` は旧値のままだが、attestation loader が path の現在内容だけを読む実装なら、cygnus profile を期待値として cygnus を受理できる。

`contract_sha256` は確かに `calibration_ref.sha256` を含む (`orchestrator/campaign/env_contract.py:129-144`)。しかし実ファイルとの照合はテストにしかなく (`orchestrator/tests/test_env_contract.py:268-273`)、floor/oracle 本番経路は ref の bytes を読んでいない (`s8b_floor_campaign.py:2121-2136`, `s8b_oracle_driver.py:471-490`)。さらに calibrator は同じ thread/workload stem を通常の `"w"` で上書きする (`orchestrator/calibrator/cli.py:152-165`)。

SHA-256 自体の束縛が暗号学的に破れるわけではない。問題は「実行時に束縛を検証していないこと」と「通常の再校正が同一 path を上書きすること」。

最小修正:

- ref を一度だけ `read_bytes()` し、その同じ bytes を hash 検証後に JSON parse する。hash 後に path を再読しない。
- exact schema、duplicate key、型、未知 field、`env_tag`、TSC 値の契約との cross-field 一致を検査する。
- 登録済み artifact は create-only/content-addressed path にする。現在の stem を登録済み成果物に使い回さない。
- 更新は新 path・新 contract identity とし、旧 bytes と旧 resolver を残す。同じ path の後差し替えを運用として禁止する。

### {severity: Critical / 真実源・登録汚染, A2 は誤った機械を正解として自己登録できる}

攻撃シナリオ: cygnus で `calibrate --env-tag pegasus --clocks-per-us ...` を実行する。`_host_info()` は実行中の機械をそのまま記録するため、その JSON を U4 で登録すると「Pegasus の期待 profile = cygnus」になる。その後 cygnus で Pegasus protocol を走らせても、厳密な attestation が完全一致して通る。

根拠:

- CLI の env tag と clock override は呼び手が自由に指定できる (`orchestrator/calibrator/cli.py:57-74,138-150`)。
- host profile は現在プロセスの値を自己申告的に採る (`orchestrator/calibrator/sweep.py:151-154`)。
- runbook は bnode 上のジョブ取得を必須とする (`docs/pegasus-runbook.md:265-272`)。
- U3 は qsub を予定しているが、U4 の登録受理条件にジョブ provenance の機械検査がまだない (`plan-env-contract-pegasus.md:91-95`)。

機側 env-tag 候補の評価:

| 候補 | 事故・偽装面 | 判定 |
|---|---|---|
| CLI 引数 | protocol と同じ値を利用者が二度入力するだけで恒真 | 期待 contract の選択にのみ使用可 |
| 環境変数 | 通常は利用者が設定・上書き可能。PBS 風の値も単独では証明にならない | 補助 provenance のみ |
| attestation 逆引き | 異なる env が同じ正規化 profile を持つと曖昧。scheduler/toolchain を証明しない | exact 1 件一致・曖昧なら拒否。ただし自動 env 選択には使わない |
| 設定ファイル | repo/home 配下なら自己申告・stale。別マシンへのコピーも容易 | root-owned/read-only または署名検証済みの場合だけ補助的な真実源 |

最小修正: env_tag の期待値は凍結 protocol/manifest だけから得て、それに現在 probe を照合する。新しい machine-env CLI/env は作らない。登録時には、bnode hostname、scheduler job/allocation、raw probe、取得時刻、CCBench/toolchain/job script の digest を共同 manifest へ束縛し、runbook の独立既知値 Xeon 8468/48 core と照合する。clock override・fallback を使った Pegasus artifact は登録拒否する。

### {severity: Critical / 恒真ゲート・receipt, 「assert 後に receipt 作成」という二段 API は照合省略を許す}

攻撃シナリオ: driver の一方で `assert_machine_pin` の呼出しを落とす、または floor の `execution_receipt_fn` seam へ shape だけ正しい receipt を渡す。`build_receipt()` 自身は比較を行わず、consumer も現在は key 集合しか検査しないため、「attestation を実行していない receipt」が受理される。

根拠:

- `build_receipt()` は無条件に receipt を作る (`orchestrator/campaign/execution_guard.py:69-87`)。
- `receipt_matches_contract()` は hardware 値を比較せず、4 key の存在だけを見る (`:90-108`)。
- floor と oracle は assert と receipt 作成が別呼出し (`s8b_floor_campaign.py:2132-2136`, `s8b_oracle_driver.py:477-490`)。
- floor validator も既存 host attestation の shape 検査だけ (`s8b_floor_campaign.py:686-717`)。
- oracle report も manifest の env/hash と receipt shape の一致だけ (`s8b_oracle_report.py:544-555`)。

最小修正:

- required contract 用には `attest_and_build_receipt()` 一つに統合し、probe・比較が全項目成功した場合だけ receipt を返す。単独の `build_receipt()` から v2 receipt を生成できなくする。
- receipt v2 に profile artifact SHA、probe method/version、正規化 expected/observed、全 required field の比較結果を記録する。`passed: true` 一個だけは禁止。
- consumer は contract policy を解決して、Pegasus では v2 を必須化し比較を再検算する。v1/v2 を無条件併用すると、Pegasus が v1 receipt へ降格できる。
- probe 不能、expected/observed field 欠落、曖昧 reverse match はすべて例外にする。

receipt v2 の移行面はプランの U1 素集合より広い。少なくとも以下が対象になる。

- production: `execution_guard.py:31,69-108`、`s8b_floor_campaign.py:686-717`、`s8b_ratified_freeze.py:240-241,1803-1835`、`s8b_oracle_report.py:495-555`、oracle driver の生成呼出し。
- tests: `test_execution_guard.py:41-87`、`test_s8b_floor_campaign.py:369-379,1961-1966`、`test_s8b_ratified_freeze.py:313-322`、`test_s8b_ratified_verify.py:447-452`、`test_s8b_oracle_report.py:116-132,318-340`、`test_s8b_oracle_driver.py:1355-1383`。

v1 schema を上書きせず、legacy linux 用 v1 と attested contract 用 v2 を schema dispatch するのが最小の互換策。

### {severity: High / 計測意味論, TSC と実効クロックがプラン上で混同されている}

攻撃シナリオ: CPU が thermal throttling で大幅に低速化していても invariant TSC は同じ速度で進むため、`clocks_per_us` は契約値に一致して pass する。逆に「実効クロック」を一回の値へ狭く固定すると、正常な turbo/governor 変動で正当ノードを拒否する。許容幅を広げれば別 SKU や設定不良を通す。

`tsc.py` 自身は、TSC がコア周波数変動と無関係だと正しく明記している (`orchestrator/calibrator/tsc.py:4-11`)。したがって runbook の「実効クロック」と同じ値ではない。加えて、probe 不能時は 2100 へ fallback し (`sweep.py:120-129`)、CLI から実測自体を省略できる (`cli.py:71-72`)。これは Pegasus 必須 attestation には使えない。

一回の campaign-start probe だけでも不足する。floor は attestation 後に全 cell を build する (`s8b_floor_campaign.py:2121-2136,2221-2224`) ため、実測時点の thermal state と離れる。

最小修正:

- `tsc_mhz` と `effective_clock` を別 field・別 comparator にする。
- TSC は `constant_tsc/nonstop_tsc` の実確認、実測 source の記録、狭い計測誤差だけを許す。required env では fallback/CLI override を禁止する。
- 実効クロックは標準化した pinned load 下の APERF/MPERF、cycles/ref-cycles 等の検証済み方法で測り、governor・turbo policy も記録する。
- 許容幅は単一サンプルへの恣意的な ±N% でなく、複数の独立 job/node の分布から事前確定する。CPU identity は CPUID/topology の exact match に任せ、clock tolerance を機種識別に使わない。
- static hardware は campaign 前、動的 clock/thermal gate は session/round の直前・必要なら直後にも検査する。失敗時に幅を後付けで広げない。

### {severity: High / profile 粒度・正規化, 現行 host/cache probe を attestation に流用すると別構成を通す}

攻撃シナリオ:

- `os.cpu_count()` が host 全体の 48 を返す一方、PBS/cpuset の実利用可能 CPU が 47 しかない。
- LLC 総量だけが同じで、LLC instance/shared-core topology の異なる機械が通る。
- sysfs の一部だけ読めず、`detect_l3_bytes()` が読めた cache だけを合計して正値のように返す。
- CPU model 名の空白・`(R)`・周波数 suffix の揺れだけで正常 node を拒否する。
- 1 socket を「1 NUMA」と仮定するが、BIOS の SNC 設定で複数 NUMA node が見える。

現行 `_host_info()` は node/machine/cpu_count/kernel の文字列だけ (`orchestrator/calibrator/sweep.py:27-33`)。L3 probe は OSError を skip し、一部でも読めれば合計を返す (`:48-69`)。これは calibration の best-effort 下限検出には妥当でも、必須 attestation には不十分。

最小修正:

- 新 leaf の単一 strict probe を calibration と runtime の両方で共有する。
- CPU は normalized marketing name だけでなく vendor/family/model 等の安定識別子を持ち、raw 名も証拠として残す。
- configured/online/affinity/physical/logical core、threads-per-core を分離し、gen_S では利用可能 48/48・SMT off を exact 検査する。
- cache は level/type/bytes/line size/shared CPU set ごとの canonical topology とし、総量だけにしない。
- NUMA は node ID と normalized cpulist/memory topology を sort 済み構造で比較する。
- required field の読取り失敗や部分取得は `None` や skip でなく全体拒否にする。

ハード更改・部分故障縮退・SNC 変更は拒否になる。それが正しい fail-closed 動作であり、運用は再投入/対象 node 隔離へ倒す。同一 `pegasus` に複数 profile を許すと throughput を混ぜるため、新 env-tag または全 consumer の `(env_tag, contract_sha256)` 分離が必要。

### {severity: High / versioning・移行コスト, A1/A3 の破壊コストは今は小さく、A2 でも将来回避できない}

A1/A3 で dataclass field を増やすと `asdict(self)` により linux-baremetal の hash も変わる。直接壊れる箇所は次の通り。

- dataclass exact field と独立 hash golden: `orchestrator/tests/test_env_contract.py:282-289,296-346`
- field が必須なら constructor: 同ファイル `:57-67,314-322`、`test_s8b_floor_campaign.py:782-786`
- protocol の current contract hash と protocol 全体 SHA golden: `test_s8b_protocol_builder.py:45-61,89-103`
- 旧 protocol の current-registry 照合: `s8b_floor_contract.py:137-150`
- 旧 receipt の current contract 照合: `s8b_floor_campaign.py:686-695`
- ratified artifact の再検証: `s8b_ratified_freeze.py:2562-2572,2661-2663,2710-2715`
- oracle manifest の current contract 照合: `s8b_oracle_driver.py:482-489`

ただし、実 protocol 凍結はまだスコープ外 (`plan-env-contract-pegasus.md:111-114`) で、repo 内 `output/**` に現行 contract hash を持つ保存済み artifact は見つからなかった。現時点の A1 は主に 2 golden 値、独立 reference、数個の constructor を更新する小～中コストであり、「大量の既存成果物が壊れる」は現状では過大評価。

一方、A2 でも calibration SHA を更新すれば contract hash は変わるため、将来の更改問題は同じ。現 verifier は env_tag から「現在の一契約」だけを引くので、旧凍結 artifact を再検証できなくなる。

最小修正: schema 判断は今行う。A1/A3 を選ぶなら一度の hash churn を受け入れる。互換性のため `None` field を canonical JSON から黙って除外すると、その policy が hash 非束縛になるので不可。将来は immutable contract version を残す resolver、または hardware profile 変更時の新 env-tag を使う。

A3 はさらに calibration と sidecar が同じ job/node/boot 由来であることを joint manifest で証明しなければならず、純粋な移行コストは A2 より高い。

### {severity: High / 実装分割・裁定漏れ, U1 と U2 の想定ファイル集合は素ではない}

攻撃シナリオ: U1/U2 を並列実装し、競合を避けるため U2 が floor/oracle を触らない。その結果、buildcache namespace や walltime gate が oracle に配線されず、runbook の「floor / oracle で必要」な enforcement が片側だけ恒真になる。

直接衝突は少なくとも次の通り。

- U1 は `sweep.py::_host_info`、U2 の calibrator pgrep admission も `calibrate()` 周辺を変更する (`sweep.py:151-168`)。
- U1 は floor/oracle の preflight を変更する。U2 の walltime も同じ「副作用前」地点へ必要。
- buildcache に contract hash を渡すには floor の `build_cells()` 呼出し (`s8b_floor_campaign.py:765-782,2221-2224`) と oracle の pipeline/cache_root 結線 (`s8b_oracle_driver.py:818-845`) が必要。
- U2 の想定一覧は oracle driver を含まない (`plan-env-contract-pegasus.md:86-97`)。

最小修正: leaf 実装は並列でも、`sweep.py` と floor/oracle の shared preflight/call-site 結線は一つの統合単位として逐次化する。少なくとも U1 → shared adapter → U2、または integration owner を一人に固定する。U2 完了条件に floor と oracle 双方の副作用前 negative test を入れる。

### {severity: High / F15・F19, U1 が実 JSON・実 driver 分岐を通らないまま完了できる}

攻撃シナリオ: comparator 単体の hand-made dict テストは通るが、実 calibrator serializer が field 名・型・clock source を別形で出す。U1 時点では Pegasus registry entry がなく、既存 1549 tests は linux legacy branch だけを通って緑になる。欠陥は qsub 後の U4 または最初の floor/oracle で初めて発覚する。

プランは U1 と実 calibration/U4 を分離し、実 artifact は後から入れる (`plan-env-contract-pegasus.md:86-95,101-108`)。これは F15 の「実出力分布を含まない mock」と F19 の「実体化経路まで届かない positive control」の再発形である (`docs/failures.md:141-151,214-229`)。

最小修正:

- hand-made JSON だけでなく、`result_to_dict()` が生成した v2 fixtureを loader→contract→guard→receipt consumer まで通す。
- 実 bnode artifact を U4 前の代表 fixture として採取・固定する。
- 負例を field ごとに実発火させる: CPU model、core、cache topology、NUMA、TSC、effective clock、expected/observed 欠落、probe 例外、hash mismatch、ambiguous reverse match。
- floor と oracle それぞれで、失敗時に run dir/WAL/budget/build が一切作られないことを検査する。
- 高水準 `execution_receipt_fn` を mock せず、low-level probe だけを差し替えて production comparator を通す。
- mutation positive control として「comparator が常に pass」「driver の attestation 呼出し削除」「Pegasus に v1 receipt」をそれぞれ赤にする。

## 付帯確認への直接回答

- §0・発効済み裁定との整合: プランの official 拒否、`linux-baremetal` 正本据え置き、Pegasus throughput 非混合、isolation policy 自体は逸脱していない。ただし、A2 の field-absence fallback、TSC を実効クロック扱いする実装、oracle に U2 enforcement を配線しない実装はそれぞれ §0/runbook 違反になる。
- A2 の linux 非対称: 既存 JSON を改変して揃えてはいけない。calibration SHA、linux contract hash、既存 calibration source ref が変わる。既存 bytes は明示的な legacy v1 として凍結し、新規 Pegasus は v2/required にする。
- A2 の後差し替え: hash を実行時検証すれば内容更新は拒否できるため、SHA 自体は破れない。現状は本番検証がなく、かつ CLI が同じ path を上書きするので、運用上の穴がある。
- U1/U2 のファイル素集合: 素ではない。`sweep.py`、floor driver、oracle driver が確実に共有面になる。設計次第では `execution_guard.py` も共有面になる。
- F9/F14: profile 欠落の legacy fallback、静的 AST 対象漏れ、`passed:true` receipt、assert/build の二段 APIが再発面。
- F15: linux branch と hand-made mock だけで 1549 tests が緑になる面がある。
- F19: 実 calibrator JSON、実 qsub provenance、registry、両 driver、receipt consumer の連結が U4/本走まで遅延している。
- 既存 1549 tests の移行: contract field 追加だけなら直接影響は数個の golden/constructor で小～中。receipt v2 は production 約5ファイル、fixture/test 約6ファイルへ波及する。v1 を破壊せず schema dispatch すれば既存 journal の互換性を保てる。

## 確認済み事項

- 現行 `contract_sha256` は全 dataclass field、従って `calibration_ref.sha256` を確実に含む (`env_contract.py:129-144`)。
- registry は read-only で未知 env を fail-closed にし、現行コードのままなら Pegasus protocol は linux machine-pin で正しく拒否される (`env_contract.py:167-179`, `execution_guard.py:56-66`)。
- floor/oracle とも現行 guard は最初の run directory/WAL 作成より前に置かれており、fail-fast の位置自体は適切。
- AST 検査核は positive control を持ち、現在列挙されているモジュールに対しては恒真ではない (`test_env_contract.py:391-426`)。問題は対象列挙の狭さ。
- `detect_l3_bytes()` の `shared_cpu_map` 重複排除は、sysfs が完全に読める場合の aggregate L3 計算としては妥当。
- `tsc.py` 自身は invariant TSC と実効コア周波数を正しく区別している。混同はプラン側の用語・照合設計にある。
- official mode は production wrapper で無条件拒否され、pilot は refreeze eligible にならない (`s8b_floor_campaign.py:147-156,2049-2076`)。
- read-only の静的レビューのみで、ファイル変更および 1549 tests の再実行は行っていない。
## C3 逐語 (calibration ジョブ設計・U4 結線)

## 所見

### {severity: Critical / 検収・裁定違反, calibrator の「完走」は採用可能性を証明しない}

攻撃シナリオ: TSC helper のビルド失敗時は実測値でなく 2100 へ fallback する。build 後の load1 が閾値超でも注記だけで続行し、within-run CV が 5% 超でも `high_variance=True` にするだけである。さらに一部 rep の失敗を残りの rep で受理し、noise-floor 点の失敗 notes は JSON に引き継がれない。これらでも CLI は確定名 JSON を書き、終了コード 0 を返す。U4 の現行テストはその bytes の hash しか見ないため、ログインノード値・外乱・部分測定を束縛した registry entry が成立する。

根拠: [sweep.py:120–196](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:120)、`orchestrator/calibrator/runner.py:225-239,275-314`、`orchestrator/calibrator/cli.py:130-172`、`orchestrator/tests/test_env_contract.py:268-273`、`docs/decisions.md:319-337`。

提案（最小修正）: certification 用の明示的な採否判定を U3 に置く。次をすべて満たす場合だけ `quality.status="accepted"` とし、それ以外は非 0 終了＋run-scoped の rejected 成果物だけを残す。

- TSC は実測由来で、override/fallback なし
- 静定 gate 成功
- 全 rep が期待本数そろい、各 subprocess が rc=0
- 必須 perf counter、L3、maxrss が欠損なし
- `saturated or lower_bound_selected`、records > 0、cache-floor 警告なし
- within-run `cv` が非 null かつ 5% 以下
- 全 measurement window の単独性 gate が成功
- post attestation が pre と整合

失敗時は rep の選別や途中再開をせず、別 allocation で全 calibration を取り直す。再試行回数も事前に有限化する。

### {severity: High / 単独性・恒真ゲート, 全体 pre/post pgrep と self-canary では shared node の無汚染を証明できない}

攻撃シナリオ: `stress-ng`、Java、GPU workload、メモリ帯域負荷など `ycsb_.*\.exe` 以外の他ユーザープロセスは検出されない。また、長い calibration の途中だけ起動・終了した ycsb は全体の pre/post probe をすり抜ける。自 PID が見える canary は同じ UID/PID namespace の可視性しか証明せず、`hidepid` 下の他 UID 不可視を検知できない。一定の外部負荷なら CV も低いまま全 throughput を偏らせられる。

根拠: [runner.py:149–181](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:149)、`docs/pegasus-runbook.md:45-50,245-252,265-275`、`docs/decisions.md:2290-2293`、`plan-env-contract-pegasus.md:91-93`。

提案（最小修正）:

- `/proc` の `hidepid`、PID namespace、他 UID の可視性を記録し、node-wide visibility を証明できなければ fail-closed
- NQSV 側で同一 host への他 job allocation を照会できるか実機 canary で確定し、使えるなら一次 gate にする
- ycsb probe は calibration 全体でなく各 measurement point、できれば各 rep の直前・直後に実行
- job 外プロセスの CPU-time delta、load/PSI、メモリ・I/O pressure を補助 gate として記録
- いずれかが発火したら当該 rep だけでなく calibration attempt 全体を不採用

self-canary は「pgrep が完全に壊れていない」証拠に限定し、他ユーザー可視性の証明には数えない。

### {severity: High / 計測状態, build 後 20 秒の非強制 settle では熱・load 状態を切れない}

攻撃シナリオ: 計算ノード上の parallel build が load1、cache、温度、周波数状態を残した直後に calibration が始まる。現行 `settle()` は閾値 4.0、timeout 20 秒で、失敗しても続行する。attestation の「実効クロック」を build 直後に採れば、登録値自体が一時状態に依存する。

根拠: [runner.py:38–57](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:38)、`orchestrator/calibrator/sweep.py:156-165`、`docs/pegasus-runbook.md:163-164,249-250`。

提案（最小修正）: 手順を次に分ける。

1. allocation・CPU topology の静的 attestation
2. pinned-clean build
3. build 子孫終了と binary hash 確定
4. 事前凍結した load 閾値を複数回連続で満たすまで cooldown。timeout は失敗扱い
5. dynamic clock/frequency policy と単独性の pre-receipt
6. calibration
7. post-receipt

`TMPDIR=/scr/<job-id>` は Python 起動前に設定し、TSC helper・使い捨て CCBench worktree・run 一時物だけに使う。JSON、receipt、ログの唯一コピーは永続領域へ置く。

### {severity: High / 計算ノード証明・schema, `bnodeXXX` 文字列は allocation の証明にならず A2 schema も未成立}

攻撃シナリオ: 現行 `_host_info()` は hostname などを記録するだけで拒否しない。ログインノードで `--env-tag pegasus` を指定しても構造的には通る。逆に hostname 命名が変われば正当な計算ノードを誤拒否する。さらに `CalibrationResult.host` は `Dict[str,str]` で、CPU/cache/NUMA の構造化 profile や scheduler receipt を格納する契約がない。

根拠: [sweep.py:27–33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:27)、`orchestrator/calibrator/model.py:191-207`、`orchestrator/calibrator/report.py:72-84`、`docs/pegasus-runbook.md:265-272`。

提案（最小修正）:

- U1 で versioned な top-level `attestation_profile` と `acquisition_receipt` を定義する
- qsub 応答 ID、job 内 `$PBS_JOBID`、`qstat -f` の assigned host、実 hostname を相互照合する。環境変数だけはユーザーが偽装できるため不足
- queue/project/node count/cpuset=48/HT off を receipt に含める
- hostname は取得 provenance に置き、runtime hardware equality の対象にはしない。別 bnode でも同 profile なら通す
- scheduler 照合方法が NQSV 上で成立するか、小さい job で positive/negative canary を先に行う

したがって実測順序は厳密に U1 → U2 → U3。U3 のコード実装だけを並行するなら、U1 schema/API を先に凍結する必要がある。

### {severity: High / forensic binding, 外部 manifest は CalibrationRef の証拠連鎖に入らない}

攻撃シナリオ: 現行 JSON は module、compiler、CCBench pin、job script、binary hash、superproject source を持たない。U3 が別 manifest にそれらを書いても、U4 の `CalibrationRef` が calibration JSON だけを hash 束縛すれば、その manifest は交換・欠落可能である。また gen_S 待ち 20 本の間に共有 worktree の orchestrator code や pin が変われば、qsub 時と実行時の source が異なる。

根拠: [report.py:72–84](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/report.py:72)、`orchestrator/campaign/env_contract.py:63-79`、`docs/pegasus-runbook.md:163-164,254-278`、`docs/decisions.md:2282-2288`。

提案（最小修正）: 既存の「JSON → CalibrationRef」を維持するなら、採否に必要な provenance を JSON 内へ入れる。

- qsub 前に U1–U3 を含む superproject commit を固定する。未コミットで投入するなら全対象 source の canonical digest を固定し、job 開始時に再照合
- exact-version の `module load`。`module -t list 2>&1`、依存 module、compiler 実体 path/version、cmake/perf/numactl/python version を構造化記録
- CCBench full HEAD、pinned-clean 結果、configure/build argv、trace-disabled 検査、binary full SHA-256
- job script bytes の SHA-256、PBS job/resource receipt

別案として `CalibrationRef` を bundle receipt manifest に向けるなら、U1 loader と全テストを同時に変更する。JSON と manifest が互いの hash を持つ循環設計にはしない。

### {severity: High / 成果物トランザクション, 固定名への `open("w")` は kill と再実行で provenance を破壊する}

攻撃シナリオ: JSON を書いた後、MD・post gate・manifest 前に kill されると、確定名に正常に parse できる未検収 JSON が残り得る。再実行は同じ workload 名を無条件 overwrite し、登録済み hash を壊す。NQSV の `.o<ID>` / `.e<ID>` は job 終了後に投入 directory へ戻るので、job 内で作る manifest には会計 summary を含められない。

根拠: [cli.py:152–172](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/cli.py:152)、`docs/pegasus-runbook.md:103-106,221-231`、`docs/decisions.md:333-336`。

提案（最小修正）:

- `attempts/<sanitized-job-id>/` の永続 staging に create-only で生成
- post gate と schema 検証後だけ accepted receipt を作る
- canonical path は atomic・create-only publish、または U4 が run-scoped path を直接参照
- signal/walltime kill は staging の rejected/incomplete attempt だけを残す
- job-side manifest と、終了後に login-node の薄い collector が `.o/.e`・会計 summary を加える final receipt を分ける
- stderr は module list と NQSV 会計 summary が入るため、「空であること」を成功条件にしない

登録後の JSON は手直し禁止。修正が必要なら旧 bytes を保存し、修正版 code で新 attempt を再実測し、必要なら `supersedes_sha256` を持つ新 artifact と registry/golden を同じ commit で差し替える。

### {severity: High / walltime・有界性, end-to-end 上限が定義されず、入力 0 なら sweep 自体も無限になる}

攻撃シナリオ: 既定値なら sweep は 1m, 2m, 4m, 8m, 16m の 5 点で有限だが、CLI は正数検証をしない。`start_records=0` では `rec *= 2` が永遠に 0 である。正常な既定値でも最大 31 bench rep、各 timeout 120 秒なので bench 部分だけで最大 3720 秒＝62 分。buildcache の configure/build には timeout がなく、runbook の 30 分例を転用すると scheduler kill が起きる。

根拠: [cli.py:65–74](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/cli.py:65)、`orchestrator/calibrator/sweep.py:90-117,187-209`、`orchestrator/calibrator/runner.py:205-226`、`orchestrator/campaign/buildcache.py:323-327`、`docs/pegasus-runbook.md:81-113,290-300`。

提案（最小修正）:

- `0 < start_records <= max_records <= frozen_cap`、threads=48、正の reps/extime を CLI で拒否検証
- build、probe、hash/publish に個別 timeout
- 予約式を `TSC + cooldown + points*sweep_reps*120 + noise_reps*120 + 2*sweep_reps*120 + build_cap + finalize_reserve` として成果物へ記録
- 例として build cap 15 分、finalize reserve 10 分なら最低約 87 分なので 90 分以上が必要。ただし gen_S の最大 walltime を実行時に確認する
- walltime 末尾に少なくとも rejection receipt 保存用の reserve を残す

### {severity: High / U4・テスト代表性, hash 実在検証の loop 化だけでは「別 env の正しい hash」を受理する}

攻撃シナリオ: Pegasus entry が誤って linux artifact を指していても、その hash を registry にコピーすれば現行テストは通る。`CalibrationRef.path` は非空しか検査せず、absolute path、`..`、symlink escape も可能である。また `test_lookup_unknown_fails_closed` は現在 `"pegasus"` を未知値として固定している。

根拠: [env_contract.py:63–79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/env_contract.py:63)、`orchestrator/tests/test_env_contract.py:168-186,238-250,268-273,335-346`。

提案（最小修正）:

- `REGISTRY.items()` 全 entry で path/hash を検査
- path は canonical repo-relative、`output/env/<tag>/calibration/` 配下、symlink/resolve escape なし
- JSON parse 後に `artifact.env_tag == registry key == contract.env_tag`
- artifact の `clocks_per_us == contract.clocks_per_us`
- Pegasus artifact は schema version、t48、凍結 workload、accepted quality、attestation/provenance の存在と意味を検査
- legacy linux artifact は exact path/hash の明示 allowlist に限定し、新 entry が legacy schema を選べないようにする
- Pegasus の手書き golden を追加し、unknown parameter から `"pegasus"` を削除
- wrong-env、missing-attestation、high-CV、partial-reps、1-byte mutation の positive control を置く

`ENV_LITERAL_VALUES` 同期 assert は維持し、新 tag・固有 clock・新 numactl literal を追加する。

### {severity: High / bootstrap, buildcache の contract_sha256 namespace は U3 と U4 を循環させる}

攻撃シナリオ: U2 が buildcache key に最終 `contract_sha256` を必須化すると、その SHA は calibration_ref の SHA を含む。しかし calibration JSON はその build で初めて生成されるため、U3 の build 前には最終 contract SHA を計算できない。

根拠: [env_contract.py:129–144](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/env_contract.py:129)、`plan-env-contract-pegasus.md:74-75,91-95`、`orchestrator/campaign/buildcache.py:105-119,148-210`。

提案（最小修正）: calibration bootstrap build は `patchharness.checkout(pin)` 内の job-scoped `/scr` cache root を使い、cache hit を許さない使い捨て build とする。binary SHA と全 build inputs は保存する。最終 contract namespace は U4 登録後の floor/oracle build にだけ適用する。これなら cache を共有しないため、bootstrap だけ contract SHA を持たなくても cross-env 偽 hit は起きない。

### {severity: High / 測定座標, clocks_per_us と numactl の確定規約が実測前に凍結されていない}

攻撃シナリオ: TSC は現在 `int(round(median))`、すなわち Python の ties-to-even だが、raw samples と median は捨てられる。後から別丸め規約や「実効クロック」の意味を採ると再測定が必要になる。また CLI default の `interleave=all` は、1 socket でも SNC 等で複数 NUMA node が見える場合に無根拠な policy となる。

根拠: [tsc.py:65–86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/tsc.py:65)、`orchestrator/calibrator/cli.py:71-74`、`orchestrator/campaign/env_contract.py:83-110`、`docs/pegasus-runbook.md:45-50,268-271`、`docs/roadmap.md:333`。

提案（最小修正）:

- 丸めは現行互換の「5 回の raw MHz の median を Python nearest-even で int 化」など、実測前に一意に凍結
- raw samples、median、整数値、分散、compiler を JSON に保存し、U4 は整数値の一致を検査
- `clocks_per_us` は invariant TSC rate と明記し、dynamic CPU MHz／governor は別 attestation 項目として許容差つきで扱う
- NUMA は `numactl --hardware`、allowed CPUs/mems、NUMA node cpulist を先に取得
- effective cpuset が 1 NUMA node だけなら `numactl=()` と `--numactl none` を明示
- 複数 node なら、policy と選択基準を先に凍結して pilot または deterministic rule で決める。CLI default を根拠に登録しない

### {severity: Medium / noise-floor 分離, U4 先行は条件付きで正しいが既存 between-run driver は Pegasus に使えない}

攻撃シナリオ: registry 登録を「正式比較可能」と誤解し、linux 用の 3% floor を Pegasus へ流用すると D19 の環境間ドリフト分離を壊す。また既存 `between_run_floor.py` は `p2_2` の linux env、clock、NUMA、records、threads を直接 import しており、registry entry を追加しても Pegasus 化されない。`NoiseFloor` の古い docstring も within-run を差の閾値と説明しており、取り違えを誘発する。

根拠: [between_run_floor.py:44–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/between_run_floor.py:44)、`orchestrator/campaign/between_run_floor.py:69-118`、`orchestrator/calibrator/model.py:145-171`、`docs/decisions.md:319-337`、`docs/roadmap.md:315`。

提案（最小修正）: U4 は「floor 測定を開始するための bootstrap 登録」と明記し、official 拒否を維持する。次段で env-neutral な floor driver を使うか、既存 driver を contract/workload 引数化する。Pegasus の between-run artifact が env・workload・binary・session medians と hash 束縛されるまで compare/oracle verdict を開かない。新 calibration JSON には `noise_floor.kind="within-run"` を明記する。

### {severity: Medium / 規律4・代表性, scale sensitivity は Pegasus 固有でなく 4t/1m を黙って流用する}

攻撃シナリオ: saturation は t48/L3 下限で決まる一方、artifact の scale sensitivity は CLI から変更不能な 4 threads / 1m を small とする。roadmap は固定 4t/1m の環境横断流用を明示的に禁じている。さらに module docstring には D15 以前の「入力非依存」が残るため、uniform の成果物を skew0.9 の代表として誤用しやすい。

根拠: [sweep.py:198–209](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:198)、`orchestrator/calibrator/cli.py:53-77`、`orchestrator/calibrator/model.py:10-13`、`docs/decisions.md:220-244`、`docs/roadmap.md:309-317`。

提案（最小修正）: small/medium を CLI で明示可能にし、Pegasus topology に基づいて事前凍結する。registry の主 calibration は将来の代表 domain に合わせ `skew0p9_rr50_rmw0` を使うのが妥当。uniform も対象にするなら別 JSON として測り、片方を他方へ代用しない。scale sensitivity を本 wave で裁定できないなら、無根拠な値を出すより schema 上 `not-measured` とする。

## 付帯確認への直接回答

### U1・U2・U3 の順序

実測順は U1 → U2 → U3 でなければならない。現行 `CalibrationResult` と serializer には A2 profile の格納先も accepted receipt もないため、U1 より先に実測すると JSON の後加工か再実測になる。単独性・walltime・永続領域 gate も U2 完了後でなければ U3 の完走判定に使えない。

U1～U3 のコード実装を並列化する場合も、先に次を interface として凍結する必要がある。

- calibration JSON schema/version
- attestation profile と acquisition receipt の区別
- quality status と rejection reason
- provenance の必須 field
- U2 gate の呼び出し位置と失敗意味論

### 「実測完了」の必要十分条件

次がすべてそろって初めて U4 へ進める。

1. qsub receipt: request ID、script SHA、source commit/digest、queue/project/node/walltime、投入時 qstat・budget snapshot
2. allocation receipt: PBS job ID と qsub ID の一致、scheduler assigned host と hostname の一致、gen_S / SFC / 1 node / cpuset 48
3. hardware profile: CPU model、physical/logical core、HT、cache、NUMA、allowed CPU/memory、TSC raw/rounded
4. toolchain/build receipt: module 全一覧、compiler 等の実体/version、CCBench full pin・clean、build argv、binary SHA、trace-disabled
5. isolation receipt: node-wide visibility 成立、co-allocation/重負荷なし、各 measurement window の pre/post probe 成功
6. calibration data: exact t48/workload/range、全 rep 完備、必須 perf 値あり、D15 採用条件成立、within-run CV ≤5%
7. post receipt: competing process なし、static attestation 不変、clock/frequency policy が許容範囲
8. artifact transaction: 永続 run-scoped path、schema validation 済み、accepted receipt、JSON/MD/job log/hash manifest、正常な NQSV accounting
9. U4 semantic tests・golden・実在 hash が全通過

一項でも欠ければ「完了」ではなく rejected/incomplete attempt である。

### sha256 束縛後の修正手順

登録済み JSON は in-place 編集しない。正規手順は「原因修正 → 新しい full job attempt → 新 artifact/hash → registry ref と Pegasus golden を同じ commit で更新」。旧 artifact は削除せず、少なくとも旧 SHA と不採用理由を追跡可能にする。hash だけ更新して手編集 JSON を追認するのは禁止。

### between-run floor

親仮説は条件付きで正しい。D19 上、U3 の `noise_floor` は within-run 品質 gate であり、between-run は独立 driver の責務である。したがって登録 bootstrap で between-run を同時実測する必要はない。

ただし U4 完了を「正式比較可能」と呼んではならず、Pegasus between-run floor が別段で取得・束縛されるまで compare/oracle verdict を拒否する必要がある。既存 `between_run_floor.py` は linux 固定なので、そのまま次段へ持ち込めない。

### 438 points・gen_S 待ち 20 本

この二値だけでは実走可能性を確定できない。欠けているのは gen_S の node-hour 課金規則、最大 walltime、実測 build cap、再試行予算である。20 本待ちは主に開始遅延だが、mutable worktree drift を増幅するため source freeze が必須になる。

投入直前に `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` を再取得し、1 full attempt と最大何回の fresh rerun を許すかを先に固定すべきである。module/perf/NUMA の preflight は本 job 冒頭で fail-fast させれば、別 allocation の canary 消費を抑えられる。

### §0 不変条件

プラン上の env_tag、計算ノード限定、isolation policy、official 拒否、linux-baremetal 非上書きは維持されている。一方、現行実装のままでは TSC fallback、非強制静定、部分 rep 受理、未束縛 attestation、linux 固定 between-run driver が実質的な逸脱経路になる。

## 確認済み事項

- 意図した正数引数なら sweep は 1m～16m の最大 5 点で有限であり、D15 の working-set 下限で早期終了できる。問題は入力検証・build timeout・全体予約にある。
- `/scr` で TSC helper や使い捨て worktreeをビルドすること自体は整合する。helper は同一 job 中に実行され、必要な最終成果物ではない。
- `skew0p9_rr50_rmw0` を両環境で使っても D59 違反ではない。env scope と env_tag を分け、throughput を横断集約しなければよい。
- D15 の根拠上、uniform と skew0.9 は別 calibration とする設計が正しい。
- within-run と between-run を別 artifact・別段にすること自体は D19 と整合する。
- 現行 linux registry は `calibration_t48_skew0p9_rr50_rmw0.json` の SHA `751304…eef5` と一致している。依頼に挙がった `skew0_rr50` artifact は別 SHA `ede7b0…cbf` で、registry の参照先ではない。
- `CalibrationRef {path, sha256}`、静的 `_build_registry()`、`ENV_LITERAL_VALUES` 同期という U4 の基本連鎖は妥当。欠けているのは artifact の意味検証と immutable publish 手順である。
- Pegasus 登録を実測後まで遅らせ、official mode と既存 `linux-baremetal` を変更しないプラン境界は正しい。
## §P 相談プロンプト原文

### プロンプト C1

あなたは敵対的設計レビュアー (read-only)。私は Pegasus env_contract 登録段 wave のマネージャーで、実装前のプランを攻撃してもらう。目的は「実装後に手戻りになる設計欠陥・検証の空隙・裁定違反」を実装前に潰すこと。

## 対象
- プラン: `plan-env-contract-pegasus.md` (repo 直下、untracked)。**あなたの担当は §2 論点 A (attestation 照合値の置き場所) と論点 B (machine-pin の複数 env 格上げ) = 実装単位 U1**。
- 裁定・契約の正本: `docs/pegasus-runbook.md` §7 (L259-284、登録要件と attestation 必須化)、`docs/decisions.md` D59。プラン §0 の不変条件は変更不可。
- 実装対象コード: `orchestrator/campaign/env_contract.py` (契約 dataclass / contract_sha256 L129-144 / _build_registry L147-164 / AST 検査 find_env_literals L182-227)、`orchestrator/campaign/execution_guard.py` (assert_machine_pin L56-66 / build_receipt L69-87)、`orchestrator/campaign/p2_2.py` (ENV_TAG L39)、`orchestrator/campaign/s8b_floor_campaign.py` (pin 呼び出し L2121-2145)、`orchestrator/campaign/s8b_oracle_driver.py` (L440-490 の contract/receipt 検査)、`orchestrator/calibrator/sweep.py` (_host_info L27-32, detect_l3_bytes L48-)、`orchestrator/calibrator/tsc.py`、`orchestrator/tests/test_env_contract.py` (ENV_LITERAL_VALUES L45、同期 assert L238-250、calibration_ref 実在検証 L268-273)。

## 攻撃観点 (最低限。これ以外も自由に)
1. 論点 A の 3 候補 (A1 契約 field 追加 / A2 calibration JSON 同居 / A3 別ファイル + ref field)。親の仮説は A2 優位。A2 を採ったときの具体的欠陥を挙げよ: (a) attestation 必須宣言をどこに置くか — env literal を registry 外に書けない AST 制約 (test L383-388) の下で「pegasus のときだけ必須」をどう表現するか。(b) linux-baremetal の既存 calibration JSON に attestation field が無い非対称の扱い。(c) calibration JSON の後差し替え (path 同じ・内容更新) で sha256 束縛が破れる面はないか。(d) A1/A3 の contract_sha256 変動が実際に壊す既存 golden・下流参照を file:line で列挙し、手戻りコストを見積もれ
2. 論点 B: 機側 env_tag の真実源の各候補 (CLI 引数 / 環境変数 / attestation 逆引き / 設定ファイル) について、取り違え・偽装・「linux-baremetal の cygnus 上で pegasus protocol を走らせる」型の事故をどう防ぐか。attestation pass を pin 相当に格上げする設計の fail-open 面 (probe 不能時・field 欠落時・許容幅内の別マシン) を攻撃せよ
3. 実効クロック照合の許容幅: turbo boost / スロットリング / 省電力 governor で正当ノードが偽陽性になる面と、許容幅を広げると別 CPU を素通しする面のトレードオフ。TSC (constant_tsc) と実効クロックの区別をプランが正しく扱っているか
4. NUMA / cache / core 数 / CPU model の照合粒度: gen_S 全 node 同構成前提 (runbook §1) が破れたとき (ハード更改・部分故障縮退) に何が起きるか。照合値の正規化 (文字列 model 名の揺れ等)
5. 恒真ゲート面 (failures F9/F14 型): attestation が「実際には照合していないのに pass を返す」「テストが attestation を bypass した経路で緑になる」構造的余地。負例 (別ハード値・欠落 field・probe 失敗) がテストで実発火するか
6. 既存テスト (1549 passed) への破壊的影響と移行コスト。特に execution_guard の receipt schema 変更が floor/oracle の journal 検証を壊す面

## 付帯確認
- 本プラン §2-§3 が §0 の不変条件・発効済み裁定を逸脱する箇所はないか
- U1 と U2 (layout/buildcache/walltime) の想定ファイル素集合に衝突はないか (execution_guard・floor driver の接触)
- failures.md 型タグ F9/F14 (恒真ゲート)・F15 (テスト代表性)・F19 (実体化遅延潜伏) の再発面

## 出力形式 (この順で)
1. `## 所見` — 各所見を `### {severity: Critical|High|Medium|Low / 種別, タイトル}` + 攻撃シナリオ (具体的な入力・状態→誤った受理/拒否) + 根拠 file:line + 提案 (最小修正)
2. `## 付帯確認への直接回答`
3. `## 確認済み事項` — 攻撃したが破れなかった点

severity は「実装後に発覚したときの手戻りコスト」基準。所見ゼロの粉飾はするな — 破れなければ破れなかったと書け。

### プロンプト C2

あなたは敵対的設計レビュアー (read-only)。私は Pegasus env_contract 登録段 wave のマネージャーで、実装前のプランを攻撃してもらう。目的は「実装後に手戻りになる設計欠陥・検証の空隙・裁定違反」を実装前に潰すこと。

## 対象
- プラン: `plan-env-contract-pegasus.md` (repo 直下、untracked)。**あなたの担当は §2 論点 C (enforcement 4 点) = 実装単位 U2**。
- 裁定・契約の正本: `docs/pegasus-runbook.md` §3 (NQSV バッチジョブ)・§7 (L259-284、enforcement 未実装 4 点の列挙 L276-278)、`docs/decisions.md` D59、プラン §0 の不変条件は変更不可。G12 = campaign を単一 allocation/node/process で完遂、walltime 不足・途中 kill は WAL を証拠保存して全数値不採用。
- 実装対象コード: `orchestrator/campaign/layout.py` (repo_output_root L27-33 / campaign_layout L76-84 / env_scope_dir L87-90 — output_root 無検査)、`orchestrator/campaign/buildcache.py` (cache_key L105-119 — env 次元なし、cache_root = ccbench submodule 内 build-variants)、`orchestrator/calibrator/runner.py` (classify_competing_probe — rc==1 かつ両 stream 空のみ無競合)、`orchestrator/campaign/s8b_floor_campaign.py` (L548-575 pre/post probe パターン)、`orchestrator/campaign/p3_s4_loop.py` (MAX_WALLTIME_S L77 / check_stop L288- — 内部予算の型)、`orchestrator/campaign/env_contract.py` (IsolationPolicy L47-60)、`orchestrator/campaign/execution_guard.py`。

## 攻撃観点 (最低限。これ以外も自由に)
1. **walltime 事前予約検査**: NQSV は残時間の標準 env var を持たない。プラン候補 = ジョブスクリプトが開始時に deadline (epoch) を導出して env var で渡し、実行側が「見積り所要 < 残時間」を fail-closed 検査。攻撃せよ: (a) 見積り所要の真実源は何か (恒真化 — 見積り 0 なら常に pass)。(b) env var 欠落・偽装・古い値の再利用 (resume 禁止との整合)。(c) qstat -f 自己参照の代替案の実現性と、ジョブ内から qstat が叩けるかの前提。(d) linux-baremetal (スケジューラなし) では検査をどう no-op にするか — env 分岐を registry 外に書けない AST 制約下で
2. **永続領域 allowlist**: layout.py への resolved path 検査挿入。攻撃: (a) symlink・`..`・bind mount で /scr を許可領域に見せる経路。(b) repo 自体が /scr 配下に clone されているケース。(c) allowlist の真実源をどこに置くか (機械固有事実を横断 code に焼かない原則との整合 — /scr は Pegasus 固有名)。(d) WAL open 後に output_root が差し替わる TOCTOU。(e) 既存の output_root 上書き利用箇所 (テスト・between_run_floor 等) を壊さないか — 利用箇所を列挙せよ
3. **PID 可視性 canary probe**: pgrep 分類器は「rc==1 + 両 stream 空 = 無競合」だが、pgrep が全プロセスを見えていない環境 (hidepid, cgroup namespace, コンテナ) では恒真の無競合になる。canary (自 PID または自分が起動した既知プロセスを pgrep が見つけられること) の設計を攻撃: 偽陰性・レース (canary 終了タイミング)・分類器契約 (rc==1 + 空が「正常」) との衝突をどう解くか
4. **buildcache contract_sha256 分離**: cache_key pre-image へ contract_sha256 を足す案を攻撃: (a) 同一ハード・同一 toolchain で env_tag だけ違うとき rebuild は本当に必要か (過剰分離のコスト) vs 分離しないときの汚染経路。(b) trace ビット (規律 1) との直交性が保たれるか。(c) cache_root が ccbench submodule 内 (共有) であることと Pegasus の複数ノード同時ジョブの衝突・破損。(d) 旧 cache エントリとの衝突・誤ヒットの残余risk
5. G12 (single_process / allow_resume=False) の実効性: enforcement 4 点が揃ったとして、G12 を破る残り経路 (同一ノード内の二重起動、qsub 二重投入、WAL append の並行) はどこか
6. 恒真ゲート面 (F9/F14): 各 enforcement が「宣言だけで発火しない」構造にならないか。負例テスト (allowlist 違反 path・walltime 不足・canary 失敗・cache 汚染) が実際に検査本体を通るか

## 付帯確認
- U2 の想定ファイル素集合 (layout.py / buildcache.py / 新 walltime leaf / calibrator 配線) が U1 (env_attestation 新 leaf + execution_guard + driver pin 置換) と衝突しないか
- failures.md 型タグ F3 (単独性)・F9/F14 (恒真)・F15 (代表性)・F19 (実体化遅延) の再発面
- プラン §0 不変条件からの逸脱はないか

## 出力形式 (この順で)
1. `## 所見` — 各所見を `### {severity: Critical|High|Medium|Low / 種別, タイトル}` + 攻撃シナリオ + 根拠 file:line + 提案 (最小修正)
2. `## 付帯確認への直接回答`
3. `## 確認済み事項` — 攻撃したが破れなかった点

severity は「実装後に発覚したときの手戻りコスト」基準。所見ゼロの粉飾はするな。

### プロンプト C3

あなたは敵対的設計レビュアー (read-only)。私は Pegasus env_contract 登録段 wave のマネージャーで、実装前のプランを攻撃してもらう。目的は「実装後に手戻りになる設計欠陥・検証の空隙・裁定違反」を実装前に潰すこと。

## 対象
- プラン: `plan-env-contract-pegasus.md` (repo 直下、untracked)。**あなたの担当は §2 論点 D (calibration ジョブ設計) = 実装単位 U3、および実測後の U4 (registry entry + テスト同期) への結線**。
- 裁定・契約の正本: `docs/pegasus-runbook.md` 全節 (特に §1 ノード仕様・§3 バッチ・§4 モジュールとビルド・§5 並列実行・§7 登録要件・§8 チェックリスト)、`docs/decisions.md` D59、プラン §0 (env_tag=pegasus はユーザー確定、登録は計算ノード実測前提、ログインノード値不可)。
- 実装対象コード: `orchestrator/calibrator/cli.py` (CLI 引数・出力パス規約)、`orchestrator/calibrator/sweep.py` (calibrate() L130-203 の手順、_host_info L27-32)、`orchestrator/calibrator/model.py` (CalibrationResult L191-207 / NoiseFloor L145-159 / BetweenRunNoiseFloor L162-188)、`orchestrator/calibrator/report.py` (result_to_dict L72-84)、`orchestrator/calibrator/tsc.py` (measure_clocks_per_us L65-、TMPDIR に C ヘルパをビルド)、`orchestrator/campaign/between_run_floor.py`、`orchestrator/campaign/env_contract.py` (_build_registry L147-164 / CalibrationRef L63-79)、`orchestrator/tests/test_env_contract.py` (ENV_LITERAL_VALUES L45 / 同期 assert L238-250 / golden L168-180 / calibration_ref 実在検証 L268-273)、既存成果物 `output/env/linux-baremetal/calibration/calibration_t48_skew0_rr50_rmw0.json`。
- 参考: CCBench は submodule。orchestrator は pinned-clean を確認する既存の隔離・評価経路を使う (CLAUDE.md 作業の進め方)。

## 攻撃観点 (最低限。これ以外も自由に)
1. **ジョブ手順の妥当性**: 提案手順 = qsub (gen_S, 1 node, -A SFC) → module load (runbook §4) → CCBench pinned-clean build (計算ノード上) → attestation probe 記録 → pre pgrep probe → calibrate (t48) → post probe → 成果物 sha256 manifest。攻撃: (a) 順序の欠陥 (build と calibrate の間の状態変化、TMPDIR = /scr 系の揮発と tsc.py の C ヘルパビルドの整合)。(b) walltime 見積りと飽和 sweep の非有界性 (sweep が収束しないとき job kill → 部分成果物が残る面)。(c) module 環境の pin をスクリプトへどう焼くか (module load の出力・バージョンを成果物へ記録する具体策)。(d) 標準出力/エラーが投入 dir へ戻る NQSV 仕様と成果物パスの整合
2. **単独性 (Exclusive OFF)**: gen_S は専有保証なし。pre/post pgrep probe は「ycsb_.*\.exe」パターンだけを見る — 他ユーザーの無関係な重負荷プロセス (この bench 名以外) による汚染は検出できない。calibration の品質ゲート (noise_floor.cv 閾値・load average 確認・再計測規約) をどう設計するか。runbook §7「単独性確認は計測ノード上で」の実装を具体化して攻撃せよ
3. **規律 4 (スケール)**: 飽和 sweep の探索範囲・打ち切り条件は Pegasus (48 core, L3 サイズ既知) で妥当か。linux-baremetal の workload 署名 (skew0p9_rr50_rmw0 等) と揃える案の是非 — 揃える根拠と、揃えることが D59「混ぜない」原則を侵さないことの確認
4. **成果物とレジストリ結線 (U4)**: calibration JSON → CalibrationRef {path, sha256} → _build_registry() 追記 → ENV_LITERAL_VALUES 追記 → golden 追加、の連鎖で: (a) sha256 束縛の運用 (JSON を後で手直しすると登録が壊れる — 意図どおりだが、手直しの正規手順は何か)。(b) calibration_ref 実在検証テスト (L268-273) の一般化の設計。(c) clocks_per_us の丸め (tsc.py 実測は非整数 → 契約は int) の規約。(d) numactl 値を Pegasus でどう決めるか (interleave の要否は NUMA topo 実測に依存 — 登録前に何を根拠に固定するか)
5. **between-run floor の要否**: 親の仮説 =「登録は within-run noise floor で足り、between-run は floor 実測段の入口で取る」。この分割が裁定・正本 (runbook §7 の「calibration と noise floor を取り直す」) と整合するか。within/between の取り違えが下流 (floor protocol の統計) を歪める面はないか
6. **恒真・代表性 (F9/F14/F15)**: ログインノードで誤って走らせた calibration を検出・拒否する構造 (attestation probe の記録が計算ノードであることの証明は何か — hostname パターン bnodeXXX への依存の脆さ)。ジョブ完走の検収基準 (何が揃っていれば「実測完了」と言えるか) を列挙せよ

## 付帯確認
- U3 の成果物 (ジョブスクリプト・生成 JSON) と U1 (attestation profile を calibration JSON に同居させる案 A2) の schema 整合 — U3 が U1 の probe 実装に依存するなら実行順序は U1 → U3 で正しいか
- 較正実測をこの wave 内で実走することの前提 (ポイント残 438、gen_S 混雑 20 本) で見落としはないか
- プラン §0 不変条件からの逸脱はないか

## 出力形式 (この順で)
1. `## 所見` — 各所見を `### {severity: Critical|High|Medium|Low / 種別, タイトル}` + 攻撃シナリオ + 根拠 file:line + 提案 (最小修正)
2. `## 付帯確認への直接回答`
3. `## 確認済み事項` — 攻撃したが破れなかった点

severity は「実装後に発覚したときの手戻りコスト」基準。所見ゼロの粉飾はするな。

## 親裁定表 (2026-07-18、C1/C2/C3 全所見)

検算: C1 (receipt shape 検査のみ / contract sha 焼き込み 1 箇所)、C2 (single_process consumer ゼロ /
buildcache 10-hex + 後方互換 fallback)、C3 (TSC fallback 2100 / CLI 検証なし / --clocks-per-us
override / between_run p2_2 結合) を親が実コードで確認 — 全て事実。**全所見 real、refuted 0。**
採用は以下 (修正採用を含む)。実装先は plan v2 (worktree 直下) の W 単位。

| # | 所見 | 裁定 | 実装先 |
|---|------|------|--------|
| C1-1 | 素の A2 は fail-open | 採用 → **hybrid**: 契約に `attestation_mode` ("none"/"required") field 追加 (hash churn 今受容)、calibration/v2 に profile 同居。既存 linux v1 JSON は現行 exact sha のみ grandfather | W0+L1 |
| C1-2 | calibration_ref 本番未検証 | 採用: read-once → sha 検証 → 同一 bytes parse → cross-field 検査。全 env で preflight 必須化。登録成果物は create-only、通常再校正 stem と分離 | L1+W2 |
| C1-3 | 登録汚染 (cygnus 偽登録) | 採用: acquisition_receipt (qsub/allocation/toolchain/isolation) を calibration v2 内へ。U4 は runbook §1 独立既知値 (Xeon 8468 / 48core) 照合込みの機械検収。override/fallback 使用 artifact は拒否 | W0+L4+W5 |
| C1-4 | 二段 API で照合省略可 | 採用: `attest_and_build_receipt()` 統合、receipt v2 (per-field expected/observed)、v1 は mode=none のみ受理、consumer 再検算 | L1+W2 |
| C1-5 | TSC↔実効クロック混同 | 採用: tsc_mhz (raw+median+nearest-even 凍結、required で fallback/override 禁止) と effective_clock (方法+governor 記録) を別 field 別 comparator。許容幅は smoke job ≥3 配分の分布から親が凍結 | L1+W4 |
| C1-6 | probe 粒度・正規化不足 | 採用: strict probe leaf 共有 (cpuinfo 安定識別子+raw、48/48 SMT off exact、cache canonical topology、NUMA sort 済構造、部分読取=全体拒否)。ハード更改は fail-closed → 新 env-tag 運用 | L1 |
| C1-7 | A1/A3 churn は今なら小 | 採用 (hybrid の根拠)。golden 更新は protocol builder + env_contract 群のみ | W0 |
| C1-8 | U1/U2 非素集合 | 採用: W0 interface 凍結 → leaf 並列 → integration 逐次 (W2a floor 系 / W2b oracle 系でファイル素) | 全体 |
| C1-9 | F15/F19 (実 JSON 不通過) | 採用: fixture は result_to_dict 生成、実 bnode artifact を U4 前に固定、mutation positive control 3 種 (comparator 恒真/呼出削除/v1 on required) | W1-W5 |
| C2-1 | U2 恒真 + 登録前 contract 循環 | 採用: 実走結線を W2 で必須化。登録前 calibration は contract 非依存 — acquisition_receipt が trust root。暫定 entry は置かない | W2+L4 |
| C2-2 | walltime 見積り恒真 | 採用: leaf が validated schedule から導出、blocking 全操作 hard timeout、binding {job_id, requested_s, started_epoch, deadline_epoch, host, boot_id, script_sha256, nonce} + monotonic 併用、余裕喪失=campaign terminal 全数値不採用。qstat -f は smoke job 実測まで昇格させない。要求判定は isolation_policy.single_process から型導出 | L2+W2 |
| C2-3 | single_process consumer 不在 | 採用: O_EXCL one-shot claim (campaign identity キー、crash 後も残留、再実行=新 identity) + oracle campaign-terminal + report 全被覆時のみ公開 (それ以外 campaign-incomplete / bench_values=[]) | L2+W2b |
| C2-4 | allowlist TOCTOU | 修正採用: DurableRootPolicy leaf + write-capability 注入 (mutating entry のみ)、resolve + mount-id 横断拒否 + open 直前 identity 再照合。機械固有 root は shared code に書かず注入。calibrator --out-root も policy 経由。FD 常時保持までは今 wave 見送り (open 直前再照合で TOCTOU 窓を最小化、残余は限界として記録) | L2+W2 |
| C2-5 | canary 偽陰性 | 採用: nonce 付き ycsb 名 child + composite wrapper (分類器契約不変) + starttime/nonce + finally kill + hidepid/PID ns attestation を required env で必須 | L1+L4 |
| C2-6 | 一回 pre/post では不足 | 採用: registration mode は各 measurement point を probe で挟み、violation=attempt 全体不採用。settled=False fatal。quarantine (.pending/attempts) → 検収後 atomic publish | L4 |
| C2-7 | buildcache 分離不十分 | 採用: contracts/<full-sha>/<full-digest>/ namespace、完全 pre-image manifest + completion marker hit 条件、toolchain manifest hash、staging + atomic publish、O_EXCL claim、stale=fail-closed、v2 経路 contract 必須・legacy 明示隔離、trace 4 象限固定、二 process 競合テスト | L3 |
| C2-8 | buildcache 並行破損 | 採用 (同上 claim/staging/competition test) | L3 |
| C2-9 | テスト規律 | 採用: 負例は production entry 経由 + 副作用ゼロ検証、C1/C2/C3 の負例リスト全部、AST 対象へ新旧モジュール追加 (`/scr` は許可領域なしの禁止 literal に) | 全 W |
| C3-1 | 完走≠採用可能 | 採用: quality.status accepted/rejected + 理由列挙 (TSC 実測由来/静定成功/全 rep 完備/必須 counter/飽和 or lower_bound/CV≤5%/全 window 単独性/post 整合)。rejected は非 0 終了 + run-scoped 成果物のみ | L4 |
| C3-2 | 単独性の時間窓 | 採用 (C2-6 と同一実装) + 補助 gate (job 外 CPU-time delta / load / PSI 記録)。NQSV 同一 host 照会は smoke で可否確定 | L4+W3 |
| C3-3 | 静定不足 | 採用: 段階手順 (静的 attestation → build → 子孫終了+hash 確定 → 凍結閾値 cooldown (失敗=fatal) → 動的 pre-receipt → 計測 → post-receipt)。TMPDIR=/scr は helper/使い捨て build のみ、成果物は永続領域 | L4+W3 |
| C3-4 | bnode 文字列は証明でない | 採用: hostname は provenance 扱い (equality 対象外)、qsub ID↔$PBS_JOBID↔qstat -f assigned host↔実 hostname の相互照合、queue/project/node/cpuset 48/HT off を receipt へ | W0+W3 |
| C3-5 | 外部 manifest は連鎖外 | 採用: provenance を calibration JSON 内へ (module -t list、compiler 実体/version、CCBench full pin+clean、build argv、binary sha、job script sha、PBS receipt)。qsub 前に source commit 固定、job 冒頭で再照合 | W0+L4+W3 |
| C3-6 | 固定名 open("w") | 採用: attempts/<job-id>/ staging + create-only + atomic publish、.o/.e は login 側 collector が最終 receipt に付加 (job 内 manifest と分離)、stderr 空を成功条件にしない | L4+W3 |
| C3-7 | 有界性 | 採用: CLI 正数検証、build/probe/hash/publish 個別 timeout、予約式凍結 (成果物へ記録)、walltime 末尾 rejection-receipt reserve。gen_S 最大 walltime は投入前確認 | L4+W3 |
| C3-8 | U4 意味検証不足 | 採用: 全 entry loop 化 + path canonical 検査 + env_tag/clocks cross-field + Pegasus 用 schema/quality/attestation 検査 + legacy exact allowlist + unknown parameter から "pegasus" 削除 + 負例 5 種 | W5 |
| C3-9 | bootstrap 循環 | 採用: 較正 build は job-scoped 使い捨て (cache hit なし、/scr 可)、binary sha + build inputs は記録。contract namespace は登録後の floor/oracle build のみ | L4+W3 |
| C3-10 | 測定座標未凍結 | 採用: TSC 丸め = raw 5 回 median の nearest-even int (現行互換) を凍結、raw/median/分散を JSON 保存。numactl 規則凍結 = 「実測 NUMA 1 node なら ()、複数 node なら interleave=all (linux 先例)」— smoke job の実測で確定 | W0+W4 |
| C3-11 | between-run 分離 | 採用 (親仮説の条件付き承認): U4 は bootstrap 登録と明記、compare/oracle verdict は between-run floor 取得まで開かない (official 拒否は既に不変)。noise_floor.kind="within-run" 明記 | W0+W5+W6 |
| C3-12 | scale sensitivity | 採用: 本 wave は schema 上 `not-measured` を正直に記録 (無根拠 4t/1m を出さない)。主 calibration workload = skew0p9_rr50_rmw0 (linux registry 先例と同型) | W0+L4 |

**却下・見送り (理由つき):** C2-4 の FD 常時保持 + openat 全面化は「open 直前 identity 再照合」まで
に縮小 (今 wave の複雑性予算。残余 TOCTOU 窓は既知限界として runbook に記録)。C1-5 の
APERF/MPERF 実装は sysfs/cpuinfo サンプリング + governor 記録で代替 (perf/msr 権限が計算ノードで
未確認のため。smoke job で見え方を確認してから将来格上げ)。他は全採用。

## 実装結果 (2026-07-19、wave 完了時追記)

### 実装単位と経過
W0 (interface 凍結: attestation_mode field + calibration/v2 schema + receipt v2 検証 + leaf データ契約)
→ W0-fix (positive control 11) → W1 並列 4 単位 (L1 attestation 実装 / L2 reservation・durable_root・
campaign_claim / L3 buildcache v2 / L4 calibrator certification mode) + W3 (tools/pegasus ジョブ資材)
→ polish (レビュー 22 項) → W2a (floor 結線) ∥ W2b (oracle 結線 + G12 all-or-nothing) → W4-fix
(smoke 実測で破れた前提 2 点) → W2-fix (レビュー 18 項 + build_v2 seam)。
実行 = codex gpt-5.6-sol high ×12、相談 = 同 max ×3、レビュー = claude opus ×16 (2 レンズ/単位 + 統合)。

### レビューが捕らえた主要 real 欠陥 (全て採用・解消)
- walltime 完全一致の統合不整合 (投入すれば必ず reject) → 包含意味論へ (内部予算+reserve ≤ 凍結最小
  6430s ≤ qsub 7200s)
- visibility gate 未接続 (hidepid ノードで accepted 成立) / acquisition host 照合の fail-open 実証
- shell ERR trap × set +e で拒否 attempt の forensic 消失 (規律 3) → || rc=$? idiom
- build_v2 固定 root × prepare_cell 隔離 worktree の seam (変異セル build 不能) → ccbench_dir
  passthrough (4 guard は渡された tree に対し維持、cache namespace 不変)
- report status gate 除去で bench 数値漏出の実証 (R5) / 予約算術の定数化が緑で通る (B 群) → 全 pin
- 変異ゲート累計: W0-fix 11/11、polish 30/30、W4-fix 6/6 (8/9 追検 → D1 で閉鎖)、W2a 8+6/14、
  W2b 14/19 (生存 5 → W2-fix で閉鎖)、W2-fix 29/29 KILL

### Pegasus smoke 実測 (2 ラウンド ×3 配分、bnode003/004/030)
- 破れた前提: /proc/1/ns/pid 非 root 読取不能 (→ /proc/2/comm==kthreadd 指標へ) / $PBS_JOBID =
  `0:NNN.nqsv` 形式 (→ 先頭 `0:` のみ除去の正規化。qstat -f も正規化 ID で成功)
- 凍結値: effective clock 中央値 2101.0 MHz (3 ノード一致、governor=performance) → tolerance_pct
  = 2.0 (式: ノード間中央値最大偏差 ×2、下限 2%。偏差 0 → 下限発動)。TSC 2100 clocks/us。
  NUMA 1 node → numactl = () で凍結。toolchain = システム gcc/g++ 11.4.0 + cmake 3.25.0
  (module に gcc/cmake 不在、既定 intelpython 経由)。gen_S Elapse 上限 86400s
- 既知限界 (記録): /proc/2/comm はプロセス側で詐称可能 (正直なコンテナには fail-closed) /
  cross-clone claim 排他は out_root 共有が前提

### 最終ゲート (W2-fix 後)
全走 1870 passed / 26 skipped / 0 failed (ベースライン 1549 から +321)。check_docs /
check_codex_agents 緑。統合レビュー (opus) の判定は worklog 記載。

## 付録 A: プラン v2 逐語 (凍結時点)

# プラン: Pegasus env_contract 登録段 — v2 (凍結。相談 C1-C3 裁定反映)

正本連鎖: 裁定表 = `output/insights/2026-07-18_env-contract-pegasus-consultations.md` 親裁定表
(全所見 real、縮小 2 点)。§0 は v1 から不変。実装は本プランの W 単位に従う。

## §0 発効済み裁定・不変条件 (変更不可)

- env_tag 値 = `pegasus` (ユーザー確定)。登録は計算ノード較正実測が前提 — 実測なしで entry を置かない
- calibration / clocks_per_us / noise floor は計算ノード (bnodeXXX) 上のジョブで取得
- 実測照合 attestation は Pegasus では必須、不一致 = fail-closed
- isolation_policy = single_process=True / allow_resume=False (G12)
- official mode 拒否は不変。正式計測正本 env-tag は linux-baremetal 据え置き (D59)。throughput 混合禁止
- 絶対規律 1/2/3/4/6

## §1 設計裁定 (実装仕様の骨格)

1. **hybrid 方式**: `ExecutionEnvironmentContract` に `attestation_mode: str` ("none"|"required") を追加
   (hash churn 今受容 — 影響 golden は protocol builder 1 + env_contract 群)。linux-baremetal =
   "none"。attestation の照合値 (hardware profile) と登録 provenance は **calibration/v2 JSON に同居**
2. **calibration/v2 schema** (新 `orchestrator/calibrator/schema_v2.py`、writer=calibrator /
   reader=campaign 両用 leaf): schema_version="calibration/v2"、既存 v1 field 互換 + 追加:
   `attestation_profile` (cpu identity 正規化+raw、physical/logical core・SMT、cache canonical
   topology、NUMA 構造、tsc {raw_samples, median, int(nearest-even), source}、effective_clock
   {samples, method, governor, tolerance_pct}、visibility {hidepid, pid_ns})、`acquisition_receipt`
   (qsub receipt / allocation receipt (qsub ID↔$PBS_JOBID↔qstat assigned host↔hostname 相互照合値) /
   toolchain (module -t list, compiler 実体+version, cmake) / CCBench full pin+clean+build argv+binary
   sha / job script sha / walltime 予約式と値 / 独立既知値照合 (Xeon 8468, 48/48, HT off — runbook §1
   由来)) 、`quality` {status: "accepted"|"rejected", reasons[]}、`noise_floor.kind="within-run"`、
   `scale_sensitivity="not-measured"` 可。exact schema・未知 field/duplicate key 拒否。
   hostname は provenance であり equality 対象にしない
3. **strict probe leaf** (新 `orchestrator/campaign/env_attestation.py`): probe() → HardwareProfile
   (部分読取 = 例外)。normalize + compare(contract+calibration_v2, observed) → per-field verdicts。
   `load_verified_calibration(contract, repo_root)`: read-once → sha256 検証 → 同一 bytes parse →
   cross-field (env_tag / clocks_per_us / schema version ↔ attestation_mode 整合)。v1 bytes は
   mode="none" の exact 現行 sha だけ grandfather
4. **receipt v2 + 統合 API** (`execution_guard.py`): `attest_and_build_receipt()` — probe + 全項目
   照合成功時のみ receipt 生成 (per-field expected/observed/verdict、profile sha、method/version)。
   v1 receipt は mode="none" env のみ受理 (schema dispatch)。単独 build_receipt から v2 は生成不能に。
   consumer (floor validator / ratified freeze / oracle report) は再検算
5. **reservation leaf** (新 `orchestrator/campaign/reservation.py`): ReservationBinding {job_id,
   requested_s, scheduler_started_epoch, deadline_epoch, host, boot_id, script_sha256, nonce} +
   monotonic 併用。required 判定は isolation_policy.single_process から型導出。見積りは driver が
   validated schedule から導出して渡す (leaf は式を検証・記録)。余裕喪失 = campaign terminal
6. **durable root policy** (新 `orchestrator/campaign/durable_root.py`): approved roots 注入 (機械
   固有 literal を shared code に書かない)、resolve + mount-id 横断拒否、write-capability 取得時
   検査 + open 直前 identity 再照合。FD 常時保持は見送り (残余 TOCTOU 窓は既知限界として記録)
7. **G12 claim** (新 `orchestrator/campaign/campaign_claim.py`): O_EXCL one-shot claim (campaign
   identity キー、job/host/boot/pid/starttime 記録)。allow_resume=False では crash 後も残留、
   再実行 = 新 identity。oracle: campaign-terminal WAL record + report は terminal completed が全
   schedule を被覆する場合のみ数値公開、それ以外 campaign-incomplete / bench_values=[]
8. **buildcache v2**: `contracts/<contract_sha256(64hex)>/<full_build_digest>/` namespace + 完全
   pre-image manifest + completion marker を hit 条件に + toolchain manifest (compiler realpath/
   version/cmake) + staging build → atomic publish + mkdir O_EXCL claim + stale claim fail-closed。
   v2 経路 (floor/oracle) は contract 必須引数、legacy caller は legacy namespace に明示隔離。
   trace bit 独立維持 (contract×trace 4 象限別 key 固定)。二 process 同時 build 競合テスト必須
9. **calibrator certification mode** (`--certify`): CLI 正数検証、TSC fallback/override 禁止、
   settled=False fatal、cooldown (凍結閾値、失敗=fatal)、各 measurement point を composite probe
   (nonce canary + classifier 契約不変) で挟む、violation = attempt 全体不採用、quality.status 判定
   (C3-1 の 8 条件)、attempts/<job-id>/ staging + create-only + atomic publish、rejected = 非 0 終了。
   bootstrap build は job-scoped 使い捨て (cache hit なし)。補助 gate (load/PSI/CPU-time delta) 記録
10. **AST 中立性拡張**: V2_ENV_NEUTRAL_MODULES へ env_attestation / execution_guard / reservation /
    durable_root / campaign_claim / buildcache / layout / oracle driver / calibrator cli・sweep を
    追加。`/scr` は許可領域なしの禁止 literal。`pegasus` literal は W5 で registry 追加と同時に
    ENV_LITERAL_VALUES へ
11. **テスト規律**: 負例は production entry 経由 + 副作用ゼロ (run dir/WAL/budget/build 不生成) を
    検査。fixture は result_to_dict 生成 (hand-made dict 禁止)。実 bnode artifact を W5 前に固定。
    mutation positive control: comparator 恒真化 / attestation 呼出削除 / v1 receipt on required /
    walltime binding 欠落 / allowlist bypass / claim bypass / cache cross-contract hit / calibrator
    fallback 受理 — 各々が赤になること
12. **測定座標の凍結**: TSC 丸め = raw 5 回の median を nearest-even int (現行互換)。numactl 規則 =
    実測 NUMA 1 node なら ()、複数 node なら ("numactl","--interleave=all") (linux 先例)。主
    calibration workload = skew0p9_rr50_rmw0、t48。scale_sensitivity は not-measured と正直に記録。
    effective_clock 許容幅 = smoke job ≥3 配分の分布から親が凍結し certification job へ注入

## §2 実装単位とファイル所有 (素集合)

- **W0 (interface 凍結、逐次)**: env_contract.py (field 追加 + golden 更新)、schema_v2.py (新)、
  execution_guard.py (schema 定数 + API 署名)、env_attestation.py / reservation.py /
  durable_root.py / campaign_claim.py (新規、dataclass + validator + API 署名。実装は W1)、
  test_env_contract / test_s8b_protocol_builder golden 更新、schema 単体テスト
- **W1 並列 (W0 後)**:
  - **L1**: env_attestation.py 実装 + execution_guard.py (attest_and_build_receipt / dispatch) +
    load_verified_calibration + test_env_attestation (新) + test_execution_guard
  - **L2**: reservation.py / durable_root.py / campaign_claim.py 実装 + 各テスト (新規ファイルのみ)
  - **L3**: buildcache.py v2 + テスト (競合テスト含む)
  - **L4**: calibrator/* (cli, sweep, runner, model, report) certification mode + テスト
    (probe は W0 凍結 API に対する seam 注入でテスト、実結線は W2)
- **W2 並列 (W1 後、ファイル素)**:
  - **W2a**: s8b_floor_campaign.py + pipeline.py + layout.py 結線 (attestation preflight / walltime /
    durable capability / claim / buildcache v2) + 負例 (production entry、副作用ゼロ)
  - **W2b**: s8b_oracle_driver.py + s8b_oracle_report.py + s8b_ratified_freeze.py (campaign-terminal /
    all-or-nothing / receipt v2 consumer) + 負例
- **W3 (W0 後、W1/W2 と並列可)**: tools/pegasus/ (新設 — 機械固有 literal 許可領域): smoke_probe
  ジョブ (probe + qstat -f 可否 + module 見え方 + hidepid + NUMA/クロック分布収集)、certification
  ジョブ (C3-3 段階手順)、login 側 collector (.o/.e + 会計 summary → final receipt)。runbook §7 追記
- **W4 (親)**: smoke ×3 投入 → 検収 → tolerance/numactl 規則確定 → certification ジョブ投入 →
  attempts 検収 (C3「実測完了」9 条件)
- **W5**: registry entry + ENV_LITERAL_VALUES + Pegasus golden + U4 意味検証 (C3-8 全項) + unknown
  parameter から "pegasus" 削除
- **W6**: runbook 現況 / phase3 チェックポイント / worklog / handoff 吸収 / insights 実装結果追記

## §3 検証プロトコル

- 各 codex 単位 (gpt-5.6-sol high、workspace-write) 完了ごとに claude opus レビュー 2 レンズ並列:
  レンズ A = 恒真・実効性 (F9/F14/F15/F19、負例の実発火、副作用ゼロ検査)、レンズ B = 裁定準拠・
  回帰 (裁定表/プラン v2 との一致、スコープ逸脱、既存テスト破壊)。所見は親裁定 → codex 再投げ
- 親検算: 全走 (`python3 tools/run_tests.py`) + §1-11 の mutation positive control 群を変異ゲートで
  機械確認 (複製 + PYTHONPATH shadow + PYTHONDONTWRITEBYTECODE、前 wave 方式)
- W4 検収 = C3「実測完了」9 条件の機械チェックリスト。1 項でも欠ければ rejected attempt として
  取り直し (rep 選別・途中再開禁止)

## §4 スコープ外

protocol JSON 実凍結・予測封印 (追認リスト裁定待ち) / floor 実測本走 / between-run floor (次段。
U4 完了は「bootstrap 登録」であり正式比較可能を意味しない) / official 解禁 / APERF/MPERF 格上げ /
FD 常時保持 openat 全面化 (既知限界として記録)

## 付録 B: レビュー所見台帳 逐語 (親裁定込み)

# レビュー所見台帳 (親裁定用)

## L2 レンズ B (完了): Critical/High 0
- [Low/採用→polish] reservation._env_text が未 strip 返し + boot_id 片側 strip 比較 → 両側 strip へ (誤拒否方向なので緊急性低)
- [Low/採用→polish] ReservationBinding per-field 負例不足 (deadline 整合違反 / bad script_sha256 / 非有限 epoch)
- [Info] W0 dataclass 無改変は field 集合照合で確認 (untracked のため git 照合不能)

## L1 実装報告の未裁定事項 (親裁定済み)
- [採用] PID ns indeterminate = AttestationError (fail-closed、schema bool のまま)
- [採用] observed tolerance_pct は sentinel、比較は expected 凍結値のみ
- [採用→polish] receipt v2 に captured_utc field を追加 (schema_v2/execution_guard/テスト連動、W2 前に)
- [polish] test_calibrator.py の xdist フレーク: worker PID=8 と path 中 "s8b" の部分文字列誤衝突 (直列は緑)

## L2 レンズ A (完了): 義務 positive control 全発火。判定 = polish 条件付き合格
- [Low-Med/採用→polish 必須] durable_root open_for_write の O_NOFOLLOW positive control 欠落 (変異で外部ファイル上書き実証) → 「approved root 内 symlink leaf 拒否 + 外部無傷」負例を test_durable_root.py へ
- [Low/採用→polish] campaign_claim docstring へ FS 前提明記 (atomic O_EXCL: Lustre/NFSv4 可・NFSv3 不可)
- [任意/採用→polish] fsync 呼出回数 assert (monkeypatch) で durability を pin

## L3 レンズ B (完了): 準拠 11/11。判定 = polish 条件付き合格
- [High/採用→polish 必須] V2_ENV_NEUTRAL_MODULES へ buildcache.py 未登録 (裁定 10 未達、W0 の取り落とし + W0 レビュー見逃し)。裁定 10 の残り = layout.py / s8b_oracle_driver.py / calibrator cli.py・sweep.py も登録漏れ → polish で全部 region=None 追加 (追加後緑を L3 レビュアーが buildcache 分は確認済)
- [Low/採用→polish] BuildResult へ v2 provenance field を additive 追加 (contract_sha256 or フラグ) — W2 の「build() 呼び続け恒真」検査を /contracts/ 部分文字列依存から解放
- [Info→W2/W4 申し送り] build/--version subprocess の timeout なし (driver 側で付与) / 共有 cache root の NFS rename 意味論は W4 で runbook 確認

## W3 実装報告 (完了、レビュー前): 全緑 + 実機前提の smoke 確定リスト 11 項を申告
- [High/採用→polish 必須・実機 blocking] walltime 意味論の統合不整合: schema cross-check を
  `walltime.required_s <= qsub.elapstim_req_s` へ変更 (完全一致は誤り)。L4 は「較正所要 <=
  required_s - reserve_s」を検査する形へ整合。required_s = ジョブ級凍結最小 (build cap +
  較正所要 + 退避 reserve、式は receipt に記録) — W3 の 6430s/7200s/600s が正
- [記録] smoke で確定する 11 項 (qstat -f 可否 / assigned host field 名 / request_id↔PBS_JOBID /
  co-allocation 照会 / gen_S 最大 walltime / module 実名 / hidepid・PID ns / cpuset・HT・NUMA /
  /scr・TMPDIR / tolerance 3 配分 / .o.e 書式) — W4 検収チェックリストへ

## L3 レンズ A (完了): 義務 positive control + 規律1 検査は全発火。判定 = polish 条件付き合格
- [Medium/採用→polish 必須] O_EXCL 排他 (M6) の独立負例: barrier を claim 直前へ移した変種で
  「lexists 通過後の 2 process claim 競合」を実プロセス検証 (現行 race test は lexists しか証明せず)
- [Low-Med/採用→polish] manifest 改竄一括負例 1 本: hit 済み entry の completion.json を 1 field
  改竄 (completion_marker="partial" / preimage から ccbench_commit 欠落) → BuildCacheError + binary
  無傷 (M2/M4/M14 群を一括で pin)
- [Low/採用→polish] buildcache docstring の「ccache が効く」記述を修正 (wrapper 経由は実コンパイラ
  差替えを見逃す既知限界を明記)
- [見送り/理由記録] M8 (is_full_sha256 guard)・M20-M23 (symlink/dup-key/bdir/再検査) の個別負例 —
  trusted-storage (durable_root 0700) 前提の防御多重で digest→path 導出が live 誤 hit を構造遮断
  済みのため。consistent forgery 非検出も同前提の既知限界として docstring 済み扱い

## L1 レンズ B (完了): 準拠 8/8。W0 申し送り (raw bytes) 解消確認。判定 = polish 条件付き合格
- [Medium/採用→**W2 必須ステップへ編入**] receipt_matches_contract の attestation_mode を必須引数化
  (既定 "none" の暗黙 fallback を構造排除)。v1 呼び出し元 (floor validator / ratified / oracle
  report) の明示化は W2a/W2b の結線と同時に。required 契約 + v1 receipt + mode 未指定の負例も W2 責務
- [Low/採用→polish] env_attestation.recorded_comparisons_match_profile は dead code → 削除 (verdict
  再計算の 3 重実装を 2 実装へ)
- [Low/採用→polish] mode=none の grandfather 二段目 gate (非 grandfathered sha 差し替え拒否) の負例追加
- [nit/採用→polish] L1 の docstring / エラーメッセージを日本語規約へ統一
- [W2 申し送り記録] validate_receipt_v2 単独で受理判定禁止 / verified の contract 取り違え防止 /
  receipt は時間束縛を持たない (freshness は reservation+claim の分担)

## L4 レンズ B (完了): 判定 = polish 必須複数 (うち High 1)
- [High/採用→polish 必須] certify accept 経路に visibility gate 追加: hidepid != "0" または
  pid_ns_shared_with_host != True → CertificationError (dynamic pre-receipt 直後、C2-5 逐条)
- [Medium/採用→polish 必須・実機 blocking] walltime 意味論の統一実装 (W3 所見と同根):
  schema_v2 = required_s <= elapstim_req_s へ / L4 _acquisition_reasons = 「受領 receipt の
  walltime はジョブ級 (W3 が build_cap 込みで計算)」を前提に、(i) 自身の較正所要 (internal formula、
  build_cap なしで正) + reserve_s <= required_s、(ii) required_s <= elapstim_req_s、の包含検査へ
  (exact 一致を廃止)
- [Medium/採用→polish 必須] acquisition cross-check 6 reason + binary-sha256 gate の負例を
  production entry 経由 parametrize で追加 (host 不一致 / pbs_jobid≠request_id / nodes≠1 /
  binary 改変 / elapstim 改変 / passed=False)
- [Medium/採用→polish] cli.py:542 の ["numactl","--interleave=all"] 直書きを --numactl 引数由来の
  構築へ (literal 回避) → その後 V2_ENV_NEUTRAL_MODULES へ calibrator cli.py / sweep.py を登録
- [採用→polish] certify では scale 感度実測を skip (実測して捨てるのは walltime ~12 分の浪費、
  C3-12 の not-measured 記録は維持)
- [記録] window-probes/rejection は forensic 専用・hash 非束縛 (W5 は quality.status を信頼源に、
  恒久策 = 将来 schema rev で digest 束縛) / evidence 4 定数は例外経路が実 gate (L4-A で変異確認)

## L4 レンズ A (完了): 生存変異多数 → polish 必須群に統合
- [High/採用→polish 必須] acquisition gate の production entry 負例 5 本以上 (host 不一致 (fail-open
  実証済) / node≠1 / receipt binary-hash 不一致 / reservation-budget 不一致 / known-values 不一致)
  + 副作用ゼロ検査。L4-B の M2 と同一実装で満たす
- [Medium/採用→polish 必須] 拒否核の isolate 負例: --clocks-per-us テストを他必須引数完備で書き直し
  (現行は恒真) / --out-root 拒否 / CLI binary-sha256 不一致 / certify TSC fallback 強制・None guard
- [Low/採用→polish] publish 衝突/失敗の except 経路で candidate.json を unlink してから rejected
  receipt を書く (accepted/rejected 矛盾残置の解消)
- [Low/採用→polish] 恒真 clause 削除: report.py isolation-window-failed の到達不能枝と死蔵 field
  (pre/post_probe_passed) を整理 (実 gate = 例外経路に一本化)、sweep.py certify settle 死枝削除
- [Low/採用→polish] quality 複合 OR の未テスト枝 (measurements 空 / throughput 数 / counter None /
  l3 None / records<=0 / 非飽和) の parametrize 追加

## L1 レンズ A (完了): RED 20 / GREEN 7。判定 = polish 条件付き合格
- [Medium/採用→polish 必須] consumer expected 再照合 (execution_guard:149) の自己整合改竄負例
  (expected=observed=別マシン値、verdict=pass、profile_sha 真値) — レビュアー提供のテスト案を採用
- [Medium/採用→polish 必須] probe governor 異種混在の負例 (2 CPU 別 governor → AttestationError。
  compare が後追いできない唯一の probe ゲート)
- [Low/採用→polish] grandfather exact-sha の合成 mode=none 契約負例 (L1-B 所見と同一項)
- [記録/対応不要] legacy dup-key hook 到達不能 (防御多重)・NUMA/cache probe ゲート弱化は compare
  が後追い (確認済)

## W3 レンズ B (完了): 準拠 7/7。判定 = polish 条件付き合格
- [Medium/採用→polish 必須] make_acquisition_receipt.py の round-trip fixture テスト (writer build() +
  reader schema_v2 receipt 検証の両通過 + 1 field drop/rename で赤の mutation control)
- [Low/採用→polish] test_pegasus_tools.py の ("pega"+"sus") 分割を素直な literal へ (evasion 臭の排除)
- [Low/採用→polish] certify_calibration.sh の os.sys.argv 2 箇所へ import sys / certify 呼出の
  --numactl を落とす (dead) + README に numactl 自動導出を一言
- [W4 親決定事項として記録]
  - tolerance 導出式の凍結 (案: smoke ≥3 配分の probe effective_clock中央値群 → pooled median から
    の最大相対偏差 ×2 (安全係数)、下限 2%。probe-to-probe 比較で条件整合)
  - smoke で module -t avail から gcc/cmake の実在版名確定 (README 例は仮置き)
  - 単独性クリーン判定の閾値明文化 (load1 等)
  - collect_receipt の引数 namespace 反転に注意 (README 表記へ厳密従属)

## W3 レンズ A (完了): fail-closed は保持、実効性 High 1
- [High/採用→polish 必須] certify_calibration.sh の ERR trap × set +e 問題: rc 捕捉 2 ブロック
  (calibrate / qstat) を `|| rc=$?` idiom へ置換 (ERR trap 文脈から外す)。拒否 attempt の
  job-result.json 生成と stage 正確ラベルを回復 (規律 3)
- [Medium/採用→polish] shell 挙動テスト追加: calibrate/qstat を stub にした subprocess 実行で
  failure.json の stage と job-result.json 生成を assert (bash -n + grep だけでは High を検出できず)
- [Low/採用→polish] PBS directive の位置検査 (shebang 直後〜最初の実行行の範囲のみ収集、範囲外や
  重複は fail)
- [確認済記録] schema 突合一致 / collector 照合は恒真でない / 段階手順・reservation 導出・source
  identity 連鎖・dry-run 副作用ゼロ・signal 経路・run_probe fail-closed・literal 封じ込め、全て健全

## W2a 実装報告 (完了): 変異 8/8 KILL、全走 1840 passed
- [裁定/採用→W2 修正ラウンド] build_v2 に timeout 引数を additive 追加し floor から 900s を渡す
  (現状は予約算定のみ。hung build は scheduler kill 頼み — forensic 弱)
- [記録] pipeline の env_contract + 非既定 ccbench root = fail-closed (安全側、採用) / claims/ は
  durable root 配下に事前作成が必要 (runbook・W6 記録 + certification 前に親が作成)
- [記録] floor reservation 凍結式 = セル数 × (build 900s + (試行+retry) × (extime×reps +
  verify 120s)) + finalize 600s

## W4-fix レビュー (完了): Critical/High 0、変異 8/9 KILL。判定 = 修正ラウンド小項目のみ
- [Low/採用→W2 修正ラウンド] toolchain capture の挙動テスト (gcc --version rc≠0 stub → failure 検出。
  || true 回帰を赤にする)
- [Info/採用→W2 修正ラウンド] normalize_request_id の縁ケース parametrize (0:0:X / 00:X / 空文字) /
  kthreadd comm 詐称可能の既知限界を docstring・runbook に一言
- [確認] 正規化は全 4 照合点に適用済・raw provenance 保持・旧方式残骸ゼロ・mode=none 回帰ゼロ

## W2a レンズ B (完了): 準拠 11/12・回帰なし。判定 = W2 修正ラウンド必須 1 (High)
- [High/採用→W2 修正ラウンド必須] build_v2 に ccbench_dir 引数を追加 (裁定 = 選択肢 a): 既定 =
  共有 submodule、指定時は prepare_cell 由来の隔離 worktree を受理し pinned-clean 検証 +
  _recheck_src_token/_assert_trace_diff を**その tree に対して**発火。pipeline の非既定 root 拒否
  guard も同整合 (allowlist 済み prepare 由来のみ通す)。floor build_cells は prepared.ccbench_dir
  を渡す。timeout 引数 (W2a 報告の裁定) も同時に追加し floor から 900s
- [Medium/採用→W2 修正ラウンド] v2 build の end-to-end canary (実 prepare → build_v2、F19) +
  pipeline 拒否枝の負例 + required-mode 正例完走テスト (journal/claim/receipt の成功形 pin)
- [Low/採用→W2 修正ラウンド] claims/ 事前 provisioning と floor ジョブの IZANAGI_RESERVATION_*
  export 要件を tools/pegasus README / runbook 現況へ明記 (floor 実走は次 wave)

## W2b レンズ A (完了): 義務 5 結線 全赤化。生存 5 → W2 修正ラウンド (テスト追加のみ)
- [Medium/採用] R5 負例: terminal status="aborted" かつ completed_rows==scheduled==全行・全被覆・
  deviation 無しの WAL で全行 incomplete + bench_values=[] を pin (status gate 単独発火形)
- [Medium/採用] D8 負例: 実 reservation_check 付き plan で (a) 残枠不足の ensure_remaining 実発火、
  (b) 途中 attestation drift の receipt_matches_contract 捕捉 (mock 丸ごと差し替えを廃した real 経路)
- [Low/採用] R2: scheduled_rows だけ manifest 行数とズレた terminal の負例 / R8: env_tag 実在 +
  contract_sha256 が registry と食い違う manifest の負例 / D1: driver 二重 terminal ガードの単体負例

## W2b レンズ B (完了): 準拠達成・全走 1840。判定 = W2 修正ラウンドへ
- [High/採用 (W2a-B と同一項の実装仕様)] build_v2 へ ccbench_dir passthrough: `sub = ccbench_dir or
  _ccbench_dir()` (legacy 同型、allowlist/recheck は既に隔離 worktree 対応済)、pipeline v2 枝の
  拒否 guard 撤去 + passthrough、preimage 不変 (cache churn なし)。oracle の実 build integration
  positive control 1 本 (fake 迂回しない)
- [採用] G12 claim root を oracle でも durable 承認領域下 claims/ へ (floor と統一、相談 C2-3 の
  cross-clone 意図へ接近。残余 = out_root 共有前提を docstring/runbook に記録)
- [採用] report campaign-terminal top-level の exact-key 化 / _not_started_reason 等の死枝整理 /
  _prepare_v2_execution の多重 recheck は削除せず monkeypatched loader で実発火させる負例を追加
  (恒真外観の解消はテスト側で)

## 付録 C: W2-fix 統合レビュー申し送り

- [W5 編入] 契約不変式「attestation_mode==required ⟹ single_process=True」を env_contract __post_init__ へ (oracle 途中 recheck が reservation ゲートに結合している latent gap の構造閉鎖。field 追加なしのため hash churn なし)

## 実測段の経過 (certification attempt 1〜10、2026-07-19)

全 attempt が fail-closed + stage 別 forensic (calibration/job-staging/) で前進。総実走 ~15 分、
消費 ~0.1pt。発見と修正 (各 commit に対応):
1. 867863 (6s): qstat 時刻 field が NQSV 表記 `Started Request Time` → パーサ追加 + 実 bytes fixture
2. 867865 (7s): worktree の submodule 未実体化 (空 dir の rev-parse が親 HEAD を返す罠) → ローカル clone
3. 867866 (9s): gflags 不在 → 永続 pinned ソースから /scr 使い捨て static build
4. 867867 (11s): CMake が PATH 型変数の `:` をリスト区切り化し /scr/0:ID パスが分裂 → ジョブ dir 名の `:` 除去
5. 867868 (10s): glog 不在 (依存全量列挙で最後と確認) → gflags 同型段
6. 867869 (136s): known-values 照合が raw 表記 vs 正規化表記の別空間比較 → 正規化空間の厳密一致へ (substring の近縁 SKU 面も閉鎖)
7. 867870 (105s): probe が calibrate を包む timeout ラッパー argv のバイナリパスに自己一致 → argv JSON + execv 間接起動 (除外規律は不変)
8. 867872 (106s): perf dispatcher がノードカーネル用 linux-tools 不在 → 実体候補を機能 smoke つき選定 + PATH 注入
9. 867874 (207s): 較正初完走 (下限基準 1M、CV 0.96%) も publish の renameat2 が NFS で EINVAL → link+unlink fallback
10. **867876 (210s): accepted** — `registered/calibration-753f535a8d024727.json`
    (sha256=753f535a...cce5a49、clocks 2100、within-run CV 1.17%、bnode011、final-receipt 済み)

並行して xdist 間欠 fail (index.lock 競合 → patch 残骸) を patchharness で恒久対策
(GIT_OPTIONAL_LOCKS=0 + 有界痕跡リトライ、3 連続全走緑で実証)。型は failures F22 に記録。

## W5 (registry 登録) 結果

pegasus entry 登録 (contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01、
linux-baremetal は不変)。契約不変式 required⟹single_process 追加。意味検証 11 変異 11/11 KILL。
統合レビュー (opus) = worklog 記載。最終ゲート 1927 passed / 0 failed (rc=0)。
