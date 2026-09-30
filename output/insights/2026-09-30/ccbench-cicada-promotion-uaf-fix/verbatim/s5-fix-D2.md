## 直したこと (file:line)

- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:246): 判定器の stdout だけを JSON として読み、stderr を別ファイルに保存する。rc=1 でも `results[0]` の巡回数・代表 witness・notes を取得し、C 行で写した tx の時刻と診断 event を照合する。代表 witness 数、event tx を含む witness 数、event key を持つ rw 辺数を記録する。これにより巡回ありの最初の raw trace も保存対象になる。
- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:324): ASan を `halt_on_error=0` にし、報告件数と最初の報告の先頭 40 行を記録する。異常終了時の `#FLAGS_*` は「未出力」と記録し、正常終了時の照合は必須のままにした。compile_commands.json の `-D` 照合も維持した。
- [v-init-ver.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/v-init-ver.patch:1): INLINE_VERSION_OPT=1 の `Tuple::init` が渡された `ver` の body を参照する対照 patch を追加。[launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:49) に T4・T5・promotion 無効の T0p/T4p、土台と T5 相当の ASan、`--parts` を追加した。
- [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/README.md:18): 13 build・43 走行と、親の Elapse 250 秒を踏まえた概算 373～804 秒を記載した。

patch の順序は T4/T4p が **BASE → init-ver**、T5/ASAN-T5 が **BASE → init-ver → uaf**。`external/ccbench/`、判定器、計装 patch、既存テストは変更していない。commit も作成していない。

## 親の実測への対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| rc=1 の判定器 JSON を空結果として扱った | closed | 親の JSON を使った fixture で 344 巡回と代表 witness を取得 |
| ASan が最初の UAF で停止した | partial | `halt_on_error=0` と報告記録を実装。計算ノードでの継続走行は未確認 |
| 異常終了時の `#FLAGS_*` 欠落で job が停止した | closed | signal 終了を「未出力」とする fixture が通過。正常終了時の欠落は引き続き同一性エラー |
| `Tuple::init` の insert 欠陥という gdb 所見 | partial | T0p/T4p と T4/T5 の対照を用意。原因の帰属は実走結果待ち |

## login で行った検査と結果 (未実走の明記)

BASE の使い捨て clone `md32-scratch/ccb` で init-ver の適用、続く uaf patch の適用確認が rc=0。修正後 `tuple.hh` の 1 TU 構文検査、`py_compile`、`--parts tpcc --dry-run`、`git diff --check` も rc=0。clone は削除した。

判定器 rc=1 の fixture で stdout/stderr 分離と witness 照合、ASan 異常終了の fixture で報告件数と `#FLAGS_*` の扱いを確認した。**全 build、TPC-C・YCSB の走行、判定器の再実走は未実走**である。

## 総括

親の実測で job を止めた二つの読み違いを修正し、insert 欠陥と UAF の寄与を分けて観測する対照を追加した。実際の帰属判定には計算ノードでの再実走が必要。