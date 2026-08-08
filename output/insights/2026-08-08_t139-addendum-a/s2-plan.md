結論から言うと、追補 A は `a01`〜`a13` の全 13 field を逐語案として埋められます。ただし、これは凍結案ではありません。特に `a03` の閾値、`a10` の planning assurance、`a11` の信頼領域、`a13` の alpha spending は実測値ではなく、pilot 前に固定する設計上の選択です。

親案は、`P1/P3/P4` を採用、`P2` は式の正しさを認めつつ不採用、`P5` は修正採用とします。テスト、build、benchmark、較正 simulation は実行しておらず、緑は主張しません。

## 固定対象

追補 A が従属する core は次の三つ組です。作業木と fold commit の双方で SHA-256 を静的照合済みです。

```yaml
core_ref:
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  path: output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

追補本文は envelope metadata と `fields` を分け、`fields` の exact-key を `{a01,...,a13}` とします。core 自身も従属先三つ組の記録を要求しています。[core §14 L362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:362)

## `a01`〜`a13` の逐語表

| field | 追補 A に置く確定値・手続き | 一次根拠 | 恒真化・後付け選択を防ぐ検査 |
|---|---|---|---|
| `a01` | performance cluster は `walltime_s=3600`, internal deadline `3300`。内訳は preflight 180、build 0、correctness/liveness 0、性能 run 540、待機 1380、終了検証 180、後片付け 120、internal slack 900、scheduler safety 300。別の verification allocation も 3600 秒で固定し、後述の表どおり 26 本へ算入する。 | [core §7–8 L198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:198)、[probe cap L370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:370)、[PBS walltime L4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.pbs:4) | 全 phase の上限と総和を整数秒で再計算し、`3600` と一致しなければ拒否する。実時間を見て slack を再配分しない。 |
| `a02` | 同一 block 内の arm 間は 30 秒。block 間は 60 秒。workload 切替は block 境界の 60 秒と同一待機であり、60+60 と加算しない。最後の run 後には待機を置かない。 | [core §8 L229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:229) | `24×30 + 11×60 = 1380` を schedule から再計算する。adaptive な待機延長・短縮は禁止する。 |
| `a03` | `load1` は判定に使わず診断値に限定する。判定量は、次 run 直前の 10.000 秒間における `cpu_busy_core_equivalents = 48 × (Δtotal−Δidle)/Δtotal`。`/proc/stat` aggregate CPU counter を monotonic clock で 10 秒離して読む。`iowait/irq/softirq/steal` は busy に数える。許容範囲は閉区間 `[0.0,1.0]`。 | 48 physical cores は [runbook §1 L33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/pegasus-runbook.md:33)。無待機の `load1` は 3.29 から 40.18 へ非減少だった。[limited-screen.tsv L2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/limited-screen.tsv:2) | raw counter 2 点と時刻だけを producer が記録し、validator が値を再計算する。`recovered=true` の申告 field は持たない。範囲は取り得る `[0,48]` より真に狭く、実現値を必ず含まない。失敗後の追加待機・再観測は禁止する。 |
| `a04` | 最初の performance run の開始 marker より前の `a03` 不成立は `pre_performance_infra_failure`。marker 後は `post_performance_failure` とし、科学状態は `判定不能`、置換不可。 | [core §9 L237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:237)、[PBS state mapping L20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.pbs:20)、[performance marker L486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:486) | `performance_started` の durable marker の有無だけで写像し、TPS・失敗した arm・残り run 数を参照しない。新しい失敗分類は作らない。 |
| `a05` | 各 performance executable のファイル全 bytes に SHA-256 を掛け、lowercase 64 hex、byte size、staged path を `arms.<arm>.binary` に記録する。各 `actual_runs[]` も使用した hash を参照する。symlink を拒否し、staging 後・最初の run 前・最後の run 後に再 hash する。 | 割当て外 build と binary hash 束縛は [core §8 L223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:223)、receipt 要件は [core §12 L285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:285) | producer の hash 文字列を信用せず、validator が同一 byte buffer から再計算する。run が参照した hash と arm hash が異なれば拒否する。 |
| `a06` | build-in-allocation 予備経路は `elapstim_req=01:30:00`、walltime 5400 秒、internal deadline 4800 秒、scheduler safety 600 秒。主経路の非余裕部分 2400 秒に source staging 180 秒と 3 arm の configure/build `3×(60+180)=720` 秒を加えた 3300 秒、internal contingency 1500 秒を持つ。 | configure 60/build 180 は [probe L421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:421)。予備経路は [core §8 L225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:225) | 予備経路の選択は当該 allocation の投入前、performance 値ゼロの時点で固定する。run 後に walltime 経路を選び直さない。 |
| `a07` | W1 argv は `[-ycsb_rmw=true,-ycsb_zipf_skew=0.9,-ycsb_tuple_num=10000,-ycsb_max_ope=10,-thread_num=48,-extime=3]`。W2 は `[-ycsb_rratio=50,-ycsb_zipf_skew=0.5,-ycsb_tuple_num=100000,-ycsb_max_ope=10,-thread_num=48,-extime=3]`。W1 の read ratio は `not_applicable` とし `rratio` 引数を足さない。 | [probe L454–457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:454)。W1 実ログは RMW=true、t48、10k、skew .9、3 秒を確認する。[run log L3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/run-1-W1-stock-r1.log:3) | argv vector の要素・順序を exact 比較する。default 値を見て引数を追加しない。変更時は別 study。 |
| `a08` | source/build identity は後述の固定表。共通 repo commit `425ed1908dfd78cda97c48c2b248cdf6b83b1e91`、CCBench pin `d706650cdb31e442bef45b9b4216951d4fb40969`、patch SHA-256 `3b9cdf…1951`。performance は `TRACE=0, ADD_ANALYSIS=0`、correctness/liveness は別 build で `TRACE=1, ADD_ANALYSIS=1`。compiler は `/bin/g++`, GNU 11.4.0。 | [submission receipt L61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-05_t139-alt-x-probe/submission-receipt.md:61)、[compile summary L1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/compile-argv.tsv:1)、[probe build flags L394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:394) | source/patch/pin、normalized compile argv、実 binary hash を独立照合する。trace-enabled と performance binary の SHA-256 同一を拒否する。将来の build 成功は本案では主張しない。 |
| `a09` | seed は `7df15572d2d88f172bc69bea9bc2dc53eddcbef41211d8ece7b0a592e5b2615d`。許容集合と SHA-256 sort 手続きは後述。replacement は置換対象と同じ `cluster_slot` と schedule を再使用する。 | [core §7 L200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:200)、[D234 L10988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:10988) | seed、slot、workload、permutation だけから一意に生成する。runtime RNG、実 TPS、失敗理由を入力にしない。validator は schedule をゼロから再生成する。 |
| `a10` | `J_max=13`、候補集合 `{4,…,13}`。26 本は `verification 1 + pilot 8 + pilot reserve 2 + main ceiling 13 + main reserve 2`。共同 95% 信頼集合、最悪 power、選択規則は後述。該当 J なし、`d^-<1`、数値保証不能なら `design_not_feasible`。 | [core §6 L171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:171)、[core §11 L271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:271) | pilot raw は固定写像への入力だけ。`J_max`、confidence level、候補集合、solver tolerance を変更しない。同じ共同集合を全 J に使い、選択後の J だけに保証を掛け直さない。 |
| `a11` | 3D Hotelling ではなく、`(N,D)` の 2D Hotelling 楕円と `H` の片側 t region の積を採る。両者に共通の最小 `q` を Bonferroni tail-sum で決める。Fieller は `(N,D)` 楕円の ratio projection。式は後述。 | [core §4 L95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:95) | `q` は `J` と `a13` のみの関数。pilot covariance から critical value を選ばない。singular covariance に pseudoinverse を使わない。 |
| `a12` | J=1 screen の `throughput.tsv`（SHA-256 `755cfa7e…c4f2`）から作る 3 次元 centered residual bootstrap。`B=1,000,000`、seed `01dad84c523b0a476655b91979c91d7174e40bb5a27757ada312abf2fe158ed2`。60 セルに同時 Clopper–Pearson UCB を掛け、どれかが `α₁` 超なら `design_not_feasible`。 | J=1 screen の利用可能性は [core §0 L13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:13)、weak-null simulation は [core §7 L219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219)、raw は [throughput.tsv L1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv:1) | q を simulation で緩和・選択しない。simulation は pass/fail だけで、pilot raw を一切入力にしない。未完了も failure と同じく pilot admission deny。 |
| `a13` | primary family 総量 `α_family=0.05`、正規 ordinal `k≥1` に `α_k=0.05/[k(k+1)]`。本 study は `k=1`、したがって `α₁=0.025`。未使用 tail は再配分しない。 | primary alpha は A に置き B から動かせない。[core §14 L334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:334)、[D234 L11005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:11005) | `Σα_k=0.05` を解析的に検査する。`b01` が 1 でも未使用 alpha を `k=1` へ戻さない。B が本 study を `k≠1` と示した場合は q を変えず main admission を拒否する。 |

## `a01` — P1 と時間予算の独立検算

### cluster の正しい構成

P1 の 36 run は正しい読みです。

1 block は「3 arm の一つの順列」であり、1 run ではありません。1 workload について全 6 順列を各 1 回実行するので、

```text
6 block × 3 arm = 18 performance run / workload
2 workload × 18 = 36 performance run / cluster
```

となります。

全 6 順列では、各 arm は位置 1/2/3 に各 2 回現れます。また各 ordered predecessor pair も 2 回、block 先頭の `START` も arm ごとに 2 回です。したがって core の「位置と直前 arm がともに 2 回」という説明と一致します。[core §7 L200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:200)

現 `record-items.md` の「1 allocation あたり 6 run」は誤りです。[record-items L75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:75)

### performance cluster allocation

| phase | 秒 | 算定 |
|---|---:|---|
| admission、attestation、schedule、prebuilt binary hash 検証 | 180 | 固定 cap |
| build | 0 | 主経路は allocation 外 |
| trace-enabled correctness / liveness | 0 | 同じ allocation へ混在させない |
| performance run | 540 | `36 × 15` |
| arm 間待機 | 720 | `12 block × 2 gap × 30` |
| block 間待機 | 600 | `2 workload × 5 gap × 60` |
| workload 切替 | 60 | 1 回。block 待機と重複加算しない |
| `a03` の観測 | 0 追加 | 待機の最後 10 秒、初回だけ preflight 内 |
| raw parse、receipt、phase 完全性検証 | 180 | 固定 cap |
| 後片付け・publish | 120 | 固定 cap |
| internal contingency | 900 | deadline 3300 まで |
| scheduler safety | 300 | 3300→3600 |
| **合計** | **3600** | walltime と一致 |

run と待機の最低必要量だけで `540+1380=1920` 秒です。probe の 30 run は各 15 秒 cap で 450 秒でした。[probe L511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:511) ここへ 6 run と 1380 秒の待機を足すため、probe の 30 run と同一視してはいけません。

### 別 verification allocation

core は trace-enabled correctness を performance と同一 allocation へ混ぜないため、別 allocation が必要です。[core §7 L208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:208)

| phase | 秒 |
|---|---:|
| source staging、patch、identity | 180 |
| 3 performance + 3 correctness の configure/build/receipt | 1500 |
| 2 workload × 3 arm の trace-enabled correctness/liveness | 360 (`6×60`) |
| evidence 検証 | 180 |
| 後片付け | 120 |
| internal contingency | 960 |
| scheduler safety | 300 |
| **合計** | **3600** |

`60 秒/run` は、J=1 probe の liveness cap 30 秒を trace-enabled correctness へそのまま一般化せず、2 倍に固定する設計値です。実測値とは主張しません。

この allocation を数えないまま `8+2+13+3=26` とすると、「総ポイント上限」が supporting allocation を隠すため、`a10` では main reserve を 3 から 2 へ減らして算入します。

## `a03` — `load1` を gate にしない理由

1 分 load average を、前の run が作った寄与 `ΔL` の減衰として近似すると、

\[
\Delta L(t)=\Delta L(0)e^{-t/60}
\]

です。

| 待機 | 前 run の寄与の残存率 |
|---:|---:|
| 30 秒 | `e^-0.5 = 0.606530660` |
| 60 秒 | `e^-1 = 0.367879441` |

したがって 30 秒待っても約 60.7%、60 秒でも約 36.8% が指標内に残ります。J=1 screen は待機なしで `pre_load1` が 13.47 から 40.18 へ上がっています。[limited-screen.tsv L8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/limited-screen.tsv:8) これは待機後の値ではなく、30/60 秒の十分性を実測した証拠ではありません。

`load1` を絶対閾値にすると、過去 1 分の自分自身の schedule を「現在の外乱」と誤認します。逆に広い閾値を置けば恒真 gate になります。そのため、`load1` は診断として保存するだけにします。

採用する `cpu_busy_core_equivalents` は直前 10 秒だけを見るため、30/60 秒待機と履歴窓が競合しません。範囲 `[0,1]` は「48 core のうち平均 1 core 相当以下」という設計上の閾値です。十分性の実測値ではなく、pilot 後にも変更しない fail-closed な規範値です。

## `a08` — arm と compile identity の固定

### source identity

| arm | base source | patch / macro |
|---|---|---|
| `stock` | CCBench `d706650cdb31e442bef45b9b4216951d4fb40969` | patch なし、mode macro なし |
| `mode1` | 同じ base | patch SHA-256 `3b9cdf1635c2afdbfa24af2b5e84e841773144147fe0d00c8b5e794817051951`、`-DIZANAGI_T139_PC_MODE1=1` |
| `modeX` | 同じ base | 同じ patch、`-DIZANAGI_T139_PC_MODEX=1` |

依存 pin は receipt の gflags、glog、masstree、mimalloc、googletest を exact に使います。[submission receipt L30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-05_t139-alt-x-probe/submission-receipt.md:30)

### configure argv

全 arm 共通:

```text
-DCMAKE_BUILD_TYPE=Release
-DENABLE_SANITIZER=OFF
-DCCBENCH_BACK_OFF=0
-DCCBENCH_BACKOFF_FIXED=-1
-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
-DCCBENCH_NO_WAIT_OF_TICTOC=0
-DCCBENCH_WAL=0
-DCCBENCH_CCACHE=OFF
-DCMAKE_EXPORT_COMPILE_COMMANDS=ON
-DCMAKE_C_COMPILER_LAUNCHER=
-DCMAKE_CXX_COMPILER_LAUNCHER=
-DRULE_LAUNCH_COMPILE=
-DCMAKE_TOOLCHAIN_FILE=
-DFETCHCONTENT_SOURCE_DIR_MASSTREE=<pinned masstree>
-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=<pinned mimalloc>
-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=<pinned googletest>
-DCMAKE_C_COMPILER=/bin/gcc
-DCMAKE_CXX_COMPILER=/bin/g++
```

performance build:

```text
-DCCBENCH_TRACE=0
-DCCBENCH_ADD_ANALYSIS=0
```

correctness/liveness build:

```text
-DCCBENCH_TRACE=1
-DCCBENCH_ADD_ANALYSIS=1
```

実 `compile_commands.json` から `transaction.cc`、`result.cc`、`util.cc` の argv を抽出し、`/scr` の一時 root を `{SOURCE}`, `{MASSTREE}`, `{MIMALLOC}`, `{GFLAGS}`, `{GLOG}` token に正規化した UTF-8 JSON の SHA-256 を `compile.identity_sha256` とします。J=1 の performance argv が `TRACE=0`、`ADD_ANALYSIS=0` だったことは raw compile summary で確認できます。[compile-argv.tsv L2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/compile-argv.tsv:2)

J=1 の liveness build は `TRACE=0, ADD_ANALYSIS=1` であり、今回 core が要求する trace-enabled correctness の代用にはしません。[compile-argv.tsv L11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/compile-argv.tsv:11)

## `a09` — 許容 schedule 集合と一意選択

arm 記号を `S=stock`, `D=mode1`, `X=modeX` とし、

```text
Π = {SDX, SXD, DSX, DXS, XSD, XDS}
```

とします。

cluster slot `j` の許容 schedule は次をすべて満たすものです。

1. workload ごとに 6 block を持つ。
2. 各 workload の block は `Π` の各要素をちょうど 1 回使う。
3. 一つの workload の 6 block を連続実行し、その後もう一方を 6 block実行する。
4. 任意の slot prefix `1..r` で、W1-first と W2-first の本数差が 1 以下。
5. replacement attempt は新しい slot を作らず、置換対象 slot と同じ schedule を使う。

seed は次の ASCII bytes、末尾 newline なし、の SHA-256 で導出した値です。

```text
t139-mainrun-a09-v1|ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

```text
7df15572d2d88f172bc69bea9bc2dc53eddcbef41211d8ece7b0a592e5b2615d
```

選択手続きは次です。

- seed の整数値は奇数なので、奇数 slot は W2-first、偶数 slot は W1-first。
- workload `w` の 6 block は、各 `p∈Π` に対して

```text
SHA256("t139-a09-v1|" || seed || "|" || decimal(j) || "|" || w || "|" || p)
```

を計算し、`(digest,p)` 昇順に並べる。
- workload group 内はその順序、group 間は上記 first-workload 規則に従う。
- collision 時は `p` の ASCII 昇順で tie-break する。

この手続きは seed と slot だけで一意です。J が 13 未満でも prefix balance が崩れず、runtime RNG を必要としません。

## `a10` — `J` の導出手続き

### 26 割当ての内訳

```text
verification allocation             1
pilot valid cluster slots            8
pilot pre-performance reserves       2
main valid cluster ceiling          13
main pre-performance reserves        2
                                      --
total                                26
```

verification allocation に reserve は置きません。そこで correctness anomaly が出れば終端 reject、開始前 infra failure で完了できなければ `design_not_feasible` です。

main の `J<13` なら未使用 main slot を reserve、追加反復、別候補へ振り替えません。

### pilot 母数

各 valid pilot cluster について

\[
Y_j=(N_{W1,j},H_{W1,j},G_{W1,j},
     N_{W2,j},H_{W2,j},G_{W2,j})^\top \in \mathbb{R}^6
\]

を作ります。`n_p=8`, `p=6`, `ν=7` とし、標本平均を \(\bar Y\)、不偏標本共分散を \(S_p\) とします。`S_p` が正定値でなければ `design_not_feasible` です。

planning model は cluster vector の iid 6 次元正規分布

\[
Y_j\sim N_6(\mu,\Sigma)
\]

です。これは分布近似として事前固定するもので、J=1 が正規性を実証したとは主張しません。

### 共同 95% 信頼集合

平均について 97.5% Hotelling region:

\[
M=\left\{\mu:
8(\bar Y-\mu)^\top S_p^{-1}(\bar Y-\mu)
\le
\frac{6(8-1)}{8-6}F_{6,2,0.975}
\right\}.
\]

共分散について、\(W\sim Wishart_6(I,7)\) とし、

\[
\ell=Q_{0.0125}[\lambda_{\min}(W)],
\qquad
u=Q_{0.9875}[\lambda_{\max}(W)]
\]

を固定します。

\[
V=\left\{\Sigma:
\frac{7}{u}S_p\preceq\Sigma\preceq\frac{7}{\ell}S_p
\right\}.
\]

\[
\Theta=M\times V.
\]

平均 region の失敗確率 0.025 と covariance region の失敗確率最大 0.025 を Bonferroni で束ねるため、\(\Theta\) の共同被覆は少なくとも 95% です。

### `d=1` gate

\[
d^-
=
\inf_{(\mu,\Sigma)\in\Theta}
\min_{k=1,\dots,6}\frac{\mu_k}{\sqrt{\Sigma_{kk}}}.
\]

`d^- < 1.0` なら、効果量を引き下げず `design_not_feasible` とします。

### 最悪 power

候補 `J∈{4,…,13}` ごとに、

\[
\pi_J(\mu,\Sigma)
=
P_{\mu,\Sigma}\{
P_{W1}\land P_{W2}
\}
\]

を、`a11` の実際の sample covariance と q を使う将来標本の確率として定義します。

\[
L_J=\inf_{(\mu,\Sigma)\in\Theta}\pi_J(\mu,\Sigma).
\]

数値評価は次の fail-closed 契約にします。

- \(\Theta\) を mean-ellipsoid 座標と Cholesky 座標で compact parameterize する。
- outward-rounded interval arithmetic による lexicographic branch-and-bound を使う。
- probability integral の絶対誤差を `1e-4` 以下、global infimum の上下 gap を `1e-3` 以下にする。
- 下側 certified bound だけを採用する。
- 収束しない、または境界 `0.80` を下側から証明できない J は不適格。

選択値は

\[
J=\min\{j\in\{4,\dots,13\}:L_j\ge0.80\}.
\]

同じ \(\Theta\) を全候補 J に使うので、「真の母数が \(\Theta\) に入る」という一つの 95% event 上で全 \(L_J\) が同時に成立します。J ごとの pointwise 95%/99% 下限を並べて最小値を選ぶ手続きではありません。

該当 J が無ければ、`J_max` を増やさず `design_not_feasible`。新しい pilot、再設計、`d<1`、同じ alpha の再利用はせず、全 attempt を保持した新 study・新 alpha ordinal だけが再開経路です。[core §6 L189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:189)

## `a11` — `C_w` と `q`

### P2 の検算

P2 の 3 次元 Hotelling 式

\[
q^2=\frac{3(J-1)}{J-3}F_{3,J-3,1-\alpha}
\]

は、`p=3`、不偏共分散、`J>3` の多変量正規モデルに対して正しい有限標本補正です。また、

\[
\inf_{C_w}c^\top\mu
=
c^\top\hat\mu-q\sqrt{c^\top S c/J}
\]

および core の Fieller `A/B/C` と整合します。

ただし、3D 楕円は primary が使わない全線形方向と H の上側まで同時に覆い、必要以上に大きい q を課します。そのため正しいものの採用しません。

### 採用する region

\(D=N+G\) とし、\((N,D)\) の標本平均と 2×2 共分散を \(\hat v,S_{ND}\) とします。

\[
E_{ND}(q)
=
\left\{
v:
J(\hat v-v)^\top S_{ND}^{-1}(\hat v-v)\le q^2
\right\}.
\]

H は片側 region:

\[
E_H(q)
=
\left[
\bar H-q\sqrt{s_{HH}/J},\ \infty
\right).
\]

\[
C_w(q)=
\{(N,H,G):(N,N+G)\in E_{ND}(q),\ H\in E_H(q)\}.
\]

共通 q は、次を満たす最小の \(q\ge0\) とします。

\[
\begin{aligned}
&
1-F_{2,J-2}\left(
q^2\frac{J-2}{2(J-1)}
\right)
\\
&\quad+
1-T_{J-1}(q)
\le \alpha_k .
\end{aligned}
\]

第1項が 2D Hotelling region の失敗確率、第2項が H の片側失敗確率です。両者の依存性にかかわらず union bound で \(C_w\) の被覆を少なくとも \(1-\alpha_k\) にします。

この region の `(N,D)` projection がそのまま Fieller region なので、

\[
A=\bar D^2-q^2s_{DD}/J,\quad
B=\bar N\bar D-q^2s_{ND}/J,\quad
C=\bar N^2-q^2s_{NN}/J
\]

を変更しません。`N>0` と `G=D−N>0` の lower bound も同じ楕円・同じ q から出ます。

studentized maximum modulus を pilot 相関から較正する案は、q を pilot raw に依存させる経路を開きます。3 本の marginal Bonferroni interval だけを使う案は、ratio projection が上記 Fieller 二次式になりません。したがって採りません。

### workload 間の IUT

workload \(w\) の null は、

\[
H_{0,w}=\{N_w\le0\}\cup\{H_w\le0\}\cup\{G_w\le0\}.
\]

真値が \(C_w\) 内にあり、null 成分が一つでも存在すれば、3 lower bound の連言は成立しません。よって workload test の size は最大 \(\alpha_k\) です。

global null は `H0,W1 OR H0,W2` です。global pass は、null である workload の pass event の部分集合なので size は最大 \(\alpha_k\)。したがって W1/W2 の間で `α/2` にする必要はありません。これは相関の有無によらない IUT の性質です。

## `a12` — weak-null simulation

### 固定入力と DGM

入力は request `892042` の `throughput.tsv` だけです。

```text
sha256 =
755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2
```

各 workload・rep `r=1..5` について、

\[
Z_{w,r}=(X-D_g,\ 0.8S-D_g,\ S-X)
\]

を作り、

\[
e_{w,r}=Z_{w,r}-\frac15\sum_{s=1}^5Z_{w,s}
\]

を empirical 3D residual support とします。

simulation 内の 1 cluster は、`a09` の 6 permutation block へ \(e_{w,r}\) を復元抽出で 6 回割り当て、その平均を cluster residual とします。各 simulated dataset はこれを J cluster 生成します。

J=1 screen は 5/6 permutation、無待機、非 qualification なので、これは cluster variance の実測や普遍的な帰無分布とは主張しません。既見 residual を使った事前固定 stress model です。

### 乱数・反復数

```text
B = 1,000,000 per (J, null component)
J = 4,...,13
null component = 6
total cells = 60
```

seed は次です。

```text
01dad84c523b0a476655b91979c91d7174e40bb5a27757ada312abf2fe158ed2
```

これは、末尾 newline なしの

```text
t139-mainrun-a12-v1|ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

の SHA-256 です。

乱数 stream は `SHA256(seed || domain || uint64_be(counter))` の counter mode とし、5 で割る際は modulo bias を避ける rejection sampling を使います。ライブラリ固有 PRNG へ依存しません。

### 判定規則

各 weak-null face では対象成分の母平均を 0 に置き、他の primary 成分を無限大とみなした上限事象、すなわち「対象成分の lower bound が 0 を超えるか」だけを数えます。これは full conjunction の false-pass 確率の上界です。

false-pass 件数を \(x_{Jk}\) とし、familywise Monte Carlo error を `δ_MC=0.001` とします。各 60 セルについて one-sided Clopper–Pearson upper bound

\[
U_{Jk}
=
Beta^{-1}
\left(
1-\frac{0.001}{60};
x_{Jk}+1,\ B-x_{Jk}
\right)
\]

を計算します。`x=B` なら `U=1`。

```text
pass ⇔ 全 60 セルで U_Jk ≤ α1=0.025
```

一つでも超える、simulation が未完了、入力 digest 不一致、seed/replicate 不一致なら `design_not_feasible` です。q の増減、候補 J の部分的除外、pilot raw を使った再較正は行いません。

この simulation 自体は今回実行していないため、pass は主張しません。

## `a13` — primary alpha

逐語値は次です。

```yaml
familywise_alpha: 0.05
spending:
  domain: positive integers k >= 1
  alpha_k: 0.05 / (k * (k + 1))
current_study:
  k: 1
  alpha: 0.025
unspent_tail:
  reclaim: false
  redistribute_after_b01: false
```

\[
\sum_{k=1}^{\infty}\frac{0.05}{k(k+1)}
=
0.05
\]

なので候補数上限を必要としません。`b01` が有限 cap を置いても tail は捨て、既存候補へ戻しません。

本 study は `k=1` を A で固定します。追補 B の `b03` は正規の根と台帳を同定できますが、ordinal を変更できません。B が `k=1` を再現できなければ main admission を拒否し、`q` を別 alpha で再計算しません。

## erratum の文面案

配置先は、追補 A と同じ確定パッケージ内の独立文書、例えば

```text
output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md
```

とします。core 自体は編集しません。

```markdown
# [T-139] 凍結 core §15 exact-key 誤記の erratum

本 erratum の対象は次の exact core だけである。

- commit: `88d68f9127b31df5aafc3d59607896626a1652e8`
- path: `output/insights/2026-08-07_t139-mainrun-design/preregistration.md`
- SHA-256: `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`

対象 core §14 の追補 A 閉集合は `a01`〜`a13` の 13 field である。
したがって、§15「投入 gate」要件 5 にある `a01`〜`a12` は誤記であり、
`a01`〜`a13` に supersede する。

同じく、§15「通る正例」にある
「`a01`〜`a12` だけを設定しており」は誤記であり、
「`a01`〜`a13` だけを設定しており」に supersede する。

上記 2 箇所以外の core の bytes、文言、受理条件、閉集合、
投入順序、commit/blob 束縛を変更または supersede しない。
本 erratum はユーザー承認を canonical decision へ fold した commit 以後にのみ発効する。
```

将来 resolver は次の順で参照します。

1. core の path/commit/SHA-256 を解決する。
2. trusted errata registry を `(core.path, core.sha256)` exact key で引く。
3. erratum を承認した fold commit が `measurement_head` の祖先であることを検査する。
4. effective `addendum_a.fields` の expected set を `{a01,…,a13}` とする。
5. その集合で addendum の exact-key を検査する。

erratum は `document_kind=core_erratum` の別文書であり、`addendum_a.fields` の一部ではありません。したがって erratum 自身が 14 番目の field になることはありません。全文 grep で `aNN` を集める resolver は禁止し、文書型と `fields` object を分離します。

erratum の実 commit/digest は land 前には存在しないため本文へ自己記載せず、receipt の `preregistration.errata[]` に外から記録します。

## `record-items.md` への確定差分

現案は top-level 18 key と全 nested object の closed schema を宣言しています。[record-items L22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:22) したがって以下は実走時に自由追加する field ではなく、承認前に schema 案へ組み込むべき差分です。

| 現案の不足・誤り | 必要な確定差分 |
|---|---|
| `planned_execution.runs[]` を 1 allocation 6 件としている | 1 cluster を `12 blocks / 36 performance runs` に訂正。各 run に `cluster_slot, workload, block_index, permutation, planned_ordinal, position, predecessor_arm, arm` を必須化。 |
| W1/W2 argv の置き場がない | `planned_execution.workloads.{W1,W2}.driver_argv[]` を exact vector として持ち、`actual_runs[].argv_sha256` で結ぶ。 |
| schedule seed と生成版がない | `planned_execution` 内に `schedule_seed`, `schedule_algorithm="t139-a09-v1"`, `cluster_slots[]`, `schedule_sha256` を置く。replacement は同じ slot を参照する。 |
| 待機の raw 記録がない | 各 planned/actual run に `preceding_wait {kind, required_s, monotonic_start_ns, monotonic_end_ns}`。producer は `satisfied` boolean を書かず、validator が秒数を再計算する。 |
| `a03` の raw counter がない | `actual_runs[].environment_observation` に `/proc/stat` の before/after counter、monotonic timestamps、diagnostic `load1` を置く。`recovered` field は禁止する。 |
| phase 別実時間と `a01/a06` walltime を再計算できない | `allocations[]` に `requested_walltime_s`, `internal_deadline_s`, `performance_started_at`。`admission_telemetry[]` に phase start/end と raw evidence pointer。 |
| `arms.*.compile` が抽象的 | `source {repo_commit, ccbench_pin, base_tree_sha, patch_path, patch_sha}`, `compiler {path, version, sha256}`, `configure_argv[]`, `translation_units.*.normalized_argv[]`, `identity_sha256`, `trace_enabled`, `analysis_enabled` を exact nested key にする。 |
| binary hash が run と結ばれていない | `arms.*.binary {path,size,sha256}` と `actual_runs[].binary_sha256` を必須化。pre/post hash evidence pointer も保存する。 |
| correctness build の分離はあるが exact compile 契約が不足 | `correctness_evidence[].build.compile` に上記と同型の identity、`TRACE=1`, `ADD_ANALYSIS=1` を持たせる。performance binary との SHA 非同一、allocation 非同一を維持する。 |
| reason code が probe/core の名前と不一致 | enum を `pre_performance_infra_failure`, `post_performance_failure`, `correctness_anomaly`, `completed` に揃える。`performance_started_at` との条件制約を付ける。 |
| planned↔actual を常に双射としている | `completed` attempt だけ 36 run の完全双射。failure attempt は planned schedule に対する actual run の厳密 prefix と failure evidence を要求する。欠けた run の捏造を禁じる。 |
| erratum の effective binding が記録できない | 既存 top-level `preregistration` の内部に exact `errata[] {commit,path,sha256,approval_fold_commit}` を追加する。top-level key は増やさない。 |
| `a12` の admission 証拠がない | `admission_telemetry[]` に calibration receipt の `path,size,sha256,B,seed,input_sha256,result` raw pointer を置く。producer の `pass` 申告を権威にせず、validator が transcript を再計算する。 |

特に、現案の無条件な planned↔actual 双射は post-performance failure の正当な prefix を拒否する一方、欠けた run の捏造を促します。`completed` と failure の条件分岐を schema に入れる必要があります。

## 親の provisional 裁定 P1〜P5

| provisional | 採否 | 理由 |
|---|---|---|
| P1: 36 performance run | **採用** | 2 workload × 6 permutation block × 3 arm。core の位置・直前 arm 均衡と一致する。 |
| P2: 3D Hotelling | **式は正しいが不採用** | 有効な構成だが不要な方向まで覆う。Fieller projection を保つ `2D Hotelling (N,D) + one-sided H` を共通 q で採る。 |
| P3: `b01` 非依存の無限 spending | **採用** | `0.05/[k(k+1)]` とし、本 study は `0.025`。cap 後の tail は再配分しない。 |
| P4: simulation は pilot 前、失敗時 DNF | **採用** | q は analytic function として先に固定し、simulation は pass/fail のみ。 |
| P5: allocation 外 build が主経路 | **修正採用** | trace-enabled correctness を別 allocation に置き、その 1 本を 26 本へ算入する。このため main reserve は 3 ではなく 2。予備 walltime は 90 分。 |

## 想定される反論と応答

1. **「30/60 秒待てば load1 は戻るので、そのまま使えばよい」**

   30 秒後も直前寄与の約 60.7%、60 秒後も約 36.8% が残ります。これは現在の競合ではなく自分の履歴を測るため、gate には不向きです。load1 は診断として残し、直前 10 秒の CPU busy を判定に使います。

2. **「3D Hotelling は正しいのだから最も安全だ」**

   正しい一方、H の上側や `(N,D)` ratio に不要な方向まで覆います。採用案も有限標本で少なくとも `1−α` を覆い、Fieller は同じ `(N,D)` region の projection です。凍結 core の同一構成要件を保ったまま狭くできます。

3. **「W1/W2 の 2 workload だから alpha を半分ずつにすべきだ」**

   primary は conjunction です。global null では少なくとも一つの workload が null であり、global pass はその workload の false pass の部分集合です。したがって size は最大 `α_k` で、和にはなりません。

4. **「1 cluster は全 6 順列だから 6 run である」**

   順列一つは 3 arm の 3 run です。6 run では各順列を実行できません。正しくは workload ごと18、合計36です。

5. **「a12 で empirical error が大きければ q を少し上げればよい」**

   それは simulation 結果による critical value 選択です。本案では q は `a11+a13` の既知関数で固定し、simulation は admission の pass/fail にしか使いません。失敗は `design_not_feasible` です。

6. **「verification allocation は統計 cluster ではないので 26 本に数えなくてよい」**

   core の語は「総ポイント上限 26 割当て相当」です。統計標本でないことは費用ゼロを意味しません。数えない案は supporting cost を閉集合の外へ隠すため、1 本として算入します。

7. **「erratum を addendum metadata に埋めれば簡単だ」**

   naive な exact-key validator では余剰 field になります。erratum は target core digest に束縛した別 document kind とし、resolver が addendum の `fields` を解析する前に effective key set を解決する必要があります。

## 静的確認の範囲

実施したのは、指定資料の読取り、core SHA-256 と fold commit blob の一致、seed の SHA-256 導出、時間総和、load1 の指数減衰、schedule の組合せ、Hotelling/Fieller/IUT の式の静的検算だけです。

pytest、build、Pegasus 実走、power solver、`a12` simulation は実行していません。したがって、テスト・build・simulation の成功や緑は一切主張しません。

## 総括

- 13 field のうち、逐語案として埋まったものは **13 件**、埋まらなかったものは **0 件**です。ただし `a12` の実行結果と未来の binary SHA-256 は、値ではなく pilot 前の固定手続きとして閉じています。
- P1〜P5 は、**P1 採用、P2 は式のみ肯定して不採用、P3 採用、P4 採用、P5 修正採用**です。
- ユーザー裁定が必要なのは、(1) `a03` の `[0,1 core-equivalent]`、(2) `a10` の共同 95% assurance と verification を含む `1+8+2+13+2` 配分、(3) `a11` の 2D+1 region、(4) `a13` の `.05/[k(k+1)]` spending、(5) erratum の resolver 参照形式、(6) 上記 nested field を組み込んだ record-items 確定版です。