指定の 2 ファイルを新規作成し、docs 編集・commit・production wiring は行っていません。

- [reflux_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:1)
- [test_reflux_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:1)

実装内容は exact `int`/`str` 検査、固定例外、sink 再検証、LSB-first codec、正準 predicate、軸順 drift guard、二重 import 相互受理を含みます。テストは 32 点 golden／旧実装差分、拒否面、forged IR、artifact、二重 runner を網羅しています。

### 独立性についての重要な申告

- `s8a_trigger_sweep.py` の `predicate_for` 実装本文は読んでいません。
- golden の値や本文は画面へ出力・目視していません。
- ただし、最終 consumer 検索時の次の `rg` で除外 glob が意図どおり効かず、golden ファイルを検索対象として走査した可能性があります。

  `rg -n 'reflux_ir_expected_goldens|reflux_ir' orchestrator --glob '*.py' --glob '!tests/**' ...`

golden 由来の行は出力されず、実装・テスト初稿の作成後に起きた事故ですが、「grep しない」という字義上の制約は厳密には守れていません。隠さず報告します。sha256 は内容を表示せず確認し、指定値 `641f89ca...f9f` と一致しました。

### C++ 識別子の出典

[骨格 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/patches/silo-backoff-trigger-gating-variant.patch:56) から読み取りました。

- 56–69 行: `IzanagiAbortReason`、`kUnset`、5 member、`izanagi_abort_reason_`
- 84 行: `izanagi_gate_pass`
- 102 行: 代入文の形

### 検査結果

- `python3 -m py_compile orchestrator/campaign/reflux_ir.py orchestrator/tests/test_reflux_ir.py`
  - rc=0、対象は新規 2 ファイル。nodeid は該当なし。
- `git diff --check`
  - rc=0。
- 新規 untracked 用 `git diff --no-index --check /dev/null <file>`
  - 両ファイルとも空白エラーなし。
- `git status --short`
  - 新規 3 ファイルだけ:
    - golden
    - `reflux_ir.py`
    - `test_reflux_ir.py`
- targeted pytest:
  - 範囲: `test_reflux_ir.py` と `test_plain_runner_coverage.py`
  - 計算ノード dispatch 前の `qstat -Q` が失敗し rc=16。
  - 収集・実行 nodeid は 0 件。テスト赤ではなく基盤 preflight failure。
- `python3 orchestrator/tests/test_reflux_ir.py`
  - `pegasus02` ログインノード規律により未実行。緑とは報告しません。
- pytest 全走
  - 未実行。親の計算ノード実行対象です。

### 所有外への静的波及

- production caller: 0 件。
- production の golden consumer: 0 件。
- 既存 `test_*.py` からの直接参照: 0 件。
- 共有 `conftest.py`／fixture 参照: 0 件。
- 間接 consumer: `test_plain_runner_coverage.py` が新規テストの `_run()`／`__main__` を検査します。
- テスト限定依存: `axis_trigger_gating`、`s8a_trigger_sweep.predicate_for`、凍結 artifact、campaign provenance。
- freeze は「6 record = 相異 3 mask」、provenance は「歴史的 artifact との 9 mask 一致」であり、独立 oracle として水増ししていません。

## 総括

成果物と静的検査は揃いましたが、golden を対象に含め得る誤った `rg` を実行したため、厳密な独立性証明には傷があります。親は本成果を独立実装子の完全適合結果として数えず、必要なら新しい隔離 context で再実装・再確認してください。