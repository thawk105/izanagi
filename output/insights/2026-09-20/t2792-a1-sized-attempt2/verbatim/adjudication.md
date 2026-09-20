# 段 4 裁定 — [T-2792] attempt-0002 投入 (2026-09-20 18:1x JST)

- 段 2・3 は省略 (DW-C00 軽量版: 設計択一なし・正しさ防壁に触れない・受理集合は変わらない。投入経路・study・attempt 名・公開先は D2172 項 2 と D2178 が名指し)。
- 裁定: **実装しない。** 実装面の差分ゼロ → 変異 matrix は免除 (DW-S04)。受入全走は免除しない (記録 commit 後に `tools/dev_wave_wait.py acceptance` で投入)。
  段は 4 → (親の実測: authorize-rerun / submit / 監視 / complete / materialize) → 稿起草 (親) → 6 (read-only review 1 本) → 7 → 8 → 9。
- 裁定 inbox の再走査 (18:1x JST): D2173〜D2183 と `docs/spool/decisions/` (README のみ) に本件を止める・変える裁定なし。
- (P1) attempt-0002 / `--decided-on 2026-09-20` (定数値) — 採用。(P2) hydrate 2 箇所 — 採用。(P3) 段構成 — 採用。(P4) 稿の骨格と並記の形 — 採用。
- 停止条件 (D2172 項 2、依頼文): authorize-rerun / submit / job / complete / materialize のどの層で落ちても再投入しない。gate 緩和・先行 attempt の
  証拠移動・policy / base の変更は不可。落ちた層と受領証を insight に記録して段 7 へ進む (稿は書けるところまで)。
- plan v2 = brief.md のまま。
