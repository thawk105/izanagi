---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2316-b4-base-site
seq: 2
---

## 再発

### F300

- **再発: 2026-09-09** — [T-2316] wave の変異走行 4 本 (probe 3 本 + 本走 1 本) がすべて
  `rc=125` `共有木の事後検査に失敗` で終わった。原因は 2026-08-25 の 2 件と同じく
  **並行 session が走行中に local main を進めた**ことで、親は走行中 repo 内で作業していない
  (wave worktree は走行前後とも `git status --porcelain` が空)。本走の窓
  10:12:22–10:33:14 JST の中、10:31:52 に別 session が `2a68ac36f` を main へ着地させたことを
  commit 時刻で実測した。結果 JSON は完全で `matching 8/8`・`MISMATCH 0`、baseline も PASSED。
- **今回の手順漏れは、本エントリの恒久対応追補を読まずに走らせたことである。**
  F300 は 2026-08-25 の時点で既に「`--source-repo` へ独立 clone を渡すと観測点が clone 1 点へ
  畳まれて事後検査が成立する」と書いていた。親はこれを走行 4 本すべての後に読み、
  `git clone --shared` した clone を `--source-repo` に渡して本走を取り直したところ、
  **`rc=0` かつ `shared_snapshot_matches: true`** で完走し、結果も 1 走目と同一だった
  (KILLED 7 + 等価 SURVIVED 1、`matching 8/8`)。追補の有効性を独立 2 例目として確認した。
  **変異 harness を起動する前に本エントリを読むことが再発防止の実体である。**
