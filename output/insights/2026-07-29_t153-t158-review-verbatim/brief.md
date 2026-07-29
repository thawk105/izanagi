# 段 1 brief — [T-153](a-d) + [T-158] 機械化群

## scope
- T-153(a) run_tests.py の cwd 強制 (相対 target 吸収込み) / (b) O11 未 stage 削除の機械検出 /
  (c) O20 clean-tree gate のスクリプト化 / (d) F43 検収 (子成果物の最小サイズ・総括見出し) の機械化。
- T-158 run_tests.py への submodule 実体検査。(e) CAB 連続配置は scope 外 (ユーザー指定 a-d)。
- 機械化後、該当 prose (O11/O18 cwd/O20/F43 再発検知) を縮約 (親 docs-only、予算純減方向)。

## 確定済み裁定
- T-127 裁定「恒久対応は prose でなくテスト・機械検査を優先」。T-153/T-158 起票文 (worklog (28)(33))。
- D95: 実装面は Codex author 必須。親は docs のみ。
- ユーザー指示: 並行セッションで main が進んでもコンフリクト解消して main 取り込みまで行う。

## 前提実測 (2026-07-29、本 worktree)
- run_tests.py: subprocess.call に cwd= 不在 (tools/run_tests.py:377,379,441)、submodule 検査なし。
- fresh worktree の submodule 未初期化は `git submodule status` の `-` 接頭辞で判別可 (実測)。
- baseline 受入全走: 3165 passed / 18 skipped / 0 failed rc=0 (63.9s、共有ログインノード、rc のみ = F41)。
- G04 発火 artifact: F43 破損原文 194 bytes = output/insights/2026-07-28_t147-review-verbatim/ (実在)。
  既存被覆: test_run_tests_nproc.py 13 本 / test_run_tests_task_run.py 25 本に cwd 強制・submodule・
  未 stage 削除の被覆なし (grep 実測) — 純増分のみ scope。

## 不変条件
- 受理集合の変更は縮小方向のみ (fail-fast 追加)。baseline 緑を赤にしない。
- orchestrator 本体・freeze 成果物・output/ に触れない (O09/O10 不発の根拠)。docs は check_docs 予算内。

## provisional 裁定 (攻撃対象)
- (P1) T-158 は自動 init (git submodule update --init external/ccbench) + init 失敗時 fail-closed。
  根拠 = 小ツール自動導入の既定 (run_tests の xdist 自動導入と同型)。
- (P2) 未 stage 削除検査は full-suite 形 (受入全走) のみ発火、rc≠0 + `git add -A` 案内。
  明示 env (IZANAGI_ALLOW_UNSTAGED_DELETIONS=1) で警告付き bypass 可。
- (P3) (c) は tools/check_wave_startup.py 新設: HEAD=local main 照合・submodule 初期化・
  worktree 内 docs/handoff/ 残置なし・clean tree を検査し rc 集約 + 是正案内。
- (P4) (d) は tools/check_codex_output.py 新設: --min-bytes (既定 500) + 総括見出し regex 検査、rc≠0。

## 成果物・分割 (所有分離、重複なし)
- author A (codex): tools/run_tests.py + orchestrator/tests/test_run_tests_preflight.py (新規)。
- author B (codex): tools/check_wave_startup.py + tools/check_codex_output.py + 各テスト (新規)。
- 親: docs 縮約、統合 commit、変異 matrix、受入全走、記録、main 取り込み。

## 段構成
- 段 2 省略 (本 brief が file:line 方針を保持)。受理集合変更に該当するため敵対検証は省かない:
  段 3 相談 2 本 (レンズ = 偽緑偽赤/回避可能性、統合・互換/consumer) + 段 6 レビュー 2 本 + fix。
- 受入全走の実行場所 = 本 worktree (共有ログインノード、rc のみ記録)。

## G05 成果物影響 (未実装時)
- (a)(b)(T-158): cwd 由来・未 stage 削除・submodule 未初期化の偽赤が受入全走 rc を汚し、worklog の
  受入記録と wave GO/NO-GO 判定を誤らせる (42 本偽赤は (33)(45) で 2 回実測)。
- (c): 立ち上げ検査漏れ (F48/F50 型) が clean-tree gate の偽判定・handoff 消失を再発させる。
- (d): F43 型破損成果物を「所見なし」と誤読 → レビュー所見の喪失 = 受入判定の偽緑。
