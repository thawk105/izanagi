| 項目 | 判定 | 根拠 |
|---|---|---|
| K-1 | **partial** | A0/A1/A2/A3 は anchor 前に開始し最終 primary read 後に終了しており、read 間への境界サンプル混入はない。一方 A4 は30読み全体を1 subwindowにしており約1.5秒、他の5読み窓の約6倍。[probe:3843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:3843) |
| K-2 | **partial** | 観測できた migration は UNRESOLVED になるが、開始・終了CPUが同じなら全 self delta をそのCPUへ帰属する。途中で移動して戻るケースは endpoint 推定のまま。[probe:2195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2195) |
| K-3 | **closed** | A1 readとsubwindow IDを結合し、CPU別 pinned/control の件数・率を保存。因果3条件には加えていない。[probe:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:491) |
| K-4 | **partial** | randomized A1順、5 target×9群、各先頭read、余り3の実装は正しい。しかし `method_table.alpha` は依然 `alpha_without_rotation` の alias。[probe:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:297)、[probe:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:472) |
| K-5 | **partial** | 境界、errno、migration、交差、α fixtureは追加済み。ただしA4長窓と同一endpointへのreturn migrationを殺すfixtureがない。 |
| S6-01 | **partial** | 誤った「4 tick」根拠は除去されたが、旧5/6 arm判定は `SNAPSHOT_NONSELF_TICKS_MAX=5` として残り、テストも固定している。[probe:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39) |
| S6-02 | **partial** | A1/A2の長いarm合計は解消。A4だけ同型の長窓が残る。 |
| S6-03 | **partial** | 検出済みmigrationの捏造は解消したが、同一endpointへ戻るmigrationではendpoint帰属が残る。 |
| S6-04 | **closed** | incidental/OOB交差が保存される。[test:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1044) |
| S6-05 | **partial** | 正しい巡回αは存在するが、旧αがなお `alpha` 名で取得可能。既存テスト自身もそのkeyをαとして読む。[test:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:662) |
| S6-06 | **closed** | 2 CPUの3+3、5/6、四値errno、理由完全一致、INVALID含意は追加済み。[test:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:802) |

## VALID に必要な条件

実効 validator と finalization が要求する条件は次の全てである。

1. `observations`・`calibration`・`environment` がmappingで、A2 modeが厳密にbusy/sham。
2. allocated CPUが昇順・重複なしの48個、PBS job ID・compute-node marker・submission bindingが成立し、scheduler情報に不一致がない。[probe:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:772)
3. calibration pinと有限なmedian±tolerance bandが一致する。
4. `observations.exceptions` が空で、6 armが全て存在する。
5. primary readが30/240/30/50/80/15、計445。全read・anchorが48 CPU、正・有限MHz、期待affinity内のreaderである。[probe:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:809)
6. 各armの診断pre/postに `error` がなく `complete=true`。EACCES/EPERMは現在 `unreadable` なので成立可能。[probe:1791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:1791)
7. 各armのprocess visibilityが完全、isolation errorが空、帰属がCLEAN/UNRESOLVEDでCOMPETITORでない。[probe:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:875)
8. anchor数・配置、A0/A3 block、A1 seed順・by_pin・各CPU5読みが一致する。
9. A2は8 unique target、各busy/sham 5読み、anchorがbarrier後、各cooldown 1秒以上、busy child≥5 tick、sham≤1 tick、INCONCLUSIVE pairが3未満。
10. A3+A2 busy evidenceがVALIDで、全anchorがchild barrier後。
11. raw `/proc/cpuinfo` 3件とproduction parserが3/3一致する。
12. method-table・coresident・causal解析が例外を出さず、終了時hash再照合とprovenance収集が成功する。

静的に恒偽、すなわち実機で絶対成立しない条件は見つからなかった。ただし成功経路では84 subwindow、48 CPUで最大4032回の閾値機会がある。A1だけで2304回、A2で768回、A3+A2で144回であり、実測なしに偽陽性率は決められないため、この多重機会自体はbacklogとする。

## 所見

### S6R2-01

- **ID:** S6R2-01
- **主張:** K-1は窓長不変ではない。A4だけ30読みを1 subwindowへ入れている。
- **file:line:** [probe:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:53)、[probe:3843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:3843)、[probe:2230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2230)
- **失敗シナリオ:** A4 readerが1.5秒間同一CPUに留まり、任意CPUのresidualが累積3 tickになるとCOMPETITOR。`store_arm` が後続A3/A2を抑止する。
- **成果物影響:** A1までしか残らず、A2・A3とα/β/γ表が欠落してU-2を選べない。
- **強度:** **強・静的確定**
- **判定:** **must-fix**
- **最小の是正案:** 親の明示裁定でA4を6 block×5 primaryへ分け、各block前にdiscarded anchorを置く。primary 445は不変。read間への境界sample挿入では直さない。

### S6R2-02

- **ID:** S6R2-02
- **主張:** K-2の「endpointだけから推定しない」は未達。同一CPUへ戻るmigrationを検出できず、全deltaをendpoint CPUへ載せる。
- **file:line:** [probe:2173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2173)、[probe:2205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2205)、[probe:2654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2654)
- **失敗シナリオ:** unpinned readerが観測点ではCPU0、間隙でCPU1を3 tick走ってCPU0へ戻ると、self 3 tickをCPU0へ誤帰属し、CPU1 residual=3として偽COMPETITORになる。逆配置では真の3-tick競合を相殺できる。
- **成果物影響:** 正常jobの偽INVALID、または汚染jobの偽VALIDで因果結論を壊す。
- **強度:** **強・反例は静的に構成可能**
- **判定:** **must-fix**
- **最小の是正案:** singleton affinityを証明できるA1/A2だけper-CPU self帰属を許し、multi-affinity窓はendpoint一致でもUNRESOLVEDにする。return-migration fixtureを追加する。

### S6R2-03

- **ID:** S6R2-03
- **主張:** K-4の正しいαと並んで、旧方式がなお `method_table.alpha` として公開されている。
- **file:line:** [probe:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:459)、[probe:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:466)、[probe:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:472)、[test:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:662)
- **失敗シナリオ:** 既存consumerまたは親の表作成が従来どおり `method_table["alpha"]` を読むと、A3 quiet/A2由来の非巡回値をα列へ載せる。
- **成果物影響:** 完走しても2×3表のα列が別方式となり、U-2が誤方式を選ぶ。
- **強度:** **強・コードと既存テストで確定**
- **判定:** **must-fix**
- **最小の是正案:** `alpha` を `alpha_with_rotation` のaliasにするか削除し、旧値は `alpha_without_rotation` の一名だけにする。K-4を優先して既存テスト期待を更新する親裁定が必要。

### S6R2-04

- **ID:** S6R2-04
- **主張:** validity gateはsubwindowの個数、ID、readとの対応を検査しない。
- **file:line:** [probe:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:875)、[test:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1004)
- **失敗シナリオ:** `subwindows=[]` のままisolationをCLEANにしたartifactも、他構造が正常ならVALIDになれる。追加テストはtracker単体で、6/48/1/10/16/3の実走配置を固定していない。
- **成果物影響:** 将来のsampling脱落をgateが検出せず、単独性証拠なしでVALIDを発行し得る。
- **強度:** **強・静的確定**
- **判定:** **backlog**。現行producerは全armで呼出しており、今回の実走に直結する欠落経路はない。
- **最小の是正案:** expected subwindow ID/countと各readのID対応をvalidatorへ追加する。

### S6R2-05

- **ID:** S6R2-05
- **主張:** 判定機会は84 subwindow×48 CPU=4032へ増え、union型の偽陽性機会も増えた。
- **file:line:** [probe:2265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2265)、[probe:2497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2497)
- **失敗シナリオ:** A1の2304判定のどれか一つで短い3-tick burstが出ると `A1_pin_sweep:competing_process_detected`。
- **成果物影響:** 正常jobが途中停止して全表を失う。
- **強度:** **中**。機会数は確定、発火率は実測依存。
- **判定:** **backlog**
- **最小の是正案:** 初回実機で各subwindowの実時間、最大residual、発火CPUを保存・確認する。実測前にgateを緩めない。

### S6R2-06

- **ID:** S6R2-06
- **主張:** 「旧arm合計判定を削除」は文字どおりには偽。5/6判定がno-subwindow fallbackとして残る。
- **file:line:** [probe:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39)、[probe:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2471)、[test:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:164)
- **失敗シナリオ:** subwindowなしのcallerは、窓長に依存する5/6 arm aggregateで判定される。
- **成果物影響:** 現行成功producerでは `subwindows` が必ず非空なので今回の実機結果には作用しない。
- **強度:** **強**
- **判定:** **backlog**。K-1とK-5の親契約自体がこの点で衝突している。
- **最小の是正案:** fallbackを削除し、5/6 fixtureをsubwindow 2/3 fixtureへ一本化する親裁定を行う。

境界sampleはA0/A1/A2/A3ともanchor前、最終series後で、primary read同士の間にはない。445、arm順、0.95/0.05/46、canonical band、cooldown、hash再束縛、process argv/env非保存は差分上維持されている。pytest・self-test・実機実行は行っていない。

## 総括

- (a) **NO-GO**。
- (b1) A4だけ約1.5秒の長窓で、K-1の窓長不変性が破れている。
- (b2) 同一endpointへ戻るmigrationでper-CPU self帰属を捏造し、偽INVALID／偽VALIDが可能。
- (b3) `method_table.alpha` が依然非巡回αで、主要表のconsumer境界が二義的。
- (c) 実機で最初に発火しそうなのは `A1_pin_sweep:competing_process_detected`。通過後は長窓A4が次点。
- (d) 修正後は84 subwindowの個数・実時間・最大residual・migration、A1交差、A2/A3 child tick、巡回α9群/余り3を確認する。
- (d) 全445読み、value=819/unreadable=48/error=0、parser 3/3、submission/final hash、affinity復元、900秒以内完了も確認する。