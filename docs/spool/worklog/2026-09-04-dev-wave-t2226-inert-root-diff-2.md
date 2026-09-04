---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2226-inert-root-diff
seq: 2
title: 段 8 — land の監査列の範囲を DW-O23 へ固定した。段 8 を段 9 の後に回した順序違反も記録する (docs のみ、branch worktree-dev-wave-t2226-inert-root-diff、実装面の差分 0)
---

## 本文

- **順序違反:** 段 8 を段 7 の後に行うべきところ、段 9 の land を先に済ませてから段 8 を実行した。
  そのため本エントリは land を 2 回に分けた 2 本目である。候補は実在したので、飛ばさずに是正した。
- **採った候補 1 件 (実測由来):** land が要求する監査 commit 列の範囲が `DW-O23` に書かれていなかった。
  範囲は `<tested main>..<tested tip>` で固定であり、競走で着地 tip を前進させても変わらない。
  本 wave は着地 tip 側で数え直して `rc=23` を踏み、land を 1 周失った。
  `tools/dev_wave_land.py --help` は「`git rev-list --reverse A..T` と同順」としか書いておらず、
  A と T が何かを束縛していない。main の履歴に「land 競合として固定 SHA … を取り込む」が繰り返し
  現れることから、この競走自体は頻出である。
- **予算の詰め方:** 追記で `docs/dev-wave/**` の L1 予算 (10625 bytes) を 204 bytes 超えた。
  D782 / D730 の手順に従い削減だけで収めた。上限は引き上げていない。削ったのは 2 件で、
  いずれも意味の正本が別にある重複である。
  (a) `DW-O23` の「wave 側で fold してはならない」の再掲 — 禁止自体は `DW-S07` と
  `docs/spool/README.md` が持つ。
  (b) `DW-O19` の `--wrapper-attempt` の説明 — 契約は `DW-M07` が持つ。
- **候補に挙げたが採らなかったもの:**
  - orphan hold が 2 path に書かれる件 — 既に `docs/failures.md` の F エントリに
    「orphan hold は 2 つの path に書かれ、dispatcher が見るのは片方だけである」と記録済み。
    本 wave の事故は記載の不足ではなく、私がそれを引かなかったことによる。文書は変えない。
  - 背景の待ち手が完了通知を早く出す件 — 実際には子は生きており `.done` も無かった。
    `DW-O01` の「完了は `.done` と exit code だけで判定し、通知も待ち手 rc も判定にしない」が
    そのまま働いて誤判定を防いだ。既存の防壁が効いた例であり、文書は変えない。
    ただし私は一度「待ち手が壊れた」と結論しかけた。通知の早出は故障ではない。
  - 親のテスト実走が login node の hook で拒否される件 — `docs/pegasus-runbook.md` が
    `tools/run_tests.py` 経由の正本を持つ。dev-wave 側へ再掲すると複製になるので足さない。

## 次の一手差分

### carry

- [T-2314]
- [T-2315]
