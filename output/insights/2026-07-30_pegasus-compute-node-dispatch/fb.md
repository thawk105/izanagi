FIX-B の FB-1〜FB-5 を、実装子の所有範囲内で完了しました。docs 編集・commit・重い処理は行っていません。

主な変更は [guard_bash.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fb/hooks/guard_bash.py:171)、[test_hooks.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fb/orchestrator/tests/test_hooks.py:561)、[test_build_site_gate.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/pegasus-fb/orchestrator/tests/test_build_site_gate.py:249) です。

| Fix | 状態 | 対応 |
|---|---|---|
| FB-1 | closed | `python -m` の module 名を repo 内 `.py` / `__main__.py` へ解決。`tools.run_tests` は exact sanctioned、`tools.pegasus.exec_calibrate` は拒否。既存 `-m pytest` 拒否も固定 |
| FB-2 | closed | `env -S` / `--split-string` を再 token 化。`exec -a` の argv0 値を飛ばして実 head を判定。非重量 command の正例も追加 |
| FB-3 | closed | coverage 4 module の configure gate と build gate を別 node で検査。片方を削除しても後段 gate に mask されない構成 |
| FB-4 | closed | stdin JSON から `main()` を呼び、`site_policy.current_site()` が LOGIN の場合に rc=2 を検査 |
| FB-5 | closed | Ninja は読み取り専用 tool の閉集合だけ許可。`clean`・変更系・未知 tool は拒否。`ctest --show-only=<fmt>` は許可 |

許可・拒否境界は次のとおりです。

- LOGIN/SUSPECT で許可: `ninja -t targets/graph/query/deps/compdb` 等の読み取り、`ctest --show-only=json-v1`、exact sanctioned entry
- LOGIN/SUSPECT で拒否: module 形式の `exec_calibrate`、wrapper 内 pytest、`ninja -t clean/cleandead/recompact/restat`、未知 Ninja tool
- OTHER / `site=None`: 既存判定を維持。`test_bash_other_keeps_legacy_acceptance_bits` と既存 bypass 回帰群が通過
- `_MENTION_RE` / `_LEAF_RE` / `_TREE_LITERAL_RE` / `_BUILDERS` / `_INTERP` / `_PURE_READERS` は未変更
- coverage の `subprocess.run(..., check=True)` と `CalledProcessError` 伝播契約は維持

guard 自身の規則エラーについては、`_runtime_site()` の例外吸収と `main()` 外周の例外処理を維持しています。新しい `env -S` 解析失敗も例外を外へ投げず、その LOGIN/SUSPECT command だけを拒否します。したがって規則エラーで Bash session 全体を停止する構造にはしていません。一方、これは literal command 面の第二防壁であり、既存 docstring の既知限界は維持しています。

検査結果:

- `python3 -m pytest orchestrator/tests/test_hooks.py -q`
  - 全ファイル範囲: `44 passed, 1 skipped`
  - FB-1/2/4/5 node、OTHER 回帰、`test_bash_finding_bypasses_all_denied` を含む
- `python3 -m pytest orchestrator/tests/test_build_site_gate.py -q`
  - 全ファイル範囲: `8 passed`
  - 期待赤 node:
    - `orchestrator/tests/test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent`
    - `orchestrator/tests/test_build_site_gate.py::test_m11_coverage_build_gates_are_independent`
- 所有7ファイルの `python3 -m py_compile`: rc=0
- 所有範囲の `git diff --check`: rc=0

波及可能性の静的確認:

- `.claude/settings.json` が `guard_bash.py` の production consumer
- `s8a_trigger_freq.py` が `s8a_trigger_coverage._build` を共有。既存呼び出し互換性は維持
- `test_campaign.py` は `s3_lock_coverage.json` を消費するが、成果物 schema は変更なし
- `test_plain_runner_coverage.py` は新規テストファイルの自走 harness を走査する。`_run()` / `__main__` は存在するが、許可範囲外のため同 meta-test は未実行

## 総括

FB-1〜FB-5 はすべて実装・許可された対象テスト範囲で closed です。未達は、親所有の mutation 本走・焦点再レビュー・計算ノード全走・実 cmake build・`tools/run_tests.py`・commitです。初回の軽量 probe は shell 引用エラーで未実行のため、緑根拠には数えていません。