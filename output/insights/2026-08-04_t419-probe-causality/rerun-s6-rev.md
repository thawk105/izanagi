## VALID に必要な条件 × Pegasus 実機

| # | 必要条件 | 前回実測・見積り | 成立判定 |
|---:|---|---|---|
| 1 | `observations` / `calibration` / `environment` が mapping、A2 mode が厳密に `busy` / `sham`、構造検査が例外を出さない | A0 の構造は正常。A1 以降は未実測 | △ |
| 2 | allocated CPU が昇順・重複なしの 48 個 | 前回は CPU 0–47 | ○ 実測済み |
| 3 | `PBS_JOBID`、有効な `bnodeNNN` marker | 前回はいずれも有効 | ○ |
| 4 | `T419_QUEUE` / `T419_PROJECT` が非空、scheduler 情報があれば一致 | `gen_S` / `SFC`。scheduler env は unavailable だがこれは許容 | ○ |
| 5 | submission 時の HEAD、driver、PBS、calibration、`env_attestation.py` の hash が一致し、関連 path が clean | 前回の submission / finalization は両方 `matched=true`。今回は新 HEAD/hash の投入が必要 | ○ 条件付き |
| 6 | calibration pin が一致し、band が有限な median±tolerance の厳密式 | 前回 `2101 ±2% = [2058.98,2143.02]`、pin 一致 | ○ |
| 7 | `observations.exceptions` が空 | A1 で競合判定が発火すると例外が入り、後続 arm も欠落する | **× 高リスク** |
| 8 | 6 arm がすべて存在し、primary 読みが A0=30、A1=240、A4=30、A3q=50、A2=80、A3c=15、計445 | generator はその形だが、A1 の早期停止で満たせない可能性が高い | **× 高リスク** |
| 9 | 全 primary read と検査対象 anchor が48要素、CPU集合一致、有限かつ正の MHz | A0 は全読み成立 | △ A1以降未実測 |
| 10 | 読みごとの affinity が full set または pin target の singleton、reader before/after がその中 | A0 full-set は成立。非rootでも自己・fork child の affinity 制限は通常可能だが実機未試行 | △ |
| 11 | pin 失敗・途中/最終 affinity 復元失敗がない | 失敗時は例外または arm 欠落。自己 affinity 操作なので成立見込み | △ |
| 12 | 各 arm の diagnostics pre/post が `complete=true` | 前回は各 snapshot で `cpuinfo_cur_freq` 48件だけ errno 13。他819 field は value。修正後は `value=819 / unreadable=48 / error=0` となる | ○ |
| 13 | 各 arm の `/proc` visibility が完全で isolation accounting error がない | A0 は838 process、visibility error 0 | △ 長い arm は未実測 |
| 14 | 各 arm で既知非自消費が CPU ごと5 tick以下、かつ unknown residual が self 上界以下で、attribution が CLEAN/UNRESOLVED | A0 は通る可能性があるが、A1/A2 の長い窓では `nqs_shpd` が6 tick以上になりそう | **× 最重要** |
| 15 | top-level anchor 数が A0=6、A1=48、A4=1、A3q=10、A3c=3、全 anchor が instrumentation 後 | A0 は成立、生成経路は決定的 | △ |
| 16 | A0/A3q/A3c の block 数・各5読み・flat/nested/anchor の一致 | A0 は成立 | △ |
| 17 | A1 pin order が seed 419 の48 CPU permutation、各 CPU が5 primary+1 anchor、`by_pin` と flat 順序が一致 | 静的には整合 | △ 実機未試行 |
| 18 | A2 が8 unique target、各 pair に busy/sham 各1、各5読み、flat一致、anchor が child barrier 後 | 静的には整合 | △ |
| 19 | child の PID/starttime、requested/observed affinity、live/terminate/wait、tick arithmetic がすべて整合 | child 実測なし | △ |
| 20 | busy child ≥5 tick、sham child ≤1 tick | 前回の `CLK_TCK=100`。各A2条件は約250msなので busy≈25 tick、A3c≈75 tick。sham は readiness 後に sleep、終了前 snapshot なので0 tick見込み | ○見込み。ただし実測なし |
| 21 | A2 cooldown が各条件1秒以上、threshold-only INCONCLUSIVE が3/8未満、status 再計算一致 | `sleep(1)` は成立見込み。ただし16 cooldown が A2 isolation 窓を約16秒延ばす | △、かつ #14 を悪化 |
| 22 | A3 contention busy evidence が VALID、全 anchor が barrier 後 | 約750ms busy なので tick 下限は十分 | ○見込み |
| 23 | raw `/proc/cpuinfo` を3件保存し、production parser と3件すべて一致 | 前回3/3、各48要素で一致 | ○ |
| 24 | method-table、coresident、causal metrics の計算が例外を出さない | 構造上は成立見込み。ただし α の意味論は後述のとおり誤っている | △ |
| 25 | provenance 収集と終了時 hash 再照合が成功 | 前回はいずれも成功 | ○ 条件付き |
| 26 | 900秒 deadline 内に測定完了し、20分 walltime 内に finalization/done-marker まで完了 | 完走見積りは約55秒。時間予算自体は十分 | ○ |
| 27 | 0.95 / 0.05 / 46 | これは VALID 条件ではなく、VALID 後の CONFIRMED/REFUTED 条件 | — 不変 |

一つでも不成立なら `execution_validity=INVALID` となり、`causal_verdict=NOT_EVALUATED` になる。現状は #14 が投入阻止点である。

### S6-01

- **ID:** S6-01
- **主張:** 閾値5の一次根拠「`nqs_shpd` が CPU 22 で4 tick」は、指定された raw から再現できない。raw が示す residual は CPU22=1、CPU44=3、合計4であり、旧 schema の competitor record は process 自身の `cpu_ticks_delta` を保存していない。
- **file:line:** [brief.md:26](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-rerun/brief.md:26)、[probe:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39)、[result.json:78284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:78284)、[result.json:78992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:78992)、[result.json:79016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:79016)
- **失敗シナリオ:** 実際の `nqs_shpd` process delta が6以上なら、修正後も最初のA0で同じ停止をする。逆に residual total 4を根拠に5 tickを許すなら、帯外だったCPU44の3 tickも混ざった別量を閾値根拠にしている。
- **成果物影響:** A0で再停止すれば A1–A3、因果判定、α/β/γ表が再び欠落し、U-2は進まない。
- **強度:** **強**。rawとの不一致は確定。ただし旧出力が捨てた真の process delta 自体は不明。
- **判定:** **must-fix**
- **最小の是正案:** 保存済み一次資料から process delta を再現できる証拠が別にあるなら provenance 付きで示す。なければ「4 tick」を事実扱いせず brief を再裁定し、full run 前に delta を保存する bounded A0 preflight を置く。閾値引上げや所有者免除では直さない。

### S6-02

- **ID:** S6-02
- **主張:** 5/6 tick は arm 全体の絶対量なのに、根拠になったA0とA1/A2で isolation window 長が約8–13倍違う。同じ常駐負荷でもA1で最初に発火する。
- **file:line:** [probe:2169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2169)、[probe:3363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:3363)、[probe:3471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:3471)、[result.json:79136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:79136)、[result.json:82666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:82666)
- **失敗シナリオ:** A0 isolation window は1.558秒。A1は `48×5×50ms` で最低12秒、A2は16条件の読み4秒＋cooldown16秒で最低20秒。同じ率なら raw のCPU22 residual 1 tickだけを外挿しても A1≈7.7 tick、brief の4 tickを使えば≈31 tick。A1がCOMPETITORとなり後続を抑止する。
- **成果物影響:** 計算 job は約A1終了時に fail-closed し、因果の本体を一度も評価できない。
- **強度:** **中〜強**。窓長は静的確定、A0値は実測。A1への定常率外挿だけは未実測。
- **判定:** **must-fix**
- **最小の是正案:** 閾値を上げず、同じ固定長の critical subwindow ごとに5/6を判定し、いずれかが6以上なら失敗させる意味論へ brief から再登録する。arm-total のままなら実機完走との両立根拠がなく、投入しない。

### S6-03

- **ID:** S6-03
- **主張:** 「per-CPU集計」は実装されていない。移動 process の全 delta を終了時CPU一個へ載せている。
- **file:line:** [probe:2049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2049)、[probe:2058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2058)、[test:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:66)、[result.json:66557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:66557)、[result.json:75777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:75777)
- **失敗シナリオ:** process がCPU0で3 tick、CPU1で3 tick消費してCPU1で終わると、実際は各CPU≤5なのに実装はCPU1=6として偽COMPETITORにする。逆方向の誤配分では真の同一CPU aggregateを隠し得る。A0でも少なくとも1 process の20→21移動が実測されている。
- **成果物影響:** 正常 job の偽INVALID、または汚染 job の偽VALIDにより因果結論が壊れる。
- **強度:** **中**。静的反例と実機 migration は確定だが、移動 process の正 tick delta は未保存。
- **判定:** **must-fix**
- **最小の是正案:** endpointだけから正確なper-CPU量を捏造しない。移動かつ正deltaは fail-closed な `MIGRATION_UNRESOLVED` とするか、実際のper-CPU証拠を採る。別CPUに3+3の正例を追加する。

### S6-04

- **ID:** S6-04
- **主張:** brief が要求する「A1 incidental CPU と帯外CPUの別集計」がないため、`ATTRIBUTION_UNRESOLVED` は因果計算上CLEANと同じである。
- **file:line:** [brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-rerun/brief.md:39)、[probe:398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:398)、[probe:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:749)、[probe:2204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2204)
- **失敗シナリオ:** A1でCPU xに1–5 tickの非自消費があり、同じCPUが帯外でも、`causal_metrics()` はその交差を一切出さず通常のhitとしてCONFIRMEDへ使う。
- **成果物影響:** レポートは reader効果と incidental activity の交絡を識別できず、U-2が誤方式を選び得る。
- **強度:** **強（静的確定）**
- **判定:** **must-fix**
- **最小の是正案:** A1 isolation の incidental CPU集合と各readのOOB集合をjoinし、CPU別・pinned/control別の overlap 件数・率を `causal_metrics` に保存する。validity gate自体は緩めない。

### S6-05

- **ID:** S6-05
- **主張:** `method_table.alpha` は、前回READMEが明示的に否定した「CPU巡回なしのK回最小」を再び評価している。A1 pin sweepもalpha表には使われない。
- **file:line:** [README.md:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/output/insights/2026-08-04_t419-probe-causality/README.md:47)、[probe:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:303)、[probe:3431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:3431)、[test:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:613)
- **失敗シナリオ:** A0同様readerが同一CPUに留まると、A3 quietも5回同じreader CPUを読み、αを0/ブロックとして報告する。これは巡回込みのαを測っていないのに execution はVALIDになり得る。
- **成果物影響:** 完走してもα/β/γの2×3表のα列が別方式の値になり、方式選択に使えない。
- **強度:** **強（コード・README・A0実測が一致）**
- **判定:** **must-fix**
- **最小の是正案:** 各α blockでK個の異なるreader CPUを明示的に巡回させ、reader/pin列を保存・検証する。できないなら現行行を `alpha_without_rotation` と改名し、α本体として報告しない。

### S6-06

- **ID:** S6-06
- **主張:** 新fixtureは入力としては単一理由だが、6 tick/error側で理由集合をassertしていない。また全nonself fixtureがCPU0固定で、per-CPU対global-totalを区別できない。
- **file:line:** [test:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:66)、[test:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:768)、[test:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:812)
- **失敗シナリオ:** 2 CPUに3+3 tickを載せても拒否するglobal-total変異や、6/errorに第二の拒否理由を足す変異が追加テストを通過できる。
- **成果物影響:** 必須の受理集合と単一理由性をテスト成果物が固定できない。
- **強度:** **強（テスト空白は確定）**
- **判定:** **backlog**。ただしS6-03/S6-04の修正時に同時追加すべき。
- **最小の是正案:** `3 tick on CPU0 + 3 tick on CPU1 ⇒ VALID/UNRESOLVED` を追加し、5/6・unreadable/errorについて `validity_reasons` の完全一致と `INVALID ⇒ NOT_EVALUATED` をassertする。EPERM、EACCES、ENOENT、EIOも直接固定する。

確認できた点として、uid・comm・cgroupを判定に使う分岐はなく、root `/system.slice` の6 tickもCOMPETITORになる。ENOENTは`absent`、EACCES/EPERMは`unreadable`、UnicodeErrorおよび他errnoは`error`へ落ち、`error`は`complete=false`からINVALIDとして効く。0.95 / 0.05 / 46、canonical band、445、arm順、hash再照合、`INVALID ⇒ NOT_EVALUATED` は差分上不変である。

## 総括

- (a) 投入判定: **NO-GO**。
- (b1) P1の4-tick根拠がrawと整合せず、さらに固定5/6を長いA1/A2 armへ適用すると再停止が濃厚。
- (b2) per-CPU attributionがendpoint近似で、A1 incidental/OOB別集計も欠落している。
- (b3) α表がCPU巡回なしの別方式を測っており、完走しても主要成果物が成立しない。
- (c) 新たに最初に発火しそうなのは `A1_pin_sweep:competing_process_detected`。通ってもA3 quietが境界、A2はさらに危険。
- (d) 修正後の投入ではA0/A1各CPUのnonself delta、incidental/OOB交差、busy/sham tick、INCONCLUSIVE数を確認する。
- (d) parser 3/3、submission/finalization hash、新HEAD、affinity復元、全445読み、900秒内完了も確認する。
- pytest・self-test・実機実行は行っていない。静的レビューと指定済みrawの読取りのみ。