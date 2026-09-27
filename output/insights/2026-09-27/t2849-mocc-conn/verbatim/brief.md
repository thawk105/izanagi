# 段 1 brief — [T-2849] 残り (3) MOCC 疎通 (2026-09-26 22:35 JST、起点 main 6c3913bc5)

- 研究前進: VLDB 差分分析 P2 (公平な比較基盤と第 2 プロトコル) の完了条件「第 2 プロトコルでの疎通」を実測で埋める。
  完了判定 = MOCC の 3 workload (rr5/rr50/rr95) で 5 手法 (random/sweep/bo/evolution/llm) の系列が同じ口で最後まで走り、
  各系列の終端と stock 比 (block-stock の median に対する比) が台帳から出ること。性能主張ではない (反復・事前登録なし)。
- scope: 既存の harness (`t2849_comparison_harness run-series / run-block-controls --protocol mocc`) を job body の harness mode で直接 qsub する。
  コード変更は想定しない (段 4 で「実装しない」なら 4→7→8→9)。仮想リスク向けの gate・検査・台帳・一般化は足さない。
- 確定済み裁定: D2220 項 6 (stock 比で報告・既知最良の参照なし)、D2248 (MOCC は別 cohort 名・root、slot は pin C)、D2251 (同時検査は write-heavy の opt-in、
  harness は write-heavy slot に常に付ける)、D2212 項 4 (1 タスク 2 node 時間以上は実測単価で見積り → ユーザー確認)、D2249 (時間帯の区切りを入れない)。
- 不変条件: 規律 1・2 (verifier・anomaly 即 reject・Tier0・意味検査は不変)。trace 保全は env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in (job body は env を消さず、
  harness の子は os.environ を継承、`b5_generator_contrast.default_runner`) — qsub -v で保全先を渡す。
- (P1) 親の provisional: read-heavy・balanced は同時検査を使わず直列検査 (着地済みの挙動のまま)。同時検査へ広げるにはコード変更と記憶量・静定上限の実測が要り、
  単価の実測で直列が許容範囲なら不要。攻撃対象。
- (P2) 規模: 各 workload で 5 手法 × 1 系列、B = 2・A = 6・N_eval = 1 (候補評価 = 初期点 2 + 探索 2 = 4 / 系列 → 20 / workload)、block 対照 1 job (block-stock 1)。
  依頼の下限 20 を選ぶ (ユーザーは T-2850 で費用過大に強く反応した)。攻撃対象。
- (P3) 単価の実測: 本投入の前に rr50・rr95・rr5 の block 対照 (stock 1 session、保全有効) を 1 job ずつ走らせ、slot 単価と保全の手間を測る (DW-G01 の生死確認を兼ねる、
  合計 < 2 node 時間なので確認不要)。この単価で本投入を見積りユーザー確認。
- (P4) llm 系列は T-2850 glue v3 の `parent_driver.py` を login で使い、親 template は T-2850 の雛形を job dir に写して submit-tree・description だけ差し替える。
  model は K0 比較と同じ claude-opus-5 (settings は B-5 の file)。LLM の週枠 429 は欠測リスクとして見積りに機会数を並べる。
- 成果物: insight `output/insights/<日付>/t2849-mocc-conn/README.md` (系列表・stock 比・費用・既知最良の参照なしの明記)、worklog/decisions fragment、phase3 のチェック。
  cohort・証跡・trace 保全は repo 外 (job dir と `/work/1/SFC/tanab/izanagi-repro-archive/t2849-mocc-conn-20260926/`)。
- 分割: submit-tree は job ごとに 1 本 (AI の worktree 置き場の外 = job dir 下)、third-party は submit-tree 内 staging へ hydrate。18 job を同時投入可 (1 job 1 node)。
- 受入・実測環境: Pegasus (runbook `docs/pegasus-runbook.md`)。受入全走は記録 commit 後に `tools/dev_wave_wait.py acceptance`。
