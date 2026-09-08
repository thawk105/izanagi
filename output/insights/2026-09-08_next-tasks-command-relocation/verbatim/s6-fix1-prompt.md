単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md (親 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/prompt-author.md (段 5 実装子契約。「役割と境界」節を全文継承する。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/focus-run.log の 189〜345 行 (焦点走の赤 4 件の本文。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_ai_provenance.py の 117〜128 行と、`_known_violation_group_stdout(53, 2)` の 4 箇所 (読めなければ即停止)

## 役割と境界 (段 5 契約の継承)
あなたは Codex role=author の fix 子である。作業 root は
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908 だけ。HEAD は d42f2bec5、tree は clean。
禁止: commit、git add / rm / reset / stash / merge / checkout、docs (.md) の編集、`.codex/` と `.claude/` 配下の編集、
所有外 file の編集、`tools/run_tests.py` と `python -m pytest` の起動、ネットワーク。
所有 file は `orchestrator/tests/test_check_ai_provenance.py` の 1 つだけ。
既存テストの反転・緩和・skip・削除・xfail 化は禁止。fixture への現行 hash 差し込みや揮発 payload の焼き込みも禁止。

## 親の裁定 (何を直すか、なぜ期待値の更新が許されるか)
焦点走 (計算ノード job 982982) で `orchestrator/tests/test_check_ai_provenance.py` の 4 node が赤:
- test_audit_history_empty_range_returns_zero_findings
- test_unregistered_malformed_finding_remains_rc1_with_production_registry
- test_forward_correction_unrelated_history_remains_native_valid
- test_ledgered_3f2c43d7580b_is_known_and_rc0
4 件とも差分は同一で、helper `_known_violation_group_stdout(53, 2)` が出す
`known-violations-post-baseline=2` に対し、実 stdout が `post-baseline=3`。
原因は commit 48837186c が `tools/known_violations/` へ c12e25078 の既知違反 (D742 baseline に無い key) を
1 file 追加し、production 台帳の post-baseline 母集団が 2 → 3 になったこと。
この helper は production 台帳の母集団を pin して未登録の drift を検出するためのものであり、
台帳が正規の登録で 1 件増えたときに pin を真値へ動かすのは、テストの反転・緩和ではなく pin の追従である。
irreversible-history (53) は D742 baseline 側の件数で変わらない。

## 作業
1. 4 箇所の `_known_violation_group_stdout(53, 2)` を `_known_violation_group_stdout(53, 3)` に変える。それ以外は変えない。
2. 他に production 台帳の件数・集合を pin する assertion (file 数 55、post-baseline 2 等の literal) が同 file に無いか grep で確かめ、
   あれば変更せずに報告する (親が裁定する)。
3. `git diff --stat` が 1 file / 4 行変更であることを示す。
4. pytest は起動できないので実走は親が行う。「実装済み・未実走」と正直に書く。
   代わりに `PYTHONPATH=. python3 -c "import sys; sys.path.insert(0,'tools'); import check_ai_provenance as c; r=c._known_violation_registry(); print(len(r))"`
   で台帳の読取が例外なく通ることだけ確かめる。

## 総括
最後に `## 総括` 節を必ず置く: 変更 file と行数、変えた literal、見つけた他の pin (あれば)、未実走の明記。
出力に結合文字 U+0300〜U+036F を使わない。
