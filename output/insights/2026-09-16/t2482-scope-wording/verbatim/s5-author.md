## 変更内容

A1〜A4 の文字列だけを変更しました。

- `orchestrator/campaign/artifact_admission.py`: 76〜87 行
- `orchestrator/tests/test_artifact_admission.py`: 1371〜1382 行
- `orchestrator/tests/test_s1_9pair_figure_provenance.py`: 78〜89 行

test の独立 literal を維持。受理述語・凍結値・E1 導出は変更していません。

## 逐語一致の確認

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -c` で production module を import。test の literal は AST から取得し、正本から抽出した A1／A2 と完全一致で比較しました。

6 個すべて一致、rc=0。初回は比較コードの Markdown 抽出ミスで失敗し、抽出修正後に確認済みです。`git diff --check` も rc=0。

## 実走結果

**実装済み・pytest 未実走**。実走 nodeid・rc はありません。未 commit 時の閉包不一致を踏まえ、親の commit 後の焦点走に委ねます。

## 波及の静的列挙

`rg` で指定 production 10 ファイルと consumer test を含む `orchestrator/`・`tools/` を検索しました。

- 指定 production は定数または epoch field 経由で新文言を出力します。
- `test_s8b_oracle_report.py` は定数参照です。
- 所有外に旧文言の独立 literal は見つかりませんでした。

## git status

```text
 M orchestrator/campaign/artifact_admission.py
 M orchestrator/tests/test_artifact_admission.py
 M orchestrator/tests/test_s1_9pair_figure_provenance.py
```

## 総括

指定の 3 ファイル・4 アンカーのみ修正し、逐語一致を確認しました。commit は行っていません。