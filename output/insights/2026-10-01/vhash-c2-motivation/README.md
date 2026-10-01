# VHash の動機 C2: 読み取りを続ける長い read-write tx が Cicada の回収境界をどれだけ止めるか (T-2916、2026-10-01)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-c2-motivation`、起点 local main `74029b18f` (開始 gate fresh rc 0、2026-10-01 00:45 JST)。00:4x〜09:43 は land 調整役の指示 (利用上限) で停止し、ユーザーの「続けて」で再開して `63378acb8` へ ff-only で進めた。
CCBench submodule = pin `68106660` (動かしていない)。job dir `/work/1/SFC/tanab/tmp/vhash-c2-motivation-2026-10-01/` (依頼の逐語 `request.md`、段 1 brief、段 4 裁定、Codex の prompt と報告、計算ノードの raw)。

**§1〜§3 は計測の投入前に commit する事前記述である。結果を見てから変えない。** 変える必要が出たら元の文を残して erratum を追記する。

## 1. 問いと、測る前に分かっていたこと

**問い (論文 §1 の動機の穴):** VHash 論文の稿 (`docs/paper-story-vhash/2026-09-30.md` §1) は「C2 (読み取りを続ける長い read-write tx) の大きさの数値は外部資料に無い」と書き、T-2916 に登録した。
D2322 項 1 は評価を「T-2930 系と T-2916 (動機の数値) を先にする」と裁定した。本 wave はこの数値を Cicada の上で測る。

**測る前の事実:**
- md_21 (`output/insights/2026-09-29/vhash-forwarding-target-policy/README.md` §4.4): 1,000 操作・read 90% の長い tx を 4 本走らせると、stock の完了率は skew 0.6 で 0.00003〜0.00008、skew 0.9 で 0。長い tx が完走しない負荷では「境界を止める大きさ」を言えない。
- md_29 の raw (`output/insights/2026-09-30/vhash-workload-space/raw/measure-m*.json.gz`) を読み直すと、1,000 操作の長い update tx (batchU) 1 本の完了率は、通常 tx の read-only 指定 95%・24 thread の点 (WO1-09) で 0.68〜0.72、
  read-only 指定 0%・48 thread の層 S では skew 0.5 でも 0.014 以下だった。**完走を決めるのは主に通常 tx の書き込み圧である。** md_29 は S/R の対・長い tx を除いた対照・計器なしの性能 build を持たない。
- md_42 (`output/insights/2026-09-30/vhash-ceiling-vs-sota/README.md` §5) は長い **read-only** の読み手 (C1) で、修正済みの最良 Cicada (R) に対し今の VHash の腕が 0.93〜0.99 倍にとどまり、主論文の候補から外す推奨を出した。
  同時に、長い読み手を除いた対照の比 R−LR / R が 1.56〜1.98 で、長い tx が通常 worker に課す費用は大きいとした。C2 は md_42 が測っていない型で、前進 C (U1) が働く唯一の型である。

## 2. 腕・負荷・成立条件 (結果を見る前に固定)

**腕 (md_42 と同じ定義):** S = md_11 の観測最良 genome (`BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0`) で ro-gcflag 修正なし。
R = 同じ genome + `IZANAGI_CICADA_RO_GCFLAG=1` (`patches/cicada-ro-gcflag-variant.patch`)。対照 S-noLT・R-noLT = 長い worker を除いたもの (通常 worker 数は同じ 47)。

**負荷:** YCSB、record 100 万、値 4 B、通常 47 worker・通常 tx 10 操作、GC 間隔 10 µs (本計測では 100 µs も)。長い tx は計器 patch の `IZANAGI_CICADA_LONGTX` の操作数型 (batch worker 1 本、`izanagi_long_kind=1` = update)。
長い tx の読み比は通常 tx と同じ `ycsb_rratio` で、通常 tx の read-only の割合は YCSB の生成のまま (読み比 rr のとき rr^10)。**計器なしの性能 build でも同じ負荷を作れる knob だけを使う** ため、計器側の `izanagi_ronly_pct` は使わない。

**smoke grid (有限、1 rep × 3 秒、計器入り build):** skew {0, 0.3, 0.6} × 長い tx の操作数 {100, 300, 1000} × rr {50, 70, 90} の 27 点 × 腕 S・R、加えて (skew, rr) の 9 組 × S-noLT・R-noLT。計 72 走。

**成立条件 (smoke):** ある点で R の走が次の両方を満たす。
- (i) 長い tx の完了率 (長い commit / 長い attempt) ≥ 0.10、かつ長い commit ≥ 100 / 走。
- (ii) 回収境界の年齢の平均 (公開ごとの境界年齢の和 / 公開回数) が、同じ (skew, rr) の R-noLT の 4 倍以上、かつ 1,000 µs 以上。

成立点が 0 なら、本計測をせず、条件と全値を記録して止める。

## 3. 本計測 (成立した場合だけ)

**点の選び方:** A = 成立点のうち R の境界年齢比 (長い / noLT) が最大の点。B = 成立点のうち R の完了率が最大の点 (A と同じなら B は置かない)。

**走行:** 各点で腕 S・R・S-noLT・R-noLT を同じ job・同じ計算ノードに置き、round ごとに順序を回転し、偶数 round は逆順にする。
- 性能: 計器を compile 時に外した build (`IZANAGI_CICADA_LONGTX` だけ、R はさらに `IZANAGI_CICADA_RO_GCFLAG`) で 5 round × 10 秒 × GC {10, 100} µs。build 時に -D 集合を照合し、計器・trace の macro が無いことを確かめる (規律 1)。
- 診断: 計器入り build で 3 rep × 3 秒 × GC {10, 100} µs。境界年齢 (平均・p50 の bucket)、公開回数、論理生存版数、熱い key 0〜7 の版の列の長さ、長い tx の完了率。
- 主表の GC 間隔は、R (長い tx あり) の throughput が高い方 (md_42 §4.2 と同じ規則)。両方を併記する。

**読み方の限界 (先に書く):** 診断値は計器入り build の観測で性能値ではない。境界年齢は timestamp 空間の値。長い tx の完了率は計器入り build でしか数えられない (計器なし build は thread 別の commit を出さない)。
正しさの判定の上限は indeterminate (新しい variant は無く、R の正しさは md_22・md_42 の検査に依存する。本 wave で trace の検査はしない)。
