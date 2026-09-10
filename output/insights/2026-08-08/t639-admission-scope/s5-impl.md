実装は完了しました。変更は指定された 5 ファイルだけで、docs 編集・stage・commit は行っていません。

## 受理・拒否挙動

| 対象 | before | after |
|---|---|---|
| `_validated_document()` | `tools/pegasus/` 外の全 key を拒否 | canonical repo 相対 path を受理。ただし非 Pegasus `local-ok` は拒否し、`unknown` / `dispatch-required` のみ受理 |
| `_is_canonical_repo_relative_path()` | 存在せず | 非空 `str`、相対 path、`..` component・後置 `/`・`\`・Unicode `Cc` なし、`normpath` 同値を要求 |
| `_is_canonical_admission_path()` | 旧名 `_is_canonical_pegasus_path()`。Pegasus prefix 必須 | loader と同じ canonical path 条件へ一般化。wrapper は別途、非 Pegasus `local-ok` を拒否 |
| `_load_pegasus_admission_registry()` | 非 Pegasus key で全 registry が縮退。sanctioned は固定二本＋Pegasus `local-ok` | deny class の非 Pegasus key を受理。非 local path と fallback path を sanctioned から差し引く。load 失敗時も同じ差し引き |
| `_pegasus_admission_entry()` | 非 Pegasus は常に `None` | registry-first。非 Pegasus deny class は entry、fallback exact path は未登録 sentinel、その他の非 Pegasus は `None`。直接 patch された非 Pegasus `local-ok` は許可しない |
| `_heavy_segment_violation()` | Pegasus entry のみ admission 診断 | Pegasus の既存文言は維持し、非 Pegasus entry/fallback は別の admission 文言で拒否 |
| `main()` | 内部例外時、ledger の raw mention は rc=0 | slash/module 両綴りを検出し exact rc=2 |
| registry | ledger は未登録。全 site allow | ledger=`unknown` を追加。LOGIN/SUSPECT deny、OTHER/COMPUTE allow |
| 未登録非 Pegasus | 全 site allow | 全 site allow のまま |
| 既存 Pegasus entry／未登録閉包 | class に応じた既存挙動 | 変更なし。deny→allow の反転なし |

逐語維持指定の lookup テスト、`outside-path`、`loader-outside-local-ok`、未登録 nested、sanctioned 導出は変更していません。変更した既存期待面は inventory の Pegasus key 絞り込みと stale `24` 表記、および新規 registry entry の literal golden 追加です。

## 静的な波及範囲

`_SANCTIONED_PATHS` の全 reader は次のとおりです。

- production: `_script_targets()`、`_is_sanctioned()`、`_executor_output_violation()`
- tests: failure 縮退集合、P4 sanctioned 衝突、新旧 Pegasus sanctioned 導出、fetch/provenance exact-path 検査

`_pegasus_admission_entry()` の全 caller は次のとおりです。

- production: `_script_targets()`、`_executor_output_violation()`、`_baseline_first_token_violation()`、`_heavy_segment_violation()`
- tests: 非 subtree `local-ok` の defense-in-depth 直接検査

所有外の production consumer は [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/check_docs.py:2348) の canonical loader と、projection／unknown／measured／README 各検査です。共有 fixture では `_PEGASUS_EXPECTED_CLASSES`、`_PEGASUS_EXPECTED_ENTRIES`、そこから導出される `_PEGASUS_DIRECT_COMMANDS`、registry failure matrix が ledger を消費します。P4 用に `_LOADER_FIXTURE_SOURCES` へ独立 synthetic loader を追加しました。check_docs の共通 synthetic baseline は変更せず、新規テスト内の複製だけを変更しています。

## 検査結果

- `py_compile`：変更した Python 4 ファイルで成功。
- `git diff --check`：成功。
- production smoke：registry 29 件、ledger の site matrix=`False/False/True/True`、未登録非 Pegasus=`True/True/True/True` を確認。
- `python3 tools/check_codex_agents.py`：rc=0。
- `python3 tools/check_docs.py`：期待どおり次の 1 finding のみ。

```text
runbook §7.0 投影表が registry と集合完全一致しない —
registry_only=[('tools/claude_session_ledger.py', 'unknown',
'unmeasured; unbounded input surfaces remain')], runbook_only=[]
```

それ以外に観測した赤は以下です。

- 新規・関連・meta-test の焦点 nodeid 群：`tools/run_tests.py` が dispatch を選択後、`qstat -Q preflight rc=1`、rc=16。テスト本体は 0 件実行。
- `test_hooks.py`＋`test_check_docs.py` の `--collect-only`：同じ理由で rc=16、collection 未実行。

したがって pytest と collection meta-test は **実装済み・未実走** です。直接 pytest への迂回はしていません。

## 変異 anchor

| 変異 | 実装後 anchor |
|---|---|
| M1 loader を Pegasus prefix 限定へ戻す | `tools/pegasus_admission_registry.py:99` |
| M2 非 Pegasus `local-ok` 禁止を削除 | `tools/pegasus_admission_registry.py:105` |
| M3 registry-first を旧 `None` へ戻す | `hooks/guard_bash.py:588` |
| M4 lookup class guard を削除 | `hooks/guard_bash.py:590` |
| M5 fallback literal から ledger を削除 | `hooks/guard_bash.py:197` |
| M6 fallback sentinel を `None` にする | `hooks/guard_bash.py:594` |
| M7 sanctioned の非 local 差し引きを削除 | `hooks/guard_bash.py:266` |
| M8 Pegasus 未登録 sentinel を `None` にする | `hooks/guard_bash.py:597` |
| M9 fallback 判定を `tools/` prefix へ拡大 | `hooks/guard_bash.py:594` |
| M10 raw mention から fallback を外す | `hooks/guard_bash.py:1636` |

## 総括

- 非 Pegasus admission は exact 登録された deny class のみに拡張し、許可集合は広げていません。
- 指定 5 ファイルのみ変更し、docs・stage・commit は未実施です。
- check_docs の赤は親 docs 未 land による予定済み 1 件だけです。
- pytest／collection は dispatch infrastructure rc=16 のため実装済み・未実走です。