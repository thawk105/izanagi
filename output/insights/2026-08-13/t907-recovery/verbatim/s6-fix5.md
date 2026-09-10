## 総括

1. 合成 runner の出力を次へ統一しました。

`--collect-only` 経路:

```text
orchestrator/tests/test_known.py::test_known
1 test collected in 0.01s
```

単独 nodeid 再走経路:

```text
=== short test summary info ===
FAILED orchestrator/tests/test_known.py::test_known - synthetic known red
=== 1 failed in 0.01s ===
```

nodeid 無指定の初回受入走も後者と同じ出力です。変更箇所は [test_dev_wave_land.py:938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_land.py:938) だけです。

2. 対応する checker 契約:

- `_COLLECTION_FOOTER`（[check_acceptance_reds.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/check_acceptance_reds.py:47)）の単数形に footer が full-match。
- `_complete_collected_nodeids`（同:860）は footer が一意、selected=1、nodeid が対象 path 配下、件数一致として受理。
- `parse_pytest_log`（同:549）は、一意な short-summary header、summary 内の `FAILED` 行、一意な terminal summary、failed 件数=1 を確認。
- `_rerun_output_proves_red`（同:905）は解析結果を `_selector_from_collection`（同:488）へ渡し、` - synthetic known red` を理由 suffix として対象 nodeid に exact-match。
- `_default_node_runner`（同:920）は、これにより rc=1 の「matching FAILED/ERROR outcome」分岐を満たします。

3. 判定関数への直接入力結果:

```text
collection_rc=0
collected=('orchestrator/tests/test_known.py::test_known',)
rerun_rc=1
parsed=('orchestrator/tests/test_known.py::test_known - synthetic known red',)
proves_red=True
selected=('orchestrator/tests/test_known.py::test_known', 'orchestrator/tests/test_known.py::test_known')
```

対象テストの AST から合成 runner 本文を直接取り出し、実際に各引数で起動した stdout を判定関数へ渡しました。nodeid 無指定出力も `parse_pytest_log` に受理されています。

4. 残存契約がないと判断した範囲:

- regex 定義: 29–54
- local/dispatch stdout の選択: 410–437
- pytest summary/outcome 解析: 440–607
- collection・単独再走: 860–1009
- probe の rc 解釈: 1222–1258
- 非帰属分類: 1418–1450

合成 runner は dispatch control 行を出さないため、`_authoritative_command_stdout` の local stdout 分岐に入ります。collection、初回受入走、単独再走という全出力経路を確認済みです。

5. 実行した検査:

- checker 判定関数への直接入力: 成功
- `py_compile`: 成功（bytecode 書き込みは抑止）
- `git diff --check`: 成功
- NFC・結合文字検査: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- `git status --short`: 指定ファイルのみ変更

pytest E2E は指示どおり未実走です。状態は「実装済み・未実走」で、親の計算ノード実走が必要です。姉妹試験、共有 fixture、checker、waiter、land、docs、assert は変更していません。commit も作成していません。