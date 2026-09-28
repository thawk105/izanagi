## 所見

- **F1｜must-fix｜brief P3・plan 5/総括。** 依頼は「検査器側の読み込みを実装する」「`orchestrator/verifier/` の変更とテスト」を成果物に指定する一方、plan は production code を変えない（`request-md_3.txt:18,25-27`、`plan.md:5,16,40`）。現行 parser は C/R/W/E を読め、DSG も protocol 分岐なしで巡回を作れる（`orchestrator/verifier/parse.py:355-429`、`dsg.py:752-785`）。**放置時:** Cicada の異常検出は示せても、依頼された実装成果物を満たしたという主張と実物が食い違う。**推奨:** 新しい読み込み分岐を形式的に足さず、既存経路を Cicada の実 trace とテストで検証できる事実を示し、この成果物指定の読み替えを親からユーザーへ裁定に回す。production 差分が必要なら、具体的な現行受理失敗を生死確認で特定してから、その一点だけ直す。`parse/dsg/model` は現行の campaign lock の source closure に含まれるため、変更時は束縛を更新し、既存 protocol の判定回帰を確認する（`orchestrator/campaign/campaign_lock.py:58-63`）。現時点で意味のある最小 production 差分は特定できない。

- **F2｜must-fix｜brief P3・plan 5/事前登録。** `cicada` の X/P/I は unavailable で、巡回なしでも `certified=false` となる（`orchestrator/verifier/model.py:37,77-82,245-247,510-519,555-572`）。**放置時:** stock の anomaly 0 を「正しさゲート通過」と記すと、後続 variant の受理集合を実際より広く見せる。**推奨:** 今回の成果を「Cicada の巡回検出経路と負例の確認」と明記する。certified を要するゲートへの採用は別の証拠面設計が必要であり、Cicada を protocol 名だけで認証対象に加えない。

- **F3｜must-fix｜brief P4・plan 4/事前登録。** 二つの候補は guard の除去後も early abort、precheck、write set 検査が残る（`external/ccbench/cc/cicada/transaction.cc:247-293,481-593`、`plan.md:15,26-29`）。さらに verifier が報告するのは SCC ごとの代表 cycle であり、発火した全 txn を列挙する仕組みではない（`orchestrator/verifier/dsg.py:935-955`）。**放置時:** `reached/changed/committed>0` と別の cycle を結び付け、変異が赤を生んだと誤認する。**推奨:** 各 patch の対照を同じ cell で走らせ、変更経路を通って commit した trace txid が、理由付き witness に実際に含まれることを確認する。出なければ候補を差し替える。依頼の「古い版を読んだまま commit させる」も代替候補として明示する（`request-md_3.txt:19-22`）。

- **F4｜should｜brief P2・plan 1/2。** 初期版を `(1,0)` に写すには、生成時の `initial_wts` の固定値が必要である（`external/ccbench/cc/cicada/include/tuple.hh:13-20,74-90`、`ycsb_cicada.cc:28-30`）。一方、Cicada の wts は取引開始時に割り当てる（`transaction.cc:34-43`）。**放置時:** 初期版を通常版と誤認すると orphan や欠落辺が生じ、また「C の版ID＝commit順」という一次資料の説明は実装とずれる。**推奨:** TRACE 専用の初期値伝達と genesis 写像は残す。版IDは「wts による版順」と説明し、実際の commit 時刻順とは呼ばない。read-only の早期 return 前と、書込みの `cpv()` 後・clear 前の emit も残す（`transaction.cc:895-913,934-947`）。これらを削ると履歴そのものが欠ける。

- **F5｜should｜brief P5・plan 3。** 内部 promotion は `INLINE_VERSION_OPT` の内側で、同値 body の write を作る（`external/ccbench/cc/cicada/include/transaction.hh:199-213`）。D1464 はこれを workload write と区別する裁定である（`ruling-D1464.md:1-8`）。**放置時:** promotion を有効にした trace を通常の W と扱えば、偽の依存辺で判定が変わる。**推奨:** `TRACE && INLINE_VERSION_OPT && INLINE_VERSION_PROMOTION` の局所 `#error` は残す価値がある。今回の固定条件が `SINGLE_EXEC=0`、`group_commit=0` なら、その二つの汎用拒否コードは削り、起動器の条件固定と未対応範囲の記録で足りる。条件を外した run を受理結果に混ぜない。

- **F6｜should｜plan 1/5/6。** v2 parser は C の宣言件数と R/W 実行数、E の有無を既に検査し、verifier には独立の commit 件数 witness がある（`orchestrator/verifier/parse.py:355-429`、`core.py:61-74`、`cli.py:48-49`）。**放置時:** emitter 内の二重件数照合や起動器独自の合計検査を必須にすると、同じ集合を数える検査が増えるだけで、欠落取引の受理集合は改善しない。**推奨:** C 件数は emit する set から書き、既存 parser と `--expected-commits` に benchmark counter を渡す。counter 照合は末尾欠落を捕まえるので残す（`external/ccbench/include/ycsb.hh:161-167`）。同じ set に由来する C 件数は独立した完全性証人とは主張しない（`output/insights/2026-09-26/t2847-si-run/README.md:29,90`）。

- **F7｜should｜brief P5/計算・plan 5/6/事前登録。** 既存テストは版の epoch 跨ぎと commit witness を扱う（`orchestrator/tests/test_verifier.py:1281-1296,2078-2108`）。依頼が求める命令列確認は明示的である（`request-md_3.txt:23`）。**放置時:** 32 bit 境界 fixture、任意の第5 fixture、全条件の焦点走、変異 matrix を必須化すると job と保守対象が増えるが、今回の判定・受理集合は変わらない。**推奨:** Cicada 固有の最小 fixture を genesis/read-only と理由付き G2 に絞り、古い snapshot と RMW は実走で判定が曖昧になった場合に追加する。TRACE=0 の命令列比較は残し、前処理比較は差分調査用にする。焦点走は witness が出ない場合だけ行う。既存コードを変えないなら mutation matrix は省く。

- **F8｜should｜brief P1・plan P1/未解決論点。** D16 の trace-hook の原則は `izanagi-trace` 枝で、一回限りの patch 例外は T-109 に限る（`ruling-D16.md:5-20`）。D579 は別タスクへの自動流用に再裁定を要すると明記する（`ruling-D579.md:11-15`）。si の out-of-tree 先例も、移送と pin 前進を人間判断として保留した記録である（`patches/README.md:794-814`）。**放置時:** patch を恒久配置として登録すると、D16 に反する参照先が一次資料に固定される。**推奨:** gitlink を動かさず、今回の試作・実走用 patch として `patches/README.md` に登録する。恒久配置だけを decisions fragment で裁定待ちとし、broken patch は D16 どおり patch に隔離する。README 登録と spool fragment は「必要なら」でなく成果物に明記する（`request-md_3.txt:25-31`）。

- **F9｜nit｜brief「親の実測」・plan「所有と波及」。** `IZANAGI_` 未登録検査は `patches/*.patch` 全件に及ぶので、診断文字列にも同語を入れない判断は正しい（`orchestrator/tests/test_p3_s4_loop.py:8682-8691`）。一方、brief の「bytes pin 0 件」は検索語と追跡対象に限られた陰性結果であり、「verifier の変更は束縛に波及」は source closure 掲載から分かる可能性の記述である（`s1-brief.md:14-15`、`campaign_lock.py:58-63`）。**放置時:** 限定的な検索結果を全経路の不存在証明として引用すると、一次資料の参照主張が過大になる。**推奨:** 検索式・対象を添えて「今回確認した範囲では」と書く。production verifier を変更しない今回の案に、束縛更新作業を先取りして足さない。

## brief / plan で正しいと確認した点

初期 wts は 0 ではなく、Cicada の read-only commit は writePhase を通らない（`external/ccbench/cc/cicada/include/tuple.hh:18-20`、`transaction.cc:934-947`）。`thid_` の数値 cast も必要である（`include/transaction.hh:58`、si 先例 `patches/instr-si-trace-v2.patch:13-17`）。`patches/ledger.json` の追記を避け、README に登録する判断、壊し patch を別 checkout に重ねる判断も妥当である。

計算は plan の固定分だけなら生死確認 1、本走 3、受入 1 の**約5 job**、焦点走が必要なら約6 job である（`plan.md:22-29`）。si 先例の生死確認・本走・焦点走は合計約392秒、変異 matrix の probe と final はさらに約1,636秒だった（`output/insights/2026-09-26/t2847-si-run/README.md:23,123`）。Cicada の build 時間は未実測だが、matrix を省いた案は2 node 時間未満という初期見積りとして妥当である。時間保証としては扱わず、投入前に実測で更新する。

## 総括

計画の核は、初期版の正確な写像、両 commit 経路での完全な v2 trace、stock 対照、発火した壊し取引に結び付く理由付き巡回、TRACE=0 の命令列確認である。現行 verifier はその trace を読める見込みだが、**異常検出が可能になることと certified な正しさゲートを通過することは別**である。production verifier の変更という依頼文との不一致は、無意味な差分を作る前に裁定を要する。実走結果はまだないため、二つの壊しが赤になることと2 node 時間内の完了は未確認である。