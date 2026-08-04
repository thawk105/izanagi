判定は **NO-GO**。静的検査だけで **BLOCKER 3件**を確認した。pytest は実行していない。

## 発火経路の実測

| 起動経路 | 実際に発火する予定の P5 検査 | 成果物・計測 ID |
|---|---|---|
| runbook §3.1 fixture | token 非発行なので seam gate、共有 session tracker、receipt 検査はすべて不発。両 receipt 欠落を正常扱いするだけ | `output/exploration/autonomous-trials/fixture-abc-g1/attempts.jsonl` と `report.json`。formal field は存在しない |
| runbook §3.2 Claude | parser token の発行・claim、既定 seam の肯定判定、共有 tracker、optional receipt 整合検査は発火 | `.../claude-abc-g1/provider/<role>/envelope_ycsb-a.g1.<role>.json` 等。実計測 ID は envelope の `session_id` と valid role-attempt の `provenance.child_id` |
| formal seam 負例 | 実起動経路なし。`main()` は `providers` / `drive` / `preview` を受け付けず、programmatic 呼出しには token issuer がない | plan は `run_root.mkdir()` 前に拒否するため、そもそも拒否 artifact path も残らない |

根拠は [runbook §3.1/§3.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/docs/phase3-s8c-autonomous-trial-runbook.md:61)、[run_trial](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1518)、[main](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1697)。

## consumer 閉集合

repo 全体の静的検索で確認した consumer は次のとおり。

- 直接 consumer:

  - `p3_autonomous_workload_trial._finish_trial()`：journal/report を生成し、書込み前 completeness を呼ぶ。
  - `assert_autonomous_trial_completeness()` と独立 CLI `verify_autonomous_trial_files()`：plan が触る唯一の意味論的 consumer。
  - `assert_campaign_layer3_chain()`：同じ trial report の `cells` を読むが、新 receipt は検査しない。
  - `main()`：返却 report から `status` と cell 数だけを stdout へ出し、新 field は読まない。

- plan が触らない下流:

  - `artifact_admission.require_admitted_campaign()` は `campaign.lock` と WAL/build receipt だけを検査する。
  - `layer3_report.build_report()` は上の admission decision と WAL を材料レポートへ射影するだけで、新 receipt を読まない。
  - `s8a_trigger_sweep`、`p3_s4_loop`、`p3_s4_loop_sort`、`p3_s4_red`、`s6_sort_sweep`、`replay` は `require_admitted_campaign()` の consumer だが、trial receipt には到達しない。
  - `build_admission.py` は別目的の build authority producer、`materializer_admission.py` は registry であり、どちらも P5 receipt consumer ではない。
  - hooks は trial path の改変面を守るだけで、field の意味を読まない。
  - `FROZEN_MANIFEST` は P3 trial 成果物を一件も含まない。

したがって plan の receipt は「書いて completeness が同じ二枚を比較する」層で止まり、certified 選択・材料レポート・proof chain の consumer はゼロである。

## BLOCKER

### BLOCKER 1 — provider seam gate の拒否経路が実起動面に存在しない

- (a) 主張: token issuer は `main()` にしかなく、注入 seam は programmatic `run_trial()` にしかない。二つの面が交差しないため、正式経路で provider 注入を拒否したことにならない。
- (b) 根拠: [brief:42-45](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/brief.md:42)、[plan:88-89,107-113](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:88)、[plan:146-156](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:146)。現行 `main()` の唯一の `run_trial()` 呼出しは既定 seam しか渡さない（[p3:1760-1775](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1760)）。
- (c) 失敗シナリオ: runbook §3.2 をそのまま実行すると token は発行されるが、`providers_injected=False`、builtin `drive/preview` しか評価できず必ず肯定側になる。一方、`run_trial(providers=fake, drive=fake, preview=fake)` は token を得られず `None` の no-op として従来どおり受理される。
- (d) 最小修正: 正式 production entrypoint と test injection helper を分離し、正式 entrypoint では token を必須化して seam 自体を公開しない。互換性のため `token=None` を残すなら、この wave で「provider 注入拒否を充足」と名乗らない。

### BLOCKER 2 — 新 token は origin/query 予約ではなく、直接反復を一切閉じない

- (a) 主張: plan の token は「Claude provider を parser が選んだ」という process-local capability にすぎず、D121 が必要とする iteration/query slot の予約ではない。
- (b) 根拠: plan の policy は [plan:93-105](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:93)。設計正本は planner 前の原子的 slot 予約と `_preview()` / `drive_iteration()` の一回限り token を要求する（[reflux design:279-283](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/output/insights/2026-08-01_t244-reflux-design/README.md:279)）。実際の `drive_iteration()` は token なしで layout、WAL provenance、checkpoint を作る（[trigger:604-666](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:604)）。
- (c) 失敗シナリオ: caller は `p3_s4_loop_trigger_gating --run-iteration` を繰り返すか、`drive_iteration()` を直接呼び、P5 token なしで campaign WAL を生成できる。plan の receipt は trial journal にしかなく、campaign identity、origin、slot、query のどれにも束縛されない。
- (d) 最小修正: 並行 P3 の `slot-reserved` `EventReceipt` を待ち、origin ID・slot ID・query digest・campaign ID を束縛した receipt を `_preview` と `drive_iteration` で消費する。それまでは token 案を設計メモに留める。

### BLOCKER 3 — receipt は自己申告であり、formal consumer と proof chain が存在しない

- (a) 主張: receipt は独立乱数と固定 policy literal だけで、trial、session、campaign、origin、実行 binary に束縛されない。二枚の一致は「同じ自己申告を二回書いた」以上の証拠にならない。
- (b) 根拠: [plan:91-105](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:91)、両欠落を許す [plan:139-159](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:139)、既知限界 [plan:267-270](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:267)。下流の admission receipt に P5 field はない（[artifact_admission:80-119](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/artifact_admission.py:80)）。Layer-3 も campaign/WAL だけを読む（[layer3_report:365-471](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/layer3_report.py:365)）。
- (c) 失敗シナリオ: 任意の Claude report に同じ形式の receipt を journal/report 両方へコピーすれば consumer は通る。逆に両方から削除しても通る。plan 自身の `test_formal_provider_init_failure_records_paired_receipt...` は、session を一件も観測していない failure report にも `role_session_policy` を記録するため、自己申告性を正例として固定してしまう。
- (d) 最小修正: 本 wave から receipt と completeness 編集を外す。残すなら、既存 `provenance.child_id` 集合、trial ID、実行 binary SHA、origin/campaign receipt を正準 digest に束縛し、artifact admission と Layer-3 が必須検査する別 P7/D96 wave にする。

## MAJOR

### MAJOR 1 — 「role 間は構造的に検出不能」は過大な一般化

- (a) 主張: instance-local set という実測は正しいが、session ID は既に durable artifact に保存されており、consumer からの横断検査は可能である。
- (b) 根拠: provider は `session_id` を `provenance.child_id` に保存する（[provider:290-345](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/claude_projected_provider.py:290)）。role-attempt はその provenance を journal/report に残す（[p3:849-856](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:849)）。completeness は現在 provenance が非空かしか見ない（[completeness:193-206](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:193)）。
- (c) 失敗シナリオ: tracker 呼出しが欠落して二 role が同じ `child_id` で valid になっても、paired receipt があれば独立 verifier は受理する。
- (d) 最小修正: runtime tracker に加え、`provider=="claude-headless"` の全 valid role-attemptについて `provenance.child_id` の exact 型・一意性を completeness が再計算する。

### MAJOR 2 — 親 brief の「成果物影響」3行のうち2行は成立しない

- (a) 主張: provider seam token と receipt は、現在の certified 選択・材料レポート・proof chain の値も受理集合も変えない。実効性があるのは cross-role tracker による §3.2 の complete/partial 判定だけである。
- (b) 根拠: brief の主張は [brief:59-66](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/brief.md:59)。しかし producer は `scientific_claim=False`、`no formal descriptor claim`（[p3:523-527](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:523)、[p3:891-903](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:891)）。runbook も no-build を配線確認に限定する（[runbook:125-163](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/docs/phase3-s8c-autonomous-trial-runbook.md:125)）。
- (c) 失敗シナリオ: 実装前後で §3.2 を走らせても、増えるのは trial-local receipt だけで、Layer-3、certified selector、proof chain は同じ入力を同じように受理する。直接 `drive_iteration()` も残る。
- (d) 最小修正: tracker だけを純増検出力として実装し、provider token/receipt は設計メモに留める。P5 全体の充足は名乗らない。

### MAJOR 3 — `--claude-executable` と PATH による provider 差し替えを formal receipt が隠す

- (a) 主張: Python provider object が owned でも、実際の provider process は caller 指定 binary である。receipt の `"owned-claude-projected-provider-set"` はこの差し替えを表現しない。
- (b) 根拠: CLI は `--claude-executable` を公開する（[p3:1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1710)）。provider は `shutil.which()` で解決した任意 binary を起動し、SHA は記録するだけで期待値照合しない（[provider:104-137](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/claude_projected_provider.py:104)）。
- (c) 失敗シナリオ: runbook §3.2 を、先頭に偽 `claude` を置いた PATH で実行する。shim が schema-valid envelope と一意 session ID を返せば全 P5 検査を通り、receipt は owned provider と主張する。
- (d) 最小修正: claim を「三つの Python seam のみ」に狭めて名称にも反映するか、formal 経路で許可 binary digest registry を要求する。期待 digest を具体化できないなら後者は実装しない。

### MAJOR 4 — 親 brief と plan の編集面が自己矛盾している

- (a) 主張: brief の成果物は「新 leaf＋テスト＋上記2ファイル」だが、plan は三つ目の production file `autonomous_trial_completeness.py` を必須編集にしている。
- (b) 根拠: [brief:34-37](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/brief.md:34) 対 [plan:139-145,248-258](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:139)。brief 自身の PROV-5（[brief:48-49](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/brief.md:48)）が成果物制約と衝突している。
- (c) 失敗シナリオ: plan に従えば親 scope 違反、成果物制約に従えば receipt consumer が未実装になる。author が解決できる実装判断ではない。
- (d) 最小修正: 段4で裁定する。推奨は receipt/completeness を外し、新 leaf、P3 driver、Claude provider、tracker テストだけに戻す。

### MAJOR 5 — 既存テストの赤化ゼロは、互換ではなく formal 区別の欠落を示す

- (a) 主張: plan どおりなら静的に赤くなる既存 test node は **空集合 `∅`**。plan:210-215 は「再実行対象」であって赤化一覧ではない。
- (b) 根拠: token なしは no-op、fixture/既存 programmatic Claude は receipt 両欠落で受理、run-start/report root は exact-key 閉集合でない（[plan:169-177](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:169)）。既存 fixture は receipt を持たない（[test_autonomous_trial_completeness:218-254](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_autonomous_trial_completeness.py:218)）。v2 固定 test も plan が version を変えないので緑のまま（[同:691-709](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_autonomous_trial_completeness.py:691)）。
- (c) 失敗シナリオ: 同じ `p3-.../v2` schema で receipt 付き Claude report と receipt なし Claude report の双方が valid になる。両側削除後も「formal だったか」を schema から判定できない。
- (d) 最小修正: v2 に formal field を足さない。正式系列を作る際に explicit discriminator と required receipt を持つ v3 を設け、既存 fixture/golden の赤化と更新を正面から扱う。

## MINOR

### MINOR 1 — 並行 P1/P3 との衝突予測が事実と逆

- (a) 主張: plan は P1/P3 が P3 driver/completeness を触る確率が高いとするが、両 wave は既存 production file を編集しないと明記している。
- (b) 根拠: [plan:264](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/out/s2-plan.md:264)、[P1 brief:9-16](/work/1/SFC/tanab/dev-wave-jobs/t244-p1-ir-emitter/s1-brief.md:9)、[P3 plan:20-27](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:20)。
- (c) 失敗シナリオ: 存在しない code overlap を理由に P5 の編集面を広げ、実際には段7の `docs/worklog.md` / `docs/decisions.md` 統合だけで起きる競合を見落とす。
- (d) 最小修正: production diff は新 leaf＋driver＋providerに固定し、docs spool の統合だけ直列化する。並行 wave が brief 外の wiring を始めた場合にのみ停止する。

### MINOR 2 — 識別子は字面では衝突しないが、意味上「予約」を二義化する

- (a) 主張: `formal_trial_gate` は `reservation.py`、`session_ledger`、`*_admission` と字面上は分離できている。しかし parser capability を “single-use reservation” と呼ぶことで、P3 の本物の `slot-reserved` receipt と衝突する。
- (b) 根拠: PBS 用 `ReservationBinding` は [reservation.py:2-55](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/reservation.py:2)、S1 ledger は [s1_direct_comparison.py:262-268](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/s1_direct_comparison.py:262)、並行 P3 は `EventReceipt` と `slot-reserved` を定義する（[P3 plan:77-113](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:77)、[同:283-301](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:283)）。
- (c) 失敗シナリオ: 後続 wiring が parser token を「予約済み」の証拠として受け取り、origin ledger の slot receipt を要求しない。
- (d) 最小修正: `ProjectedProviderCliCapability` 等へ改名し、`reservation`、`authority`、`origin token` を説明文から除く。

## 親実測の独立判定

- `run_trial:1551` の既存拒否が一経路だけ、は正しい。ただし production `main()` には注入面がなく、新 gate の実効性へ一般化できない。
- `_observed_session_ids` が instance 単位、は正しい。「role 間は構造的に検出不能」は誤り。既存 `provenance.child_id` から consumer 検査できる。
- `reservation.py` が PBS 用、は正しい。ただしそこから「build token 型の再利用が自然」は導けない。必要なのは origin/query slot receipt である。
- `FROZEN_MANIFEST` に P3 trial 成果物がない、は正しい（[test_frozen_artifacts.py:38-114](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_frozen_artifacts.py:38)）。これは凍結 bytes が不変というだけで、certified/material/proof の受理集合が変わる証拠にはならない。

## 総括

**BLOCKER は3件であり、この plan をそのまま実装してはならない。** 最大の問題は、token を発行できる面と注入 seam が存在する面が交差しておらず、runbook の実コマンドでは provider 注入の拒否を一度も観測できないことである。さらに、提案 token は D121 が要求する origin/query slot の予約ではなく、`drive_iteration()` の直接反復を完全に残す。receipt も trial・session・campaign・originへ束縛されず、唯一の consumer は同じ二枚の自己申告を比較するだけで、artifact admission、Layer-3、certified 選択、材料レポート、proof chain は一切読まない。

3要件のうち現時点で実効的な純増は、runbook §3.2 の12 role attemptsに対する cross-role session trackerだけである。しかも既存 `provenance.child_id` を completeness が横断検査すれば、独立再検証可能な形へ小さく強化できる。provider token、optional receipt、completeness v2 への field 追加は成果物価値も現在の正式受理集合も変えないため、設計メモに留めるべきである。推奨する段4裁定は「trackerだけを実装して P5 は未充足のまま明記し、origin reservation はP3、formal consumer結線はP7/D96へ送る」である。