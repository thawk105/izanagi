単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — 段 4 裁定 (プラン v2、変異 M1〜M5、計測の事前登録・land 条件)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s5-author-l-out.md、s5-author-p-out.md — 実装子の最終報告。
- 実装差分: wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy の commit `eb65d322f` (`git show eb65d322f` で読む)。対象 file `orchestrator/tests/test_s8b_oracle_driver.py`。
- 計測 probe (repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ (t2273lc_run_series.sh、t2273lc_run_measure.sh、t2273lc_run_warm.sh、t2273lc_ab_analyze.py、t2273lc_gate.conf)。改作元は /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/。
- 第 4 回診断: /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md。

## 目的 (レンズ A: 正しさ・変異の帰属・計測の妥当性)

自分たちの受入 test 基盤の高速化 wave の段 6 敵対レビューである。実装を守る側に立つな。根拠 (file:line) 付きで次を攻撃せよ。

1. **受理集合:** 共有 session 下で builder の fixture に届く output/ の集合・bytes・mode・mtime が、現行の直接複製と同じか。`copy_visible_output` の lock・marker・残骸処理・並行する別 key の builder・fork 子・`close()` による削除との競合に欠陥はないか。単独走の経路が変わっていないか。
2. **正例と変異:** 新規 test `test_t080_shared_base_visible_output_uses_one_snapshot` と既存実 builder 検査への assert が、段 4 で事前登録した M1〜M5 を**単一理由で**殺すか (他の assert・他層による mask、等価変異、fixture の過剰決定がないか)。とくに M1 の kill が `mock.patch.object(_bases, "copy_visible_output", ...)` の instance 属性差し替えで成立するか (builder が参照する `_T080_SHARED_BASES` がその `_bases` と同一物か、fork 子で成立するか)。test が実 repo を読まない・書かないか、tmp だけで閉じるか。
3. **既存 test への波及:** `t080_small_cache_builder` 系、`test_t080_shared_base_waits_for_builder_lock` の flock 観測、`bases.parent.glob("*/complete.json")`、consumer AST 検査 (helper consumer 20 node)、`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`、全件性検査 2 か所。
4. **計測 probe:** 改作後の run_series / run_measure / analyze が事前登録 (順序 A,B / B,A / A,B、門番、HEAD・clean の前後照合、無効対の取り直し、Δi・ri・両中央値、land 条件、5 分別判定、collection 一致) を正しく実装しているか。前回版から外した検査のうち、本 wave でも要るもの (測定の有効性に効くもの) を誤って外していないか。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う (焦点走を別途投入済み)。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` (番号付き。重大度 must-fix / should / nit、根拠 file:line、放置時に test 結果・受理集合・測定判定がどう変わるか 1 行、最小是正)
- `## 変異表` (M1〜M5: kill node、単一理由か、懸念)
- `## 総括` (3〜6 行。GO / 修正後 GO / NO-GO)
