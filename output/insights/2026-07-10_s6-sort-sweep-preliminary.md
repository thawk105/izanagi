# 段6前提タスク (i): sort comparator 機械列挙 sweep — 偵察結果 (2026-07-10)

**位置づけ = 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。**
失敗条件 (c) の判定は出さない (16対1 の非対称比較・列挙空間は coder iteration 1 出力後の
設計で grid の事前固定 (pre-commitment) 未充足・ランダム変異アーム欠落)。段 6 の正式
grid / (c) 判定は本結果を材料流用せずゼロから再導出する (firewall)。設計判断の正本 =
D46、駆動 = `orchestrator/campaign/s6_sort_sweep.py` (c8194da)。

## 実験

- 列挙空間: 構文契約 (storage_/key_/rcdptr_ × asc/desc × 辞書式 prefix) + 退化点 nosort
  = 15 候補 + stock 対照。全点 SWO (厳密弱順序) を構成的に保証 + Python 有限モデル
  総当たり検査 (D42 の非 SWO ハングを実走前に遮断)。
- 計測: p2_2 確定動作点 (records 1M / threads 48 / extime 3 / reps 5 / CLK 1800 /
  numactl interleave)。全点 legacy+s2 verify (certified のみ採録)。
- 一次資料 (campaign):
  - balanced 本走: `p3-s6-sort-sweep-balanced-sweep-dd25aa8c` (16 点)
  - write-heavy 本走: `p3-s6-sort-sweep-write-heavy-sweep-0484feef` (16 点)
  - balanced 再測: `p3-s6-sort-sweep-balanced-sweep-1b39095e` (sp_dd/stock/sk_aa)
  - write-heavy 再測: `p3-s6-sort-sweep-write-heavy-sweep-d4552403` (sk_ad/stock/sk_aa)
  - 各 campaign の `reports/s6_sort_sweep_provenance.json` (name→variant_id→comparator
    全文) と `reports/s6_sort_sweep_report_*.md` (全点表)

## 結果

**正しさ: 32 本走点 + 6 再測点の全てが certified (legacy+s2 で anomaly 0、abort 0)。**
「施錠順序は correctness の入力でない」(D41 の読み替え) が全順序・逆順・順序不定
(恒 false comparator 含む) の全域で実測裏付けされた。permutation 保存 assert (D42) も
全点沈黙。

**性能地形 (記述統計。数値の正本は各 campaign の report md):**

| 観察 | balanced (rr50) | write-heavy (rr5) |
|---|---|---|
| stock | 913,843 tps (CV 0.80%) | 1,045,252 tps (CV 0.83%) |
| valid 全順序 12 点レンジ | +2.46% (floor 3.0% 内) | +2.72% (floor 内) |
| 本走 best vs stock | sp_dd +1.57% (floor 内) | sk_ad +3.55% (floor 僅か超) |
| 再測での best 再現 | **再現せず** (順位入替: sk_aa 921k > sp_dd 912k > stock 908k) | **再現** (sk_ad 1,098,674 > sk_aa 1,074,352 > stock 1,055,167、vs stock +4.12%) |
| abort 率 | 全点 ~19-20% (順序に不感) | 14-18% (退化点が高め) |

1. **balanced: 差なし方向。** 全点が floor 内に収まり、本走 winner が再測で再現しない
   (argmax 選択バイアスの実演)。sort comparator は balanced では性能の入力になっていない。
2. **write-heavy: sk_ad (storage 昇順→key 降順) の stock 超えが 2 run 再現**
   (+3.55% / +4.12%、順位 sk_ad > sk_aa > stock も一致)。ただし限定 3 点:
   (a) floor 0.030 は stock silo 実測の暫定流用で write-heavy の高 abort 域には未較正、
   (b) 差を分解すると「lambda 実装差」(sk_aa vs stock: +1.5〜1.8%) と「key 降順の寄与」
   (sk_ad vs sk_aa: +2.0〜2.3%) の合成で、**各成分は単独では floor 内**、
   (c) 系列 n=2。有意性は主張しない (事前登録の統計計画のサンプル設計 4 点は本偵察では
   放棄宣言済み — 系列検定は原理的に不可能な n)。
3. **退化点 (順序不定) が両 workload とも表の最上位** (s_asc: balanced 950k /
   write-heavy 1,087k)。順序の質でなく「comparator 評価コスト + swap 発生量」だけが
   僅かに効く示唆。退化点は floor 判定不能扱い (報告どおり)。
4. **coder 到達点 (sk_aa 同値) は valid 12 点中 10-11 位** — coder iteration 1 の到達
   順序 (= stock 順序) は空間内で凡庸。coder は iteration 1 (n=1) 中間時点であり最終
   到達ではない。

## 段 6 への示唆 (人間判断材料 — 本 insight は判断しない)

- **sort 軸に「順序の質」由来の floor 超地形は見当たらない。** 唯一の floor 超観察
  (write-heavy sk_ad) も分解すると実装コスト次元 + 順序次元の合成で、各成分は floor 内。
  headline 候補軸としての sort は、失敗条件 (c) の判定以前に「軸自体に地形が無い」
  可能性が高い — D44 (i) が想定した「本走前に軸選定・設計を見直す」ケースに該当しそう。
- 段 5 sort 軸 iteration 2 継続 (worklog 2026-07-10 (5) 次の一手③) の期待値は本結果で
  下がった。代替: 段 8a (軸提案のループ内化) の前倒し / 別軸のオンボーディング検討。
- 軸の生死を安価に先取りする器 (機械列挙 sweep、16 点 ≈ 40-80 分) が再利用可能になった
  — 段 8a のテンプレ化の固定費実測としても価値がある。
- write-heavy の S2 verify は S2_FLAGS 固定 (rr50) のため被覆は off-workload (D43 系の
  既知限定)。fairness 偏向 (D41 型15) は本 sweep では検出しない。

## 還元判断

CCBench 本体のバグ・還元事項なし (全点 certified、既存機構の想定内動作のみ)。
