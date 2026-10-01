## 判定

**NO-GO。** commit `068f664dd` の測定値・正しさ記録は一次資料と一致する。ただし、測定への影響を否定する断定と「約2.2 node 時間」の試算は修正が必要。

## 所見

| ID | 重大度 | 根拠・問題 | 提案 |
|---|---|---|---|
| A-F1 | **must-fix** | [README L60・§7](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:60) の「測定値の汚染は無い」「延びたのは wall と確保 node 時間だけ」は観測を超える。lock 所有者は未観測で、`rounds=1`・競合 probe 通過・stock の `settled=true` は影響皆無の証明ではない。[pipeline L2764](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/orchestrator/campaign/pipeline.py:2764) 自体も lock が捕捉しない競合を明記している。結論・節題の原因断定も、本文の「時刻からの推定」より強い。 | 「時刻は R2 の直列化と整合する」「既存 probe による競合検出はなく、通常の受理条件を満たした」に限定する。測定値への影響皆無は断定しない。 |
| A-F2 | **must-fix** | [README L202](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:202) の「原 attempt と同じ1 job あたりの所要なら約2.2 node 時間」は計算が合わない。原会計は `(386+841+1218)×5/3600 = 3.395833…`。待ち時間を除いた試算なら、除いた区間・workload 別所要・計算式が示されていない。 | 2.2 を削除するか、待ち時間の推定と実測時間を区別した計算式を示す。別 wave の予算根拠には、そのまま転用しない。 |
| A-F3 | should-fix | [README L203](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:203) は rep の兄弟 node 配布を改善案とするが、[pipeline L2649](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/orchestrator/campaign/pipeline.py:2649) で既に兄弟4本と head の rep0 を並行実行している。「1本5分」の根拠も示されていない。 | 既存の rep 並列化と、新たな cell／workload の job 分割を区別する。5分は未検証の目標として書くか削除する。 |
| A-F4 | should-fix | [wrapper L157](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/tools/t2853_r2_fig10_plot.py:157) の caption 置換2は、protocol の連言と負の rr95 による説明を原 attempt だけに帰属させる。R2 も同じ protocol で全 cell が通り、rr95 の effect が負なので、同じ説明が成立する。明示的な虚偽ではないが、R2 の status の意味を弱めており、単なる地位語置換という説明にも収まらない。 | R2 自身について「3 workload の連言で、負の read-heavy effect により reject」と説明する。 |
| A-F5 | should-fix | [段4裁定 L10](/home/SFC/tanab/.claude/jobs/24a01078/wave/s4-ruling.md:10) は README hash 問題を記述で処置している。しかし provenance の `70c11b46…` に対し対象 commit の README は `f35f797c…`。[wrapper L134](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/tools/t2853_r2_fig10_plot.py:134) は現行 README を再 hash し、生成器 L443–445 は一致を要求するため、既存 provenance の閉包は現行 tree では成立しない。歴史的 hash の説明だけでは再検査手順にならない。 | 検査時に参照する投入前 README の snapshot／commit と復元手順を明示する。描画時の検査成功と、現行 tree での再検査可能性を区別する。 |

## 確かめたこと

- **数値：** 原 attempt・R2 の全12 cellについて、raw の5標本から中央値、平均、`t₀.₉₇₅,₄ × 標本標準偏差 / √5` を再計算。README・対照表と一致し、R2 provenance・`artist_series` とも一致した。
- **効果・判定：** R2 は rr5 `+0.6239734604583511`、rr50 `+0.1389998460596873`、rr95 `−0.11449452408913763`。pin された floor による厳密な `< −floor` 判定は順に no-regression／no-regression／regression。`r2-record.json` と一致。両 attempt の outer status `reject` も protocol と整合する。
- **正しさ境界：** R2 の6 cell、計36件の correctness 記録はすべて trace 有効・certified・pass・serializable。binary／build identity が対応し、性能は別の trace 無効 binary、`CCBENCH_TRACE=0`。WAL の必要 field でも36件すべて `anomalies=0`、abort stage なし。
- **会計：** R2 の NQSV Elapse は `1531 / 1527 / 1541 s`、各5 node。合計 **22,995 node 秒＝6.3875 node 時間**。全 request の `driver_rc=0`、pin `6810666`。原 attempt は **3.395833… node 時間**。
- **事前固定・凍結：** §0 の commit 時刻は **10:28:52 JST**、`submit_start` は **10:29:38 JST**。46秒前に固定され、`e92aeea8f..068f664dd` は追記のみ。指定された原成果物・結果稿・既存 fig10・生成器・policy・driver は `5f9e8c549..068f664dd` で不変。
- **wrapper・hash：** 期待 certification／manifest hash と判定は record から読み、入力から自己生成していない。測定値の受理検査・レイアウト検査を外す変更はない。collect 成果物10件、record、図、表、wrapper の記載 hash は一致。原図の陽性対照は `artist_series`・caption・`tracked_inputs` が既存 provenance と一致した。
- **bench lock：** bench と性能検証の fanout・完了待ちは同じ `bench_lock()` 内。既定 path は `~/.izanagi/bench.lock`、job body は `IZANAGI_BENCH_LOCK` を設定しない。記載された空き時間は WAL から再計算して一致。rr95 検証完了→rr5 bench 開始は2巡で **0.0212秒／0.0185秒**。直列化の推定と整合する。
- **原 attempt の重なり：** request 表は会計と一致。rr50・rr95 の重なりは **9分58秒**で、「約10分」は正しい。
- **親 brief：** P1・P2 の期待値分離は実装でも維持されている。記録ファイル名等の変更は段4裁定で説明されている。

## 確かめていないこと

- 保存されていない trace の再判定、実行時 correctness argv の独立観測。
- node 上の lock 所有 PID、実効 lock path／共有 filesystem の実測、全競合の連続観測。
- 費用超過の継続承認について、段4裁定等の記録を超える連絡原文。
- 描画・閉包検査・負例・受入テストの再実行。今回は静的照合のみで、編集・commit・テスト・子 agent 起動は行っていない。

## 総括

測定結果と図の数値を崩す不一致、anomaly を通した証拠、期待値の自己照合は見つからなかった。**修正必須なのは、観測を超えた汚染否定と根拠不明の費用試算である。** これらを直し、推定・実測・再検査可能性の境界を揃えてから GO とする。