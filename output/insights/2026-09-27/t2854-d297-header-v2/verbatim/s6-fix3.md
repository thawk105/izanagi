## 変更点 (file:line)

[tools/check_trace0_preprocess_identity.py:1119](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:1119) で header 検査結果を先に計算し、`check()` を辞書 literal を返す単一の `return` に戻しました。`header_rule` は header 差分がある場合だけ末尾の `**` 展開で追加します。既存 test は編集していません。

## 洗い出した consumer test と照合結果

- `test_mocc_trace_job_contract.py`: F7 の AST 固定を満たしました。返り値の文字列 key 順と `compiler` の key は commit `339d7c188` と一致します。他の参照は checker のパス、起動、成果物の結合です。
- `test_check_trace0_preprocess_identity.py`、`test_check_trace0_header_rule.py`: import と呼び出しの固定に反する変更はありません。
- `test_mocc_trace_pair.py`: checker 名は fixture 内のパスです。
- `test_silo_validation_isolation.py`: `CHECKER` は別の検査器を指します。

所有外では `tools/pegasus/mocc_trace_pilot.sh` が caller、`orchestrator/campaign/mocc_trace_pair.py` が成果物 consumer です。今回の返り値変更による固定条件との衝突は見つかりませんでした。

## 自走した確認

- F7 を修正前に直接呼び出して赤、修正後に直接呼び出して緑を確認。
- header test の全 12 関数を直接呼び出し、全件通過。所要は合計約 15 秒。
- header のない mocked 経路で、修正前 HEAD と返り値および JSON bytes が一致。
- `git diff --check` 通過。変更ファイルは検査器 1 件のみ。

## 未実走・懸念

全 pytest と実 CCBench 判定は実走していません。JSON bytes の比較は mocked 経路での確認です。

## 総括

既存 test の期待値と header 判定を変えず、F7 が要求する返り値の AST 形状を復元しました。