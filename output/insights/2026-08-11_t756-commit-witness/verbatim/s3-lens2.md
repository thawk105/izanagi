静的検査のみ実施しました。必須資料はすべて読了し、pytest・実測・編集は行っていません。コード上の反例と、現行経路では破れなかった面を分けます。

## 所見

### L2-1

- 主張: `C` 行数と `commit_counts_` の一致は Silo/YCSB に限定され、TPCC・BoMB 系へ一般化すると終了競合で正しい trace を赤にする。
- 根拠: `external/ccbench/include/ycsb.hh:161-167` は commit 後に必ず counter を増やす一方、`external/ccbench/include/tpcc.hh:102-112`、`external/ccbench/include/bomb.hh:1144-1154`、`bomb_static.hh:106-116`、`bomb_pessimistic.hh:1233-1243`、`dbomb_deterministic.hh:435-445`、`sbomb_deterministic.hh:224-234` は commit 後に `quit` を検査してから counter を増やす。worker は `external/ccbench/common/runner.hh:192-194,297-300` で quit 通知後も join まで実行中 transaction を完了しうる。現行 verify flags は `orchestrator/campaign/pipeline.py:97-112` の YCSB のみ。
- 失敗シナリオ: TPCC/BoMB の `tx.commit()` 中に `quit=true` となる。`external/ccbench/cc/silo/transaction.cc:584-607` で C 行は出るが、workload 側は counter 増分前に return する。trace は N 件、stdout witness は N-1 件となり、`trace-batch` ではない通常 run が mismatch/indeterminate で abort される。
- 深刻度: must-fix。TPCC/BoMB を verify 対象へ再利用した場合、正しい variant が受理集合から除外され、fitness も付かない。
- 処方: witness 検査の適用条件を `silo + YCSB` に明示的に限定する。別 workload を対象にする場合は、その commit 後 counter の終了契約を個別に証明してから有効化する。

### L2-2

- 主張: 同じ `trace_dir` を再利用すると、`ofstream` の open 失敗時に前 run の trace が残り、commit witness と一致して false-green になりうる。
- 根拠: `external/ccbench/include/trace.hh:49-62` は `open` の成否を確認せず、`std::ios::trunc` は `is_open()==false` の間は再試行される。`orchestrator/verifier/parse.py:203-225` は run ID や生成時刻を確認せずディレクトリ内全 trace を読む。pipeline 自身は `orchestrator/campaign/pipeline.py:849-850,916-917` で一時ディレクトリを作るが、`_run_trace` の一般契約には空ディレクトリ検査がない。
- 失敗シナリオ: run A の N 件の完全 trace を残した同一ディレクトリで run B を実行し、既存 `trace_*.log` の権限不良で全 open が失敗する。run B の `commit_counts_` が偶然 N なら、B は trace を一行も書いていないのに `len(txns)==N` となり、serializable trace として認証される。
- 深刻度: must-fix。再利用経路では前 run の証拠が現 run の verifier JSON・受理判定・fitness に混入する。
- 処方: witness run の開始時に `trace_dir` が存在しない、または `trace_*.log` がゼロであることを必須条件にする。現在の pipeline の fresh-temp 契約を直接 API・校正経路にも明示する。

### L2-3

- 主張: `_run_trace` の `parse_bench_stdout` 利用は、重複した `commit_counts_:` の last-wins により witness を偽造できる。
- 根拠: `orchestrator/calibrator/benchparse.py:20-36` は辞書へ代入するだけで重複を拒否しない。プランも `s2b-plan.md:91-108` で同じ辞書化を採用している。通常の CCBench 出力は `external/ccbench/common/result.cc:47-50,633-638,677-682` で一回だけ出る。
- 失敗シナリオ: stdout が `commit_counts_:\t100` の後に `commit_counts_:\t1` を含み、trace には一件だけ残る。辞書値は 1 となり、`expected_commits=1`、`len(txns)=1`、batch=0 で、真の counter 100 に反して certified になる。
- 深刻度: blocker。攻撃可能な stdout で不完全 trace が certified となり、受理集合と winner/fitness が不当に拡大する。
- 処方: unprefixed な `commit_counts_` と `batch_commit_counts_` は各一行だけを許可し、重複時は fail-closed にする。`#` 付き provenance key は別名として扱う。

### L2-4

- 主張: S2 calibration の verifier 経路には expected witness が渡らず、S2 の独立校正結果は FN-1 を引き続き受理する。
- 根拠: `orchestrator/campaign/s2_verify_calibration.py:130-150` は commit counter を取得するが、`_verifier_run` は `:155-178` で expected 値なしの CLI を起動する。`_measure_candidate:194-207,222-231` は verifier の `certified` だけを gate2 に使う。S2 binary は `:278-285` で `ycsb_silo.exe` を実行する。プランの配線一覧 `s2b-plan.md:176-183` にもこの経路がない。
- 失敗シナリオ: 最大 txid 側の trace file を失ったが残存 txid が密連番に見える trace を S2 calibration に渡す。CLI は expected なしで `certified=True` を返し、`stock_certified` と候補 gate が緑になる。
- 深刻度: must-fix。S2 calibration JSON の `certified`・`stock_certified`・選択された extime が、不完全 trace を根拠に緑となる。
- 処方: calibration 側にも同じ witness を渡すか、S2 calibration を受理判定ではなく計測専用と明記する。pipeline の extra correctness 経路（`orchestrator/campaign/loop.py:138-145`）とは別経路であることを文書化する。

### L2-5

- 主張: 新設する `trace-no-commit-witness` と `trace-batch-commits-unattributed` は critic の構造化 liveness rejection に接続されていない。
- 根拠: プランは `s2b-plan.md:121-135` で新 reason を追加するが、`orchestrator/critic/digest.py:116-122` の `LIVENESS_REASONS` と `:273-314` の分類には存在しない。未知 reason は `other` 件数へ落ちる。pipeline は `orchestrator/campaign/pipeline.py:504-507,731-746` で abort、campaign は `orchestrator/campaign/loop.py:290-295` で fitness なしにする。
- 失敗シナリオ: 正しい TPCC 系 run が終了競合で witness mismatch となる、または stdout の計器形式が変わって missing witness となる。variant・genome・workload を持つ構造化 rejection にならず、critic には未知 reason の集計値だけが渡る。
- 深刻度: must-fix。fitness は安全側に付かないが、variant ごとの帰属・次手生成の参照・campaign の失敗原因分類が失われる。
- 処方: 新 reason を `LIVENESS_REASONS` と `_LIVENESS_HINTS` に追加し、witness 値と workload を `extra` として保持する。missing witness と unsupported batch は別の説明文にする。

### L2-6

- 主張: プランの #1〜#11 の変異表は主要な verifier/pipeline 結線を覆うが、stdout 重複、trace_dir 再利用、非 YCSB終了競合、S2 calibration の fail-open を検出する変異がない。
- 根拠: `s2b-plan.md:340-356` の変異表は core 比較、`clean()`、report、5-tuple、guard、keyword 結線を対象にする。一方、`benchparse.py:20-36` は重複入力を未検査で、非 YCSB counter 経路は上記 L2-1、S2 calibration は `s2_verify_calibration.py:155-178` にある。
- 失敗シナリオ: 実装者が last-wins を残したまま実装しても、計画された #1〜#11 の入力はすべて一意 stdout・fresh trace・YCSB なので全て緑になる。
- 深刻度: must-fix。受理集合を拡大する実装欠陥が mutation suite で検出されず、そのまま land しうる。
- 処方: duplicate metric、既存 trace file、quit 中 commit、S2 calibration の mismatch を各一件ずつ追加する。既存 #2/#3 と #6/#10 は同一テストで kill されるため、mutation report 上の帰属も明記する。

## 攻撃したが破れなかった面

- 現行 Silo/YCSB の通常経路では、`ycsb.hh:161-167` が commit 成功後に必ず counter を増やし、Silo は `transaction.cc:584-596` で一件だけ C を出す。`runner.hh:297-300` の join 後に thread-local stream destructor が走るため、正常終了時の flush 順序も成立する。
- validation 失敗では `transaction.cc:693-699` が `writePhase()` を呼ばず、abort の `gc_records()`（`:27-40`）も C を出さない。成功時は C emit 後に `gc_records()`（`:687-690`）を行うため、epoch/GC 境界が C emit を飛ばす反例は見つからなかった。
- open 失敗・disk full では `ofstream` が fail state のまま C 行を落としうるが、fresh directory なら pipeline の `ncommit==0` または witness mismatch で赤になる。`std::terminate` も join 前に正常 flush を保証しないが、process return code 非ゼロを先に拒否する。なお C 行だけ残って R/W が落ちる FN-2 は `brief.md:16-19` と `s2b-plan.md:225-230` が明示的に残す負債である。
- `local_batch_commit_counts_` はこの pin の CCBench tree では宣言・集計のみで増分箇所がなく、`result.hh:16-20`、`result.cc:685-690` に限られる。Silo の batch defaults も `external/ccbench/cc/silo/include/common.hh:40-45` で 0、pipeline の YCSB flags に batch 指定はない。したがって現在の green Silo/YCSB run が `trace-batch-commits-unattributed` で赤になる反例は静的には成立しない。BoMB 系も `local_commit_counts_` を使い、batch counter ではない。
- `parse.py:105-116` の last-wins は duplicate txid を `dup_txids` に記録し、`Integrity.clean()` が false になる設計なので、同一 trace 内の重複 C は `len(txns)` 比較だけで false-green にはならない。global txid も `trace.hh:41-46` で thread 間共有される。
- trailing `_`、タブ区切り、`#` provenance 行は `benchparse.py:27-35` の仕様と整合する。欠落・非整数はプランの `None` guard で fail-closed になる。問題は重複行だけである。
- 凍結証拠は、`silo_ladder_rung1.py:1425-1445` の exact key 検査、`:2842-2857` の trace 再計算、`test_silo_ladder_rung1_evidence.py:1060-1064` の完全辞書一致、`test_silo_ladder_rung1_driver.py:73-86,322-340,623-626` の fixture/schema、`t152_write_intent_coverage.py:444-466,527-542` とその test `:760-799` で横断確認した。実 artifact の byte pin は `output/.../raw-manifest.json:1656-1657` の `correctness/verifier.json` hash である。
- プランは witness なしの `result_to_dict` を条件付き挿入にし、`s2b-plan.md:264-268` で key・値・順序・bytes の regression を予定している。これを守る限り、再凍結の実機再走は不要である。bytes が変わる場合だけ、計算ノードで ladder probe を再走して manifest/hash を再凍結する必要がある。
- 規律5の観点では、新 module・schema version・汎用 framework・設定 flagを導入せず、optional fields と既存 parser の再利用に留めている。`s2b-plan.md:157-183` の7ファイル案は、現時点で過剰機構とは判定しない。

## 総括

現行の Silo/YCSB・batch=0・fresh trace 経路は安全側に倒れる設計です。一方、stdout 重複は blocker、mocc 適用・trace_dir 再利用・S2 calibration・critic reason 接続・未カバー変異は land 前の must-fix です。