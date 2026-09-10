判定は **WAIT 自体は現行裁定下で real、ただしプランの主要な根拠は refuted** です。`D121` 参照ゼロから「評価器ゼロ」を導くことはできず、実際の到達不能理由は P6 の明示的停止、registered manifest の exact `G=2`、origin 束縛の registered-only 制約です。

[severity: must-fix] [観点 6 / 追加論点]
主張: 親 M6 の「`D121` を参照する実装 0 件、ゆえに P1〜P9 評価器 0 件」は一般化しすぎである。現物には conditions 1〜7・9〜10 を評価して P6 で明示停止する formal consumer があり、現在の直接的 blocker は `P6Unavailable` である。一方、P 別独立再導出は設計択一 1〜10 には含まれないが、裁定要約では再開条件として明記されているため、現行 WAIT を外すには再裁定が必要である。
根拠: [parent-measurements.md:83](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/parent-measurements.md:83>)、[reflux_formal_consumer.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/reflux_formal_consumer.py:942)、[reflux_formal_consumer.py:1034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/reflux_formal_consumer.py:1034)、[design-v2.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:104)、[excerpt-t434-ruling.md:7](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/excerpt-t434-ruling.md:7>)
影響: 「評価器 9 本を新設するまで永久 WAIT」という不要な依存を作る一方、実在する formal consumer と P6 の真の欠落を再利用しない。certified 選択の受理集合は現在は開かないが、解除条件の同定を誤る。
提案: WAIT の理由を「裁定済み再開条件、P6 の実 accreditation 不在、後述の launch 到達不能」に差し替える。段 4 では「全 P を機械再導出する」対「人間 commit A が status 判定の authority となり、機械は型・参照・hash・topology を検証する」を明示的に再裁定する。

[severity: must-fix] [観点 2 / 追加論点]
主張: P evaluator を揃えても、プランの cap=3 正例は現行 API では発火しない。registered manifest は `generations == 2` しか parse せず、receipt の `origin_binding_sha256` を実行時に再導出できる origin 経路は registered-effective 専用だからである。unregistered exploratory は cap=3 の候補経路だが origin binding を発行できない。
根拠: [plan.md:31](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:31>)、[trial_registry.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/trial_registry.py:771)、[p3_autonomous_workload_trial.py:1258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1258)、[p3_autonomous_workload_trial.py:1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1412)
影響: 受領証受理枝の実受理集合は空のままになる。正式 registry、certified 選択、正式材料レポートは `G=2` のままで、cap=3 正例は作れない。
提案: 段 4 で、(a) registered manifest・事前登録も receipt-backed `3..10` へ改訂する、または (b) origin を持たない unregistered 専用 schema を別 scope として裁定する、のどちらかを選ぶ。後者は D121 の前提意味を弱めるため非推奨。

[severity: must-fix] [観点 5 / 6]
主張: C11 は cap-lift receipt の第 7 runtime consumer ではない。現行評価器は定数が 2 以上かと既存三入口を静的に見るだけで、成功末尾も `EVIDENCE_UNDEFINED` である。さらに D882 は C11 の `required_evidence` と evaluator を変えないと明示しており、プランの C11 改訂は予約 locus と正面衝突する。
根拠: [brief.md:21](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/brief.md:21>)、[s8c_preregistration_evidence.py:2525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:2525)、[s8c_preregistration_evidence.py:2565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:2565)、[decisions.md:32477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:32477)、[plan.md:101](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:101>)
影響: 凍結済み事前登録契約を変更しても C11 の最終 status は変わらず、cap の実受理集合も広がらない。成果は増えず、事前登録 proof chain だけが別変更単位と衝突する。
提案: T-434 から C11 contract/evaluator 改訂を削除する。receipt 結線を C11 の新しい充足根拠にするなら、D882 が要求するとおり独立裁定、`DECIDER_VERSION` bump、次世代 freeze を別変更単位で行う。

[severity: must-fix] [観点 5]
主張: 条件 11 の内容 hash 生成閉包もプランから落ちている。contract を変えると literal hash test の期待値が静的に不一致になるうえ、D882 が予約した `g11` は既に D1066 の別改訂で実在するため、親 M3 の「g11 を後続 T-435 が発行する」という前提も現物と食い違う。
根拠: [test_s8c_preregistration_core.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_s8c_preregistration_core.py:1195)、[decisions.md:32456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:32456)、[decisions.md:32489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:32489)、[condition-freeze.v1.g11.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g11.json:1)、[plan.md:181](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:181>)
影響: plan C の path 集合では契約の frozen hash と世代台帳を整合させられない。事前登録の参照鎖が stale になり、正式試行の受理を失う。
提案: C11 を T-434 から除外する。T-435 は `g11` 前提を再裁定し、現行末尾の次世代番号で改訂し直す。

[severity: must-fix] [観点 1]
主張: 人間 commit topology を新規 `cap_lift_receipt.py` 内で再実装する計画は、既存 `s8b_ratified_freeze.py` の再利用方針と編集 path 表が矛盾する。plan A は新規ファイルしか所有せず、既存 helper の公開化・共通化 locus が無いため、実装時には private import か写経のどちらかになる。
根拠: [plan.md:76](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:76>)、[plan.md:89](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:89>)、[plan.md:183](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:183>)、[s8b_ratified_freeze.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:450)、[s8b_ratified_freeze.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:546)、[s8b_ratified_freeze.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:607)
影響: shallow/replace/grafts、履歴内別 blob、trailer 表記、create-only diff のどこかで二実装の受理集合がずれる。人間承認 topology の保証格が artifact 種別ごとに変わる。
提案: `_capture_head`、commit graph、immutable introduction、`AI-Agent: none`、parent/diff 検査を schema 非依存の共有 module へ抽出し、s8b と cap-lift の双方から利用する。`_assert_user_commit` 単独では exact 1 parent を保証しないため、親一致は cap policy 側で追加する。

[severity: must-fix] [観点 1 / 4]
主張: strict JSON・canonical bytes・sealed capability・HEAD blob・git env も既存実装と重複する。さらに completeness に別の literal/schema/topology parser を作る計画は、同一 receipt に二つの parser を持つ過剰実装である。
根拠: [plan.md:15](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:15>)、[plan.md:102](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:102>)、[s8c_acceptance_receipt.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:151)、[s8c_acceptance_receipt.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:233)、[s8c_acceptance_receipt.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:357)、[s8c_acceptance_receipt.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:580)、[s8c_acceptance_receipt.py:1230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:1230)
影響: producer と completeness で canonical/path/topology の受理集合が分岐し、一方だけ通る receipt が生じる。材料レポートと台帳が同じ SHA を持っていても検証結果が consumer ごとに変わる。
提案: schema 固有 field 判定だけを新設し、canonical decoder、path/hash、Git 読取、sealed reverify は共有する。completeness は共有 verifier の結果を用い、journal/report/search_config/Layer 3 の独立比較だけを担当する。

[severity: must-fix] [観点 2]
主張: plan が列挙する supervisor report 構築は正常系の一箇所だけであり、`_budget_indeterminate_report` が取り残される。この report は generation budget を持ち、run-start・completeness・通常 report 構築より前に返り得る。
根拠: [plan.md:100](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:100>)、[p3_autonomous_workload_trial.py:1881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1881)、[p3_autonomous_workload_trial.py:1905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1905)、[p3_autonomous_workload_trial.py:4660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:4660)
影響: registered cap-lift を将来到達可能にすると、予算不足時だけ receipt を持たない `generation_budget_per_workload > 2` の report object と lifecycle terminal が残る。通常材料レポートとの参照整合も検査されない。
提案: cap receipt を indeterminate report にも投影し、同一 SHA を検査するか、receipt-backed run は予算予約前に envelope を確定して全 return path に共通投影する。

[severity: should-fix] [観点 1 / 4]
主張: Layer 3 の全 `runs` row に同一 receipt body を複製する必要性は示されていない。campaign-level `search_config` は既に Layer 3 の top-level `workload` にそのまま投影されるため、SHA の束縛は自動的に材料レポートへ入る。既存 acceptance receipt も top-level の `{path,sha256}` 一件である。
根拠: [p3_autonomous_workload_trial.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:762)、[layer3_report.py:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:631)、[layer3_report.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:643)、[layer3_report.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:763)、[plan.md:101](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:101>)
影響: run 数だけ同じ authority bytes を複製し、行間不一致という新しい拒否状態を作る。材料レポートの値は増えないが、schema・テスト・fresh rebuild 比較の受理集合だけが複雑になる。
提案: `workload.cap_lift_receipt_raw_sha256` に加え、standalone audit が必要なら top-level に一つだけ別名の cap-lift reference/envelope を置く。既存 `acceptance_receipt` との同名化はしない。

[severity: should-fix] [観点 1 / 6]
主張: 親が挙げる既存 Layer 3 acceptance wiring は、正例が発火する完成 consumer ではない。acceptance receipt parser は `certifying=false` を構造的に強制する一方、`build_accepted_report` は `certifying=true` を要求するため、現 checkout のその枝は意図的に到達不能である。
根拠: [parent-measurements.md:56](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/parent-measurements.md:56>)、[s8c_acceptance_receipt.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_acceptance_receipt.py:420)、[layer3_report.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:682)、[layer3_report.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:701)
影響: これを positive-control 済みの先例として数えると、二つ目の dead receipt branch を作る。certified 選択や材料レポートの受理集合は広がらない。
提案: 再利用対象を sealed reverify と `{path,sha256}` projection に限定し、既存 accepted branch 自体を実効性の証拠に数えない。

[severity: should-fix] [観点 3 / 6]
主張: プラン内の主要な現行コード行番号は読み直されており、設計メモの古い番号をそのまま写した箇所は見つからなかった。ただし WAIT の根拠に使う `design-v2.md` 自身は `PROPOSED_UNRATIFIED`、cap=1、T-435 待ちのままで、親 brief がいう「設計正本」と現況が食い違う。
根拠: [design-v2.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:3)、[design-v2.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:36)、[brief.md:3](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/brief.md:3>)、[p3_autonomous_workload_trial.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:143)
影響: stale memo の再開条件だけを規範として引き、後発裁定だけを選択的に上書きする状態になる。実装者が cap、Layer 3 版、T-435 順序のどれを正本とするか一意に決められない。
提案: WAIT の規範根拠は裁定要約と後発 D に置き、design-v2 は歴史設計として扱う。現行アンカーは plan のものを維持する。

観点 7 については、プランが A/B/C を別々に land しないことと単一 commit を明記しているため、記載どおりなら「形式 receipt だけで先に上限が開く」中間 land は生じない。ただし上記の到達不能と consumer 欠落を直した後も、candidate G と人間 receipt commit A の二段 topology は維持する必要がある。[plan.md:177](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:177>)、[plan.md:187](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-cap-lift-receipt/artifacts/dev-wave-t434-cap-lift-receipt/plan.md:187>)

今 land できる T-434 の誠実な behavioral subset はありません。receipt core だけは D841 違反、C11 だけは受理集合を変えず D882 と衝突し、runtime consumer だけでは registered `G=2` と origin binding が残ります。共有 primitive の抽出も T-434 の成果そのものではなく、単独先行すると DW-G05 型の infrastructure 先行になるため、完全な変更単位内で行うべきです。

## 総括

must-fix は **7 件**です。

最大の懸念は、プランが「P evaluator 不在」を唯一の blocker と見ている一方、現物では registered manifest が exact `G=2`、origin binding が registered-only、P6 が `P6Unavailable` であり、評価器を追加しても cap=3 正例が発火しないことです。親の N1 と N2 は現物で裏が取れましたが、N3 の「C11 は第 7 consumer」は refuted、M6 の「評価器 0 件」は測定方法からの過剰一般化です。

段 4 で裁定すべき択一は次です。

- 推奨: **WAIT を維持するが理由と依存を修正する**。P6 accreditation の実体、registered manifest/事前登録の `G>2` 方針、D882/T-435 locus の解消後に、既存 receipt/topology primitive を再利用して全 consumer と正例を同時 land する。
- 代替: **独立 P evaluator 要求を再裁定で外し、人間 commit A を status authority とする**。ただし、これだけでは registered `G=2` と origin binding の矛盾は解けないため、同時に launch scope を再裁定しなければ受理枝は発火しない。

静的検査のみで、pytest・build は実行していません。