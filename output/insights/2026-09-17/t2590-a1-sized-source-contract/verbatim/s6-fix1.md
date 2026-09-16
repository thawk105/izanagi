## 実 sink の行番号 (visitor 直接呼出しの結果)

`_production_build_sources()` → `_benchmark_build_sinks()` の結果、一致する sink は 1 件でした。

`orchestrator/campaign/paper_story_a1_paired.py` / `campaign` / `<module>.run_measurement` / **7428**

## 変更箇所 (file:line、旧値 → 新値)

`orchestrator/tests/test_ccbench_spawn_sites.py` の数値のみ更新しました。

- 944 行：`7423 → 7428`
- 2731 行：`7423 → 7428`

## 他の行番号 pin の有無

他の行番号 pin はありません。paired.py の残りの参照は呼出し件数の pin でした。

## pytest / 直接呼出しの結果

指定の pytest 選択条件で **47 passed in 240.09s**、終了コード 0。

当該 ledger test の直接呼出しも成功。test 関数数は変更前後とも 46 です。

## 反実仮想の結果

両方を一時的に `7429` にすると、2789 行の `assert len(matches) == 1` で想定どおり失敗しました。

`finally` で `7428` に復元し、復元内容の一致と直接呼出しの成功を確認しました。

## 総括

所有ファイルの数値 2 箇所だけを修正しました。段 5 の実装差分には触れず、commit 操作も行っていません。