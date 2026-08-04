# 変異 matrix — [T-244] D121 P1 の機械部品 (2026-08-04)

**結果: 19/19 KILLED、生存ゼロ。** うち 17 件は `tools/mutation_harness.py` が KILLED と分類し、
2 件 (V14 / V20) は harness が分類できないため**親が手動注入して kill を確認**した。

anchor commit = `b76fb09` (実装 `38afb06` + main merge `13bbdfc` + docs)。
実行は Pegasus 計算ノードへ dispatch (`--runner-mode dispatch --detached`)。
runner argv = `python3 tools/run_tests.py -rf orchestrator/tests/test_reflux_ir.py`。

## 結果表

| ID | 変異 | 判定 | 経路 |
|---|---|---|---|
| V1 | emitter: sentinel 項 (`kUnset`) を先頭から削る | KILLED | harness |
| V2 | emitter: 選言の区切りを ` \|\| ` → ` or ` | KILLED | harness |
| V3 | emitter: 末尾 `;` を削る | KILLED | harness |
| V4 | emitter: 要因の並びを逆順にする | KILLED | harness |
| V5 | enum 名を 1 個改名 (`kReadValiTid` → `kReadValiTID`) | KILLED | harness |
| V6 | wire: bit 順を MSB-first にする | KILLED | harness |
| V7 | parser: 長さ検査を `!=` → `<` に緩める | KILLED | harness |
| V8 | parser: `strip()` を足す | KILLED | harness |
| V9 | mask: `type() is int` → `isinstance` (bool を通す) | KILLED | harness |
| V10 | sink: mask 再検証を消す (forged exact IR) | KILLED | harness |
| V11 | sink: `isinstance` → `type() is` (二重 import 破壊) | KILLED | harness |
| V12 | 拒否メッセージへ分類情報を足す | KILLED | harness |
| V13 | golden の 1 行を別 predicate へ書き換える | KILLED | harness |
| V14 | golden へ Call (`str(...)`) を注入する | **KILLED** | **親の手動確認** |
| V16 | 軸要因順の drift guard を無効化する | KILLED | harness |
| V17 | 代入先変数名を改名する (`izanagi_gate_pass` → `…x`) | KILLED | harness |
| V18 | sink の `except Exception` を 3 例外へ狭める | KILLED | harness |
| V19 | `SCHEMA_ID` を `"unrelated/v1"` へ変える | KILLED | harness |
| V20 | golden へ非 `__future__` の `import sys` を注入する | **KILLED** | **親の手動確認** |

**V15 (正例) は変異ではない。** 「正準 32 点をすべて通す」は clean 走行の
`test_wire_codec_is_bijective_round_trips_and_matches_all_goldens` と
`test_parse_wire_rejects_all_noncanonical_forms_uniformly` が担保しており、
過剰拒否がないことは baseline 緑で成立している。

## V14 / V20 を harness が分類できない理由 (erratum ではなく設計上の帰結)

F1 の fix で入れた golden 純粋性の AST 防壁は、テスト module の**冒頭 (module level)** で
`_validated_golden_assignments()` として発火する。したがって golden に禁止ノードが入ると
**collection error** になり、`FAILED <node>` 行が出ない。`DW-M08` は
「rc≠0 で failed node 0 件は fail-closed 停止」と定めるため、harness は正しく停止した。

これは検出力の欠落ではない。むしろ module 冒頭で落ちるため**そのファイルのテストが 1 つも
走らない**という、より強い fail-closed である。親は次を実測して kill を確認した。

| ID | rc | 診断 | 復元 |
|---|---|---|---|
| V14 | 1 | `AssertionError: golden contains forbidden AST nodes: {'Call'}` | hash 一致で復元 |
| V20 | 1 | `AssertionError: golden contains forbidden AST nodes: {'Import'}` | hash 一致で復元 |

復元は `git checkout --` で行い、golden の sha256 が凍結値
`641f89ca02b8b0b3e85ff679fc7c0656058e9570fc558356e2c36ff35cee1f9f` に戻ることを毎回照合した
(`DW-O19`)。

## erratum — 事前登録した `expected_nodes` が狭すぎた (初回走行)

`mutation-ledger-erratum-run1.json` が初回走行の生台帳である。V1〜V5・V9・V10・V12 の
8 件が `MISMATCH` になった。**内訳は「期待した node はすべて落ちており、加えて別の node も
落ちた」= 上位集合**であり、検出力不足ではない。原因は親の予測が狭かったことである —
emitter の出力 bytes を変えれば、凍結 freeze 照合と campaign provenance 照合も当然落ちる。

訂正は `expected_nodes` を実測値へ広げただけで、**どの変異も KILLED / SURVIVED の判定は
変わっていない**。変異内容 (`replacements`) もテストも一切弱めていない。
初回台帳は消さず erratum として保持する (`DW-M02`)。

初回走行はさらに、親が段 7 の insights を作った untracked file を harness が検出して
baseline 直後に停止した (`mutation-ledger-aborted-untracked.json`、job dir に保持)。
docs を commit して clean tree にしてから再走した。

## 走行の分割

| 台帳 | 対象 | 結果 |
|---|---|---|
| `mutation-ledger-erratum-run1.json` | V1〜V14 (初回、expected 未訂正) | 5 KILLED / 8 MISMATCH / 1 PARSE_ERROR |
| `mutation-ledger-part1.json` | V1〜V14 (expected 訂正後) | **13 KILLED** / 1 PARSE_ERROR (V14) |
| `mutation-ledger-part3.json` | V16〜V19 | **4 KILLED** |
| (手動) | V14 / V20 | **2 KILLED** |

V14 が harness を止めるため、V16〜V19 は V14 を外した spec で別走した。
分割の理由は harness の fail-closed 停止であって、都合の悪い変異の除外ではない。
