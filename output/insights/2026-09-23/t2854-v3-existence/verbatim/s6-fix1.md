## 変更内容 (file ごと、追加削除行数)

| file | 追加／削除 | 変更 |
|---|---:|---|
| `orchestrator/verifier/dsg.py` | +40／−23 | file ごとの復号キャッシュ、W の版 tuple を取引単位で生成、異種 op の版だけ集合を保持、読み照合用集合と不要時の走査省略 |
| `orchestrator/tests/test_verifier.py` | +3／−3 | B1 の指定行削除、B2 の DSG 構築を共有 |

production 差分は **63 行**で、上限80行以内です。B3 の読みごとの空 dict／set 生成も除去しました。B1 以外の既存期待値・比較内容は変更していません。

## 所要の変化 (測った条件、または未測定)

**未測定**です。提示された親の実測ログは修正前の外部証拠として読みました。今回の改善幅を示す測定値ではありません。

## 試験の実走結果

**実装済み・未実走**です。

- 指定の直接 pytest：PreToolUse hook が Pegasus ログインノードでの実行を拒否。
- `python3 tools/run_tests.py orchestrator/tests/test_verifier.py -q -p no:cacheprovider`：`qstat -Q preflight rc=1`、終了コード16、`child_started=false`。
- 編集2ファイルの AST 構文検査、`git diff --check`：成功。

全緑・出力一致の実走確認は報告しません。

## 変異の照準に使う現在の行

以下はすべて `orchestrator/verifier/dsg.py` の現在行です。

| 判定・用途 | 行 | 現在の文字列 |
|---|---:|---|
| object 入口の v3 判定 | 333 | `if txns and isinstance(txns[0], TxnV3):` |
| object 入口の呼出し | 334 | `self._check_existence()` |
| compact 入口の v3 判定 | 348 | `if any(c.schema == 3 for c in trace.files):` |
| compact 入口の呼出し | 349 | `graph._check_existence()` |
| 表込み identity：object | 357 | `yield (txn.txid, object_identity(item),` |
| 表込み identity：compact | 376 | `objects[token] = _object_at(columns, token)` |
| 重複版／genesis commit の除外 | 393 | `if ig.version_dups or ig.genesis_commits:` |
| 版の所有者と op | 401 | `history[version] = (txid, op)` |
| 異種 op 判定 | 402 | `elif prior[1] != op:` |
| 異種 op 集合 | 403 | `mixed.setdefault((obj, version), {prior[1]}).add(op)` |
| 異種 op 診断 | 412 | `"ambiguous-write-version", tuple(sorted(ops)))` |
| 曖昧 object の派生診断除外 | 415 | `if obj in ambiguous:` |
| 版の並べ替え | 417 | `versions = sorted(history)` |
| 初期存在 | 418 | `live = history[versions[0]][1] != "I"` |
| I-on-live | 424 | `if op == "I" and live:` |
| U-on-absent | 426 | `elif op == "U" and not live:` |
| D-on-absent | 428 | `elif op == "D" and not live:` |
| D の後の状態 | 432 | `live = op != "D"` |
| D 版の照合集合 | 434 | `deleted.add((obj, version))` |
| 読み走査の必要条件 | 435 | `if unborn or deleted:` |
| genesis 読み | 437 | `if version == GENESIS:` |
| 初期不存在との照合 | 438 | `if obj in unborn:` |
| 指定された D 版の読み | 440 | `elif (obj, version) in deleted:` |
| 詳細の整列 | 442 | `details.sort(key=lambda v: (v.txid, v.table, v.key, v.version, v.kind))` |

M5 の `model.py`、M13 の `core.py` は未編集で、前段報告の照準から移動していません。変異試験は未実走です。

## 裁定からの逸脱と理由

実装範囲・規模の逸脱はありません。試験は実行制御と dispatch 障害により未実走です。新しい抽象・module・並列化は追加せず、commit は作成していません。

## 総括

局所最適化と B1〜B3 を指定2ファイルへ適用しました。production は63行、構文・差分検査は成功しました。判定・出力を維持する実装ですが、試験・性能測定による確認は未完了です。