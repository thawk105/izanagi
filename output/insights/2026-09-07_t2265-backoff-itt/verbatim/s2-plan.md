## 総括

段 2 では次を固定するのが妥当である。ファイル編集・commit・実測は行っていない。

- 主解析は policy 2 の `write-heavy / 48 threads` における、現在の割当が次窓へ与える近接 ITT とする。
- 12 seed の各 run 内で「推奨方向 minus 反転方向」の差を計算し、run を cluster として12個の run 差を等重み集約する。
- 等価域は対称な log 域 `[-ln(1.03), +ln(1.03)]` とし、標準的 TOST に対応する90% CIで等価判定する。95% CIも推定結果として併記する。
- P1-3 の「1更新 ITTを常時反転のrun効果に近似する」は採用しない。反実仮想 ITTとtrace-disabled性能対比は別の推定対象として扱う。
- `prereg_sha256` は旧 `docs/dynamic-backoff-preregistration.md` の来歴束縛として残す。新しい反実仮想主張は、別 field `counterfactual_preregistration` に入れる新文書の64文字SHA-256だけが束縛する。
- Pegasus投入体は既存 `.pbs` / `.py` だけを使い、解析 module は計測機へ投入しない offline module とする。
- `_validate_grid_contract` と `_validate_backoff_trace_contract`、認証のexact 2 cell、patch A hard pin、既存literalは変更しない。

## 事前登録の設計案

`docs/backoff-counterfactual-preregistration.md:1` を新規作成し、旧文書の版・発効形式 `docs/dynamic-backoff-preregistration.md:9` と束縛規則 `docs/dynamic-backoff-preregistration.md:21` を踏襲する。

### 0. 版と発効

- v1、発効日、凍結commitを記す。
- policy 2の反実仮想artifactを1件も見ていない時点で、以下のestimand、seed、判定、停止規則を凍結したと明記する。
- 旧事前登録はrun単位の動的backoff gridを対象とし、更新単位ITTを覆わないことを明記する。根拠は機構README `output/insights/2026-09-07_t2265-backoff-counterfactual/README.md:136` と `:140`。
- 発効後の変更は追記commitでのみ行い、既取得結果には遡及適用しない。

### 1. 主推定対象とoutcome

run `r` の policy 2 trace eventを時系列 `i=0,...,m_r-1` とし、次を固定する。

```text
Z[r,i] = assigned_invert
         0: 推奨方向を割当
         1: 反転方向を割当

T[r,i] = window_commits[r,i] / window_us[r,i]

Y[r,i] = ln(T[r,i+1] / T[r,i]),  i = 0,...,m_r-2

D[r] = mean(Y[r,i] | Z[r,i]=0)
       - mean(Y[r,i] | Z[r,i]=1)

theta_hat = (1/R) * sum_r D[r]
```

- `Y[r,i]` は更新 `i` の直後に観測される次窓throughputの変化である。割当はpatchのLCG更新 `patches/cicada-adaptive-counterfactual.patch:548`、clampはその後の `:566` にある。
- 正の `theta_hat` は推奨方向の方が反転方向より次窓の幾何平均throughput変化を大きくしたことを意味する。
- 最終eventは次窓を持たないため、割当や値を見ず位置だけで常に除く。
- 隣接する `Y` は同じ窓を共有し、carryoverもあり得る。この依存はrun内でモデル化せずcluster化する。
- 主estimandは現在の割当に対する無条件の近接ITTである。常時policy 0/1の長期効果ではない。

### 2. 主層と副次層

主層は `policy 2 / write-heavy / 48 threads` のみとする。stage 1でこの層の `cw-as-dyn` はbackoff中央値6 us、最大17 us、gradient 0が0.2%、naiveなrun内差SEが0.0082だったためである（`stage1-measurements.md:21`、`:38`）。

副次解析は確認的判定へ使わず、同じ推定量と95% CIを次について出す。

- 残る workload × threads 5層。
- `recommended_delta_sign` の `-1 / 0 / +1`。これは現在の割当前に確定する値だが、過去の割当で形成された状態である。
- `both_actions_feasible` の `0 / 1`。現在の割当前に計算されることはpatch `patches/cicada-adaptive-counterfactual.patch:516` と `:530` が固定している。
- event順をrun内の相対位置で4分した時間block。
- 上記を恣意的に交差させて「効いた部分集合」を選ばない。各軸の周辺層だけを出す。
- `inversion_realized` は層にも除外にも使わない。

### 3. 等価域と判定

```text
Delta = ln(1.03) = 0.029558802...
equivalence region = [-Delta, +Delta]
exp(theta) region = [1/1.03, 1.03]
                  = [0.970873786..., 1.03]
```

根拠は旧事前登録の実用差3% `docs/dynamic-backoff-preregistration.md:93`。ただし旧文書の非対称比 `[0.97,1.03]` ではなく、forward/invertを入れ替えても不変な対称log域へ直す。

判定を次のように固定する。

- 等価: run-cluster 90% CI全体が等価域内。これは両側有意水準5%のTOST。
- 推奨方向の実用優越: 95% CI下端が `+Delta` より大きい。
- 反転方向の実用優越: 95% CI上端が `-Delta` より小さい。
- それ以外: inconclusive。
- 95% CIが0を跨がないだけでは「実用優越」と呼ばない。
- 等価と統計的非ゼロは論理的に両立し得るため、95% CIとTOST結果を別fieldで報告する。

### 4. 分散と検出力

run差を独立clusterの単位とする。

```text
s_D^2 = sum_r (D[r] - theta_hat)^2 / (R - 1)
SE(theta_hat) = s_D / sqrt(R)
df = R - 1
```

主解析は `R=12`、90% CIには `t(0.95,11)=1.795885`、95% CIには `t(0.975,11)=2.200985` を用いる。

検出力設計は次で固定する。

- 計画cluster SDは `0.032 log point`。
- これはstage 1のnaiveなrun内SE 0.0082の約4倍であり、未知のrun間変動と系列依存に保守的な余裕を置く。
- 真の `theta=0`、正規なrun差、R=12、上記TOSTという計画モデルでは等価判定力は約82%。目標は80%以上。
- stage 1は単一legacy runかつtrace v1なので、cluster SDの実測推定ではないことを明記する。

### 5. seed

次の12値を固定する。生成規則はASCII文字列
`izanagi-t2265-policy2-seed-NN` のSHA-256先頭8 byteをbig-endian unsigned 64-bit整数としたもの。

| slot | seed |
|---:|---:|
| 00 | 5744733223455690259 |
| 01 | 781552995023334429 |
| 02 | 1606918558588661 |
| 03 | 16736322205931003081 |
| 04 | 1227967287010452276 |
| 05 | 2171878327641984105 |
| 06 | 2057459156086657874 |
| 07 | 11135758292722279839 |
| 08 | 13576760736062537317 |
| 09 | 5470969369189575692 |
| 10 | 2410271300384854639 |
| 11 | 13467815584134101060 |

性能block 0..6のpolicy 2にはslot 00..06を同順で使う。LCGは単一の決定的full-period系列の異なる開始点であり、形式的に独立な乱数streamとは主張しない。

### 6. 除外・欠測規則

- 全eventを使用し、clamp、実適用差分0、`inversion_realized`、`Y`、外れ値、throughput大小による除外・winsorizeをしない。
- `both_actions_feasible=0` と `recommended_delta_sign=0` も主解析に残す。これがITTである。
- schema、SHA、exact axes、seed、trace summary、連続seqなど事前処置の契約に違反するartifactは入力不適格とする。
- `dropped>0` は現driver自身がartifact完成前に拒否する契約である（`t2187_adaptive_const_probe.py:1082`）。
- `window_commits=0` が1件でもあれば、そのeventだけを除外せず、log outcomeが定義不能として主判定全体をinconclusiveにする。
- 片方の割当がrun内に1件もない場合もrunを選択的除外せず、主判定をinconclusiveにする。
- complete artifactがあるslotは最初に完走した1件だけを採る。metricを見て再測定しない。

### 7. 停止規則

- 診断は固定12 seed、性能は固定7 block。途中解析・逐次停止・seed追加をしない。
- 各slotは初回とinfra-only再投入2回の最大3 receiptまで。再投入できるのはoutcomeを開く前に確認できたqueue、node、prologue、build、identity、artifact未完成だけ。
- 12診断runが揃わなければ確認的ITT判定を出さない。
- 性能は7 blockを予定し、7未満は表とCIのみで確認的性能判定を出さない。
- 完成artifactの遅さ、分散、効果、clamp等を理由に置換しない。

### 8. trace-disabled性能の副次計画

性能outcomeを、block `b`、cell `a`、workload `w`、threads `t` のsole throughputとして固定する。

```text
P[b,a,w,t] = throughputs[0]
L[b,a1,a0,w,t] = ln(P[b,a1,w,t] / P[b,a0,w,t])
```

7 block内対比を次の順で事前指定する。

1. `p1 / p0`: 常時反転policyと推奨policyのrun全体差。
2. `p2 / p0`: 無作為割当policyと推奨policyのrun全体差。
3. `p2 / p1`: 無作為割当policyと常時反転policyのrun全体差。

各対比はblock内log比の平均と95% t CIを全6 workload × threads点で出す。`none` と `stock` はgrid契約を満たす対照として全値を示すが、主ITTの判定には使わない。

### 9. 主張範囲

主張できるのは指定環境、Silo、固定workload、固定threads、固定seed集合における、trace-enabled policy 2の一窓先近接ITTだけである。

主張できないものは次。

- trace-disabled buildの性能を診断ITTから推論すること。
- 1更新ITTを常時policy 0/1のrun効果へ置き換えること。
- carryoverが1窓で消えること。
- policy 0/1/2の直列性。
- 他protocol、他hardware、他threads、他workloadへの一般化。
- 決定的LCGが暗号学的または形式的に独立な乱数であること。

性能表はtrace-disabled artifactだけから作るが、policy非0は未認証と明記する。

## driver の変更計画 (file:line)

- `tools/pegasus/probes/t2187_adaptive_const_probe.py:80`
  - 旧 `PREREGISTRATION` はそのまま残し、`COUNTERFACTUAL_PREREGISTRATION = ROOT / "docs" / "backoff-counterfactual-preregistration.md"` を追加する。
- 同 `:150`
  - 既定seed定数を後方互換用として維持する。
- 同 `:507`
  - decimalかつ `0 <= seed < 2**64` を要求するargparse typeを追加する。bool、負数、上限超過、16進記法を拒否する。
- 同 `:563`
  - `genome_for(..., step_policy_seed=None)` とし、policy 2では明示seedを `BACKOFF_STEP_POLICY_SEED` へ渡す。policy 0/1は既定seedを維持し、seed違いでinert binaryを作り直さない。
- 同 `:589`
  - seedをcell identityへ混ぜない。seedはcell文字列ではなくrun割当identityであり、12-field literalを変えない。
- 同 `:812`
  - `_counterfactual_prereg_sha256()` を追加し、新文書のbytesをSHA-256する。自己参照hashを文書へ書かない。
- 同 `:2639`
  - `--step-policy-seed` を追加。policy 2 cellがある場合だけ必須とし、それ以外の既存呼出は変えない。
- 同 `:2698`
  - `_validate_backoff_trace_contract` は無変更。seed検査をこのexact literal検査へ混ぜない。
- 同 `:2727`
  - `_artifact_contract_metadata` は、12-field policy cellを含むrunについて
    `counterfactual_preregistration: <64 lowercase hex>` を返す。`"pending"` は生成不能にする。
- 同 `:3178`
  - parse後にpolicy 2の有無と明示seedを照合し、build前にfail closedする。
- 同 `:3224`
  - counterfactual runのtop-levelに `step_policy_seed` と新文書hashを記録する。既存 `prereg_sha256` は旧文書hashのまま残す。
- 同 `:3274`
  - 各buildへ解決済みseedを渡す。可変seedを実際に使うのはpolicy 2だけとする。
- 同 `:3361`
  - journalからも復元できるよう、policy 2 rowへ `step_policy_seed`、counterfactual runの全rowへ新文書hashを記録する。
- 同 `:3387`
  - `"pending"` の直接代入を削除する。
- `tools/pegasus/probes/t2187_adaptive_const_probe.pbs:67`
  - `IZANAGI_T2187_STEP_POLICY_SEED` を受ける変数と、非空時だけ作る `--step-policy-seed` argv配列を追加する。
- 同 `:108`
  - seedはASCII decimalだけを許可する。uint64上限はPython側で再検査する。
- 同 `:136`
  - traceのexact 2 literal gateは逐語で維持する。
- 同 `:372`
  - performance branchにseed argvを渡す。certify branch `:386` 以降には渡さず、認証のexact 2 cell契約を変更しない。
- `patches/README.md:289`
  - `"pending"` の現行説明だけを「新事前登録bytesのSHA-256を記録」に更新する。過去insight `output/.../README.md:140` は当時の事実なので改変しない。
- `patches/cicada-adaptive-counterfactual.patch:35`
  - patch自体は変更しない。既にseed CMake option、LCG、割当前trace、clamp順序を備えている。

## 解析 module の計画 (file:line)

`orchestrator/campaign/backoff_counterfactual_analysis.py:1` を新規のoffline moduleとして置く。PBSやPegasus registryからは呼ばない。

公開面は次とする。

```python
analyze_counterfactual(
    diagnostic_paths: list[Path],
    performance_paths: list[Path],
    preregistration_path: Path,
) -> dict
```

任意のoffline CLIは同関数の薄いwrapperだけとし、入力pathを明示列挙させる。globや「最新artifact」の暗黙選択は行わない。出力はcreate-only JSON
`izanagi-backoff-counterfactual-analysis/v1` とする。

入力検査:

- diagnostic 12件、performance 7件のファイルSHA-256を記録。
- repo head、driver/PBS hash、patch stack、旧 `prereg_sha256`、新hashが集合内で一致すること。
- diagnosticはschema v3、`kind=diagnostic-backoff-trace`、`headline_eligible=false`、`throughput_scope=diagnostic_only`。
- performanceはschema v3、`kind=performance-only-probe`、`backoff_trace=false`、trace symbol/string count 0。
- diagnosticは現exact literal `t2187_adaptive_const_probe.py:266`、workloads/threadsは `:259` と `:260`。
- performanceは事前登録したexact 5 cell順、全3 workload、threads 24/48。
- seed集合、diagnosticの12 seed一意性、performanceのrep 0..6とseed 00..06対応を検査する。
- artifact内の値で入力を選別しない。

計算出力:

- seedごとの `D[r]`、arm件数、主推定値、cluster SD/SE、90%/95% CI、TOST判定。
- 全副次層。同一run内に片armがなければ値を捏造せず理由付きnull。
- trace-disabled性能の3対比、block値、95% CI。
- 入力provenance、欠測、判定不能理由、主張限界。
- 診断throughputを性能表へ流す経路は設けない。

## テスト計画 (file:line)

- `orchestrator/tests/test_t2187_adaptive_const_probe.py:1447`
  - default seedの後方互換、任意uint64 seedがpolicy 2 genomeだけへ届くこと、policy 0/1がseedで変わらないことを検査する。
- 同 `:2021`
  - pending期待を削除し、新文書の実SHA-256、top-levelとrowの一致、`pending` がdriver sourceに存在しないことを検査する。
- 同 `:2049`
  - PBSが新envをdecimal検査し、performance execへ1回だけ渡すことを固定する。
- 同 `:2213`
  - exact診断軸テストを変更しない。
- 同 `:2253`
  - exact 2 literalの陽性・陰性集合を変更しない。
- 同 `:2313`
  - Python/PBS literalのbyte同一検査を変更しない。
- `orchestrator/tests/test_dynamic_backoff_transitions.py:823`
  - `_policy_defines` にtest-only seed引数を追加し、別seedでbuildしたpolicy 2の最初の割当列をLCG式から独立再計算して照合する。
- 同 `:1321`
  - 既定seedの逐語列 `0111001000100110` は既存回帰として維持する。
- 同 `:1428`
  - policy 0ではseed/LCG stateがpreprocess後に残らず、policy 2では別seedが残ることを追加確認する。
- `orchestrator/tests/test_backoff_counterfactual_analysis.py:1`
  - 合成artifactでoutcome alignment、最後のevent除外、run等重み、cluster variance、90/95% CI、TOST境界を検査する。
  - clamp、action 0、`inversion_realized=0`、極端なYが除外されないことを検査する。
  - post-treatment除外を入れる変異、seed重複、SHA不一致、trace/performance混入、zero commits、片arm欠落をfail closedまたはinconclusiveにする。
  - artifact順を入れ替えても結果bytesが同一になることを検査する。
- patch A hard pinの既存検査 `test_t2187_adaptive_const_probe.py:1554` とtrace完全除去検査 `test_dynamic_backoff_transitions.py:1470` は変更しない。

このdispatchではread-only制約に従いpytestを実行しない。親は実装後、上記3 test fileを必ず `tools/run_tests.py` 経由で実行し、pytestを直接起動しない。

## 投入計画 (逐語の qsub 引数)

以下は新事前登録とdriverを含むtracked-clean commitから、記載順に1 jobずつ完了を待って投入する。診断12本が終わるまで結果解析を開始せず、その後に性能7本を直列投入する。

診断12本:

```sh
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=5744733223455690259' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=781552995023334429' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=1606918558588661' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=16736322205931003081' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=1227967287010452276' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=2171878327641984105' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=2057459156086657874' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=11135758292722279839' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=13576760736062537317' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=5470969369189575692' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=2410271300384854639' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=1,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt,IZANAGI_T2187_CELLS=cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=13467815584134101060' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
```

性能7 block:

```sh
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=0,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=5744733223455690259' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=1,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=781552995023334429' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=2,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=1606918558588661' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=3,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=16736322205931003081' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=4,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=1227967287010452276' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=5,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=2171878327641984105' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
qsub -v 'IZANAGI_T2187_MODE=performance,IZANAGI_T2187_BACKOFF_TRACE=0,IZANAGI_T2187_OUT_DIR=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2265-itt,IZANAGI_T2187_CELLS=none:0:100:1000:10+stock:1:100:1000:10+cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0+cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1+cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,IZANAGI_T2187_WORKLOADS=write-heavy+balanced+read-heavy,IZANAGI_T2187_THREADS=24+48,IZANAGI_T2187_REP_INDEX=6,IZANAGI_T2187_STAGE=2,IZANAGI_T2187_STEP_POLICY_SEED=2057459156086657874' tools/pegasus/probes/t2187_adaptive_const_probe.pbs
```

診断引数はPython側のexact contract `t2187_adaptive_const_probe.py:2698` とPBS側 `t2187_adaptive_const_probe.pbs:136` をそのまま通る。性能cellはexact `none` とexact stockを各1本持つためgrid契約 `t2187_adaptive_const_probe.py:445` を通る。

## 親 brief への異議

- P1-1: おおむね採用。ただしLCGは固定seedから決まる疑似無作為列なので「厳密に独立」とは書かず、事前固定された近接ITTと限定する。
- P1-2: 採用。stage 1の実測が最も処置の届く層を支持する。
- P1-3: 一部棄却。`±ln(1.03)` は採るが、「1更新ITT ≈ 常時反転run効果」は採らない。carryover未測定で、policy 1/0は別軌跡だからである。
- P1-4: 採用。ただし12本の根拠をcluster SD 0.032、TOST power約82%として明文化し、性能7本とは別estimandにする。
- P1-5: 「記述的二次」は採用。両fieldは現在の割当前だが過去割当の影響を受けた状態なので、現在の割当との効果修飾以上へ一般化しない。
- P1-6: 採用。性能はexact `none + stock + p0 + p1 + p2`。workloadsは3種、threadsは24/48に固定する。

## 残る不確実性

- stage 1は単一legacy runで、真のrun間cluster SDを推定できない。検出力は計画仮定に依存する。
- 12 seedは同じLCG周期上の異なる開始点であり、形式的な独立streamではない。
- 固定cell順のtrace-disabled性能にはjob内時間ドリフトが残るため、性能対比は副次に留める。
- policy非0の直列性は未認証であり、本scopeでは認証を追加しない。
- `window_commits=0` や片arm欠落は想定上ほぼ起きないが、発生時は事前規則どおり確認的判定不能となる。