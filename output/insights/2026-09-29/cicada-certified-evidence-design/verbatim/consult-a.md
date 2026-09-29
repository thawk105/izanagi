## 所見

- **A1｜must-fix｜brief P1・P2、plan §2 U。** U は「W 行ごとに設置・公開を確認する」片方向の照合で、**公開された版を W 行が漏れなく記録したか**を確認しない。P も sort 前後だけを比べる。根拠: `plan.md:20-21,28`、`external/ccbench/cc/cicada/transaction.cc:481-530,687-720`、`external/ccbench/cc/cicada/include/transaction.hh:247-256`。具体例は、T1 が `R(x₀), W(y₁)`、T2 が `R(y₀), W(x₂)` を実行し、両方の読みを先に済ませてから書きを公開する列である。本来は `T1→T2→T1` の巡回になる。壊れた variant が T1 の `y₁` 公開後、trace 出力前に write set からその要素を落とすと、P は通過済み、U は出力された W だけを調べ、判定器から `y₁` の辺が消える。**放置すると、巡回する variant が certified になり、論文の「検査した実行履歴」も誤る。** 設置・公開の台帳と W 行を世代・key・op ごとに**双方向**照合し、sort 後から emit までの消失も拒否する。

- **A2｜must-fix｜brief P2・P4、plan §2 B・H。** B の「read set 登録時の世代」と「終了時の世代」が一致しても、その間に返した `TupleBody*` が別世代の body を指していた区間を保証できない。`read()` は read set への登録後に body pointer を返し、workload が commit 前に消費する。inline 版は `unused` に戻して再取得でき、通常版も GC 後に再利用できる。`REUSE_VERSION=0` は解放する。根拠: `external/ccbench/cc/cicada/transaction.cc:126-137,156-189`、`external/ccbench/include/ycsb.hh:121-143,161-169`、`external/ccbench/cc/cicada/include/transaction.hh:173-195,217-245`、`external/ccbench/cc/cicada/include/tuple.hh:54-71`。`ycsb_cicada.cc` と `tpcc_cicada.cc` は runner に workload を渡し、TPC-C も `tpcc.hh:102-114` で workload の後に commit するため、調べた経路に commit 後の body 消費は見当たらない。問題の窓は**read 登録から workload の最後の body 消費まで**である。**放置すると、回収→同一アドレス再利用→終了時に整合した値を読む列を見逃し、壊れた GC 接続を certified にし得る。** 退役・再利用を消えないイベントとして記録し、read 登録から body 消費終了までの世代不変を照合する。`REUSE_VERSION=0` は解放済み object を決して再参照せず、隔離または対象外にする。

- **A3｜must-fix｜brief P2・P3、plan §2 B・U。** B/U の記録点は、pending を待った後の status、aborted 版の飛ばし方、read set からの再読、read-own-write、update/delete による集合変更をまだ閉じていない。特に trace は read set を列挙する一方、`read()` は read set または write set の既存要素から body を返し、`delete_record()` は既存 write を erase する。read-only は validation を通らず return する。根拠: `external/ccbench/cc/cicada/transaction.cc:103-126,153-165,205-217,348-401,934-956`、`patches/instr-cicada-trace.patch:68-97,119-130`。**放置すると、成功 API 操作や再読を trace が代表していない variant でも R/W 件数と H の自己申告が一致し、受理集合が広がる。** YCSB に限定しても、API の成功 read/write intent、read set・write set の遷移、commit frame の R/W を双方向に突き合わせる契約が必要。read-own-write は外部版への R として出さない場合も、その省略規則と body の同一性を明記する。TPC-C の不在読み・scan・delete は別契約とする。

- **A4｜must-fix｜brief P1、plan §2「設置順は診断」。** BHG の論理は、忠実な reads-from、各 key の実在版を漏れなく含む全順序、対象とする履歴の終状態の扱いが揃えば、**物理的な設置時刻順そのもの**を必須にしない根拠になる。ただし現判定器が使う順序は W の commit 版 ID の数値順で、物理鎖順や最終状態を検査しない。根拠: `orchestrator/verifier/dsg.py:455-479,752-785`、`external/ccbench/cc/cicada/transaction.cc:515-530`。例えば `W₁(x₁), W₂(x₂)` を数値順 `1<2` と記録し、物理的な最終可視版が `x₁` でも、終端 read が無ければグラフは非巡回のままになる。**放置すると「観測した R/W の 1SR」を「実行終了時の状態を含む正しさ」へ拡大して論文に書いてしまう。** P1 は狭い 1SR 主張として残せるが、終状態を主張するなら終端 read または最終版の証拠を足す。U の全公開版被覆と、数値版順を採用できる条件も明文化する。

- **A5｜must-fix｜brief P4、plan §2・§5。** `H.read_checked == R 行数` は、両方が同じ read set のサイズから作られれば恒真である。照合を飛ばしても `H` と R は一致する。文面検査も emitter が literal `#if TRACE` に存在することだけを見る。根拠: `plan.md:28-30,55`、`orchestrator/verifier/model.py:233-267`、`patches/instr-cicada-trace.patch:77-89`。**放置すると照合を実行しない variant が certified になる。** H は補助的な完全性検査と位置付け、独立した照合結果・違反経路を確かめる positive control を各分岐に置く。件数一致だけを発火証明と呼ばない。

- **A6｜must-fix｜brief P2、plan §2・§6。** 現行の文面検査は CMake `SOURCES` の `.cc` だけを読む。Cicada の `SOURCES` は `transaction.cc util.cc` で、`precheckInValidation()` と既存 `traceCommit()` の本体は header 側にある。根拠: `external/ccbench/cc/cicada/CMakeLists.txt:1-3`、`orchestrator/verifier/model.py:119-180,204-230`、`external/ccbench/cc/cicada/include/transaction.hh:247-256`、`patches/instr-cicada-trace.patch:68-101`。**放置すると、真の B/U/P site が評価に見えず certified に届かないか、`.cc` に置いた飾り emitter だけで受理してしまう。** header を source snapshot と hash の閉包に含め、site ごとの実装と call path を評価する設計を先に決める。`.cc` の薄い wrapper だけで「在る」と判定しない。

- **A7｜should｜brief P2・P7、plan §5。** 提案された B の強制回収は実際の body 使用前に UAF・異常終了し得る。U の「公開を飛ばす」は後続 reader を pending 待機で止め得る。P の「sort 後に落とす」は P の比較**後**に置けば対象面を発火させない。根拠: `plan.md:48-55`、`external/ccbench/cc/cicada/transaction.cc:108-117,687-720`、`external/ccbench/cc/cicada/include/transaction.hh:253-256`。**放置すると、壊し試験の失敗を証拠面の検出力と誤認し、実装費用も過小評価する。** B は退役イベントが実際の B カウンタへ届く最小列、U は後続待機を避ける単一取引と status 変異、P は比較の内側での要素破壊を使い、対象カウンタの増加を直接確認する。

- **A8｜should｜brief P6・P7、plan §2・§6。** parser は未知 tag を拒否するため、H/V に加え診断用 J/K/L/N を出すなら両 parser の受理・検査も必要である。さらに現状は Cicada が proof-surface 対象外、campaign の source allowlist 外、floor baseline 外である。根拠: `orchestrator/verifier/parse.py:335-355`、`orchestrator/verifier/model.py:37,501-519`、`orchestrator/campaign/source_digest.py:85-100`、`orchestrator/campaign/genome.py:172-188`、`orchestrator/campaign/between_run_floor.py:59-85`、`orchestrator/campaign/pipeline.py:731-743,2117-2118`。**放置すると設計を「実装済み」と数えても campaign に trace を供給できず、また既存 Silo/MOCC/SI の受理集合を誤って変える。** 実装案の完了条件に、CCBench patch、通常・compact parser、Integrity、Cicada 専用 ProofSurfaceAssessment と protocol 登録、fixture・凍結 baseline、source binding、genome の許可設定、campaign と BASELINES の接続を列挙する。診断 tag を実装しない初期版では出力もしない。

## brief / plan で正しいと確認した点

- 現行 certified の主要な連言は、非空履歴、非巡回、integrity clean、commit witness、X/P の文面証拠で、I emitter の存在は連言外。Cicada は対象 protocol 外である。根拠: `orchestrator/verifier/model.py:37,77-82,501-519,554-572`。
- 既存 Cicada patch は読んだ wts を保存するが、不一致は stderr の件数であり判定へ入らない。Version 構造体にも触れない。根拠: `patches/instr-cicada-trace.patch:8-25,35-44,68-89`。
- `REUSE_VERSION=1/0`、inline 版の返却・再取得、`gc_versions()` の detach、`gc_records()` の delete を分ける必要がある。根拠: `external/ccbench/cc/cicada/include/transaction.hh:173-245`、`external/ccbench/cc/cicada/transaction.cc:806-855`。
- 読み可視区間や rts 順序の診断は forwarding＋GC の原因帰属に有用である。ただし忠実な履歴の 1SR を判定するだけなら、機構内部の全順序を個別に再証明することとは区別できる。根拠: `external/ccbench/cc/cicada/transaction.cc:543-593`、`orchestrator/verifier/dsg.py:752-785`。

## 推奨への意見

**中間案を推す。** B・U・P の実装価値は高いが、現 plan のまま certified へ昇格する推奨には同意しない。まず A1・A2・A5・A6 を設計の必須条件に直し、YCSB の一設定で正例と独立した壊しを成立させる。その費用を示してから実装判断を求める。成立前の論文表現は「観測 trace で巡回を検出しなかった、判定は indeterminate」に留める。

## 総括

親 brief の P1 は**物理設置時刻順を必須にしない**という限定では妥当だが、版の網羅、reads-from、終状態まで自動的に保証する根拠にはならない。最大の修正点は、B の body 使用区間と U の**公開版から W 行への逆向きの被覆**である。これらを閉じずに B・U・P の名前と H の件数だけで certified を許すと、実際に巡回する実行を受理し得る。