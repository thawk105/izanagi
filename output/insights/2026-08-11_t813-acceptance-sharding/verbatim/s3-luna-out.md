## 判定

現行データでは、シャーディングは「受入待ち行列の正しい解」とは言えない。テスト部分の短縮シグナルはあるが、現行の k4 測定は受入全走と意味が一致せず、分割不変性・資源不変性とも成立していない。

### 所見1 — lease 占有時間の直列部分が過小評価されている

**(a) 主張**

受入 lease のサービス時間は「pytest の約9分」だけではない。概念的には次の形になる。

```text
S(k) = F_fixed + U_unshardable + (T_test - U_unshardable) / k + H(k)
```

ここで、`F_fixed` は取得後の同期・preflight・land・release、`U_unshardable` は分割不能なテスト、`H(k)` は分割に伴う dispatch・collection・queue・干渉である。

シャーディングで直接短縮できるのは、pytest 実行のうち、別 shard に安全に分けられる部分だけである。

**(b) 根拠**

取得後に、main の再読込、behind/overlap 確認、`merge --no-ff --no-commit`、commit、再確認を行う。[`tools/dev_wave_wait.py:811–865`](tools/dev_wave_wait.py:811)

その後、受入コマンドを実行し、成功時は lease を保持したまま land に進む。[`tools/dev_wave_wait.py:866–919`](tools/dev_wave_wait.py:866)

受入全走には、削除 preflight、RuleOps preflight、submodule 処理が含まれる。[`tools/run_tests.py:591–763`](tools/run_tests.py:591)

dispatch には probe/import、qsub、queue 待ち、結果・会計ファイル回収がある。[`tools/pegasus/dispatch_compute.py:539–613`](tools/pegasus/dispatch_compute.py:539)、[`tools/pegasus/dispatch_compute.py:1371–1394`](tools/pegasus/dispatch_compute.py:1371)、[`tools/pegasus/dispatch_compute.py:1461–1773`](tools/pegasus/dispatch_compute.py:1461)

成功後も provenance 監査、fold、land、lease release が残る。[`tools/dev_wave_land.py:2099–2423`](tools/dev_wave_land.py:2099)、[`tools/wave_land_window.py:747–784`](tools/wave_land_window.py:747)

受入全走の実測は `535.64–566.42秒`、中央値約546秒である。[`facts.md:57–61`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:57)

一方、現在の分割単位では、最長 shard 内のテストが `263.08秒`、base では最長テストが `303.96秒` ある。[`measurements.md:47–64`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:47)

したがって現在の file/group atomization を前提にしても、

```text
S(∞) >= F_fixed + 約263秒
```

であり、`k→∞` でゼロにはならない。さらに `H(k)` は増加し得る。

**(c) 反証条件**

同一 tip・同一環境で、取得から release までの timestamp を段階別に採取し、`k` 増加により preflight、dispatch、receipt、land の各区間まで実際に短縮されること、かつ最長 263 秒級のテストも分割可能であることが確認されれば、この下限評価は修正される。

**(d) 自己判定**

`T_test`、最長テスト、直列処理の存在は **real**。各固定区間の典型所要時間はまだ未計測なので、その合計への適用は **speculative**。

---

### 所見2 — 段2の Amdahl 数値は、仮定内でも下限を落としている

**(a) 主張**

段2は `900–1500秒` の占有から `546秒` を引き、非テスト部分を `354–954秒` として、4分割時を `490.5–1090.5秒` と見積もっている。[`s2-plan.md:145–148`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:145)

しかしこれは `546/4` としており、分割不能な約263秒を4分割している。仮に段2の `F_fixed=354–954秒` が正しいとしても、Amdahl 補正後の理想 k4 は、

```text
F_fixed + 263 + (546 - 263) / 4
= 約688–1288秒
```

となる。したがって、段2の `490.5–1090.5秒` は、約197秒分の不可分な critical path を取り落としている。

**(b) 根拠**

親 brief 自身が「15–25分のうち全走は約9分」としている。[`brief.md:30–36`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/brief.md:30)

しかし `15–25分` と `546秒` は同一 run の paired measurement ではない。また、段2の `354–954秒` は、古い占有時間レンジから現在の受入全走中央値を引いた差分にすぎない。[`s2-plan.md:145–148`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:145)

実測 k4time でも pytest makespan は `271.87秒` で、理想的な `1/4` ではなく、すでに約263秒の下限付近で飽和している。[`measurements.md:19–28`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:19)

**(c) 反証条件**

同一 run の占有時間を `F_fixed` と `T_test` に分解し、複数の意味的に green な paired run で、最長 group/test が実際に複数 shard に分割できることを測れば、上記の補正値を否定できる。

**(d) 自己判定**

Amdahl の算術誤りと未対応の最長テストは **real**。`354–954秒` を固定部分として使えるかは paired 測定がないため **speculative**。

---

### 所見3 — 「ポイントほぼ不変」は親の測定からは成立しない

**(a) 主張**

1 dispatch = 1 ノード全体という前提では、k4 の node×time はほぼ不変ではない。

**(b) 根拠**

測定値は次の通りである。

| arm | makespan | PBS elapsed の合計 | base 比 |
|---|---:|---:|---:|
| base | 539.83秒 | 546秒 | 1.00 |
| k4count | 437.78秒 | 758秒 | 1.39 |
| k4time | 271.87秒 | 634秒 | 1.16 |

[`measurements.md:30–45`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:30)

k4count は試験数を均等化しても shard の elapsed が `444/233/59/22秒` と大きく偏り、k4time でも `277/188/67/102秒` である。[`measurements.md:6–28`](../../../../dev-wave-jobs/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:6)

段2自身が ±10% を「ほぼ不変」の判定基準にしているが、k4time はすでに +16%、k4count は +39% である。[`s2-plan.md:214–221`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:214)

さらに、base・k4count・k4time のいずれも、import error、receipt 競合、またはその双方により rc0 の受入全走ではない。[`measurements.md:86–132`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:86)

**(c) 反証条件**

同一 commit/tree、同一 acceptance set、同一 gate、同一 worker 総数で、少なくとも5 paired blockを実行し、すべて semantic green、かつ `sum(nodes × charged elapsed)` の信頼区間が ±10% 内に収まれば、ポイント不変の主張は成立し得る。

**(d) 自己判定**

表の数値と +16%/+39% は **real**。semantic failure を除いた場合の真の resource overhead はまだ **speculative**。

---

### 所見4 — 現行 k4 は「1 lease の中の分割」ではなく、4つの独立 dispatch に近い

**(a) 主張**

現行測定を、そのまま lease 占有時間の短縮値として使うことはできない。現在の dispatcher は1 requestにつき1 PBS job、1ノードである。4 shard を起動しても、1つの受入 coordinator が保持する lease 内の coordinated execution にはなっていない。

**(b) 根拠**

dispatcher は receipt 上 `nodes=1` を作り、PBS script と qsub も `-b 1` である。[`tools/pegasus/dispatch_compute.py:1356–1367`](tools/pegasus/dispatch_compute.py:1356)、[`tools/pegasus/dispatch_compute.py:433–504`](tools/pegasus/dispatch_compute.py:433)、[`tools/pegasus/dispatch_compute.py:1461–1486`](tools/pegasus/dispatch_compute.py:1461)

現行実装では compute 上の affinity は48 CPUで、明示した `-n48` は各 shard にそのまま適用される。[`orchestrator/campaign/site_policy.py:100–127`](orchestrator/campaign/site_policy.py:100)、[`tools/run_tests.py:1816–1868`](tools/run_tests.py:1816)

つまり k4 の現在形は、概ね4ノード・最大192 xdist worker の予約である。段2の「総 worker 数48、k4なら各12」は将来の単一 controller 設計であり、現在の測定 arm ではない。[`s2-plan.md:132–143`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:132)

また、5 job 同時起動時には dispatch wall が791秒、PBS elapsed は444秒で、queue 待ちだけで約350秒相当の差が出ている。[`measurements.md:134–138`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:134)

PBS queue 待ちはノード課金時間には入らないが、lease を取得した後の dispatch 待ちなら利用者の待ち時間・lease 占有時間には入る。したがって queue wait は「ポイント」と「待ち行列 latency」で別々に扱う必要がある。

**(c) 反証条件**

1 coordinator が lease を保持し、k node に対して同一 acceptance identity の子 job を起動し、結果を一度だけ typed merge する実装を用意したうえで、queue wait・child runtime・receipt 回収・release までを測定すれば、この指摘は否定できる。

**(d) 自己判定**

現行 dispatcher の1 job/1 node、queue 待ちの差、将来案との非同値性は **real**。coordinator 実装後の queue 挙動は **speculative**。

---

### 所見5 — xdist の固定費と group 偏りが、k 増加の効率を押し下げる

**(a) 主張**

各 shard を `-n48` で実行すると、shard が小さいほど worker 起動・import・collection の固定費が支配的になる。`--dist loadgroup` は group を shard 間で再分割せず、group の偏りを温存する。

**(b) 根拠**

`run_tests.py` の `_NPROC_CAP=32` はデフォルト nproc の上限であり、明示的な `-n48` を縮小する仕組みではない。[`tools/run_tests.py:53–62`](tools/run_tests.py:53)、[`tools/run_tests.py:206–220`](tools/run_tests.py:206)

xdist が有効なら `--dist loadgroup` が付与される。[`tools/run_tests.py:367–385`](tools/run_tests.py:367)

全体 collection は `8725 items / 163 files` で13.56秒かかる。[`facts.md:36–42`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:36)

k4count の最小 shard は pytest 16.46秒であり、collection だけで約82%を占める。小 shard では worker 起動・module import の比率がさらに上がる。

また、real-repo group は13ファイル・44 itemにまたがり、`conftest.py` が group を付け、collection finish で優先配置する。[`facts.md:44–55`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:44)、[`orchestrator/tests/conftest.py:123–282`](orchestrator/tests/conftest.py:123)

2026-08-09の旧測定では48 worker相当の並列効率が24.5%、今回の qstat でも平均使用CPUは shard で約6 coresに留まる。[`facts.md:63–67`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:63)、[`measurements.md:66–71`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:66)

さらに、shard ごとの collection が変わることで、`tests`、`codex_roles` の import error が発生する。これは `test_reflux_ir.py` の sys.path side effect に依存していたためである。[`measurements.md:86–118`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:86)

**(c) 反証条件**

各 shard で `-n48` を維持したまま、collection/import/worker-startup の時間が shard 数に比例せず、group の最大単位も均等化され、CPU利用率と makespan が k に応じて安定して改善することを、semantic green の paired run で示す必要がある。

**(d) 自己判定**

固定費、group atomicity、24.5%/平均6 cores、import failure は **real**。将来の hermetic な collection 実装後の効率は **speculative**。

---

### 所見6 — 現在の suite は shard partition invariance を満たしていない

**(a) 主張**

シャードごとに `run_tests.py` を呼ぶ設計では、受入全走の gate と観測対象が変わる。

**(b) 根拠**

ファイルリスト形状は `_is_acceptance_run=False` になり、削除・RuleOps gate は no-op、その他の gate も warning 扱いになる。[`measurements.md:1–4`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:1)、[`tools/run_tests.py:505–563`](tools/run_tests.py:505)

一方、段2は acceptance gate `594/632/705/1677` を coordinator で一度だけ実行する設計を必要条件としている。[`s2-plan.md:83–92`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:83)

k4count では collection union が `8725` ではなく `8716` となり、10 tests が collection error の影響を受けている。[`measurements.md:73–84`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:73)

同じ worktree の `output/pegasus-dispatch` へ複数 dispatch が書くため、snapshot/receipt 競合も発生している。runbook は同一 worktree の受入隣接実行について、output・git/index・tracked/untracked の干渉を禁止している。[`docs/pegasus-runbook.md:936–957`](../../../../docs/pegasus-runbook.md:936)

**(c) 反証条件**

canonical collection の ordered multiset、collection error、skip/marker、artifact set、typed return code を coordinator が取得し、全 shard の union が canonical acceptance と完全一致することを、実際に検証できれば否定できる。

**(d) 自己判定**

現行 arm が acceptance semantics を満たしていないことは **real**。修正後に完全一致できるかは **speculative**。

---

### 所見7 — 待ち行列の改善境界は、到着率が未計測のためまだ決められない

**(a) 主張**

lease が1本のままなら、シャーディングが効くのは、短縮後のサービス時間が到着率に対して安定条件を満たす領域だけである。

M/G/1 の近似では、

```text
ρ = λ E[S]
Wq = λ E[S²] / (2(1 - ρ))
```

であり、`ρ` が1に近い場合は少しの短縮でも queue が大きく縮むが、`ρ` が十分小さい場合は queue がほとんど存在せず、シャーディングの効果も小さい。

**(b) 根拠**

元の裁定パッケージには、同時点で3待ち、待ち時間 `92分・67分・1分`、handoff 24、worktree 14という snapshot がある。[`question-lease-serialization/ruling-package.md:11–28`](../../../../dev-wave-jobs/question-lease-serialization/ruling-package.md:11)

worklog には「今日6 land のうち3–4 acceptance run が無効化された」という記録があるが、観測時間幅がない。[`docs/worklog.md:2955–2979`](../../../../izanagi/docs/worklog.md:2955)

したがって `λ`、burstiness、同一波の再試行率は求められず、queue の短縮率を数値保証できない。

観測上の占有 `900–1500秒` を仮にサービス時間とみなすと、単一 lease の処理能力は約 `2.4–4.0 waves/hour`。段2の固定部分を仮定し、Amdahl 補正後の理想値 `688–1288秒` を使っても約 `2.8–5.2 waves/hour` 程度であり、4倍処理能力にはならない。

**(c) 反証条件**

少なくとも数週間分の wave 到着時刻、lease acquire 時刻、service start/end、再試行、land failure を記録し、`λ` と `S` の分布を得れば、効く領域と効かない領域を定量化できる。

**(d) 自己判定**

待ち行列式と安定条件は **real**。現在の到着率とシャーディング後の queue 短縮量は **speculative**。

---

### 所見8 — T-810 は wall-clock 判定の結論を条件付きにする

**(a) 主張**

シャードの node placement によって、時間上限テストや実時間判定の余裕が変わる可能性がある。したがって、wall-clock、flake rate、points の結論は T-810 の測定 protocol に条件付きである。

**(b) 根拠**

repo 内には次の実時間依存面がある。

| 対象 | 根拠 |
|---|---|
| RuleOps preflight `<60s`, `<45s` | `orchestrator/tests/test_ruleops.py:3444–3451` |
| dev-waves protocol `<0.15s` | `orchestrator/tests/test_dev_waves_protocol.py:256–312` |
| worker stop `<5s`, `<2s` | `orchestrator/tests/test_dev_waves_worker.py:188–198, 378–385` |
| checker `<1s` | `orchestrator/tests/test_dev_waves_checker.py:304–317` |
| login headroom `<0.5s` | `orchestrator/tests/test_login_headroom.py:982–1001` |
| land lock `<2s` | `orchestrator/tests/test_dev_wave_land.py:1223–1245` |
| s8c subprocess timeout 180s | `orchestrator/tests/test_s8c_preregistration_invariant.py:28–65` |
| worker launcher の wall contract | `orchestrator/tests/test_codex_worker_launch.py:949–960`、`tools/codex_worker_launch.py:1402–1419` |

RuleOps は real-repo serial group に含まれる。[`orchestrator/tests/conftest.py:182–184`](orchestrator/tests/conftest.py:182)

今回の probe は複数 bnode で green だったが、各 arm と node が一度ずつ程度であり、node effect と treatment effect を分離していない。[`measurements.md:140–148`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:140)

T-810 の元の対象は CC の N-node protocol で、pytest の node差にその結果を直接移すことはできない。[`docs/archive/worklog-phase3-0811-418.md:612–628`](../../../../docs/archive/worklog-phase3-0811-418.md:612)

**(c) 反証条件**

同一 pytest arm を node と時刻に対して randomized/Latin-square 配置し、各 wall-clock gate の残余マージン、flake、charged elapsed を測れば、node placement の影響が無視できることを示せる。

**(d) 自己判定**

該当する timeout/wall-clock 面の特定は **real**。node差が結論をどの程度変えるかは **speculative**。なお T-810 の結果にかかわらず、現行 import/collection 非同値性は否定できない。

---

### 所見9 — 分割より費用対効果が高い代替がある

**(a) 主張**

最も費用対効果が高い第一候補は、T812 の自己保持 lease deadlock を除去すること。通常系の次点は、実測で支配的な遅いテストの改善である。

**(b) 根拠**

元の裁定は、lease 占有縮小を第一方針とし、T812 deadlock、docs-only 受入除外、遅いテスト改善を候補にしている。[`question-lease-serialization/ruling-package.md:71–80`](../../../../dev-wave-jobs/question-lease-serialization/ruling-package.md:71)

worklog には T812 が約18–20分の無効占有を回収する対象として記録されている。[`docs/worklog.md:2418–2421`](../../../../izanagi/docs/worklog.md:2418)

遅いテストについては、`test_s8b_oracle_driver.py` と `test_codex_reasoning_ab.py` の2ファイルだけで serial sum の約63%を占め、200秒超のテストが9本ある。[`measurements.md:47–64`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:47)

collection/import 固定費も、全走で13.56秒あり、分割すると shard ごとに繰り返される。[`facts.md:36–42`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:36)

受入対象の縮小は効果が大きくても I1/I2 を破るため、現行の意味を維持する改善とは扱えない。[`brief.md:18–23`](../../../../dev-wave-jobs/dev-wave-t813-shard-eval/brief.md:18)

**(c) 反証条件**

T812 の発生頻度が極めて低い、遅いテストの改善コストが高すぎる、または profiling により時間が外部 subprocess にあることが示されれば、優先順位は変わる。docs-only 適用率と cache hit rate も実測が必要である。

**(d) 自己判定**

T812 の無効占有と遅いテストの集中は **real**。それぞれの改善で平均 queue が何分縮むかは **speculative**。

## 総括

- 分割は待ち行列問題の正しい解か: **現状では否。lease が1本のままの混雑に対する条件付きの補助策であり、semantic green と到着率の実測が先。**
- 費用対効果で最も高い手段: **T812 の自己保持 lease deadlock 修正。追加ノードなしで、発生時の18–20分級の無効占有を除去できる。**
- 親 brief と段2プランの誤り: **「9分を1/kで縮める」「ポイントはほぼ不変」「k4で490.5–1090.5秒」という見積りは、不可分な約263秒、反復固定費、queue待ち、意味的不変性を落としている。**

実装・編集・commit・テスト実行は行っていない。