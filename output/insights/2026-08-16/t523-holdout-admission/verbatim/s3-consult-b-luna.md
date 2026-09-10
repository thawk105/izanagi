### 所見 1

- severity: must-fix
- 攻撃シナリオ: 第三の throughput producer が `run_once` を使わず、`subprocess.run([binary, "-ycsb_rratio=80", ...])` を直接呼ぶ。プラン自身がこの迂回を認めており、D の文書規約以外に自動封鎖がない。
- 根拠: [plan_v1.md:59](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:59)、[runner.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/runner.py:421)、[s1_verify_extime_calibration.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s1_verify_extime_calibration.py:260)、[s2_verify_calibration.py:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s2_verify_calibration.py:115)、[s3_lock_coverage.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s3_lock_coverage.py:87)
- 成果物影響: 第三 producer の holdout throughput が ledger 外で生成され、certified 選択と報告は観測回数を証明できない。
- 提案: 全 throughput subprocess を単一 gateway へ移し、直接実行を静的検査または許可リストで拒否する。そこまでしないなら「共通下位境界」という主張を標準 API 利用者だけへ狭め、裁定パッケージにする。

### 所見 2

- severity: must-fix
- 攻撃シナリオ: 正当な calibrator が `--workload ycsb_zipf_skew=0.8,ycsb_rratio=80,ycsb_rmw=0` を指定する。汎用 CLI と pipeline は任意 workload を受けるが、プランの rratio-only 判定は sealed admission を発行する経路なしに拒否する。
- 根拠: [brief.md:21](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/brief.md:21)、[brief.md:49](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/brief.md:49)、[plan_v1.md:45](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:45)、[plan_v1.md:76](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:76)、[cli.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/cli.py:134)、[cli.py:938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/cli.py:938)、[sweep.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/sweep.py:80)、[pipeline.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/pipeline.py:156)、[pipeline.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/pipeline.py:443)
- 成果物影響: brief の「正当な非 holdout 測定を 1 件も巻き込まない」と I5 が偽になり、既存 calibrator の受理集合が縮む。
- 提案: ratio だけで分類せず、freeze 由来 provenance と非 holdout 用の別 authority を設けるか、拒否を正式な受理集合変更として D96 と裁定へ戻す。tokenless bypass は作らない。

### 所見 3

- severity: must-fix
- 攻撃シナリオ: floor 実走後、`result.json`、journal、manifest、freeze、protocol をそのままにして ledger だけ削除または別 run の行へ置換する。既存 ratified verifier は ledger を要求せず、同じ result を受理する。
- 根拠: [plan_v1.md:187](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:187)、[s8b_ratified_freeze.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_ratified_freeze.py:197)、[s8b_ratified_freeze.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_ratified_freeze.py:223)、[s8b_ratified_freeze.py:2944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_ratified_freeze.py:2944)、[s8b_floor_stats.py:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_stats.py:409)、[s8b_verdict.py:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_verdict.py:1005)
- 成果物影響: certified result と下流 report は admission 行、観測回数、row digest を参照せず、proof chain は実走時だけの防壁に留まる。
- 提案: ledger path、raw hash、row digest を manifest/result/journal/receipt に束縛し、ratified closure、verifier、report、oracle が必ず検証する。結線を今 wave に入れないなら certified proof の scope 外として裁定化する。

### 所見 4

- severity: must-fix
- 攻撃シナリオ: 現在の protocol で floor を起動する。protocol 自体は存在するが、clean worktree には `output/claims` と `output/s8b-holdout-observations` がなく、claims は事前 provisioning 必須、ledger 親も既存親ディレクトリなしでは開けない。さらに Pegasus では crash 後の `--resume` が拒否される。
- 根拠: [floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/output/s8b-freeze/floor_protocol.json:1)、[holdout_freeze.json:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/output/s8b-freeze/holdout_freeze.json:620)、[env_contract.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/env_contract.py:252)、[s8b_floor_campaign.py:4179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4179)、[s8b_floor_campaign.py:4246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4246)、[layout.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/layout.py:139)、[campaign_claim.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/campaign_claim.py:170)、[plan_v1.md:175](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:175)
- 成果物影響: protocol authority は発行可能だが、初回起動は外部 provisioning 前提で、crash 後は claim と部分 ledger が残って floor が完了不能になる。
- 提案: ledger 親と claims root の provisioning を明示的な preflight にし、Pegasus 用の承認済み recovery/resume 経路を用意する。`allow_resume=False` のままなら resume を受理成果物として約束しない。

### 所見 5

- severity: must-fix
- 攻撃シナリオ: P1 が exact row を読み、lock を解放して token を生成する間に、P2 が同じ key の row を読み、同じく新 token を生成する。両者が測定 callback を呼べば、ledger は 1 行でも実測は 2 回になる。
- 根拠: [plan_v1.md:173](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:173)、[plan_v1.md:181](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:181)、[plan_v1.md:306](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:306)、[trial_registry.py:1614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/trial_registry.py:1614)、[trial_registry.py:1677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/trial_registry.py:1677)、[campaign_claim.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/campaign_claim.py:171)
- 成果物影響: ledger の一回性は token 発行回数や実測回数を拘束せず、I3 の「同一 key の二重観測拒否」が成立しない。
- 提案: token 発行を durable な `consumption_started` と原子的に結び、owner/fencing token を測定中も保持する。同一 key の resume 競合、別 clone、NFSv3 を含む試験を追加し、保証できない filesystem は fail-closed にする。

### 所見 6

- severity: should
- 攻撃シナリオ: `rratio=80` のまま `skew=0.8`、`rmw=1`、`records=2000000`、`threads=64` を指定する。プランはこれらを token と ledger row で exact 照合して拒否するため、generic holdout binding に skew/rmw/records/threads を実質追加している。
- 根拠: [plan_v1.md:45](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:45)、[plan_v1.md:75](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:75)、[plan_v1.md:147](/home/SFC/tanab/.claude/jobs/dev-wave-t523-holdout-admission/plan_v1.md:147)、[s8b_floor_contract.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_contract.py:302)、[s8b_floor_contract.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_contract.py:359)、[trial_registry.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/trial_registry.py:51)
- 成果物影響: T-525 の対象を未実装と宣言したまま新 admission の受理集合だけが全軸束縛になり、将来の T-525 で ledger key、既存行、certified 意味論の再定義が必要になる。
- 提案: 「floor cell の改変検出」と「holdout binding」を D で明確に分離する。全軸束縛を必要とするなら T-525 依存として裁定し、T-523 の未実装宣言を撤回する。

### 所見 7

- severity: should
- 攻撃シナリオ: caller が registry の `H1` を floor の `holdout_id` として渡す。実 freeze の cell key は `rr80` であり、同じ文字列を一つの `holdout_id` として join すると H1/rr80 の対応を誤るか、正当な cell を拒否する。
- 根拠: [brief.md:82](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/brief.md:82)、[trial_registry.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/trial_registry.py:50)、[trial_registry.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/trial_registry.py:52)、[s8b_floor_contract.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_contract.py:356)、[plan_v1.md:121](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:121)
- 成果物影響: ledger row と freeze cell の join が別 holdout を指し、certified 選択に誤った H1/H2 provenance を付ける。
- 提案: プランの `freeze_holdout_key`、`freeze_candidate_id`、`trial_workload_name` の分離を必須化し、互換的な曖昧 alias を ledger や下流 consumer に残さない。

### 所見 8

- severity: should
- 攻撃シナリオ: 一つの子で neutral leaf、append primitive、trial_registry 抽出、runner、5132 行の floor campaign、CLI 固定、docs、D、複数の境界テストを同時に変更する。局所テストが通っても、下流 ratified consumer の ledger 欠落を見逃せる構成である。
- 根拠: [brief.md:88](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/brief.md:88)、[plan_v1.md:191](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:191)、[plan_v1.md:195](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:195)、[plan_v1.md:203](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:203)、[plan_v1.md:215](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:215)、[plan_v1.md:247](/home/SFC/tanab/.claude/jobs/e047415d/tmp/wave-t523/plan_v1.md:247)
- 成果物影響: 8c の不変性、floor の一回性、下流の certified 閉包を一つのレビュー単位で保証できず、部分実装が正当化されやすい。
- 提案: 必須の downstream binding を含めて wave の完成条件を固定し、不要な trial_registry の機械的抽出は別 wave または裁定へ分離する。

## 総括

NO-GO。  
`run_once` は直接 subprocess producer を自動封鎖せず、ratio-only 判定は既存の汎用 calibrator を巻き込む。  
ledger は現状の verifier、ratified closure、report、oracle に結線されていない。  
Pegasus は resume 不許可で、crash 後の claim と部分 ledger が floor を止める。  
T-525 相当の束縛も実質的に入り、scope の裁定が必要である。静的検査のみで、pytest は実行していない。