# 段 1 brief — [T-2228] A-2 経路で関門の 2 層目以降が発火することを実体で確かめ、出た層を直す

wave: `dev-wave-t2228-a2-gate-layers` / branch `worktree-dev-wave-t2228-a2-gate-layers`
基点 main: `396dc8988` (T-2226 着地 95a3f02ae の後)
worktree (子の cwd もここ): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-a2-gate-layers`
job artifact dir: `/home/SFC/tanab/.claude/jobs/a33f2475/tmp/dw/t2228-a2-gate-layers/`

## 1. 確定済みユーザー裁定と命令

- 命令 (逐語は `command-args.md`): 本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  規律 2 を緩めない。Codex author = D95。2 層目以降が発火することを、性質でなく実体を名指しした正例・負例で確かめる。
  既完走 A-2 4-cell (reject) への影響を報告に含める。
- 起動時の編集面重複検査: T-2226 (同 file の inert 経路) と重なったため着手前に報告し、着地 (95a3f02ae) を待って開始した。
- D1198: 供給と実行側の意味を独立した必須節と負例で持つ。D1523 (T-2226、着地済): inert 比較は差を取ってから置き場所由来かを判定。
  D1522: 下層の実体を名指しする直接検査にし、差し替えは実効発火を assertion で固定し、正例対照を同じテストに置く。
  逐語は `verbatim-rulings.md`。

## 2. 実測で確認した前提 (親が本 worktree で実測)

- T-2022 の 4-cell 実走 commit `639c1dbad` の A-2 driver は `condition_meaning_gate` を参照しない (grep 0 件)。関門の配線は `0218acc61` (2026-09-01)。
- attempt `a2gate-20260902b` (commit e9b91eb76) の `jobs/rr5/scheduler/job.stderr`: cell-0 で
  `BACKOFF_FIXED:supply-effectuation:preprocess-root-dependent-builtin`、`BACKOFF_NOINLINE:supply-effectuation:preprocess-root-dependent-builtin`、
  `BACKOFF_NOINLINE:runtime-meaning:meaning-witness-undeclared`。BACKOFF_FIXED の runtime-meaning は緑 (非緑列挙に無い)。
- `orchestrator/campaign/paper_story_a2_certification.py:577-697` `_condition_gate_family_context` は cell ごとに 2 腕を評価し
  `require_condition_gate_family(use_class="paper")` (同 file:670)、`admitted` でなければ即 `CertificationError` (同 file:675-685)。
  **cell-0 (stock) の赤で、cell-1 (adopted: 非 inert 経路 `requested-default-preprocess-different`) の腕、4 cell の admission、
  receipts (同 file:686-697)、`run_campaign` (同 file:3111-3142) は A-2 経路で一度も実行されていない。これが「2 層目以降」の実体。**
- T-2226 着地後の main で inert 経路の終端は `stock-inert-preprocess-identical` / `stock-inert-preprocess-root-location-only` (緑) /
  `stock-inert-mismatch` (赤) の 3 値 (`condition_meaning_gate.py:2547-2591`)。T-2226 の受入は login node の合成 fixture で、
  実 CCBench (`cc/silo/transaction.cc` の `ERR` → `include/debug.hh` の `__FILE__`) に対する実測は無い。1208 で層を 1 つ剥がすたびに次が出た履歴があるので、層 4 の可能性を実測で潰す。
- receipts は `summary.condition_gate_receipts` として `run_campaign` 完了後に materialize される (同 file:3142, 4212)。campaign が失敗すると admission の証拠は job.stdout の後続 log 以外に残らない。
- unit test `orchestrator/tests/test_paper_story_a2_certification.py:124-252, 500-560` は関門 4 関数 (`capture_define_inputs`、2 評価関数、`require_condition_gate_family`) を全て stub し、
  record も `SimpleNamespace`。**実体の `require_condition_gate_family` を driver から通す検査は 0 件。**
- policy v2 (`orchestrator/campaign/paper_story_a2_certification.v2.json`) の cells: `rr5-stock {BACK_OFF:0, BACKOFF_FIXED:-1}`、`rr5-fixed10`、`rr50-stock`、`rr50-fixed5`。
  `controlled_define_base` に `CCBENCH_BACKOFF_NOINLINE=0`。durable base `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824`。
- login node は `buildcache.require_heavy_work_site` が cmake を拒否 (`buildcache.py:1825, 3474`)。関門文脈の実走は計算ノードのみ。
  先例: 1208 が attempt `a2gate-20260902a/b` を production 入口 `tools/pegasus/submit_paper_story_a2_certification.sh` で投入して層を剥がした。
- 新規 probe を `tools/pegasus/probes/` へ足すと `tools/pegasus/admission_registry.json`、`orchestrator/tests/test_hooks.py:2601,2810` の exact dict、
  `orchestrator/tests/test_ccbench_spawn_sites.py:907,2661` の inventory に触る (T-2187 probe の pin)。
- DW-O09: `paper_story_a2_certification.py` の bytes pin は 0 件。source 形 pin は同 test の `count("patchharness.checkout(") == 1` (行 75)、`run_source` の順序 assertion (行 63-90)、行 3244-3248 の `count(passed) == 2`。
  DW-O08/O10: 凍結成果物 (t2022-20260828c の `certification.json` sha `f685b40d...`) の bytes は変わらない。新 attempt は別 leaf。producer の出力形は変えない → O10 不成立。
- 他 3 driver (`backoff_sweep.py:105-154`、`backoff_repro.py:70-74`、`s1_direct_comparison.py:275-294`) の stock 比較は同じ `evaluate_define_supply_effectuation` の inert 経路を通る (T-2226 B-6)。本 wave では実測しない。

## 3. scope (本題だけ)

1. **正例 (実体・production 入口、親の計測操作、コード変更なし):** main `396dc8988` の detached tree から A-2 attempt `t2228-20260904a` を投入し、
   rr5 / rr50 の各 2 cell について supply / meaning の reason code、admission、receipts、campaign 到達を実測する。層 4 が出たら本題として直す。
2. **実体を名指しした unit 正例・負例 (Codex author):** driver の `_condition_gate_family_context` を、実体の `require_condition_gate_family` と
   実体の `_issue_arm_record` 経由の `ConditionArmRecord` で通す。正例 = admitted → receipts に record の canonical JSON と admission が入る。
   負例 = 実体の赤 record → 実体の family 判定が `admitted=False` → driver が `CertificationError` に `detail` を載せる。
   差し替えは compiler を要する 2 評価関数と `capture_define_inputs`、patch / prebuild だけに限定し、呼ばれた回数を assertion で固定 (D1522)。
3. 既完走 4-cell (reject) への影響を段 7 の記録で確定する。

**scope 外**: receipts の campaign 前保存 (台帳追加)、他 3 driver の inert 経路実測、BACKOFF_NOINLINE の意味 arm 厳格化 (T-2227)、新規 probe、CCBench 改変、一般化した helper。

## 4. 不変条件 (緩めない)

- 規律 2: 関門の受理集合を広げない。赤を緑にするテスト変更・stub 化をしない。層 4 の修正も「本物の差を赤にする」向きに倒す。
- 既存テストの期待値を変えない。既存 attempt を触らず、既存測定を無効にしない (規律 7)。
- production コードは、層 4 が実測で出た場合だけ変更する。

## 5. 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 正例の実体は production 入口の実 attempt で取り、専用 probe は作らない。probe は 3 箇所の registry pin と別 Codex 単位を要し、命令の「検査・台帳の追加は scope 外」に反する。代償は campaign 本走 (workload 1 本 約 1 時間 × 2 node)。
- **(P2)** unit の負例は `_issue_arm_record` で作った実 record (integrity 検査を通る) を評価関数の差し替えで返し、実体の `require_condition_gate_family` に判定させる。record を `SimpleNamespace` で偽装しない。
- **(P3)** 層 4 が出た場合、修正先は gate 本体でも driver でもよいが、受理集合を広げる向きなら裁定パッケージへ返す。
- **(P4)** 「2 層目以降」= cell-0 の赤で到達しなかった cell-1 の腕・admission・receipts・campaign。腕の評価順 (supply → meaning) のことではない (両腕は cell ごとに無条件に呼ばれる)。

## 6. 成果物の形

- attempt `t2228-20260904a` の receipts / job.stdout / job.stderr (durable base)。insight `output/insights/2026-09-04_t2228-a2-gate-layers/README.md`。
- `orchestrator/tests/test_paper_story_a2_certification.py` の正例・負例 (Codex author)。層 4 が出た場合のみ production 修正。
- 段 4 で変異事前登録、段 6 で変異 matrix + 受入全走。

## 7. 並列分割方針

段 5 実装子 1 単位 (test file 1 本、層 4 が出れば同じ子に持たせる)。段 2 / 3 / 6 は正しさ防壁に触るため省かない。

## 8. 受入・実測環境

計算ノード: attempt 投入 (queue gen_S、先例 a2gate-*)。login node: unit test は `tools/run_tests.py` 経由 (login/dispatch 自動判定)。

## 変更面の実アンカー

| 種別 | path:line | 内容 |
|---|---|---|
| 読む | `orchestrator/campaign/paper_story_a2_certification.py:577-697` | 関門文脈、admission、receipts |
| 読む | `orchestrator/campaign/paper_story_a2_certification.py:3111-3142` | 関門文脈の呼び出しと campaign |
| 読む | `orchestrator/campaign/condition_meaning_gate.py:923-990` | `_arm_record` / `_issue_arm_record` (実 record の作り方) |
| 読む | `orchestrator/campaign/condition_meaning_gate.py:3707-3770` | `require_condition_gate_family` |
| 読む | `orchestrator/campaign/condition_meaning_gate.py:3302-3500` | `_validate_supply_green_evidence` 等 (実 record の integrity 検査) |
| 編集 | `orchestrator/tests/test_paper_story_a2_certification.py:50-60, 124-252, 500-560` | 既存 stub 検査 (期待値は変えない)、正例・負例を追加 |
| 条件付き編集 | `orchestrator/campaign/condition_meaning_gate.py:2547-2591` | 層 4 が実測で出た場合のみ |
