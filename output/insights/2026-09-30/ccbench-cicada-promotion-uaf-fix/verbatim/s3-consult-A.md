## 所見 — 原因の仮説

- **must-fix｜P1 はコード上成立する。** [read_internal()](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/transaction.cc:92) は読み取り専用 tx の `rts_` で版を選び、最初に飛ばした版を `later_ver_` に保存する（同ファイル:102–126）。[validation()](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/transaction.cc:543) はそのポインタから再検査する。例えば `rts=10, wts=30` で `L(15, aborted) → V(5, committed)` を読み `V` を記録した後、別 tx が `B(25, committed)` を先頭に置く。promotion の RMW が `A(30)` を先頭に設置すると、鎖は `A→B→L→V` になる。再検査は `L→V` だけを見て通る。`B.rts≤30` なら write set 検査も止めない（同ファイル:576–592）。放置すると修理 commit が実在する読み取り不整合を残し、巡回 0 の一般化も誤る。読み取り専用から転換した読みを `wts` 時点の最新版から検査するか、読み取り専用 tx の promotion 自体を抑止する。

- **should｜P1 の成立条件を絞る。** `later_ver_` がない場合は最新版から検査する。`later_ver_` 自体が `wts` 未満の確定版なら通常はそこで不一致になる。上のすり抜けには、`later_ver_` が aborted、または pending から aborted となり、その**手前**に `wts` 未満の確定版が加わる条件が要る（transaction.cc:545–566）。`REUSE_VERSION=1` の再利用を、この反例の必要条件とする根拠はない。保持中の `later_ver_` の解放・再利用まで主張するには、`MinRts` と回収の別の破れを示す必要がある（[gcAfterThisVersion()](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/transaction.hh:173)、transaction.cc:831–838）。放置すると診断結果を誤帰属する。診断ではポインタの状態遷移と、飛ばされた確定版を分けて記録する。前 wave 相談 A の「途中に確定版が入れば不一致」は、この鎖では誤りである（[相談 A:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/s3-consult-A.md:9)）。

- **should｜P1 だけで K 4 件・R 327 件を説明し切れない。** その件数は一つの promotion 設定の観測であり、P1 の発火件数も witness との対応も未測定である（[前 wave §4.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/README.md:82)）。`rts` 読みと `wts` 書込みの混在は、転換前の**全読取**を正しく再検査しなければ別の巡回経路になる。一方、後続 `update()` の素通りは実在する値の欠落だが、それ単独を巡回の原因とは断定できない（transaction.cc:205）。early abort は `Status::OK` を返すが、提示済みの YCSB・TPC-C ループは `status_` を調べるため、直ちに aborted tx の commit とは言えない（transaction.cc:253–261,291–297、[相談 A:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/output/insights/2026-09-29/ccbench-cicada-bugfix/verbatim/s3-consult-A.md:7)）。放置すると原因未確定のまま修理と記録を確定してしまう。plan の witness 照合で各経路を帰属させる。

## 所見 — 修理案の安全性

- **should｜読み取り専用 tx の promotion 抑止は、安全側の最小修理として妥当。** 原論文 §3.1 の固定 `rts` snapshot・read set 無検証に戻る（[原論文抜粋:5–14](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/cicada-paper-excerpt.txt:5)）。ただし §3.3 の「読んだ非 inline 版を同じ値で RMW 化」は、読み取り専用 workload では発火しなくなる（同:41–49）。放置時の成果物リスクは、この変更を「promotion 機能全体の修理」と記すこと。読み書き tx での promotion は残ると明記し、その経路の witness と後続 update を確認する。[plan:25](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:25) の性能方向は予測のまま扱う。

- **should｜最新版からの再検査は転換前の読取に限定する。** [plan:26](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:26) の限定なら、既存の通常の読み書き tx の走査起点・受理集合を変更しない。全 read set に一律適用すると通常の読み書き tx にも走査費用が増え、同時更新との判定時点を変え得る。放置すると「非既定 promotion 経路だけの修理」という commit の説明が崩れる。転換前の要素を識別し、`wts` で見える版と記録版を比較する。原論文 §3.4 の timestamp 時点の検証にも合う（原論文抜粋:56–65）。

- **must-fix｜後続 `update()` の素通りは値を失わせる。** promotion が `update()` で RMW を write set に積むと、同じキーへの本来の `update()` は body を使わず成功を返す（[transaction.hh:201–211](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/transaction.hh:201)、transaction.cc:205）。放置すると修理後 commit の「書いた値」と実値が食い違い、版だけの trace と巡回 0 では発見できない。[plan:27](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:27) の promotion 由来要素だけを本来の body で置換する方針は妥当だが、既存 write の一般処理に拡げず、値を使う確認を要する。

## 所見 — UAF

- **must-fix｜P3 の順序変更は報告済み UAF を消すが、並行読み手の寿命を解決しない。** 現行は INSERT tuple を削除してから `writeSetClean()` が `continuing_commit_` と install 済み版の status に書く（[transaction.cc:745–755](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/transaction.cc:745)、[transaction.hh:343–367](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/transaction.hh:343)）。順序を直しても、他 thread が `get_value()` で tuple pointer を取得した直後なら、索引から外した後も `read_internal()` がその tuple を参照できる（[masstree_wrapper.hh:182–186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/external/ccbench/include/masstree_wrapper.hh:182)、transaction.cc:170–177）。放置すると修理 commit に別の UAF が残り、ASan 0 件の記録を一般化できない。削除対象を退避して clean した後も、既存読者が離れるまで tuple と inline 版の解放を遅延させる寿命処理が必要。

- **should｜四組合せの結果を区別する。** `INLINE_VERSION_OPT=1` では INSERT の `new_ver_` は tuple 内にあり、順序変更で clean 自身の直接 UAF は消えるが、早い tuple 解放は読者に危険である（[transaction.hh:217–225](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/transaction.hh:217)）。`OPT=0` では版は別確保で、tuple を消しても install 済み aborted 版は解放されない。`REUSE_VERSION=0/1` のいずれも、INSERT は `finish_version_install_=true` なので clean の reuse・delete 分岐へ入らない（[cicada_op_element.hh:44–50](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-G/cc/cicada/include/cicada_op_element.hh:44)、transaction.hh:346–364）。放置すると漏れと UAF の両方を「ASan が静か」で閉じてしまう。既存の未回収を明記し、再利用は読者の退避後に限る。INSERT を `writeSetClean()` で単純に飛ばす案は status を pending のまま残すため採れない。

## 所見 — 確認と正例の射程

- **must-fix｜小走行の巡回 0 と ASan 0 件を修理の証明にしない。** [plan:42](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:42) は観測した履歴・実行だけを判定する。TPC-C の完走は例外の非再現、ASan 0 件はその走行での非検出であり、値の一致、全スケジュール、四つの macro 組合せの寿命を保証しない。放置すると一次資料の結論が実測を超える。「巡回 0、上限 indeterminate」、完走率、ASan の対象組合せをそのまま記す。anomaly が出た variant は引き続き失格とする（[common.txt:30–33](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/common.txt:30)）。

- **should｜壊し patch の帰属条件は、巡回 witness との対応まで必要。** [plan:44](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:44) の修理箇所だけを戻しても、他の precheck が先に abort すれば巡回は出ない。逆に別経路の巡回を同じ走行で拾えば「promotion の誤りを単一理由で検出」とは言えない。放置すると正例の記録が誤る。壊した条件を通って commit した tx の key・版を、判定器の `rw` witness と照合する（[report.py:147–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix/orchestrator/verifier/report.py:147)）。ただし DSG trace は値を記録しないので、後続 update の値欠落を狙う壊しの正例にはならない。

- **should｜`#error` を外した trace は診断変種として有用だが、W 行の意味を限定する。** patch は read set の記録版を R 行へ、write set の版を W 行へ出し、commit 前に呼ぶ（[instr-cicada-trace.patch:68–96](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/instr-cicada-trace.patch:68)、同:107–129）。promotion 成功後の RMW は W 行に載るが、W 行だけで promotion 由来か本来の update かは区別できず、値の正しさも見ない。放置すると診断変種の結果を標準計装の保証や性能値として記す誤りになる。`#error` 除去を明記し、C 行・R/W 行数・`READ_WTS_MISMATCH` と witness を照合する。TRACE や診断計器付きの throughput を性能値に使わない（[common.txt:23–33](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/common.txt:23)）。

## (P1)〜(P5) と plan への意見

| 項目 | 意見 |
|---|---|
| P1 | **成立。ただし原因帰属は未確定。** aborted `later_ver_` の手前に入った確定版が具体的な穴。前 wave 相談 A の一般化は誤り。 |
| P2 | `bad_alloc` の三候補は未帰属。後続 update の値欠落は静的に確定するが、例外原因とは別に扱う（[brief:12](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/s1-brief.md:12)、[plan:6](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:6)）。 |
| P3 | clean 後に delete する案は直接 UAF の修理として必要。ただし並行読者から見た tuple の解放時点が未解決。 |
| P4 | G と gc 修理の merge 方針に静的な異議はない。gc 差分は scan と `gc_records()` に限られる（[F-to-gcfix.diff:5–31](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/verbatim/ccbench-gcfix/F-to-gcfix.diff:5)）。実 merge の結果はここでは未確認。 |
| P5 | D297 の拒否を pass と呼ばず、非 Cicada path の引継ぎを推論とする [plan:9](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/out/s2-plan.md:9) は妥当。 |

## 総括

最優先は、P1 を具体的な版鎖と巡回 witness に帰属させること、そして P3 の tuple 解放を並行読者に対して安全にすることです。plan の小走行は必要な観測ですが、この二点の静的な穴を埋める代わりにはなりません。ファイル編集・build・テストは行っていません。