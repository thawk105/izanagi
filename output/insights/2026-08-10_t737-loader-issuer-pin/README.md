# [T-737] 量化縮退の integration pin — production loader と発行 tool の 2 層へ穴を塞ぐ wave

wave branch: `worktree-dev-wave-t737-loader-issuer-pin`
基準 commit: `7a84b638` / 統合 `4d81ac48` / fix `3a5a76d7` / fix2 `f9b44c4c` / 受入 tip `de46bdc3`
正本: `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md` §5 選択肢 G

## 何をして、何をしなかったか

**した。** `_validate_activation_transition` の 2 つの量化点に対する `[:N]` 縮退族を、
private gate の直呼びではなく **65 env の合成 registry で実際の入口から**通す pin を 8 本追加した。
production コード (`orchestrator/campaign/**`、`tools/**`) は **1 byte も変えていない**。

**していない。** 選択肢 A / A′ / B1 / B2 / C1 / C3 の候補採用、hypothesis 依存の導入、
本番側 guard (選択肢 D)、`ident` 経路の pin。

## この wave が確定させた事実 (すべて実測)

- **新 pin は G / P 双方の `[:N]` を N ∈ {1, 4, 8, 64} で殺す。** 最終 commit `f9b44c4c` の
  変異 matrix A = **8/8 KILLED**、事前登録と完全一致 (MISMATCH 0)。
- **変更前 HEAD (`7a84b638`) の既存テストは N=4 と N=64 を殺せない。** 変異 matrix B =
  **4/4 SURVIVED**、事前登録と完全一致。**これが純増検出力の実測である。**
  N ≤ 3 は既存 4 env fixture が既に殺すため純増ゼロ (`test_transition_rejects_fourth_env_downgrade`
  ほか)。
- **過剰拒否も検出できる。** 変異 matrix C (`+ 1` を落として全 +1 遷移を拒否させる) = **1/1 KILLED**。
- 純増の**実測点は N ∈ {4, 8, 64}** であり、`4 ≤ N ≤ 64` は M=65 fixture に対する**静的な envelope**
  である。N ≥ 65 は **fixture-equivalent** であって program-equivalent ではない
  (関数は任意長の tuple を受けるため、66 env なら `[:65]` は非同値)。**族は閉じていない。**

## 層ごとに何が言えて、何が言えないか (誇張しないための区別)

| 層 | 入口 | 言えること |
|---|---|---|
| leaf | `activation.load_activation_state` | **semantic kill。** 縮退で拒否 → 受理へ反転する |
| production loader | `env_contract.current_activation_state()` | **到達性 + 診断感度**。量化点まで到達し拒否理由が遷移 gate に帰属することは示すが、**受理集合の反転は示さない** |
| 発行 tool | `issuer.main(argv)` | **semantic kill。** 縮退で record が publish される |
| `ident` | `ident._load_current_activation_state` ほか | **未被覆** |

production loader 層が semantic kill にならないのは、縮退が gate を通ったあとに
`_verify_entry_calibration` (`env_contract.py:535`) が存在しない合成 calibration を検証して
**別理由で**拒否するためである。閉じるには 65 env × 2 世代の calibration 成果物を作るか、
`_verify_entry_calibration` を patch して correctness gate を迂回するかのどちらかが要る。
後者は採らない。前者は裁定へ返す。

**この mask は段 6 の敵対レビュー 2 本 (`s6-lensC.md` / `s6-lensD.md`) が独立に検出した。**
親は段 4 の事前登録で「手前に同じ入力を落とす層が無いこと」しか確認しておらず、
**後続の層**を見ていなかった。F28 の同型再発である。

## 並行 wave との衝突が実際に起きた (guard が止めた)

段 3 のレンズ B が「[T-720] が発行 tool の import 経路を変えたら patch が空振りし、
実 authority へ publish しうる」と予測したため、issuer node に fail-closed guard を置いた。
受入前に local main を取り込んだところ **[T-720] の import 統一が landed しており**、
guard が `KeyError` で発火して受入 1 走目が 4 赤になった。
**guard は設計どおり動いた。**壊れていたのは guard の意図ではなく、namespace literal に
依存した実現手段である。fix2 (`f9b44c4c`) で、patch した seam が実際に呼ばれた証跡を assert する
namespace 非依存の形へ置き換えた。例外台帳へ literal を登録する直し方は採らない。

## 受入

`de46bdc3` で **8020 passed / 20 skipped / rc=0 / 511.90 秒**。
1 走目 (`57c72a66`) は上記の namespace 変更で 4 赤 (原因 1 件)。逐語は `accept-run1` として
job artifact に残し、insights には最終走だけを凍結する。

## ファイル

- `s1-brief.md` 段 1 brief / `s2-plan.md` 段 2 プラン
- `s3-lensA.md` `s3-lensB.md` 段 3 敵対相談 (正しさ境界 / scope・実効性)
- `s4-adjudication.md` 段 4 裁定と変異事前登録
- `s5-impl.md` 実装子報告 / `s6-lensC.md` `s6-lensD.md` 段 6 敵対レビュー
- `s6-fix.md` fix 報告 / `s6-refocus.md` 焦点再レビュー / `s6-fix2.md` namespace fix 報告
- `mutation-spec-{A,B,C}.json` 事前登録 / `mutation-ledger-{A,B,C}.json` 本走台帳
- `mutation-ledger-{A,C}-run1.json` fix2 前 (`3a5a76d7`) の 1 走目。**erratum として保存する** —
  結果は本走と同じ (A 8/8 KILLED、C 1/1 KILLED) だが、`DW-M07` に従い最終 commit で本走し直した

## 残る穴 (裁定へ返す)

1. `ident.py:211` / `:292` が leaf を直接呼ぶ第 3 の production 経路。certified campaign lock の
   新規作成と再検証に使われる。選択肢 G の「2 層」外のため本 wave では実装していない。
2. production loader 層の M>N semantic kill と正例が無い (上表のとおり)。
3. 実 registry が 3 env 以上へ育ったときの追随。合成 65 env の pin は壊れないが、
   `[:len(GENERATIONS)]` のような実件数依存の縮退は素通りする。
4. 既存の発行 tool test 4 本が `sys.path` を復元しない (本 wave 以前からの欠落)。
