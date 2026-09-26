## 所見

1. **must-fix** — [pipeline.py:2714](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2714): patch は検証後の `source_root` から取得する。反例は、build 時の source が A で、その後 trace 実行中に tracked file が B に変わる入力。verifier は A の固定済み snapshot で判定するが、inventory は B の patch を `complete` として保全する。**影響:** その inventory から組む R1 は異なる protocol source を検証し、評価結果が変わり得る。**代案:** opt-in 時に判定へ束縛した source の patch bytes を保持して保全へ渡す。少なくとも取得時の差が判明した inventory を `complete` にしない。裁定の「hash 不一致を gate にしない」も、この反例について再裁定が必要。

2. **should** — [test_t2853_trace_preservation.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:95): test は一時 repo を作るが、`ccbench_pin` は存在しない `deadbeef` のまま。**影響:** test が緑でも、記録した pin と patch から source を組む R1 手順は成立していない。**代案:** fixture の実 HEAD を evidence の pin にし、その checkout に復元 patch を適用して source を照合する。

3. **nit** — [test_t2853_trace_preservation.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/tests/test_t2853_trace_preservation.py:249): `subprocess.run` と `Path.read_bytes` の全体差し替えは、評価 fixture 内の別用途の Git 呼出しや verifier file 読取りも拾う。**影響:** fixture が変わると opt-in と無関係な偽赤になり得る。**代案:** 保全関数の呼出し境界で計測対象を絞る。現状で偽緑を作る根拠は見当たらない。

## 削除・縮小の候補

1. [pipeline.py:2694](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-archive-inventory-figure-redraw/orchestrator/campaign/pipeline.py:2694) の `repo_head` 用 Git 呼出しは既存の `_current_repo_head` に寄せられる。ただし現行の sanitized Git 環境を保つ引数追加が要るため、**起動箇所は減らず**、小幅な重複削減に留まる。
2. `_RepetitionExecutionOutcome.commit_count_witness` は parse-error 後にも witness を渡すために必要。既存 payload だけへの置換では値を失うので、削除候補にはしない。`source_digest._tracked_diff_sha256` も hash しか返さず、保全する patch bytes の取得は代替できない。
3. `verifier_invocation`・`tracked_diff_sha256`・`patch_bytes`・`patch_path` は段4裁定で指定された記録であり、この差分から削ってよいものはない。追加 test も指定された4本の範囲内。

## 総括

**NO-GO**。must-fix は、判定に使った source と保全 patch がずれても inventory が `complete` になる点。trace の復元先は `files[].archive_path`、元の argv の trace dir は `original_directory` から対応付けられる。静的レビューのみ実施し、pytest は実行していない。