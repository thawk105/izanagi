## 総括

段 2 の「19 module / 25 literal purpose site」は識別子検索としては再現するが、consumer 閉包ではない。path 検索で少なくとも 4 site が追加される。  
重大な落ち: S6/S8A の再開判定、`backoff_repro`、A-2 の frozen WAL certification。  
また `s8b_oracle_report.py` の変更は reviewed-spec の source hash golden に抵触する。  
したがって、段 2 プランのまま実装へ進むのは不可。scope 再裁定またはプラン修正が必要である。

## 所見

- B-01 / 判定 refuted / scope 内 / 親 brief の 19 module / 22 site は、実際には表だけで 25 site。さらに path 検索で後述の 4 site が増える。標準入口は [`_require_admitted_campaign()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:1141) だが、全 consumer は通らない / 成果物影響: closure 記録が過少になり D1246 の取り残しを再発する。
- B-02 / 判定 real / scope 内 / S6 [`_replay_outcome()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s6_sort_sweep.py:400) と S8A [`_replay_outcome()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8a_trigger_sweep.py:499) は、raw `wal.replay()` の COMMIT だけで `replayed-certified` を返す / 成果物影響: resume 時の provenance、完了件数、exit status が偽 certified になり得る。
- B-03 / 判定 real / scope 内 / [`backoff_repro._bench_tps()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/backoff_repro.py:80) は COMMIT だけを certified TPS とし、resume 利用も明記する。同様に A-2 は [`_raw_cell_from_wal()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/paper_story_a2_certification.py:2574) で frozen WAL を直読する / 成果物影響: cross-run 再現判定と A-2 `observed-positive` certification が receipt/anomaly 不整合を受理できる。
- B-04 / 判定 real / scope 内 / 3 bypass は一般化ではなく実在 consumer。backoff は lock-only 後に raw snapshot を replay し ([backoff_requested_us.py:444](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/backoff_requested_us.py:444))、S1 は raw prefix を標本化し ([s1_report.py:369](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s1_report.py:369))、S8B report は raw window を judge 入力へ射影する ([s8b_oracle_report.py:1719](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_report.py:1719)) / 成果物影響: 手順 4〜6 を削ると certified report への穴が残る。
- B-05 / 判定 real / scope 外 / 手順 2 の `commits > 0`、`aborts >= 0`、witness exact shape、batch 0、workload exact shape、`verify_configs` 完全一致は、D1246 の確定最小条件である attempt、verdict、`certified`、`anomalies`、receipt 束縛を越える。D1246 は現在 consumer 用の小 helper に限定する ([decisions.md:40872](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/docs/decisions.md:40872)) / 成果物影響: fixture fanoutと受理条件を追加するため、残すなら個別根拠か追加裁定が要る。
- B-06 / 判定 refuted / scope 内 / fixture は `log_receipted_commit()` だけでは完成しない。同関数は COMMIT と receipt を書くだけで、attempt ID や `verify_done` は注入しない ([commit_receipt_support.py:111](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/commit_receipt_support.py:111)) / 成果物影響: 既存 helperと `wal.log()` の組合せなら実現可能だが、段 2 の追随説明は不足。
- B-07 / 判定 real / scope 内 / `s8b_oracle_report.py` は manifest の generator source で、実 byte hash が検査される ([s8b_oracle_manifest.py:458](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_manifest.py:458))。独立 golden に現行 report SHA が固定されている ([test_s8b_oracle_manifest.py:90](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_manifest.py:90)) / 成果物影響: 手順 6 は golden 追随なしでは関連テストを壊す。
- B-08 / 判定 refuted / scope 内 / 「production 6 file の小変更」は closure 修正後には最低 8 fileとなる。A-2とbackoff-reproを除外するなら明示裁定が必要 / 成果物影響: 現行分割のままでは「全 consumer 閉包済み」とは記録できない。
- B-09 / 判定 real / scope 内 / S1/S8B は lock-only gate、lock hash取得、WAL読取が別 read になる。プランは同一 snapshot の再確認を規定していない / 成果物影響: receiptが束縛するlockとepoch判定したlockが異なるTOCTOU窓が残る。

## 自分で再導出した consumer 閉包 (全件)

### 識別子から得た 22 full-admission site

16 module / 22 site。すべて [`require_admitted_campaign()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:1190) へ到達する。

- `orchestrator/critic/digest.py:1586`
- `orchestrator/campaign/p3_b4_closed_critic.py:740,1779`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:3088`
- `orchestrator/campaign/s6_sort_sweep.py:475`
- `orchestrator/campaign/backoff_extended_sweep_report.py:459`
- `orchestrator/campaign/backoff_sweep_report.py:57`
- `orchestrator/campaign/backoff_overthrottle.py:145`
- `orchestrator/campaign/p3_b4_wiring_probe.py:1475` — `runtime.artifact_admission.*`
- `orchestrator/campaign/p3_s4_loop_sort.py:546,743`
- `orchestrator/campaign/autonomous_trial_completeness.py:4423,4912,4959`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:1088` — `L.*`
- `orchestrator/campaign/p3_s4_loop.py:1240,1576,1791`
- `orchestrator/campaign/s8a_trigger_sweep.py:577`
- `orchestrator/campaign/replay.py:184`
- `orchestrator/campaign/layer3_report.py:685`
- `orchestrator/campaign/p3_s4_red.py:191`

### 識別子から得た 3 lock-only/raw-WAL site

- `orchestrator/campaign/backoff_requested_us.py:450` — `artifact_admission.*`
- `orchestrator/campaign/s1_report.py:385`
- `orchestrator/campaign/s8b_oracle_report.py:553` — `_artifact_admission.*`

したがって、段 2 の 19 module / 25 literal purpose site はこの範囲では real。

### path 検索で追加された 4 certified site

- `orchestrator/campaign/s6_sort_sweep.py:400-403`
- `orchestrator/campaign/s8a_trigger_sweep.py:499-502`
- `orchestrator/campaign/backoff_repro.py:80-93`
- `orchestrator/campaign/paper_story_a2_certification.py:2064,2574-2678`

D1246 の「現に存在する certified consumer」を成果物上の意味で数えると、最低でも 21 module / 29 source-level admission site である。`tools/` 配下に current certified site はなく、plot 2本は明示的 `HISTORICAL_RAW` だった。

## 層の被覆で落ちているもの

| 層 | 判定 | 根拠とscope |
|---|---|---|
| Layer3 report | covered | certifying build は `CERTIFIED_ACCEPTANCE` を再実行する ([layer3_report.py:624](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/layer3_report.py:624))。persisted report も completeness が再 admission する ([autonomous_trial_completeness.py:4959](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/autonomous_trial_completeness.py:4959))。 |
| critic digest | covered | certified CLI は full gate ([digest.py:1586](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/critic/digest.py:1586))。歴史 digest は明示的 `HISTORICAL_RAW`。 |
| critic projection | coveredだが影響あり | `artifact_admission.py` 自体が B4 projection closure に含まれる ([p3_b4_closed_critic.py:615](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_b4_closed_critic.py:615))。既存 B4 receipt は current projection hash 再検査で拒否され得る ([p3_b4_closed_critic.py:1637](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_b4_closed_critic.py:1637))。 |
| plot provenance | scope 外 | `plot_backoff.py:269` と `plot_s1_9pair.py:562` は `HISTORICAL_RAW` を provenance にも記録する。certified への回り込みではない。 |
| campaign registry | scope 外 | 現行 acceptance receipt は構造上 `certifying=False` 以外を拒否する ([s8c_acceptance_receipt.py:420](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8c_acceptance_receipt.py:420))。 |
| S8B judge | report結線が必要 | judge は E1 eligibilityとrow `status=="completed"`を信頼する ([s8b_oracle_judge.py:227](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s8b_oracle_judge.py:227))。report helper失敗を `protocol_violation` へ落とせば閉じる。 |
| replay receipt | covered | replay入口は full gate、source receiptも再検査する ([commit_receipt.py:426](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/verifier/commit_receipt.py:426))。 |
| paper-story A-1 | scope 外 | 明示的 non-certifying protocol。専用WAL topologyは保存receiptを既に検査する ([wal.py:1392](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/wal.py:1392))。 |
| paper-story A-2 | 落ち、scope 内 | `certified=True` なら anomalies や COMMIT receipt を見ずpassへ射影する ([paper_story_a2_certification.py:2417](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/paper_story_a2_certification.py:2417))。その結果が `observed-positive` を作る ([paper_story_a2_certification.py:2186](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/paper_story_a2_certification.py:2186))。 |
| known-axes freeze | scope 外の裁定候補 | COMMITだけからargmaxを選ぶ歴史freeze generator ([s1_known_axes_freeze.py:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/s1_known_axes_freeze.py:267))。凍結bytesは変更せず、将来再生成にもcurrent certificationを要求するかを別裁定にする。 |
| B10 shape sweep | scope 外の裁定候補 | COMMITをcorrectness-certified binaryとして使うが、成果物は明示的 `official_certification=False` ([b10_backoff_shape_sweep.py:2442](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/b10_backoff_shape_sweep.py:2442))。 |

## scope をはみ出している項目 / 削ると穴が残る項目

はみ出し、または要縮約:

- 手順 2 の full VerifyResult 再演に近い追加述語。最低限は同一 attempt、`verdict=="serializable"`、`certified is True`、exact int `anomalies==0`、保存receiptのlock/variant/attempt/terminal/evidence束縛に閉じるべき。
- 手順 7 の S6/S8A rowごとの再 helper 呼出し。全COMMITをchokepointで検査済みなら重複であり、D1246の小 helper 方針に反するほどではないが不要。むしろ未結線の `_replay_outcome()` を直すべき。

削ると穴が残る:

- 手順 2 の最小 helper本体。
- 手順 3 の全COMMIT chokepoint。
- 手順 4〜6 の3 bypass。これらは一般化ではなく実在 consumer。
- 手順 8〜9 のfixture追随とmutation-killing test。
- 手順 10 のconsumer閉包成果物。
- さらに段 2 に無い S6/S8A resume、backoff-repro、A-2 結線。

裁定パッケージ候補:

- A-2とbackoff-reproをD1246から除外するなら、「別certification protocol」「legacy reproduction」という明示裁定が必要。推奨は、いずれも current production の persisted certified claim なので scope 内。
- known-axes、plots、A-1、B10 nonofficialをcurrent certifiedへ再分類する変更は本wave外。将来必要なら別裁定とする。

## 変更単位の分割案

1. 共通核: `artifact_admission.py` の最小 helper、22 site chokepoint、helper単体正負test、full-admission fixture追随。
2. raw consumer群: 3 bypass、S6/S8A `_replay_outcome()`、backoff-reproと各fixture。S6/S8A row helperは省く。
3. A-2 adapter: frozen WAL再構築時のhelper結線、A-2 test、S8B source-hash golden追随。

各commitは拒否条件を追加するだけなので受理集合は広がらない。ただし 1 の時点では raw consumer 6本、2 の時点では A-2 が未閉鎖である。別waveとして途中landするならこの穴を明記し、A-2除外裁定なしに「D1246完了」としてはならない。安全なのは3commitを同一land単位に積むこと。

## 凍結 gate に触れる新規名

- `require_persisted_certified_commit` 自体を列挙するpublic-symbol inventoryは見当たらない。
- `STAGE_VERIFY_DONE` は新定数ではなく既存 ([model.py:26](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/model.py:26))。
- `artifact_admission.py` のbyte変更は exact 24 path のmember数を変えないが、future E1表示とB4 projection hashを変える。
- `s8b_oracle_report.py` のbyte変更は `PIN_GATE_SPEC_RAW` 内の report SHAと `PIN_GATE_SPEC_SHA256` を更新対象にする。
- S6/S8AのT-080 SHAはmigration basis commitのblobを読むためlive source変更では更新しない ([t080_freeze_migration.py:1365](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/t080_freeze_migration.py:1365))。
- `test_frozen_artifacts.py` はexact 23 output pathのみでPython sourceは対象外 ([test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_frozen_artifacts.py:41))。
- 新 insight 名はプランで未確定。`output/insights/*.md` は `check_docs.py` の内容走査対象 ([check_docs.py:2611](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/tools/check_docs.py:2611))。
- 段 2 は実際には新 test fileを要求していない。新設するなら全 `test_*.py` を走査するplain-runner gateにより、自走harnessまたはREADME allowlistが必要 ([test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_plain_runner_coverage.py:44))。
- 新parametrize IDはartifact/S6/S8A testには固定inventoryなし。ただし `test_critic.py` はduration ledgerの凍結suite prefixに含まれる ([update_acceptance_duration_ledger.py:21](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/tools/update_acceptance_duration_ledger.py:21))。
- `test_campaign_import_invariant.py` と `test_ccbench_spawn_sites.py` は全production Pythonを再帰走査するが、canonical relative importとsubprocess追加なしなら一覧変更は生じない。

## 親 brief の誤り

- P1: real。helperを既存 `artifact_admission.py` に置けばexact 24 pathを維持できる ([campaign_lock.py:49](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/campaign_lock.py:49))。
- P2: refuted。chokepointが全COMMITを検査すれば1 variantだけのanomalyもview発行前に拒否される。必要なのはS6/S8A row二重検査ではなく、chokepoint前に動くraw resume pathの結線。
- P3: real。S1 fixtureはbuild_startにattempt IDもverify recordもなく ([test_s1_report.py:94](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s1_report.py:94))、S8B fixtureも同様 ([test_s8b_oracle_report.py:556](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_report.py:556))。
- closure表: 見出しの22は誤り。表自体は25 literal siteを含む。さらにsemantic closureから4 site落ちている。
- pin閉包: exact 24、D1163のavailability-only、T-080のbasis-blob判定はいずれもreal。ただし「既存campaign admissionを無効化しない」ことと、B4 projectionやS8B generator source hashが変わらないことは別である。
- 親の独立実測1: `_claims_certified_execution()` がcontract keyだけを見る点はreal ([artifact_admission.py:623](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:623))。
- 親の独立実測2: live pathが`vr.certified`偽をabortする一方、persisted admissionがverdict/receiptを見ない点はreal ([pipeline.py:1301](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/pipeline.py:1301))。
- 親の独立実測3: S6/S8Aの`certified = commit is not None`重複はrealだが、不完全。raw resume、backoff-repro、A-2にも同型がある。

## 段 2 プランの誤り

- 19 module / 25 literal siteを全consumer閉包と扱っている。
- 手順 7 はS6/S8Aのreport rowだけを直し、実際に`replayed-certified`を発行するresume pathを落としている。
- backoff-reproとA-2を落としている。
- helperの検査述語が確定scopeより広い。
- S1/S8Bでlock epoch、lock hash、WAL snapshotの同一性を閉じる手順がない。
- S8B report source hashの独立golden追随がない。
- fixture対象は最低でも `test_backoff_consumers.py` と `test_paper_story_a2_certification.py` が追加で必要。
- 「production 6 file」は修正後closureでは最低8 file。
- P2のためのS6/S8A row二重呼出しは不要で、chokepoint全COMMIT検査とraw resume結線へ置き換えるべき。

テストは実走していない。以上はread-onlyの静的検査結果である。