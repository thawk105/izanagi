# [T-810] 段 1 前提実測 (2026-08-11、base main 9abd23da)

すべて実物から採取した。既存 docs は根拠にしていない。

## F-1. registered calibration は 2 件・**2 ノード**ある (runbook §7.5 の記述は stale)

`orchestrator/campaign/env_contract.py:_build_registry` の静的 registry:

| generation | record | host | 取得 UTC | noise_floor mean (tps) | within-run CV |
|---|---|---|---|---|---|
| pegasus g1 | `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` | **bnode011** | 2026-07-18T19:58:30Z | 3,918,457.8 | 0.011706 |
| pegasus g2 | `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` | **bnode048** | 2026-08-06T02:27:45Z | 3,848,941.0 | 0.012479 |

両者は同一 CCBench head `d706650cdb31e442bef45b9b4216951d4fb40969`、同一 workload
(`ycsb_rratio=50`, `ycsb_zipf_skew=0.9`, `ycsb_rmw=0`)、`threads=48`、noise_floor は
`records=1,000,000` の 10 反復。**平均差 = 69,516.8 tps = 1.774%**、
within-run の標本平均 SE は各 CV/√10 ≈ 0.37% なので差の SE ≈ 0.53% (名目 3.3 SE)。

**ただしこの 1.774% を「ノード間差」と読んではならない。**19 日離れており (F-2 のとおり)
binary も異なるため、node 効果・occasion 効果・binary 効果が完全交絡している。
runbook §7.5 の「登録済み calibration も bnode011 単独の記録 (CV 1.17%) しか持たず」は
2026-08-06 の g2 登録以降 **事実として古い**。ただし同節の結論 (ノード間分散を答えない) は残る。

## F-2. 「同一 binary」は既存経路では自動的に成立しない

g1 と g2 の `acquisition_receipt.ccbench.binary_sha256` は異なる
(`9ef84125ca4b3067…` vs `25c82a74bf98d303…`)。`build_argv` の差分は **4 箇所すべてが
job-scratch path** である:

```
-/scr/0_867876.nqsv/ccbench-source        +/scr/0_892707.nqsv/ccbench-source
-/scr/0_867876.nqsv/ccbench-build         +/scr/0_892707.nqsv/ccbench-build
--DCMAKE_PREFIX_PATH=/scr/0_867876.nqsv/gflags-install;/scr/0_867876.nqsv/glog-install
+-DCMAKE_PREFIX_PATH=/scr/0_892707.nqsv/gflags-install;/scr/0_892707.nqsv/glog-install
-/scr/0_867876.nqsv/ccbench-build         +/scr/0_892707.nqsv/ccbench-build
```

toolchain は完全一致 (`gcc 11.4.0` / `/usr/bin/x86_64-linux-gnu-gcc-11` / `cmake 3.25.0` /
`module intelpython/2022.3.1`)。`certify_calibration.sh` は node-local `/scr/$PBS_JOBID` に
build するので、**job ごとに path が binary へ焼き込まれ、同一 head でも bytes が変わる**。
`job_script_sha256` も両者で異なる (`4b50b998…` / `b56a0f7d…`)。

構造的には可能である: `orchestrator/campaign/buildcache.py` の既定 `cache_root` は
`<ccbench>/build-variants` (= `/work` 上の共有 path) で、`assert_binary_sha256` を持つ。

## F-3. 成果物への流入は 3 段の明示行為でしか起きない

**訂正 (段 2 の裏取りで判明、2026-08-11):** 「attempts → registered が別行為」は**誤り**である。
`orchestrator/calibrator/cli.py:793-856` の certify 経路は staging から
`registered/calibration-<digest16>.json` へ `_rename_noreplace` で**自動 publish** する。
したがって明示行為は 3 段ではなく **2 段** (registry への literal 追記と activation) であり、
`calibrator --certify` を流用する設計は 1 段目を自動で踏む。これが本 protocol で
既存 certify 経路を使わない最大の理由である。

`attempts/<job-id>/` (job が create-only で書く) → `registered/<name>.json` (certify が自動 publish) →
`env_contract.py` の静的 registry へ path + sha256 の literal を書く (reviewed golden
`contract_sha256` の一致検査つき) → `env_contract_activations` の head 更新 + 全 process 再起動。
`tools/issue_env_contract_activation.py --help` = 「発行だけでは有効化されず、表示された
head 定数を record と同一 commit で更新し、全 process を再起動して初めて有効になる」。
**自動昇格経路は無い。**

## F-4. `FROZEN_MANIFEST` は 23 path の whitelist で、`output/` への新規ファイル追加では壊れない

`orchestrator/tests/test_frozen_artifacts.py:38` の manifest に calibration record は無く、
`test_frozen_artifacts_match_manifest` は manifest の key だけを走査する。
exact key-set 検査 (`FROZEN_KEYSET_PROVISIONAL_82803D6D`) も manifest 自身の集合に対する検査である。

## F-5. T-139 pilot は **3 arm を同一 cluster (= 1 allocation) 内で**測る

`output/insights/2026-08-07_t139-mainrun-design/preregistration-draft.md` §3:
「cluster = 1 allocation」、`m_{A,wj}` は workload `w`・arm `A`・cluster `j` の代表値で、
`N_wj = m_X,wj − m_Dg,wj`、`D_wj = m_S,wj − m_Dg,wj`、`G_wj = m_S,wj − m_X,wj`。
受理条件は cluster level の標本平均・標本共分散から作る同時信頼領域。
Q4 = 「1 allocation = 1 immutable subcampaign + trial aggregator」、
Q5 = 「pilot 先行の二段階・目標効果量 d≈1.0 ≒ 11 cluster」(worklog (139)/(141)/(142))。

したがって **3 arm はノードを共有し、contrast はすべて node 内差である。**

## F-6. 計測 job の実寸

`tools/pegasus/certify_calibration.sh` = `#PBS -b 1`、`elapstim_req=02:00:00`、
予約式 `TSC(10) + cooldown_max(1200) + points(5)*sweep_reps(3)*120 + noise_reps(10)*120
+ 2*sweep_reps(3)*120 + build_cap(1080) + finalize_reserve(600) = 6610` 秒。
うち **build が 1080 秒**、noise 10 反復が 1200 秒。実測 sweep の 1 点あたり `walltime_s` は
3.47〜4.54 秒 (records 1e6〜4e6、threads 48)。

## F-8. 依存は静的リンクされる (段 3 待機中に親が実測)

`tools/pegasus/certify_calibration.sh:396` と `:460` はいずれも
`-DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF` で gflags / glog を `/scr` へ static
build / install する (同 `:357` のコメント「pinned-clean gflags を /scr で static build/install」)。
build_argv も `-DCMAKE_PREFIX_PATH=<gflags-install>;<glog-install>` を渡すだけである。
したがって **1 回だけ build した `ycsb_silo.exe` の bytes を各ノードへ配る設計は構造的に成立する** —
`/scr` に居残る shared library への依存を作らない。残る runtime 依存 (libstdc++ 等) は
同一 OS image である前提を、`ldd` の解決 path と hash の記録で確認する必要がある。

## F-9. 実 record の within-run 10 反復に下降傾向がある (親が独立に計算)

`verify-s3.py` による。lag-1 系列相関は両者ほぼ 0 なので、問題は自己相関ではなく**傾き**である。

| record | host | index との相関 r | t (df=8) | 傾き | 初回→最終 |
|---|---|---:|---:|---:|---:|
| `753f535a…` | bnode011 | −0.2985 | −0.88 | −4,523 tps/rep | −1.91% |
| `94a4b79f…` | bnode048 | **−0.6590** | **−2.48** | −10,454 tps/rep | −2.61% |

bnode048 側は両側 5% で有意である (2 件検定の多重性は留保)。
**ドリフトが within-run の σ_e に混入すると比 `σ_a/σ_e` が小さく出る**ため、
「ノード差は小さい」と誤結論する向きに効く。反復ごとの時刻記録と drift に頑健な要約が要る。

## F-10. `N=12, R=10` は与えられた条件下の最小設計ではない (親が独立に再計算)

`κ*=0.5`, `α=0.05`, assurance ≥ 0.80, per-node SD の RSE < 0.25 という段 2 の条件で、
`assurance(N,R) = P[F_{N−1,N(R−1)} < (1+Rκ*²)·F_{0.05;N−1,N(R−1)}]` を自前の F 分位で解いた。

| N | R | node-rep | F_0.05 | assurance | RSE(per-node) |
|---:|---:|---:|---:|---:|---:|
| 11 | 10 | 110 | 0.386262 | 0.785893 | 0.2357 |
| 12 | 10 | 120 | 0.407702 | 0.828815 | 0.2357 |
| **9** | **13** | **117** | 0.336560 | **0.807958** | **0.2041** |
| 13 | 9 | 117 | 0.425942 | 0.814876 | 0.2500 (条件不成立) |

段 2 の N=11/12 の値は再現した。しかし **`N=9, R=13` が全条件を満たし、
測定回数 (117 < 120) も確保ノード数 (9 < 12) も少ない。**
したがって 12/10 は「最小」ではなく、**何を最小化するか (同時確保ノード数 / 総ノード時間 /
経過時間) を先に決めない限り N・R は確定できない。**
また段 2 の RSE 式 `1/√(2(R−1))` は per-node SD の精度であり、pooled `σ_e` なら
`1/√(2N(R−1))` (上表のどの設計でも 0.07 程度で自動的に成立する)。**どちらの σ の精度を
条件にするかが未確定である。**

## F-7. キュー実状 (2026-08-11、段 1 時点)

`qstat` = `903116.nqsv izdw-13b RUN` / `903117.nqsv izdw-ee3 QUE` の 2 本のみ。
どちらも他 wave の dev-wave 用 dispatch であり、**T-139 の pilot / 本走 job は走っていない**。
`qstat -Qf gen_S` の値 (job server 149、CPU Number Min=Max=Std=48、Submit 数 UNLIMITED) は
worklog (418) の同日実測を参照する。
