# 受入全走の wall はスケジュールではなく直列鎖で決まる — 並べ替え仮説の実測反証 (2026-08-18)

- wave: `dev-wave-accept-bottleneck` (branch `worktree-dev-wave-accept-bottleneck`)
- base main: `38f173cb`
- 依頼: 「受入全走のボトルネックを特定し、改善してください。リワードハック禁止。
  テストなどは cpu コアを (全力で使い潰せていることが望ましい)」
- 結論: **実装差分ゼロ。** 並べ替えによる改善仮説を、実装したうえで対測定により反証した。
  受入全走の wall は `real-repo` 直列鎖 + 約 26 秒の固定費で決まっており、
  **スケジュールは変更前から下界に張り付いている。**

## 1. 実測した cost 構造 (gen_S 計算ノード、割当 48 CPU、`--dist loadgroup`、`-n 48`)

計測 14 走。うち非対 8 走 (bnode037 / bnode025 / bnode002 / bnode088 / bnode085) と、
同一 branch 上で編集面 5 file を commit 間で切り替えた**対測定 6 走** (A/B 交互)。

| 量 | 実測範囲 |
|---|---|
| pytest 本体 wall | 99.35 〜 122.03 秒 |
| testcase 直列総和 | 2862.9 〜 4198.2 秒 (12951 〜 12961 件) |
| `real-repo` 群の直列鎖 | 77.53 〜 94.86 秒 (69 件) |
| `s8c-preregistration-candidate` 群の直列鎖 | 71.65 〜 77.54 秒 (4 件) |
| `dev-waves-runtime` 群 | 15.4 〜 15.9 秒 (22 件) |
| 単体最長テスト | 54.89 秒 |
| **wall − `real-repo` 鎖長** | **20.57 〜 28.84 秒 (14 走すべて)** |
| 実効並列度 | 3332 / (116.89 x 48) = 59% |

**wall = `real-repo` 直列鎖 + 約 26 秒の固定費**が 14 走すべてで成立する。
固定費は worker 48 本の起動と、全 worker が 12951 件を各自 collection する費用
(単一 process の collection 実測 4.08 秒) と最終集約である。

## 2. 反証した仮説 (親の段 1 と、段 2 プラン)

### 2.1 親の第 1 仮説 — 「群が行列の終盤から始まる」(誤り)

親は `xdist/scheduler/loadscope.py:368-382` が workqueue を collection 順の OrderedDict に積み
`popitem(last=False)` で FIFO 配布することを読み、`s8c-preregistration-candidate` (75.45 秒の鎖) が
12859 unit 中 10248 番目にあるため 52.5 秒後に開始する、と結論した。

**これは誤りである。** `xdist/plugin.py:130-142` の `--loadscope-reorder` は **default=True** で、
`loadscope.py:374-379` が workqueue を**件数の降順**へ並べ替える。3 群は既に行列の先頭 (位置 0/1/2) にある。
この誤りは段 3 レンズ B が独立に指摘し、親が実装を読んで確定した。

### 2.2 段 2 プランの hoist — 実測上の no-op

「`xdist_group` marker を持つ item を持たない item の前へ寄せる」案は、上記のとおり
xdist が既に行っていることの再実装であり、忠実シミュレータ上で 93.94 秒 → 93.94 秒の完全な no-op だった。

### 2.3 親の第 2 仮説 — 「件数降順は所要時間の代理として不適切」(実装したうえで反証)

長い**非群**テスト (54.89 秒 1 本と 32〜35 秒級の `test_s8b_floor_campaign.py` 群) は
1 item = 1 unit のため件数降順では後方に沈む。閾値 20 秒の 17 unit を所要時間降順で先頭へ出せば
完全 LPT (78.8〜83.7 秒) に到達する、と模型は予測した。

実装 (`conftest.py` の宣言 + 純関数 reorder、`run_tests.py` の `--no-loadscope-reorder`) を
段 5・段 6 で完成させ、marker が宣言 17/17 の一致を報告することも確認した。**そのうえで反証された。**

**対測定 6 走 (A = 現行順、B = 実装形、A1 B2 B3 A4 A5 B6 の交互)**

| run | arm | wall | 鎖長 | 直列総和 | wall − 鎖長 |
|---|---|---|---|---|---|
| p1 | A | 115.97 | 88.35 | 3327.21 | 27.62 |
| p2 | B | 122.03 | 93.19 | 4198.22 | 28.84 |
| p3 | B | 110.29 | 87.07 | 3788.39 | 23.22 |
| p4 | A | 121.58 | 94.86 | 3478.11 | 26.72 |
| p5 | A | 113.12 | 88.74 | 3191.78 | 24.38 |
| p6 | B | 103.05 | 77.53 | 3494.96 | 25.52 |
| **A 平均** | | 116.89 | 90.65 | 3332.37 | **26.24** |
| **B 平均** | | 111.79 | 85.93 | 3827.19 | **25.86** |

wall の 5.1 秒差は**すべて鎖長の差 4.7 秒**で説明される。鎖の内容は両 arm で同一であり、
差は走行間変動である。ノード速度を除いた `wall − 鎖長` は **26.24 対 25.86 = 0.38 秒差**で、
**効果はゼロ**である。

**決定的なのは B の直列総和が A より 495 秒 (15%) 大きいのに `wall − 鎖長` が同じ点である。**
鎖以外の仕事は 47 worker 上で完全に鎖の下へ隠れており、その並べ替えは wall に影響しえない。

## 3. なぜ模型が外れたか

親の離散事象シミュレータ (`simulate_xdist.py`) は `_assign_work_unit` / `_reschedule` の
`pending <= 2` 先読み / 初期 1+1 配布を再現したが、次を持たない。

- worker 48 本の起動と各 worker の collection (実測で約 26 秒の固定費)。
- 所要時間が**スケジュール非依存**という仮定。実際には junit の duration は共走の競合を含む。
  B arm の直列総和が 15% 大きいのはその現れである。

模型は「非群の長い unit が後方で拾われて makespan を伸ばす」と予測したが、
実機ではその unit は鎖の下に収まっていた。**この suite に定所要時間の LPT 模型を当てはめてはならない。**

## 4. 残る律速と、効く手 / 効かない手

**効かないと実測で確定した手**

- work unit の配布順の変更 (本 wave)。
- worker 数を増やす。48 は gen_S の per-job 上限 (receipt の `CPU Number Max: 48`)。
- worker 数を減らす。`-n 32` は模型で 93.6〜103.7 秒と悪化する。

**効く手 (magnitude 付き)**

1. **`real-repo` 鎖の短縮 ([T-827])。** 鎖 77.5〜94.9 秒が wall の 74〜78% を占める。
   鎖上位 3 件で鎖の 76% (`test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive`
   22.38 秒、`test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e` 19.75 秒、
   `test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment` 19.38 秒)。
   鎖を x 秒縮めれば wall はほぼ x 秒縮む。次の床は s8c 鎖 71.7〜77.5 秒。
2. **`real-repo` の排他閉包の細分化 ([T-826] / [T-813])。** 69 件は 1 worker に直列化されるが、
   conftest の注釈では大半が reader である。reader/writer を分けられれば鎖は writer 分まで縮む。
   ただし [T-813] の再評価条件 3 つは未成立であり、本 wave では触れていない。
3. **固定費 約 26 秒。** wall の 22〜25%。48 worker が各自 12951 件を collection する費用。
   単一 process の collection は 4.08 秒。

## 5. 段 3 / 段 6 の敵対検証が親を止めた点

- 段 3 レンズ B (v1) が「1 unit ずつ配る模型は実 xdist の先読みと一致しない」を BLOCKER とし、
  親の「完全 LPT と同値」を撤回させた。
- 段 3 レンズ A (v2) が `pytest_configure` で `loadscopereorder` を切る案を BLOCKER とし、
  workqueue が controller の `config.option` だけで決まる (`loadscope.py:374`) ことを根拠に
  `run_tests.py` 側へ移させた。
- 段 3 レンズ B (v2) が「宣言が空・全 stale のとき 113.70 秒へ悪化する」を BLOCKER とし、
  親は fallback 分岐ではなく**規則そのもの** (残りを件数降順) で退化を消した。
- 段 6 レンズ B の所見 15 が示した解釈表 (「99〜108 秒なら no-op 経路の可能性が高い」) は、
  実測 106〜113 秒に対して正しく発火した。

## 6. 親自身の誤り (すべて撤回済み)

1. 「work unit は collection 順 FIFO で配られる」— `--loadscope-reorder` の既定 True を見落とした。
2. 「群を先頭へ寄せれば完全 LPT と同値」— 先読みを模型に入れていなかった。
3. 「閾値 20 秒の 17 unit で完全 LPT に到達する」— 固定費と競合結合を模型に入れていなかった。
4. 非対 8 走の before/after 比較を最初に出したが、ノードが完全に交絡していた
   (before = bnode037x3 / bnode025、after = bnode002x2 / bnode088 / bnode085)。対測定で置き換えた。

## 7. 不採用にした実装の所在

段 5・段 6 で完成させた実装は commit `5e49ac7a` として一度作り、対測定の後に破棄した。
逐語は repo 外の job dir に保全してある
(`/work/1/SFC/tanab/dev-wave-jobs/2026-08-18_acceptance-bottleneck-cores/impl-final-5e49ac7a.patch`)。
段 6 の敵対レビュー 2 本は BLOCKER 0 / MUST-FIX 計 17 件を出しており、
仮に効果があったとしても、その修正なしでは land できない状態だった。

## 8. 工数

codex 子 8 本 (plan x2、consult x4、author x1、fix x1、review x2)、すべて `outcome=accepted`。
model = `gpt-5.6-luna`、reasoning = `max`。
親の実測 = gen_S への dispatch 14 走 + 焦点走 2 回。
