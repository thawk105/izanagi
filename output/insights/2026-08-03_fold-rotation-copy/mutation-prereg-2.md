# 変異事前登録 — scope 拡張分 (T-352 / T-358)

**登録時刻 = 2026-08-03 12:30 (実装子 A / B が走行中、実装完了前)。**
逐語 anchor (`old` / `new`) は実装完了後に確定し、`DW-M07` に従って最終 commit へ anchor を再検証してから
本走する。本書は gate の位置・期待 node・第一失敗 code の事前登録である。

`review2.md` 所見 9 の指摘に従い、**第一失敗 code を各変異に明記する**。
別 gate が先に発火する候補、受理集合を変えず診断文字列だけで赤くなる候補、
`PYTHONHASHSEED` 等で揺れる候補は登録しない。

## T-352

| id | 変異する gate | 期待赤 node (spec2.md の項目) | 第一失敗 code |
|---|---|---|---|
| N01 | `remaining` の exact-one 必須検査を無効化 | 項目 1 | `completion-remaining-field` が出ない |
| N02 | 値語彙 `none` の比較を任意非空値へ緩和 | 項目 2 | 同上 |
| N03 | cardinality `== 1` を `>= 1` へ緩和 | 項目 3 | 同上 |
| N04 | **機械 field 群の位置束縛を外し、item block 全体の raw regex にする** | 項目 4 (fence / comment decoy) | 同上 |
| N05 | `remaining` 行の canonical 除去を省略 | 項目 5 | canonical 出力の exact 比較 |
| N06 | 禁制語 regex (`残件あり` / `一部完了`) を削除 | 既存 `test_n18_...` | `completion-remaining` が出ない |
| P02 | `更新` / `見送り` にも `remaining` を要求する (**過剰拒否の正例**) | 項目 7 | `completion-remaining-field` が誤発火 |

N04 は今回の敵対検証が実際に見つけた穴に直接帰属する。手前に同じ入力を拒否する検査は無い
(valid ID・indent・base が揃い、禁制語にも一致しない入力を使う)。

## T-358

| id | 変異する gate | 期待赤 node (spec2.md の項目) | 第一失敗 code |
|---|---|---|---|
| N07 | 追記位置を「先頭行の行末」から「block 末尾」へ変える | 項目 10 / 11 / 12 | byte-exact oracle の不一致 |
| N08 | 対象探索を fence / comment 不可視化なしの raw regex にする | 項目 19 | `deferred-append-duplicate` の誤発火 |
| N09 | target 不在を `continue` で握り潰す | 項目 16 | `deferred-append-missing` が出ない |
| N10 | 探索範囲を `### 裁定・完了記録` まで広げる | 項目 17 | `deferred-append-missing` が出ない |
| N11 | 可視な重複 ID を last-wins で選ぶ | 項目 18 | `deferred-append-duplicate` が出ない |
| N12 | 同一 suffix の重複拒否を外す | 項目 24 | `deferred-append-duplicate-suffix` が出ない |
| N13 | action 順序で `見送り追記` を `見送り` より前に置く | 項目 20 | `worklog-action-order` が出ない |
| N14 | 逐次意味論を「fold 開始時点から存在する項目だけ」へ縮める | 項目 21 | `deferred-append-missing` の誤発火 |
| N15 | 空 / 空白のみ suffix の拒否を外す | 項目 15 | `deferred-append-shape` が出ない |

## 登録しない候補と理由 (review2 所見 9)

- **`_DeferredAppend` を `_Operation` へ混ぜる変異**: 対象が active でないため、保存則検査より手前の
  `transition-target` が先に拒否する = 偽 kill。代わりに項目 25 は parse 結果の
  `operations` / `deferred_appends` を直接検査する形でテスト側が固定する。
- **resume 時に同じ `after_bytes` を再書込みする変異**: after target は skip されるため suffix が
  増えず、テストが緑のままになる = 恒真。代わりに resume は「phase への write が発生しないこと」を
  検査する形にする。
- **error ID を改名するだけの変異**: 受理集合が変わらないのに負例が赤くなる = 診断文字列 kill。
- **fragment 収集を実 FS 列挙順 / `set` 反復順へ変える変異**: 収集時点で既に sort 済みの列を受け取るため
  局所変異として成立せず、`set` 版は `PYTHONHASHSEED` で kill / survive が揺れる。
  順序は exact `(wave, seq, item index)` oracle と固定 `fold_date` でテスト側が固定する。
