---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t574-world
seq: 4
title: 直前エントリの受入数を訂正する — land した tip を certify したのは 7066 passed で、題の 6846 は再走前の値だった (docs のみ、実装差分なし、branch worktree-dev-wave-t574-world)
---

## 本文

- **erratum。** [T-574] 残余の wave (直前エントリ) の題は「受入 6846 passed / 20 skipped」と書いたが、
  これは main `0d64599e` を取り込んだ時点の値である。その後 main を 2 度取り込み
  (`3d6b157b`、`23337171`)、land 直前に受入を再走した結果は **7066 passed / 20 skipped
  (`child_rc=0`)** で、**land した tip `ff63ef72` を certify したのはこちら**である。
  題の数値は land 前の再走で更新すべきだった。凍結済みエントリは書き換えず、本エントリを
  訂正記録とする。一次資料は
  `output/insights/2026-08-06_t574-world-expansion/README.md` の「実測」節 (訂正済み)。
- 変異 4/4 KILLED、`check_docs` 違反なし、provenance 全史監査 6 違反 (いずれも本 wave 外) は
  直前エントリのとおりで変わらない。実装差分は 1 byte も変えていない。

## 次の一手差分

### carry

- [T-529]
