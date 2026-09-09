## 所見

### [refuted] [nit] 登録格子に到達不能点や別分岐へ落ちる点はない

根拠 — codec は物理値 0〜999 を生値、1000〜9999 を `+2000` で符号化し、`decode(encode(x))=x` とする。[backoff_extended_sweep.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:60) [patch:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/patches/silo-backoff-fixed.patch:69)

| 物理 µs | raw | decode | C++ 商 | 実現 µs |
|---:|---:|---:|---:|---:|
| 999 | 999 | 999 | 0 | 999 |
| 1000 | 3000 | 1000 | 3 | 1000 |
| 1001 | 3001 | 1001 | 3 | 1001 |
| 1414 | 3414 | 1414 | 3 | 1414 |
| 2000 | 4000 | 2000 | 4 | 2000 |
| 2828 | 4828 | 2828 | 4 | 2828 |
| 3000 | 5000 | 3000 | 5 | 3000 |
| 4000 | 6000 | 4000 | 6 | 4000 |
| 5657 | 7657 | 5657 | 7 | 5657 |
| 8000 | 10000 | 8000 | 10 | 8000 |
| 8944 | 10944 | 8944 | 10 | 8944 |
| 9999 | 11999 | 9999 | 11 | 9999 |

raw 値としての 1000〜2999 は Python decoder が拒否する wire-domain hole で、C++ では商 1/2 の別形へ入る。しかし登録点はすべて codec を通るためこの hole に入らない。raw 3000 は物理 1000、raw 9999 は物理 7999 である。

成果物影響 — 格子値・raw 表・受理集合の変更は不要。

提案 — 事前登録に「物理値」と「raw 値」を明確に分け、raw hole `[1000,2999]` を発行禁止集合として併記する。

### [real] [must-fix] 判定入力の field 契約がなく、`cv` と `certified` を既存 report の意味で読むと誤判定する

根拠 — 現行 report の実体は次である。[backoff_extended_sweep.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1088) [同:1149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1149)

- `backoff_us`: integer µs、文脈点は null
- `kind`: string
- `abort_rate_reps`: length-5 number array、無次元
- `throughput_tps_reps`: length-5 number array、TPS
- `representative_abort_rate`: median-throughput rep に付随する値で、abort 中央値ではない
- `median_tps`: number、TPS
- `cv`: throughput CV、無次元
- `correctness_verified`: bool
- `certified`: 現行 T2418 report では常に false
- top-level `reps/extime_s/records/threads/status`: integer/string

`backoff_extended_sweep_report.py` も `tps_reps` と `cv` を一組として検査している。[backoff_extended_sweep_report.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep_report.py:85) 一方、プランは abort と throughput の CV を別々に要求するが、将来 report の exact field 名を固定していない。[plan.md:155](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:155) また既存 report は correctness を bool へ畳み、5 本の correctness verdict を保存しない。点の `certified` は `false` なので、失敗条件の「certified」をこの field に結びつけると全 cohort が恒偽になる。[plan.md:168](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:168)

成果物影響 — `cv` を abort CV と誤読すれば formal 受理集合が変わり、`certified` を点 field に結べば全 27 cell が失敗する。

提案 — spec に `analysis_input_contract` を追加し、少なくとも `abort_rate_reps`、`throughput_tps_reps`、`abort_rate_cv`、`throughput_tps_cv`、5 本の correctness verdict、binary identity、elapsed time、prereg commit/spec SHA の field 名・型・単位を固定する。

### [real] [must-fix] 探索開示の `median_abort_rate` が一箇所だけ中央値ではない

根拠 — プランは write-heavy / 2000 µs を `0.0293` として `median_abort_rate` に収録する。[plan.md:234](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:234) 実 reps は `[0.0292,0.0296,0.0292,0.0293,0.0292]` なので中央値は `0.0292`、平均は `0.0293`。現行 `representative_abort_rate` は abort 順位でなく median-throughput rep から選ばれる。[runner.py:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/calibrator/runner.py:1254)

成果物影響 — `disclosed_exploration.median_abort_rate.write-heavy[0]` が `0.0293` から `0.0292` に変わる。

提案 — 真の中央値へ直すか、key を `representative_abort_rate` に改名する。正式計算にはいずれも使わず、5 rep の算術平均を再計算する。

### [refuted] [nit] 探索値が 5% 飽和判定を通るという懸念

根拠 — [plan.md:122](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:122) の式へ実 reps を代入した結果は次のとおり。片側確率は `1-0.05/24`。

| workload | 区間 | qhat | se | nu | qL | U |
|---|---|---:|---:|---:|---:|---:|
| write-heavy | 2000→4000 | -0.56249 | 0.004209 | 5.666 | -0.58196 | 0.33194 |
| write-heavy | 4000→9999 | -0.60286 | 0.002339 | 7.188 | -0.61251 | 0.34594 |
| balanced | 2000→4000 | -0.58819 | 0.003593 | 6.277 | -0.60395 | 0.34205 |
| balanced | 4000→9999 | -0.66825 | 0.003827 | 7.594 | -0.68371 | 0.37744 |
| read-heavy | 2000→4000 | -0.51045 | 0.002958 | 7.172 | -0.52267 | 0.30392 |
| read-heavy | 4000→9999 | -0.52330 | 0.003479 | 6.674 | -0.53813 | 0.31134 |

したがって `U<=0.05` は探索 6 区間では全て偽で、30.4〜37.7%である。一方、静的点の abort CV は 0.00263〜0.006151、既存 `cv` すなわち throughput CV は 0.001822〜0.006508なので、`CV<0.02` は全静的点で真。探索値域では両 gate とも一定の verdict だが、将来格子に対する論理的な恒真・恒偽ではない。

成果物影響 — 同程度の傾きなら結末は飽和ではなく域内非飽和となり、CV では失敗しない。

提案 — `maximum_reported_cv` を `maximum_reported_throughput_cv=0.006508...` とし、別に `maximum_recomputed_abort_cv=0.00615149...` を開示する。

### [real] [must-fix] 8944 µs による終端二分は 5 rep では 5%幅を判別できない

根拠 — 通常半オクターブは `h=0.346574` だが、8000→8944 と 8944→9999 はそれぞれ約 `0.1115`。[plan.md:40](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:40) `n=5`、両端 CV が探索の最大 abort CV 0.006151、真に平坦な `qhat=0` とすると、`t(0.9979167,8)=3.9618` である。

- 半オクターブ: `Uflat=3.03%`。5%を判別可能。
- 終端短区間: `Uflat=9.13%`。真に平坦でも飽和にならない。
- プランが引用する 0.0065 を使うと `Uflat=9.63%`。
- 終端で 5%/倍増が意味する実区間差はわずか 0.822%。半オクターブでは2.532%。

同じ CV が両端にある近似では、短区間に必要なのは abort CV 0.006151なら12 rep、0.0065なら13 rep。さらに `CV<0.02` gate はこの検出可能性を保証せず、2%近傍では半オクターブさえ不足する。

成果物影響 — 5 rep のままでは 8000 µs より右の真の plateau を「域内非飽和」と報告しやすく、8944追加の目的を達成しない。

提案 — 全点を増やさず、raw count 化を前提に 8000/8944/9999 の性能 rep だけ13へ固定する。5 repを守るなら8944を外し、8000→9999を分割せず、8000以後の開始位置は右 censor と明記する。

### [real] [must-fix] 1e-4量子化を無視した se は飽和側へ有利で、正値・標本分散ゼロでは nu が未定義になる

根拠 — 9999 µs の量子幅 `1e-4` は平均に対し write-heavy 0.876%、balanced 0.688%、read-heavy 1.355%。各標本 sd はそれぞれ `4.47e-5 / 8.94e-5 / 4.47e-5` で、全て量子幅より小さい。parser は raw count より先に、出力済み `abort_rate` を採用する。[benchparse.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/calibrator/benchparse.py:66)

丸め後の標本 sd 自体が上向きか下向きかは一般には符号を確定できない。しかし丸め値を exact として既知の ±0.5e-4 不確実性を捨てる区間は、resolution-aware 区間より必ず狭い。結果は qL が高い側、U が低い側になり、飽和を宣言しやすくなる。また既存 t2266 実物には正値 `[0.0237]*5` が存在する。[t2266 read-heavy JSON:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/t2266-backoff-static-tail-read-heavy.json:1) 隣接両 cell がこの状態ならプランの `nu` は `0/0` となるが、特殊規則は全ゼロ abort しか扱わない。[plan.md:134](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:134) [同:157](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:157)

成果物影響 — 飽和区間の受理集合が広がり得るうえ、正値・両端分散ゼロ区間では verdict を生成できない。

提案 — 各 rep の `abort_counts_` と `commit_counts_` を保存し、`aborts/(aborts+commits)` を全精度で再計算する。不可なら量子化区間を伝播し、正値ゼロ分散は `indeterminate` とする規則を追加する。

### [refuted] [nit] 9点格子が時間枠を超える懸念

根拠 — t2266 の8 genomeは build・verify・bench・commitを11分で完走し、律速は build ではなく取引数に比例する直列性検査だった。[t2418 README:39](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:39) 単純比例でも9点は `660×9/8=742.5秒`、約12.4分/job。3 job合計の資源時間は約37.1分だが、各 job は独立である。現行 cap は195分、PBSは300分。[b10_backoff_grid.sh:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh:4) [同:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh:10)

成果物影響 — 格子・repを時間理由で削る必要はない。終端3点だけ13 performance repにしても十分収まる。

提案 — 予測値ではなく「8点11分からの比例上界12.4分/job」として事前登録へ明記する。

### [refuted] [nit] 既存系列・test・docs lintとの直接衝突

根拠 — 既存識別子と stem は `extended` / `b10-backoff-grid-*`、`t2266-tail` / `t2266-backoff-static-tail-*`、`t2418-explore` / `t2418-backoff-static-explore-*` に分離済み。[backoff_extended_sweep.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:81) [同:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1197) [同:1258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1258) `EXTENDED_SWEEP_US[-1]==1000` の pin は実在する。[test_backoff_extended_sweep.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/tests/test_backoff_extended_sweep.py:388) プランはこの test と定数を変更しない。[plan.md:582](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:582)

新規 prereg path/schema は現 repoに同名 hitがない。将来の formal RUN_KIND/schema/stemはまだ命名されていないため、現時点で衝突する実体もない。

成果物影響 — 現 wave の文書名、既存系列の受理集合、凍結物、testは変わらない。

提案 — 次 waveで具体名を決めた時点に、specの禁止3系列との集合非交差 testを置く。

### [real] [nit] `check_docs.py` は新規 prereg本文を検査対象にしない

根拠 — `docs/README.md` は living docsだが、新規 `b10-backoff-static-tail-preregistration.md` は列挙にもglobにも入らない。[check_docs.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/check_docs.py:124) 行番号参照、D/path実在性は living docsだけへ適用される。[check_docs.py:6673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/check_docs.py:6673) placeholder検査は worklog/archive/insightsだけである。[check_docs.py:2591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/check_docs.py:2591) 任意の新規docsに対するbyte予算や三軸語検査も実装されていない。

予定するREADME追記自体には禁止形の行番号参照もplaceholderもなく、新規path作成後はpath実在性を満たす。したがって既存条項への直接違反はないが、checker緑は新規本文の健全性を証明しない。

成果物影響 — prereg本文に腐る参照やplaceholderがあっても、`check_docs.py` の受理結果は変わらない。

提案 — 本 waveでchecker変更は要求しない。author/reviewが新規本文を手動走査し、checker緑を本文検査済みの証拠として報告しない。

## 親 brief への攻撃

指定された数値主張には誤りなし。

- `RECORDS=1_000_000 / THREADS=48 / EXTIME=3 / REPS=5` は現行 `p2_2.py` の literal と探索 report top-levelの双方で一致する。[p2_2.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/p2_2.py:54)
- 表現上限9999、raw上限11999は codecで確認できる。[backoff_extended_sweep.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:60)
- `EXTENDED_SWEEP_US` の上端1000と、そのtest pinは実在する。[backoff_extended_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:55) [test_backoff_extended_sweep.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/tests/test_backoff_extended_sweep.py:388)

ただしbriefは判定量のfield契約、abort量子化、終端短区間の検出力を確定事項に含めていない。この欠落により、docs-only成果物のままでは次waveが異なる受理集合を実装できる。

## 総括

codec、既存系列の分離、上端test pin、時間枠は成立している。  
探索6区間のUは30.4〜37.7%で全て非飽和、静的点のCV gateは全て通る。  
must-fixは判定field契約、誤ったmedian開示、1e-4量子化、正値ゼロ分散規則の4点。  
特に8944による終端二分は5 repでは真のplateauも通せず、目的と検出力が矛盾する。  
raw abort/commit countを保存し、終端3点だけ最大13 performance repへ増やすのが最小の修正である。