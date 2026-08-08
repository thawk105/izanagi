# [T-642] 段 1 brief — DW-S04 射程改訂 (P3)

## scope

`docs/dev-wave/core.md` の `DW-S04` 末尾 2 行 (79-80 行) だけを書き換える。他ファイル・他節・
入口 (`.claude/commands/dev-wave.md`) は 1 byte も変えない。コード・テストの差分はゼロ。

## 確定済みユーザー裁定 (2026-08-08 /rulings、一次控え §43)

`DW-S04` の射程を「実装差分ゼロの wave は**変異 matrix だけ**対象外。実 repo を読むテストが
あるなら**受入全走は走らせる**」に改める。docs 起因の赤の検出力を契約に合わせる。

## 実測済みの前提 (brief 前に確認)

- 対象文は `core.md:80` の 1 箇所のみ。同文は repo 内の他の正本に存在しない
- `docs/dev-wave/**` 合計 = **25196 / 25200 bytes (余白 4)**。core.md 個別 cap 9600 (現 8646) は非拘束
- `DW-S04` 本文に機械 pin なし。`check_docs.py` は `## DW-S04` 節の実在のみ検査。`4→7→8→9` の
  literal pin も無い
- 並行 wave 5 本のうち `docs/dev-wave/**` を編集するものは無い (T-632 は入口ファイルのみ)

## 不変条件

1. `docs/dev-wave/**` 合計 ≤ 25200 bytes。**予算引き上げも他ファイルの縮約審査もしない** (T-641 裁定 (c))
2. 「実装しない」裁定時の段 5・6 skip と `4→7→8→9` の規範を失わない
3. `## DW-S04` 見出しと節 ID を変えない (check_docs の節実在検査)
4. 入口ファイルを触らない (T-632 wave が同ファイルを編集中 — land 衝突を作らない)

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 増分 bytes は 79-80 行の圧縮で**自弁**する。案 O = 225 bytes (現 227) で正味 **−2 bytes**。
  重複を理由に他文を削除する払い方は採らない
- **(P2)** 「実 repo を読むテストがあるか」の判定主体は wave 親であり、判定を機械化する新 gate は
  作らない (予算 4 bytes では新節を作れない。機械化は scope 外)
- **(P3)** 本 wave 自身が新契約の最初の適用対象 (docs-only・実装差分ゼロ) であり、受入全走を走らせる
- **(P4)** 段 5 実装子は不要。docs-only の本文編集は凍結境界どおり親が行う

## 改訂案 O (段 2/3 の攻撃対象)

```
「実装しない」裁定のときだけ段 5・6 を飛ばして `4→7→8→9` とする。対象外は変異 matrix だけで、
受入全走は実 repo を読むテストがあれば走らせると worklog に書く。
```

## 成果物の形

`core.md` の 2 行差分、worklog fragment (`docs/spool/worklog/`)、insights 1 本。変異 matrix は
実装差分ゼロのため対象外、受入全走は新契約に従って実走する。

## 成果物影響 (DW-G05)

実装しない場合、docs のみの wave が契約どおり受入全走を省き、`check_docs` / `spool fold` が拾う
赤 (= worklog・decisions・failures の 3 台帳と成果物索引の破損) を land 前に検出できないまま
main へ入る。台帳の値と参照が壊れたまま certified 報告の索引に載る。

## 並列分割・環境

段 2 = codex plan 1 本 (read-only)、段 3 = 敵対 2 レンズ並列 (read-only)。段 5 は親編集。
受入全走は repo root で `python3 tools/run_tests.py` (追加 flag なし)。Pegasus のログインノードから
計算ノードへ自動 dispatch される。
