# F241 の根本原因を実測で決着させる — 「perf が無い」ではなく「振り分け役を呼んでいた」

wave = `dev-wave-f241-perf-attribution`、base commit = `764fdf202`。
実測日 = 2026-09-04 (JST)。実測環境 = Pegasus (login = pegasus02、計算ノード = gen_S)。

`authority: none` / `default_effect: no-state-change` — 本書は測定の記録であり、
受理集合・運用経路・裁定を 1 bit も変えない。

## 結論 (先に書く)

F241 は「計算ノードに現行 kernel 用 perf が無く、環境側 (管理者手番) に linux-tools を
入れてもらう**以外に道はない**」と結論していた。実測により、次のように分かれた。

**真である部分。** 計算ノードの kernel は `5.15.0-173-generic` だが `/usr/lib/linux-tools/` には
`5.15.0-100-generic` と `5.15.0-135-generic` しか無い。この不一致のため、PATH の literal `perf`
は `stat` が rc=2 で失敗する。F241 が観測した rc=2 そのものは正しい観測である。

**誤っている部分は 3 つある。**

1. **「perf が無い」への無限定な一般化。** 既設の
   `/usr/lib/linux-tools/5.15.0-{100,135}-generic/perf` は実在して動く。
   46/46 の測定で `--version` と `stat` がともに rc=0 を返し、
   cycles・instructions・LLC-loads・LLC-load-misses の 4 event すべてに実数値が出た。
2. **「導入以外に道はない」。** rc=2 を返すのは `/usr/bin/perf` という**振り分け役**であって
   perf そのものではない。候補から動く実体を選ぶ道は既に repo にあり
   (`tools/pegasus/certify_calibration.sh`)、その道を通った受領証も repo にある。
3. **「perf を外す回避を採ってはならない」。** これは現行の受理集合と矛盾する。
   D352 の裁定により、正式系列は perf 不在でも進み、`use_perf=false` の測定は eligible である。

**この訂正は「perf を使え」と言っていない。** 絶対 path を運用の選択に使う変更は
F89 の受理集合裁定を要し、[T-970] は見送りで確定している。本 wave は事実と記録だけを直した。

## 機構 (なぜ rc=2 になるのか)

`/usr/bin/perf` は Ubuntu の bash script で、次だけを行う。

- `/usr/lib/linux-tools/$(uname -r)/perf` が存在すれば `exec` する。
- 存在しなければ、**他の導入版へ fallback せず**、
  `WARNING: perf not found for kernel <版>` を stderr へ出して **exit 2** する。

したがって `perf` の非 0 rc は「この kernel 版に対応する実体が無い」ことしか言わない。
**その先に動く実体があるかどうかについては、何も言わない。**

## 実測

### 対の設計

同じ node・同じ job・同じ subprocess 実装の中で、literal `perf` と
`/usr/lib/linux-tools/*/perf` の全候補を対にして測った。ノード間差・時点差で
交絡しないようにするためである。両側 control を同じ run に含めた。

- positive control: `/bin/true` を素で起動して rc=0 (測定機構が生きている)。
- negative control: 実在しない候補 `/usr/lib/linux-tools/izanagi-f241-no-such-kernel/perf`
  が `FileNotFoundError` で起動しない (不在の検出力がある)。

両 control は 24 run すべてで成立した。

### 計算ノード (gen_S)

24 job を投入し、**23 job が結果を返した**。request `975613` は scheduler 出力 (`.o` / `.e`) も
probe 出力も戻らず、原因不明のため集計から除外した (回収率 23/24)。

distinct node は **6** である (bnode049 / bnode074 / bnode075 / bnode076 / bnode092 / bnode101)。
同じ node に複数 job が当たっており、bnode092 と bnode101 だけで 17/23 run を占める。
全 node が kernel `5.15.0-173-generic`、`perf_event_paranoid=0`、
`/usr/lib/linux-tools/` は 100 と 135 の 2 つだけだった。

| 呼び方 | 測定数 | `--version` rc | `stat` rc | 4 event の実数値 |
|---|---:|---|---|---|
| literal `perf` | 23 | 2 | **23/23 が 2** | 0/4 |
| 絶対 path (100 と 135) | 46 | 0 | **46/46 が 0** | **46/46 が 4/4** |

`stat` の argv は `perf stat -e cycles,instructions,LLC-loads,LLC-load-misses -- /bin/true`。
literal の stderr は全件 `WARNING: perf not found for kernel 5.15.0-173` で始まる。
絶対 path はすべて symlink である (F89 の記述と一致)。

### ログインノード (pegasus02)

kernel `5.15.0-190-generic`、`perf_event_paranoid=4`、tools は 101 / 136 / 173。

| 呼び方 | `--version` rc | `stat` rc | 理由 |
|---|---|---|---|
| literal `perf` | 2 | 2 | `not found for kernel 5.15.0-190` |
| 絶対 path 3 本 | **0** | 255 | `perf_event_paranoid` |

ログインノードでは、実体は 3 本とも在って起動する。`stat` が拒まれるのは**不在ではなく権限**で
ある。同じ「使えない」でも、計算ノードの rc=2 とは別の原因である。

## この測定が主張しないこと

- **production の測定経路が完走することは示していない。** 親の probe の argv は
  `perf stat -e <events> -- /bin/true` であり、`orchestrator/calibrator/perf_preflight.py` の
  production argv は `-x,` と `-o <tmp>/perf.csv` を加えて CSV を読む。
  `certify_calibration.sh` は `sleep 0.1` を使う。示したのは
  **候補実体・権限・4 event group・短命 process までの直接 smoke** であって、
  CSV 出力と読取、PATH shim、実 workload ではない。
- **「道はある」は経路によって真偽が違う。** shell 経路 (`certify_calibration.sh`) は
  `[[ -x ]]` で candidate を受理し realpath を PATH 先頭へ置くので、この道は既に開いている。
  Python 経路 (`orchestrator/qualification/submission.py::_executable`) は
  `not Path(found).is_symlink()` を要求するため symlink の候補を捨てる (F89、未裁定)。
  床値 preflight は literal `perf` だけを probe し、候補は evidence にしか使わない (D348)。
  この 3 経路を「絶対 path」の一語でまとめてはならない。
- **F241 の 8 node と同等の標本強度ではない。** F241 は名前つき 8 node、本測定は 6 distinct node
  である。過去の実測 (T-293 の bnode005 / bnode009 など) は別日・別 probe の独立した補強で
  あって、合算して「8 node」と数えることはできない。
- gen_S の全 node、別 kernel の node、将来の allocation へ一般化しない。全標本が
  kernel・paranoid 値・tools 集合の 1 種類ずつしか見ていない。
- 欠測 1 件 (975613) の無作為性は保証しない。

## repo が既に持っていた反証

F241 は 2026-08-12 に書かれた。その時点で、同じ repo には次があった。

| 出所 | 日付 | 記述 |
|---|---|---|
| `docs/failures.md` の F89 | 2026-08-03 | 候補が指す perf は計算ノード (bnode005 / bnode009) に実在し、`--version` も production 同一 smoke argv も rc=0。ただし Python 経路は symlink を拒む |
| `output/insights/2026-08-03_t293-perf-site/README.md` | 2026-08-03 | 同上の実測の全文 |
| `output/env/pegasus/calibration/job-staging/0:892707.nqsv/` | 2026-08-06 着地 | 計算ノード (同 dir の `hostname.stdout` = `bnode048`) で `/usr/lib/linux-tools-5.15.0-135/perf` を選び、`perf-candidate-0.smoke` に 4 event の実数値を記録 |
| `docs/pegasus-runbook.md` の環境事実 | — | 「perf は dispatcher (`/usr/bin/perf`) がカーネル不一致で使えない。実体を policy の候補から機能 smoke つきで選定し PATH 注入する」 |

F241 の後にも、同じ機構が独立に 2 度書かれた。

| 出所 | 日付 | 記述 |
|---|---|---|
| `docs/failures.md` の F501 | 2026-08-16 頃 | 「Ubuntu 標準の `/bin/perf` ラッパー (kernel version 不一致を検出して警告終了する) が選定済み perf より優先されるようになっていた」 |
| `output/insights/2026-08-26_b10-balanced-profile/README.md` | 2026-08-26 | 「**perf は計算ノードで動く。** … `/usr/bin/perf` の dispatcher は必ず失敗する。一方 `/usr/lib/linux-tools/5.15.0-135-generic/perf` は `stat` / `record` / `report --stdio` のすべてで rc=0」 |

**同じ台帳 (`docs/failures.md`) の中に、同じ物理事実についての相反する根本原因が 23 日間併存した。**
F241 の実 campaign ノードの片方である **bnode049**、および
`output/insights/2026-08-04_t425-floor-scoping/README.md` が「perf 不在で全 rep 失敗」と記録した
**bnode074** の両方で、本測定は絶対 path が rc=0・4/4 を返している。

## 台帳への反映

- F241 に `supersede: 2026-09-04` を 1 行追記した。新しい F は採らない。
- F1 (一次資料に当たらず周辺記述から転写する) の **再発**として顕在化した。
  F241 は、同じ台帳の F89 と `/usr/bin/perf` の実物のどちらも確認せずに、
  観測 (rc=2) からの推論を根本原因として記録した。これは F1 の既存射程
  (「機構の実在状態を一次資料なしで転写する」「推測の確度が見立てから確定事実へ変わる」) に一致する。

## 未適用の訂正 (ユーザー手番)

`docs/b10-backoff-shape-preregistration.md` の §7 は
「perf に依存する診断は本実験の範囲外とする (**この計算ノードに perf は無い**)」と書いており、
括弧内は本測定により誤りである。**本 wave はこの文書の bytes を変えていない。**

理由は、この文書が発効済み事前登録であり、`orchestrator/campaign/b10_backoff_shape_sweep.py` の
`run_formal` が `report` を含む全 phase で `load_preregistration` を通し、作業木の bytes が
`git show <prereg_commit>:<path>` と完全一致することを要求するためである。
2026-09-04 時点で、別 wave が `prereg 77b33e37d` に束縛された B-10 正式走を実行中であり
(request `974207.nqsv`、`verify-perf balanced`、および 13.7〜17.5 時間の read-heavy 走行が予定)、
1 byte の追記でも残り phase が `prereg-blob` で停止する。

> **但し書き (D1529、2026-09-04)。** 括弧内の「13.7〜17.5 時間」は
> `output/insights/2026-09-02_t2191-verifier-parallel/README.md` の見積りの再掲である。その入力帯
> (1 反復 1346.9-1465.6 秒) は read-heavy で commit 数が飽和した 3 変種の本規模反復 (反復数 5・5・3)
> から出ていて、そのうち 3 反復は、campaign 記録上 commit (取引の確定ではなく変種の認証確定) に
> 到達しないまま打ち切られた実行 (欠測 attempt、`constant-mu2` 変種 `292d58f1dad8`) の観測分で
> ある。値を無効にするものではなく、欠測 attempt を除いた再計算は行っていない。

適用が安全になる条件は次のいずれかである。

1. `dev-wave-t1905-b10-continuation` の B-10 正式走 (balanced + read-heavy + report) がすべて
   完了し、`prereg 77b33e37d` を指す残り phase が無くなったとき。
2. 同 wave が残り phase を、追記を含まない固定 checkout (例: 同 wave の `submit-tree`、
   detached `c7ed56589`) からだけ実行すると確定したとき。

置き場所は**文書末尾**である。`## 9.` の最終行の後に `## 10.` として足す。§7 の本文行は
書き換えない (段 3 レンズ A が §0 内への挿入を規律 7 に不適合と裁定した)。
canonical machine spec block を 2 個にしないため、`IZANAGI-B10-SPEC` の marker 文字列を
本文に書いてはならない。適用後は `parse_preregistration` の `as_dict()` と `spec_sha256` が
追記前と完全一致することを実走で確かめる。

適用する本文は次のとおりである。

---

### 10. Erratum (2026-09-04) — §7 の perf 不在記述

§7 の「perf に依存する診断は本実験の範囲外とする」という**範囲の決定は変えない**。
括弧内の理由「この計算ノードに perf は無い」だけが事実として誤っていた。正しくは
「本実験の運用経路が probe する PATH の literal `perf` は、現行 kernel 用 linux-tools が
無いため動かなかった」である。

2026-09-04 の同一 node・同一 run の対測定では、kernel `5.15.0-173-generic` の
6 distinct bnode / 23 job で literal `perf` の `stat` は 23/23 が rc=2、4 event は 0/4 だった。
一方、既設の `/usr/lib/linux-tools/5.15.0-100-generic/perf` と
`/usr/lib/linux-tools/5.15.0-135-generic/perf` は 46/46 の測定で `--version` / `stat` とも rc=0、
4 event は 4/4 だった。証拠は `output/insights/2026-09-04_f241-perf-attribution/` に固定した。

本節は発効後に判明した事実の訂正であり、**事前登録ではない**。§5 の機械可読 spec、登録 grid、
解析 field、実行・報告規則、過去の成果物の束縛を変更せず、絶対 path の採用も認可しない。
本実験で perf 依存診断を行わないという範囲、literal `perf` だけを probe する現行運用、
perf 不在で測定を進める裁定はいずれも不変である。

---

上の本文中で `### 10.` としているのは、本書 (insight) の見出し階層と衝突させないための表記で
ある。実際に事前登録文書へ入れるときは `## 10.` にする。

## 成果物

- `measurements/` — probe 出力 24 file (計算ノード 23 + login 1) と、
  派生集計 `pairing-rows.json` の計 25 file。
- `probe-verbatim.md` — probe と job script の逐語、投入 argv、集計手順、
  `/usr/bin/perf` の該当部分。実装面を増やさないため `.py` は repo へ入れない。
