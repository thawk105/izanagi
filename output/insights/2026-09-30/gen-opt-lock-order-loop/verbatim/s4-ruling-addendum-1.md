# 段 4 追補裁定 1 — 2026-09-30 23:15 JST

## 事実
- 段 5 の実装子 2 本 (author-u1・author-u2) は、`tools/run_tests.py` が子の sandbox から計算ノードの状態確認 (qstat) に失敗して rc=16 になった時点で、prompt の「失敗したら止まれ」に従って途中で停止した。起動器が残差を終端 commit した (u1 `a0fed7ea4`、u2 `47ace7fc5`)。
- これは既知の制約 (子は `tools/run_tests.py` も `python -m pytest` も走らせられない。/rulings 第 30 回項 8: 子に自走の実走を指示しない、子の報告は「実装済み・未実走」、赤の実測は親の焦点走) で、親の prompt の書き漏れである (段 8 の改善候補)。
- 単位 2 の報告: 新 driver の CLI が coder 由来の build 権限を発行するには `orchestrator/campaign/materializer_admission.py` の `MATERIALIZER_ADMISSION_REGISTRY` に登録が要る。既存の探索軸 driver 5 本 (`p3_s4_loop.main`・`p3_s4_loop_sort.main`・`p3_s4_loop_policy.main`・`p3_s4_loop_trigger_gating.main`・`p3_autonomous_workload_trial.main`) が同じ形で 1 行ずつ `ADMITTED_GATEWAY` / `CODER_ENTRYPOINT` に登録されている。

## 裁定
1. 継続子 (同じ木・同じ branch) に残りを実装させる。試験は走らせず「実装済み・未実走」と報告させる。変異の単一理由性の自己確認は静的な説明 (どの 1 か所を外すとどの assert が落ちるか) に替え、実走は親の変異 matrix で行う。
2. 単位 2 の所有に `orchestrator/campaign/materializer_admission.py` を加える。許すのは `MATERIALIZER_ADMISSION_REGISTRY` への `"orchestrator.campaign.p3_s4_loop_lock_order.main"` の 1 項目の追記 (`ADMITTED_GATEWAY`、`CODER_ENTRYPOINT`、理由文 1 行) だけ。他の項目・定数・関数は変えない。これに従属する inventory の件数 (build authority の site 集合など) の追記は既存の許可に含む。
   - 理由: 軸ごとに 1 行の同型の先例が 5 本あり、driver を CLI から動かす (1 周を通す) のに要る。正しさの関門 (order_gate・小モデル関門・要求つき判定・certified 行の照合) は発行元の登録で緩まない。
