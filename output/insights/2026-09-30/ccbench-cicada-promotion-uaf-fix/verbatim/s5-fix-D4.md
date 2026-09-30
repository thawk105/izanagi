## 直したこと (file:line)

- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:49): T6p を build 定義と走行順から削除した。T6・ASAN-T6 は残した。
- [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/README.md:16): 対照を T0p・T4p に修正し、`--parts tpcc` を **13 build・40 走行**に更新した。

## login で行った検査と結果 (未実走の明記)

`py_compile` と `--parts tpcc --dry-run` は成功した。dry-run は `dry-run-inputs-valid` を返し、T6p が登録されていないことを確認した。最初の dry-run は手入力した BASE OID の誤りで失敗したため、正しい OID で再実行した。

**build と TPC-C 走行は未実走。**

## 総括

走行順・判定・記録と `v-update-keep.patch` は変更していない。T6 系の patch 順は BASE → init-ver → uaf → update-keep のまま。`external/ccbench/`、既存テスト、その他の所有外 file は編集せず、commit も作成していない。