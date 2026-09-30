# VHash md_22: read-only commit でも GC の公開を進める — Cicada で安く直せる分と、固定 snapshot のままでは残る分 (2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-ro-gc-publish` (branch `worktree-dev-wave-ro-gc-publish`)、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 22:0x JST)、CCBench submodule = pin `68106660` (動かしていない)。
job dir `/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/` (Codex の prompt と報告、起動器、完全な raw・trace、変異の scratch)。依頼は `verbatim/request-md_22.txt` と `verbatim/request-common.txt`。対象 item は worklog の [T-2911]。
段 1〜6 の全文は `verbatim/` (brief、plan、相談 2 本、段 4 裁定、レビュー 2 本、焦点再レビュー 2 本、fix 裁定 9 本、レビューを閉じる裁定)。
逐語の正規化 2 件 (`git diff --check` 抵触のため、Markdown 改行用の行末空白を除去、可視文字不変): `verbatim/s6-review-a.md` は 7 行、原文 sha256 `c3f93d8f26c45e48a9e6d5be0b5fc7c42b9b6497d8fd368472a4ece163ad2ba3`・7,931 byte → `86d0cb361f454df84fbffaf17b843604b67f42d21e16182e672ee63d3ace7d50`・7,917 byte。`verbatim/s6-review-b.md` は 8 行、原文 `e11d13fb055fcaae3578abc2051fdb07933e798f35aaf0d214d54fea0372be6b`・11,194 byte → `3cfeca0fe5b56a782fe5896efab5d02ab48910fbe787c40be658ef6ec0280fac`・11,178 byte。原文は job dir の `codex/stage6a/out.md`・`codex/stage6b/out.md` (復元はその file を写す)。

**この文書の公開回数・境界年齢は計器入り build の診断値、throughput は計器・trace なし build の値である。正しさは判定器で巡回 0 を確かめた範囲で、上限は indeterminate (certified・serializable とは書かない)。**

## 0. 結論 (図から)

![公開回数と境界年齢](figures/ro_gc_publish-publication_boundary.png)

![throughput の比](figures/ro_gc_publish-throughput.png)

図の読み方: 横軸は条件 (S = 既定 genome・skew 0、T = md_11 の観測最良 genome・skew 0.9、数字は ro 指定率 %、`wait10msR` は worker 1 が 10 ms かかる read-only tx を続ける、`none` はそれが無い)。
図 1 は stock (青) と variant (橙) の絶対値 (対数軸、小点が 6 反復、印が平均と 95% CI)。stock が公開 0 回で境界年齢が定義できない条件は、軸の下の帯に「0 (6/6)」「undefined (6/6)」と示した。図 2 は同じ job・同じノードで交互に走らせた対ごとの throughput 比 (variant / stock、対数軸、破線が 1)。

1. **Cicada では、read-only tx だけを続ける worker が 1 本いるだけで GC の境界の公開が止まる。** ro commit は `mainte()` を通らず GC flag を立てないので、全 worker の flag を待つ leader は公開できない。長い ro (10 ms) を 1 本続けた 6 条件で、stock は 3 秒間の公開が **36/36 走で 0 回**だった (ro 指定率 0% の条件も含む)。ro commit の後始末 (`read_set_`・`node_map_` を消した後) で `mainte()` を呼ぶ variant では、公開が **289〜299 回 / 3 秒**に戻った (長い ro 1 本の commit ごとにほぼ 1 回)。
2. **長い ro が無くても、ro が多い設定では公開が大きく増える。** ro 95% で公開回数は S が 4,978 → 139,567 回、T が 7,314 → 145,150 回 (各 6 反復平均、3 秒)。公開時の境界年齢の平均は S が 810 → 36 µs、T が 527 → 32 µs。ro 0% では差が無い (S 15,205 対 14,628 回、354 対 366 µs、T 26,004 対 25,541 回、191 対 195 µs)。md_15 が観測走の時刻分割から見積もった「公開待ちの 76〜77% は ro commit が flag を立てないため」(md_15 §6.2) と同じ向きの、介入による実測である。
3. **公開の停止は throughput を大きく落とし、variant はそれを戻す (計器なし build)。** 長い ro がいると stock の throughput は長い ro なしの 1/1.6〜1/32 に落ち (例 T50: 5.45M → 0.17M tps、T95: 12.70M → 0.52M tps)、variant/stock の比は **1.56〜16.83** (条件別平均 S0 6.08、S50 3.96、S95 1.59、T0 4.25、T50 16.74、T95 15.50)。長い ro が無いときの比は **0.964〜1.073** (36 対)。既定 genome の ro 95% では 6 対すべてで variant が遅く平均 −1.1% (ro commit ごとの `mainte()` の費用と見られる)、最良 genome では T50 +5.2%、T95 +3.2%。**比は 3 秒の走行での値で、stock の版の蓄積は走行時間とともに進むので、長い走行では差が変わりうる (§11)。**
4. **安全: 版を守っているのは GC flag ではなく、tx の間変わらない per-thread の rts slot である (小モデル)。** Cicada の flag・slot・leader 公開・GC 切断を共有変数 1 回の読み書きを 1 step にして写した有界モデルで、5 構成 × 6 腕を全探索し 30 腕すべて完了した。ro commit で flag を立てる安全腕 2 形 (flag だけ、`mainte()` 全体) は、適法な切断が実際に起きる状態列 (w3 で 624 本・2,496 本の切断遷移) を通っても GC 安全違反 0。ro の途中で flag だけを立てる版 (陰性対照) も違反 0。これに対し、ro の途中で slot を上げる版と ro commit で slot を ∞ にする版は違反に到達した (最短 49 step・38 step)。**flag を早く立てても安全で、slot を tx の途中で動かすと危険** — md_14 が実測した不具合 (tx の途中の安全点で slot を上げた) と同じ構造。
5. **正しさ: variant を trace build に載せて判定器に掛け、24 走すべてで巡回 0** (既定・最良 genome × ro 50/95% × 長い ro の有無 × 3 seed、commit 済み txn 計 12,321,579、判定器 rc=3 = 上限 indeterminate、読んだ版の食い違い 0、variant の flag 立ては各走 196〜209,933 回で変更経路を実際に踏んだ)。
6. **固定 snapshot のままでは残る分 (b):** variant でも、長い ro がいる条件の公開時の境界年齢は **12.5〜14.3 ms** (長い ro なしとの差 12.5〜14.0 ms) で、長い ro の長さ (10 ms) 程度に留まる。公開された境界と同じ rts を持っていた tx のうち ro の割合は ro 95% で 0.88〜0.95。長い ro の rts が境界を押さえる分は、snapshot を前へ動かさない限り直らない (本 wave は変えていない)。

**この図から読み取ってはならないこと。** 公開回数・境界年齢は計器入り build の値で、Cicada の性能を言っていない。throughput 比は YCSB (48 worker・1M 件・3 秒・gc 10 µs) の値で、長い ro は worker 1 の全 tx を 10 ms の read-only にした合成負荷である。最良 genome (INLINE_VERSION_OPT=1) の trace が inline 版の読み書きを漏れなく記録するかは md_20 の結果待ちで未確認。

## 1. 確かめたこと・確かめていないこと

**確かめたこと (実測):**
- 小モデル: 5 構成 (w2-k1-r1・w2-k1-r2・w2-k2-r1・w2-k2-r2・w3-k1-r1) × 6 腕、上限 200 万状態で全 30 腕 complete (§3)。
- 判定器: variant の trace build 24 走で巡回 0、integrity の数値項目 11 種すべて 0、trace の txn 数 = commit 数 (§4)。
- 計測: 12 条件 × 6 対 × 2 arm の診断 144 走と throughput 144 走、各条件の stock と variant を同じ job・同じノードで均衡順序 (AB BA AB BA AB BA) に交互 (§5〜§7)。
- 既定 macro 0 の build は stock と同じ変更経路 (variant patch は `#if IZANAGI_CICADA_RO_GCFLAG` の内側だけ、挿入後に `#line` で行番号を戻す)。3 通りの木 (pin・pin+trace・pin+vlife) に fuzz なしの `git apply` で当たる (test と smoke で確認)。
- 非同居: 自分の計測系 7 job と並走 wave (md_18・md_20・md_21) の dispatch receipt 55 件を照合し、同じノードで時刻が重なる組 0 (§10)。

**確かめていないこと:**
- **certified・serializable:** Cicada には判定器の証拠面 (X/P/I) が無く、巡回 0 の上限は indeterminate (md_3・md_14 と同じ)。
- **最良 genome の trace 網羅:** INLINE_VERSION_OPT=1 の経路で trace が inline 版を漏れなく記録するかは md_20 の担当で、本 wave の時点で main に結果が無い。
- **小モデルの外:** delete・insert、group commit、3 worker・2 key・2 read の構成、全メモリ順序 (モデルは逐次一貫性)。
- **効果の分解:** variant は ro commit で `mainte()` 全体を呼ぶので、「公開を早める」と「自 thread の GC を早める」の 2 つを含む。C++ で両者を分けた腕は作っていない (小モデルは flag だけの腕も探索した)。
- **非 ro 手続きの write の実行時件数:** workload の計数は試行・ro 試行・commit・長い ro だけで、非 ro が少なくとも 1 op を書くことは構造 test で確かめた。
- **長い走行・他の負荷:** 3 秒・YCSB・48 worker だけ。長い ro は worker 1 の全 tx を read-only にした合成。

## 2. 何を変えたか

| file | 内容 |
|---|---|
| `patches/cicada-ro-gcflag-variant.patch` | `cc/cicada/transaction.cc` の ro commit で、`read_set_.clear(); node_map_.clear();` の後・`return true;` の前に `#if IZANAGI_CICADA_RO_GCFLAG` で `mainte();` を呼ぶ。`IZANAGI_CICADA_RO_GCFLAG_COUNT` (companion RO_GCFLAG=1) で「ro commit 数」と「その `mainte()` で flag が 0→1 になった回数」を数え、終了時に 1 行出す (検査用、性能 build では使わない)。43 行 |
| `patches/cicada-ro-gcflag-workload.patch` | `IZANAGI_CICADA_ROGC_WORKLOAD`。手続き生成時 (retry では変えない) に実行時 flag の確率で全 op を READ・ro にし、非 ro は少なくとも 1 op を write にする。worker 1 を長い ro に固定し、読み終えて commit 呼び出しの前に指定 µs 待つ。YCSB の既存乱数系列を乱さない別系列。計器・計器なし・trace の 3 build で同じ手続き生成を使うための patch (vlife 側の ro 書換えは使わない)。142 行 |
| `orchestrator/campaign/vhash_ro_gc_publish.py` | driver。`smoke`・`verify`・`measure`・`throughput`。source copy ごとに macro なしの依存物 build → condition gate → 本 build。verify の受理は判定器 rc ∈ {0, 3}・巡回 0・integrity 数値項目 0・txn 数 = commit 数・`READ_WTS_MISMATCH` 0・COUNT の flag 立て > 0 |
| `tools/vhash_forwarding_model/ro_gc_publish.py` | 小モデル (§3) |
| `tools/plotting/plot_vhash_ro_gc_publish.py` | 図 2 枚と (b) の数表 (`analysis/boundary-table.json`) を raw から再計算 |
| 登録簿 | condition gate に 3 macro (DefineSpec・分岐目印・件数 pin)、screening 既定値、loop test の許可表、materializer、spawn site の分類、tests README |

`patches/ledger.json` には登録しない。同台帳は D18 第 4 類 ability probe 専用で entry 1 件を契約が要求する (D2288 と同じ理由)。md_22 の「ledger・README の該当 entry」とはこの点で食い違い、`patches/README.md` にだけ entry を書いた。

## 3. 小モデル (`tools/vhash_forwarding_model/ro_gc_publish.py`)

Cicada の begin の 3 手 (wts slot store、MinWts load、rts slot store)、ro の読み (固定 rts で版を選び pointer を保持)、update worker の版の追加と `mainte()` (execute flag の確認 → GC の境界 load → 鎖の切断 → timer → flag の確認と store)、leader の公開 (各 flag の load、各 wts/rts slot の load、MinWts/MinRts の store、flag の reset、execute flag の store) を、共有変数 1 回の読み書きを 1 step として写した。GC 安全の判定は回収側の境界計算を使わない独立 oracle (生きている reader の rts から選ぶ版と保持 pointer の版が切られたら違反)。直列化可能性はモデルの対象外 (C++ の判定器で確かめる)。progress は「長い ro が active の間に MinRts の値が変わる公開があったか」(公開回数ではない)。

| 腕 | 変えた規則 | 意味 |
|---|---|---|
| stock | — | ro commit は flag を立てない |
| safe-flag | ro commit の参照解放後に flag を立てる | 最小の変更 |
| safe-mainte | ro commit の参照解放後に `mainte()` (GC 実行 → flag) | patch の対応物 |
| neg-early-flag | ro の途中で flag だけを立てる | 陰性対照 (md_22 の「flag を上げる前に reader の参照が残る」) |
| bad-raise-slot | 陰性対照 + ro の途中で slot を最新 MinWts−1 へ上げる | 正例 (md_14 の不具合と同じ構造) |
| bad-clear-slot | safe-flag + ro commit で slot を ∞ にする | 正例 (md_22 の「境界を下げる」: 次の begin の store 前に公開が入ると下限が公開値より下がる) |

結果 (親が上限 200 万状態で実走、`model/ro_gc_publish-model.json`。状態数・切断は探索した遷移の数で、実行 1 回の回数ではない):

| 構成 | stock 状態数 / 公開 / 切断 | safe-flag 状態数 / 切断 / 違反 | safe-mainte 状態数 / 切断 / 違反 | neg-early-flag 状態数 / 違反 | bad-raise-slot 違反 / 最短 step | bad-clear-slot 違反 / 最短 step |
|---|---|---|---|---|---|---|
| w2-k1-r1 | 299 / 0 / 0 | 4,594 / 10 / 0 | 13,478 / 40 / 0 | 16,630 / 0 | 10 / 49 | 12 / 38 |
| w2-k1-r2 | 345 / 0 / 0 | 5,171 / 10 / 0 | 14,055 / 40 / 0 | 18,815 / 0 | 10 / 50 | 18 / 39 |
| w2-k2-r1 | 345 / 0 / 0 | 5,171 / 10 / 0 | 14,055 / 40 / 0 | 19,033 / 0 | 10 / 49 | 12 / 38 |
| w2-k2-r2 | 529 / 0 / 0 | 7,479 / 10 / 0 | 16,363 / 40 / 0 | 28,209 / 0 | 30 / 50 | 36 / 39 |
| w3-k1-r1 | 5,980 / 0 / 0 | 154,824 / 624 / 0 | 502,328 / 2,496 / 0 | 562,350 / 0 | 654 / 71 | 1,044 / 49 |

- 30 腕すべて complete (所要 2 分 23 秒、最大 RSS 1.2 GB)。stock は長い ro の間どの構成でも公開 0 (progress なし)、安全腕 2 形と陰性対照は progress あり。
- bad-raise-slot の違反は「ro の途中の flag」と「ro の途中の slot 引上げ」の両方を要する (witness に `early_store_flag` が 2 回入る)。variant のように flag を commit 時にだけ立てる形では、slot を tx の途中で上げても、ro が参照を手放す前に公開が起きない。**違反を起こすのは slot を tx の途中で動かすことで、flag の時機そのものではない。**
- 範囲は上の 5 構成に限る (3 worker・2 key・2 read は状態数の見積りで上限を超えるため探索していない)。

## 4. 正しさ検査 (md_3 / md_17 の trace と判定器)

pin → `instr-cicada-trace.patch` → workload → variant の順に当て、`TRACE=1`・`IZANAGI_CICADA_ROGC_WORKLOAD`・`IZANAGI_CICADA_RO_GCFLAG`・`_COUNT` で build し、4 worker・200 件・1 秒・gc 10 µs の小走行を判定器 (`orchestrator.verify --protocol cicada --expected-commits <commit 数>`) に掛けた。

| 走行 | commit | 結果 |
|---|---|---|
| verify1 (5c781ae7c、36633.nqsv、bnode085、Elapse 428 s) | 24 走、txn 計 11,954,950 | 24 走すべて判定器 rc=3・巡回 0・数値項目 0・txn 数 = commit 数・mismatch 0・flag 立て > 0。**driver は rc=1** (受理条件が `integrity.clean` を要求し、Cicada では証拠面が無いため常に false。段 6 fix5 で受理条件を「数値項目 0・txn 一致」に直した) |
| verify2 (981f2f63d、36731.nqsv、bnode026、Elapse 438 s) | 24 走、txn 計 12,321,579 | **24/24 受理**。rc=3 (上限 indeterminate) 24 走、巡回 0、mismatch 0、ro commit 計 9,866,341、flag 立て各走 196〜209,933 |

条件: default genome (S) と最良 genome (T) × ro 50/95% × 長い ro の有無 × seed 1〜3。trace の raw は repo 外 (job dir `raw/verify{1,2}-traces/`、各 5 GB 強)、verify2 の record は `raw/verify2.json.gz` (compact)。

## 5. 計測の条件

| 軸 | 値 |
|---|---|
| 系列 | S = 既定 genome (BACK_OFF=1, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=1, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)、skew 0。T = md_11 の観測最良 genome (BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0)、skew 0.9 |
| ro 指定率 | 0、50、95% (手続き単位、workload patch) |
| 長い ro | none、wait10msR (worker 1 の全手続きを read-only にし、読み終えて commit の前に 10 ms 待つ) |
| 共通 | YCSB 10 ops、非 ro 手続きの op は読み 50% (少なくとも 1 write)、payload 4 B、48 worker、1,000,000 件、3 秒、gc_inter_us 10、group_commit 0 |
| arm | stock (`IZANAGI_CICADA_RO_GCFLAG` なし)、variant (あり)。各条件 6 対、順序 AB BA AB BA AB BA、同じ job・同じノード |
| build | 診断 = pin + vlife + workload + variant、`IZANAGI_CICADA_VLIFE`=1 (vlife 側の ro 書換えと長い tx 用 macro は使わない)。throughput = pin + workload + variant、VLIFE・TRACE・COUNT なし (driver が拒否) |

job: 診断 measure1 (5c781ae7c、36634.nqsv、bnode005、Elapse 677 s)、throughput1 (5c781ae7c、36637.nqsv、bnode031、Elapse 641 s)。別の checkout (job dir 下の detached checkout) から同時に投じ、別ノードで走った。5c781ae7c から最終 commit までに patch は変わっておらず、driver の変更は verify の受理条件 (fix5) だけで measure・throughput の経路は同じ。

実現 ro 試行率 (workload の計数、試行ベース): S は 0.000 / 0.500 / 0.950 (指定どおり)、T の ro 50% は 0.408 (stock・variant とも。BACK_OFF=0 の T では update の abort と retry が多く、試行数に占める ro の割合が下がる)、T の ro 95% は 0.945〜0.949。

## 6. 結果 (a): 公開回数と境界年齢 (診断 build、6 反復平均)

| 条件 | 公開回数 / 3 s: stock → variant | 境界年齢の平均 µs: stock → variant | commit 数 (百万): stock → variant |
|---|---|---|---|
| S0-none | 15,205 → 14,628 | 354 → 366 | 11.48 → 11.46 |
| S0-wait10msR | **0** (6/6) → 298.5 | 未定義 → 14,272 | 2.02 → 10.66 |
| S50-none | 22,173 → 57,906 | 218 → 90 | 16.19 → 16.11 |
| S50-wait10msR | **0** (6/6) → 299 | 未定義 → 14,104 | 4.34 → 14.94 |
| S95-none | 4,978 → 139,567 | 810 → 36 | 24.01 → 23.63 |
| S95-wait10msR | **0** (6/6) → 298.3 | 未定義 → 13,133 | 15.91 → 23.36 |
| T0-none | 26,004 → 25,541 | 191 → 195 | 9.74 → 9.63 |
| T0-wait10msR | **0** (6/6) → 289.7 | 未定義 → 13,601 | 1.98 → 7.48 |
| T50-none | 17,491 → 34,726 | 269 → 141 | 14.08 → 14.12 |
| T50-wait10msR | **0** (6/6) → 296.5 | 未定義 → 12,665 | 0.48 → 7.84 |
| T95-none | 7,314 → 145,150 | 527 → 32 | 33.60 → 34.03 |
| T95-wait10msR | **0** (6/6) → 299 | 未定義 → 12,504 | 1.46 → 22.31 |

(commit 数は計器入り build の値で性能値ではない。値の原本は `analysis/summary.json`、raw は `raw/measure1.json.gz`。)

## 7. 結果: throughput (計器・trace なし build、対ごとの比)

| 条件 | stock tps (6 反復平均) | variant tps | 比の平均 (最小〜最大) |
|---|---|---|---|
| S0-none | 4.24M | 4.22M | 0.997 (0.988〜1.002) |
| S0-wait10msR | 0.66M | 4.00M | 6.08 (5.94〜6.71) |
| S50-none | 6.01M | 5.98M | 0.995 (0.984〜1.006) |
| S50-wait10msR | 1.42M | 5.61M | 3.96 (3.88〜4.37) |
| S95-none | 9.29M | 9.19M | 0.989 (0.985〜0.993) |
| S95-wait10msR | 5.66M | 8.97M | 1.59 (1.56〜1.68) |
| T0-none | 3.46M | 3.54M | 1.025 (0.964〜1.073) |
| T0-wait10msR | 0.64M | 2.72M | 4.25 (4.09〜4.71) |
| T50-none | 5.45M | 5.73M | 1.052 (1.021〜1.073) |
| T50-wait10msR | 0.17M | 2.82M | 16.74 (16.67〜16.83) |
| T95-none | 12.70M | 13.11M | 1.032 (1.023〜1.047) |
| T95-wait10msR | 0.52M | 8.03M | 15.50 (15.43〜15.57) |

- 長い ro が無い 36 対の比は 0.964〜1.073、長い ro の 36 対は 1.560〜16.831。
- 既定 genome の ro 95% では 6 対すべてで variant が遅い (0.985〜0.993)。ro commit ごとに rdtscp・flag 確認・自 thread の GC 実行が加わる費用と整合する。最良 genome では ro 50/95% で variant が速い (長い ro なしでも公開が増えて境界が新しくなる効果と整合するが、機序は本計測では分解していない)。

## 8. (b) 固定 snapshot のままでは残る分

variant の長い ro 条件と長い ro なし条件の境界年齢の差 (反復ごとの差の平均、`analysis/boundary-table.json`) と、公開された境界と同じ rts を持っていた tx のうち ro の割合 (vlife の保持者集計):

| 系列・ro | 境界年齢の差 µs (wait10msR − none) | 公開時の保持者のうち ro の割合 |
|---|---|---|
| S0 | 13,906 | 0.024 |
| S50 | 14,014 | 0.310 |
| S95 | 13,097 | 0.877 |
| T0 | 13,405 | 0.026 |
| T50 | 12,524 | 0.808 |
| T95 | 12,472 | 0.947 |

- variant で公開が再開しても、長い ro の rts (begin 時の MinWts − 1、tx の間変えない) が境界を押さえるので、境界年齢は長い ro の長さ (10 ms) 程度に留まる。これを縮めるには ro の snapshot を前へ動かす必要があり、固定 snapshot を要求する ro では許されない (出典メモ §17 の 2 種の区別)。
- ro 0% で保持者の ro 割合が小さいのは、長い ro 以外に ro がいないため (長い ro 1 本 / 48 worker)。保持者の集計は「同じ rts を持っていた」の意味で、その tx だけが境界を押さえていたという意味ではない (md_15 §6.4 と同じ)。
- **保持時間そのもの (長い ro の slot が最小である時間) は測っていない** (vlife は公開時にだけ保持者を採る)。

## 9. md_22 の依頼との対応・食い違い

| 依頼 | 本 wave |
|---|---|
| (a) と (b) を分けて扱う | (a) を実装・検査・計測、(b) は §8 の観測と限界だけ |
| 小モデルに ro commit が flag を上げる場面、GC 安全と serializability を全探索、危ない版を正例に | GC 安全は全探索 (§3)。**serializability はモデルの対象外** (段 6 のレビューで固定履歴の J1 が恒真に近いと指摘され削除。C++ の判定器で確かめた §4)。「flag を上げる前に reader の参照が残る」は陰性対照 (違反 0)、「境界を下げる」は bad-clear-slot (違反あり) |
| Cicada の inert variant patch、md_3 / md_17 の判定器 | §2・§4。INLINE_VERSION_OPT=1 の trace 網羅は md_20 未着で未確認 |
| md_11 の観測最良設定を土台、ro 比率 × 長い ro、stock と variant を同時刻、throughput は計器なし | T 系列が土台。md_15 の最大効果条件 (既定 genome・skew 0) を S 系列として追加 (段 3 の指摘) |
| ledger・README の該当 entry | README だけ (§2、ledger は契約上 1 件固定) |
| 合計 2 node 時間未満、md_18・md_20・md_21 と同じノードで計測しない | §10・§12 |

## 10. 生出力の所在

- raw (本 dir `raw/`、gzip): `measure1.json.gz` (診断)、`throughput1.json.gz`、`verify2.json.gz`、`smoke3.json.gz`。measure1・throughput1・verify2 は **compact**: 各 run に重複して入っていた build の受領証を `{macro, trace, vlife, sha256}` と `build_key` (最上位 `builds` の key) に縮め、外した写しの sha256 を `build_sha256` に残した (`compaction` field)。stdout・vlife・workload・count・verifier の report は変えていない。compact からの作図は完全な raw からの作図と数値が一致した (数表の違いは入力 path と sha256 だけ)。`raw/SHA256SUMS` に compact・gzip・完全な raw (`full:` 接頭辞) の sha256。
- 完全な raw と trace は repo 外 (job dir `raw/`、永続を保証しない)。
- 図: `figures/` (生成器 `tools/plotting/plot_vhash_ro_gc_publish.py`、入力は compact raw、provenance json に入力 sha256)。
- 小モデルの結果: `model/ro_gc_publish-model.json` (`python3 -m tools.vhash_forwarding_model.ro_gc_publish --out <json> --max-states 2000000` の出力、1fad6942b。module は最終 commit まで不変)。
- 集計: `analysis/summary.json` (本文の表の原本)、`analysis/boundary-table.json` (§8)。
- 非同居の照合: `analysis/node-overlap.json`。並走 wave の receipt には絶対時刻が無いので、終了 = receipt の mtime、開始 = mtime − state_history の最大経過秒 (queue 待ちを含む広い窓) とした。host と窓が取れた 45 件で重なり 0、10 件は host が無く照合不能、md_18 は receipt が無かった。

## 11. 限界

- **走行時間:** 3 秒。stock で公開が止まると版が溜まり続けるので、長い ro の条件の stock の throughput は走行時間に依存する (長いほど悪化すると見込まれるが測っていない)。
- **合成の長い ro:** worker 1 の全手続きが 10 ms の read-only。長い ro が少数・断続的な負荷では効果の大きさが変わる。
- **観測者効果:** 公開回数・境界年齢は vlife 計器入り build の値。throughput は計器なし build。
- **効果の分解なし:** variant は公開の早まりと自 thread の GC 実行の早まりの両方を含む。
- **正しさの上限:** indeterminate。最良 genome の trace 網羅は md_20 待ち。delete・insert・TPC-C は検査していない。
- **小モデル:** 5 構成、逐次一貫性、delete なし。
- **T 系列の実現 ro 率:** ro 50% 指定で試行ベース 0.408。

## 12. 実装と検証の記録

- 段 1 brief (`verbatim/s1-brief.md`)、段 2 plan 1 本、段 3 相談 2 本 (正しさ境界、実効性と過剰)、段 4 裁定 (`verbatim/s4-ruling.md`、単一 patch・workload patch 新設・計数 macro・S/T 2 系列・均衡順序・変異事前登録)。
- 段 5: Codex `role=author` 2 本 (小モデル、patch・driver・登録簿・作図)。
- 段 6: レビュー 2 本 (2 本とも NO-GO) → fix1 (小モデルの範囲・安全腕で切断が起きない空の主張・正例の初期状態・固定履歴の J1 削除、登録簿の赤 10 件、作図 schema、verify の記録名)。以後は親の実機での発見に対する fix: fix2 (spawn-site 件数 pin)、fix3 (masstree の config.h が build 時生成物で gate の前処理が失敗 → gate 前に依存物 build)、fix4 (vlife build に LONGTX 専用の flag を渡していた)、fix5 (verify の受理条件が Cicada で到達不能)、fix6 (spawn-site test の行番号)、fix7・fix8 (作図: 実データの値域で配置検査が落ちる、公開 0 回の印が variant の値と同じ高さに見える)、fix9 (表示範囲外の目盛りラベルを配置検査が数える)。fix の裁定は `verbatim/s6-fix{1..9}-ruling.md`、焦点再レビュー 2 本 (`verbatim/s6-focus{1,2}.md`) はいずれも統合 GO。2 本目は親の派生値の誤記 1 件 (長い ro なしの比の下限を 0.985 と書いた、正しくは 0.964) を検出し、本文は訂正済み。
- 焦点走 (変更 test と consumer 44 file): 1 回目 10 failed → … → 最終 commit 41e47091d で 5,166 passed / 0 failed (36822.nqsv)。
- 変異 (本 dir `mutation/`、事前登録は `verbatim/s4-ruling.md` と `verbatim/s6-fix1-ruling.md` の erratum): D1009 の独立 clone を source-repo に、`dispatch_compute.py --task mutation` の束ね経路で走らせた。
  - 初回 dispatch probe (05e0e435f、36746.nqsv、Elapse 2,051 s、`spec-probe.json`・`ledger-probe.json`): 全変異 SURVIVED 期待で観測 node を集めた。baseline PASSED、登録した負の変異 13 件すべてが赤 node を出し、等価変異 EQ-1 は生存。
  - 本走 A (最終 commit 41e47091d、36824.nqsv、Elapse 408 s、`spec-final-a.json`・`ledger-final-a.json`、test は小モデルと publish の 2 file): registered 13 = matching 13 (KILLED 12、EQ-1 SURVIVED)。
  - 本走 B (同 commit、Elapse 112 s、`spec-final-b.json`・`ledger-final-b.json`、test は condition gate の 1 file): registered 1 = matching 1 (MB3 KILLED)。
  - 殺した変異: 小モデルの GC 安全 oracle を常に無違反にする (MA1)、正例の slot 引上げを消す (MA2)、leader が flag を見ずに公開する (MA3)、safe-mainte の ro が `mainte()` を通らない (MA4)、適法な切断を起こさない (MA7)、variant の `mainte()` を無条件にする (MB1)、gate の inert 値 (MB3)、throughput が VLIFE を拒否しない (MB4)、順序の均衡を崩す (MB5)、verify が巡回 (rc=1) を受理する (MB6)、COUNT の flag 立て 0 を受理する (MB7)、非 ro の write 保証を消す (MB8)、作図の stock と variant を取り違える (MB9)。
  - 登録から外したもの: MA5 (参照解放の前に GC 実行、単一の注入点が無い)、MA6 (fix1 で J1 adapter を削除)、MB2 (`mainte()` を参照解放の前へ移すと hunk の文脈ごと書き換わり patch の適用自体が壊れ、単一理由にならない)。
  - MB1・MB8 は patch の文字列構造を見る test (`test_both_patches_apply_without_fuzz_on_real_preimages`) が殺す。C++ の実行時挙動は smoke の計数行と verify で確かめた範囲に限る。本走 A は file を絞ったので MB1 は構造 test だけで殺され単一理由 (probe では condition gate の登録簿 test も同時に赤になった)。
- local main の取り込み (2026-09-30): 受入の終端 merge が main 17995a4fe (VHash hot block wave の着地) との 7 file 衝突で止まった。衝突 13 箇所はすべて「両 wave が同じ登録簿の同じ位置へ別の項目を足した」型だった。加えて衝突の外で、両 wave が同じ件数 pin を同じ新値へ書き換えていた (例: `_COMPILE_TIME_BRANCH_MACROS` 51→54)。このため git の 3-way 合成は、両 wave 分の合算が要るのに 1 回分の加算しか残さない。裁定 (`verbatim/s6-merge2-ruling.md`: 和集合、件数 pin の再導出、受理集合を動かさない) に従って Codex `role=author` の fix 子が合成の最終形を書いた。合成後の macro は 75 個で、件数 pin は branch 57・meaning 58・CMake 51、本 wave の build sink は covered 4 / proven-unreachable 71、s8b は covered 75、T2520 は deferred 14 / proven-unreachable 61 になった。merge commit は afd33c945 (message は子の起草、trailer は codex author と claude integrator)。子を merge 途中の作業木へ投入して起動時に停止した件は F815 の再発、同値 pin の型は新規 F として failures fragment に記録した。
  - 焦点走 8 (afd33c945、上の 44 file に main 側の hot block test 3 file を足した 47 file、37045.nqsv): 5,253 passed / 0 failed / 8 skipped。
  - 変異 B の取り直し (afd33c945、合成で gate の登録簿と test が書き換わったため。spec は同一 bytes、37046.nqsv、Elapse 106 s、`ledger-final-b2.json`): registered 1 = matching 1 (MB3 KILLED、赤 node は事前登録の 2 本と一致)。
- 計算ノードの使用 (各 job の Elapse): smoke 3 本 19 + 148 + 151 s、verify 2 本 428 + 438 s、本計測 2 本 677 + 641 s、焦点走 8 本 139 + 136 + 181 + 261 + 176 + 175 + 174 + 179 s、変異 probe 2,051 s、変異本走 408 + 112 + 106 s、provenance 監査 10 s。**合計 6,610 s (約 1.84 node 時間、2 node 時間未満)**。land 前の受入全走は別 (段 9 の関門)。

## 13. 次の版 (paper-story-vhash 2 版目) へ

- **U0 (GC 接続) の足場:** Cicada の GC は「全 worker の flag」を公開条件にしているため、read-only だけを続ける worker が 1 本いると公開が止まり、3 秒の YCSB で throughput が最大 1/32 まで落ちた。これは snapshot の意味と無関係な実装上の欠陥で、ro commit で `mainte()` を通すだけで直る (比 1.56〜16.83、長い ro なしの費用は −3.6〜+7.3%)。**VHash の GC 側の主張を測る比較相手は、この修正を入れた Cicada にすべき** (入れない stock に勝っても、公開停止という別の欠陥に勝っただけになる)。
- **残る分 (b):** 修正後も、長い ro の rts が境界を押さえる分 (長い ro の長さ程度、本計測で約 13 ms) は残る。snapshot を前へ動かせる ro (serializable でよい ro) に限って縮められる余地で、VHash の forwarding (md_14・md_21) が狙う部分と重なる。固定 snapshot が要る ro では縮められない。
- **安全の論点:** 版を守るのは tx の間変えない rts slot で、flag の時機ではない (小モデル)。tx の途中で slot を動かす変更 (前進を GC へ反映する設計) は、flag を tx の途中で立てることと組み合わさると回収に届く (md_14 の不具合と同じ構造)。
