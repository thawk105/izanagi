## 変更内容

指定の `excluded_scope` 3か所だけを A2 v3 に更新しました。

- `orchestrator/campaign/artifact_admission.py`: 84–86行
- `orchestrator/tests/test_artifact_admission.py`: 1379–1381行
- `orchestrator/tests/test_s1_9pair_figure_provenance.py`: 86–88行

他の定数・判定・期待値は変更していません。

## 逐語一致の確認

指定の `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -c` で、import した定数と AST で取得した独立 literal 2件を、裁定資料から抽出した A2 v3 と比較しました。すべて完全一致、rc=0。ASCII 括弧と直前の半角空白も確認済みです。一時 file は作成していません。

## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| レビュー B should-fix：例外の係り先が曖昧 | closed | 採用済み A2 v3 の括弧書きへ3か所とも完全一致で更新 |

## 実走結果

pytest は未実走。nodeid・rc はありません。未 commit による既知の `contract-loader-drift` を避け、焦点走は親の commit 後に委ねます。

逐語比較と `git diff --check` はともに rc=0。

## git status

```text
 M orchestrator/campaign/artifact_admission.py
 M orchestrator/tests/test_artifact_admission.py
 M orchestrator/tests/test_s1_9pair_figure_provenance.py
```

## 総括

実装済み・テスト未実走。変更は指定3 file の文字列のみで、commit は行っていません。