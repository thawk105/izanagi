単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s5-author-A-prompt.md — **段 5 実装子 A の契約 (全文を継承する。commit しない・テストを走らせない・docs を編集しない・所有 file 以外を編集しない等の制約はすべてそのまま有効)**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s6-adjudication.md — **段 6 裁定 (本 fix の正本)。R5 と R6 だけが本 fix の対象**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s6-review-B.md — レビュー B (所見 4 と 7 が R5 / R6 の元)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py と orchestrator/tests/test_b5_contrast_launch.py — 所有 file。読めなければ即停止

## 作業 (fix A1)

1. **R5:** `orchestrator/tests/test_ccbench_spawn_sites.py` を base commit `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` と同じ内容に戻す (前回の実装子 A が足した launcher 用の process 起動目録 test とその補助を除く)。
   `git show 8fd2a2f5c775954d6a32cee019ac7ce276298e4d:orchestrator/tests/test_ccbench_spawn_sites.py` の bytes と一致させる。
2. **R6:** `orchestrator/tests/test_b5_contrast_launch.py` の schedule 検査の重複を整理する。`test_registered_schedule_llm_four_per_stage` は「各 (block, stage) の LLM job がちょうど 4 本」だけを検査し、
   `test_registered_schedule_six_orders_twice` は「各 workload で 6 順序が各 2 回」と「各 (workload, block) で LLM と各 baseline の先後が 2 対ずつ」を 1 回ずつ検査する (共通 helper を 2 node から呼ばない)。
   検査内容を弱めない (性質の数え上げは schedule 関数の出力から独立に行い、期待値を同じ算式で作らない)。他の test は変えない。

## 制約 (実装子 A の契約をすべて継承)

- **既存テスト (本 wave 以前から tracked の test) の期待値を変更しない。** 反転・緩和・skip・削除をしない。本 wave で新設した test (`test_registered_*` など) は R6 の範囲でだけ編集してよい。
- `tools/pegasus/admission_registry.json` は触らない (前回の変更は親が取り込まない)。launcher・driver・job body の production code は触らない。
- **`git commit` を一度も実行しない。** docs を編集しない。**テストを走らせない** (静的検査 `python3 -m py_compile` は可)。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更した箇所 (関数名・行)
2. `test_ccbench_spawn_sites.py` が base と bytes 一致したことの確認方法と結果
3. 静的検査の結果 (実行したコマンドと rc)
4. 変異 MA5〜MA8 がそれぞれどの node で落ちるはずか (MA6 は `test_registered_schedule_six_orders_twice` へ再照準)
5. 未実走であることの明記
最後に `## 総括` を置く。
