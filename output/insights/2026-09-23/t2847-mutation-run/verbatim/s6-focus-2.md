## 対応表

| 確認点 | 判定 | 根拠 |
|---|---|---|
| F01：固定公開版の再利用 | **closed（W4 の静的評価）** | [V20 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-published-version-mismatch.patch:50) は UPDATE ごとに公開 epoch を減らす。公開版同士は、カウンタが一周するまで重複しない。 |
| 公開版と後続 C/W 版 | 重複なし | 公開版の tid は `2^28`。公開版を読んだ後の [TID 生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:567) は tid を増やしてから最大値を選ぶ。W4 の単一 thread では、先行する高 epoch の C/W 値も worker に保持される。 |
| 同じ key の C/W 版 | 重複なし | `mrctid_` を毎回進めるため、29 bit の巻き戻り前は C/W 値が重複しない。 |
| 29 bit の巻き戻り | W4 では到達しない見込み | 高い公開 tid からの増分には約 `2^28` 回の C/W 生成が要る。ただし、1 秒間の実行回数を静的に保証する上限はない。 |
| epoch の 0・genesis 到達 | W4 では到達しない見込み | 初回公開値は `UINT32_MAX`。epoch 1 は約 `2^32−1` 回目、0 は `2^32` 回目の UPDATE で生じる。 |

## 新しい所見

**なし。** 追加した atomic は使用箇所より前に宣言され、`#if` は登録値どおり 4 箇所です。マクロ未定義側は元の `storeRelease(..., maxtid.obj_)` を保持し、pin への `git apply --check` と差分の `git diff --check` は通りました。

## 総括

**GO（焦点の静的再レビュー）。** F01 の公開版重複は解消しています。build と W4 実走は行っておらず、到達回数と発火・anomaly counter の確認は未了です。