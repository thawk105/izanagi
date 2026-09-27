---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: worktree-dev-wave-t2849-mocc-conn
seq: 1
---

## {{D:mocc-connectivity-run}}. 第 2 プロトコル MOCC の疎通は 5 手法 × 3 workload を 1 系列ずつ (探索 2 件、候補 20 / workload) で既存の harness に通し、balanced・read-heavy は直列検査のまま、trace は qsub の env で保全する。結果は stock 比で記録し、read-heavy の anomaly と K0 planner の axis 名の揺れは別課題に分ける

**決定:** D2220 項 6 の第 2 プロトコル (S2 = MOCC) の疎通を次の形で行い、記録した (記録 `output/insights/2026-09-27/t2849-mocc-conn/README.md`)。

1. **規模。** 各 workload (rr5・rr50・rr95) で random・sweep・bo・evolution・llm を 1 系列ずつ (A = 6・B = 2・N_eval = 1) と block 対照 1 (block-stock 1 session)。候補評価は 20 / workload。
   依頼の範囲 (20〜40) の下限で、単価実測 3 job の job Elapse から約 10〜14 node 時間と見積もり、ユーザーが「20 候補 × 3 workload (推奨)」と回答した (D2212 項 4)。実績は本投入 13.65 node 時間。
2. **検査の方式。** write-heavy は着地済みの同時検査 (D2251)、balanced・read-heavy は直列検査のまま。同時検査を広げるコード変更と記憶量・静定上限の実測は、疎通 1 回の節約より準備費が大きいので行わない。
3. **trace 保全 (D2233 の opt-in) は qsub の `-v` で `IZANAGI_TRACE_ARCHIVE_ROOT` を渡して有効にする。** job body は env を消さず、harness の子は `os.environ` を継承するので、job body のコード変更は要らない。
   保全先は repo 外の `izanagi-repro-archive/t2849-mocc-conn-20260926/`。
4. **submit-tree と LLM 親。** submit-tree は job ごとに 1 本 (job dir 下、`git worktree lock`、third-party は tree 内 staging へ hydrate、D2248 の insight §6 の作法)。
   llm 系列の親は T-2850 glue v3 の起動器を改変せずに使い、親 template は T-2850 版から固定 commit・description・materials root だけを差し替えた写しを job dir に置く。
5. **結果の扱い。** 15 系列すべて `b-complete`。比較は block 対照の stock に対する比だけで書き、既知最良の参照は無い (参照比は null)。1 系列・反復なしの観測なので手法の優劣・性能の主張に使わない。
6. **read-heavy の anomaly。** 候補 slot 25 件中 6 件で G2 (write skew) を検出し、pipeline が候補を reject した (規律 2 のまま)。stock slot 7 件と write-heavy・balanced の候補 slot 50 件は 0。
   原因 (MOCC 本体・literal の差し込み・verifier) は未確定のまま別課題 {{T:mocc-readheavy-anomaly-cause}} とし、決まるまで論文の主張に使わない。
7. **K0 planner の axis 名。** llm 系列の提案 13 機会中 7 件が「planner の axis が `silo-backoff-magnitude` でない」で拒否された。silo の試走にもあり protocol に依らない。
   救済せず A を消費する現行の扱いは変えず、直し方は別課題 {{T:k0-planner-axis-name}} とする。

**理由:**
- 完了条件は「5 手法が同じ口で走る基盤と第 2 プロトコルでの疎通」で、依頼の下限の規模で全手法・全 workload の終端まで通ることを確かめれば足りる。ユーザーは費用の過大に強く反応してきた (探索の独立反復の試走の計算確認)。
- 同時検査の拡張は依頼で「使うなら先に測る」とされ、本題の実装だけという scope の外に準備費が出る。
- 保全口は env の opt-in として作られており、job body の env 契約はそのまま通る。コードを変えずに有効にできる。
- anomaly は正しさゲートが MOCC の探索候補を実際に落とした観測だが、stock を同じ throughput 域で走らせる手段が今回の構成に無く、原因を確定できない。確定前に主張へ使うと誤りを残す。

**却下した選択肢:**
- 40 候補 × 3 workload (約 20〜26 node 時間) — 疎通には下限で足り、ユーザーが 20 を選んだ。
- read-heavy・balanced にも同時検査を使う — コード変更 (Codex author・変異・受入) と記憶量・静定上限の実測が要る。
- 同じ submit-tree を複数 job で共有する — 前回 wave で stock root の同一性検査が他 job の変更で停止した (29530)。
- anomaly を出した候補の再評価や、anomaly の条件を避ける値域への探索の制限 — 正しさ判定の結果を後から動かすことになる (規律 2・3)。
