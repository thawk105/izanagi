# 段 4 裁定 — [T-765] DW-S04 免除条項の曖昧さ解消

## 所見の裁定

| # | レンズ | severity | 判定 | 裁定 |
|---|---|---|---|---|
| A1 | A | blocker | **real・採用** | 段 2 推奨の `裁定を受けて` は因果・時系列 `R` を追加し、`C∧Z∧R` とも `C_external∧Z` とも読める。不採用。 |
| A2 | A | blocker | **real・採用** | `実装差分` の射程は入口の「実装面」(コード・テスト・実行可能 probe / harness / script・機械設定) が正本。親 (P1) の「コード・テストだけ」は却下。文面も `実装面差分ゼロ` へ束縛する。 |
| A3 | A | blocker | **real・採用** | 本 wave の自己免除経路を段 4 で閉じる (下記)。 |
| A4 | A | must-fix | **real・採用** | D237 は現役の canonical decision で、見出しが Z 単独十分条件に見える。遡及改変せず、前向きの decisions fragment で読みを確定する。 |
| A5 | A | nit | **real・採用** | main が `034d7590` へ進んでいた。取り込み済み、L1 は 10,606 で不変を再実測。 |
| B1 | B | blocker | **real・採用** | A1 と同一。受動態で同一 wave へ束縛する案を採る。 |
| B2 | B | must-fix | **real・採用** | 次点の `かつ` 案も不採用 (`裁定` と `wave` の並列に読める)。 |
| B3 | B | must-fix | **real・採用** | A2 と同一。 |
| B4 | B | must-fix | **real・採用** | 親 brief の「[T-786] 段 2 が (ii) を採った」は一次資料より強い。正しくは「(ii) に基づく一般化案を候補提示したが、段 2 自身が非等価と認め、段 3 レンズ A が blocker とした」。記録はこちらを使う。 |
| B5 | B | must-fix | **real・採用** | `C=false` は docs-only であることでなく、**規範文を置換する通常経路である**ことを根拠に段 4 で明示裁定する。 |
| B6 | B | nit | **refuted・不採用** | `matrixのみ` の 100 bytes 案は、`matrix` と助詞の間の空白を落として 1 byte 稼ぐもの。本文書の表記規約 (`matrix だけ`、`matrix、`) と不整合で、体裁の一貫性を 1 byte で売ることになる。`だけ` を維持する。 |

## 確定した置換文

```
旧: 免除は実装差分ゼロの「実装しない」裁定の変異 matrix だけ。
新: 免除は「実装しない」と裁定され実装面差分ゼロの wave の変異 matrix だけ。
```

- **101 bytes** (旧 83、+18)。L1 = 10,606 → **10,624 / 10,625 (余白 1)**。予算値は 1 bytes も上げない。
- 受動態 `と裁定され` が裁定の被適用者を `wave` に固定し、A1/B1 の因果・別 wave 読みを閉じる。
- `実装面差分ゼロ` が入口の定義語へ束縛し、A2/B3 の「script・probe だけ変えた wave が Z=true」を閉じる。
- 免除対象は `変異 matrix だけ` のまま。直後の受入全走非免除文は 1 文字も変えない。
- 意味範囲: `C∧Z` を維持。拡大 (Z 単独) も縮小も起こさない。

## 本 wave 自身の扱い (A3/B5、変更不能な裁定)

- **C = false。** 根拠は「docs-only だから」ではなく、**本 wave は段 4 で規範文の置換を実装すると裁定した通常経路 (`4→5(省略)→6→7→8→9`) であり、`4→7→8→9` の「実装しない」経路を採っていない**こと。
- **Z = true。** 実装面 (コード・テスト・実行可能 probe / harness / script・機械設定) の差分はゼロ。
  運転 script・prompt・probe はすべて repo 外 (`dev-wave-jobs/dev-wave-t765-exemption-wording/`)。
- したがって `C∧Z = false` で、**本 wave は変異 matrix を免除しない**。新文面を自分の免除根拠に使わない。
- 受入全走も免除しない (同節次文。実 repo を読むテストは
  `orchestrator/tests/test_check_docs.py::test_dev_wave_waiter_consumer_pins_accept_current_docs_contract` 等が実在)。

## 変異事前登録 (DW-M01)

**実効 gate の再照準を伴う。** 本 wave の変更を機械的に拒否できる層は
`python3 tools/check_docs.py` の L1 層予算だけである。real repo の L1 超過で赤になる **pytest node は存在しない** —
`test_dev_wave_layer_budget_rejects_plus_one` は `_build_min_repo()` の合成 repo を測り
(`orchestrator/tests/test_check_docs.py:2632-2675`、参照ファイルは同 726-760 行で合成)、
実 repo の bytes を見ない。よって `tools/mutation_harness.py` の pytest node 抽出では KILLED を作れない
(`DW-M08` の期待 node 契約が成立しない)。`DW-M01` の F28 経路に従い、**実効 gate へ再照準した
gate 変異 1 件**を親が `DW-O19` の規律で実行する。

- **M1 (gate 変異)**
  - anchor: `docs/dev-wave/core.md` の確定文 (101 bytes、統合 commit 後の逐語)
  - 変異: 意味等価な 104 bytes 版 `免除は「実装しない」と裁定された実装面差分ゼロの wave の変異 matrix だけ。`
  - 期待: `python3 tools/check_docs.py` が **rc=1** かつ finding は
    `docs/dev-wave/**: L1 unique footprint 10627 bytes > 予算 10625 bytes` **のみ** (単一理由性)
  - 復元: `git checkout --` 後に commit と byte 一致を確認する
- **M0 (正例)**: 確定文のまま `python3 tools/check_docs.py` が rc=0

**機械変異では証明できないもの:** 曖昧さの解消そのもの (本文の意味を pin する検査は存在しない)。
これを KILLED や緑として記録しない。代替証拠は真理値表、独立 2 レンズの敵対レビュー、consumer 棚卸し、
段 6 焦点レビュー、段 7 の逐語凍結である。

## scope 外として裁定パッケージへ返すもの

1. **D237 見出しと [T-642] 自己免除の運用実績。** 遡及改変はしない (歴史記録)。前向きの decisions
   fragment で読みを確定するところまでが本 wave。**docs-only wave に免除の明示的な carve-out を作るか**は
   免除範囲の変更であり (a) 系の裁定になるため、実装せずユーザーへ返す。
2. **codex 子の `evidence_status=invalid` (2 例目)。** 段 3 レンズ A は `codex_exit_code=0`・`validator_rc=0`・
   rollout の `session_meta=1` / `turn_context=1` / model・effort・cwd 一致がすべて成立しながら
   `launcher_rc=1` で未採用になった。[T-786] 段 6 fix 子と同型で独立 2 例目 (`DW-G03` の族一般化条件に到達)。
