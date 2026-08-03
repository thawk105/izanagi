親の診断と一致しました。実装欠陥ではなく、main 側 fake fold が生成した不正な receipt が原因です。

[fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:1502) を実 planner と同じ 5 field・canonical JSON 形式へ修正し、実物 `validate_spool_layout()` を通ることも assertion で固定しました。

| 所見 | 状態 | 対応 |
|---|---|---|
| `- main-side fold` が receipt schema 違反 | closed | canonical JSON receipt に変更 |
| main fold・merge・両経路という E2E 意図 | closed | setup、merge、no-fold/declared-fold 分岐、期待値を維持 |
| R3 cutoff 配線の退行検出 | closed | 下記の静的追跡で維持を確認 |
| pytest による修正後確認 | partial | Pegasus ログインノードのため未実走 |
| 新たな回帰 | regressed なし | 実装・他テストは未変更 |

R3 は次の理由で維持されています。

- no-fold 経路は [`trusted_main_cutoff_sha=tested_main`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1826) を通ります。
- declared-fold 経路は最終検証の [`trusted_main_cutoff_sha=trusted_main_cutoff_sha`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1517) を通ります。
- どちらかを削除すると merge commit の全 parent が走査され、loser 側 parent との差分に main 側 `FOLDED.md` 変更が現れて `landed-fold-owned-path` となり、対応する loop 分岐の `landed` assertion が赤になります。

確認結果:

- `git diff --check -- orchestrator/tests/test_dev_wave_land.py`: 成功
- `python3 -m py_compile orchestrator/tests/test_dev_wave_land.py`: 成功
- 未実走 nodeid: `orchestrator/tests/test_dev_wave_land.py::test_main_fold_resync_reaches_no_fold_and_declared_fold_consumers`
- docs 編集・commit・`tools/dev_waves/git_state.py` の追加編集なし

## 総括

- 原因は親診断どおり、不正な main-side receipt fixture。
- fixture を実 planner と同じ canonical JSON 形式へ修正。
- 実物 layout validator の assertion を追加。
- E2E の main fold、merge、両 cutoff 経路を維持。
- R3 の退行検出も静的に維持確認済み。
- pytest は Pegasus 規律により未実走。