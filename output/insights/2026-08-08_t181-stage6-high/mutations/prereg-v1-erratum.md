# 変異事前登録 (DW-M01) — 実装前に親が登録する

対象: `tools/check_docs.py` の段 6 reasoning pin と、B-02 / B-04 の gate 強化。
登録時刻の anchor commit: `b97ad3b5` (docs)。実装 commit 後に `DW-M07` で anchor を再検証する。

各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つに絞れること」を
実装後にコードで確認する。確認できなければ登録を取り下げ、実効 gate へ再照準する。

| # | 変異 | 期待 kill | 単一理由性の懸念 |
|---:|---|---|---|
| M1 | pin tuple から `DW-S06-A` の行を削る | S06-A=max を拒否するテスト | なし (S06 固有) |
| M2 | pin tuple から `DW-S06-C` の行を削る | S06-C=max を拒否するテスト | なし (S06 固有) |
| M3 | exact-list 判定 `values != [expected]` を `expected not in values` へ弱める | decoy / 重複を拒否するテスト | **既存 S02/S03 decoy テストも赤くなる。** comparator 共有のため S06 単独 nodeid の receipt を別に取る |
| M4 | B-02 の可視化先行を raw 抽出へ戻す (pin 側) | hidden whole-section 負例 | **M5 と冗長。** 単独で SURVIVED しうる → M7 を併記 |
| M5 | B-02 の可視化先行を raw 抽出へ戻す (必須 H2 inventory 側) | hidden whole-section 負例 | **M4 と冗長。** 同上 |
| M6 | B-04 の終端厳格化を外す | `reasoning=high/max` 等を拒否するテスト | なし (B-04 固有) |
| **M7** | **M4 + M5 の両層同時変異** (`DW-M04` に従い kill 期待を事前登録) | hidden whole-section 負例が赤 | 冗長 gate の裏取り。**これが B-02 の実効 kill 証拠** |
| M8 | production path から pin 呼出しを削る | production path 負例 | **既存 S02/S03 production テストも赤くなる。** finding 集合の exact 一致を要求する形にして S06 固有性を確保する |

## 登録から外した候補

- 段 2 プランの変異 #7 (重複節の先頭だけ受理) — global H2 uniqueness (`check_docs.py:3634-3643`) が
  独立に拒否し続けるため実効受理集合が変わらない。`DW-M03` に従い**冗長 gate と明記して単独変異の
  証拠から外す**。B-07 の指摘どおり。

## 受理集合を縮小する wave の追加登録 (DW-M01)

本 wave は受理集合を縮める (S06 に値を要求し、曖昧値と hidden section を拒否する)。
承認外の過剰拒否を検出する**正例**も登録する。

| # | 正例 | 期待 |
|---:|---|---|
| P1 | 実 repo の現行 docs (S02=max, S03=max, S06-A=high, S06-C=high) | 通る |
| P2 | S06-A / S06-C の可視 `high` + comment / fence 内の `max` | 通る (不可視は無視) |
| P3 | `DW-S06-B` に effort literal が無い現状 | 通る (継承のため literal 不在が正) |
