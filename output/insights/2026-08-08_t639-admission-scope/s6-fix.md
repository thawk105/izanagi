段 6 fix を指定範囲内で実装しました。commit・stage は行っていません。pytest は dispatch 基盤 rc=16 のため「実装済み・未実走」です。

## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | partial | 非 Pegasus `local-ok` を deny sentinel に変更し、`local_ok_paths` を Pegasus 配下へ限定。[guard_bash.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:275)、[guard_bash.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:604)。lookup 強化と二重汚染 E2E を追加。[test_hooks.py:2011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:2011)、[test_hooks.py:2025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:2025) |
| F2 | partial | detector を fallback 集合から生成し、5 綴りを集合駆動で検査。[guard_bash.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:202)、[test_hooks.py:2260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:2260) |
| F3 | partial | 綴りごとに独立 root で fixture 作成・source 変異・subprocess 実行する形へ修正。全5綴りで exact rc=2 assertion を保持。[test_hooks.py:2609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:2609) |
| F4 | partial | class・evidence を含む完全行を一意 anchor にし、`count()==1` を維持。[test_check_docs.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_check_docs.py:1082) |
| F5 | closed | 下記 M1〜M10 の各 anchor を静的スクリプトで検査し、すべて `count=1`。F5 用の production 変更はなし。 |

`partial` は pytest nodeid が未実走であるためです。手動 smoke では、二重汚染時の LOGIN/SUSPECT deny・OTHER allow、および全5綴りの内部例外 rc=2 を確認しました。

## 検査結果

実走を試みた nodeid:

```text
orchestrator/tests/test_hooks.py::test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree
orchestrator/tests/test_hooks.py::test_bash_non_pegasus_local_ok_corruption_cannot_borrow_sanctioned_allow
orchestrator/tests/test_hooks.py::test_bash_non_pegasus_fallback_set_matches_registry_projection
orchestrator/tests/test_hooks.py::test_bash_non_pegasus_raw_mention_detector_covers_fallback_spellings
orchestrator/tests/test_hooks.py::test_bash_main_internal_error_conservatively_rejects_non_pegasus_admission_mentions
orchestrator/tests/test_hooks.py::test_bash_non_local_registry_entry_overrides_sanctioned_path
orchestrator/tests/test_check_docs.py::test_admission_non_pegasus_registry_entry_requires_projection_only
```

`tools/run_tests.py` は `qstat -Q preflight rc=1`、rc=16 で、テスト本体は0件実行でした。直接 pytest には迂回していません。

- `python3 tools/check_docs.py`: rc=0、finding なし
- `python3 tools/check_codex_agents.py`: rc=0
- 変更対象4ファイルの `py_compile`: 成功
- `git diff --check`: 成功
- production smoke: 成功
- pytest: **実装済み・未実走**

## F5 変異 anchor

すべて逐語一致件数は1です。

M1 — [pegasus_admission_registry.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus_admission_registry.py:99)

```python
        if not _is_canonical_repo_relative_path(path):
            raise AdmissionRegistryError(f"registry path is invalid: {path!r}")
```

M2 — [pegasus_admission_registry.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus_admission_registry.py:105)

```python
        if (not path.startswith("tools/pegasus/")
                and entry["class"] == "local-ok"):
            raise AdmissionRegistryError(f"registry path is invalid: {path!r}")
```

M3 — [guard_bash.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:606)

```python
    entry = _PEGASUS_ADMISSION_REGISTRY.get(path)
    if entry is not None:
```

M4 — [guard_bash.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:608)

```python
        if (path.startswith("tools/pegasus/")
                or entry["class"] != _PEGASUS_LOCAL_OK):
            return entry
        # wrapper と sanctioned 導出が同時に壊れても allow に反転させない。
        return _PEGASUS_UNREGISTERED
```

M5 — [guard_bash.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:197)

```python
_NON_PEGASUS_ADMISSION_FALLBACK_PATHS = frozenset({
    "tools/claude_session_ledger.py",
})
```

M6 — [guard_bash.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:614)

```python
    if path in _NON_PEGASUS_ADMISSION_FALLBACK_PATHS:
        return _PEGASUS_UNREGISTERED
```

M7 — [guard_bash.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:284)

```python
        sanctioned_paths = frozenset(
            (_NON_PEGASUS_SANCTIONED_PATHS
             - non_local_paths
             - _NON_PEGASUS_ADMISSION_FALLBACK_PATHS)
            | local_ok_paths)
```

M8 — [guard_bash.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:617)

```python
    if path == "tools/pegasus" or path.startswith("tools/pegasus/"):
        return _PEGASUS_UNREGISTERED
```

M9 — M6 と同じ一意 block。[guard_bash.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:614)

```python
    if path in _NON_PEGASUS_ADMISSION_FALLBACK_PATHS:
        return _PEGASUS_UNREGISTERED
```

M10 — [guard_bash.py:1656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:1656)

```python
        if (_MENTION_RE.search(raw)
                or _PEGASUS_RAW_MENTION_RE.search(raw)
                or _NON_PEGASUS_ADMISSION_RAW_MENTION_RE.search(raw)):
```

## 波及可能性

- `_pegasus_admission_entry()` の所有外 caller は `_script_targets()`、`_executor_output_violation()`、`_baseline_first_token_violation()`、`_heavy_segment_violation()`。[guard_bash.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:957)
- `_SANCTIONED_PATHS` は `_script_targets()`、`_is_sanctioned()`、executor 判定が共有するため、将来の非 Pegasus entry 追加時も site matrix の再確認が必要。
- raw detector は `main()` の内部例外経路だけに影響し、`decide()` 正常系の受理集合は変更しない。
- 共有 fixture は `_LOADER_FIXTURE_SOURCES`、`_prepare_guard_fixture()`、`_run_guard_subprocess()`。[test_hooks.py:1681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:1681)
- 所有外 consumer は `tools/check_docs.py` の canonical loader／投影検査と、親所有の registry・runbook・README。今回はそれらを編集していない。

## 総括

- F1〜F4 は実装済みだが pytest 未実走のため `partial`、F5 は一意性実測済みで `closed`。
- `check_docs.py` と Codex 構成検査は rc=0、手動 smoke も成功。
- pytest 7 nodeid は dispatch infrastructure rc=16 のため0件実行。
- 親には上記 anchor を mutation harness へ反映し、焦点 nodeid を再走してもらう必要がある。