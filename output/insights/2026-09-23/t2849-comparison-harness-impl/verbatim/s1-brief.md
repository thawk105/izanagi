# 段 1 brief — [T-2849] 5 手法比較基盤の実装 (単位 1〜7) + [T-2853] (1) trace 保全口

- wave: worktree-dev-wave-t2849-comparison-harness (worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2849-comparison-harness)
- 起点 local main 3886a1fd36657537af2b6c6ed389257363d92bef (2026-09-23 07:43 JST、開始 gate fresh rc 0)
- 依頼逐語: 本 dir の ../s1/request.md

## 研究前進
VLDB 差分分析 P2 (gap-analysis §4 P2) の「random・sweep・BO・進化・LLM を同じ候補適用・検証・計測の口で比べる」比較の、S1 (silo backoff 1..1000 µs) での実行基盤を作る。完了判定 = 5 arm が同じ p3_s4_loop 単回評価経路を通る系列制御が単体試験で動き、[T-2850] 事前登録の値 (B・A・k・系列数) を入れれば投入できる形。あわせて [T-2853] §7 の「論文根拠の実験は作業保管を全量 zstd」を標準経路で可能にする (今は検証後に trace を rmtree)。

## scope (設計正本 = D2220 と insight output/insights/2026-09-22/t2849-comparison-harness-design/README.md §11 単位 1〜7)
1. 機械生成 proposal の slot を B-5 接頭辞から外す: p3_s4_loop.py:3547-3566 (`--b5-slot` の接頭辞検査 `b5-generator-contrast-v1|`、`--machine-generated-proposal` の `--b5-slot` 必須)。本基盤の名前空間 `t2849-harness-v1|` を受ける。
2. S1 の 5 arm 系列制御: B-5 の run_series (b5_generator_contrast.py:722-841) と同手順 + 初期点 slot (静的 5・10 µs、系列ごとに fresh、B の外) + 5 arm + 全 arm の A 上限。**兄弟 module** (新 file) に置き、b5_generator_contrast.py は編集しない (import して関数を呼ぶ)。台帳は SeriesLedger 相当で schema 名だけ別。
3. 生成器: BO (x = ln v の逐次 GP-EI、Matérn 5/2、格子の超パラメータ選択、雑音 (ln 1.03)^2、1000 点全列挙、失敗 v 除外) と (1+1) 進化 (λ = ln 4、log 尺度、親置換は真に大きいときだけ) を標準ライブラリで。random / sweep は B-5 の重み表・格子を名前空間だけ変えて使う (sweep は初期点の値を除く 26 点)。固定入力の値照合試験を持つ。
4. K0 LLM の入口 (D2220 項 2): 機械生成の印なし + `--allow-coder-derived-build` の slot、knowledge manifest なし、coder role = coder-v4-autonomous。current_perf / baseline の期待値と照合に初期点を加える。whiteboard 5 field・iteration = b・継承照合は B-5 のまま。**(P2) 参照。**
5. 参照点と endpoint 集約: `p2_2_flag_opt` の exact flags (balanced・write-heavy = B0-L-W0、read-heavy = B0-T-W0、output/s1-freeze/known_axes_freeze.json:90-99・:542-549) を stock と同じ検証・計測へ渡す入口 (今の stock / 候補経路は BACK_OFF=1 固定、p3_s4_loop.py の _BASE/stock 経路)、block ごとの測定、全系列への anomaly 波及、初期点を含む endpoint 資格、insight §4.6 の欠測と fallback の優先。
6. 費用 field: job Elapse (job ごと 1 回、PBS_JOBID を記録し集約で引く)、生成器の計算 wall、LLM 役割呼び出しの回数と wall、人間の介入の記録。
7. node-local bench lock を B-5 mode の外でも (D2209 は job body tools/pegasus/p3_s4_loop_pegasus.sh の B-5 分岐で IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock")。**(P3) 参照。**
8. [T-2853] (1): pipeline.py:2160-2178 (`tempfile.mkdtemp(prefix="izanagi_eval_trace_…")` → `finally: shutil.rmtree`) に、明示 opt-in のときだけ trace dir を zstd で保全してから消す口。既存経路 (opt-in なし) の挙動・bytes 出力は不変。保全の記録は WAL / proof chain に入れず保全先の側に置く (proof chain の schema を変えない)。参考実装 = repo 外 runner の `zstd -T0 -3` + file 別 sha256/bytes/行数 inventory (insight t2853 §4.1)。

scope 外: 単位 8 (MOCC)、第 2 プロトコル疎通、launcher / registered schedule (値は T-2850)、新しい gate・検査・台帳 (台帳の schema 名変更は可)、B-5 module・B-5 事前登録・B-5 束の編集、t2857 (silo 関数方策の file 群・docs/axis-onboarding.md)・t2854 (CCBench・verifier) の編集面、orchestrator/tests/test_p3_s4_loop.py の編集 (t2857 子木が編集中 → 新規 test file に置く)。

## 確定済みユーザー裁定
D2212 項 4・第 31 回項 1 (開発の検査を含む job 合計 2 node 時間以上は実測単価の見積りで事前確認)、D95 (実装面は Codex author)、D2220 (設計)、D2209 (bench lock の置き方)。

## 不変条件
- 規律 1・2: 正しさゲート (verify・anomaly 即 reject) と trace の compile 時除去は変えない。保全は検証の後段の副作用で、verdict・受理集合を変えない。
- 既存経路の argv・挙動は不変: B-5 の `b5-generator-contrast-v1|` slot、非 B-5 の 3 経路、opt-in なしの pipeline.evaluate。
- B-5 module / 事前登録 / 束 / .claude/agents/ は編集しない (P2 の裁定次第)。
- 生成器は自系列の記録だけを入力にする (R0、参照値を渡さない)。

## (P1) 親の provisional 裁定・攻撃対象 — B-5 束の hash 束縛
B-5 発効束 draft (output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json, status draft, ユーザー承認待ち) の files_sha256 は p3_s4_loop.py・pipeline.py・tools/pegasus/p3_s4_loop_pegasus.sh・.claude/agents/planner-v4.md を束縛し、現行と一致 (親実測)。本 wave は前 3 file を必ず変える。束の target_commit_rule は「承認対象は T-2797 の land commit と、その status だけを変える発効 commit。本走は発効 commit の detached 固定 checkout」なので、**発効 commit を T-2797 land commit の子として (main 先端でなく) 作れば束は一致したまま**。provisional: 本 wave は 3 file を変え、この事実を insight と worklog の T-2797 項に 1 行残す (束・B-5 は編集しない)。

## (P2) 親の provisional 裁定・攻撃対象 — K0 LLM の役割契約
新事実 (D2220 裁定時に未見): .claude/agents/planner-v4.md「K2手動loopの任意診断入力 (T-2783)」節は `k2_critic_diagnosis` を「K0/K1・B-4・8c へ適用しない」と明記し、p3_s4_loop.py:1295-1340 planner_context_payload も K2 以外を拒否する。coder-v4-autonomous.md の入力は leakproof_context・baseline・planner_direction・whiteboard の 4 key だけ。D2220 の「D2155 射影を K0 へ」「初期点と投入前の拒否を閉じた兄弟 key で」は役割定義 2 file の改訂を要し、両 file の sha は .codex/role-adapters/*.json・orchestrator/tests/test_codex_agents.py・B-5 束・図の provenance に束縛されている。
provisional: 本 wave は役割定義を変えず、既存の役割契約内で K0 LLM の入口 (slot argv・handshake・current_perf/baseline への初期点・K0 用 LLM 巡 tool) を実装する。critic 還流と兄弟 key は「役割定義の改訂 (sha 束縛の連鎖を含む)」の別 T へ送り、insight に D2220 との差として明記する。代案: (a) 本 wave で役割定義も改訂、(c) 単位 4 を丸ごと送る。

## (P3) 親の provisional 裁定・攻撃対象 — 実行経路
本基盤を計算ノードで走らせる job body 分岐が無いと単位 7 の置き場が無い。provisional: job body に B-5 分岐と同型の最小 harness 分岐 (driver 起動直前だけ IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"、非 harness 経路の argv・環境は不変) を足す。代案: driver 自身が slot subprocess の env に job 固有 lock を設定する。

## 成果物の形
新 module 2〜3 本 (系列制御・生成器・K0 巡 tool) + p3_s4_loop.py / pipeline.py / job body の最小変更 + 新規 test file。docs は段 7 で insight・fragment。

## 並列分割方針 (段 2 で所有 path を確定)
- U-A: p3_s4_loop.py (単位 1・5 の入口) + pipeline.py (単位 8) + それらの新規 test。
- U-B: 兄弟 module (単位 2・3・5 の集約・6) + 新規 test。
- U-C: K0 LLM 巡 tool (単位 4) + job body 分岐 (単位 7) + 新規 test。
interface (CLI flag 名・env 名・台帳 event) は plan v2 で固定してから並列投入。

## 受入・実測環境
受入 = tools/dev_wave_wait.py acceptance (Pegasus dispatch)。実測単価: 受入 1 回 ≈ 0.25 node 時間、焦点走 1 回 ≈ 0.06 node 時間 (記憶の実測、2026-09-22)。変異は pure unit test なら login self-run (node 時間 0)。見込み ≤ 1.2 node 時間 < 2 → 事前確認不要の見込み、段 4 で再見積り。
