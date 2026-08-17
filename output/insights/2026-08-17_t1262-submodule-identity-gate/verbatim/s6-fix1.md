## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | `os.walk(onerror=...)` の例外を検査理由へ変換し fail-closed 化。実権限と注入経路の両方を扱うテストを追加 |
| F2 | closed | root は inventory 前、submodule は worktree Git 前に object format と local config を検査 |
| F3 | closed | filesystem probe 由来の core 3 key を許可。`init.templateDir` は key 名を含めて拒否 |
| F4 | closed | source 限定で submodule 4 key と `user.name/email` を追加。`core.fsmonitor` は引き続き拒否 |
| F5 | closed | root preflight failure は即時拒否。submodule failure は理由を集約し、その repository の内容検査のみ省略 |
| F6 | closed | `_git_dir` と `_direct_submodules` に `--no-replace-objects` を追加 |
| F7 | closed | oracle と submodule row の exact key 集合を literal で固定 |
| F8 | closed | single-reason helper を tuple exact equality に強化 |
| F9 | closed | verify 単位の preflight cache を導入し repository ごと一回に限定 |
| F10 | closed | F1、F2、F4 の正負・順序テストを追加。ただし post-fix 実走は基盤障害で未実走 |
| RA3 | closed | 不採用裁定を維持。source root への allowlist 適用は追加していない |

`partial`、`regressed` はありません。ただし状態は実装と静的検査による判定で、post-fix pytest の緑は未確認です。

## 変更内容

- [tools/codex_reasoning_ab.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:715): source submodule preflight の cache と source 限定 allowlist を追加。
- [tools/codex_reasoning_ab.py:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:773): `_git_dir`、`_direct_submodules` の replace object 無効化。
- [tools/codex_reasoning_ab.py:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:926): submodule の worktree Git より前に preflight。赤なら内容検査を開始しない。
- [tools/codex_reasoning_ab.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1118): inventory で赤い repository の再帰を省略。
- [tools/codex_reasoning_ab.py:1389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1389): static・source dynamic allowlist を拡張。
- [tools/codex_reasoning_ab.py:1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1487): walk error の fail-closed 化。
- [tools/codex_reasoning_ab.py:1637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1637): repository 単位 preflight と cache を実装。
- [tools/codex_reasoning_ab.py:1706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1706): 赤い submodule の理由を集約し内容検査を省略。
- [tools/codex_reasoning_ab.py:1910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1910): closure 検査でも cache と検査省略を共有。
- [tools/codex_reasoning_ab.py:2140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:2140): root preflight を inventory より前へ移動。
- [orchestrator/tests/test_codex_reasoning_ab.py:2155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:2155): test helper も verify と同じ preflight cache を共有。
- [orchestrator/tests/test_codex_reasoning_ab.py:2172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:2172): single-reason assertion を exact equality 化。
- [orchestrator/tests/test_codex_reasoning_ab.py:2459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:2459): F1からF10の回帰 node を追加・拡張。

## 追加・変更したテスト

新設・直接変更した nodeid:

- `orchestrator/tests/test_codex_reasoning_ab.py::test_verify_snapshot_oracle_and_submodule_row_key_sets_are_literal`
- `...::test_submodule_content_identity_reasons_rejects_walk_error`
- `...::test_submodule_content_identity_reasons_rejects_forbidden_config_key`
- `...::test_submodule_content_identity_allows_filesystem_probe_config_keys`
- `...::test_verify_snapshot_root_preflight_precedes_inventory`
- `...::test_verify_snapshot_submodule_preflight_skips_worktree_git_and_aggregates`
- `...::test_verify_snapshot_runs_each_repository_preflight_once`
- `...::test_submodule_identity_discovery_git_calls_disable_replace_objects`
- `...::test_init_submodules_from_local_source_allows_source_only_config_keys`
- `...::test_init_submodules_from_local_source_rejects_unexpanded_source_key`

single-reason helperの exact 化により、既存の verify-level rejection node 15件も強化されています。対象は empty index、blob mismatch、index/HEAD mismatch、rogue admin、ignored extra、replacement ref、admin symlink、external common-dir、symlink payload、実行 bit、CRLF、intermediate symlink、post-seal config、root config、grandchild change の各 nodeです。

## 実走結果

- `git diff --check -- tools/codex_reasoning_ab.py orchestrator/tests/test_codex_reasoning_ab.py`: rc=0
- 両 file の Python AST parse: rc=0
- 焦点走: 上記10 nodeid selectorを、`FORCE_COLOR` / `COLORTERM` を外して `tools/run_tests.py` から複数回試行
- 結果: rc=16。毎回 `qstat -Q preflight rc=1` となり、pytest 起動前に Pegasus dispatch infrastructure failure
- したがって全追加・変更 node は「実装済み・未実走」。緑とは報告しません
- 親提示の `603 passed / 21 skipped` は修正前の証拠であり、post-fix 結果には数えていません

## 波及と残件

repo 全体の静的検索では、変更した private helper の所有外 Python caller はありませんでした。内部 caller は snapshot build、relocation、inventory、closure、`verify_snapshot` に限定されています。

共有 fixture では `_synthetic_verify_snapshot_with_submodules`、`_synthetic_nested_submodule_snapshot`、`_synthetic_verify_snapshot_spec`、`_clone_without_submodules` が影響範囲です。consumer 側では `test_real_repo_serialization.py`、`conftest.py`、growth-hold inventory が同 test file の real fixture nodeを列挙しますが、helper を直接呼びません。

親側で必要な残件は、queue 復旧後の焦点走と全受入、変異走行、記録、commitです。docs と commit は変更しておらず、作業木の変更は指定された2 fileだけです。

## 総括

F1からF10を実装し、RA3の不採用境界も維持しました。  
walk error、preflight順序、理由集約、allowlist、重複実行を production 側で閉じています。  
oracle schemaは exact key集合で固定し、path依存 golden literalは追加していません。  
静的検査は通過しましたが、Pegasusのqueue preflight障害によりpost-fix pytestは未実走です。