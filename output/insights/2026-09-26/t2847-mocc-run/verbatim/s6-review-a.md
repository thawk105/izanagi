## 所見

| ID・重大度 | 位置 | 根拠と提案 |
|---|---|---|
| F1・**must-fix** | [s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/s4-ruling.md) R4 | R4 の「一意な 8 状態」に正常な stock の非空 S が入らない。また V34 は `changed=0` が定義なので、述語を実際に評価した全 cell まで字義上「未発生」になる。分類契約に「対照正常」を追加し、V34 の到達は site 別 counter で表すべき。現行 R4 のまま「全 46 cell に 8 状態の一つが付いた」と報告するのは不正確。 |
| F2・**should** | [V25 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-skip-canonical-restore.patch:57)、[pin C transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:721) | gate は R2 の四条件を満たす。`upgrade` は CLL_ の read lock を write lock へ昇格する場合の値。CLL_ は走査前に sort され、保持 suffix は `key >= tuple`。RLL_ 再取得との照合を suffix に限っても、この変更に起因する同一 lock の再取得・`unlockCLL()` の二重解放経路は見つからない。ただし停止原因は静的に確定できない。J3 の 3 cell は「同 job の stock は約 1 秒で完走、変異 build は 120 秒で停止。診断欠落。相互待ち・自己待ちの原因未確定」と記録する。 |
| F3・**should** | [V34 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/control-mocc-negated-temperature-predicate.patch:90)、[ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/include/ycsb.hh:55) | 4 site の `>=` と `!(<)` は unsigned 温度と閾値で等価。297 の `else if`、971 の `||` の短絡位置も維持される。W は `rratio=0, rmw=true, max_ope=5` により READ_MODIFY_WRITE のみを生成し、delete は呼ばない。read した tuple は write set にも入り、`construct_RLL()` は重複した read 要素を飛ばすため、site567・971 は全 cell で 0。対照が示すのは**評価された 297・460 の等価性と verifier の正常判定**であり、567・971 の実行時等価性ではない。 |
| F4・**nit** | [V25 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-skip-canonical-restore.patch:43)、[V34 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/control-mocc-negated-temperature-predicate.patch:76) | flag は各 `begin()` でリセットされ、abort 後の retry も `begin()` を通る。`committed` は `validation()`・`writePhase()` 成功後に増えるため取引境界と整合する。V25 の `reached` は取引数でなく gate 評価回数。 |
| F5・**nit** | [launch_mocc_run.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/launch_mocc_run.py:121) | driver と flags、argv、cwd、trace env、120 秒 timeout、非ゼロ rc 時の verify 抑止、`_verify()` 呼び出しが一致。pin C checkout、clean 確認、所有 patch 適用、条件 gate も通る。4 JSON とも build 完了・例外 0、各 patch の touch set は `cc/mocc/transaction.cc`、変異 gate の supply／meaning は green、admission は true。stock は無 patch・無 macro。差分に baseline 混入や verifier 受理拡張は見つからない。 |

## 分類表

略記：**期待**＝期待した層で検出、**盲点**＝盲点として certified、**未発生**＝機構未到達、**発火不明**＝発火未確認の S、**停止**＝verdict なし。X／P は各 counter。全て同 job の stock 対照は非空 S、X/P・他 integrity は 0。

| build | hot t1 / t4 | cold t1 / t4 | default t1 / t4 |
|---|---|---|---|
| V13 L・W | 期待 X=1,072,230 / 期待 X=1,228,132、巡回679・version dup3,725 | 期待 X=1,877,685 / 期待 X=2,349,066、巡回3,471・dup19,591 | 期待 X=1,885,977 / 期待 X=2,368,502、巡回3,570・dup21,405 |
| V14 P・W | 期待 P=616,898、commit 8 / 期待 P=4,433、commit 183 | 期待 P=222,527 / 期待 P=236,948 | 期待 P=223,173 / 期待 P=230,295 |
| V15 E・W | 期待 X=1,310,422 / 期待 X=1,453,797、巡回3,393・dup16,006 | 期待 X=1,358,158 / 期待 X=1,448,105、巡回1,403・dup8,454 | 期待 X=1,370,868 / 期待 X=1,466,025、巡回1,430・dup8,866 |
| V16 H・U | 期待 X=2,055,633 / 期待 X=7,331,144、dup68,698 | 未発生 S、commit 1,055,656 / 未発生 S、commit 3,560,813 | 発火不明 S、commit 1,060,159 / 発火不明 S、commit 3,557,150 |
| V25 R・W | 盲点 S、`reached=1,304,770; changed=447,413; committed=177,188` / 停止 120.1秒・診断欠落 | — / 停止 120.1秒・診断欠落 | — / 停止 120.1秒・診断欠落 |
| V34 T・W | 対照正常 S、site297/460=839,305/839,305 / 対照正常 S、896,703/930,430 | 対照正常 S、892,763/892,763 / 対照正常 S、932,229/970,573 | 対照正常 S、893,668/893,668 / 対照正常 S、933,028/972,708 |

V14 の P は全て `size-changed`。V25 hot t1 の X/P・他 integrity は 0。V34 は全 6 cell で `changed=0`、site567/971=0、X/P・他 integrity=0。stock は J1 の W 6、J2 の W/U 12、J3 の W 4、J4 の W 6 の全 **28 run** が非空 S で、commit はそれぞれ 179,782–198,118、184,147–3,555,838、183,614–200,546、180,899–200,816。stock と V34 の「対照正常」は、現行 R4 の 8 状態に正式な名称がない。

## 未確認点

- 停止 3 件の待機関係。timeout では診断行も完全な trace も得られず、deadlock の種類は確定できない。
- V34 site567・971 の実行時評価。今回の W では両 site とも 0。
- 親が投入した焦点テスト・build の結果。本レビューでは再実行していない。

## 総括

**条件付き GO**。実装と計測帰属に規律 2 違反は見つからない。受入記録を確定する前に、R4 の正常対照の状態名と V34 の `changed=0` の扱いを修正し、停止原因を断定しない記述にする必要がある。