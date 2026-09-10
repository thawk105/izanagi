## 所見

### [RB-1] CLI が Pegasus 用 campaign ID を捨て、既存 Linux 成果物を再び読む・上書きする

**深刻度:** BLOCKER  
**型タグ:** [ドリフト] [恒真ゲート] [テスト代表性]

**根拠:** 計測本体は `measurement_env="pegasus"` を加えた `campaign_cfg` を使いますが、CLI 後処理は元の `cfg` から旧 ID を再計算しています。

- 分離処理: [p3_s4_loop_trigger_gating.py:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:301)
- 計測側の正しい layout: [同:470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:470)、[同:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:575)
- CLI が旧 `cfg` へ戻る箇所: [同:698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:698)、[同:734](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:734)
- 旧 digest の上書き: [同:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:735)

既定 Pegasus ID は静的再計算で `…-75727902` ですが、CLI 後処理は既存の `…-3f72ecd5` を指します。旧 campaign には iteration=2、Linux WAL 12件、provenance、digest がすべて実在します。

**具体的な失敗シナリオ:** compute 上で fixture CLI を `--no-build` 付きで実行するだけで、本体は Pegasus layout に dry-pass を作る一方、後処理は旧 Linux WAL から digest を再生成し、既存の `s8a_trigger_loop_digest.txt` を上書きします。`--run-iteration` では旧 loop state/provenance が実在するため、Pegasus 側とは別の成果物を確認して rc=0 になり得ます。

**提案:** 解決済み `campaign_cfg` または `layout` を `main()` まで単一値で運び、再計算しないこと。compute CLI の正負例で旧 campaign 全 bytes 不変、出力・終了判定・digest が新 ID のみに属することを固定すること。

### [RB-2] 8c の下位入口から compute 運転でき、裁定 §4 に直接違反する

**深刻度:** BLOCKER  
**型タグ:** [恒真ゲート] [防壁の射程誤認]

**根拠:** compute 拒否は `run_trial()` にしかありません（[p3_autonomous_workload_trial.py:1029](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:1029)）。一方、

- `_finish_trial(..., site=...)` は無検査で `_run_workload` へ渡す: [同:651](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:651)、[同:682](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:682)
- `_run_workload(..., do_build=True, site=PEGASUS_COMPUTE)` は Pegasus campaign を構築する: [同:763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:763)、[同:782](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:782)
- その site を実 trigger へ渡す: [同:943](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:943)

`docs/failures.md` F72 は `_run_workload()` 自体を独立した強制入口として扱うよう明記しています（[failures.md:1513](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:1513)）。

**具体的な失敗シナリオ:** 他 module またはテストが `_run_workload` を直接呼び、valid providers と `site=PEGASUS_COMPUTE` を渡す。4 role と build/verify/bench が同一 compute process で動き、裁定が明示的に除外した「8c の compute 運転」が成立します。

**提案:** `site` 配線を8cから撤去するか、少なくとも `_run_workload` と `_finish_trial` の双方で `do_build && actual_site != OTHER` を拒否すること。直接入口の負例を追加すること。

### [RB-3] trigger の公開 `site` 引数で実 site を偽装でき、admission・attestation・campaign 分離を迂回できる

**深刻度:** BLOCKER  
**型タグ:** [恒真ゲート] [防壁の射程誤認]

**根拠:** 新しい keyword-only `site` は caller 値をそのまま信頼します。

- `run_one_iteration`: [p3_s4_loop_trigger_gating.py:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:456)、解決箇所 [同:470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:470)
- `drive_iteration`: [同:557](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:557)、解決箇所 [同:574](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:574)
- admission は渡された文字列だけを見る: [同:292](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:292)
- v2/attestation は `resolved_site == COMPUTE` の場合だけ: [同:488](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:488)

**具体的な失敗シナリオ:** 実 compute 上で `drive_iteration(..., site=OTHER)` を呼ぶ。quarantine reject なら build 不要で `linux-baremetal` WAL が書かれ、clean proposal なら attestation と v2 build を外して legacy 経路へ落ちます。これは親裁定 N3 が問題にした「注入 site の信頼」を driver 層に再導入しています。

**提案:** 計測 sink で `_current_site()` を解決し、caller から site 文字列を受け取らないこと。上流 site が必要なら actual site と一致検査する証跡としてのみ扱うこと。

### [RB-4] 兄弟 driver の拒否は sink に置かれておらず、複数の programmatic 呼び口と未列挙 driver が開いたまま

**深刻度:** MAJOR  
**型タグ:** [恒真ゲート] [テスト代表性] [防壁の射程誤認]

`p3_s4_loop.run_one_iteration`（[p3_s4_loop.py:623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop.py:623)）と sort 版（[p3_s4_loop_sort.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_sort.py:213)）は実計測入口で拒否しており、配置は妥当です。

一方、素通しできる呼び口は次です。

- coverage: `_build` / `_one_run`（[s8a_trigger_coverage.py:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py:102)、[同:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py:187)）。拒否は `main()` のみ（[同:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py:205)）。
- freq: `_run_freq`（[s8a_trigger_freq.py:77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_freq.py:77)）。拒否は `main()` のみ（[同:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_freq.py:117)）。
- sort/trigger sweeps: `_eval_one`（[s6_sort_sweep.py:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s6_sort_sweep.py:301)、[s8a_trigger_sweep.py:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_sweep.py:347)）。
- backoff screening: `_run_screened_workload`（[backoff_sweep.py:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/backoff_sweep.py:82)）。

さらに、`p2_2.run_workload`、`backoff_repro.run_workload`、`demo.main`、`p3_kickoff.main`、`p3_s4_red.main`、`sanity_silo.main` は compute 拒否なしで legacy `run_campaign` を呼びます。例: [p2_2.py:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p2_2.py:128)、[backoff_repro.py:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/backoff_repro.py:89)。

**具体的な失敗シナリオ:** compute 上で `_eval_one` を直接呼ぶと、quarantine reject は build 前に `ENV_TAG=linux-baremetal` で WAL へ入ります。未変更の P2 driver は既存 stock cache hit があれば、そのまま throughput を Linux 値として記録できます。

**提案:** `loop.run_campaign` で「actual compute かつ `env_contract is None`」を拒否し、`screening_driver.evaluate_candidate` にも同じ sink gate を置くこと。raw trace helper は各実行直前で拒否すること。

### [RB-5] critic digest は新しい環境次元を落としたまま、Pegasus 数値の実 consumer になっている

**深刻度:** MAJOR  
**型タグ:** [ドリフト] [防壁の射程誤認]

**根拠:**

- `GenomeLI` / `WorkloadDigest` に env がない: [critic/digest.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/critic/digest.py:38)、[同:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/critic/digest.py:71)
- loader は `r.env_tag` を読まず集約する: [同:192](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/critic/digest.py:192)
- renderer に env 表示がない: [同:478](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/critic/digest.py:478)
- trigger は workload `{}` で digest を作る: [p3_s4_loop.py:245](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop.py:245)
- 8c はその文字列を critic へ直接渡す: [p3_autonomous_workload_trial.py:967](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:967)

**具体的な失敗シナリオ:** Pegasus campaign の throughput が Linux digest と同じ外形で critic に入り、critic payload の他フィールドにも site/env がありません。campaign 分離は算術混合を防ぎますが、実 consumer に環境を伝えていません。

**提案:** digest 構築時に WAL の env_tag 一意性を検査し、schema・見出し・critic payloadへ明示すること。

独立確認では Layer3 は env 一意検査と `env_tags` 出力を既に持ち（[layer3_report.py:388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/layer3_report.py:388)）、`measurement_env` 追加も受理します。screening は Linux calibration 固定ですが、target compute 経路から未使用なので、RB-4 の gate が閉じるなら別 wave でよい範囲です。

### [RB-6] 新テストが配置・下位入口・安定 ID を検査せず、上記 BLOCKER をすべて通す

**深刻度:** MAJOR  
**型タグ:** [テスト代表性] [恒真ゲート]

**根拠:**

- 兄弟 driver テストは AST 上の呼出し個数だけを数え、支配関係・実行位置を検査しない: [test_p3_s4_loop_trigger_gating.py:437](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:437)
- compute campaign ID は「旧 ID と異なる」だけで、新 ID を固定せず、期待 key も production 定数自身から取る: [同:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:525)
- 8c compute 負例は `run_trial` と CLI だけ: [test_p3_autonomous_workload_trial.py:277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_autonomous_workload_trial.py:277)、[同:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_autonomous_workload_trial.py:667)
- 8c の `do_build=True` OTHER 正例はなく、no-build 正例しかない: [同:690](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_autonomous_workload_trial.py:690)

**具体的な失敗シナリオ:** rejection call を `main()` または dead branch に移しても AST count は緑です。`_CAMPAIGN_ENV_KEY` を別名へ変えて compute ID を漂流させても ID 不等号テストは緑です。8c build を全 site で拒否する変異も、現テスト集合では検出できません。

**提案:** compute CLI の実 layout/digest 統合テスト、`_run_workload` 直接負例、OTHER build 正例、全 lower sink の behavioral negative、literal key と exact compute ID の golden を追加すること。

## 子の報告との食い違い

- 単位 B の「campaign identity 分離を実装」は本体内部に限れば正しいですが、CLI consumer が旧 ID を再計算するため E2E では成立しません。
- 「8c compute capability を追加していない」はコードで反証されます。`_run_workload` / `_finish_trial` から到達可能です。
- 「兄弟 legacy driver は compute を拒否」は高位入口だけの主張です。下位 helper と未列挙 legacy caller が残っています。
- 「required attestation を実測直前に発火」は、caller が正直な `site` を渡す条件付きです。`site=OTHER` で迂回できます。
- 「既存 Linux campaign は env 分離で保護」は、CLI の旧 digest 書込によって成立しません。
- pytest 未実走・緑を主張しない、という両報告の記述はコード外事実として整合しています。本レビューでも pytest は実行していません。
- 静的検索上、`run_campaign` / `evaluate` の trailing optional 引数による未追随 caller と、full v2 digest literal の既存 pin は見つかりませんでした。
- production 差分に claim・reservation・lease・`/scr` namespace 実装はありません。`/scr` はテスト用 prefix 文字列だけです。scope 違反は8c compute配線です。

## GO / NO-GO

**NO-GO。**

RB-1〜RB-3 はそれぞれ独立した BLOCKER です。特に、compute の `--no-build` だけで既存 Linux digest を上書きし得るため、現状で target CLI を起動してはなりません。

## 総括

- Pegasus campaign 分離は内部では実装されたが、CLI 後処理が旧 campaign へ戻る。
- 8c compute 禁止は上位入口だけで、下位入口から実運転できる。
- caller 注入 site により admission・attestation・env 分離を偽装できる。
- legacy compute 拒否は sink に無く、programmatic 呼出しと未列挙 driver が残る。
- critic digest は Pegasus 環境情報を落としたまま実 consumer へ渡される。
- pytest は未実行であり、現テストも上記回帰を代表していない。