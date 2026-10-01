---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-vhash-c2-motivation
seq: 2
---

## 再発

### F300

- **再発: 2026-10-01** — `dev-wave-vhash-c2-motivation` の変異本走 (M0〜M9、固定 commit `b0d3efa90`) は 10 本とも登録どおり (matching 10 / 10) に完走したが、`tools/mutation_worktree.py` が `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で `rc=125` を返した。wave の木は走行前後とも clean で、走行中に別 session の land (CCBench pin F、10:54) が local main を進めたのが原因 (2026-08-25 の 2 件目の再発と同じ型)。防ぎ方 (`DW-M07`: `--source-repo` は D1009 の独立 clone) は手順に書かれていたが、親が入口の条件 dispatch 15 (変異を走らせる直前に `DW-M07` を読む) を実行せずに投入したため適用しなかった。同じ読み落としで初回の起動は `--attempt-out` の単独指定 (`DW-M07` が必須の組と書く) で引数エラーになった。手順の欠落ではなく既存の読み込み契約の不履行で、手順文書は変えない。結果 JSON は完全で判定に影響しないので再走していない。
