F1〜F7 をすべて修正しました。編集は許可された実装・テストの 2 ファイルだけで、golden、docs、production wiring、commit には触れていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | golden を import せず、実行前に閉じた AST allowlist で検査して `ast.literal_eval` する方式へ変更。文書文字列、future import、指定 2 代入、tuple/string/int literal、Load/Store 以外を拒否 |
| F2 | closed | 空白・タブ・改行・全角空白・引用符で包まれた正準文字列、および空白除去で正準化される長い内部空白例を追加 |
| F3 | closed | `_reject()` を `raise ... from None` 化。property 取得失敗後は `except` の外で拒否。型、`str`、`repr`、`args`、`vars`、cause/context を両 import 経路で検査 |
| F4 | closed | `ir.mask` 取得を `except Exception` で統一拒否。`RuntimeError` を送出する実 subclass を両 sink・両 import 経路で検査 |
| F5 | closed | 骨格 patch の追加行を読み、代入先、理由変数、enum 型、sentinel と 5 要因 member の実在を production private token と照合 |
| F6 | closed | plain runner が `skiputil.Skip` を generic ERROR より先に捕捉し、SKIP を別計数 |
| F7 | closed | `SCHEMA_ID == "izanagi-trigger-gate-ir/v1"` を exact pin |
| 回帰 | regressed なし | 既存期待値の反転・緩和・skip・削除なし |

主な変更箇所は [reflux_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/campaign/reflux_ir.py:51) と [test_reflux_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/test_reflux_ir.py:31) です。

### 実行した検査

- `python3 -m py_compile`  
  範囲: 指定 3 ファイルすべて。`PYTHONPYCACHEPREFIX` は `/tmp` に隔離。  
  結果: rc=0。
- `git diff --check`  
  結果: rc=0。
- 未追跡ファイル向け `git diff --no-index --check /dev/null <file>`  
  範囲: 3 ファイルすべて。差分存在を示す期待どおりの rc=1、whitespace 診断は 0 件。
- `git status --short`  
  結果: 指定された未追跡 3 ファイルのみ。
- `sha256sum orchestrator/tests/reflux_ir_expected_goldens.py`  
  結果: `641f89ca02b8b0b3e85ff679fc7c0656058e9570fc558356e2c36ff35cee1f9f`。
- 所有外 Python consumer の `rg` 検索  
  結果: 該当なし。

実行 nodeid はありません。ホストが `pegasus02` のため、pytest・plain runner とも未実行です。したがって runtime テストを緑とは報告しません。実行した検査に赤はありません。

### 静的な波及可能性

- 所有外の production caller/consumer: 現時点の Python コードには見つかりませんでした。production wiring も追加していません。
- 共有依存: `axis_trigger_gating.GATEABLE_REASONS`、legacy predicate oracle、骨格 patch、known-axes freeze、既存 campaign provenance。
- 共有 fixture/runtime: `skiputil.Skip` と二重-runner契約。
- consumer test: `test_plain_runner_coverage.py` が新規テストファイルの自走 harness を検査します。親の全走ではこの meta-test を含めた確認が必要です。
- 骨格 patch の C++ token が変更された場合、新設した authority 照合が意図的に赤になります。

### Golden

[reflux_ir_expected_goldens.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py) は編集していません。作業前後の sha256 は指定値のままです。

## 総括

F1〜F7 はすべて `closed`、`partial`・`regressed` はありません。dev-wave author 契約どおり、docs・commit・所有外ファイルを変更せず、親が計算ノードで pytest 全走できる状態で引き渡します。