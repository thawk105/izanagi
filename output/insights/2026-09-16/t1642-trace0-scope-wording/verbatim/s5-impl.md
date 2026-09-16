## 実装した差分 (file:line + 逐語)

**A1 — `tools/check_trace0_preprocess_identity.py:3`**

```python
"""選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を検査する。

この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に対しては必要条件の一つである。
この検査だけで trace の完全除去を証明したと解釈してはならない。
この保証は使用した compiler と選定した macro context に依存し、admission toolchain と同一であるとは主張しない。
"""
```

**A6 — `tools/pegasus/mocc_trace_pilot.sh:1744`**  
既存の hard gate 説明 2 行を残し、直後に追加。

```bash
  # This check proves the D297 guarantee and is one necessary condition for
  # complete trace removal from the measurement build; it does not prove that removal.
```

**A7 — 同ファイル `:357`、`:426`**  
両箇所を次の同一文字列へ変更。

```text
Certifies the D297 TRACE=0 preprocess identity gate, which is only one necessary condition for complete trace removal from the measurement build and does not prove that removal.
```

## 触らなかったアンカーの確認

`GUARANTEE`、`CheckError` docstring、`_mocc_trace_include_addition_index` docstring、旧 `:539–541` コメントは不変です。report schema・field 集合、既存テストも変更していません。

## 受理・拒否挙動の不変の確認

変更前は、祖先関係と対応する source 差分を確認し、選定 context の正規化 preprocess 出力・include 活性が一致する場合に受理します。限定された mocc include 追加例外も既存どおりです。

空差分、header・未対応差分、期待 path 不一致、空 context・比較件数不一致、preprocess 失敗、同一性不一致などは拒否します。静的に解決できない間接値に関する扱いも変更していません。

基準 `9d52ef145` との全 bytes 比較で、指定置換以外の変更がないことを確認しました。checker は module docstring を除く AST も一致し、受理集合・拒否条件は不変です。

manifest validator は `reason` を逐語照合しません。ただし `:568` で非空の単一行文字列を要求し、`:575` 以降で manifest 全体の禁止表現も検査します。新文言はこれらに抵触しません。

## 走らせた検査と結果 (実走 nodeid つき)

| 検査 | 結果 |
|---|---|
| `git diff` 閲読・変更ファイル一覧 | 指定 2 ファイル・3 アンカーのみ |
| `git diff --check` | rc=0 |
| 指定の `ast.parse` コマンド | rc=0 |
| 全 bytes の指定置換比較 | 両ファイル一致 |
| module docstring を除く AST 比較 | 一致 |
| checker `--help` 前後比較 | 両方 rc=0、出力完全一致 |
| `bash -n tools/pegasus/mocc_trace_pilot.sh` | hook に拒否され、未実走 |

pytest の実走 nodeid はありません。焦点 4 ファイル・受入全走は未実走です。親の全走を代替しません。

## 波及の静的列挙

- manifest consumer：2 経路の `reason` と生成 JSON bytes が変わります。validator の逐語照合はありません。
- caller：pilot が採取する checker SHA、`submit_mocc_trace.sh:319` が採取する pilot SHA が変わります。
- 共有 fixture・consumer test：`test_check_trace0_preprocess_identity.py`、`test_mocc_trace_job_contract.py`、`test_mocc_trace_pair.py`、`test_hooks.py` が関連します。変更していません。
- 将来の receipt・digest 束縛には新 bytes が反映されます。過去成果物は変更していません。

## 総括

指定文言は実装済みです。commit・index・branch 操作、新規ファイル作成、所有外ファイルの編集はしていません。構文検査とテストは未実走のため、`closed` とは申告しません。

PreToolUse の `guard_bash` が `bash -n` を拒否しました。理由は、対象が Pegasus の dispatch-required 実行体であり、計算ノードでの実行を要求するためです。