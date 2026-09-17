単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/stage4-ruling.md — 段 4 裁定・plan v2・変異事前登録。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/reviewA-out.md — 段 6 レビュー A (nit N1・N2・N3 の原文)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/reviewB-out.md — 段 6 レビュー B (nit 1 = AST pin の引数・分岐所属)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/focus1-driver.log — 変更 test file の単独焦点走 (65 passed、計算ノード)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 実装 (**編集しない**、読むだけ)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 編集対象。読めなければ即停止。

## 依頼 — 段 6 fix (nit 3 件、test file のみ)

**編集してよい file は `orchestrator/tests/test_t126_qualification_driver.py` だけ。** driver・docs・他 file は編集しない。commit しない。git の状態変更 (add / stash / checkout / reset) をしない。

段 5 実装子契約を継承する: 既存テストの期待値を変更しない (反転・緩和・skip・削除を禁じる。赤なら実装側が誤りとして報告して止まる)。受理集合に触れない。揮発 payload を期待値に焼き込まない。fixture へ現行 hash を差し込まない。

### 直す nit

1. **N1 (レビュー A・B 共通) — AST 配線 pin の射程:** `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message` を補強する。(a) `os._exit(_run_attestation_child(...))` の Call が `if is_child:` の body 直下 (`ast.If` で `test` が `ast.Name(id="is_child")`) にあること、(b) その Call の keyword 引数が exact に `{repo_root: source_root, contract: contract, capability: capability, relative: relative, stage: stage, round_index: round_index}` (`ast.unparse` した value 文字列で比較) であること、(c) `raise AttestationError(_attestation_rejection_message(...))` が `os.waitstatus_to_exitcode(status) != 0` を test に持つ `ast.If` の body 直下にあり、keyword が exact に `{capability: capability, relative: relative, attempt_dir: layout.attempt_dir}` であること。既存の「個数 1」assertion は残す。
2. **N2 (レビュー A) — `Path.exists` の全体 patch:** `test_t2683_parent_message_unreadable_sidecar_is_best_effort` の `damage == "exists"` 分岐で、`Path.exists` を無条件で失敗させる代わりに、sidecar の path (末尾が `.mismatch.json`) のときだけ `OSError` を上げ、それ以外は元の `Path.exists` へ委譲する wrapper にし、`monkeypatch.context()` で patch の範囲を `_t2683_message(...)` 呼出しに限定する。期待値は変えない。
3. **N3 (レビュー A) — M1/M5 の赤地点:** `test_t2683_mismatch_preserves_all_comparison_rows` と `test_t2683_empty_comparisons_writes_rejected_sidecar` で、`load_json_strict(sidecar)` の前に `assert sidecar.is_file()` (明示 assertion) を置く。他の assertion は変えない。

### 検査と報告

- 実走: `python3 -m pytest orchestrator/tests/test_t126_qualification_driver.py -q -p no:cacheprovider` を試みる。sandbox の hook 拒否や dispatch 障害で走らない場合は「実装済み・未実走」と書く (親が計算ノードで再走する)。`python3 -c "import ast; ast.parse(open('orchestrator/tests/test_t126_qualification_driver.py').read())"` 相当の構文確認は必ず行う。
- 完了報告に、変更した test 関数名と各 assertion の追加行、既存 assertion を変えていないことの申告、M10/M11 (production の raise 固定文言化・closure 子分岐のインライン復帰) が補強後の AST test で依然赤になる静的根拠を書く。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内)。続けて `## 変更一覧` (file:line)、`## 実走`、`## M10/M11 の赤根拠`、`## 懸念`。
