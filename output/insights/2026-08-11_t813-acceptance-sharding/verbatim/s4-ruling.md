# 段 4 裁定 — [T-813]

親裁定。段 2 (plan/sol) と段 3 (consult/sol・luna) の所見を real/refuted と採否で確定する。
**本 wave は「実装しない」で終端する (4→7→8→9)。** 実装差分ゼロ、成果物は裁定パッケージ + 記録。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | 段 2 | P3(a) 集合一致では不足、順序付き多重集合が要る (conftest が収集中に marker 付与・収集終了で並べ替え) | **real** | 採用。§1 (A) を書き換えた |
| 2 | 段 2 | P3(d) `max(rc)` は誤り。rc は名義尺度、runner 独自 rc 13〜16 と混在 | **real** | 採用。§1 (E) を型付き集約へ置換 |
| 3 | 段 2 | P3(c) gate は「各シャード」でも「全体で 1 回以上」でもない。594/632 は snapshot に対し exactly once、705 は実行 root ごと、1677 は分類保証 | **real** | 採用。§2 を全面差し替え |
| 4 | 段 2 | M2 は不成立。xdist が `-n` 非ゼロ時に `--tx` を local popen で上書きする | **real (親が xdist/plugin.py:325 を逐語確認)** | 採用。M2 を「不成立」と明記 |
| 5 | 段 2 | `--rsyncdir` は 4.0 で削除予定、既定 ignore `.*` が `.git` を送らない | **real** | 採用 |
| 6 | 段 2 | M3 は `-b k` が正しく、leader 1 台方式ではポイントだけ k 倍で短縮にならない | **real** | 採用 |
| 7 | 段 2 | F-9 の provider は `test_reflux_ir.py`。consumer は 5 file・9 import 文が静的下限で、一部は同居により赤が隠れている | **real** | 採用。§3-1 に反映 |
| 8 | 段 3 sol | `X` が ignored bytes を束縛しないので `A0(X)` が関数でない | **real** | 採用。§1 (D) の中心に置いた |
| 9 | 段 3 sol | group-atomic では排他閉包にならない (未登録 reader/writer 9 node + T-080 fail-open + 別名 group の実 Git writer + runner writer) | **real** | 採用。§3-3 として独立節にした。**本 wave 最重要の所見** |
| 10 | 段 3 sol | 705 の predicate は存在検査だけで gitlink pin・HEAD・dirty を見ない | **real** | 採用。§2 に明記 |
| 11 | 段 3 sol | 赤の帰属は receipt ID では機械化できない。差分再走が要る | **real** | 採用。§3-4 |
| 12 | 段 3 sol | 親の性能値は採用値にできない (in-sample・意味論赤・queue・worker 交絡・n=1) | **real** | 採用。§4 に限界 6 点として明記し、§0 の位置づけを「signal であって採用値でない」に変更 |
| 13 | 段 3 sol | 「receipt は repo 内固定」は過剰一般化。`dispatch_compute` に repo 外 `output_root` seam がある | **real** | 採用。§3-2 を訂正 |
| 14 | 段 3 luna | S(k) モデル。`S(∞) ≥ F_fixed + 263 秒` | **real** | 採用。§5 |
| 15 | 段 3 luna | 単一 lease の処理能力は 2.4〜4.0 wave/時、理想でも 2.8〜5.2 wave/時。4 倍にならない | **real** | 採用。§5 |
| 16 | 段 3 luna | 到着率 λ が未計測なので queue 短縮量を保証できない | **real** | 採用。§9 の筆頭 |
| 17 | 段 3 luna | 費用対効果の最上位は [T-812] (自己保持 deadlock)。追加ノード無しで 18〜20 分級の無効占有を除去 | **real** | 採用。§7 の冒頭に置いた |
| 18 | 段 3 sol | M6 (旧 M5) は「単一 collection」ではない。collection は worker ごとに走る | **real** | 採用。M6 の記述を訂正 |
| 19 | 段 3 sol | I1 の全称式には witness が無い。有限 probe は反例探索であって証明ではない | **real** | 採用。§1 に明記し、fail-closed fallback を要求に加えた |

**refuted / 不採用にしたものは無い。** 段 2・段 3 の指摘はすべて file:line か実機確認で裏が取れた。

## 親 brief の (P#) の帰結

- **(P1) file 単位:** 条件付き維持。argv と manifest の単位としては妥当だが、**意味論的独立単位ではない**。
- **(P2) group-atomic:** **否定。** 排他閉包にならない (所見 9)。
- **(P3)(a)(c)(d):** **否定・書き換え** (所見 1・2・3)。(b) は ordinal 主鍵へ強化。(e) は支持し**事前条件**へ格上げ。
- **(P4) 形状判定を manifest 証明へ:** 必要だが不十分。**後半 (`--tx` allowlist で足りる) は撤回** (所見 4)。
- **(P5) 本 wave は実装しない:** **支持。確定。**

## 変異事前登録 (DW-M01)

**実装差分ゼロのため免除。** 変異 matrix は作らない (DW-S04 の明示的免除に該当)。
受入全走は免除されないため、記録 commit を含む最終 tip で実走する。
