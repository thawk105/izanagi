## 読んだ資料

指定された 12 資料をすべて読了した。書き込み、build、pytest、benchmark は実施していない。

- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s4-ruling.md`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s6-integrated.diff`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s3-parent-remeasure.md`
- `orchestrator/campaign/genome.py`
- `external/ccbench/cc/tictoc/transaction.cc`
- `external/ccbench/cc/tictoc/util.cc`
- `external/ccbench/cc/tictoc/CMakeLists.txt`
- `external/ccbench/cc/cicada/transaction.cc`
- `external/ccbench/cc/cicada/util.cc`
- `external/ccbench/cc/cicada/include/transaction.hh`
- `external/ccbench/cmake/Options.cmake`
- `orchestrator/campaign/between_run_floor.py`

## tictoc の主張照合

| 主張 | 判定 | 一次資料の file:line |
|---|---|---|
| `:626` で lock word を内側 spin loop 内から再読込する | 一致 | `cc/tictoc/transaction.cc:561-635` が内側 `for (;;)`、`:626` がその中の `loadAcquire` |
| 外側 `retry:` は write-set loop `:556-557` | 一致 | `cc/tictoc/transaction.cc:556-557` |
| 内側 spin loop は `:561-635` | 一致 | `cc/tictoc/transaction.cc:561-635` |
| `(1,1)` は `#if` が選ばれ、`#elif` が dead なので `(1,0)` と同じ | 一致 | `cc/tictoc/transaction.cc:564-624` |
| `SLEEP_READ_PHASE` は `:68-70` の計測撹乱ノブ | 一致 | `cc/tictoc/transaction.cc:68-70`。read 冒頭で `sleepTics` を挿入する |
| `PARTITION_TABLE` は protocol、workload、共通 header の全件検索で live site なし | 確認不能 | 射影内では `cc/tictoc/CMakeLists.txt:7` の option 定義以外に出現なし。ただし `cc/tictoc/include/`、workload source、`external/ccbench/include/`、`common/` は射影外で、親の報告を一次資料として再検証できない |
| `OPTIONS` に bare define はない | 一致 | `cc/tictoc/CMakeLists.txt:4-10`。全項目が `NAME=${CCBENCH_NAME}` 形式 |
| `PREEMPTIVE_ABORTS` と `TIMESTAMP_HISTORY` は独立軸 | 一致 | 前者は read 経路の `transaction.cc:128-139`。後者は `:379-406`、`:508-511`、no-wait 内の `:587-606` に独立 site がある |

## cicada の主張照合

| 主張 | 判定 | 一次資料の file:line |
|---|---|---|
| `SINGLE_EXEC` は多版から単版へ測定対象を変える | 一致 | `cc/cicada/transaction.cc:85-119`、`:235-289`、`:705-707`、`:762-768`、`:952-955` |
| `PARTITION_TABLE` は print 専用で README と現行コードが食い違う | 確認不能 | 射影内コードでは `cc/cicada/util.cc:326-336` の表示だけ。ただし README と残りの protocol/workload source が射影外なので、全件性と README 文面は独立確認不能 |
| `WRITE_LATEST_ONLY` は読取選択を変えず、保守側に余分な abort を加える | 一致 | read 選択 `transaction.cc:79-137` は flag を参照しない。書込側 `:242-270` と validation `:490-529` で、より新しい latest がある場合を abort 側へ狭める。正しさを緩める分岐はない |
| `(OPT,PROMOTION)=(0,1)` の CC/data path は `(0,0)` と同じ | 一致 | `transaction.cc:128-135` と `include/transaction.hh:199-215` の二つの data-path site は、いずれも外側の `#if INLINE_VERSION_OPT` 内 |
| `util.cc:330` は promotion 値を `INLINE_VERSION_OPT` の外側で表示する | 一致 | `cc/cicada/util.cc:326-336`。`:330` は無条件の `ShowOptParameters()` 本体 |
| genome にない flag は fresh configure で default 0 | 不一致 | `SINGLE_EXEC`、`PARTITION_TABLE`、`WORKER1_INSERT_DELAY_RPHASE` は 0 (`Options.cmake:29,33,49`)。しかし `INSERT_READ_DELAY_MS` と `INSERT_BATCH_DELAY_MS` は空文字 default (`:38-39`) で、normalize 時に定義自体を落とす (`:71-85`) |
| `OPTIONS` に bare define はない | 確認不能 | cicada の `CMakeLists.txt` が射影に含まれていない。`Options.cmake` の helper だけでは呼出し側の bare define 不在を証明できない |
| delay 3 件は計測撹乱ノブ | 確認不能 | `WORKER1_INSERT_DELAY_RPHASE` は commit 前の直接 delay なので一致 (`transaction.cc:923-927`)。`INSERT_READ_DELAY_MS` と `INSERT_BATCH_DELAY_MS` の使用 source は射影外で、`Options.cmake:38-39` の名称と単位だけでは確定不能 |

## 規律の観点

- 規律 2: `WRITE_LATEST_ONLY` は読取選択コードを変更せず、更新を latest に限定して追加 abort 側へ狭める。正しさゲートを緩める軸ではなく、`SINGLE_EXEC` と同じ理由で外す必要はない。ただし parent の根拠は `:242-262` だけでなく validation の `:490-529` も含めるべきである。
- 規律 4: 登録された両空間の軸に、確認できた delay/sleep ノブは混入していない。軸一覧は `genome.py:149-155,180-185`。
- 規律 6: notes は README を権威として引用せず、「現行コードとの食い違い」と記述している。この書き方は正しい。ただし README 自体が射影外なので、食い違いの事実は今回独立確認できない。
- 正しさ境界: `BASELINES` は `silo` と `mocc` だけ (`between_run_floor.py:59-71`) で、`SPACES` を import・参照しない。CLI は `:344-347` で membership を検査し、`:363` の source admission も `SPACES` から独立している。したがって今回の登録だけでは floor 測定経路は開かない。
- ただし `:363` は、その docstring 自身が述べるとおり trace hook の文字列証拠だけであり、意味論的正しさや verifier 成功を証明しない (`:111-121`)。また直接の `measure_point_floor()` 呼出し (`:202-252`) はこの二層を通らない。これは既存面であり今回の差分が開いたものではない。

## must-fix

- `genome.py:191-193` の「genome に列挙しない flag は fresh configure で default 0」という一般化を、少なくとも `SINGLE_EXEC` など numeric boolean flag に限定すること。`INSERT_READ_DELAY_MS` と `INSERT_BATCH_DELAY_MS` は空値・未定義であり、逐語では事実と一致しない。
  成果物影響: 下流が omitted flag を一律 numeric 0 と解釈し、build identity や軸候補の判定根拠を誤る。

- 独立確認に必要な `cc/tictoc/include/`、workload source、共通 header、cicada README/CMakeLists/workload source を review 射影へ含めるか、全件検索・README 不一致・delay 2 件・cicada bare define 不在の断定を弱めること。
  成果物影響: これらの不在・意味論主張は軸の除外と受理集合を直接決めるため、親の報告だけでは独立 review を通せない。

- `s3-parent-remeasure.md:50-51` の「`BASELINES[protocol]` で `KeyError`」を修正すること。現行コードは先に `between_run_floor.py:344-347` で `ValueError` を送出し、`:362` の添字参照には到達しない。
  成果物影響: 正しさ境界の fail-closed 箇所と期待例外を誤った参照として残す。

## nit / backlog

- `WRITE_LATEST_ONLY` の説明は semantic conclusion として妥当だが、parent の `transaction.cc:242-262` だけという引用は不完全で、validation の `:490-529` も作用点である。軸集合は変わらないため nit。
- notes test は C++ の事実ではなく語句だけを検査する。この限界は test docstring と裁定で明記済みで、現差分の受理集合を直ちに変えないため backlog。
- `measure_point_floor()` の直接呼出しなど既存の pre-verifier measurement surface は残る。今回の `SPACES` 登録とは独立なので本 review の must-fix にはしない。

## 総括

tictoc の no-wait 制御構造、行番号、24 通りの制約根拠は一次資料と一致した。
cicada の `SINGLE_EXEC` 除外、promotion 含意、`WRITE_LATEST_ONLY` 採用も静的には妥当である。
一方、fresh default 0 の一般化には一次資料との不一致がある。
さらに全件不在、README、cicada CMake、delay 2 件は現在の射影では独立確認できない。
正しさ境界については、今回の登録だけで floor 測定経路が開かないという狭い結論を支持する。