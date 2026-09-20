単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s6-focus.md` — 焦点再レビュー (残件: A1 partial = 文字列の文法 preflight 拒否は WAL diff-reject 経路、B04 partial = `logical_sessions` の stock 無条件加算、TR:301 の `score_sessions` 追従 nit)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s6-adjudication.md` — 段 6 裁定 (B04 の仕様 = 投入済み論理 slot 数)
- **編集対象** (repo root `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix3`、HEAD = 統合 commit 4 `11d46a74a`):
  `orchestrator/campaign/b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_p3_s4_loop.py`
- 読むだけ (触らない): `orchestrator/campaign/b5_generator_contrast.py` (`classify_slot` の WAL 分岐 :340–350、`_execute_slot`)、`orchestrator/campaign/p3_s4_loop.py` (`_run_one_iteration_resolved` の文字列 preflight 拒否 :2166–2200、`record_diff_reject`)。

## この fix の仕事 (親の裁定)

1. **B04 (report):** `logical_sessions` は「投入済み論理 slot 数」= (stock-start が submitted なら 1) + submitted search の論理 slot 数 + submitted score session 数 + submitted block-stock 数。runner が 1 回も呼ばれない系列 (開始前 allocation 枯渇、stock の pre-start failure) では 0。対照 test 2 本 (runner 0 回 → 0、stock 投入済み + search 3 投入 → 4) を TR に足し、`test_..._logical_sessions=2` の縮約例は producer が作れる形へ直す。
2. **A1 残件 (test のみ、実装は変えない):** 文字列の文法 preflight 拒否 (例: 正常な代入に空白を足して `MAX_BACKOFF_HOLE_BYTES` 超過にした `implementation`) は既存の WAL diff-reject (`build_start` → `abort(reason=diff-quarantine)`) が durable 記録であり、sidecar `proposal-rejected.json` は書かれず CLI rc は 0 である。この経路で driver の `classify_slot` が `rejected-preprocess` (A のみ、B 不変、retry 無し、系列継続) になることを TG の負例 1 本 (fake runner が sidecar 無し + slot-start あり + WAL に diff-quarantine abort を合成) で固定する。TL には B-5 mode で文字列 preflight 拒否が `outcome="rejected"` / rc 0 / sidecar 無しになる正例を 1 本足す (現行挙動の固定。仕様変更ではない)。
3. **nit:** TR:301 付近の `test_fresh_median_not_search_max_and_slow_endpoint_not_replaced` の終端 `score_sessions` を score session の fitness に追従させる。
4. 触らない: 上記 4 file 以外のすべて (特に `b5_generator_contrast.py`、`p3_s4_loop.py`、`tools/**`、docs)。`git add` / `git commit` / `git stash` / `git checkout` / `git reset` / `git rm` を実行しない。既存 test の期待値を変えない (上で名指しした fixture の是正だけ)。
5. **実走:** `cd <repo root> && PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B orchestrator/tests/test_b5_generator_contrast_report.py`、同 `test_b5_generator_contrast.py`、`python3 -B -c "import sys,pytest; sys.exit(pytest.main(['orchestrator/tests/test_p3_s4_loop.py','-q','-rf','-k','b5 or preflight or grammar']))"`。実走 nodeid・件数・結果を報告に列挙。
6. 報告は最終メッセージ本文。見出しは `##`。節: `## 変更の要約`、`## 新 test 一覧`、`## 実走結果`、`## 未了・懸念`、`## 総括`。
