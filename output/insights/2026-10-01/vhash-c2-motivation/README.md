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

## 4. 結論 — 成立点は 0。C2 が修正済みの最良 Cicada の回収境界を止める量は、長い tx の試行 1 回の長さ (1 ms 前後) で頭打ちだった

事前登録 (§2) の成立条件を driver の aggregate で機械的に当てた結果、**27 点すべて不成立 (成立 0、`measure_allowed = false`)**。§2 の規則どおり本計測 (§3) は行わず、ここで止める。

1. **長い read-write tx が完走する点では、境界は「長い tx が無いとき」の数倍〜20 倍遅れるが、絶対値は 1 ms 未満である。** 操作数 100・300 (skew 0・0.3) と操作数 100 (skew 0.6) の 15 点で R の完了率は 0.36〜0.97。
   そのときの境界年齢の平均は 217〜864 µs で、同じ (skew, rr) の R-noLT (39〜74 µs) の 3.4〜20.6 倍。成立条件 (ii) の下限 1,000 µs に届いた点は無い。
2. **境界年齢が 1 ms を超えるほど長い tx は、ほぼ commit しない。** 操作数 1,000 (skew 0・0.3) では境界年齢の平均が 883〜1,873 µs (R) になるが、完了率は 0〜0.0025 (3 秒で長い commit 0〜7 回)。
   skew 0.6 では長い tx が途中で abort するので試行が短く (操作数 1,000 でも 0.15〜0.22 ms)、境界年齢の平均も 413〜612 µs (R) にとどまる。完了率は操作数 300 で 0.012〜0.022、1,000 で 0。
3. **境界年齢の平均は、長い tx の試行 1 回の長さ (3 秒 / 長い attempt 数) の 1.5〜4 倍に収まる** (R の 27 走で 1.5〜3.9 倍。例: skew 0・操作数 300・rr 50 の R で試行 0.33 ms・境界 864 µs、操作数 1,000・rr 90 で試行 1.24 ms・境界 1,873 µs)。
   長い tx が abort して再試行すると境界は先へ進むので、C2 が境界を止める量は試行 1 回の長さの数倍で上から押さえられる、と読む (再試行で時刻を取り直すことを source で確かめてはいない。倍率の範囲は観測で、機序は推定)。
4. **版はほとんど溜まらない。** 論理生存版数は全点で record 数 (100 万) の 1.00〜1.10 倍、熱い key 0〜7 の版の列の最大は skew 0・0.3 で 1〜5 版。skew 0.6 では最大 68 版の走があるが、長い tx の無い R-noLT でも 110 版の走があり、長い tx の寄与とは読めない (1 rep)。
5. **この負荷では S と R はほぼ同じ。** 長い tx がある走の完了率・境界年齢は S と R で近い (例: skew 0・操作数 300・rr 90 で完了率 0.713 / 0.717、境界 731 / 795 µs)。
   通常 tx の read-only は YCSB の自然な割合 (rr 90 で 0.9^10 ≈ 35%) なので、ro-gcflag 修正の差は長い tx の無い対照に小さく出るだけである (rr 90 の noLT: S 72・R 39 µs (skew 0)、S 123・R 69 µs (skew 0.6))。
6. **C1 との対比:** md_29 の長い read-only tx (batchR) は stock で 3 秒間の MinRts の公開が 0 回、版が record の 5.4〜14.5 倍だった。md_42 は修正済みの R でも長い読み手が通常 worker の throughput を 1.56〜1.98 倍下げると測った。
   本 wave の C2 は、完走する限り境界の遅れが 1 ms 未満・版の増分が 10% 以下で、**C1 より桁違いに小さい。**

## 5. 結果の表 (smoke、R の診断走、1 rep × 3 秒、GC 10 µs、計器入り build)

境界年齢は公開ごとの境界年齢の和 / 公開回数 (timestamp 空間、µs)。比 = R の境界年齢 / 同じ (skew, rr) の R-noLT。生存版 = 論理生存版数 / record 数。列 = 熱い key 0〜7 の版の列の長さの最大。

| 点 | 成立 | 完了率 | 長い commit | 境界年齢 (R) | 境界年齢 (R-noLT) | 比 | p50 bucket | 生存版 | 列 |
|---|---|---|---|---|---|---|---|---|---|
| skew0-ops100-rr50 | False | 0.9081 | 22828 | 315 | 62 | 5.1 | 256 | 1.008 | 1 |
| skew0-ops100-rr70 | False | 0.9178 | 28143 | 245 | 47 | 5.3 | 256 | 1.043 | 1 |
| skew0-ops100-rr90 | False | 0.9732 | 38390 | 217 | 39 | 5.6 | 256 | 1.007 | 1 |
| skew0-ops300-rr50 | False | 0.4059 | 3739 | 864 | 62 | 13.9 | 1024 | 1.045 | 1 |
| skew0-ops300-rr70 | False | 0.4257 | 4583 | 733 | 47 | 15.7 | 1024 | 1.042 | 1 |
| skew0-ops300-rr90 | False | 0.7170 | 7810 | 795 | 39 | 20.6 | 1024 | 1.019 | 1 |
| skew0-ops1000-rr50 | False | 0.0005 | 3 | 1043 | 62 | 16.8 | 1024 | 1.054 | 1 |
| skew0-ops1000-rr70 | False | 0.0014 | 7 | 1438 | 47 | 30.9 | 1024 | 1.104 | 1 |
| skew0-ops1000-rr90 | False | 0.0025 | 6 | 1873 | 39 | 48.5 | 2048 | 1.019 | 1 |
| skew0.3-ops100-rr50 | False | 0.8894 | 22330 | 352 | 66 | 5.3 | 256 | 1.006 | 2 |
| skew0.3-ops100-rr70 | False | 0.9005 | 27915 | 285 | 52 | 5.4 | 128 | 1.006 | 2 |
| skew0.3-ops100-rr90 | False | 0.9670 | 38387 | 218 | 44 | 4.9 | 256 | 1.001 | 2 |
| skew0.3-ops300-rr50 | False | 0.3627 | 3558 | 795 | 66 | 12.1 | 512 | 1.012 | 2 |
| skew0.3-ops300-rr70 | False | 0.3717 | 4181 | 736 | 52 | 14.1 | 512 | 1.015 | 2 |
| skew0.3-ops300-rr90 | False | 0.6709 | 7485 | 816 | 44 | 18.4 | 1024 | 1.005 | 2 |
| skew0.3-ops1000-rr50 | False | 0.0003 | 2 | 987 | 66 | 15.0 | 512 | 1.053 | 5 |
| skew0.3-ops1000-rr70 | False | 0.0000 | 0 | 883 | 52 | 16.9 | 512 | 1.032 | 3 |
| skew0.3-ops1000-rr90 | False | 0.0008 | 3 | 1561 | 44 | 35.2 | 2048 | 1.013 | 2 |
| skew0.6-ops100-rr50 | False | 0.4671 | 16963 | 322 | 74 | 4.4 | 128 | 1.046 | 68 |
| skew0.6-ops100-rr70 | False | 0.4465 | 20034 | 226 | 67 | 3.4 | 128 | 1.001 | 4 |
| skew0.6-ops100-rr90 | False | 0.7336 | 35333 | 281 | 69 | 4.1 | 128 | 1.002 | 3 |
| skew0.6-ops300-rr50 | False | 0.0191 | 500 | 334 | 74 | 4.5 | 128 | 1.011 | 23 |
| skew0.6-ops300-rr70 | False | 0.0120 | 377 | 308 | 67 | 4.6 | 128 | 1.022 | 27 |
| skew0.6-ops300-rr90 | False | 0.0217 | 571 | 366 | 69 | 5.3 | 256 | 1.002 | 7 |
| skew0.6-ops1000-rr50 | False | 0.0000 | 0 | 413 | 74 | 5.6 | 256 | 1.011 | 25 |
| skew0.6-ops1000-rr70 | False | 0.0000 | 0 | 462 | 67 | 6.9 | 256 | 1.018 | 25 |
| skew0.6-ops1000-rr90 | False | 0.0000 | 0 | 612 | 69 | 8.8 | 512 | 1.004 | 5 |

S の 27 走、S-noLT の 9 走、性能 build の生死走 (1 秒、throughput 4.57〜4.77 M tps) は raw にある (§8)。性能 build の生死走は build と起動の確認であって、性能比較ではない。

## 6. 論文 (paper-story-vhash) への含意

- **§1 の動機に「C2 が回収を止める」は使えない。** 修正済みの最良 Cicada では、完走する長い read-write tx の回収境界の遅れは 1 ms 未満、版の増分は 10% 以下だった。T-2916 が埋めようとした数値は「小さい」という答えになった。
- **C2 の痛みは GC ではなく長い tx 自身の完了である。** 操作数 1,000 の長い update tx は skew 0 でも 3 秒で 0〜7 回しか commit しない (md_21 §4.4 と同じ向き)。前進 C (U1) を動機づけるなら「長い tx の完了」であり、md_21 は C-partial が成功率を上げても完了率を上げないと測っている。
- md_42 の「今の VHash を主論文の候補から外す推奨」を、C2 の側からも補強する結果である (C1 では費用は大きいが VHash の腕が取り戻さない、C2 では費用そのものが小さい)。

## 7. 確かめたこと / 確かめていないこと

確かめたこと (実測): smoke 3 job (78 走、うち診断 72 走と性能 build の生死走 6 走) がすべて rc 0・計器行の parse と flag の echo 照合を通過。性能 build の -D 集合が期待集合と一致 (build 時に検査、計器・trace の macro なし)。成立判定と点の選択は driver の aggregate (`raw/smoke-aggregate.json`)。

確かめていないこと・限界:
- **1 rep × 3 秒の smoke だけ。** 本計測 (反復・GC 100 µs・計器なし build の throughput 比較) は成立条件により行っていない。
- **通常 tx の書き込み圧を下げる knob を含まない。** 計器なし build でも同じ負荷を作るため、通常 tx の read-only 指定 (`izanagi_ronly_pct`、計器側の flag) を使わなかった (§2)。
  md_29 では read-only 指定 95%・24 thread (WO1-09) で操作数 1,000 の長い update tx が完了率 0.68〜0.72 で完走し、境界年齢 p50 の bucket 上界 (2 反復平均) が 196,608 µs・公開 21〜22 回だったが、これは修正なしの build で、read-only commit が公開を進めない欠陥 (md_22) による停止が混ざる。
  **修正入りの R で、通常 tx の read-only 割合が高い (書き込み圧が低い) 領域に、完走しかつ境界を 1 ms 以上止める C2 があるかは未測定である。** 測るには計器なし build にも read-only 指定を作る最小の workload patch が要る。
- thread 数 (通常 47 + 長い 1)、record 数 100 万、通常 tx 10 操作、値 4 B、GC 10 µs の 1 構成だけ。長い tx は 1 本。
- 計器 patch の `izanagi_long_kind=1` (長い tx を update に固定) は計器入り build でだけ効く。計器なし build の長い tx は YCSB の生成のまま (操作数 100 以上・rr ≤ 90 で全 read になる確率は 0.9^100 ≈ 3×10⁻⁵ 以下)。本 wave は計器なし build を生死走にしか使っていない。
- §4 項 3 の「再試行で境界が進む」機序は推定。境界年齢は timestamp 空間の値 (clock boost を含む)。論理生存版数は物理メモリ量ではない。
- 正しさの判定の上限は indeterminate (新しい variant なし、trace の検査なし)。

## 8. 生出力の所在と実行の記録

- raw (gzip -9、本 dir `raw/`): `smoke-skew0-a1.json.gz`・`smoke-skew0.3-a1.json.gz`・`smoke-skew0.6-a1.json.gz` (driver `smoke` の出力。各走の stdout・argv・計器行・build の receipt を含む)。展開前の sha256 は `raw/SHA256SUMS`。
  成立判定の集計 `smoke-aggregate.json` は raw から再生成できるので repo に置かず sha256 だけ記録した:
  `python3 -m orchestrator.campaign.vhash_c2_motivation aggregate --smoke <3 本の raw> --out <path>`。
- **CCBench は pin C (`68106660`) で測った。** driver は vlife と同じく source copy を C の commit で取り出す。計測の後、10:54 に main の pin が F (`25898d00`) に進み、本 wave は記録の前に取り込んだ。
  C → F の差分は `cc/cicada`・`include/ycsb.hh`・`common` を 1 file も触らないので、計測した Cicada の source は F でも同じである。取り直しはしていない。
- smoke: 計測用 checkout 3 本 (commit `59b36d8cc`) から skew ごとに 1 job、同時刻に投入。request 40672 (skew 0、bnode034、Elapse 209 s)・40673 (skew 0.3、bnode069、211 s)・40674 (skew 0.6、208 s)。各 job の build (依存物 1 + 4 種) は約 110 s。
- 各走の前に driver が単独性を確かめる (vlife の `_assert_single_tenant`)。

## 9. 実装と検証の記録

- **変更 file:** `orchestrator/campaign/vhash_c2_motivation.py` (新設、476 行。vlife の build・run・parse・genome の部品を import して使い、既存 module の関数・定数は変えない)、
  `orchestrator/tests/test_vhash_c2_motivation.py` (新設、360 行)、`orchestrator/campaign/materializer_admission.py` (materializer 1 件)、`orchestrator/tests/test_p3_build_authority_cli.py` (一覧 2 行)、`orchestrator/tests/README.md` (一覧 1 行、親)。
  patch・`vhash_cicada_vlife.py`・md_42 / md_39 の所有物・`external/ccbench` は変えていない。
- **段の構成:** 軽量版 (正しさ防壁・受理集合・設計択一に触れない計測 driver の新設なので、段 2・3 と段 6 の review 子を省いた)。driver の本体は親が読んで裁定 (plan v2) との一致を確かめた。
- **子の工数 (Codex `gpt-6-astra`・ultra):** author 1 (約 18 分) と fix 2。fix 1 = test の取り出しの欠陥 (下記)、fix 2 = main 取り込みで main 側の版を採った登録 2 行の足し直し。実装面の変更はすべて Codex `role=author`。
- **焦点走 (計算ノード):** 統合 commit `59b36d8cc` で 12 file (新 test、build authority・spawn site・materializer 登録・vlife の既存 test、test 一覧系、inventory 4 群) を走らせ、1,774 passed・8 skipped・1 failed (request 40666、Elapse 179 s)。
  失敗は新 test の 1 件で、aggregate の対の比を取り出すときに kind (perf / diag) を絞らず、並びが先の diag の対 (throughput を持たない) を拾っていた。driver は正しく、test の取り出しを直した (`b0d3efa90`)。単独再走 24 passed (request 40722)。
- **変異 (事前登録 M0〜M9、段 4 裁定):** 固定 commit `b0d3efa90` の使い捨て worktree で `tools/mutation_harness.py` (dispatch) を走らせ、基準走緑、M0 (等価) 生存、M1〜M9 KILLED。10 本すべてで赤になった test の集合が登録と一致した (ledger の matching 10 / 10)。
  M1 (perf build に計器 macro を足す)・M2 (R から RO_GCFLAG を外す)・M3 (対照に長い worker を残す)・M4 (対照の通常 worker を 48 にする)・M5 (完了率の閾値を 0 にする)・M6 (境界年齢比の閾値を 1 にする)・M7 (全 round 同じ腕順)・M8 (完了率に通常 tx の commit を使う)・M9 (点 B に完了率最小を選ぶ)。
  wrapper (`tools/mutation_worktree.py`) の終了コードは 125 で、理由は事後検査の「source/main 共有木の観測 bytes が変化した」。走行中に別 session の land (pin F、10:54) で main の木が動いたためで、wave の木は走行の前後で clean だった。ledger と 10 本の判定はこの終了コードの影響を受けない。初回の起動 (attempt 1) は `--attempt-out` の単独指定で引数エラーになり、変異は走っていない。
  ledger (repo 外): `/work/1/SFC/tanab/tmp/vhash-c2-motivation-2026-10-01/mutation-ledger-2.json`、spec sha256 `2527fa4c…`。
- **記録の検査:** 三軸語の走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc 1 だが、hit 3 件はすべて既存の較正 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file) で、本 wave の file は 0 件。`tools/check_docs.py` 違反なし、`tools/spool_fold.py --dry-run` は planned。
- **受入全走:** §11 に記録する。

## 10. 計算資源

| 用途 | request / Elapse |
|---|---|
| smoke | 40672 / 209 s、40673 / 211 s、40674 / 208 s |
| 焦点走 | 40666 / 179 s、40722 / 11 s |
| 変異 | dispatch 11 回 (基準走・collection・10 変異、各 10 s 前後) |

受入全走を除き約 0.2 node 時間 (2 node 時間未満)。本計測は成立条件により投入していない。
