## 再計算の結果

### 格子・符号化

規則は[本体 §4.1（135行）](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:135)、codec は[実装 64–79行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:64)、C++ 分岐は[patch 69–70行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/patches/silo-backoff-fixed.patch:69)と照合した。

| k | 丸め前 | 再計算値 | raw | decode | 商 | C++ 実現値 | 本体 |
|---:|---:|---:|---:|---:|---:|---:|---|
| 6 | 1249.875000 | 1250 | 3250 | 1250 | 3 | 1250 | 一致 |
| 5 | 1767.590176 | 1768 | 3768 | 1768 | 3 | 1768 | 一致 |
| 4 | 2499.750000 | 2500 | 4500 | 2500 | 4 | 2500 | 一致 |
| 3 | 3535.180353 | 3535 | 5535 | 3535 | 5 | 3535 | 一致 |
| 2 | 4999.500000 | 5000 | 7000 | 5000 | 7 | 5000 | 一致 |
| 1 | 7070.360705 | 7070 | 9070 | 7070 | 9 | 7070 | 一致 |
| 0 | 9999.000000 | 9999 | 11999 | 9999 | 11 | 9999 | 一致 |
| 境界 | — | 1000 | 3000 | 1000 | 3 | 1000 | 一致 |

`k=2` が唯一のちょうど 0.5 で、ゼロから遠い側の 5000 になる。`formal_tail_values_us`、`analysis_values_us`、`encoded_static_points`、`binary_identity.physical_amounts_us` は[§5 の423–435行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:423)および604行と全点一致した。

全 raw は 3000 以上、商は 3/4/5/7/9/11 なので定数枝 `raw - 2000` を通る。decoder は raw 1000 と2999をともに拒否し、3000を1000へ戻した。したがって発行禁止域 `[1000,2999]` の主張も正しい。

### 測定順

昇順 `[1000,1250,1768,2500,3535,5000,7070,9999]` に指定 seed の `shuffle` を1回適用した。

| workload | 再計算した順序 | [本体 196–200行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:196) |
|---|---|---|
| write-heavy | 2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070 | 一致 |
| balanced | 1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999 | 一致 |
| read-heavy | 3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000 | 一致 |

### 区間の対数比

| 区間 | `log(right/left)` |
|---|---:|
| 1000→1250 | 0.223143551 |
| 1250→1768 | 0.346705413 |
| 1768→2500 | 0.346441768 |
| 2500→3535 | 0.346422567 |
| 3535→5000 | 0.346724613 |
| 5000→7070 | 0.346422567 |
| 7070→9999 | 0.346624608 |

境界参照の「0.2231」は正しい。一方、tail の実範囲は **0.3464226〜0.3467246** であり、[本体164行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:164)の「0.3465〜0.3467」は厳密には偽である。

### 検出力

探索の印字済み abort 率から得た最大 abort CV は balanced/9999 の `0.006151493748`。量子化値なので参考計算に限る。両端をこの CV、`n=5` とすると自由度は8。

| 多重度 | t 分位点 | 半オクターブ `U_flat` | 旧短区間 h≈0.1115 |
|---:|---:|---:|---:|
| 24 | 3.961773 | 3.036% | 9.134〜9.137% |
| 18 | 3.758586 | 2.882% | 8.686〜8.689% |

18比較では実 tail 6区間の `U_flat` は **2.8810〜2.8835%**。5%基準に届く。§6の「おおむね3%」「9%前後」は正しい。throughput の最大 CV `0.006508358` を誤用しても3.05%/9.17%だが、正式な `U_flat` に使うべきなのは abort CV である。[本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:232) [§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:676)

### 時間予算

探索3 job の scheduler 開始から最終 WAL commit までは balanced 407.9秒、read-heavy 413.0秒、write-heavy 411.0秒だった。5 genome から8 genomeへの実績比例は **652.7〜660.8秒、約11分/job** で、先例の実走11分とも一致する。[一次資料50–52行](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:50)

ただし formal は correctness を1 cellあたり5回要求する一方、現行 WAL は1 cellあたり `verify_done` 1件である。探索15 cellで観測した最長 verify 時間16.922秒を、追加4回×8 cellへ保守的に足しても、約1202秒、**20.0分/job**。`SWEEP_CAP_S=11700` 秒と PBS 18000秒に十分収まる。[投入 script 4–20行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh:4)

## 所見

### [real] [must-fix] `indeterminate` を含む aggregate verdict が排他的でない

根拠 — [§4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:275)とJSONの `allowed_aggregate_verdicts` は優先順位を定めていない。例えば各 workload に別領域の連続2飽和区間があり、同時に1区間だけ `indeterminate` なら、`saturated-in-all-workloads` と `indeterminate-in-region` の両条件が成立する。「indeterminate を含む workload が有効か」も未定義である。

成果物影響 — 同一の区間表から aggregate verdict が少なくとも2通り生成でき、受理集合と headline が変わる。

提案 — JSONで verdict の優先順位、または相互排他的な完全条件を固定する。特に `indeterminate` が workload 全体をマスクするのか、その区間だけをマスクするのかを明記する。

### [real] [must-fix] ゼロ境界とカウンタ定義域が total でない

根拠 — `qhat=log(m_i/m_prev)/h` なので、all-zero→positive は未定義だが、[§4.4 269–273行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:269)は単に「非単調として§7へ」とする。§7が invalid にするのは `qL>0` だけで、その `qL` 自体が計算不能である。また `(abort,commit)=(0,0)`、負数、有限だが0の throughput を拒否する条項がない。

成果物影響 — 同じ入力が invalid、計算例外、またはゼロ abort 特例のいずれにもなり得て、verdict が一意でない。

提案 — 各 counter を非負の exact integer、`abort+commit>0`、throughputを有限かつ正と固定し、all-zero→positive は `qL` を経ず直接 `invalid` とする。ゼロ特例と zero-dispersion 規則の適用順もJSONへ書く。

### [real] [must-fix] 必須契約違反の一部が失敗条件へ写像されていない

根拠 — observation provenance は[§4.8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:310)で必須だが、[JSONの失敗列挙](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:626)にはその欠落・不一致がない。同様に、seed/測定順、records/threads/extime、workload座標、物理値とraw/genomeの対応違反も明示的な invalid 条件に入っていない。

成果物影響 — 数値repだけ揃った、出所不明または誤った動作点の成果物に科学的 verdict を発行できてしまう。

提案 — 必須 provenance の欠落・不一致、全 execution literal、測定順、workload座標、label/physical/raw/genome対応の不一致を失敗条件へ追加する。

### [real] [must-fix] `analysis_input_contract` が正規化名と実在 source path を結んでいない

根拠 — [fields 506–519行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:506)のうち、現 report に直接あるのは主に `backoff_us` と `throughput_tps_reps`。現物では次の対応になる。

| spec 名 | 現物 |
|---|---|
| `abort_counts_reps` / `commit_counts_reps` | 不在。stdout key `abort_counts_` / `commit_counts_` はparserが知るだけ |
| `abort_rate_reps_recomputed` / `abort_rate_cv` | 不在 |
| `throughput_tps_cv` | 現 report は単に `cv` |
| `correctness_verify_records` | report fieldではなく、WALの `stage=verify_done`、`payload.certified` |
| `binary_sha256` | 不在。WALには `perf_bin_sha256` と `trace_bin_sha256` の2種 |
| `rep_index` | 現 report は `reps[].rep` |
| `source_run_kind` | 現 report はtop-level `run_kind` |

producerも `abort_rate_reps` と `throughput_tps_reps` だけを作る。[report構築 1149–1194行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1149)

成果物影響 — consumerが不存在 field を直接要求して全件拒否するか、`binary_sha256` にtrace側を選んで別のbinary受理集合を作り得る。

提案 — 各正規化 field に `source_stage`、`source_path`、変換規則を付ける。特に binary は `build_done.payload.perf_bin_sha256`、correctness は committed attemptに束縛された `verify_done.payload.certified` と逐語化する。

### [real] [nit] tail の対数比レンジが狭すぎる

根拠 — 実値は0.346422567〜0.346724613で、[§4.1の0.3465〜0.3467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:161)から上下にはみ出す。

成果物影響 — 格子、解析値、受理集合は変わらず、格子均一性を説明する参照値だけが変わる。

提案 — `0.34642〜0.34673`、または丸めて `0.3464〜0.3468` と直す。

### [real] [nit] 11分先例は formal の correctness 5反復と完全同型ではない

根拠 — 本体は性能・正しさ各5 repを要求するが、現行実装の採用条件は `state.committed_verify` の非空と全件certifiedであり、個数5を要求しない。[loader 1080–1086行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1080) 探索WALも1 cellにつきverify 1件である。

成果物影響 — capや格子は変わらないが、所要見積もりは約11分から、保守的には約20分/jobへ変わる。

提案 — 時間節に「11分は現行1 verify/cellの実績。formal 5反復を実測外挿しても約20分」と追記する。

### [refuted] [nit] 本体の3535/7070を親裁定の3536/7071へ戻すべきという懸念

根拠 — 親裁定は[33行および149–156行](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/adjudication.md:31)で3536/7071とするが、規則からは3535.180…→3535、7070.360…→7070である。本体側が正しい。

成果物影響 — 本体は変更不要。親 literal を適用すると格子、raw、3順列、6区間すべてが誤って変わる。

提案 — 親裁定を後続実装の数値 oracle にせず、本体の生成規則と再生成値を使う。

### [refuted] [nit] §5 JSONまたはmarker切り出しが壊れているという懸念

根拠 — exact marker は[327行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:327)と674行に各1件。範囲を切り出しcode fenceを除いて `jq -e` へ渡すと rc=0。JSON内部のmarker文字列は0件だった。

成果物影響 — spec bytesとparse受理結果の変更は不要。

提案 — なし。

### [refuted] [nit] `correctness_authority` が誤った場所を指すという懸念

根拠 — 現物の権威は admitted WAL の committed attemptに属する `verify_done.payload.certified` である。loaderもreplay後の `state.committed_verify` を検査する。[1023–1086行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1023) point側 `certified=false` を使わないという本体の指定は正しい。

成果物影響 — correctness authority と現行受理集合の変更は不要。

提案 — field-source mappingの明確化だけを上のmust-fixで行う。

### [refuted] [nit] 投入前条件が既に満たされているという懸念

根拠 — 現行 `RUN_KINDS` は既存3種だけで formal consumerはない。[81–84行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:81) counterはCCBenchが印字しparserも認識するが、report/WALへ保存されない。[benchparse 66–78行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/calibrator/benchparse.py:66) observation単位のprovenanceも要求6 field中 `source_measurement` 以外は未実装である。したがって[§8.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:715)の3条件はすべて未充足で、本体の現状記述は正しい。

成果物影響 — 現在はformal成果物を受理できないという記述の変更は不要。

提案 — なし。

### [refuted] [nit] §6の3%/9%概数が多重度18では崩れるという懸念

根拠 — 多重度変更で t は3.961773から3.758586へ下がり、`U_flat` は半オクターブ2.88%、短区間8.69%となる。いずれも通常の丸めで3%/9%である。

成果物影響 — 5%検出可能条件、格子、受理集合の変更は不要。

提案 — 必要なら参考値に「18比較、最大abort CV使用」と計算条件を添える。

### [refuted] [nit] `docs/README.md` の地図が本体の数値と矛盾するという懸念

根拠 — [地図29–33行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:29)は上限アンカー7点、境界1点、対数傾き、検出力条件、失敗条件という本体構造と一致し、誤った3536/7071等のliteralも持たない。

成果物影響 — 地図の参照先・説明・受理集合は変わらない。

提案 — なし。

## 総括

格子、raw符号化、3測定順、5%検出力、JSON parse、correctness authority、時間枠は成立している。  
本体の3535/7070が正しく、親裁定の3536/7071が計算誤りである。  
must-fixは、aggregate verdictの非排他性、ゼロ境界の未定義、必須契約違反の失敗条件漏れ、fieldとWAL source pathの未結合の4件。  
時間枠はformal correctness 5反復を保守的に加えても約20分/jobで、195分/300分枠内にある。  
docs-onlyの範囲で、JSONと散文の判定規則を閉じればよい。