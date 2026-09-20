## 変更

[test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2344-fix1/orchestrator/tests/test_t671_source_binding.py:1638) の1638・1717・1723・1801・1807行で、`timeout_seconds` の独立 literal を **630 → 850** に変更しました。変更はこの5か所だけです。

## 検証

`tempfile.mkdtemp()` と `pytest.MonkeyPatch()` による直接呼出しで、対象3関数すべて緑でした。**pytest 実走ではありません。**

メモリ上で5か所を630へ戻す反実仮想では、3関数とも元の `assert calls == [`（1627・1710・1794行）で赤になることを確認しました。`git diff --check` も成功しました。

## literal 検索

`rg` で検索し、修正後の `630`・数値 `63`・`620` は残存なし。1469行の `62` は任意件数のスケーリング試験入力なので維持しました。現行path数の期待値は295行の `85` で、追加修正は不要でした。

## 裁定・レビューとの整合

RA-1／RB-1の指摘と一致しています。裁定本文の期待値変更禁止に対しては、今回の明示指示で許可された5 literal の追随だけを行いました。

## 総括

指定修正と直接呼出し検証は完了しました。
production・他test・docsの変更、作業checkoutのcommit操作はありません。
残る検証上の限界は、pytestによる焦点走を再実行していないことです。