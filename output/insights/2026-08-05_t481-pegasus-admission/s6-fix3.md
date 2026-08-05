## 総括

実装済みです。編集は指定された 2 ファイルだけで、docs 編集・commit は行っていません。

### 変更箇所

- [guard_bash.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:715)
  - executor の出力 option を target 決定前だけ解析。
  - `cProfile/profile -o|--outfile` が registry/sanctioned path を指す場合は拒否。
- [guard_bash.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:753)
  - `--help` / `--report` を program より前だけ非実行 mode と判定。
  - `pydoc -n/-p/-b/-w` の非実行 mode を反映。
- [guard_bash.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:840)
  - shell startup file は明示 `-c` かつ非対話なら target にしない。`-i` 併用時は従来どおり target。
- [guard_bash.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1073)
  - 出力先上書き拒否、baseline の先頭非 option token 判定、args 全体の `-m pytest` 検出を分離。
  - 残余 argv の全 path 拒否を廃止。
- 回帰テストは [test_hooks.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:741)〜[test_hooks.py:912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:912) に追加・修正。dense、bundle、`--`、版付き Python、wrapper を含みます。

### baseline からの受理集合差分

指定された baseline 3 本、計 84 綴りを直接比較しました。

DENY→ALLOW: **0 件**

ALLOW→DENY: **10 件**。すべて `s4-ruling.md` §2 の意図した縮小です。

- `-m` 借用
  - `python3 -mpytest tools/pegasus/submit_certify.sh`
  - `python3 -mpytest tools/run_tests.py`
- script 実行 module
  - `python3 -m cProfile tools/pegasus/exec_calibrate.py /tmp/argv.json`
  - `python3 -m cProfile -o /tmp/p.out tools/pegasus/certify_calibration.sh`
- module identity
  - `python3 -m pytest.__main__ orchestrator/tests/test_hooks.py`
  - `python3 -mpytest.__main__ -q`
  - `python3 -m _pytest.main orchestrator/tests`
- interpreter option 値による script 隠し
  - `python3 -W ignore tools/pegasus/exec_calibrate.py /tmp/argv.json`
  - `python3 -X faulthandler tools/pegasus/exec_calibrate.py`
  - `bash -O extglob tools/pegasus/certify_calibration.sh`

裁定 §2 以外の baseline 差分は **0 件**です。特に baseline DENY だった dense `-mpy_compile` と `-mrunpy` も DENY に戻しました。

### 検査結果

- `python3 -m py_compile hooks/guard_bash.py orchestrator/tests/test_hooks.py`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: 成功
- G1〜G5 焦点 `decide()` probe: **31 綴り、mismatch 0**
- baseline 3 本: **84 綴り、DENY→ALLOW 0**
- `HEAD~2` の既存テスト関数 78 本: AST 比較で変更・欠落 **0**
- mutation M1〜M6 の old anchor: 全て現コードに一意、各 1 件

`pegasus02` ログインノードのため pytest・変異は未実走です。**実装済み・未実走**であり、PASS は主張しません。

### 所有外への波及・残件

- runtime caller は `guard_bash.py` 内部だけで、所有外コードへの直接変更はありません。
- 旧 `probe_fix_result.json` は `python3 -mpy_compile tools/pegasus/collect_receipt.py` を ALLOW と期待しているため、現在はその 1 行だけ mismatch になります。しかし baseline の `probe_attached_m.json` は同綴りを DENY と実測しており、単調性に従って DENY を正としました。artifact は編集許可外なので、親で再生成が必要です。
- 再レビュー R7 の mutation expected-node 集合は親管理のままです。anchor は全て有効ですが、既知の stale node 集合は本修正では変更していません。
- G1〜G5 で直せなかったコード所見はありません。