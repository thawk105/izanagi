# 変異 harness の結果要約 (親作成、2026-09-19 23:50 JST)

手順: 変更前 commit `657e1e5a7` で probe (全件 SURVIVED 期待、失敗 node 集合 S_pre を記録) → 削除 commit `0917fc400` で S_post = S_pre − Del を KILLED 期待に登録して本走。runner は module ごとに当該 test file 1 本 (`python3 tools/run_tests.py --force-dispatch <file> -q -rf`)、`tools/mutation_harness.py --repo <固定 commit worktree> --runner-mode dispatch --detached`。source は主 repo の登録 worktree `.codex/worktrees/tinv-mut-{h,l}` (submodule 初期化済み、clean)。**erratum:** 段 4 裁定は「独立 clone」(DW-M07 の wrapper 経路) と書いたが、実行は上記の登録 worktree へ harness を直接当てる DW-M05 経路にした (fresh clone は submodule 供給 URL が非 local で初期化 tool に拒否されるため)。harness が `repo_head` (probe 657e1e5a7 / post 0917fc400) と clean tree を束縛しており観測事実は同じだが、DW-M07 の文言どおりではない。

| spec | 変異 | probe (pre) 失敗 node | 削除 node のうち検出していたもの | post 期待 = 実測 | 状態 |
|---|---|---:|---:|---:|---|
| H `orchestrator/campaign/s8b_holdout_freeze.py` | M1 `min(eligible…)`→`max(…)` (1981 行) | 6 | 1 (`[drop-candidate-selection]`) | 5 = 5 | KILLED |
| H | M2 `if required_run_id != selected_run_id:`→`if False and …` (1983 行) | 6 | 1 | 5 = 5 | KILLED |
| H | E1 encoding comment に `# mutation-control` (対照) | 0 | 0 | 0 = 0 | SURVIVED |
| L `orchestrator/campaign/p3_s4_loop.py` | M1 `assigned_value != coder_value`→`==` (assert_value_literal_consistent) | 23 | 1 (`test_value_literal_consistency_accepts_match`) | 22 = 22 | KILLED |
| L | M2 `if decision.accepted:`→`if decision.accepted or True:` (_assert_coder_value_domain) | 20 | 4 (`[nonintegral|bool|zero|above-upper]`) | 16 = 16 | KILLED |
| L | E1 encoding comment (対照) | 0 | 0 | 0 = 0 | SURVIVED |

- H の M1/M2 で残る検出 node: `[min-to-max]`、`[use-reported-eligible]`、`test_restored_namespace_rejects_later_eligible_run`、`test_v2_candidate_enumerates_and_reads_earlier_run_through_bound_dirfds`、`test_floor_selection_threads_earlier_run_identity_and_manifest_to_derivation`。
- L の M1 で残る検出 node には `…accepts_declared_integral_boundaries[middle-int]`/`[middle-float]` (削除関数の同値 case) を含む 22 node。M2 で残る検出 node には `test_backoff_value_adapter_preserves_main_exception_and_structured_rule[20.5-…]`/`[True-1-…]`/`[0-0-…]`/`[1001-1001-…]` (削除 row の同値 case) を含む 16 node。
- baseline: H 変更前 162 passed / 2 skipped、削除後 161 passed / 2 skipped。L 変更前・削除後とも PASSED (post は file 内 node 数が 5 減)。
- harness summary は両 post とも `matching 3 / registered 3` (KILLED 2、SURVIVED 1、MISMATCH 0)。probe は設計どおり `MISMATCH 2 / SURVIVED 1` (rc=1) で、erratum として保存する。
- 非 ASCII id は両 file とも 0 件。drift mask (source の HEAD blob 比較で一律に赤になる gate) は両 runner とも 0 件 (E1 が赤 0)。
- 検算 (`check-pre-post.py`): 全変異で S_post == S_pre − Del、負例は非空 → ALL OK。
- 実行期間 (queue 待ち込みの外側 wall、所要ではない): probe は 22:57 起動 → 23:26 完了、post は 23:29 → 23:48 (2 spec 並列、各 spec = collection 1 + baseline 1 + 変異 3 = dispatch job 5 本)。所要は各 job の Elapse (結果 JSON の receipt path) または runner 報告時間 (H baseline 35.0 s / 35.4 s) を正とする。

一次資料 (job dir): `mutation-spec-{h,l}-probe.json` (sha 013e9bcc… / 968e3c1c…)、`mutation-spec-{h,l}-post.json` (sha b92591ef… / bdfcd328…)、`mut-{h,l}-{probe,post}.results.json`、`.attempts.json`、`.log`。

主張の範囲: 登録した変異 (module ごと負例 2 + 対照 1) に対して、削除 node が検出していた変異を残存 node が全件検出することを示した。あらゆる欠陥に対する検出力の一般保存の証明ではない。主根拠は §3 の同値性 (同関数・同型・同入力、または残存 assertion による包含) で、変異はその裏取りである。
