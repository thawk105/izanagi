# 段 4 裁定 — [T-1505] (2026-09-18 06:2x JST)

- 段 2・3 は省略 (DW-C00 軽量版: 設計択一なし・正しさ防壁に触れない・受理集合は変わらない。投入経路と study は D2120 項 3 が名指し)。
- 裁定: **実装しない。** 実装面の差分ゼロ → 変異 matrix は免除 (DW-S04)。受入全走は免除しない (記録 commit 後に `tools/dev_wave_wait.py acceptance` で投入)。段は 4 → (親の実測) → 7 → 8 → 9。
- 裁定 inbox の再走査: D2121〜D2134 と `docs/spool/decisions/` (README のみ) に本件を止める・変える裁定なし。
- (P1) attempt-0001 — 採用。(P2) hydrate 2 箇所 — 採用。判定は job 冒頭の dependency preflight に委ねる (自前の検査を足さない)。(P3) 段構成 — 採用。
- 停止条件 (D2120 項 3): submit / job / complete / materialize のどの層で落ちても再投入しない。落ちた層と受領証を insight に記録して段 7 へ進む。
- plan v2 = brief.md のまま。
