判定は **NO-GO** です。現プランで得られるのは有用な診断値ですが、D19 の意味で compare に使える between-run floor ではありません。

## 所見

### A1

- **id**: A1
- **主張**: 1 submission cohort の 8 allocation から得る量は、真正な between-run floor ではなく same-submission-cohort session-median CV である。
- **根拠**: D19 は same-window 測定を「真の run 間ドリフトを捉えない楽観的下限」として floor に採らなかった [docs/decisions.md:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:337)。独立単位を node / 時間窓 cluster で数える規定は D138 でなく D134(f) [docs/decisions.md:6542](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:6542) であり、D138 は P6 帰納契約の別件 [docs/decisions.md:6718](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:6718)。プラン自身も `time-window cluster=1` [plan.md:216](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:216)、`between_run_compare_floor.status=not-established` [plan.md:252](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:252) と認めている。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: certified 採否へ配線すれば時間ドリフトを欠いた低い閾値で偽 faster を増やし、配線しなければ floor 取得完了とは台帳に記録できない。
- **推奨**: 数値名を `same-submission-cohort allocation-session-median CV` に限定し、compare floor は必ず `not-established`、T-088/T-011 は未完のまま複数時間窓の裁定へ返す。

### A2

- **id**: A2
- **主張**: (P1) は import 閉包だけで task と成果物の同一性をすり替えており、generic rr50 診断を T-088/T-011 の official H1/H2 floor として扱えない。
- **根拠**: 現行 checkpoint は official guard 段階 3・4と実行 revision 束縛を floor 実測前 gate とする [docs/phase3.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3.md:118)。worklog (131) は T-011 と T-088 の重複、および下流 8 件を明記する [worklog (131):23](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/archive/worklog-phase3-0803-131-132.md:23)。事前登録が要求するのは H1/H2 の対象別 floor [docs/phase3-8c-preregistration.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8c-preregistration.md:109) であり、プランが測るのは rr50 一点 [plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:79)。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: prereg の H1/H2 欄は空のまま、official floor と材料レポートは判定不能のままなのに、T-088/T-011 だけが誤って閉じられうる。
- **推奨**: generic 診断を新しい別 task として明示するか、T-088/T-011 を名乗るなら official guard・revision binding・H1/H2 protocol に従うかの二択にする。

### A3

- **id**: A3
- **主張**: 8 セッションの CV 点推定は「保守側に丸めて floor に使う」には精度不足であり、時間窓成分については標本数が実質 1 なので推定不能である。
- **根拠**: 実装は標本標準偏差 `n-1` と算術平均から CV を作る [orchestrator/calibrator/analyze.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/analyze.py:220)、現行既定は 8 sessions [between_run_floor.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/between_run_floor.py:57)。i.i.d. 正規・小 CV という楽観的近似でも相対 SE は `1/sqrt(2(n-1)) = 26.7%`、標準偏差の概算 95% 区間は観測値の約 `0.66〜2.04倍`。D134 も効果量・検出力なしの固定標本数を拒否している [docs/decisions.md:6552](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:6552)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 低めに外れれば偽 faster、高めまたは上側信頼限界を採れば偽 tie が増えるが、same-window 欠落は系統的に低い側＝偽 faster 側へ倒す。
- **推奨**: 推定対象、許容相対誤差、信頼水準、効果量・検出力から cluster 数を事前決定する。1 wave 制約下で満たせなければ点推定を floor に昇格しない。

### A4

- **id**: A4
- **主張**: session-median の周辺 CV は、独立した baseline と variant の差の採否閾値そのものではない。
- **根拠**: 現行 `compare` の docstring 自身が、独立 2 測定の差の標準偏差は概ね `√2×CV` で、CV 直結は約 `0.71σ` にすぎないと認める [stability.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/stability.py:238)。official S8b 式は 2 セルの標準偏差を RSS で合成し、さらに 3% の wired minimum を採る [s8b_floor_stats.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/s8b_floor_stats.py:311)。D134 は複数推定値の単純な最大にも所定の被覆がないと訂正した [docs/decisions.md:6537](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:6537)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 将来 `raw_session_median_cv` をそのまま `noise_cv` に昇格すると、proof chain は存在しても採否意味論が過小閾値になる。
- **推奨**: artifact に「周辺 CV、差分散の推定式、被覆水準、採否閾値」を別 field で持たせ、単純 CV の consumer 配線を schema で禁止する。

### A5

- **id**: A5
- **主張**: (P2)/(P5) の pre/post pgrep と attestation は shared-system isolation を証明せず、ノード外の共通外乱を捉えない。
- **根拠**: probe は割当ノードから `pgrep -af ycsb_.*\.exe` を一度実行するだけ [runner.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/runner.py:171) で、canary は PID visibility を証明するだけ [runner.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/runner.py:264)。Pegasus は `Exclusive submit=OFF` [docs/pegasus-runbook.md:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/pegasus-runbook.md:45)。**推測**: 共有 fabric・ストレージ・電力/温度の実際の寄与量は未測定であり、同時 cohort 全体を同方向へ動かす common-mode は横断 CV から消える。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: common-mode を落とせば偽 faster、束自身が発生させた共有負荷を無差別に含めれば偽 tie が増え、どちらの floor か説明不能になる。
- **推奨**: 同一ノードの検出済み競合は事前規定で除外・fail-closed、将来の通常運用でも避けられない node/fabric/電力変動は複数 node・時間窓にまたがる母集団へ含める。除外する外乱は実走前に telemetry と理由コードを固定する。

### A6

- **id**: A6
- **主張**: (P4) は用途分離の指摘までは正しいが、「この between-run floor が 1 測定の品質ゲートに使えるか」という問いに別途測った within-run CV で答えるのはカテゴリーの取り替えである。
- **根拠**: D19 は within-run を 1 測定の品質、between-run を採否 floor と明確に分離する [docs/decisions.md:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:331)。現在の品質ゲート閾値は 5% [docs/roadmap.md:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/roadmap.md:215)。Pegasus artifact の 1.17% は `kind="within-run"` という推定値 [calibration JSON:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577) で、品質ゲート閾値そのものではない。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 台帳や材料レポートが between 値を品質判定へ誤配線するか、1.17% を新しい gate と誤認して再測定を過剰化する。
- **推奨**: 判定は「between floor の品質ゲート用途 = 非適用」と返し、各 5-rep session の `within_cv <= 5%` は別 assessment として記録する。

### A7

- **id**: A7
- **主張**: 親 brief の「飽和最小を満たした」という N2 は誤りであり、rr50 の 1M/48 点から別 workload/config/scale の floor へ外挿できない。
- **根拠**: 登録 artifact は `lower_bound_selected=true`、`saturated=false` [calibration JSON:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1603) で、binding は rr50/1M/48 のみ [calibration JSON:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1685)。roadmap は floor を env・records・threads・代表 workload/config の署名別に保存する [docs/roadmap.md:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/roadmap.md:315)。既存 linux 同窓 CV も rr5=0.666%、rr50=1.067%、rr95=0.110% と一様でない。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: rr50 の値で H1/H2 や別構成を丸めると、対象ごとに偽 faster/偽 tie の方向が変わり、prereg の対象別 floor は依然未充足になる。
- **推奨**: rr50 一点の適用範囲を exact signature に閉じる。official 成果物には最低 H1(rr80)・H2(rr20) の 2 workload 点、さらに承認済み per-pair 設計が要求する各比較セルが必要である。一束で診断点は測れても、時間分離 floor は成立しない。

### A8

- **id**: A8
- **主張**: プランは certified 採用を無条件に拒む点では後付けを防いでいるが、between CV が within CV を下回った場合の材料レポート上の意味を事前規定していない。
- **根拠**: linux の全 3 点で between は within 以下で、特に rr5 は 2.19% 対 0.67% [rr5 JSON:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:13)。D19 は median 集約と状態共有による現象として扱い、fresh 値を採らなかった [docs/decisions.md:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:337)。プランの policy 列挙にはこの関係の判定規則がない [plan.md:160](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:160)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: certified 選択は現案なら不変だが、低い結果を「Pegasus は安定」と肯定材料にする後付け余地が材料レポートと台帳に残る。
- **推奨**: 結果にかかわらず「below-within は invalid でも安定性証明でもない」「time cluster=1 なら compare status は常に not-established」を schema とレポータで固定する。

### A9

- **id**: A9
- **主張**: 親 brief の「Pegasus within 1.17% だから linux の between 3% は tie を過剰化しうる」という一般化は証拠になっていない。
- **根拠**: 親の推論は [brief.md:77](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/brief.md:77) にあるが、1.17% は bnode011 の 1 session・10 rep の within 値 [calibration JSON:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577)。D19 が塞いだ穴は、まさに within から between を推定して偽 faster を出す経路 [docs/decisions.md:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:335)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 「3% は過大」という未実証の方向づけが低い Pegasus floor 採用への圧力となり、将来の certified 受理集合を偽 faster 側へ広げる。
- **推奨**: これは仮説と明記し、Pegasus の cross-time between データが得られるまで 3% より高いか低いかを主張しない。

### A10

- **id**: A10
- **主張**: (P3) の新規 registered artifact は現 consumer から完全に孤立するため安全ではあるが、「将来参照できる floor の供給」という成果にはならない。
- **根拠**: 現 consumer は `calibration/between_run_noise_*.json` を glob し `between_run.cv` を読む [screening_driver.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/screening_driver.py:36)。Pegasus contract は既存 calibration の exact path/hash だけを束縛する [env_contract.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/env_contract.py:180)。新 prefix はどちらにも接続されず、プランも既存 consumer を不変とする [plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:305)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: certified は不変だが、台帳だけが「登録済み」を成功と数え、材料レポートや選択は参照不能という consumer 取り残しになる。
- **推奨**: diagnostic artifact は `observations/` 等へ置くか、registered に置くなら `eligible_for_compare=false` を validator と全 discovery consumer が強制する。consumer 設計なしに「供給済み」と記録しない。

### A11

- **id**: A11
- **主張**: (P5) の argv seam 再利用は transport/provenance の再利用にすぎず、測定の統計的同一性や official protocol 適合性を一切保証しない。
- **根拠**: 現 shell は rr50 calibrator の argv を JSON 化しているだけ [certify_calibration.sh:719](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/certify_calibration.sh:719)、`exec_calibrate.py` は文字列配列を検証して `execv` するだけ [exec_calibrate.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/exec_calibrate.py:23)。一方、承認済み official protocol は n=8/reps=5、H1/H2、RSS、wired minimum 3% を別契約として持つ [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/s8b-freeze/floor_protocol.json:1)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 強い hash/provenance が「正確に間違った estimand」を証明し、材料レポートの見かけの信頼性だけを高める。
- **推奨**: transport 変更より先に estimand・sampling frame・formula・状態遷移を hash 固定し、wrapper はその exact protocol だけを実行可能にする。

### A12

- **id**: A12
- **主張**: (P6) は「実装は一束制約の外」と広く解釈しているが、プランは実走前から真正な floor が一束に収まらないと確定しており、既に「足りなければ裁定へ返す」条件を満たしている。
- **根拠**: ユーザー裁定は不足時に拡大せず返す [brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/brief.md:12)。プランの総括も「統計的に使える真正な between-run floor は収まらない」と明記する [plan.md:386](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:386)。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 最大 16 node-hoursと広い実装差分を費やしても certified・prereg・材料レポートは前進せず、lower-bound registry だけが残る。
- **推奨**: 現段階で NO-GO を返し、「診断用 lower-bound artifact に 1 wave を使う価値があるか」を明示的に再裁定してもらう。

## 総括

- **(a) 判定: NO-GO。** 現プランは同一 submission cohort の診断値を安全に隔離する設計としては成立するが、D19 の between-run floor、T-088/T-011 の official H1/H2 成果物、または compare の採否閾値を取得しない。
- **(b) 最も重い所見 3 件**: A1（時間窓 cluster=1 で estimand 不成立）、A2（generic rr50 と official T-088/T-011 の成果物すり替え）、A3（n=8 の CV 精度不足かつ時間成分 n=1）。
- **(c) 1 ジョブ束で科学的に意味のある floor が取れるか: いいえ。** 取れるのは同一時間窓における node/build/session dispersion の診断的下限だけで、cold-boot・時間ドリフト・shared-system common-mode を含む採否 floor ではない。これは有用な観測値ではあるが、floor として certified 選択へ使ってはならない。

read-only の静的検査のみで、ファイル編集・pytest・ジョブ投入は行っていません。