## 直したこと (file:line)

- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:237): 正常終了時は表示された `#FLAGS_*` を argv と照合する。表示されない `tpcc_*` は値と「表示なし」を記録し、共通 flag 4 個の欠落や表示値の不一致は identity-error とする。異常終了時の扱いは D2 のまま。
- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:262): TPC-C stdout の `failed` 行を種類別に数える。照合エラーの走行も結果に保存してから停止する。
- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:49): T6・T6p・ASAN-T6 を追加。T6 系の patch 順は **BASE → init-ver → uaf → update-keep**。Release は M・R2 × 各 2 反復、build 交互の順を維持した。
- [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/README.md:18): 親の 280 秒と `result.json` の走行秒数を踏まえ、`--parts tpcc` を 14 build・44 走行、概算 354～682 秒に更新した。

## 親の実測への対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| YCSB の witness と Y1 の巡回 0 | closed | 親の実測を採用。再走しない |
| ASAN-T5 の正常終了後、未表示の `tpcc_*` で停止 | closed | 実 stdout を使った照合 fixture が通過 |
| 土台 ASan が最初の UAF で rc=1 停止 | closed | 観測として記録。異常終了時の flag 扱いは維持 |
| ASAN-T5 の `insert order failed` 123,859 行 | partial | 行数を再現して数えた。T6 との比較は未実走 |

## login で行った検査と結果 (未実走の明記)

`py_compile`、`--parts tpcc --dry-run`、`git diff --check` は成功。使い捨て clone で T6 の 3 patch を順次 `git apply --check`・適用でき、`tuple.hh` の 1 TU 構文検査も成功した。clone は削除済み。親の stdout では `insert order failed` を **123,859 行**と数え、表示値不一致・共通 flag 欠落がエラーになることも fixture で確認した。

**全 build、TPC-C 走行、ASan-T6 の実走は未実走。** `external/ccbench/`、判定器、計装 patch、既存テスト、その他の所有外 file は変更していない。commit は作成していない。

## 総括

TPC-C の対照走行を止めた flag 照合を修正し、後続 update の寄与を T5/T6 と T6p、ASan で比較できる状態にした。原因の帰属は計算ノードでの `--parts tpcc` 実走結果を待つ。