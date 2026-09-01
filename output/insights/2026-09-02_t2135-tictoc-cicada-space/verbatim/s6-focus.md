## 読んだ資料

指定資料はすべて読み取り可能だった。読めなかった path はなし。書き込み、pytest、build、benchmark は実施していない。

- `s6-parent-remeasure-2.md`
- `s6-review-b.md`
- `s6-review-a.md`
- `s6-fix1.md`
- `s4-ruling.md`
- `orchestrator/campaign/genome.py`
- `orchestrator/tests/test_campaign.py`。全体を AST parse し、対象 test の `:248-352` を逐行確認。
- `external/ccbench/cmake/Options.cmake`
- tictoc: `CMakeLists.txt`、`util.cc`、`ycsb_tictoc.cc`、`tpcc_tictoc.cc`、`bomb_tictoc.cc`、`sbomb_tictoc.cc`
- tictoc `include/` 全8件: `atomic_tool.hh`、`common.hh`、`result.hh`、`scan_callback.hh`、`tictoc_op_element.hh`、`transaction.hh`、`tuple.hh`、`util.hh`
- cicada: `CMakeLists.txt`、`README.md`、`util.cc`、`transaction.cc`
- `orchestrator/campaign/between_run_floor.py`

ただし「tictoc の `cc/tictoc/` 全体」や notes の「共通 header 全件」という断定に必要な `cc/tictoc/transaction.cc`、`external/ccbench/include/`、`external/ccbench/common/` は射影されていない。cicada の4 workload source も射影外である。

## 所見ごとの対応表

| 出所 | 所見 | 判定 | 根拠 |
|---|---|---|---|
| B must-fix 1 | cicada notes の「default 0」の誤った一般化 | closed | 現物は `SINGLE_EXEC` だけを default 0 に限定し、delay 系を空値と明記する (`genome.py:191-194`)。一次資料も `SINGLE_EXEC=0` (`Options.cmake:33`)、delay 2件は `""` (`:38-39`)。 |
| B must-fix 2 | 射影不足で全件検索などを独立検証できない | partial | README、両 CMake、delay default、cicada transaction は独立確認可能になった。一方、`tictoc/CMakeLists.txt:2` が列挙する `transaction.cc`、notes が主張する共通 header、`cicada/CMakeLists.txt:3` の workload source は射影外。全件性はなお閉じない。 |
| B must-fix 3 | fail-closed 箇所と例外型の誤り | closed | 訂正済みの親 docs は `_parse_cli_args` の `ValueError` とする (`s4-ruling.md:42-44`)。現物も `between_run_floor.py:344-347` で送出し、`:352-357` で捕捉して return 2。`:362` へ到達しない。 |
| B nit 1 | `WRITE_LATEST_ONLY` の引用が blind write 側だけ | closed | notes は blind write `:242-262` と validation `:490-529` の双方を引用 (`genome.py:197-199`)。実コードとも一致する。 |
| B nit 2 | notes test は語句だけを検査 | partial | test docstring 自体が限界を明記する (`test_campaign.py:327-328`) が、検査は依然として語句存在だけ (`:338-352`)。 |
| A nit 1 | 親の M4 期待 pair 集合が誤り | closed | 裁定は逆向き制約の集合を `{(0,0),(0,1),(1,1)}` に訂正済み (`s4-ruling.md:170`)。現行の正しい含意制約 test は `{(0,0),(1,0),(1,1)}` (`test_campaign.py:315-324`)。 |
| A nit 2 | R11 の限定句そのものを assert しない | partial | notes には「既存の非標準 CMakeCache を戻す主張ではない」が残る (`genome.py:192-193`) が、test は `fresh configure` までしか assert しない (`test_campaign.py:339`)。 |
| A nit 3 | notes test の語句検査という限界 | partial | A nit 2とは別に、C++ の事実を検査しない構造は維持されている (`test_campaign.py:327-352`)。 |

## 独立検証の結果

| 主張 | 判定 | 一次資料の file:line |
|---|---|---|
| tictoc の `PARTITION_TABLE` に live site 0 | 確認不能 | 射影内の検索結果は定義2件だけ: `Options.cmake:29`、`tictoc/CMakeLists.txt:7`。射影された `util.cc`、4 workload、`include/` 全8件には0件。ただし CMake が source として列挙する `tictoc/transaction.cc` (`CMakeLists.txt:2`) と、notes が主張する共通 header が射影外なので、`cc/tictoc/` 全件の0件は確定できない。live site は発見していないため regressed ではなく確認不能。 |
| tictoc OPTIONS に bare define がない | 一致 | `tictoc/CMakeLists.txt:4-10` の6 entry はすべて `NAME=${CCBENCH_NAME}`。 |
| cicada OPTIONS に bare define がない | 一致 | `cicada/CMakeLists.txt:4-13` の9 entry はすべて値付き。 |
| cicada README と現行 protocol code が `PARTITION_TABLE` で食い違う | 一致 | README は thread 数への table 分割を主張 (`README.md:46-47`)。CMake の protocol source は `transaction.cc` と `util.cc` (`CMakeLists.txt:2`) で、`transaction.cc:1-986` は0件、`util.cc:326-336` は option 表示だけ。ただし workload source まで含めた全件性は射影不足。 |
| delay 2件の default は空値 | 一致 | `Options.cmake:38-39` が `""`。空値 entry は normalize 時に落とされる (`:71-85`)。`genome.py:193-194` の限定は正確。 |
| `WRITE_LATEST_ONLY` は blind write と validation の双方に作用 | 一致 | blind write/RMW 選択と早期 abort は `transaction.cc:242-262`、validation の latest 限定と abort は `:490-529`。読取選択 `:79-137` には当該 flag がない。 |
| CLI の tictoc/cicada は `_parse_cli_args` の `ValueError` で止まる | 一致 | `BASELINES` は silo/mocc のみ (`between_run_floor.py:59-71`)。membership 拒否は `:344-347`、捕捉と終了は `:352-357`。baseline 参照 `:362`、build `:383-388`、測定 `:395-403` より前。 |
| 他に測定への迂回路がない | 不一致 | CLI 内の迂回路は見つからない。一方、`measure_point_floor()` の直接呼出し (`between_run_floor.py:202-252`) は protocol membership と source admission を通らず、`:213-215` と `:220-222` で測定する。これは既存の programmatic surface で、`s4-ruling.md:77-83` でも scope 外として認識済み。したがって fail-closed の結論は CLI 経路に限定すべき。 |

## 回帰の検査

| 項目 | 結果 | 根拠 |
|---|---|---|
| 軸集合 | 回帰なし | tictoc は5軸 (`genome.py:149-155`)、cicada も5軸 (`:180-185`)。test の完全一致 assert (`test_campaign.py:256-263,301-308`) と一致。 |
| 制約述語の return | 回帰なし | tictoc は両1だけを拒否する `not (A and B)` (`genome.py:85-88`)。cicada は `not PROMOTION or OPT` (`:100-103`)。 |
| `_no_wait_xor` / `SILO_SPACE` / `MOCC_SPACE` | 回帰なし | 現物はそれぞれ `genome.py:63-71,106-137`。`727ca869f^..727ca869f` の差分でも、これら既存定義への追加・削除行はない。 |
| `TICTOC_SPACE.notes` | 回帰なし | `genome.py:157-168` に死にフラグ、no-wait の3 pair、siloとの差、進行性の限界、YCSB、静的導出、bare define の説明が残る。 |
| cicada notes assert | 回帰なし | `test_campaign.py:327-352` の全 literal を AST で1件ずつ照合し、全26語句が存在した。pytest は未実走。 |

cicada notes の逐語照合は次のとおり。

| test | 要求語句 | notes | 現物位置 |
|---|---|---|---|
| `:338` | `SINGLE_EXEC` / `多版から単版` | 両方あり | `genome.py:190-191` |
| `:339` | `測るものそのもの` / `fresh configure` | 両方あり | `:190-192` |
| `:340` | `PARTITION_TABLE` / `print 専用` | 両方あり | `:194` |
| `:341` | README 不一致句 | あり | `:194-195` |
| `:342` | `WORKER1_INSERT_DELAY_RPHASE` | あり | `:196` |
| `:343` | delay 2件 | 両方あり | `:196` |
| `:344` | `計測撹乱ノブ` | あり | `:197` |
| `:345` | `WRITE_LATEST_ONLY` / 読み側不変 | 両方あり | `:197-198` |
| `:346` | `余分に abort` | あり | `:197-198` |
| `:347` | `(OPT,PROMOTION)=(0,1)` / `(0,0)` | 両方あり | `:199-201` |
| `:348` | CC/data path 同一 / 起動時表示差 | 両方あり | `:201-203` |
| `:349` | `24` / `YCSB workload` | 両方あり | `:203` |
| `:350` | `静的導出` / `実測ではない` | 両方あり | `:203-204` |
| `:351` | `bare define` / 残存候補なし | 両方あり | `:204` |
| `:352` | CLI 個別指定 / 全組合せの限定 | 両方あり | `:188-190` |

## 残る must-fix

B must-fix 2が1件残る。

`tictoc/transaction.cc`、notes がいう共通 header の実体、cicada の workload source を射影へ追加して全件不在を独立検証可能にするか、`genome.py:159-160,194-197` の断定を実際に検証できた範囲へ弱める必要がある。

CLI の直接 function 呼出しによる迂回路は実在するが、既存 surface として裁定済みの scope 外であり、今回の新しい must-fix には格上げしない。ただし「module 全体が fail-closed」と一般化してはならない。

## 総括

B must-fix 1・3、B nit 1、A nit 1は閉じている。
default、bare define、README不一致、`WRITE_LATEST_ONLY` の両作用点は一次資料と一致した。
一方、全件不在を証明する射影はなお不足しており、B must-fix 2は partial のままである。
CLI は `ValueError` で測定前に閉じるが、`measure_point_floor()` 直接呼出しは既存の迂回路である。
軸・制約・tictoc notes・cicada notes の全26 assert 語句に回帰は見つからなかった。
pytest、build、benchmark は実走していない。