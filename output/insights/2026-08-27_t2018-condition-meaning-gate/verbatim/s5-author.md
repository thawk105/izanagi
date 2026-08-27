## 総括

dirty 実装を段4裁定へ照合し、material な誤りを1件修正しました。wrong-RHS の実効値が偶然要求値と一致しても、cache mapping identity が異なれば `supply-value-mismatch` で拒否します。

それ以外の指定境界に material な不整合は確認していません。pytest は dispatch 障害で未実走です。

## 変更

- `assert_backoff_fixed_supply()` に、`BACKOFF_FIXED` が必ず `CCBENCH_BACKOFF_FIXED` から供給されることの検査を追加。
- 誤った RHS の既定値が要求値と同じ場合も拒否する敵対テストを追加。
- 独立公開 API は以下です。
  - `capture_backoff_fixed_inputs()`
  - `assert_backoff_fixed_supply()`
  - `assert_backoff_fixed_meaning()`
- 共有 extractor、source-owner-aware effective mapping、F707/F718 fixture、authority anchor は維持。
- 既存テストの期待値変更・緩和・skip・xfail・削除はありません。

## 独立 arm の含意

Supply arm は source owner に対応する CMake cache-to-TU mapping を再導出します。供給表が非空でも mapping が無い F707 は compiler 解決前に `macro-not-supplied`、wrong-RHS または値不一致は `supply-value-mismatch` です。

Meaning arm は supply の結果を参照せず、captured hole を standalone TU で実 compiler 評価します。case × context の canonical float64 bits を pointwise 比較するため、式文字列の存在や単射性だけでは受理しません。F718 は supply 緑でも expected 1000.0／observed 0.0 を `decoded-meaning-mismatch` で拒否します。

Proof kind は standalone-TU／finite-pointwise-witness に限定され、actual target TU、dynamic reachability、exact build inputを主張しません。`driver_integration="none"` で、現行1000点は未保護です。

## 検査

- `git diff --check`: rc=0
- 変更7 Python fileのAST parse: rc=0
- U+0300からU+036F: 該当なし
- trailing whitespace: 該当なし
- authority patch、supplied fixture、F707 fixtureのconditional/hole byte anchor: 静的照合済み
- dirty path: 段4の所有集合内のみ

| 項目 | 状態 |
|---|---|
| 所有・禁止境界 | closed |
| 構文・静的整合 | closed |
| supply実装 | 実装済み・pytest未実走 |
| meaning実compiler評価 | 実装済み・pytest未実走 |
| 既存互換性 | 静的監査済み・pytest未実走 |
| 確定回帰 | 0件。ただし実走未確認 |

## 未実走・赤

`python3 tools/run_tests.py orchestrator/tests/test_condition_meaning_gate.py -q` は `rc=16`、`child_started=false` でした。`qstat -Q preflight rc=1` のためpytest nodeは1件も起動しておらず、緑とは申告しません。

未実走です。

- `test_condition_meaning_gate.py` 全体
- sort共有wrapper互換node
- source_digest effective mapping境界node
- plain-runner meta-test
- acceptance duration ledger coverage meta-test

既存テスト赤は観測していません。test child自体が未起動のため、赤なしの確認にもなっていません。

## 所有外波及

Production callerは0本です。共有 parser の既存consumerである sort oracleへ波及可能性がありますが、公開wrapperと従来の受理拒否文言は維持しています。

source_digestの新adapterは追加APIで、既存digest経路は変更していません。fixture consumerは新test fileだけです。所有外のtracked file、docs、patches、ledger、driver、格子、符号化式は編集せず、commitとgit addも行っていません。
