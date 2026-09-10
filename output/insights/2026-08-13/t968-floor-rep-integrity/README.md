# [T-968] 床値 session の rep 完備性 (rc + counter) — dev-wave 材料

2026-08-13、branch `worktree-dev-wave-t968-floor-rep-integrity`、base `31b004b7`。

## 何を閉じたか

床値 campaign は rep ごとの rc と perf counter 完備性を記録も検査もしていなかった。
そのため probe 成功後に本番 perf が壊れた rep の throughput が「有効」として session median に
入り、cell medians と床値を汚染しうる (wave 前から在る穴)。

ユーザー裁定「採用 (除外区分の追加で)」(2026-08-13 第 7 束) に従い、rep 階層の証跡
(`rep_observations`) と除外区分 (`rep_integrity_failure`) を新設した。除外条件は
**rc と counter 完備という機械的事実だけ**で、throughput・median・CV・値の大小は条件に入らない。

## 凍結境界

`allowed_excluded_reasons` の 4 理由表は、ユーザーが seal 済みの
`output/s8b-freeze/floor_protocol.json` (774 bytes, sha256 `261cec1c…`) の中身である。
`s8b_floor_contract` の pin 検査は凍結保留の対象外で生きているため、protocol 表へ 5 番目を
足すと seal 済み protocol が拒否され campaign が起動不能になる。よって新区分は protocol 検証より
後の journal/result 層に置き、**凍結 bytes は 1 byte も変えていない**。

## ファイル

- `brief.md` — 段 1 brief (穴の実体と (P1)(P2))。
- `s4-ruling.md` — 段 4 裁定と変異事前登録。
- `s6-fix-ruling.md` — 段 6 レビュー所見の裁定と変異再照準。
- `mutation-spec.json` / `mutation-ledger.json` — **probe 走** (`DW-M08`)。
  期待 node 集合の不足で 4 件 MISMATCH。検出できなかった変異は無い (SURVIVED 0)。
- `mutation-spec-run2.json` / `mutation-ledger-run2.json` — 権威走。
  **7/7 KILLED、MISMATCH 0、SURVIVED 0**。
  ただし M10 は 57 node を赤にする過剰決定であり、`DW-M03` に従い単一理由の証拠から外す。
- `verbatim/` — 段 2 プラン、段 3 敵対レンズ 2 本、段 5 実装子報告、段 6 レビュー 2 本、
  段 6 fix 2 巡の逐語。

## 実測

- 焦点走 (9 file、計算ノード): fix 前 21 failed → 1 failed → **710 passed / 4 skipped**。
  `test_s8b_approved.py` の `ModuleNotFoundError: No module named 'tests'` は
  file 選択走固有の偽赤で差分由来ではない。
- 段 5 / 段 6 の codex 子は pytest を 1 度も実行していない (ログインノードの gate が拒否し、
  子は dispatch できない)。テスト実測はすべて親が計算ノードへ dispatch した。

## scope 外として返す real 所見

- 床値経路が実行する `perf` の realpath・identity が toolchain binding に無く、`PATH` 先頭の
  wrapper で counter 完備性を operator が on/off できる。[T-967] / [T-970] (F89 未裁定) と
  同じ閉包。**本 wave 単独で operator 制御の除外を閉じたとは主張しない。**
- `competing_process` の自己申告で測定済み session を捨てうる穴は wave 前から在り、
  台帳上も別 wave の責務。本 wave は「measure が完了した session は証跡提出を免除しない」
  ことで悪化だけを防いだ。
