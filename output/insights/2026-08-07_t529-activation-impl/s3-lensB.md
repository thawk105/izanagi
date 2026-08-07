## must-fix

### 1. P1/P2 は D196 の blocker を解除していない

[s1-brief.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s1-brief.md:40) と [s2-plan.md:357](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:357) は「consumer 配線完了＝D196 前提充足」「DW-G04 不充足は既知なので無視」と一般化している。しかし D196 は発火する正例を書けない場合の実装保留まで決定しており、DW-G04 も既存 artifact path または計測 ID が無ければ設計メモに留めると明記する。[decisions.md:9490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/docs/decisions.md:9490)、[core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/docs/dev-wave/core.md:57)

T-574 の inventory が「追加配線先 0 件」とした部分は成立するが、それ自身が「発火正例は未充足」と結論している。[T-574 README.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/output/insights/2026-08-06_t574-world-expansion/README.md:48) ユーザー裁定後の現行台帳も R1 と DW-G04 を残 blocker としている。[worklog.md:3022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/docs/worklog.md:3022) temp repo の合成 g2 は DW-G04 が要求する「既存 production artifact」ではない。

**未修正時の成果物影響:** 試行台帳の依存・完了参照だけが「活性化権限実装済み」へ進む一方、production の certified 選択受理集合は `official` 拒否／`no-active` のままで、合成試験だけが発火証拠として残る。

### 2. 実測 5 は R1 と T-529 裁定 (1) を誤って同一視している

[s1-brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s1-brief.md:31) は T-529 裁定 (1) が R1 を回答済みとするが、両者の択一は異なる。

- T-529 (1) は activation record の trust root を reviewed commit とするか外部署名にするか、である。[rulings inbox:263](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:263)
- R1 は artifact に記録された hash だけで、当時 active だった証明なしに世代を選んでよいか、である。[historical README.md:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/output/insights/2026-08-06_t574-historical-resolver/README.md:59)

プランは全 candidate を index 化する historical resolver を維持するため、record が g1 のままでも registered g2 は `resolve_by_contract_sha256()` で解決可能である。[s2-plan.md:160](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:160)、[env_contract.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:329) これは未裁定の R1(a) を暗黙採用している。

**未修正時の成果物影響:** historical freeze／oracle report の受理集合が「registry にはあるが一度も active でなかった g2」を記録した artifact まで拡大し、calibration・proof 参照が未発効世代へ結合される。

### 3. floor の公式経路は gate より前に書き、Python gate 自体へ到達しない

プランは [s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:166) で `_run_campaign_core()` 内を最初の write としている。しかし公式入口の外側には次の writer がある。

- `submit_floor.sh` は submission directory と capture files を作る。[submit_floor.sh:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/submit_floor.sh:274)、[submit_floor.sh:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/submit_floor.sh:296)
- `floor_campaign.sh` は attempt/job-staging、prologue、driver stdout/stderr を Python 起動前に書く。[floor_campaign.sh:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/floor_campaign.sh:88)、[floor_campaign.sh:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/floor_campaign.sh:882)
- 同 wrapper は `--mode official` で起動するが、Python CLI は `run_campaign()` より前に official を拒否する。[floor_campaign.sh:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/floor_campaign.sh:894)、[s8b_floor_campaign.py:3472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_floor_campaign.py:3472)

したがって予定された receipt gate は pilot/direct-test 経路にしか発火せず、公式経路では名ばかりである。wrapper と [test_pegasus_floor_tools.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/tests/test_pegasus_floor_tools.py:843) も実装単位から漏れている。

**未修正時の成果物影響:** activation 拒否時にも floor submission、job-staging、`job-result.json` の参照が試行台帳へ残り、certified floor の受理集合は空のままなのに「floor は pre-write 保護済み」と記録される。

### 4. T-126 も submitter／PBS wrapper が Python gate より先に永続化する

[s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:170) は `QualificationRoot.issue()` を最初の write とするが、実際には以下が先行する。

- submitter が qualification namespace、submission directory、capture、series ledger を作る。[submit_t126_qualification.sh:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/submit_t126_qualification.sh:288)、[submit_t126_qualification.sh:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/submit_t126_qualification.sh:301)
- PBS wrapper が job-staging、source-stage evidence、driver stdout/stderr を書いた後で driver を起動する。[t126_qualification.sh:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/t126_qualification.sh:75)、[t126_qualification.sh:719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/t126_qualification.sh:719)、[t126_qualification.sh:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/t126_qualification.sh:736)

裁定 (5) の writer 閉包へ送るなら、T-126 を「最初の write 前に保護した入口」と数えてはならない。保護対象なら両 shell を scope と所有一覧へ追加する必要がある。

**未修正時の成果物影響:** activation 拒否前に submission・series ledger・job-staging・prologue evidence が生成され、最終 qualification result は無くても試行台帳の attempt 集合と参照が増える。

### 5. `env_attestation` の述語再利用は既存 import 順で循環初期化になる

プランは `env_contract` の module 初期化中に activation state を load しつつ、較正検査を `env_attestation.load_verified_calibration()` から再利用する。[s2-plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:91)、[s2-plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:133)

しかし `env_attestation` は module 初期化時に `env_contract` を importする。[env_attestation.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_attestation.py:22) `s8b_oracle_report`、T-126、silo、および複数試験は `env_attestation` を先に importするため、その途中で `env_contract → activation loader → 部分初期化中の env_attestation.load_verified_calibration` となり、関数定義前に到達する。[s8b_oracle_report.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_report.py:36)、[t126_driver.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/qualification/t126_driver.py:27)、[test_env_attestation.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/tests/test_env_attestation.py:25)

共有 leaf への述語抽出、または `env_attestation` 側の遅延 import が必要であり、同ファイルと関連試験を単位 A に含める必要がある。

**未修正時の成果物影響:** oracle report・T-126・silo 等が import 時に停止し、それらの report／qualification／試行台帳の受理集合が空になる。

### 6. import-time HEAD loader は T-126 の git-archive 実行面で authority root を得られない

プランは `env_contract` import 時に HEAD tree/blob を読むが、`repo_root=...` の決定方法を未定義のままにしている。[s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:71)、[s2-plan.md:137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:137)

T-126 は HEAD を `/scr/.../source` へ `git archive` 展開し、その `.git` を持たない source stage から driver を import・実行する。[t126_qualification.sh:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/t126_qualification.sh:437)、[t126_qualification.sh:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/t126_qualification.sh:736) `--git-repo-root` は import 完了後にしか解釈できない。[t126_driver.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/qualification/t126_driver.py:23)

authority Git root と実行 source/calibration rootを分離して明示注入するか、activation load を CLI 引数取得後へ遅延しなければ実装できない。

**未修正時の成果物影響:** T-126 の全 production run が activation state 読込みで停止し、qualification series result／final receipt の受理集合が空になり、wrapper の失敗 artifact だけが残る。

## should-fix

### 7. P3 の activation reachability が S8c evidence 層に結線されていない

[s2-plan.md:169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:169) は P3 を保護対象とするが、S8c condition 12 は `lookup`、`attest_and_build_receipt`、reservation だけを要求・検査し、新 activation API を知らない。[s8c_preregistration_evidence_contract.v1.json:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431)、[s8c_preregistration_evidence.py:575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8c_preregistration_evidence.py:575)

このままでは P3 の activation 呼出しを削除しても C12 の判定は同じである。activation receipt を C12 の代替と混同せず、独立 reachability と negative control を追加するか、「C12 証拠ではない」と明記すべきである。関連する [test_s8c_preregistration_predicates.py:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/tests/test_s8c_preregistration_predicates.py:278) も単位 B から漏れている。

### 8. activation 例外の境界翻訳が未定義

新 module は `ActivationStateError` を定義する一方、六入口の翻訳表は `EnvContractError` だけを前提とする。[s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:68)、[s2-plan.md:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:175)

`admit_current()`、`issue_activation_receipt()`、`assert_current_activation()` が内部例外を必ず `EnvContractError` へ変換するのかを固定しないと、report の rc 2、oracle の `status="refused"` 等が uncaught traceback に変わる。

### 9. env-neutral AST 閉包に新 authority module が入っていない

既存の env 固有 literal 防壁は対象ファイルを列挙するが、当然ながら新設予定の `env_contract_activation.py` は含まれていない。[test_env_contract.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/tests/test_env_contract.py:78) プランの test 更新一覧にもこの追加がない。[s2-plan.md:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:225)

grandfather は exact contract hash 一件に限定する設計なので、新 module を env-neutral 検査対象へ追加し、env 名による特例へ変異していないことを固定すべきである。

## nit

### 10. selector は実行入口ではなく proof-chain producer と明記した方がよい

実 producer を `s8b_prediction_runner.seal()` と訂正した点自体は正しい。[s2-plan.md:171](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation-impl/s2-plan.md:171) ただし節名の「六つの入口」は、selector を workload execution admission と誤読させる。`5 実行・適格性 writer + oracle report + selector proof-chain producer` のように層を明記すると、入口被覆率の過大解釈を避けられる。

## 総括

判定は **NO-GO**。T-574 の「追加 historical consumer は 0 件」という inventory と、oracle report／selector の入口訂正、silo・`loop.py` の非保護宣言は成立している。

一方、R1 と DW-G04 は未解決であり、floor/T-126 には gate 前 writer が実在する。さらに import 循環と T-126 の git-archive 実行面により、単位 A の authority loader は現プランどおりには起動できない。pytest その他のテストは実行しておらず、静的検査だけである。