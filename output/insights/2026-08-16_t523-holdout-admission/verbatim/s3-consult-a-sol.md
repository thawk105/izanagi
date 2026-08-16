### 所見 1
- severity: must-fix
- 攻撃シナリオ: freeze の H1 セルと floor binary を取得し、`backoff_profile._profile_run(binary, cell["workload"], tmp)` を直接呼ぶ。これは `perf record` で binary を実行して TPS を返すが、`run_once`、admission、台帳を一度も通らない。
- 根拠: `orchestrator/campaign/backoff_profile.py:104-129,137-160`、`orchestrator/campaign/s8b_floor_contract.py:302-314,352-362`、`plan_v1.md:58-59`
- 成果物影響: H1/H2 の TPS を台帳外で取得でき、certified 選択の「未観測 holdout」参照が偽になる。
- 提案: TPS を取得する全 production subprocess を共通 effect gateway へ移し、YCSB binary の直接実行と `parse_bench_stdout` の組を静的検査で禁止する。

### 所見 2
- severity: must-fix
- 攻撃シナリオ: `flags.txt` に `--ycsb_rratio=80` と残りの座標を書き、`run_once(binary, ["--flagfile=/path/flags.txt"], admission=None)` を呼ぶ。提案 classifier は明示された `-ycsb_rratio=` を見つけず非 holdout と判定する一方、CCBench の gflags は flagfile を展開して rr80 を実行する。同様に `FLAGS_ycsb_rratio=80` と `--fromenv=ycsb_rratio` でも通る。
- 根拠: `plan_v1.md:40,45`、`orchestrator/calibrator/runner.py:366-376,409-422`、`external/ccbench/cc/silo/ycsb_silo.cc:24-27`、`external/ccbench/include/ycsb.hh:20-25`
- 成果物影響: classifier の判定対象が実効引数に対して空になり、rr80 の throughput が台帳外で観測される。
- 提案: `--flagfile`、`--fromenv`、`--tryfromenv` を gateway で拒否し、`FLAGS_*` を除いた閉じた環境と正規化済み direct flag だけを binary へ渡す。

### 所見 3
- severity: must-fix
- 攻撃シナリオ: canonical protocol/freeze を使い、`mode="pilot"` で `perf_preflight_fn` に「既存 floor binary を rr80 で直接実行してから正常 receipt を返す」callback を注入する。callback は manifest と提案台帳の作成前に呼ばれるため、admission なしで測定できる。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:4052-4081,4139-4144,4300-4302,4386-4395`、`orchestrator/tests/test_s8b_floor_campaign.py:3004-3029`、`brief.md:30-33`
- 成果物影響: pilot の事前観測が台帳に残らず、後続レポートは未観測 holdout を扱ったように見える。
- 提案: production entrypoint では全 mode で副作用可能な seam を拒否する。テスト注入は測定効果を持てない private harness に隔離する。

### 所見 4
- severity: must-fix
- 攻撃シナリオ: 現行 `TrialLaunchAdmission` と同型の `_seal` 実装にすると、caller は module-private seal を import して正しい field とともに dataclass を構築できる。さらに `copy.copy` や seal を変更しない `dataclasses.replace` は同じ seal object を保持するため、seal identity だけの検査を通る。
- 根拠: `orchestrator/campaign/trial_registry.py:67-69,164-175,1364-1372`、`orchestrator/tests/test_trial_registry.py:1214-1216`、`plan_v1.md:112-115,191-193,295-300`
- 成果物影響: 台帳 append を経ない偽 admission で `run_once` が受理され、ledger row と測定値の対応が消える。
- 提案: seal ではなく `id(token) -> state` に token 本体を保持し、`state.token is token` を要求する identity capability にする。copy、pickle、dict 復元、private seal 使用を境界テストへ加える。

### 所見 5
- severity: must-fix
- 攻撃シナリオ: `admit_floor_holdout_observations` から H1 の正規 token を一度取得した後、同じ binary と完全に同じ gflags で `run_once(..., admission=token)` を任意回数直接呼ぶ。token は発行済みで payload も一致するため毎回通るが、台帳は最初の `admit` 一行から増えない。
- 根拠: `plan_v1.md:123-125,167-181,207-213`、`brief.md:46,82-85`、`orchestrator/calibrator/runner.py:392-450`
- 成果物影響: 一つの ledger key で任意の best-of-N が可能になり、レポートの値を選別しても観測回数は一件と表示される。
- 提案: campaign admission と別に、既存 schedule の attempt ごとの single-use ticket を測定直前に durable 消費する。これを T-524 として除外するなら、T-523 だけでは I3 を満たせないと裁定へ返す。

### 所見 6
- severity: must-fix
- 攻撃シナリオ: 同じ HEAD から二つの Git worktree を作り、各 worktree で同時に pilot を開始する。`repo_output_root()` は各 checkout 配下を返すため台帳 inode と `flock` が別になり、双方が「初回」として同じ12 keyを取得する。
- 根拠: `.git:1`、`orchestrator/campaign/layout.py:40-46`、`plan_v1.md:149-154,185`
- 成果物影響: 同一 repository、同一 key に二つの ledger と二組の floor 値が生まれ、proof chain の権威参照が非一意になる。
- 提案: `git rev-parse --git-common-dir` から導く共有 durable rootなど、全 worktree が同じ物理台帳と lock を使う設計にする。

### 所見 7
- severity: must-fix
- 攻撃シナリオ: 一回目の実測後、ledger を commit する前に `ledger.jsonl` だけを削除し、新しい fresh run を起動する。Git history に ledger blobがないため history tip は `None` となり、helper は空の新規台帳を作って同じ key を再受理する。
- 根拠: `plan_v1.md:167-185`、`orchestrator/campaign/trial_registry.py:1581-1611,1624-1634,1653-1659`
- 成果物影響: 同じ holdout セルを二回観測しても最終 ledger には二回目の行しか残らず、レポートの観測回数が過少になる。
- 提案: reservation 行を commit または外部 append-only authority へ確定するまで測定を開始しない二段階手順にする。`fsync` と実測後 commit の運用記述だけでは塞がらない。

### 所見 8
- severity: must-fix
- 攻撃シナリオ: 少なくとも seq0 を測定したところで crash させ、manifest と ledger を残して `journal.jsonl` を削除する。その run dir を `--resume` すると、journal 不在は空 list、manifest 有りかつ campaign-start 無しは `M-prestart` と分類される。既存 ledger rowから token が再発行され、started seq が空なので seq0 から再測定される。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:902-925,3617-3635,4404-4414`、`orchestrator/campaign/s8b_floor_contract.py:451-466`、`plan_v1.md:172-177`
- 成果物影響: ledger 行数を増やさず同一 session を再観測でき、floor 値を都合の良い再走へ差し替えられる。
- 提案: ledger 発行後は journal 不在を拒否し、attempt authorization を権威台帳にも append して resume の skip 集合を journal だけから導出しない。

### 所見 9
- severity: must-fix
- 攻撃シナリオ: 一回目の完了後、holdout workload と binary を変えずに canonical protocol の `master_seed` だけを変更した commit を作る。新 HEAD blob は提案 authority を通り、`protocol_sha256` が変わるため ledger key も変わり、同じ H1/H2 セルを fresh run として再受理する。
- 根拠: `plan_v1.md:90-108,121-147`、`orchestrator/campaign/s8b_floor_campaign.py:556-577,619,4193-4199`、`orchestrator/campaign/t080_freeze_migration.py:47-50`
- 成果物影響: 同じ実質 workload の二回観測が別 key として合法化され、holdout 性が protocol bytes の変更だけでリセットされる。
- 提案: raw freeze/protocol hash は証跡 field に残し、一回性判定には測定効果を表す安定した cell fingerprint を使う。再観測の解除には別の明示的な人間裁定 capability を要求する。

### 所見 10
- severity: must-fix
- 攻撃シナリオ: 通常 calibration CLI に `--workload ycsb_rratio=20,ycsb_zipf_skew=0,ycsb_rmw=1` を渡す。これは freeze の H2（skew 0.9、rmw 0）とは異なる非 freeze 入力だが、ratio-only gate は admission 不在として拒否する。
- 根拠: `orchestrator/calibrator/cli.py:98-108,124-147`、`output/s8b-freeze/holdout_freeze.json:307-315`、`plan_v1.md:72-76,255-261`、`brief.md:21-23,49-50`
- 成果物影響: 合法な calibration の受理集合とレポート集合が縮み、brief I5 と「一件も巻き込まれない」という一般化が破れる。
- 提案: rr20/rr80 全体を予約語化する明示裁定を得るか、freeze provenance を保持した typed execution request に設計し直す。現状のまま I5 充足とは記録しない。

### 所見 11
- severity: must-fix
- 攻撃シナリオ: 将来、canonical freeze と既存 verifier に H3=`rr30` を追加するが、neutral leaf の H1/H2 表を更新し忘れる。第三 producer がその freeze cell を `run_once` に渡すと ratio30 は非 holdout と分類され、token なしで実行される。
- 根拠: `plan_v1.md:72-76,191-201`、`orchestrator/campaign/s8b_floor_contract.py:317-362`、`orchestrator/campaign/s8b_holdout_freeze.py:984-1001`
- 成果物影響: 将来の H3 throughput が ledger 外へ漏れ、族一般化したはずの certified 選択が H1/H2 専用防壁へ退化する。
- 提案: ratified freeze の全 holdout と protected signature table の exact 集合一致を production gate にし、未知 holdout は拒否する。できなければ設計主張を「現行 H1/H2 限定」へ狭める。

### 所見 12
- severity: should
- 攻撃シナリオ: 変異3で callback 直前 assert を `pass` にし、計画どおり `_validate_live_admissions` を通さない private helper testへ forged tokenを渡すと赤になる。一方、同じ forged tokenを production の `_Runner.run()` に渡すと、前段の全 token 検査が base と mutant の両方を callback 前に拒否するため、production 受理集合は変わらない。
- 根拠: `plan_v1.md:49-52,227-233,349-354`、`orchestrator/campaign/s8b_floor_campaign.py:3569-3589`
- 成果物影響: mutation ledger は「防壁を KILL した」と記録するが、certified artifact の受理集合に対する当該行の帰属は成立しない。
- 提案: genuine mapping が前段を通過した後に token を交換する TOCTOU 入力で production pathを赤にするか、重複検査なら変異対象から外して唯一の権威境界へ統合する。

## 総括

NO-GO。  
`run_once` 外の実 throughput 経路と gflags の間接入力だけで、台帳なしの H1/H2 観測が成立する。  
正規 admission も再利用可能であり、一行の台帳から任意回の best-of-N を実行できる。  
台帳は worktree 分離、未 commit 削除、journal 削除 resume に対して権威になっていない。  
ratio-only 判定は brief I5 も破り、事前登録変異の一部は production 境界への帰属が成立しない。  
本所見は静的検査のみであり、pytest、CCBench 実測、変異 harness は実行していない。