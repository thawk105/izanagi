実装は完了しました。docs・commit には触れていません。pytest は計算ノードへの dispatch 障害により未実走なので、`closed` や全緑とは申告しません。

## 総括

### (a) 変更した関数と行

- [hooks/guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:183)
  - 三値 + `reason` / `primary_gate` / `evidence` の admission registry。
  - `_SANCTIONED_PATHS` を `local-ok` から導出（324行）。
  - registry lookup と未登録 Pegasus の deny（577行）。
  - Python prefix parser（588行）。
  - `-m` module parsing・script executor 判定（647、691行）。
  - shell prefix parser（739行）。
  - `_script_target` の一般則（774行）。
  - pytest module identity 正規化（810行）。
  - `_provenance_script_borrow` は維持（864行）。
  - registry class に基づく拒否（896行）。

- [orchestrator/tests/test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:726)
  - `-m`、script executor、静的 reader、Python/shell option matrix。
  - LOGIN/SUSPECT 全 entry bit、OTHER/COMPUTE 不変（1043、1052行）。
  - 未登録 nested deny（1059行）。
  - 再帰 inventory 同期 meta-test（1066行）。保証範囲は inventory 同期だけと明記。
  - 既存の sibling pin と `exec_calibrate.py` anti-glob pinは維持。

依頼上は18本でしたが、再帰条件では `probes/` の4実行体も該当して実 inventory は22本でした。4本は証拠なし昇格をせず `unknown` とし、現行 DENY を維持しています。

### (b) 受理集合の変化

現在 ALLOW → DENY:

- `python -m pytest.__main__ ...`、`python -m _pytest.main ...` と、その密着・bundle・版付き形。
- `-mpytest` / bundle pytest が `tools/run_tests.py` または既存5本の `local-ok` pathを借用する形。
- 分離形の `cProfile` / `profile` / `pdb` / `trace` / `runpy` / `timeit` / `coverage run` が、Pegasus の非 `local-ok` scriptを実行する形。
- `python -W <value> <Pegasus script>`、`python -X <value> <Pegasus script>`。
- `bash -O <value>`、`-o <value>`、`--rcfile <value>`等で非 `local-ok` scriptを隠す形。

現在 DENY → ALLOW:

- `python -mpy_compile <Pegasus path>`、`-mjson.tool`、`-mcompileall` の密着・bundle形。pathはdataとして扱います。
- `python -c <code> -m pytest`、`python -c <code> <Pegasus path>`。`-c`後はdataです。

Pegasus entryの直接実行 bit自体は変更していません。既存5本だけが `local-ok`、残りはDENYです。cwd/symlink、`env -S` grammar、3段shell、`systemd-run`、入力cap、`pytest -h/--co`はscopeどおり未変更です。

### (c) 検査結果

成功:

- `python3 -m py_compile hooks/guard_bash.py orchestrator/tests/test_hooks.py`
- 追加テストと主要既存pinの軽量直接呼出し: 19関数 PASS
- 3逐語JSONとのbit比較: 意図した反転だけを確認
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0

pytest実走:

- 指定範囲: `orchestrator/tests/test_hooks.py`
- 実行要求: `python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q`
- 結果: `qstat -Q preflight rc=1` により dispatch infrastructure failure、wrapper rc=16
- 実走nodeid: 0件

Pegasusログインノード上のpytestへはフォールバックしていません。

### (d) 所有外への波及可能性

- `.claude/settings.json` から呼ばれる production hook の拒否理由がclass別文言になります。exit bit契約は維持しています。
- `tools/run_tests.py` と `tools/check_ai_provenance.py` は非Pegasus sanctioned pathとして従来どおりです。
- 新しいPegasus実行体は、registryへ登録しなければruntime DENYかつinventory meta-test赤になります。
- private parser/helperの所有外Python callerは静的検索で見つかりませんでした。
- runbook、decisions、worklogなどの説明側は親による追随が必要です。

### (e) 実装できなかった項目

- pytest実走のみ未完了です。原因は計算ノードdispatchのscheduler preflight障害です。
- docs編集とcommitは段5 author契約およびユーザー指示により実施していません。
- 裁定でscope外とされた項目は意図的に実装していません。