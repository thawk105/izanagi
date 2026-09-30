# U2 自己検査 (2026-09-30)

## 集計器の実物照合

`aggregate-ab.py` の `run_data()` を読取り専用で既存の緑 3 走に実行した。各走とも 3 shard、`issues=[]`。値は shard 0 の代表値。W は junit suite `time`、pre は junit suite `timestamp` から `report.session_timeline.collection_finished_epoch_s` まで、T = W − pre。

| digest | W0 s | pre0 s | T0 s | max span0 s | max 占有0 s | 群 A0 s | 群 B0 s | T-080 nodeid 数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 034e88f9 | 467.527 | 98.184 | 369.343 | 359.2 | 308.9 | 3014.9 | 2267.4 | 44 |
| 46bbd9aa | 273.005 | 68.248 | 204.757 | 194.7 | 166.3 | 2056.0 | 1025.7 | 44 |
| 43ba29da | 355.801 | 138.914 | 216.887 | 206.8 | 200.5 | 1831.6 | 948.4 | 44 |

`baseline/span_result.txt` の上記 3 走 × 3 shard の maxspan・maxocc とすべて小数 1 桁で一致。`baseline/result.txt` の上記 3 走 × 3 shard の最忙 worker 占有、shard 0 の群 A・群 B 合計とすべて小数 1 桁で一致。shard 1/2 の群 A/B は 0 で、baseline の `other shards n=0` と整合。例: 43ba29da の shard 1 は maxspan=maxocc=172.1 秒、shard 2 は 162.3 秒。

W/pre/T は baseline の両テキストが同じ走について値を直接表示していないため数値照合不可。ただし W/pre の式は前 wave の `aggregate.py` と同じであり、T はその差。T-080 の nodeid 別値も baseline は nodeid 別の中央値を表示するが同一走の値を表示しないため直接照合不可。群 A/B は baseline `analyze.py` と同じ classname・name 条件。占有は junit testcase の `time` を worker property ごとに加算、span は report timeline の first/last の差。worker 占有を `report.worker_occupancy.duration_s` から転記せず junit から再計算した。

## runner 静的確認

`bash -n scratch-as0/run-pair-ab.sh scratch-as0/run-arm.sh` と `ast.parse()` による `aggregate-ab.py` 構文確認は成功。runner のソースで以下を確認した。

- 予約は `mkdir pair`、既存 pair と pid を拒否。予約後は `set -e` を使わず、エラーを配列に蓄積して `record.json` と `.done` を書く。pid 作成失敗も記録経路に進む。
- 2 腕 runner の pair ID は p1/p1r、単腕 `run-arm.sh` は p2/p2r。引数は絶対 path、既存出力 dir、40 桁 commit。2 腕 runner は異なる A/B 木・commit も要求。出力 dir が木の内側なら拒否。
- 各腕で `git rev-parse HEAD` と `git status --porcelain`、期待 commit、起動前後の tests pyc 数を記録。dirty/起動前 HEAD 不一致は起動を止める。終了後 HEAD も期待 commit と起動前 HEAD に照合する。対 1 は両腕の起動前 tests pyc = 0 を起動条件と集計の有効条件にした。対 2 の A は値を記録し、正式受入 B の pyc は受領証に値がないため未計測。
- 起動前の `ps -eo pid,etime,args` 全行、対象 2 種の process 本数と該当行、shard dir 一覧を保存。環境を各専用腕で記録し、`PYTHONDONTWRITEBYTECODE` と `PYTEST_ADDOPTS` を unset。`IZANAGI_ACCEPTANCE_SHARDS=3` で `tools/run_tests.py` を起動する。対 1 は両腕を同時起動し、開始差 5 秒超をエラーにする。各腕の開始・終了 epoch/JST、rc、log を保存。
- 各腕の log に shard marker がちょうど 1 行あることを求め、その `session_root` が shard 親 dir の直下かつ事前 inventory にないことを確認する。3 intent の group/index/submission_dir と 3 request の `repo_root` を worktree に完全一致で照合する。専用走の request に存在しない `runner_binding` は要求しない。marker 0 行/複数行や照合失敗はエラー。commit は起動前後の HEAD で束縛する。
- 集計器は外側 rc、各 shard の pytest rc/junit failures/errors、HEAD、status、環境、shard 対応、起動差を検査し、赤・欠落・不一致を無効対にする。L1〜L4 は有効な対 1 と対 2 が揃った場合だけ判定する。L4 は対 1 の W0(B) − W0(A) ≤ 0。

## 段 6 fix の実物自己検査

新しい `run_data()` の intent `submission_dir` と request shard index/count の完全照合を既存の緑 3 走 `034e88f9`、`46bbd9aa`、`43ba29da` に当てた。いずれも 3 shard、issues = []。各走の shard 0 nodeid 数は 4309、4309、4319。3 走すべての共通 nodeid の shard-0 所属を 2 組で比較すると、共通数は順に 28,310、28,339、A0 のみ 0、B0 のみ 0。これは割付一致の正例であり、本 wave の A/B 対そのものではない。差分が出た場合の例示出力と無効判定は実対では未検査。

前 wave の `acceptance-receipt-final3-green.json`、SHA で結び付く `acceptance-child-final3-1.log`、`acceptance-final3-1.started.txt` を `official_data()` に渡した。issues = []、3 shard、`tested_main = a0848199e17328eb624fd44e743fc655b96bfe99`、shard digest `8286b42c37d7861956a6d017339c3e56`、起動記録 `2026-09-30T03:21:13+0900` を取り出した。3 request の `tested_main` と `repo_root` は各々完全一致で、intent group/index/submission_dir と shard binding も一致した。受領証の `tested_tip` は `a32c9d61c2ba61e43bb2675b03396f6774197dc9` で `tested_main` と異なるため、集計器はこの 2 field を混同しない。

受領証 v5 自体に起動時刻 field と shard dir field はない。前者は正式受入を呼ぶ側の `started.txt` を別引数で受け、後者は受領証の `log_sha256` に一致する child log の `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` 行から読む。started.txt は waiter 呼出し前の時刻であり、`tools/run_tests.py` の厳密な開始時刻ではない。対 2 の起動差は診断値で、有効判定には使わない。温/冷の目安は前 wave で pre の峰 65〜80 秒 / 125〜140 秒。対 2 は両腕の pre 値と峰を出力し、L4 は対 1 だけに適用する。

対 2 の集計入力は `aggregate-ab.py OUTPUT_DIR p1 p2 --official-pair p2 --official-receipt RECEIPT --official-log CHILD_LOG --official-start-file STARTED_TXT`。`run-arm.sh p2 A_WT OUTPUT_DIR A_COMMIT` の `A_COMMIT` は正式受入の `tested_main` と同じ値にし、集計時に完全一致を再確認する。

## 残る未検査

正式受入、pytest、2 腕・単腕 runner の本走は実行していない。したがって実対での起動差、A2 と正式 B2 の commit 一致、p1 の冷条件、shard 割付不一致時の無効化、L4 の実測判定、予約後異常の動的挙動は未検査。前 wave の正式受入例では B 側の起動前 tests pyc 数を取得できない。

## 対 1 実記録での修正後検査

`meas/out/p1/record.json` と A.log/B.log を `/tmp` に複製し、実 shard dir は読み取り専用のまま修正後の `aggregate-ab.py` を `p1` に実行した。両腕の shard dir は各 log の唯一の marker から導出され、出力の `derived_shard_dir_arms` は `A`, `B`。旧 record の `A/B shard directory missing` だけが検証後に解消された。対の verdict は **invalid**: A の外側 rc=1、A shard 2 の pytest rc=1 が残る。B は外側 rc=0、3 shard とも pytest rc=0。割付は共通 nodeid 28,478、A0/B0 片側のみ 0。

| 対 1 の値 | A | B | A−B または B−A |
|---|---:|---:|---:|
| shard 0 W (s) | 293.339 | 335.124 | ΔW0 = −41.785 |
| shard 0 pre (s) | 68.570 | 89.596 | |
| shard 0 T (s) | 224.769 | 245.528 | ΔT0 = −20.759 (−9.236%) |
| max(W1,W2) (s) | 285.835 | 242.818 | B−A = −43.017 |
| max pre (s) | 91.660 | 89.596 | |

`bash -n` による両 runner の構文検査と Python AST による集計器の構文検査は成功。実記録は旧 runner によるもので終了後 HEAD 記録がなく、その項目の遡及検証はできない。修正後 runner の本走、正式受入、pytest は実行していない。

正式受入の既存 shard `8286b42c37d7861956a6d017339c3e56` を `run_data(..., official=True)` で再照合し、3 shard、issues=[]、受領証側で用いる request の `tested_main` は全 shard で `a0848199e17328eb624fd44e743fc655b96bfe99` と確認した。
