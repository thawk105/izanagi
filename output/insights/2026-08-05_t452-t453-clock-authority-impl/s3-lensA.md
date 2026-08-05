# レンズ A 敵対レビュー

## 前提照合

- 登録較正の `tolerance_pct=2.0`、48 標本、外れ値 `3080.935` は確認できた（[registered calibration:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484)、[同:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1493)）。
- `contract_sha256` が contract field 全体から導出されることも正しい（[env_contract.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_contract.py:150)）。path/SHA を動かさない限り、凍結 floor protocol の pin が動かないという限定付き主張は成立する。
- tracked な `calibration/v2` は3件とも tolerance `2.0` であり、schema `<100.0` 化によって既存 expected artifact が parse 不能になる実例はなかった（[attempt 867874:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/calibration/attempts/0_867874.nqsv/calibration.json:1493)、[attempt 867876:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/calibration/attempts/0_867876.nqsv/calibration.json:1493)）。
- N2 の Silo 例外を production allow-through にせず、evidence/raw/calibration/driver の SHA で閉じた test-only identity にする方針は妥当（[s2-plan.md:228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:228)、[同:367](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:367)）。

### A-1 — 自己不整合な現登録較正が current admission に残る

- **主張:** 設計が要求する「再較正まで campaign を閉じる」が機械化されていない。exact 既知例外は監査用 test にしかなく、loader は現登録較正を受理し続ける。
- **file:line:** [設計 README:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:141)、[同:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:150)、[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:153)、[s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:151)、[同:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:215)、[test_s8b_floor_campaign.py:3441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_s8b_floor_campaign.py:3441)。
- **失敗シナリオ:** 現較正を loader が受理し、live observed を `[2101.0] * 48` とする。expected median は `2101.0`、policy 帯は `[2058.98,2143.02]` なので issuer/consumer は pass する。既存 E2E fixtureも、現較正の外れ値を帯内へ clamp して official 経路を成功させる形である（[test_s8b_floor_campaign.py:3464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_s8b_floor_campaign.py:3464)）。
- **成果物影響:** 自己不整合と既知の較正に基づく execution receipt と floor 試行が pass し、certified 選択の環境根拠と試行台帳が不正になる。
- **強度:** must-fix。
- **最小の是正案:** `load_verified_calibration()` の current required admission で policy 一致に加え expected profile の canonical self-pass を必須化する。既知集合は歴史監査用に残してよいが、allow-through に使わない。schema parser は別に保ち、履歴 parse は維持する。

### A-2 — self gate と Silo の policy wiring 変異が生き残る

- **主張:** metamorphic test は producer/loader/issuer/consumer の4者しか動かさず、self gate と Silo を含まない。両者の負例は極端な約45–47%外れ値なので、誤った literal `5.0` でも同じく reject される。
- **file:line:** [s2-plan.md:202](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:202)、[同:207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:207)、[同:264](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:264)、[設計 README:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:124)。
- **失敗シナリオ:** Silo または self gate を「全標本比較だが幅は literal `5.0`」へ変異させる。median `2101.0`、標本1個 `2164.03`（+3%）なら policy `2.0` では fail、変異では pass。一方、提案済み `3047.574` / `3080.0` 負例は `5.0` でも fail するため全テストが緑のままになる。
- **成果物影響:** Silo の `effective_clock_match/all_pass`、または取得時 candidate/publish が canonical より広い受理集合を記録する。
- **強度:** must-fix。
- **最小の是正案:** self gate と Silo の live/raw 両経路も metamorphic test に含め、`2%ではfail・3%または5%ではpass` となる差分 vector を置く。private 任意幅 helper を admission caller が直接呼ばないことも AST/call-site 検査で固定する。

### A-3 — 「完全一致」の負例が粗く、近似・丸め比較を殺せない

- **主張:** loader は `5/99`、issuer は `5`、consumer は `3/5/99` しか試さないため、`int(tolerance)==int(policy)`、丸め比較、`math.isclose` への退行が残る。
- **file:line:** [s2-plan.md:209](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:209)、[同:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:211)、[同:213](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:213)、[同:257](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:257)。
- **失敗シナリオ:** well-formed、SHA 再計算済み artifact の tolerance を `2.9`、expected/observed を双方 `[100.0]` にする。`int` 比較なら各層が pass するが、提案された `3.0/5.0/99.0` はすべて reject され、metamorphic の policy `3.0` 対旧 `2.0` も期待どおりなので緑が維持される。
- **成果物影響:** 非 policy artifact/map が VerifiedCalibration・issuer verdict・receipt consumer の受理集合へ入り、材料レポートの宣言値と実際の policy が食い違う。
- **強度:** must-fix。
- **最小の是正案:** 全 equality 層へ `math.nextafter(2.0, ±inf)`、`2.5`、`2.999…` の well-formed 負例を直接与え、対象層自身の reason/verdict を検査する。

### A-4 — duplicate-key 検出を外す変異に負例がない

- **主張:** production 案は duplicate-key 検出を要求するが、列挙された新テストには duplicate JSON がない。plain `json.loads` へ退行しても exact key 検査後には重複が消えているため緑になる。
- **file:line:** [s2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:43)、[同:252](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:252)、[同:253](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:253)、[certify_calibration.sh:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/certify_calibration.sh:571)。
- **失敗シナリオ:** v2 の clock object に、最初は外れ値を含む `samples_mhz`、最後は全て帯内の同名 `samples_mhz` を置き、raw manifest/SHA も再計算する。last-wins parser は exact 3-key object として受理し、canonical gate は後者だけを見て pass する。
- **成果物影響:** raw 観測の意味が一意でないまま Silo evidence・観測 hash・試行台帳へ pass として束縛される。
- **強度:** must-fix。
- **最小の是正案:** v1/v2 それぞれ top-level、`profile`、`effective_clock` の重複 key を持つ構文上 valid な JSON 負例を追加する。全 raw consumer が同じ duplicate-rejecting parser を通ることも固定する。

### A-5 — T126 の既存 fail-closed bug 修正が未裁定の受理集合拡大

- **主張:** plan は型移行に紛れて `verified.calibration` を `verified.attestation_profile` へ直すが、これは単なる型注釈変更ではない。現状は必ず type gate で失敗する経路を成功可能にする。
- **file:line:** [t126_driver.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:439)、[同:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:443)、[env_attestation.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:612)、[s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:71)、[brief.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/brief.md:11)。
- **失敗シナリオ:** clean observed profile を与える。現行コードは `CalibrationV2` を expected に渡して `AttestationError`、変更後は `accepted` の T126 attestation record を発行する。提案テストは変更後の成功だけを期待する。
- **成果物影響:** これまで空だった T126 qualification の受理集合が広がり、qualification 試行台帳と下流 eligibility が変わる。
- **強度:** must-fix。
- **最小の是正案:** 段4でこの bug fixによる受理集合拡大を明示裁定し、brief scopeへ追加する。未裁定なら本 waveから外して別タスク化する。

### A-6 — hash projection version が artifact に束縛されない

- **主張:** `projection_schema` を呼出側が自由に渡せる一方、T126 出力は引き続き `t126-qualification-attestation/v1` で、選んだ projection version を記録しない。設計の「同一 schema 名で hash の意味を変えない」を満たさない。
- **file:line:** [設計 README:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:94)、[同:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:104)、[s2-plan.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:50)、[同:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:73)、[t126_driver.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:451)。
- **失敗シナリオ:** v1 artifact を strict parseした後、caller が誤って v2 projectionを選ぶ。sentinelを含まない hash が生成されるが、recordには projection versionがなく、verifierは誤選択を識別できない。v1正例だけの hash test は緑のまま。
- **成果物影響:** `observed_profile_sha256` の参照先 preimage が非一意になり、材料レポートと qualification 台帳の proof chain が再計算不能になる。
- **強度:** must-fix。
- **最小の是正案:** parser戻り値に source schemaを持たせ、hash APIはそこから versionを導出して自由引数を廃止する。T126 recordにも projection schemaを必須記録するか schemaをv2へ上げ、歴史 rawから独立計算した literal SHAを置く。

### A-7 — brief の v1 corpus 内訳が実ファイルと不一致

- **主張:** success 19 / failure 3 という総数は正しいが、brief の「smoke 4件」は誤り。実際の success 19 は staging 15 + smoke 3 + Silo 1であり、smokeは success 3 + failure 3である。
- **file:line:** [brief.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/brief.md:24)、[s2-plan.md:327](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t452-t453-clock-authority/s2-plan.md:327)、[smoke 867857:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/smoke/0:867857.nqsv/observation.json:8)、[smoke 867860:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/smoke/0:867860.nqsv/observation.json:3)、[Silo probe:1500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/attestation-job.json:1500)。
- **失敗シナリオ:** 実装子が brief の内訳で corpus を作ると、clock付きでない smoke failureを1件混ぜ、Silo v1を落とし得る。また、明示リストだけを数えるテストなら新しい tracked v1 artifactを追加しても19/3のassertは緑のまま。
- **成果物影響:** legacy replay対象と歴史 hash/reference の集合が実 artifact集合とずれ、試行台帳の一部が将来 parse不能になる。
- **強度:** must-fix。
- **最小の是正案:** briefを訂正し、tracked artifactを探索して得た exact path集合と手書き golden path集合の一致をassertする。なお静的再計算では、N2の16件に加えてsmoke success 3件もcanonical falseだった。

## scope 外の real 所見

### A-S1 — policy `2.0` でも expected samples の出所は偽造可能

- **主張:** T-477/provenance scope。policy-valid・self-passな expected samplesを合成し、SHAとregistryを更新する経路は本wave後も残る。
- **file:line:** [設計 README:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:193)、[同:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/output/insights/2026-08-04_t452-clock-tolerance-authority/README.md:200)、[test_env_contract.py:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:353)。
- **失敗シナリオ:** 攻撃対象環境に合わせた samples、tolerance `2.0`、self-passな calibrationを `output/env/<key>/calibration/` 配下へ置き、SHA/registryを更新する。現行path検査は `registered/` やproducer receiptを要求しない。
- **成果物影響:** 新しい trial/contract世代で環境参照元を差し替えられる。旧凍結 floorはcontract不一致でfail-closedのまま。
- **強度:** backlog（scope外のreal所見。今回の実装要求にはしない）。
- **最小の是正案:** T-477でcontent-addressed pathとpublish receipt/policy sourceの束縛を設計する。

## 総括

- **(a) NO-GO。**
- **(b-1)** 自己不整合な現登録較正をloaderが受理し、clean live観測ならcurrent campaignがpassできる。
- **(b-2)** self/Siloの幅変異、近似一致、duplicate-key除去を提案テストが層別に殺せない。
- **(b-3)** T126を未裁定で成功可能にし、v2 hash projectionをartifact schemaへ束縛していない。
- **(c)** 実装子が最初に間違えそうなのは、exactな既知例外testを「campaign quarantine」と誤認する点。実際にはadmissionを一切閉じない。
- 最初にcurrent calibrationの機械的quarantineを確定し、その後に層別変異matrixとT126裁定を直すべきである。
- pytestは実行せず、全判定は静的検査による。