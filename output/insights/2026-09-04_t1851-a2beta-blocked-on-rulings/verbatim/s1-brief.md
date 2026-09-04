# [T-1851] 段 1 brief — 実装単位 A の後半 A2β (E1 / E2)

日付: 2026-09-04。branch `worktree-dev-wave-t1851-unit-a`。継承 tip `520b1ddba`。
main 取り込み後 tip `7771c9e65` (local main `1b7822110`)。

## scope (引数)

A2' の残り = E1 (起動層の生の事実からの terminal projection)、E2 (台帳専用理由語彙 4 語の
active 化)、E3 (`_assert_profile()` の schema 別 exact validator 化)、E4 (v2 mutation /
capability 消費 / claim v3 / v2 resume)。境界 signature は A1' 段 4 裁定 3 節に固定済み、との前提。

## brief 前の実測が引数の前提を 2 点覆した (DW-S01 / DW-S04)

1. **E3 と E4 の構造面は済んでいる。** 継承 tip `520b1ddba` は A2α
   (`69497db66`〜`9df7105f6`、5 file / +1,671 / −97) を含む。A2α の README
   (`output/insights/2026-09-03_t1851-a2alpha-generation-open/README.md`) が
   E3 (exact validator、新 2 field 込み) と E4 (path の世代分岐 11 呼出し、create-only publish、
   claim v3、capability 消費、v2 resume) を積んだと記録し、変異 21/21 一致・受入 child-green で
   閉じている。引数の「E3 必須 — 現行は v1 固定で 5 箇所で全拒否」は A1' 時点の記述であり、
   現物では既に解消している。引数は A1' の job dir handoff
   (`/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/handoff.md`、A2α で未更新) に
   基づいて起草されたと判断する。
2. **E1 / E2 はユーザー裁定待ちで着手できない。** A2α 段 4 裁定と段 2 plan・段 3 レンズ 2 本の
   3 者が独立に「A1' が固定した 2 つの封印 terminal API の signature のままでは、同じ裁定が
   承認した『起動層所有の生の事実から再導出し、自己申告 field は比較にだけ使う』を実装できない」
   と結論し、A2α README 13 節が裁定パッケージ 3 件をユーザーへ返した。
   `docs/decisions.md` (main、D1622 まで) に該当する裁定は無く、/rulings 第 7 回 (worklog 1260)
   の索引 15 件にも含まれていない。したがって「境界 signature は固定済み」は形式上は真だが、
   その signature では E1 を承認済み要求どおりに実装できず、補正には受理面と public API 面の
   拡大を伴うため親では裁定できない (`DW-STOP`: ユーザー裁定待ち)。

## 確定済みユーザー裁定 (不変)

- D1341: 6 段 (B1 / A1' / A2' / B2 / D1 / C / D2) を揃えて 1 変更単位で land する。本 wave も land しない。
- D95: 実装面は Codex author。規律 2 (正しさゲート) を緩めない。
- A1' 段 4 裁定 3 節 (E1 の要求: 生の事実からの再導出、自己申告 field は比較専用)。
- A2α の 2 決定 (v2 terminal は封印 API 実在まで二層で無条件拒否 / capability 束縛は境界の範囲に留め
  非束縛集合を明記)。いずれも本 wave が触らない。

## 本 wave が実施したこと

- 旧 worktree の再利用 (占有 0 件を pgrep で実測)、`check_wave_startup.py --mode resume` rc=0。
- local main `1b7822110` (146 commit) を `--no-ff --no-commit` で取り込み、`7771c9e65` として commit。
  main 側の実装面の変更は単位 A の編集面 4 file とその consumer 2 file に 1 file も交差せず、
  重なった file は `docs/dev-wave/operations.md` だけ (自動 merge、競合なし)。
  実装面で両親のいずれとも異なる file は無いので Codex author の合成監査は発火せず
  (`docs/ai-provenance.md` の実装面契約と `DW-O17` の「両親と異なる実装面」条件)、
  integrator trailer で記録した。合成の意味的健全性は焦点走と受入全走で実測する。
- 全史 provenance rc=0 (8,167 件)、`check_docs.py` rc=0。

## 段 4 への提案 (親の provisional 裁定)

**(P1) 本 wave は E1 / E2 を実装しない。** `4→7→8→9` とし、段 7 で本 wave の実測 (main 取り込み、
引数前提の訂正、裁定待ち 3 件の再提示) を fragment に記録して停止する。
段 9 は D1341 により land しない。裁定 3 件は A2α README 13 節の文面をそのまま
ユーザーへ返す (親の推奨は同節の「推奨」に同じ)。

## 変更面

実装面の差分 0 (merge 以外)。変異 matrix は `DW-S04` により免除。受入全走は免除せず実走する。
