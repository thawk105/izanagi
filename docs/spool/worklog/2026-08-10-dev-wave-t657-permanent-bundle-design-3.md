---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t657-permanent-bundle-design
seq: 3
title: [T-657] 恒久設計 wave の逐語を insights へ凍結した — 段 7 の逐語凍結を land 後に補った (docs のみ、受入 rc=0、branch worktree-dev-wave-t657-permanent-bundle-design)
---

## 本文

- **段 7 が要求する insights 逐語の凍結を、直前エントリの land 後に補った。** 凍結先は
  `output/insights/2026-08-10_t657-permanent-bundle-design/`。逐語は段 1 brief、段 2 プラン、
  段 3 敵対 2 本、段 4 親裁定、段 6 レビュー 2 本と焦点再レビュー 3 巡の計 10 本。
- **手順の欠落は親の運用ミスであり、機構の不備ではない。** `DW-S07` は worklog / decisions と
  同じ段で逐語を凍結するよう定めており、直前エントリはそれを行わないまま land した。
  逐語自体は repo 外の wave 作業 dir に残っていたため失われていない。
- README に**射程**を明記した — 本 wave は実装差分ゼロであり、権限束の resolver も環境候補の
  record も consumer 移行も 1 行も実装していない。pegasus 第 2 世代は `registered-inactive` のまま
  であり、旧 branch も merge していない。「[T-657] が解決した」と引用してはならない。
- 逐語中の絶対 path は wave 実行時の作業 dir を指すこと、file:line は本 wave 時点の値であること、
  親が refuted と裁定した指摘を real として引かないことも README へ書いた。
- 未解決 placeholder の走査は 0 hit。可逆 defang は不要だった。

## 次の一手差分

### carry

- [T-657]
