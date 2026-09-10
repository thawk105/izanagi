## 所見

1. **重大度 = must-fix — 発火軸の非列挙性と random の有限 contract が両立していない。**  
   [段2プラン §4](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:79) は有限 site・有限 production・`K≤4` を完全固定する。LLM も同じ contract に閉じるなら全候補を機械列挙でき、[§8 の「完全列挙器を持たない軸」](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:221)に反する。LLM に contract 外の任意コードを許すなら、random/sweep だけ狭い support に閉じた非対称比較になる。さらに random は必ず非-stock 変異を出す一方、LLM の stock/no-op/重複候補規則は未定である。  
   **影響:** LLM が安全な stock 重複で B=10 を埋め、random だけ anomaly を負う受理集合を許し、endpoint・系列 score・6 比較の成立値が変わる。

2. **重大度 = must-fix — correctness/certification 経路が exact contract として束縛されていない。**  
   §6 は一般名詞の「certification pipeline」に留まり、`pipeline.evaluate`、引数 preimage、WAL `COMMIT` receipt、report の certified-evidence hard gateを要求していない。現行 `pipeline.evaluate` の既定 correctness は tuple=200/thread=4/rr50 の小構成で、性能は1M/48である（[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/pipeline.py:127)）。`performance_correctness_workload(perf)` は実在するが optional であり、`screening` を指定すれば bench-first にもなる（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/pipeline.py:774)）。workload 条件分岐で小構成だけ正しい候補を塞げていない。  
   **影響:** 性能 workload では不正な候補が `certified` endpoint として選ばれ、レポートと台帳の COMMIT/正しさ参照が誤る。

3. **重大度 = must-fix — incomplete を一律「判定不能」にするため、arm 依存の失敗が選択的 censoring になる。**  
   [§3](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:68) は、LLM の生成遅延・内容起因コンパイル失敗、random の低 Tier0 通過率、純粋な機械故障をすべて同じ incomplete にする。P2-5 は未到達を予算上限の最悪値へ算入しており、今回の扱いと逆である。また `build infrastructure error` と candidate-induced build failure の識別規則、retry が A/B のどちらを消費するかも閉じていない。  
   **影響:** 本来は LLM または baseline の敗北になる系列が判定不能へ消え、台帳の A/B 消費値と workload の受理状態が系統的に変わる。

4. **重大度 = must-fix — anomaly を `-100%` の性能観測へ変換すると、correctness failure が任意尺度の性能差になる。**  
   anomaly の即 reject と slot 消費は支持する。しかし全 reject または endpoint 再検証失敗を `-100%` にすると、実測 throughput がない系列が平均差 permutation test と中央値へ入る。[連言条件4](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:196) は「未処理 anomaly がない」だけなので、処理済み `-100%` baseline を材料にLLM勝利が成立しうる。安全候補偏重は成果物の正しさには望ましく、correctness gateを緩めるより害が小さい。危険なのは、それを性能優越へ数値変換することにある。  
   **影響:** baseline の anomaly 数だけで平均差・p値・endpoint受理が大幅に動き、certified 性能差ではない値が headline に入る。

5. **重大度 = must-fix — 「固定 schema」は固定されておらず、LLM と baseline の情報利用も非対称である。**  
   [§6](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:154) は「最低限」と書くため追加フィールドを許し、`anomaly_class` の閉じた enumもない。§1 が約束する性能履歴はschemaに存在せず、Tier0不通過の `proposal_index` も表現できない。さらに random/sweep は state に応じて分岐しないため、同じ bytes を渡しても、状態を treatment として利用するのはLLMだけである。比較されるのは「LLM」ではなく「適応的LLM閉ループ vs open-loop baseline」であり、B-4のfeedback効果と交絡する。  
   **影響:** 同じ raw 台帳からでも、追加された signal と attribution の解釈次第で「LLM固有」とするレポート参照・主張受理集合が変わる。

6. **重大度 = must-fix — `paired_stock` と `floor_cmp` が純関数として未定義である。**  
   系列 score の `paired_stock_throughput` について、測定数、前後順、arm間共有、source/hash、失敗時処理がない。[floor式](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:180) も、24 endpoint CVの最大なのか、arm内pool CVなのか、どのCV推定量かが不明である。`max(3%, fresh CV)` 自体は、fresh対象別再測を常に行う限り「floor流用禁止」と直ちには矛盾しない。ただしLLM endpoint/stock標本を二つの baseline 比較で共有できる書き方であり、比較対象別再測義務を機械確認できない。  
   **影響:** stock分母、floor閾値、median difference、同等判定、最終endpoint選択が実走後の実装解釈で変わる。

7. **重大度 = must-fix — Holm族6は一つのactivation内しか閉じず、軸を替えた再発火を制限していない。**  
   将来複数軸を順に承認・実走し、成功軸だけ報告する経路が残る。activation総数、最初の適格軸を採る規則、axis間のα配分がない。また一部比較が判定不能になった場合、Holm入力を `p=1` とするか族から除くかも未定である。「時間分離」の定量条件とblock割当照合もない。  
   **影響:** 同じ各軸の生p値でも、試した軸数・欠測pの扱い・block構成によりHolm調整値とB-5受理集合が変わる。

8. **重大度 = must-fix — 休眠解除条件5点は operative gate ではなく、自己申告で満たせる。**  
   軸の「単一scalarでない」「非列挙」は意味判断、閲覧資料台帳は記憶の自己申告である。「同じ条件を強制できる」は実走がそのconsumerを通った保証ではない。human approvalも、承認対象commit・decision ID・実行権限receiptへ束縛されていない。formal取得前commitも、runがその祖先commitをattestしなければ事後記載できる。条件3の「consumerが実在し、強制できる」は特に恒真化しやすい。  
   **影響:** 未承認・別経路の走行がformal台帳に入り、exploratory結果がB-5証拠として受理されうる。

9. **重大度 = must-fix — 親の段1が、既存予算・入口をB-5互換と一般化した部分は成立しない。**  
   `generation_budget_per_workload` はcertification slotではなく外側のLLM generation数であり、role-invalidやinner loop停止でも終了する。現コードは `MAX_APPROVED_GENERATIONS=2` でB=10を拒否する（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/p3_autonomous_workload_trial.py:144)）。同入口はaxisもtrigger-gatingへhard-codeされている（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/p3_autonomous_workload_trial.py:560)）。既存sweepもB/A/hash順を共有するB-5 driverではない。  
   **影響:** 発火条件3の「B/A/停止条件を強制できる実行入口あり」という台帳値・参照が偽になり、実装未完を実走可能として扱う。

10. **重大度 = should-fix — 親の全件検索は意味的全件検索ではなく、機械sweepも一件取りこぼしている。**  
    検索語は別名実装を拾わない。実際、random順replayの [search_baselines.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/search_baselines.py:81)、C4無作為抽出、汎用mutation harnessが存在する。ただしどれも「同一編集面のrandom code-fragmentを生成しpipeline評価するB-5 arm」ではなく、より広い静的確認でも正式random armは見つからなかった。一方、機械sweep inventoryは [s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/s8a_trigger_sweep.py:1) を落としている。  
    **影響:** 現時点の受理集合は変わらないが、実行入口台帳の参照が不完全で、将来の前提充足判定を誤らせる。

## 支持する箇所

- anomalyの即reject、anomalyにもslotを消費させる方向は支持する。
- 性能早期停止禁止、N追加禁止、欠けた系列の差し替え禁止は支持する。
- 検定単位をpath-dependentな系列に置き、6比較をHolm族へ固定する骨格は支持する。
- workloadごとのrandom/sweep双方への連言、全9セル・全anomaly・全incomplete報告は支持する。
- sweep-matchedとsweep-ceilingの分離、hash順、命名provenanceは支持する。
- 現行 `pipeline.evaluate` にtrace/perf別build、TRACE差分検査、perf buildのtrace symbol拒否がある点は確認できた。

## 親の段 1 実測への指摘

- 「ランダム変異アーム不在」という結論は、意味検索を広げても正しい。ただし提示された検索語だけでは証明にならず、「全件検索0件」は方法を限定して書くべきである。
- 「3アームを走らせられる適格軸が現存しない」も現在の正式B-5については正しい。trigger-gatingにはLLM loopと機械sweepがあるがD52の対象外でrandom armがなく、backoff/sortも不適格である。
- T-140を「段階Bへ差し戻し、存廃が裁定待ち」としたbriefは古い。現正本はmax_ope=10で地形なしを実測し、**workload条件付き休眠**へ確定している（[phase3.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/phase3.md:159)、[worklog一次記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/archive/worklog-phase3-0727-26-0728-32.md:390)）。
- 「3アームとも `pipeline.evaluate` を通せばtrace-disabled計測を機構で担保できる」は、trace-disabledという狭い性質についてはコードで裏が取れる。ただし同一引数・同一correctness workload・同一COMMIT consumerまでの対称性は、それだけでは保証されない。
- 段1の「評価回数予算と停止条件が実在」はB-5互換性を過大一般化している。現存するのは別実験のgeneration budget、s8b/s8c ledger、axis固有sweepであり、B=10 certification slotの共通consumerではない。

## 総括

現状の草案では、correctnessを緩めずに守る方向そのものは正しい。  
しかし有限random contractと非列挙軸の矛盾、arm別support、`-100%`擬似性能値により、LLM必要性の因果解釈は成立しない。  
trace-disabled機構は既にあるが、草案はその必須経路・exact引数・report receiptへ束縛できていない。  
floor、stock、欠測Holm、複数axis activationには実走後に動かせる自由度が残る。  
休眠解除条件も現状は宣言であり、実行拒否・承認receipt・report hard gateが必要である。  
したがって、休眠維持の結論は支持するが、この草案を将来の実走規約として発効させるのはまだ不可である。