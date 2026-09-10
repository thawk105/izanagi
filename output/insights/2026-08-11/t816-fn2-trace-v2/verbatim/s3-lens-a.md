現プランのまま段 5 へ渡すべきではない。狭義の「C が残った R/W 接尾辞切断」は検出できるが、FN-2 閉鎖と TRACE=0 同一保証には blocker が残る。以下は read-only の静的レビュー結果であり、変更・build・test は行っていない。

### 1. [blocker] C の件数は独立 witness ではなく、同時欠落を自己整合させる

**根拠:** 件数と R/W 出力を同じ `read_set_` / `write_set_` から取る設計である [s2-plan.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:20)。現実装も C、R、W を同じコンテナから連続生成する [transaction.cc:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:584)。

具体例: API 成功後から `writePhase()` までに `write_set_` の一要素が失われると、`write_count` と W 行が同時に 1 減り、E も正常に出る。commit witness は C 件数しか照合しない [pipeline.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/pipeline.py:350)。これは既に「落とすほど速く、かつ certified」と実測され、独立な write-intent shadow だけが検出した事例である [T-152 insight:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/output/insights/2026-07-29_t152-write-intent-shadow.md:9)、[同:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/output/insights/2026-07-29_t152-write-intent-shadow.md:39)。read 側も同型の未解決 T-168 である [triage.md:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/output/insights/2026-08-03_task-inventory/triage.md:272)。

abort txn に C/E が無いこと自体は正常である。`writePhase()` は validation 成功時だけ呼ばれる [transaction.cc:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:693)。また read-only txn の `write_count=0` は正当なので、ゼロ件を一律拒否してはならない。`0/0 + E` は正当な空 txn と両集合消失を識別できない。

**成果物影響:** 欠落した R/W 辺によって `total_cycles` が非ゼロから 0、`certified` が false から true へ変わり、壊れた高速 variant が selected になりうる。

### 2. [blocker] 件数と E は内容置換・X 欠落・実行欠落を証明しない

**根拠:** プラン自身が、E が残った中間 X 欠落を検出できないと認めている [s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:34)。X は integrity を unclean にする認証信号である [model.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/model.py:111)。

残る具体形は三つある。

- 重要な R 一行が消え、別の R が重複すれば総数は一致する。現 parser は R を単に append し、txn 内重複を integrity 違反にしない [parse.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:117)。
- X 一行だけ消えて E が残れば、C の R/W 件数は無関係なので検出不能である。
- W は実データ更新より前に全件出力される [transaction.cc:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:601)。実際の `memcpy` / `storeRelease` は後段である [transaction.cc:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:630)。したがって E は write loop 終端到達を示すだけで、各 W の実行完了 witness ではない。

この形式で証明できるのは「C が保持した件数に対する R/W framing」であり、record 内容や実行との対応ではない。

**成果物影響:** X 欠落では `lock_coverage_violations` が 1 以上から 0 へ変わり、indeterminate が certified へ昇格する。

### 3. [blocker] d706650 からの新 branch は、承認済み T-152 を落とす分岐になる

**根拠:** プランは d706650 を直接親として新 commit を作る [s2-plan.md:134](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:134)。しかし write-intent shadow の `c9c1a9c` は実装済み・未統合であり [T-152 insight:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/output/insights/2026-07-29_t152-write-intent-shadow.md:3)、ユーザーは既にその新 pin を承認している [archived worklog:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/archive/worklog-phase3-0729-49-58.md:577)。

つまり新 FN-2 commit と c9c1a9c は sibling になり、後の単一 pin で双方を得られない。しかも T-152 は所見 1 の同時欠落を塞ぐ、まさに必要な独立 witness である。新 commit は c9c1a9c を含む系譜として構成するか、統合 SHA を改めて裁定対象にしなければならない。

**成果物影響:** c9c1a9c が脱落すると `write_intent_violations` が本来非ゼロの erase variant で 0 となり、台帳上閉じた穴が再び certified 選択へ戻る。

### 4. [blocker] include 行比較には「有効条件」がなく、TRACE=0 相違を緑にできる

**根拠:** `_cpp_normalize()` は全 `#include` を先に削除する [source_digest.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:320)。補助検査は include 行の文字列と順序だけを抽出し [source_digest.py:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:569)、プランもこれで死角を閉じるとしている [s2-plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:113)。

具体的な緑構成: 必須の `#include "include/transaction.hh"` 行そのものは変えず [transaction.cc:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/transaction.cc:7)、新側だけでその行を TRACE 有効時の条件内へ移す。include 列は同一で、include 削除後の TRACE=0 preprocess も同一になる。しかし実 TRACE=0 compilation では header が取り込まれず、旧 TU と異なるか compile 不能になる。TRACE は既知マクロなので未知マクロ検査も止めない。

直接・マクロ経由の `__has_include` は現 helper が明示拒否しており [source_digest.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:504)、そこ自体には別の fail-open は見つからない。ただしそれは include の条件付き活性を保証しない。

**成果物影響:** checker の `tu_identity=pass` が出たまま TRACE=0 binary が旧 pin と異なり、報告された throughput 全値が規律 1 の保証外になる。

### 5. [blocker] 一つの compiler での一致は、実 admission toolchain の一致ではない

**根拠:** preprocessing は compiler builtin を保持するため、結果は compiler/version 依存である [source_digest.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:323)。予約 builtin はその一 compiler の環境照会に存在すれば受理される [source_digest.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:403)。

具体的な緑構成: 新側の TRACE=0 差分を compiler major 条件のうち g++-11 では inactive、g++-12 では active な枝に置く。g++-11 checker は一致し、Pegasus compute の g++-12 build は異なる。実際、compute admission は site により system `g++` を選ぶ [buildcache.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:454)。

さらにプランは実走に g++-13 を要求する [s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:118) が、この環境には login/compute とも存在しない [pegasus-runbook.md:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/pegasus-runbook.md:619)。既存 real-build control もそのため skip する [test_s8b_oracle_driver.py:4154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_oracle_driver.py:4154)。

**成果物影響:** checker の compiler-specific `pass` が admission binary 全体の保証へ誤昇格し、同じ source/pin 表示の throughput と cache identity が実 toolchain ごとに異なる。

### 6. [must-fix] 8 genome は `-D` の値空間全体ではない

**根拠:** 8 genome が列挙するのは BACK_OFF、二つの no-wait、WAL だけである [genome.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/genome.py:74)。一方、CMake は ADD_ANALYSIS、KEY_SIZE、MASSTREE_USE、VAL_SIZE 等を全 target に供給し、command line override を正式に許している [Options.cmake:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cmake/Options.cmake:3)、[同:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cmake/Options.cmake:13)。

例えば既定 0 の非 genome option でだけ有効になる新コードは、全 8 genome で checker が緑でも、その option を 1 にした build では残る。「手動 `-D` は保証外」という文章 [s2-plan.md:114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:114) だけでは、その build が性能成果物へ入ることを機械的に禁止しない。

また `GLOBAL_VALUE_DEFINE` overlay は [source_digest.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:184) にあるが、これは workload TU の `ycsb_silo.cc` で定義される [ycsb_silo.cc:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/ycsb_silo.cc:3)。`transaction.cc` は別 source として compile される [CMakeLists.txt:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/silo/CMakeLists.txt:1) ため、この overlay は実在しない TU 文脈を検査して過剰拒否を起こしうる。

**成果物影響:** 非 genome option が admission へ混入すると `tu_identity=pass` のまま throughput が別 binary の値になり、逆に架空 overlay の差だけなら正しい pin の checker 結果が false になる。

### 7. [blocker] (P1) の P 行先例は同型ではなく、C schema を二重権威化する

**根拠:** D41 の P は既存 helper・既存同名 record がなく、txid 採番前にも出る独立タグだった [decisions.md:1305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/decisions.md:1305)。同時に parser/model/core/report の四層へ配線された [同:1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/decisions.md:1316)。

今回の C は既に v1 helper と schema 定義を持つ [trace.hh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:17)、[trace.hh:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/include/trace.hh:78)。SI もその helper を使う [si/transaction.cc:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/external/ccbench/cc/si/transaction.cc:526)。直接 stream 経路を足すと同じ C tag に二つの schema authority が残る。旧 helper 呼出しの消し忘れなら、同一 txn に v1/v2 C が二本出る。

さらに「real-build control」は `_run_trace` と verifier を mock しており [test_s8b_oracle_driver.py:4185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_oracle_driver.py:4185)、実際の C/E bytes、exactly-one C、件数、E 位置を一つも観測しない。P1 は実装手段として直ちに不可能ではないが、D41 を根拠とする正当化と現テスト計画は成立しない。

**成果物影響:** C 二重出力・混在時は `dup_txids` または `trace-parse-error` となり、対象 variant の fitness/certified 行が成果物から消える。

### 8. [blocker — 手順 4 開始条件] (P2) のまま v1 拒否すると SI を壊し、緩めると Silo FN-2 が残る

**根拠:** 現 parser は C を固定 5 field で unpack し [parse.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:101)、E は未知タグとして拒否する [parse.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/parse.py:173)。pipeline はその `ParseError` を `trace-parse-error` abort にする [pipeline.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/pipeline.py:1023)。verifier API に protocol/version 入力もない [core.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/verifier/core.py:19)。

層ごとの実効範囲は次のとおり。

| 層 | 本 wave 後の実効状態 |
|---|---|
| emit | local Silo だけ v2、SI は v1 |
| 形式権威 | `trace.hh` は v1 のまま、v2 は Silo 実装内だけ |
| parser / verifier | v2 を検証せず ParseError |
| campaign | v2 run を abort、fitness/certification なし |
| pin / 凍結成果物 | d706650 の v1 のまま |
| 現 certified 集合 | 既存 FN-2 characterization が false-green のまま [test_verifier.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_verifier.py:642) |

現 campaign 空間が Silo だけなのは事実 [genome.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/genome.py:87) だが、将来の全 protocol v1 拒否を正当化しない。手順 4 の前に「SI も v2 化するため編集面を広げる」「trusted protocol/version を verifier 入力へ束縛し Silo v1 だけ拒否する」「v1 拒否を延期し台帳を開いたままにする」の択一を裁定パッケージへ返す必要がある。

**成果物影響:** 無差別拒否なら SI の certified/fitness 行が全消滅し、arity だけで SI v1 を許せば旧 Silo v1 も受理され FN-2 の false-certified 行が残る。

### 9. [must-fix] 「gitlink 不変だから C++ 変更は inert」は一般には偽

**根拠:** プラン自身の real-build control は submodule working-tree の実 HEAD を取得して build する [test_s8b_oracle_driver.py:4163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_s8b_oracle_driver.py:4163)。`source_digest.compute()` も working-tree bytes を読む [source_digest.py:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:640)。test runner の入力 fingerprint は recursive submodule HEAD/status/diff を含む [run_tests.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/run_tests.py:1537)。通常 build は宣言 pin と実 HEAD の不一致を拒否する [buildcache.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/buildcache.py:1071)。

したがって正しい限定は「d706650 に復元した後の、committed gitlink を読む既存成果物は不変」である。新 HEAD checkout 中は build、digest、cache key、test fingerprint のいずれにも active である。

**成果物影響:** 新 HEAD 中の実行では `src_token`・cache key・受入 fingerprint または build の成否が変わり、「既存値不変」というレポート記載が偽になる。

### 10. [must-fix] raw diff 列挙が再帰的でなく、実 commit 対を検査できない

**根拠:** プラン記載は `git diff-tree --raw -z --no-renames` で `-r` がない [s2-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:101)。read-only で d706650 を含む既存 commit 対へ実行すると、この形は `cc/silo/transaction.cc` ではなく top-level tree `cc` の M だけを返した。`-r` を加えた場合に初めて対象ファイルが返った。

追加・削除・rename、missing object、empty diff を拒否する方針自体は妥当であり、明示された pass-on-empty 経路は見つからない。ただし記載コマンドをそのまま実装すると、正例が exact-path gate で必ず赤になる。

**成果物影響:** 実走 C の `tu_identity` が pass にならず、承認レポートと pin 前進が恒久的に未達になる。

### 11. [blocker] 変異の事前登録がなく、現状の前後層では「kill」が mask される

**根拠:** brief は変異台帳を成果物に要求する [brief.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/brief.md:47) が、段 2 plan の試験節には変異、期待 node、単一理由が一件もない [s2-plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:120)。DW-M01 は実装前登録と前後層による mask 排除を要求する [mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/dev-wave/mutation.md:5)。

特に以下は帰属不能になる。

- C/E emitter の欠落・重複は、現 parser が正常 v2 まで必ず拒否するため、pipeline 赤を emitter gate の kill と数えられない。
- real-build control は trace 実行を mock するため、emitter 変異が生存しても緑のままである。
- empty target、include 比較、preprocess failure の負例を「非ゼロ終了」だけで判定すると、狙った検査を消しても後段の別エラーで赤になりうる。これは F126 [failures.md:3493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/failures.md:3493) と F150 [failures.md:3939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/failures.md:3939) の同型である。
- 対象 0 件を明示負例にしなければ F9 の「対象不在を skip」型 [failures.md:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/failures.md:142)、compiler 不在を skip にすれば F209 型 [failures.md:5243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/failures.md:5243) になる。
- include の raw syntax を見るだけなのは、効果でなく書き方を検査した F199 型 [failures.md:5041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/docs/failures.md:5041) そのものである。

raw trace を parser から独立に観測する emitter control と、各 checker 段へ他条件を正常化した単一故障 fixture がなければ、変異台帳は証明にならない。

**成果物影響:** 台帳の mutation status が実際は SURVIVED/MASKED なのに KILLED と記録され、レポートが FN-2/規律 1 を機械保証済みと誤記する。

### 12. [nit] コメント差まで「byte 同一」と呼ぶのは過剰表現

**根拠:** `_cpp_normalize()` は preprocessing によりコメントを除去し [source_digest.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/source_digest.py:320)、プランはその出力 bytes を比較する [s2-plan.md:106](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:106)。したがって純粋なコメントだけの差は緑になる。

同一 compiler/flags の実行コードという規律 1 の目的には通常問題ないが、「source bytes 同一」「全 preprocessing 入力同一」ではなく「選定 context における normalized preprocessor output 同一」と報告すべきである。

**成果物影響:** certified/throughput 値は変わらないが、レポートの保証種別が literal byte identity から normalized-output identity へ訂正される。

## 総括

blocker は、(1) 同一コンテナ由来件数の共倒れ、(2) X・内容・実行欠落の非被覆、(3) 承認済み c9c1a9c を外す分岐、(4) 条件付き include の false-green、(5) compiler 間 false-green と g++-13 不在、(7) C schema 二重権威と emitter 実測欠落、(8) protocol 無差別 v1 拒否、(11) 変異帰属不在である。

**(P1): 反対。** P は新規独立タグで verifier 四層まで同時実装されたが、C は既存 helper・既存 schema・SI consumer を持つ。同型ではなく、直接 stream を採るなら少なくとも単一 schema authority と raw-output control が別途必要である。

**(P2): 本 wave の編集スコープとしてのみ条件付き賛成、手順 4 の前提としては反対。** SI を今触らないことは許容できるが、global v1 rejection は禁止し、上記三択を裁定パッケージへ返すまで手順 4 を hard-block すべきである。現 wave の正しい台帳状態は「FN-2 closed」ではなく「Silo v2 emitter/checker staged, not integrated」である。