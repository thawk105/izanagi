### 所見 1 — 13 field は揃うが、erratum が無検査の第 3 権威になる

区分: blocker

根拠 ([s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:16), [s2-plan.md:529](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:529), [preregistration.md:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:313), [preregistration.md:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:375), [D234:11026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:11026)): 表の行は `a01`〜`a13` のちょうど 13 件で、行数上の欠落・余剰はない。しかし actual document grammar は示されず、`core_ref` と `fields` の envelope exact schema が未定義である。さらに現行 resolver 署名は core/A/B しか受けず、計画が追加する `trusted errata registry` は署名外である。提案本文にも、説明でいう `document_kind=core_erratum` の機械可読 field は存在しない。

反例または検算:

- resolver が `fields` だけを読むなら erratum は見えず、core §15 の `a01`〜`a12` が残る。
- 文書全体を field とみなすなら、`core_ref`、見出し、説明、erratum 参照が余剰になる。
- registry を暗黙に読むなら、commit/blob 束縛されていない第 3 文書が受理集合を書き換える。
- `record-items` の現行 `preregistration` は `{core,addendum_a,addendum_b,fold_commit}` だけを示す一方、計画は `errata[]` を追加する ([record-items.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:38), [s2-plan.md:590](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:590))。

提案: ユーザー裁定で、(1) A envelope の exact keys、(2) erratum の exact schema、(3) 承認済み erratum blob の同定根、(4) `PreregBinding` と receipt への erratum 三つ組、(5) supersede 可能箇所を §15 の 2 箇所だけに限定する検査、を一体で定める。一般 errata registry ではなく、この core digest に対する one-off の exact replacement を推奨する。

### 所見 2 — `a03` は形式上恒真ではないが、正常割当てを通す証拠が一件もない

区分: blocker

根拠 ([s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:24), [s2-plan.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:94), [preregistration.md:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:347), [limited-screen.tsv:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/limited-screen.tsv:2)): `cpu_busy_core_equivalents` は変動量、`[0,1]` は有限で理論的 support `[0,48]` の真部分集合なので、禁止された定数・全域範囲・範囲なしには該当しない。

反例または検算:

- 36 行の実測は `load1` であり、新指標の `/proc/stat` counter ではない。したがって新範囲に「probe 実測が何件入るか」は計算不能である。
- full table の `pre_load1` / `post_load1` はともに最小 3.29、最大 40.18。`13.47` は liveness 6 本終了時の値にすぎず、親 brief の「3.29→13.47」は 36 行全体の要約ではない ([limited-screen.tsv:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/limited-screen.tsv:7), [limited-screen.tsv:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/limited-screen.tsv:37))。
- 仮に `[0,1]` を load1 に適用すれば 36/36 が不成立で、恒偽 gate になる。
- load1 の前 run 寄与は 30 秒後 60.653%、60 秒後 36.788% 残る。最後の 10 秒だけを測る発想はこの平滑問題を避けるが、その 10 秒指標自体の実測がない。
- 「10.000 秒」は許容誤差がなく、逐語なら通常の `sleep` で一致不能になりうる。`Δtotal` の構成列も未指定で、Linux の `guest/guest_nice` を重複加算する実装差が残る。

提案: A 凍結前に、30/60 秒待機の末尾 10 秒について同じ `/proc/stat` raw counter を採る非 study engineering probe を別 wave で行うか、「未実測の fail-closed 規範値を受け入れる」ことをユーザー裁定に戻す。併せて counter 列、guest 除外、clock、許容観測時間幅を byte-level に固定する。

### 所見 3 — `a04` の本文写像は正しいが、receipt は同じ境界を保存できていない

区分: major

根拠 ([s2-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:25), [t139_positive_control_probe.pbs:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.pbs:20), [t139_positive_control_probe.sh:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:486), [t139_positive_control_probe.sh:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:511)): 計画は `.pbs` と同じ `performance_started` durable marker の有無で分けている。待機後の `a03` 失敗も、最初の marker 後なら `post_performance_failure` となる。新しい §9 分類は作っておらず、この本文部分は適合する。

反例または検算: schema 差分は `performance_started_at` という値を置くだけで、marker の raw bytes を必須化していない ([s2-plan.md:584](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:584))。marker 消失・collector 不全時に、実 run が存在しても `null` と書けば開始前へ写せる。現行 schema の enum も `pre_measurement_infrastructure` / `post_measurement_failure` と別名である ([record-items.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:81))。

提案: create-only marker の path/size/SHA-256/raw pointer を attempt に持たせ、validator が読み直す。marker 不在でも performance run の raw 痕跡が一つでもあれば、保守的に post 側へ倒す。

### 所見 4 — `a01` の秒数は収まるが、cap を hard deadline にする契約がない

区分: minor

根拠 ([s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:55), [README.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-05_t139-alt-x-probe/README.md:106), [t139_positive_control_probe.pbs:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.pbs:4))。

反例または検算:

- performance cluster: `180 + 36×15 + 24×30 + 11×60 + 180 + 120 = 2400` 秒。contingency 900 で deadline 3300、scheduler safety 300 で walltime 3600。
- verification allocation: `180 + 1500 + 6×60 + 180 + 120 = 2340` 秒。contingency 960、safety 300。
- fallback: 非余裕 3300、deadline 4800、walltime 5400。
- よって probe の `3817 > 3300` 事故は、この直列和には再現しない。900 秒の内部余裕と 300 秒の scheduler safety は数値上は余裕と呼べる。
- queue 待ちは allocation 実行前なので `elapstim_req` の直列和には入れない。calendar time / 混雑リスクとしては別管理になる。
- ただし先例の `timeout --foreground` は `--kill-after` を持たず、TERM を無視する子を cap 秒で必ず止める保証がない ([t139_positive_control_probe.sh:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:22))。

提案: `serial hard cap ≤ internal_deadline`、TERM grace、SIGKILL、cleanup の秒数帰属を A に固定する。

### 所見 5 — `a05` の hash は「実際に exec された bytes」を独立再計算できない

区分: blocker

根拠 ([s2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:26), [s2-plan.md:585](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:585), [preregistration.md:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:290)): 計画は staged path の pre/post hash と `actual_runs[].binary_sha256` を持つが、durable な実行ファイル bytes または content-addressed pointer を要求していない。probe receipt にも executable 自体は残っていない。

反例または検算: B1 を最初に hashし、run 時だけ B2 へ差し替え、最後に B1へ戻せば pre/post hash と receipt は整合する。`actual_runs[].binary_sha256` は producer の申告であり、独立な実行証拠ではない。`/scr` の staged path が消えれば、後段 validator は hash を再計算できない。

提案:

- allocation 外 build artifact と staged artifact の両方を immutable path/size/SHA-256 で保存する。
- 実行は immutable fd/content-addressed copy に束縛し、各 run の exec witness を残す。
- 全 translation unit の compile manifest、link argv、compiler executable hash、動的 library/ELF interpreter、source tree/patch/dependency witnessを保存する。
- probe の [compile-argv.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/compile-argv.tsv:1)、[nm-witness.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/nm-witness.tsv:1)、[dependency-witness.tsv](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/dependency-witness.tsv:1) と raw 出力を最低線とする。

### 所見 6 — `a07` は明示 argv だけ一致し、effective workload は固定できていない

区分: blocker

根拠 ([s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:28), [t139_positive_control_probe.sh:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:454), [W1 log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/run-1-W1-stock-r1.log:1), [W2 log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/run-16-W2-stock-r1.log:1)): W1/W2 の明示 argv は shell L454–457 と逐語一致する。しかし全 30 log では `clocks_per_us=2100`, `epoch_time=40`, `ycsb_rratio=50` が共通で、W1 にも `rratio=50` が実在する。W2 の `ycsb_rmw=0` も既定値である。

反例または検算: 同じ明示 argv のまま CCBench default を変更すれば、A は一致するのに effective workload が変わる。W1 の read ratio を `not_applicable` と書くだけでは、実 flag 50を再現できない。

`#FLAGS_` 行が保証するのは、実行 process が報告した一部 gflags の effective 値である。caller argv、default の由来、source identity は保証しない。`ShowOptParameters()` は `KEY_SIZE=8`, `VAL_SIZE=4`, `MASSTREE_USE=1` 等を示すが、TRACE、mode macro、compiler、source、依存は保証しない。

提案: 省略 flag も含む expected effective flag map を A に固定し、可能なら全 flag を明示 argv 化する。actual argv の canonical bytesと run log の path/size/hash を receipt に持ち、validator が `#FLAGS_` / `ShowOptParameters()` を exact map として照合する。

### 所見 7 — 規律 1 の配置は正しいが、`a08` が build identity を事前固定していない

区分: blocker

根拠 ([CLAUDE.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/CLAUDE.md:58), [s2-plan.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:29), [s2-plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:152), [s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:166)): performance 3 arm を `TRACE=0/ADD_ANALYSIS=0`、correctness/liveness を別 allocation・別 build/run の `TRACE=1/ADD_ANALYSIS=1` とする配置は規律 1 と両立する。

反例または検算:

- J=1 probe の liveness は実際には `TRACE=0/ADD_ANALYSIS=1` であり、未来の trace-enabled build の witness ではない。計画自身もこれを認める ([s2-plan.md:168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:168))。
- `identity_sha256` は build 後に得る値で、A に expected digest/template が固定されていない。
- 対象は `transaction.cc/result.cc/util.cc` の 3 TU だけで、他 TU、link argv、runtime dependency の変化を許す。
- compiler SHA-256 は record 差分案にしか現れず、`a08` 本文値は path/version に留まる。

提案: performance / correctness を独立した exact build object とし、全 compile/link manifest、expected macro map、compiler bytes、依存 snapshot、binary artifact を事前仕様へ入れる。trace-enabled と trace-disabled の別 allocation ID・別 run ID も validator 条件にする。

### 所見 8 — `a09` の均衡は構成できるが、hash preimage が実装依存である

区分: major

根拠 ([s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:170), [s2-plan.md:198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s2-plan.md:198)): SHA-256 sort は runtime RNG を使わず、奇数 slot=W2-first、偶数 slot=W1-first とするため、prefix `1..r` の差は常に `ceil(r/2)-floor(r/2)≤1` になる。

反例または検算: seed を ASCII lowercase hex 64 byte、`j` を先頭ゼロなし十進 ASCII と仮定した構成例は次のとおりで、全 permutation を一度ずつ使える。

```text
slot 1: W2-first
  W1: DSX XSD XDS SXD DXS SDX
  W2: DXS XSD SDX SXD DSX XDS
slot 2: W1-first
  W1: SXD SDX DXS XSD XDS DSX
  W2: SDX XDS DSX SXD XSD DXS
```

しかし `seed` が ASCII hex か32 raw bytesか、`decimal(j)` の符号・先頭ゼロ、文字 encoding、digest sort が raw bytesかhex文字列かが未指定である。異なる実装は別 schedule を生成する。

提案: preimage の byte grammar を逐語固定する。`J_max=13` なので、slot 1〜13 の expected schedule と canonical `schedule_sha256` を A に併記すれば実装差をほぼ消せる。

### 所見 9 — 受領証 closed schema は未完成で、6 run 記述は core と両立しない

区分: blocker

根拠 ([record-items.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:22), [record-items.md:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:32), [record-items.md:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-producer-adjudication/record-items.md:76), [preregistration.md:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:200)): `record-items.md` は全 nested object へ `additionalProperties:false` を宣言する一方、nested exact keys/types を完全列挙していない。さらに「1 allocation あたり6件」は誤りである。

反例または検算: 1 workload は `6 permutation block × 3 arm = 18 run`、2 workload で36 run。6件では全順列の1/6しか表せず、正常 cluster を拒否するか、欠落した30 runを見えなくする。

現行18 top-level keyの内側に置けるが、nested schema にまだ存在しない必須情報は少なくとも次である。

- `a01/a06`: allocation role、main/fallback の投入前選択、requested walltime、absolute/internal deadline、phase cap/start/end、verification allocation との対応。
- `a02`: planned/actual wait の kind、required seconds、monotonic raw timestamps。
- `a03`: `/proc/stat` の列別 before/after counter、clock、実際の観測時間、load1診断。
- `a04`: durable performance marker bytes、failure event、markerとの整合制約。
- `a05`: allocation外 artifact、staged artifact、exec witness、pre/post hash の独立 pointer。
- `a07`: planned/actual argv の canonical bytes、effective flag map、run log pointer。
- `a08`: performance/trace build の全 compile/link/source/compiler/dependency identity。
- `a09`: seed encoding、algorithm version、cluster slot、canonical schedule hash、replacementの同一slot制約。

提案: top-level 18 key は維持し、承認前に nested schema を完全な一枚へ改訂する。今、提案段階で schema を直すのは余剰違反ではない。一方、凍結後・実走時に未知 nested field を自由追加すること、または top-level 19個目を足すことは余剰 field 違反である。

### 所見 10 — docs-only scope は正当だが、「追補 A 確定済み」という状態名は不正確

区分: major

根拠 ([s1-brief.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s1-brief.md:15), [s1-brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-addendum-a/s1-brief.md:17), [D234:11062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:11062), [D234:11079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/decisions.md:11079), [DW-G04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/docs/dev-wave/core.md:60)): D234 は gate の機械配線を後続 producer wave に明示的に残すので、コードを足さないこと自体は違反ではない。DW-G04 上は設計メモ／裁定パッケージの状態である。

反例または検算: 台帳へ無限定に「追補 A 確定済み」とだけ書くと、resolver、submit gate、receipt、validator が一つも存在しないのに pilot admission が可能になったように読める。さらに本 brief はユーザー承認前に凍結しないと明記している。

提案: 状態を次の3段階に分ける裁定パッケージを返す。

1. `追補A案・erratum案・schema案＝承認待ち`
2. land/fold 後も `文書発効済み／機械gate未実装／pilot投入不可`
3. producer/resolver/validator/consumer の実装・受入後だけ `投入gate有効`

## 総括

- blocker: **6件**
- 判定: **NO-GO**
- ユーザー裁定が要る点:

  1. erratum を exact blob に束縛した one-off 入力として D234/resolver に組み込むか、新しい core に戻すか。
  2. `a03=[0,1]` を未実測の fail-closed 規範値として承認するか、同一指標の事前 engineering probe を別 wave で要求するか。
  3. 台帳上の状態名を「文書発効」と「機械 gate 有効」に分離するか。
  4. 最終的な追補 A・erratum・18-key nested schema の同時承認。

`a01` の秒数、`a04` の本文上の開始境界、`a09` の交互 workload 順は静的検算上成立した。ただしテスト・build・Pegasus 実走は行っておらず、緑は主張しない。