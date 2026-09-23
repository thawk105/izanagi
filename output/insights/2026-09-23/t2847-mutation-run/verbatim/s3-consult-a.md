## 所見

**F01 — must-fix — 発火印を判定材料に使うには保存と意味の定義が足りない。** [s2_verify_calibration.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s2_verify_calibration.py:162) は stderr を捕捉するが、正常終了時の返却値には入れない（同 :180–196）。`T2847_FIRED` を出すだけでは成果物に残らない。さらに、枝に入った取引が後で abort すれば、変異は commit 履歴へ現れない。**提案:** 起動器で stderr を保存し、「枝到達」と「変異を含む取引の commit」を別の証拠として記録する。stderr 出力は共有 flag を一度だけ立ててから行い、lock 保持中や payload 複写と TID 再読の間に置かない。trace 有効時だけコンパイルする契約は [CLAUDE.md「絶対規律」1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/CLAUDE.md:50) に適合するが、`#if <変異マクロ>` だけでは性能 build への混入を防げない。

**F02 — must-fix — V21 の発火後は「最後の成功取引」だが、書込み自体も失われる。** [transaction.cc:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:706) で `writePhase()` を省くと C/R/W/E と tuple 更新が全て省かれる。一方、YCSB は `commit()` が true なら [ycsb.hh:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/include/ycsb.hh:166) で `local_commit_counts_` を増やす。`quit` は [runner.hh:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/common/runner.hh:298) で立ち、1 thread の worker は現取引から戻った後 [runner.hh:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/common/runner.hh:192) で終了するため、発火すれば trace の末尾欠落になる。ただし write set がある場合、取得済み lock も解放されない。**提案:** 「証人あり I／なし S」は *非空の先行 prefix と、追加の構造違反がない場合* に限定し、発火取引が read-only か write を持つかを記録する。V21 を純粋な trace emitter 欠落と呼ばない。

**F03 — must-fix — V20 の「未使用版」は具体値を固定しないと orphan の帰属が崩れる。** C と W は [transaction.cc:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:602)、公開 tuple は同 :660、次の R は同 :606–609 の `read_set_` 由来である。公開版が別取引の W と衝突すれば orphan ではなく誤った producer に結びつく。`maxtid` は後続の INSERT/DELETE 枝で `absent` bit も変える（同 :663–685）。**提案:** YCSB の UPDATE のみを対象に、lock=0・latest=1・absent=0、genesis より大きく、C/W に現れない版を事前固定する。1 thread の「その key を次取引で読む」証人を保存し、`orphan_reads` と `write_version_mismatch` を個別に確認する。静的に orphan の確定まではできない。

**F04 — must-fix — V26/V27 の「枝到達」は値の破壊を証明しない。** V26 は [transaction.cc:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:211) の read set 優先のため、*先に一度も読んでいない key への blind write → 同 key read* でだけ対象枝へ届く。V27 は同 :529 が二度目の update を元々捨てる。`rratio=0`・10 操作は再選択を可能にするだけで、異なる値の二度目の書込みを保証しない。[ycsb.hh:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/include/ycsb.hh:128) の WRITE は新しい payload を作るが、その値の違いを workload は検証しない。**提案:** V26 は read set 不在と返却 bytes が write buffer と異なること、V27 は二度目の入力と最終 buffer が異なることを診断する。単なる `searchWriteSet` hit を「盲点 certified」の証拠にしない。

**F05 — should — V18/V35 の有効枝実行と TID 規則違反は別である。** `max_wset_` は lock した既存版（[transaction.cc:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:191)）、`max_rset_` は validation した読取版（同 :474）。両者を一方だけにしても [transaction.cc:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:572) の worker TID と epoch との最大化が差を覆いうる。V18 の版逆転・重複、V35 の「読んだ版より小さい commit」は表の flag だけからは導けない。**提案:** 変異後 `maxtid` と元の計算値を比較し、さらに対象 write/read の版との大小を記録する。V35 の S は予測であり、発火した規則違反を伴う certified と未発生 S を分ける。

**F06 — should — V22 の stderr を TID 再読の直前に入れると対象 race を変える。** payload 複写は [transaction.cc:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:263)、再読は同 :270–277。`fprintf` をこの間に置くと競合 window が拡大する。再読差が lock bit だけでも「値と版の不整合」にはならず、その後の abort もありうる。**提案:** 差の判定・印は二度目の TID 取得後に置き、epoch/tid が違う場合を別計数する。certified の主張には、該当 read が commit したことまで追う。

**F07 — should — 対照の S 判定だけでは誤検出と未到達を分けられない。** [s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:63) の stock は同 flag の健全性確認として有効。ただし V24 は YCSB に scan/insert がなく（[ycsb.hh:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/include/ycsb.hh:121)）、S は未到達である。V32 の 1 thread は逆順 sort の発火は見られても、複数 worker 共通の順序という安全根拠までは実測しない。**提案:** 各対照の印と非空 commit を保存する。stock が N/I ならその workload の変異 verdict を帰属不能として扱う。V24 の機構評価には scan と並行 insert を含む workload が要る。

**F08 — should — gate 登録は受理領域を実際に広げる。** [condition_meaning_gate.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/condition_meaning_gate.py:271) の `SUPPLY_DOMAIN_MACROS` は `_DEFINE_SPECS` から作られ、同 :956–982 の `make_define_request` と CLI の同 :4431 で新マクロが選択可能になる。したがって「既存の受理条件を広げない」という [s2-plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:31) の文言は厳密には誤り。**提案:** 判定基準と patch 束縛は緩めず、*許可ドメインへの14マクロ追加* と明記する。通常の variant/baseline 経路からこれらを選ばないことを起動側で確認する。`-D<macro>=1` は [s2_verify_calibration.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s2_verify_calibration.py:308) の破壊実験 build に限定する。

**F09 — should — P1 と P5 は概ね妥当だが、P5 の「source 上の誤り」例外は狭く記録すべき。** mocc V25/V34 は計装なしでは期待する S 側の検証ができず、si V28/V29 は現 parser が旧形式を E にするため、今回の検出表から外す判断を支持する（[s2-plan.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:1)、[設計書 §4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/output/insights/2026-09-22/t2847-verifier-detection-design/README.md:210)）。V25 の停止は計装なしでも観測可能、という限定は残す。P5 による修正時は初回結果、誤りの source 根拠、修正後の別 run を分離し、期待表そのものを遡及変更しない。

## patch ごとの発火条件

| V | 最初に「挙動が変わった」と言える条件と確認先 |
|---|---|
| 17 | read set の `check.lock` が真、同 key が write set に無く、版一致検査は通過。[transaction.cc:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:453)・:466。X は write lock 被覆を検査するため、この変更単独では必然でない（同 :624–633）。commit と巡回は別途確認。 |
| 18 | `max_wset_` を外した結果、最終 `maxtid` が元計算と異なる。版逆転または同 key の重複はさらに別条件。[transaction.cc:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:567)・:572–582。 |
| 19 | 固定版が元の `maxtid` と異なる取引が commit。I は同 key の別取引 W と版が重複したとき。[transaction.cc:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:579)・:615。固定値は genesis・lock/latest/absent bit を保護する。 |
| 20 | UPDATE の tuple に C/W と異なる版を実際に公開。orphan には次の commit 取引がその版を R に記録し、同版の W が無いことが必要。[transaction.cc:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:660)・:606–616。 |
| 21 | validation 成功後に `quit_` が真で `writePhase()` を省き、`commit()` が true。1 thread なら後続取引なし。証人差は [ycsb.hh:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/include/ycsb.hh:161)・:166–167。 |
| 22 | payload 複写後の二度目の TID が最初と異なり、古い payload と新 TID を read set に置く。版差を別確認し、その取引の commit を追う。[transaction.cc:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:263)・:269–277。 |
| 23 | 非空 UPDATE payload の公開 bytes が write buffer と実際に異なる。[transaction.cc:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:658)。1 thread、1 write で届く。 |
| 24 | `node_map_` が非空で、node 版不一致を本来なら拒否する時。[transaction.cc:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:477)。計画の YCSB 行では発火しない。 |
| 26 | read set に無く write set に同 key があり、返す旧 tuple payload と write buffer が異なる。[transaction.cc:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:211)・:216–219。 |
| 27 | 同 key の二度目の `update()` に入り、その入力に対する buffer 処理が元コードの「無視」と異なる。[transaction.cc:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:529)。値の違いと commit を別確認。 |
| 35 | `max_rset_` を外した結果、最終 `maxtid` が元計算と異なる。規則違反には `maxtid` が実際に読んだ版以下となることが必要。[transaction.cc:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:567)・:572–582。 |
| 31 | `BACK_OFF` 有効で `abort()` の backoff 枝を通り、二度目の待機を実行。[transaction.cc:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:42)・:47。 |
| 32 | write set に異なる二 key 以上があり、逆順 sort が元順と異なる並びを作る。[transaction.cc:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:408)。 |
| 33 | 事前固定した入力条件に一致し、lock 前に abort する。その条件に一致しない取引の commit も必要。[transaction.cc:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:383)・:437。 |

## 未確認点

- patch 本体はまだ無いため、各有効枝の具体的な bit 操作、未定義時の pin 一致、発火印の保存経路は実証できない。
- V19 の固定版、V20 の公開版の具体値と epoch をまたぐ衝突可能性は実装後に再検査が必要。
- V17/V18/V22/V35 の N・I・S は schedule と完走履歴に依存する。静的検査は期待 verdict の可能性までで、発生の証明ではない。
- V24 の phantom と V25 の停止の verifier 層は、今回の YCSB 14 本では検証されない。

## 総括

14 patch は pin `e9e477ca` の変更点に対応するが、**枝到達、値や版の実際の変化、commit 履歴への残存を分けて記録すること**が必要です。特に V20、V21、V26、V27 を現在の計画の印だけで「期待層で検出」または「盲点として certified」と判定すると、未発生を取り違えるおそれがあります。静的検査のみで、build・実走は行っていません。