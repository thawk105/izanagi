# 受入 blocker 修正 (案 5) の変異事前登録

**登録の時点を正直に書く。** この登録は fix 子を投入した**後**、**その差分を 1 行も見る前**に書いた。
DW-M01 は「変異は実装前に登録する」と定めており、投入前に書くべきだった。手順違反である。
実装を見てから変異を設計すると事前登録の意味が壊れるため、差分の閲覧前に凍結した。
anchor (old 逐語) だけは実装後に取り、**位置と期待は本文で先に固定する。**

## 何を守る変異か

案 5 が入れるのは「失効した外部証拠に依存する入口だけを精密判定し、不在なら理由付きで skip する」
機構である。守るべき性質は 3 つで、変異はその 3 つに 1 対 1 で対応させる。

1. 不在のときに skip する (これが無いと全 wave が止まり続ける)。
2. **重複は skip にしない** (fail-closed を維持する)。
3. **破損・sha 不一致は skip にしない** (fail-closed を維持する)。

## 登録する変異

| ID | 位置 (実装後に逐語を取る) | exact 変異 | 期待 | kill として数えるか |
|---|---|---|---|---|
| B1 | 新設した可用性判定の呼び出し | 判定そのものを削除し、従来どおり直接読取へ落とす | KILLED | 数える |
| B2 | 可用性判定の「不在」分岐 | 重複 (一致 2 件以上) も skip に倒すよう条件を広げる | KILLED | 数える |
| B3 | 可用性判定の「不在」分岐 | sha256 不一致 / 破損も skip に倒すよう条件を広げる | KILLED | 数える |
| B4 | skip 理由の文字列生成 | 失効した session label を理由から落とす | KILLED | **数えない (診断感度 pin)** |

**B2 / B3 を数える理由:** どちらも「本来赤にすべき入力を緑 (skip) にする」方向であり、
受理集合と fail-closed 挙動を期待と逆向きに変える。DW-M03 の kill の定義に合う。

**B4 を数えない理由:** 受理集合も fail-closed 挙動も変えず、skip 理由の可読性だけを落とす。
段 4 で D1 / D2 を診断感度 pin へ回したのと同じ扱いにする。

## 単一理由性について、実装前に言えること

- B1 の赤理由は「不在時に skip されず error になる」1 つに絞れるはずである。
  前後に同じ入力を skip へ倒す層は現時点で存在しない (既存 `is_dir()` ガードは root の有無しか
  見ず、本件では発火しない)。
- B2 / B3 は、負例テストが「重複」「破損」をそれぞれ独立に構成するなら、
  赤理由はそれぞれ 1 つに絞れる。**正例と負例を同一 node に詰めた場合は絞れない**ので、
  段 6 の PF-02 と同じ理由で node を分ける。分かれていなければ親が差し戻す。
- 実装後に anchor を取った時点で、**上の主張がコードで成立するかを親が確認する。**
  成立しない位置は登録から外し、理由を残す (F28)。

## erratum — 初回 probe は baseline 緑を満たさず中止した

初回 probe (`mutation-blocker-probe-out.json`、spec sha256
`ce979b48...`) は **baseline が `PARSE_ERROR` (rc=1) で、変異を 1 件も実行せずに中止した。**
結果は消さずここへ残す。

- baseline の赤の本文は
  `ValidationError: submodule is not initialized: external/ccbench/third_party/shirakami`
  で、21 error。
- 原因は**レビュー B の P-01 がそのまま発火したもの**である。portable fixture は
  source repo の submodule 実体化状態に依存し、変異用の使い捨て worktree はそれを満たさない。
  `tools/mutation_worktree.py:607-616` は `submodule update --init --no-fetch` を行うが
  **再帰的ではなく**、失敗しているのは入れ子の submodule である。
- **受入全走には影響しない。** 受入は submodule を再帰初期化済みの wave worktree で走る
  (親が wave 開始時に `dev_wave_submodule_init.py` を実行済み)。
  影響するのは変異用の使い捨て worktree だけである。

**再走の変更点 (正直に射程を狭めたことを書く):** runner argv に
`-k "historical_rollout_preflight or require_historical_rollouts"` を足し、
**preflight 機構の検出器だけ**を走らせる。理由は 2 つある。

1. 登録した 4 変異はいずれも preflight helper だけを触り、**検出器は新設の preflight test 4 本**
   である。portable fixture を必要とする node は変異位置と無関係である。
2. 使い捨て worktree では入れ子 submodule を初期化できず、baseline を緑にできない。

**したがって本変異走行が主張するのは「preflight の fail-closed が変異で守られていること」だけ**
であり、portable fixture へ移した 22 node の検出力は**この走行の観測範囲の外**である。
その 22 node は受入全走で実走して確かめる。

## probe の扱い

期待 node の完全集合は実装を見るまで確定できない。**DW-M07 に従い、初回は全件 SURVIVED 期待の
probe として走らせ、観測 node を集めてから KILLED 期待で再登録する。** 初回結果は消さず残す。
