## 所見の対応表

| 追補 1 | 状態 | 確認結果 |
|---|---|---|
| 1. stock 専用 resolver | closed | STOCK のみ receipt 発行、非 STOCK は `None` |
| 2. 成功条件の維持 | closed | variant／BUILD_START の STOCK 判定を維持 |
| 3. admission class | closed | WAL の `machine-generated`／`backoff-sweep` を検査 |
| 4. digest test の緑化 | closed | 実 admission を通過、checkpoint 保持 |
| 5. M16／M17 | closed | 両変異をプロセス内で kill |

## 変更の要約

指定の 2 ファイルだけを変更しました。

- `p3_s4_loop.py`: `_stock_capability_resolver()` を追加し、stock 経路だけに接続。
- `test_p3_s4_loop.py`: 非 STOCK 拒否テストと receipt の検査を追加。既存 build mock に grammar 引数を検査するラッパーを追加。

既存の期待値、候補経路、admission gate は変更していません。

## 実走結果

指定の `pytest.main()` 形式で実行しました。以下の個別 nodeid は `orchestrator/tests/test_p3_s4_loop.py::` 配下です。

| 対象 | 件数・結果 | pytest rc |
|---|---:|---:|
| 同ファイル全件 | **550 passed** | 0 |
| 指定の焦点走（`resolver` 含む） | **47 passed、503 deselected** | 0 |
| `test_plain_runner_coverage.py` 全件 | 3 passed | 0 |
| M16: `test_stock_resolver_refuses_non_stock_evidence` | 1 failed＝KILLED | 1 |
| M17: `test_stock_digest_refresh_keeps_checkpoint`、`test_stock_control_reaches_campaign_under_applied_template` | 2 failed＝KILLED | 1 |

M16 は ABORT reason の不一致、M17 は実 admission 拒否と resolver 引数欠落で検出しました。変異によるファイル変更はありません。

途中の試走では mock の引数不足と新テストの設定不足を検出・修正しました。最終走は上表のとおりです。`git diff --check` も通過しました。

## 波及

sort／trigger driver は独自 gate を持ち、変更不要です。`p3_b4_launcher.py` の共有 main、job body、他テスト、docs は未変更です。

親の insight には、stock の admission class が `machine-generated` であり、source の STOCK 性は `src_token` で保証する点を記録してください。

## 未了・懸念

実 compiler での STOCK 成立・性能測定は本段では未実施です。full／short PIN 比較の正規化は scope 外として残しています。

## 総括

本 fix の実装・回帰・変異検証は完了しました。差分は working tree に残し、git add／commit は実行していません。