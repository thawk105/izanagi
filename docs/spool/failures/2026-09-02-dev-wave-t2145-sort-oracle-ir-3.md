---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2145-sort-oracle-ir
seq: 3
---

## 新規

### {{F:merge-resolution-whole-file-overwrite}}. 競合解消で子の file を丸ごと上書きし、相手側の変更を黙って捨てた [手順漏れ] [テスト代表性]

- 事象: local main (133 commit 先行) を取り込む際、`orchestrator/campaign/p3_s4_loop.py` の
  import 段落 1 箇所だけが競合した。親は競合解消を Codex `role=author` にやらせたが、
  子は**取り込み前 HEAD の clean な作業ツリー**で解決内容を書いた。親はその file を
  **丸ごと**マージ結果へ上書きし、main 側が同じ file へ入れていた変更 13 箇所
  (`knowledge_manifest` 関連) を捨てた。merge commit は競合なく成立し、
  静的な合成監査も「重複・打ち消し・受理集合を広げる前提はいずれも無い」と報告した。
  **マージ後の実走が 5 件の赤を出して初めて発覚した** (761 passed、本来は 766)。
- 根本原因: 「子に解決内容を書かせる」設計が、子の作業ツリーの base を取り込み前 HEAD に
  置いていた。その file は**競合ハンク以外にも相手側の変更を含む**ため、file 単位の適用は
  常に相手側を落とす。競合の単位はハンクであって file ではない。
- 恒久対応: 競合解消の適用は**ハンク単位**で行う。子に file 全体を書かせる場合は、
  子の作業ツリーを**マージ結果**に置く。それが hook (HEAD blob drift) で不可能なら、
  子には解決内容の**指示**を出させ、親はマージ結果の該当ハンクだけを編集する。
  取り込み後は必ずテストを実走する — 静的監査は本欠陥を検出できなかった。
- 再発検知: 取り込み commit の前後で、相手側 branch にしか無い識別子の出現数を数える
  (本件では `knowledge_manifest` が 13 → 0 になっていた)。マージ後の実走を省かない。

### {{F:merge-in-progress-worktree-blocks-codex-children}}. merge 途中の作業ツリーでは codex の子が stage 非依存で死ぬ [手順漏れ]

- 事象: 競合解消を子にやらせるため、merge 途中 (`--no-ff --no-commit`、`UU` あり) の
  worktree へ Codex `role=author` を投入したところ、prompt を読む前に rc=2 で死んだ。
  理由は `NG: Codex hook 配線の exact 検証に失敗: tools/pegasus/admission_registry.json:
  working bytes が HEAD blob から drift`。取り込みが持ち込んだ file が HEAD と食い違うためで、
  競合とは無関係の file だった。
- 根本原因: hook は HEAD blob 束縛 file の一致を起動条件にしている。merge 途中は定義上
  多数の file が HEAD と食い違うので、**あらゆる stage の子が起動できない**。
- 恒久対応: merge 途中の worktree へ子を投入しない。競合解消を子にやらせるときは、
  clean な作業ツリーを渡し、競合両側と自動 merge 結果を **repo 外の job dir へ射影して**読ませる。
- 再発検知: 子の投入前に対象 worktree が merge 途中でないことを確かめる
  (`.git/MERGE_HEAD` の不在、`git status --porcelain` に `UU` が無いこと)。

## 再発

### F57

- **再発: 2026-09-02 ([T-2145] 受入全走 2 走目)** — tip `e281804b4` の全走 (20166 collected) で
  `test_codex_worker_launch.py::test_manifest_is_appended_while_correlated_session_is_running`
  が 1 件落ちた (**1 failed / 20073 passed / 92 skipped**)。同 node は F57 に既載である。
  本 wave の差分は launcher 実装にも同 test file にも到達しない (全範囲の path 検索で 0 件)。
  **同一 tip の 1 走目では同 file が全件通っている** (そちらは別の 3 件が落ち、いずれも本 wave の
  設計の帰結として追随済み)。`DW-O18` により帰属しない。
  **新しい情報が 2 つある。**
  (1) `loadavg=(26.72, 19.58, 20.02)` で発火した。既載の 1 分平均は 15.05 / 12.67 / 12.92 / 17.42 で、
  **26.72 は既載の最大を大きく上回る**。5 分平均 19.58・15 分平均 20.02 も既載の最大 (4.83 / 4.03) の
  4 倍以上であり、**持続負荷がこの水準での発火は初出**である。発火時は他 wave の codex 子が
  16 本 (7 wave: `a1-pilot-sizing` 6 本ほか) 走っていた。
  (2) **単独再走が緑にならなかったのは初出である。** 既載の再発はいずれも
  「全走で赤、単独再走は緑」だったが、本件は同 file の単独再走が
  `test_thread_missing_after_grace_kills_process_group` (`FileNotFoundError` on pytest tmpdir)、
  `test_cumulative_limits_do_not_reset_between_attempts`、
  `test_authority_bound_job_rejects_prior_invalid_attempt` (いずれも launcher returncode mismatch)
  の**別 3 node**で赤になった。**赤の node が単独再走でも移動する**ことを示し、
  「再走すれば緑が取れる」という運用上の前提がこの負荷帯では成り立たないことの直接の証拠になる。
  恒久対応は既載のまま変えない。
