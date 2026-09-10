# 親が実測した生の値と再現手順

測定は計算ノード gen_S の 1 PBS job (`966271.nqsv`、hostname `bnode032`、Elapse 1596 秒) で行った。
checkout は `dd5fddf04e7d876cee9ff9a87849cdf60d07080b`。10 arm を投入し 9 arm が成立した
(`Z-B1` = 較正 + timing は arm 生成に至らず missing)。

計測 probe は repo 外に置いた使い捨てで、commit していない。逐語は `verbatim/probe-source.md`。

## A. 既存 14 走の残差を実測最大 worker で再計算した

**前 wave の一次表 (`2026-09-01_t2097-acceptance-floor-decomposition/measurements.md` §F) は
`wall − max(最長単体, 総報告時間/48)` を残差としていた。** これは理論下界を引いた値であって、
実測の最大 worker report 合計を引いた値ではない。段 3 のレンズ A がこの食い違いを指摘した。
全 14 走・42 shard を `report.json` の `worker_occupancy` から再計算した。

```
shard-0 n=14 中央値= 77.21 最小= 75.66 最大= 84.53
shard-1 n=14 中央値= 56.38 最小= 55.83 最大= 60.04
shard-2 n=14 中央値= 56.62 最小= 55.86 最大= 58.23
```

**実測値で引くと残差は下界で引くより安定する。** 例えば `349543d5` の shard-1 は
下界差引 78.35 秒に対し実測差引 56.30 秒である (差 22 秒)。

全 42 行 (session 先頭 8 文字 / shard / pytest wall / 実測最大 worker report 合計 / 残差 / 下界差引):

```
7ac4faab  shard-0  wall= 226.01  maxworker=  147.811  resid= 78.20  (下界差引= 81.86)
7ac4faab  shard-1  wall= 166.68  maxworker=  107.977  resid= 58.70  (下界差引= 60.35)
7ac4faab  shard-2  wall= 134.02  maxworker=   77.375  resid= 56.65  (下界差引= 57.77)
349543d5  shard-0  wall= 213.91  maxworker=  135.676  resid= 78.23  (下界差引= 87.78)
349543d5  shard-1  wall= 176.01  maxworker=  119.708  resid= 56.30  (下界差引= 78.35)
349543d5  shard-2  wall= 130.63  maxworker=   74.259  resid= 56.37  (下界差引= 57.44)
6f39928e  shard-0  wall= 202.49  maxworker=  125.597  resid= 76.89  (下界差引= 78.94)
6f39928e  shard-1  wall= 137.46  maxworker=   80.377  resid= 57.08  (下界差引= 59.54)
6f39928e  shard-2  wall= 125.82  maxworker=   69.211  resid= 56.61  (下界差引= 62.53)
690c10ec  shard-0  wall= 233.30  maxworker=  155.953  resid= 77.35  (下界差引= 88.79)
690c10ec  shard-1  wall= 141.84  maxworker=   81.796  resid= 60.04  (下界差引= 63.10)
690c10ec  shard-2  wall= 132.95  maxworker=   76.029  resid= 56.92  (下界差引= 62.87)
4524841d  shard-0  wall= 212.33  maxworker=  135.793  resid= 76.54  (下界差引= 86.83)
4524841d  shard-1  wall= 144.47  maxworker=   88.223  resid= 56.25  (下界差引= 62.73)
4524841d  shard-2  wall= 123.61  maxworker=   66.484  resid= 57.13  (下界差引= 63.07)
b6b39445  shard-0  wall= 223.89  maxworker=  144.207  resid= 79.68  (下界差引=104.47)
b6b39445  shard-1  wall= 140.49  maxworker=   82.715  resid= 57.77  (下界差引= 59.43)
b6b39445  shard-2  wall= 132.09  maxworker=   75.465  resid= 56.62  (下界差引= 62.57)
bd617d36  shard-0  wall= 195.83  maxworker=  119.895  resid= 75.93  (下界差引= 77.24)
bd617d36  shard-1  wall= 140.65  maxworker=   84.818  resid= 55.83  (下界差引= 73.02)
bd617d36  shard-2  wall= 136.62  maxworker=   79.592  resid= 57.03  (下界差引= 66.96)
92a64a50  shard-0  wall= 210.04  maxworker=  134.379  resid= 75.66  (下界差引= 77.22)
92a64a50  shard-1  wall= 140.86  maxworker=   84.396  resid= 56.46  (下界差引= 59.54)
92a64a50  shard-2  wall= 123.54  maxworker=   66.937  resid= 56.60  (下界差引= 57.66)
68f13f48  shard-0  wall= 226.78  maxworker=  148.257  resid= 78.52  (下界差引= 92.38)
68f13f48  shard-1  wall= 130.04  maxworker=   73.771  resid= 56.27  (下界差引= 61.65)
68f13f48  shard-2  wall= 132.65  maxworker=   75.696  resid= 56.95  (下界差引= 67.34)
63bcb314  shard-0  wall= 212.79  maxworker=  136.381  resid= 76.41  (下界差引= 86.81)
63bcb314  shard-1  wall= 215.36  maxworker=  156.991  resid= 58.37  (下界差引= 59.62)
63bcb314  shard-2  wall= 131.86  maxworker=   76.001  resid= 55.86  (下界差引= 67.37)
ab716aea  shard-0  wall= 216.66  maxworker=  139.588  resid= 77.07  (下界差引= 78.29)
ab716aea  shard-1  wall= 188.57  maxworker=  132.651  resid= 55.92  (下界差引= 77.42)
ab716aea  shard-2  wall= 199.71  maxworker=  141.479  resid= 58.23  (下界差引= 64.03)
3125bcc7  shard-0  wall= 286.39  maxworker=  205.362  resid= 81.03  (下界差引= 81.15)
3125bcc7  shard-1  wall= 133.92  maxworker=   78.065  resid= 55.85  (下界差引= 58.49)
3125bcc7  shard-2  wall= 139.76  maxworker=   83.884  resid= 55.88  (下界差引= 67.82)
8410a1ac  shard-0  wall= 220.86  maxworker=  144.005  resid= 76.85  (下界差引= 77.03)
8410a1ac  shard-1  wall= 134.89  maxworker=   78.736  resid= 56.15  (下界差引= 68.02)
8410a1ac  shard-2  wall= 136.59  maxworker=   80.089  resid= 56.50  (下界差引= 66.47)
dd911f21  shard-0  wall= 310.26  maxworker=  225.734  resid= 84.53  (下界差引= 90.98)
dd911f21  shard-1  wall= 141.47  maxworker=   84.029  resid= 57.44  (下界差引= 60.24)
dd911f21  shard-2  wall= 124.84  maxworker=   68.931  resid= 55.91  (下界差引= 57.18)
```

wall は各 shard の PBS stdout の要約行、最大 worker は `report.json` の `worker_occupancy` から取った。
最長単体は `report.json` に無いので、下界差引の項だけは JUnit の千分位丸め値を使っている
(出典を出力へ明記した)。

## B. 今回の 9 arm

`残差 = wall − 実測最大 worker report 合計`。probe 欄の `none` は計装なしの対照。

| arm | shard | probe | wall | 最大 worker | 残差 | 赤 |
|---|---|---|---:|---:|---:|---:|
| R2-A1 | 2 | none | 266.00 | 207.192 | 58.81 | 3 |
| R2-B1 | 2 | timing | 189.87 | 131.714 | 58.16 | 3 |
| R1-B1 | 1 | timing | 130.57 | 72.631 | 57.94 | 30 |
| R1-A1 | 1 | none | 130.88 | 73.083 | 57.80 | 30 |
| R1-A2 | 1 | none | 131.39 | 73.343 | 58.05 | 30 |
| R1-B2 | 1 | timing | 131.32 | 73.133 | 58.19 | 30 |
| R2-B2 | 2 | timing | 190.76 | 132.131 | 58.63 | 4 |
| R2-A2 | 2 | none | 192.85 | 134.393 | 58.46 | 4 |
| Z-S1 | 2 | selector | 55.73 | 0.000 | 55.73 | 0 |

**残差は 57.80〜58.81 秒に収まる。** shard も計装の有無も cache 状態も、この量をほとんど動かさない。

`R2-A1` の wall 266.00 秒は最初の arm で、worktree の `__pycache__` が冷えている
(pytest rewrite cache 315 件は既存だが `.pyc` は 691 件へ増えた)。
それでも残差は 58.81 秒であり、cache の温度は最大 worker の稼働側に乗って残差には乗らない。

## C. 残差の 4 区間分解 (R2-B1)

```
A = 55.209 秒   session 開始 → 最繁 worker (gw0) の最初の report 開始
B =  0.035 秒   gw0 の report 窓内の非 report 時間
D =  0.000 秒   gw0 の最終 report 以降に他 worker が report していた時間
C =  2.913 秒   全 worker の最終 report → terminal が wall を測る時点
--------------
    58.156 秒 = 残差
```

`A+B+D+C == wall − R_w*` は望遠鏡和の**恒等式**であって検証ではない (段 3 のレンズ A の指摘)。
probe はこれを `algebraic_identity` として明記し、独立検査を別に持つ (§E)。

補助値 (親成分へ閉じる子成分):

```
B の子: within_probe_protocol_nonreport = 0.033412679 秒
        unclassified_outer_protocol     = 0.001535393 秒
C の子: 最終 report → worker 終了通知受信 = 0.224304357 秒
        worker 終了通知受信 → wall 終点   = 2.688499191 秒
```

残差の外側 (別表。内訳合計に入れない):

```
runner 起動 → pytest session 開始 = 0.657336538 秒
runner の外側 wall               = 191.620718365 秒
```

## D. A の内訳 — controller の event 時刻 (session 開始 = 0)

```
arm     48 worker 生成完了   48 worker ready   collection 完了 (最初〜最後)
R2-B1        3.127 秒            3.473 秒         51.010 〜 55.176 秒
R2-B2        3.17  秒            3.59  秒         50.55  〜 55.52  秒
R1-B1        3.17  秒            3.53  秒         50.23  〜 55.09  秒
R1-B2        3.23  秒            3.70  秒         51.00  〜 55.31  秒
```

R2-B1 の全体時刻:

```
-0.102  probe module import
-0.017  pytest_configure (controller)
 0.000  pytest_sessionstart (terminal がここから wall を測る)
 0.008  xdist_setupnodes
 0.040 〜 3.127  48 本の gateway 生成
 3.169  sessionstart 終了 / runtestloop 開始
 3.169 〜 3.473  48 worker が ready
 3.473  注入した環境変数を production の姿へ復元
51.010 〜 55.176  48 worker の collection 完了通知を controller が受信
55.209  最繁 worker の最初の report 開始 (= A)
187.184  runtestloop 終了
187.185  sessionfinish 開始
189.733  terminal summary 開始
189.869  terminal summary 終了 / sessionfinish 終了
189.87   pytest stdout の wall
```

**worker 起動 約 3.2 秒、全 collection 約 51.7 秒、終端 約 2.9 秒**である。

## E. 測定の質 (probe が自分で記録した検査結果)

```
probe の中立性     : 計装 arm と対照 arm の赤 nodeid 集合が一致 (shard-2 = 3 件、shard-1 = 30 件)
環境復元           : env_restore_failed=false、failed_process_count=0 (controller + 48 worker)
                     復元後の期待値 = PYTHONPATH unset / PYTEST_PLUGINS unset
時計               : 全 process の offset drift < 1.5 マイクロ秒 (停止閾値 5 ミリ秒)
report との一致    : probe の report duration と production report.json の差は最大 2 ナノ秒
独立検査           : controller と worker の report 件数一致、protocol span が report を被覆、
                     report phase が閉じている、report union が wall 内、
                     terminal 点が hook の上下限内 — すべて true
停止条件           : affinity 48、finished==selected、shard-1 と shard-2 の universe 一致
                     (19572 件、digest 814a47b3e4a7...)、hook 実行順が想定どおり — すべて充足
D1299 の 5 項      : tested_tip=dd5fddf04e、K=3、worker=48、
                     collection_digest=814a47b3e4a7...、growth_hold_effective_opt_in=false
外乱               : disturbed=true。理由は Lustre の kernel thread (kiblnd) の CPU 増分と
                     process 可視性の欠落。競合する PBS job は 0 件 (foreign_pbs_job_ids=[])
```

外乱フラグは立っているが、その内訳は kernel thread と可視性欠落であり、同居 job は検出していない。
**残差の値は 9 arm で 1 秒幅に収まっており、この外乱で結論は動かない。**

## F. 較正走 (テスト 0 件)

```
arm Z-S1 : wall = 55.73 秒
           選択 6524 / 完走 0 / universe 19572
           calibration_selected_is_nonempty = true
           calibration_finished_is_empty    = true
```

production の shard plugin が全 collection と割付と state 保存を終えた**後**に実行 item を空にした。
production の runner・plugin・scheduler・gate・selection・排他はいっさい変更していない。

## G. 再現手順

```bash
# 1) 集計 (既存 artifact から)
python3 <probe>/_t2097_residual_probe.py summarize \
  --root /work/1/SFC/tanab/.izanagi-acceptance-shards \
  --job-tag t2097-0_966271.nqsv \
  --out <出力>.json

# 2) 既存 14 走の残差再計算
python3 <probe>/_t2097_residual_probe.py recompute-archive \
  --root /work/1/SFC/tanab/.izanagi-acceptance-shards \
  --out <出力>.json

# 3) 計算ノードでの本走 (probe は repo 外に置く)
qsub -o <log>.stdout -e <log>.stderr <probe>/_t2097_residual_probe.pbs
```

生 artifact: `/work/1/SFC/tanab/.izanagi-acceptance-shards/t2097-0_966271.nqsv-*`
(arm ごとに `shard-N/{report.json,junit.xml,pytest.stdout,outer.json,probe/*.json}`)、
集計 `t2097-0_966271.nqsv-summary.json`。

## H. 失敗した 2 回の走行 (同じ罠を踏まないために残す)

```
job 966024 (bnode011): 1 arm で停止。
  probe を worktree 直下に置いたため
  test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes が
  未追跡 2 file を検出して赤。加えて openssl 由来の赤 3 件。

job 966221 (bnode013): 2 arm で停止。
  probe を repo 外へ移した後も、PYTHONPATH と PYTEST_PLUGINS を注入したため
  実行環境を検査するテストが落ちた。対照 3 赤に対し計装は 56 failed + 2 error。
  内訳は test_run_tests_preflight.py 47、test_pytest_failure_digest.py 4、
  test_codex_worker_launch.py 2、test_run_tests_testops_observation.py 2、
  test_mocc_trace_pair.py 2、test_mocc_trace_job_contract.py 1。
  併せて集計が 1 arm の失敗で停止し、残り 8 arm を失った。
```

3 回目 (966271) は、import 直後に環境変数を production の姿へ戻し、
arm 単位で集計を継続する形へ直してから走らせた。
