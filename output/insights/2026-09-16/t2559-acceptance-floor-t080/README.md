---
authority: none
default_effect: no-state-change
---

# 受入全走の律速の再確定と、t080 fixture 高速化の可否 (2026-09-16)

依頼は「受入全走の高速化・効率化」。結論は **本 wave では実装しない**。
律速を実測で確定し直し、3 つの高速化候補をいずれも不採用と裁定した。

## 一次資料

| 区分 | 所在 |
|---|---|
| 受入成果物 (repo 外) | `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-N/{report.json,junit.xml}` |
| 段 1 親 brief | `stage1-brief.md` (同 dir、訂正前の記述を含む。訂正は `stage4-ruling.md` §1) |
| 段 2 plan (codex, read-only) | `stage2-plan.md` |
| 段 3 敵対レンズ A (検出力・受理集合) | `stage3-lensA.md` |
| 段 3 敵対レンズ B (費用モデル・実効性) | `stage3-lensB.md` |
| 段 4 裁定 | `stage4-ruling.md` |

probe script は repo 外 (job dir) に置き、repo へは入れていない。数値は本書と `stage4-ruling.md`
に逐語で残す。

## 1. 受入全走の律速はどこか (2026-09-16 の実測)

直近 7 走の `junit.xml` の `testsuite time` 中央値:

| shard | junit time 中央値 | 内訳 (中央値) |
|---|---|---|
| **shard-0** | **325.5 秒** | pre 約 65 + disp 29.6 + test span 231.0 |
| shard-1 | 229.8 秒 | pre 約 60 + disp 0.1 + span 169.5 |
| shard-2 | 236.6 秒 | pre 約 59 + disp 0.1 + span 177.7 |

- **300 秒を超えているのは shard-0 だけである。**
- shard-0 の span は最長単体 node にほぼ等しい (span 231.0、最長 node 222.51、差 8.49 秒)。
- 最長 node は
  `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`。
  t080 e2e 群は 200〜222 秒が 10 本並ぶ。shard-0 の t080 系 38 node の所要総和は 2611.1 秒で、
  shard-0 の node 所要総和の 32% にあたる (CPU 時間ではない — 待ちを含む)。
- 次点の非 t080 node は 161.1 秒
  (`test_s8c_preregistration_predicates::test_repository_candidate_uses_real_s8c_budget_module`)。
- shard-0 の real-repo lock の union は 186.5 秒 (span の 81%)。44 worker が延べ 1502.5 秒保持する。
- 当日 103 走での代表 node の分布は中央値 227.8 / 最小 198.8 / 最大 482.7 秒。
  日別中央値は 09-07 の 223.8 から 09-16 の 227.8 までほぼ横ばいである。

**この結果は D1918 と `[T-2495]` の記録を失効させる。** 当時 (2026-09-10) の最遅は shard-2 で、
床は xdist group `p3-b4-material-report` だった。現在その group は shard-1 の最忙 worker 169.5 秒で、
最遅ではない。ユーザー裁定 項35 の「次も実測で律速を選ぶ」に従い、対象を shard-0 の t080 へ改める。

## 2. なぜ t080 e2e が 200 秒級なのか

`_t080_stub_free_e2e_repo` は 4 フィールドの key ごとに base repo を 1 回組み、
テスト 1 本ごとにその base を独立実体へ複製する。base 構築は次を含む。

1. `orchestrator/` 全体の複製。
2. git 可視 `output/` の複製 — tracked だけで **22,976 件 / 614.6 MB** (2026-09-16 時点)。
3. 配置した全 file の `git add -A` と commit。
4. submodule の配置、historical source の上書き、receipt の発行 (`issue_receipt=True` の key)。

さらに発行前後で holdout の production scanner が走る。この scanner は
`enumerate_repository_files` で **repo 全体 (tracked regular + 非 ignored untracked + ccbench)** を
列挙し、非除外の全件を open/read/decode する。**「oracle は output を 4 path しか読まない」という
段 1 の前提は誤りである。**

## 3. 3 つの高速化候補と裁定

| 案 | 内容 | 裁定 | 理由 |
|---|---|---|---|
| A | 複製する output を固定 whitelist へ限定 | **不採用** | 非除外 output の任意 file に三軸 conjunction が入ったときの拒否経路が消える。既存の未知性負例は fixture 作成後に root 直下へ置く形なのでこの脱落を検出しない。受理集合が拡大する (規律 2) |
| B | 実 repo の object store 全体を alternates で借りる | **不採用** | ancestry 観測が `missing-commit` から `not-ancestor` へ変わりうる。report の独立検算は 17 observation のうち先頭 15 件しか覆わず、既存 assert が検出しない。貸出元の prune で object を失う risk もある |
| C | 必要 blob だけ fixture 内へ移送し独立 index を組む | **本 wave では採らない** | 係数削減であって成長比例を断たない。下限に届く経路は案 B と同じ object store 露出を要し、自己完結化は 660 MB の pack 化で削減分を食う見込み (未測定)。効果の符号が未確認 |

## 4. 実測した数値 (repo 外 probe)

### 4-1. index 化の現行費用と下限

| 方式 | index 化 | write-tree | commit | tree OID |
|---|---|---|---|---|
| 現行 `git add -A` | 79.33 / 114.37 / 191.30 秒 | 3.93 秒 | 0.25 秒 | 637411045f4e |
| 既存 OID を `update-index --index-info` | 0.03 / 0.04 秒 | 0.60 秒 | commit-tree 0.01 秒 | 00d210d723e7 |

複製 24,017 件のうち **24,017 件すべて**が実 repo の index entry と path 一致した。
`git commit` 経由の B は 69.05 / 121.22 秒かかる (index-info が stat 情報を持たず refresh が走るため)。
`write-tree` + `commit-tree` なら 0.61 秒である。

### 4-2. tree 差は 1 file だけで、原因は現行 fixture 側にある

`orchestrator/tests/fixtures/sort_swo_masstree/config.h` の 1 件のみ。
`orchestrator/tests/fixtures/sort_swo_masstree/.gitignore` の `/config.h` が原因で、
実 repo では tracked なので ignore に優先するが、fixture は `git init` からの `git add -A` なので
**この tracked file を取り込めていない**。fixture の可視集合が実 repo と 1 件ずれている。

### 4-3. 意味を変えない圧縮設定では効果を確認できなかった

同一 tree で `.git` を作り直しながら 2 巡した。**3 方式の tree OID はすべて同一**で、
圧縮設定が意味を変えないことは確認できた。しかし所要は round 1 が A0 87.95 / A1 91.04 / A2 106.72 秒、
round 2 が A0 26.76 / A1 7.95 / A2 7.46 秒で、**符号が反転している**。時間効果は未確認である。

### 4-4. login node の外乱

同一内容の `output/` 複製が 20.64 / 214.98 / 284.00 / 285.74 / 297.90 / 571.40 秒に振れた (28 倍)。
**単発測定は裁定の根拠にならない。** 本書の数値は、同一 tree 内で方式を交互に測った対比較だけを
比較に使っている。

## 5. 本 wave が主張しないこと

- 「受入全走が 5 分を切った」とは主張しない。単発 A/B では目標 25.5 秒を走間変動から分離できない
  (レンズ B の感度分析: wall の σ=20 秒でも各条件 10 走、σ=50 秒なら 61 走)。
- 「t080 の所要増加の主因が repo 成長である」とは主張しない。全件処理の存在はコードで示せるが、
  日別中央値は 9 日窓で横ばい (223.8→227.8 秒) である。
- 「222 秒は混雑でなく固有費用である」とは主張しない。単独走でも 300 秒級だったことまでを言う。

## 6. 残した裁定パッケージ候補

1. 成長比例の構造そのもの (fixture が実 repo の output を写す設計 = 受理集合を変えるか)。
2. fixture 側の全件 scan と、実 repo を直接 scan する検査の検出力の重複
   (後者は `orchestrator/tests/growth_test_holds.py` で保留登録されている)。
3. fixture の可視集合が実 repo と 1 件ずれている (§4-2)。
4. report の独立検算が 17 observation のうち先頭 15 件しか覆っていない。
