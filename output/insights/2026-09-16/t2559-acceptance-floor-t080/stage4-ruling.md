---
authority: none
default_effect: no-state-change
---

# 段 4 裁定 — 受入全走の高速化・効率化 (2026-09-16)

親が段 2 plan と段 3 の 2 レンズを real/refuted で裁定した記録。可変状態の正本ではない。

## 0. 結論

**本 wave では実装しない。** in-scope の高速化候補 3 本はいずれも、受理集合を変えるか、
既存 assert が検出しない観測変化を伴うか、効果の符号が実測で確認できなかった。
ユーザー裁定 項35「prewarm 等は効果を先に測り、未確認のまま実装しない」に従う。
成果は実測による律速の再確定、前提 2 件の反証、案の可否の裁定、裁定パッケージ 4 件である。

## 1. 親 brief の訂正 (レンズ A・B の指摘を採用)

| # | 指摘 | 判定 | 訂正後の記述 |
|---|---|---|---|
| a | 「消費側は output を 4 path しか参照しない」 | **real** | 誤り。`orchestrator/campaign/t080_freeze_migration.py` の 4 定数は宣言にすぎず、`verify_receipt` は holdout の `search_repository` に入る。`orchestrator/campaign/s8b_holdout_freeze.py` の `enumerate_repository_files` は **repo 全体 (tracked regular + 非 ignored untracked + ccbench submodule)** を列挙し、以降で全件を open/read/decode する。known builder も campaign 成果物を glob で探索する |
| b | 「base 構築 1 回 = 144 秒」 | **real** | 誤帰属。計測元 `test_t080_shared_base_builds_real_builder_once_across_processes` は `issue_receipt=False` で、**base→test コピーを 2 回**と process 起動・config 検査を含む。base 構築単体に帰属できない |
| c | 「t080 群 2611.1 秒 = shard-0 の CPU の 32%」 | **real** | 誤り。junit の所要には lock 待ち・I/O 待ちが入り CPU 時間ではない。「shard-0 の node 所要総和の 32%」と書く |
| d | 「単独走 314.59 秒なので 222 秒は混雑でなく固有費用」 | **real** | 強すぎる。login 単独走も共有資源の混雑から独立でない。言えるのは「単独走でも 300 秒級だった」までである |
| e | 「1,852 件→22,976 件 と 15〜22 秒→144 秒 が対応する」 | **real** | 証明されていない。file 内 comment の 15〜22 秒は 2026-07-27 の別測定区間で、144 秒とは測定対象が違う。全件処理の存在はコードで言えるが、25.5 秒超過の主因が成長項だとは言えない |
| f | 「最遅 shard 325.5 秒」の測定面 | **real** | junit `time` の shard 別中央値であり、D1620 が定める canonical receipt の最遅 shard wall ではない |
| g | アンカー誤り | **real** | `orchestrator/` の copytree は T:1380 (T:1373 は `git init`)、helper は T:964、可視集合 assert は T:1705–1707 |

**(P1) は反証、(P3) は未証明**として記録する。(P2) は部分反証 (§2-2)。

## 2. 候補案の裁定

### 2-1. 案 A (複製する output を固定 whitelist へ限定) — **不採用**

レンズ A 所見1 を **real** と裁定する。非除外 output の任意の可視 file に三軸 conjunction が
入ると、現行は fixture へ複製され発行 subprocess の production scan が拒否する。whitelist は
この拒否経路を消す。既存の未知性負例は fixture 作成**後**に root 直下へ file を置く形なので、
この脱落を検出しない。known-axes 側にも同型がある (glob に一致する追加候補を隠すと複数候補拒否が消える)。
**node 集合・assert の文字列が同じでも受理集合が拡大する。規律 2 により採らない。**

### 2-2. 案 B (実 repo の object store 全体を alternates で借りる) — **不採用**

レンズ A 所見2 を **real** と裁定する。実 repo にあり fixture に無い recorded commit が
alternates 経由で見えると、ancestry が `missing-commit` から `not-ancestor` へ変わりうる。
report の独立期待値との比較は 17 observation のうち先頭 15 件しか行わず、report と verifier は
同じ object store を見るため一致してしまう。**既存 assert はこの観測変化を検出しない。**
加えて貸出元の prune で借り手が object を失う (fixture の `gc.auto=0` は貸出元を保全しない)。

### 2-3. 案 C (必要 blob だけ fixture 内へ移送し独立 index を組む) — **本 wave では採らない**

レンズ A 所見4・レンズ B 所見3/4 を **real** と裁定する。C は係数削減であって成長比例を断たない。
親が主項を実測した結果 (§3) は「下限は非常に低いが、その下限に届く経路は案 B と同じ
object store 露出を必要とする」であり、自己完結化 (660 MB の pack 化) は削減分を食う見込みである
(未測定)。効果の符号が確認できない以上、項35 に従い実装しない。

## 3. 親の実測 (repo 外 probe、/tmp 上の複製 tree に対して実施)

### 3-1. index 化の現行費用と下限

| 方式 | index 化 | write-tree | commit | tree OID |
|---|---|---|---|---|
| A 現行 `git add -A` | 79.33 / 114.37 / 191.30 秒 | 3.93 秒 | 0.25 秒 | 637411045f4e |
| B 既存 OID を `update-index --index-info` | **0.03 / 0.04 秒** | **0.60 秒** | commit-tree **0.01 秒** | 00d210d723e7 |

- 複製 24,017 件のうち **24,017 件すべて**が実 repo の index entry と path 一致した (clean worktree)。
- B は実 repo の object store を alternates で見せて成立している。
- B の `git commit` 経由は 69.05 / 121.22 秒かかる (index-info が stat 情報を持たないため refresh が走る)。
  `write-tree` + `commit-tree` を直接使うと 0.61 秒で済む。

### 3-2. tree 差はちょうど 1 file で、原因は現行 fixture 側にある

差分は `orchestrator/tests/fixtures/sort_swo_masstree/config.h` の 1 件だけだった。
B 側の OID は実 repo HEAD の blob と一致し、worktree 実体も 10,448 bytes ある。
原因は `orchestrator/tests/fixtures/sort_swo_masstree/.gitignore:8` の `/config.h` である。
実 repo では tracked なので ignore より優先されるが、fixture は `git init` からの `git add -A` なので
**この tracked file を取り込んでいない**。fixture の可視集合が実 repo と 1 件ずれている。

### 3-3. 意味を変えない圧縮設定では効果を確認できなかった

同一 tree に対し `.git` を作り直しながら 2 巡した。

| 方式 | round 1 | round 2 | objects |
|---|---|---|---|
| A0 現行 (既定) | 87.95 秒 | 26.76 秒 | 164.7 MB |
| A1 `core.compression=0` | 91.04 秒 | 7.95 秒 | 610.3 MB |
| A2 `+core.looseCompression=0` | 106.72 秒 | 7.46 秒 | 610.3 MB |

**3 方式の tree OID はすべて同一** (637411045f4e) で、圧縮設定が意味を変えないことは確認できた。
しかし round 1 と round 2 で効果の符号が反転しており、**時間効果は確認できていない**。
login node の外乱は同一操作で 20.64〜571.40 秒 (28 倍) に及ぶ。

## 4. 数値モデルの扱い

レンズ B 所見1/2/5/6 を **real** と裁定する。

- `144 + 8.47 + 70 ≈ 222.51` は異なる測定対象の和であり、成分モデルの検証ではない。
  「base 118.54 秒未満」という目標値は撤回する。
- 「最長 node 197 秒未満」は `wall = 65 + 29.6 + span` と `span − 最長 node = 8.49 秒`を
  固定したモデル内の必要条件であり、一般的な必要条件ではない。
- 単発 A/B では目標 25.5 秒を走間変動から分離できない。同日 n=103 の代表 node 分布は
  幅 283.9 秒 (198.8〜482.7)、中央値から最小への自然変動だけで 29.0 秒ある。
  レンズ B の感度分析では wall の σ=20 秒でも各条件 10 走、σ=50 秒なら 61 走が要る。
- したがって本 wave は **「受入全走が 5 分を切った」とは主張しない。**

## 5. 変異事前登録

実装面の差分がゼロなので、DW-S04 に従い変異 matrix を免除する。受入全走は免除しない。

## 6. 裁定パッケージ候補 (scope 外の real 所見)

1. **成長比例の構造そのもの。** t080 e2e は実 repo の git 可視 output を fixture へ写し、
   production scanner がその全件を read/decode する。tracked output は 2026-07-27 の 1,852 件から
   2026-09-16 の 22,976 件へ増えた。これを断つには「fixture が実 repo の output を写す」設計
   (= 受理集合) を変える必要があり、親の一存では決めない。
2. **検出力の重複。** fixture 側の全件 scan が守る「実 repo の output に三軸語が無いこと」は、
   実 repo を直接 scan する検査とも重なる。後者は `orchestrator/tests/growth_test_holds.py` で
   保留登録されている。どちらがこの検出力を持つべきかはユーザー裁定事項。
3. **fixture の可視集合が実 repo と 1 件ずれている** (§3-2)。fixture は
   `orchestrator/tests/fixtures/sort_swo_masstree/config.h` を取り込めていない。
   取り込むと scan 対象が 1 件増える。忠実性の是正だが所要は増える方向である。
4. **report の独立検算が 17 observation のうち先頭 15 件しか覆っていない** (レンズ A 所見2)。
   案 B を採らなくても残る検出力の穴である。
