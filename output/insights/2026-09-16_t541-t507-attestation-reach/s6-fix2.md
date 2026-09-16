## 直した内容

`attest.sh` に `compare_profiles` の観測 wrapper を追加した。実関数へ委譲し、比較行を記録して、戻り値の同一オブジェクトをそのまま返す。`_attest` は1回だけ呼び、終了時には元の比較関数へ戻す。

例外時は非 pass 行を stdout に JSON 出力して再送出し、stderr の traceback と非ゼロ終了を維持する。成功時の payload 出力は従来どおり。

## 不一致時に出る情報の形

以下は形式例であり、実測値ではない。

```json
{"non_pass_comparisons": [{"field": "effective_clock.governor", "expected": "performance", "observed": "powersave", "verdict": "fail"}]}
```

`verdict != "pass"` の行を値の変更なしに出力する。比較結果が得られる前の例外では配列は空になる。

## 触っていないことの確認

実装変更は `attest.sh` のみ。`orchestrator/`・既存テスト・docs は編集していない。作業開始時から存在した driver とテストの変更には手を加えていない。

較正値・判定条件・tolerance、世代を固定しない lookup、PBS directive・queue・`python3.10`・cwd を維持した。再 probe、job 投入、commit、git add、ブランチ操作は行っていない。script の記録先は stdout / stderr のみ。

## 静的確認の結果

- `bash -n`：終了コード0。
- Python 本体の `ast.parse(..., feature_version=(3, 10))`：成功。
- AST 上の `_attest` 呼出箇所：1つ。
- `git diff --check`：終了コード0。

実走・テスト実行・計算ノードでの受理確認は行っていない。

## 総括

実装済み・未実走。closed とは申告しない。

`-o` の指定がないため、報告を `output/insights/2026-09-16_t541-t507-attestation-reach/s6-fix2.md` に保存した。
