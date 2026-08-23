---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t863-family-root-erratum
seq: 1
title: [T-863] 公表 core v2 §8.1 の偽命題を canonical decision で限定訂正する (docs のみ、branch worktree-dev-wave-t863-family-root-erratum)
---

## 本文

- ユーザーは択 (a) を選び、R3 待ちは正しさでなく着手順の従属だったとして外した。判断は
  {{D:t863-family-root-erratum}} へ集約した。
- main 前進を検出して段 2 を現基準から再実行し、独立 2 レンズを再走した。初回・再走の real 所見は
  すべて採用した。
- canonical acceptance は tested main `26c8979f16624ee48c10157b2f7d3d766da0cf69`、tested tip
  `2c19c86b9372f27c492a7cd784ad8cd0a69a40ec` に対して `child-green` だった。全走は
  14878 passed / 67 skipped、赤 0、flake 0。lease は取得されなかった。

## 次の一手差分

### 完了

- [T-863] 公表 core v2 §8.1 の `family_root` 偽命題を canonical decision で限定訂正した。
  remaining: none
  base: 7e47855cde36789b1c885e18dacd8c93e87f40fcc1e6b0dfbe9ede3a0f60495a
