# [T-737] 量化縮退の integration pin — production loader と発行 tool の 2 層へ穴を塞ぐ wave

wave branch: `worktree-dev-wave-t737-rebuild` (基準 main `909914ef`、実装 commit `c0788404`)
正本: `output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md` §5 選択肢 G

**この wave は branch を一度作り直している。** 最初の branch
`worktree-dev-wave-t737-loader-issuer-pin` (基準 `7a84b638` / 統合 `4d81ac48` / fix `3a5a76d7` /
fix2 `f9b44c4c` / 受入 tip `de46bdc3`) は、受入前の main 取り込みで作った merge commit `57c72a66` が
`DW-O17` の「実装面 path が両親と異なれば Codex `role=author` へ」に反していた。並行 wave [T-720] の
import 機械書換えと本 wave のテスト追加が同じ file で結合され、結果が両親のどちらとも一致しないため
checker が実装面の著作と判定する。**親が受入 script の merge message を事前に `role=integrator` だけで
書き、merge が共有 file を巻き込んだ後に条件を再評価しなかったことが原因である。**
既知違反台帳へ登録する裁定を求める案は取り下げ、**merge を一切作らない形で現 main の上へ積み直した。**
最初の branch は残置してあり、削除していない。

## 何をして、何をしなかったか

**した。** `_validate_activation_transition` の 2 つの量化点に対する `[:N]` 縮退族を、
private gate の直呼びではなく **65 env の合成 registry で実際の入口から**通す pin を 8 本追加した。
production コード (`orchestrator/campaign/**`、`tools/**`) は **1 byte も変えていない**。

**していない。** 選択肢 A / A′ / B1 / B2 / C1 / C3 の候補採用、hypothesis 依存の導入、
本番側 guard (選択肢 D)、`ident` 経路の pin。

## この wave が確定させた事実 (すべて実測)

- **新 pin は G / P 双方の `[:N]` を N ∈ {1, 4, 8, 64} で殺す。** 実装 commit `c0788404` の
  変異 matrix A = **8/8 KILLED**、事前登録と完全一致 (MISMATCH 0)。
- **本 wave の追加前 (main `909914ef`) の既存テストは N=4 と N=64 を殺せない。** 変異 matrix B =
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
親は段 4 の事前登録で手前の層だけを読み、gate の**後続**にある別 module の検証層を見なかった。
`DW-M01` は既に「同じ入力を拒否する層が前後に無いこと」を求めているので、
破れたのは規則ではなく適用である。F28 の同型再発として台帳へ追記した。

## 並行 wave との衝突が実際に起きた (guard が止めた)

段 3 のレンズ B が「[T-720] が発行 tool の import 経路を変えたら patch が空振りし、
実 authority へ publish しうる」と予測したため、issuer node に fail-closed guard を置いた。
受入前に local main を取り込んだところ **[T-720] の import 統一が landed しており**、
guard が `KeyError` で発火して受入 1 走目が 4 赤になった。
**guard は設計どおり動いた。**壊れていたのは guard の意図ではなく、namespace literal に
依存した実現手段である。fix2 (`f9b44c4c`) で、patch した seam が実際に呼ばれた証跡を assert する
namespace 非依存の形へ置き換えた。例外台帳へ literal を登録する直し方は採らない。

## 受入

**作り直し後の branch (`c0788404`) で本走した値を正とする。** 値は本 wave の worklog エントリに書く。

作り直し前の branch では 2 走した。1 走目 (`57c72a66`) は上記 namespace 変更で 4 赤 (原因 1 件)、
2 走目 (`de46bdc3`) は **8020 passed / 20 skipped / rc=0 / 511.90 秒** で緑だった。
作り直しで base main が `7a84b638` → `909914ef` へ動いているため、**この 8020 は作り直し後の
land 対象に対する受入結果ではない。**逐語はいずれも job artifact に残す。

## ファイル

- `s1-brief.md` 段 1 brief / `s2-plan.md` 段 2 プラン
- `s3-lensA.md` `s3-lensB.md` 段 3 敵対相談 (正しさ境界 / scope・実効性)
- `s4-adjudication.md` 段 4 裁定と変異事前登録
- `s5-impl.md` 実装子報告 / `s6-lensC.md` `s6-lensD.md` 段 6 敵対レビュー
- `s6-fix.md` fix 報告 / `s6-refocus.md` 焦点再レビュー / `s6-fix2.md` namespace fix 報告
- `mutation-spec-{A,B,C}.json` 事前登録
- `mutation-ledger-{A,B,C}.json` **本走台帳** — 作り直し後の branch で走らせたもの
  (A / C は `c0788404`、B は base main `909914ef`)
- `mutation-ledger-{A,C}-superseded.json` 作り直し前の branch (`3a5a76d7`) で走らせた台帳。
  **同じテスト内容を別 SHA・別 base で測った複製として保存する** — 結果は本走と一致した
  (A 8/8 KILLED、C 1/1 KILLED)。作り直し前はさらにその前 (`f9b44c4c`) でも同結果を得ている

## 残る穴 (裁定へ返す)

1. `ident.py:211` / `:292` が leaf を直接呼ぶ第 3 の production 経路。certified campaign lock の
   新規作成と再検証に使われる。選択肢 G の「2 層」外のため本 wave では実装していない。
2. production loader 層の M>N semantic kill と正例が無い (上表のとおり)。
3. 実 registry が 3 env 以上へ育ったときの追随。合成 65 env の pin は壊れないが、
   `[:len(GENERATIONS)]` のような実件数依存の縮退は素通りする。
4. 既存の発行 tool test 4 本が `sys.path` を復元しない (本 wave 以前からの欠落)。
