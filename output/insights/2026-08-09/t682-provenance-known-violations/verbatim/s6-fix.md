## 総括

| 所見 | 判定 | 根拠 |
|---|---|---|
| C-01 | partial | selector と期待診断を分離し、value 側を `finding value` に修正。[test_check_ai_provenance.py:1726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1726)。production 診断は維持。[check_ai_provenance.py:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:568)。pytest 未実走のため closed にしない。 |
| D-01 | partial | C-01 と同じ診断 oracle 不一致を修正し、既存 node ID を明示的に維持。[test_check_ai_provenance.py:1756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1756)。pytest 未実走。 |
| C-02 | partial | 拒否 category を `Cc/Cf/Zl/Zp` に拡張。[check_ai_provenance.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:143)、[check_ai_provenance.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:468)。指定文字の note/value 負例を追加。[test_check_ai_provenance.py:1726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1726)。pytest 未実走。 |

変更したファイル:

- [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py): `Cf/Zl/Zp` を拒否集合へ追加。
- [orchestrator/tests/test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py): 診断期待を分離し、U+00AD、U+2060、U+2028、U+2029、tab、LF、DEL の両 field 負例を追加。

pytest 試行:

- `...::test_registry_rejects_control_and_zero_width_characters` 相当を `-k` 指定: rc=16、pytest 開始前に停止。0 passed / 0 failed。
- `orchestrator/tests/test_check_ai_provenance.py` 全体: rc=16、pytest 開始前に停止。0 passed / 0 failed。
- 原因: sandbox 上で `qstat -Q` が `Unknown user-id`、headroom 台帳も更新不能となり、dispatch preflight が失敗。
- 直接 pytest を起動する禁止迂回はしていない。

補助検証では、負例 matrix 26/26 の拒否診断一致、production registry 30 件の検証成功、`git diff --check`、両ファイルの AST parse 成功を確認した。

追加 23 entry の `note` / `expected_finding_value`、計46 fieldを `Cc/Cf/Zl/Zp` で走査し、該当は **0件**。登録値は変更していない。

未確認は pytest の実走結果と全ファイル回帰。親環境での再実走が必要。テストの新設・改名はなく、meta-test の追加対象はない。既存の probe `.py` 削除・`.md` 新設は段5の先行差分であり、今回は触れていない。docs 編集、git add、commit、branch 操作は行っていない。