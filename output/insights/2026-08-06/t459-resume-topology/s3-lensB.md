指定ファイルはすべて読めた。以下は静的レビューのみで、書き込み・pytest・緑の確認は行っていない。

## 入口分類

|分類|経路|
|---|---|
|既に `ensure_resumable_wal` を通る|`loop.run_campaign` [loop.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:154)、screening の準備／候補評価 [screening_driver.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/screening_driver.py:101)・[screening_driver.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/screening_driver.py:147)、S-1 [s1_direct_comparison.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s1_direct_comparison.py:247)、guided の継続評価 [guided.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:191)|
|`ensure_campaign_identity` だけ|s6 [s6_sort_sweep.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s6_sort_sweep.py:276)、s8a [s8a_trigger_sweep.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8a_trigger_sweep.py:378)、p3 backoff [p3_s4_loop.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:706)、sort [p3_s4_loop_sort.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:236)、trigger [p3_s4_loop_trigger_gating.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:541)、guided fresh start [guided.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:159)|
|間接的に被覆|`backoff_sweep` は通常 `run_campaign` [backoff_sweep.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/backoff_sweep.py:163)、screening 時も screening driver 経由なので独自 start writer はない|
|プラン外の外側入口|三つの `drive_iteration` は、上表の inner writer を呼ぶ前に停止・checkpoint／provenance 書き込みを行える|

## 所見 1 — 二つの同時 resume で欠陥が再発する

- **severity:** blocker 候補
- **根拠:** recovery の flock は関数内の scan/append で解放される計画 [s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:67)。その後、`run_campaign` は別区間で replay・skip 判定・評価を行う [loop.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:170)・[loop.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/loop.py:240)。通常 `wal.append` は一レコードの排他追記だけで topology を検査しない [wal.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:324)。プランの並行テストも「recovery abort が一件」まで [s2-plan.md:298](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:298)。
- **取り残しシナリオ:** A が active の campaign に R1/R2 が同時 resume。R1 が A を recovery-abort、R2 は修復不要と判断する。両方が retryable と replay し、R1 が start B、R2 が start C を順に追記する。あるいは R2 が R1 の B を「中断」と誤認して abort し、R1 が後から `build_done(B)` を書く。
- **成果物影響:** B/C の二重 start は [wal.py:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:906) で拒否され、campaign 全体の admission、certified 選択、Layer3、台帳参照が再び失効する。プランが認める「旧 evaluator 生存」だけでなく、二つの新 resumer でも同じ結果になる。
- **提案:** 同 wave で、`ensure→replay→新 start` を覆う campaign-wide execution lease を導入するか、全 post-policy `build_start` を「flock 下で現 topology を検査してから追記する」専用 API に寄せること。少なくとも並行テストは二つの完全な `run_campaign` を barrier で競合させ、最終 WAL が admitted か、一方が二つ目の start 前に fail-closed することを要求する。

## 所見 2 — p3 の `stopped-before` がプランの seam より外側にある

- **severity:** blocker 候補
- **根拠:** プランは三経路とも inner 関数だけを置換する [s2-plan.md:164](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:164)。しかし外側の backoff driver は `check_stop` で return してからでないと `run_one_iteration` を呼ばない [p3_s4_loop.py:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:823)・[p3_s4_loop.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:831)。sort も同型 [p3_s4_loop_sort.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:318)・[p3_s4_loop_sort.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:327)。trigger は provenance header まで先に書く [p3_s4_loop_trigger_gating.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:709)・[p3_s4_loop_trigger_gating.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:720)。
- **取り残しシナリオ:** iteration 中に start A 後 crash。再起動時に walltime、reverse streak、収束条件のいずれかが成立すると、outer driver が `stopped-before` を返し inner seam に到達しない。trigger の `allow_resume=True` site では provenance header だけが更新される。
- **成果物影響:** 非 trigger では active A が残り、Layer3 は commit 不在 reject として certified 集合から候補を落とす [layer3_report.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:471)。trigger では WAL start A に対応する provenance がなく admission 自体が失敗する。さらに identity 照合前に checkpoint／provenance sidecar が変更され得る。
- **提案:** `ensure_resumable_wal` を各 public `drive_iteration` の layout 解決直後、`check_stop`、checkpoint、provenance 書き込みより前へ置く。direct `run_one_iteration` 呼び出し用の inner guard は残すか、共通 funnel にする。trigger の recovered mapping 同期も `stopped-before` より前でなければならない。

## 所見 3 — guided は「fresh-only」ではなく、継続入口から同じ writer を再利用する

- **severity:** must-fix
- **根拠:** `_log_eval` は attempt ID のない `build_start→…→commit` を書く [guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:127)。`cmd_evaluate` は commit のみを評価済み集合にする [guided.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:122)・[guided.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:203)うえ、同じ `_log_eval` を再度呼ぶ [guided.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:219)。プランは attempt-schema 無しを no-op とする [s2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:83)一方、`cmd_start` が fresh-only であることだけを理由に除外する [s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:174)。
- **取り残しシナリオ:** `_log_eval` の最初の start 後に process death。次の `cmd_evaluate` では recovery が no-op、commit がないため同じ genome は未評価扱いとなり、二つ目の start が書かれる。
- **成果物影響:** `trial_result` も commit だけを読み [guided.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:224)、孤児／二重 start を隠したまま `trajectory`、`n_evaluated`、`reached_cost` を出す。反対に generic admission へ渡すと、guided lock は post-policy [guided.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:97)なのに start に ID がなく [wal.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:898)、clean run さえ拒否される。
- **提案:** 標準 attempt recovery に無理に混ぜず、既存の no-build pseudo-WAL/schema 問題として別タスクへ切る。ただし本 wave では scope を「admission-aware build attempt」に狭め、guided の未終端 pseudo-eval は二つ目を書かず明示拒否する番人を置かない限り、「全 `build_start` 被覆」とは報告しないこと。

## 所見 4 — M3/M6 の一般化には admission を通らない反例がある

- **severity:** must-fix
- **根拠:** paper-quality plotter は `require_admitted_campaign` を呼ばず、WAL を直接 parse する [plot_backoff.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:110)。commit に先行する最後の bench を certified として採る [plot_backoff.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:133)うえ、PNG/PDF と WAL SHA provenance を出す [plot_backoff.py:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/tools/plotting/plot_backoff.py:283)。また S8b oracle は `ident.bind_admission_policy` ではなく独自 one-shot lock [s8b_oracle_driver.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8b_oracle_driver.py:967)から `pipeline.evaluate` を直呼びする [s8b_oracle_driver.py:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8b_oracle_driver.py:1344)。その report も raw WAL consumer [s8b_oracle_report.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8b_oracle_report.py:1249)。
- **取り残しシナリオ:** backoff WAL が `start A, start B, bench B, commit B` になっても、generic admission は campaign 全体を拒否する一方、plotter は B を描画する。S8b は crash 後 resume 自体を拒否するため T-459 は再発しないが、「今後生成される campaign はすべて post-policy」の反例になる。
- **成果物影響:** plot の `best_M`、`best_bf`、CI、PNG/PDF、provenance が topology-invalid WAL から生成され得る。S8b は独自 report が build_start 一意性を検査する [s8b_oracle_report.py:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8b_oracle_report.py:1008)ため、ここでは fail-closed であり certified 漏出は見つからなかった。
- **提案:** M3 を「shared admission gate を使う Layer3／critic／completeness 経路」に、M6 を「`loop.run_campaign` 系」に限定する。plotter の admission gate 化は独立した既存 consumer 欠陥なので別タスクが妥当。ただし図を T-459 の受理成果物に含めるなら同 wave の blocker とする。S8b は別 schema・one-shot と明記し、T-459 へ混ぜない。

## 所見 5 — trigger provenance 拡張は同 wave に必須

- **severity:** blocker 候補（§8を外す／後続 wave に送る場合）
- **根拠:** `_wal_attempt_provenance` は `records_by_stage` の最後の start 一件しか読む [p3_s4_loop_trigger_gating.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:499)。同 helper は明示的に最後勝ち [wal.py:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1048)。admission は全 start と provenance attempt の完全一致を要求する [artifact_admission.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:449)・[artifact_admission.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:481)。
- **取り残しシナリオ:** `binding A, start A, crash, recovery-abort A, binding B, start B, …, commit B`。provenance entry は通常 iteration 終了後にしか書かれない [p3_s4_loop_trigger_gating.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)ため、通常 entries は B だけになる。WAL starts は `{A,B}`、provenance は `{B}`。
- **成果物影響:** topology を直しても trigger campaign は admission 不通のままで、Layer3、critic digest、autonomous completeness、certified 参照がすべて失われる。
- **提案:** `recovered_attempts` は同 wave に含める。これは crash 無しでも常に発生する独立欠陥ではない。通常 retry では各 iteration 終了時に A/B の entry がそれぞれ残るため、欠落は「start 後、entry 前の interruption」に因果的に結び付く。validator は通常 entries と recovered mapping の和集合一致に加え、ID/key 一致、exact recovery abort、variant/commitment 一致、通常 entries との役割重複拒否を検査する。同期位置は finding 2 のとおり early-stop より前。

## 所見 6 — 中心テストは強いが、入口網羅テストは穴を殺さない

- **severity:** must-fix
- **根拠:** 現行の crash テストは active start を seed した後、WAL を書かない fake evaluate を使う [test_campaign.py:3991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:3991)・[test_campaign.py:4018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:4018)。共通 helper も evaluate 全体を差し替える [test_campaign.py:3725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:3725)。s6/s8 の resume tests は real reject writer を使うが、start+abort が完成済みで crash 窓がない [test_s6_sort_sweep.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s6_sort_sweep.py:302)・[test_s8a_trigger_sweep.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s8a_trigger_sweep.py:349)。
- **取り残しシナリオ:** プランの追加案は p3 系について `run_one_iteration` の early-writer test だけ [s2-plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:307)。outer `drive_iteration` が stopped-before になる finding 2 は、inner seam を完全に巻き戻しても検出されない。並行 recovery test も finding 1 の二重 retry を検出しない。
- **成果物影響:** テストが緑でも、停止済み trigger campaign の admission 不通や、二つの concurrent resumer による campaign-wide 拒否が残る。
- **提案:** 三つの public `drive_iteration` それぞれで、real attempt-schema start A と pre-stop state を seed し、呼出後に A の exact abort、二つ目の start 不在、admission 成功を検査する。trigger は recovered mapping と admission まで要求する。並行テストは recovery helper だけでなく全 resume runner を競合させる。guided は「no-op」を期待値に焼くテストではなく、未終端 trial が追加 start を書かず明示拒否することを検査する。
- **検出力判定:** 中心 E2E 案は、修正巻き戻し時に最終 replay/admission の受理集合が変わるため十分強い。診断文字列だけではない。プラン本文上、期待値反転・skip・既存値への合わせ込みは見つからなかった。

## 所見 7 — recovery の schema 判別条件が曖昧

- **severity:** must-fix
- **根拠:** プランは「attempt-schema marker を持つ start が一つでもあれば」topology validation とする [s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:79)一方、「attempt-schema key が全くない guided だけ no-op」とも書く [s2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:83)。この二条件は、start 以外にだけ `build_attempt_id` がある malformed WAL で一致しない。
- **取り残しシナリオ:** `commit(build_attempt_id=X)` に対応 start がなく、その後に tail trigger-binding orphan がある。start marker 基準なら topology を事前検査せず tombstone を追記し、次 replay で初めて orphan commit を拒否する。
- **成果物影響:** campaign は結局拒否されるが、既に不正な WAL の `wal_sha256` が recovery により変わり、overlay ledger、report、plot provenance の参照が不用意に失効する。「invalid topology は一 byte も変えない」という受入と食い違う。
- **提案:** no-op 条件を exact に定義する。任意 record に attempt ID、admission body、receipt SHA、trigger commitment のいずれかがあれば、append 前に必ず strict topology へ送る。guided は単なる key 不在推測ではなく、lock/config の明示的 no-build schema で識別する。

## consumer 取り残し — 攻撃したが破れなかった範囲

新しい record は新 stage ではなく既存の `abort` なので、WAL 白名簿 [model.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:20)・[wal.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:66)、Layer3 白名簿 [layer3_report.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:46)は破れない。

`start A, recovery-abort A, start B, commit B` に対して、Layer3 は A を監査用 `aborts` に残しつつ、commit がある variant を reject にしない [layer3_report.py:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/layer3_report.py:474)。s6/s8 も commit 存在を certified の gate にし、abort が残っていても aborted にはしない [s6_sort_sweep.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s6_sort_sweep.py:431)・[s8a_trigger_sweep.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8a_trigger_sweep.py:535)。

critic は未知 reason を `other_counts` に入れ [digest.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/critic/digest.py:267)、明示的に「非 liveness・CC 設計と独立」と表示する [digest.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/critic/digest.py:669)。certified 集合は変えないが digest の件数は増えるため、この意図を consumer test で固定すべきである。

formal completeness／台帳側は shared admission と fresh Layer3 の完全比較を行う [autonomous_trial_completeness.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/autonomous_trial_completeness.py:1165)。qualification は `QualificationEventSink` へ出す別 schema [t126_driver.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/qualification/t126_driver.py:492)・[pipeline.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:556)であり、campaign WAL consumer ではない。例外は finding 4 の raw plotter と guided である。

## 説明と実装の食い違い

- **severity:** must-fix
- **根拠:** 「5 inner entry を置換すれば全入口」という説明 [s2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:162)は outer stopped-before を支えない。「guided fresh-only」[s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:174)は `cmd_evaluate` の再利用 writer を支えない。「guided WAL は受理/no-op」[s2-plan.md:246](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:246)は post-policy topology の ID 必須規則を支えない。trigger recovery 同期を 736–745 に置く案 [s2-plan.md:196](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s2-plan.md:196)は、実コード上 run と early-stop 判定の後である。
- **取り残しシナリオ:** findings 2、3、5 の各順序。
- **成果物影響:** stopped-before trigger の admission 不通、guided trajectory の孤児隠蔽、recovered trigger の全 Layer3／critic／台帳参照欠落。
- **提案:** 実装着手前にプランの seam 表を public entry 単位へ書き直し、guided の scope、trigger 同期順、post-policy の対象範囲を明示する。

## 段階導入

- **severity:** must-fix
- **根拠:** recovery を `ensure_resumable_wal` で先に有効化すると、trigger WAL は A を abort できても §8 の schema／writer が未導入なら admission が即座に落ちる。逆に `replay` の副作用だけ先に消すと、未置換入口では trigger orphan が修復されない。
- **取り残しシナリオ:** core recovery commit を land → trigger resume → WAL は正規化 → provenance は旧 schemaのまま → `starts != provenance_attempts`。
- **成果物影響:** topology 修復済みなのに trigger の certified 選択、Layer3、critic、台帳が利用不能となり、「実装したが使えない」状態になる。
- **提案:** 安全な切り方は次の順序。

  1. `append` helper 抽出だけを byte-equivalent refactor として入れる。
  2. optional `recovered_attempts` の reader/writer/validator を後方互換で先に入れ、空 mapping と mutation tests を固定する。
  3. recovery 関数・reason を追加するが、まだ production seam から呼ばない。
  4. `ensure_resumable_wal` への接続、`replay` 副作用除去、全 public entry の置換、trigger 同期、並行 runner 防壁を同じ activation commit にする。

中間 commit では T-459 完了を主張せず、最終 activation 後にだけ全入口 E2E を受入条件とする。

## 総括

- blocker 候補あり: recovery flock 解放後の二つの concurrent resumer で二重 start が再発する。
- blocker 候補あり: p3 三系統の outer `stopped-before` が計画 seam を迂回する。
- trigger `recovered_attempts` は crash 固有の proof-chain 欠落を塞ぐため同 wave 必須。
- guided は既存 no-build pseudo-WAL 問題なので別タスク推奨だが、literal な「全 build_start」主張は修正が必要。
- M3/M6 は plotterとS8bに反例があり、共有 admission／loop 系へ限定すべき。
- 中心 real-writer E2E は検出力があるが、outer stop と完全な並行 resume のテストを追加する必要がある。
- scope 勧告: core＋全 public resume seam＋trigger schemaを同 wave、guided／raw plotter／S8b schema統一は別タスク。