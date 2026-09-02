## 欠陥の性質についての判定

**A-01**

- 主張: commit 0 件で loop が空走すること自体は欠陥ではない。「存在する全 commit の証拠が妥当」という全称命題は 0 件でも真である。現行コードと既存テストから読む限り、`CertifiedCampaignView` は「E1 の admission 済み WAL で、存在する commit は全て検査済み」を表し、commit の存在までは表していない。欠陥は issuer loop ではなく、全称保証を「certified commit が存在する」という存在保証として読む consumer 契約の曖昧さにある。
- 根拠の file:line: [artifact_admission.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:329)、[artifact_admission.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:1268)、[test_artifact_admission.py:1296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_artifact_admission.py:1296)。既存テストは no-commit campaign の view 発行を明示的に要求している。
- 誤っていた場合に何が壊れるか: view 型そのものが existential certificate なら、P1 の「0 件 view を維持する」は欠陥を温存し、型名を信頼する全 consumer が危険なままになる。
- 親が何を測れば決着するか: E1 の 0 commit、1 valid commit、1 invalid commit の3 fixtureで、issuer と consumer の期待 truth table を固定する。特に「view 発行」と「commit 由来主張」を別 assertion にし、人間裁定で view 型の意味を明文化する。

**A-02**

- 主張: 現在確認できる実 consumer は、0 commit から誤った certified 値を発行していない。`load_workload` と `load_landscape` は空集合を返し、backoff report は skip する。唯一明確に `certifying_input=True` を生成できる `build_accepted_report` は、コード自身が「certified-selection consumer は存在しない future entrypoint」と宣言している。したがって起票の「証拠なし certified view が現在誤主張を発行する」は過大であり、現状は API の意味不一致または将来リスクである。
- 根拠の file:line: [digest.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/critic/digest.py:701)、[replay.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/replay.py:179)、[backoff_sweep_report.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_sweep_report.py:65)、[layer3_report.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:682)。
- 誤っていた場合に何が壊れるか: 未調査の consumer が空集合を「certified success」として保存しているなら、プランの選択的配線から漏れる。
- 親が何を測れば決着するか: production の20件を E1・0 commit view で個別に通し、「例外」「空」「red/abort report」「certified 値または成果物」の4分類を記録する。`build_accepted_report` に production caller が存在するかも call graph で確定する。

## 受理集合の検査

**A-03**

- 主張: プランは `s1_report` と `s8b_oracle_report` で受理集合を広げうる。現在の単数 helper は、対象 commit を選んだ後も WAL 全体を evidence universe として使う。プランは success segment または window だけを渡すため、以前の segment/window に同じ variant・`build_attempt_id` の verify がある入力を無視できる。現在はその追加 verifyとの receipt 不一致で拒否されるが、提案後は通りうる。
- 根拠の file:line: helper は supplied records 全体から同じ attempt の先行 verify を集める [artifact_admission.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:662)。S1 は現在 campaign 全体を渡す [s1_report.py:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s1_report.py:351)、[s1_report.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s1_report.py:526)。S8B も現在 `persisted_records` 全体を渡す [s8b_oracle_report.py:1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s8b_oracle_report.py:1634)、[s8b_oracle_report.py:2030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s8b_oracle_report.py:2030)。縮小案は [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:38) と [s2-plan.md:40](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:40)。
- 誤っていた場合に何が壊れるか: brief の不変条件「今まで拒否された入力を通さない」に直接違反し、別 session/window の証拠を隠すことで不正 commit を標本や oracle 行へ昇格できる。
- 親が何を測れば決着するか: 正規 success の前に、同じ variant・attempt IDで receipt に無い verify を別 segment/windowへ置く差分 fixtureを作り、現行と実装案がともに拒否することを確認する。共通 helper は「検査対象 commit」と「証拠探索に使う全 records」を別引数にしない限り、この同値性を表現できない。

**A-04**

- 主張: A-03以外の変更は静的には受理集合を広げない。issuer の共通 scan は同じ単数述語を全 commit に適用し、count 型・整合検査と nonzero helper は拒否条件の追加である。S6、S8A、P3 duplicate は最新 commit だけから対象 variant の全 commit へ広がる可能性があり、同値または縮小である。したがってプランの「広げない証明」は A-03 の2経路だけで破れている。
- 根拠の file:line: 共通 scan 契約 [s2-plan.md:22](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:22)、追加拒否 [s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:47)、現行 S6 の latest commit 選択 [s6_sort_sweep.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s6_sort_sweep.py:483)、P3 duplicate の単数選択 [p3_s4_loop.py:1160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/p3_s4_loop.py:1160)。
- 誤っていた場合に何が壊れるか: refactorした8 consumerのいずれかで、証拠探索の範囲・物理順・lock SHAが変わり、拒否済み receipt が通る。
- 親が何を測れば決着するか: 各 direct callerについて、現行 helper結果と共通 helper結果を同一 records上で比較する predicate-level differential testを置く。単なる spy 呼出回数ではなく、複数 attempt・複数 commitを含める。

## 恒真な保証の検査

**A-05**

- 主張: `count == records内のcommit件数` は正規 issuer 経路では同じ候補集合から二重導出されるため恒真であり、persisted evidence 検査の独立防壁ではない。scanが証拠検査を省略して件数だけ増やす変異でも一致する。また「callerは件数を渡せない」は誤りで、module global tokenを使った直接構築が既存テストに存在し、D1252も同一 processからの偽造可能性を明記している。
- 根拠の file:line: 同一 recordsからのscanと照合 [s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:24)、[s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:55)。token は [artifact_admission.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:71)、直接構築は [commit_receipt_support.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/commit_receipt_support.py:196) と [test_t1286_commit_receipt.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_t1286_commit_receipt.py:431)。既裁定は [decisions.md:40927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/docs/decisions.md:40927)。
- 誤っていた場合に何が壊れるか: count fieldを独立な証拠検査と誤認し、scan弱体化を constructor assertが止めるという過大主張が残る。
- 親が何を測れば決着するか: scan内の単数 helperだけを除去し、件数は正しく増やすM1を実走する。count整合 assertではなく既存 receipt負例がkillすることを明記する。token強化はD1252によりscope外のままとする。

**A-06**

- 主張: 3つの nonzero 配線は先行述語から含意され、0件入力では到達しない恒真 gateである。`backoff_sweep_report` は commit由来 static点が無いと先にskipし、`backoff_overthrottle` は非空の期待全集合と committed bindingsのexact一致を先に要求し、`backoff_extended_sweep_report` は commit由来 `perf_statuses` が1種類であることを先に要求する。
- 根拠の file:line: [backoff_sweep_report.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_sweep_report.py:65)、[backoff_sweep_report.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_sweep_report.py:77)、[backoff_overthrottle.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_overthrottle.py:172)、[backoff_overthrottle.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_overthrottle.py:192)、[backoff_extended_sweep_report.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_extended_sweep_report.py:472)、[backoff_extended_sweep_report.py:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/backoff_extended_sweep_report.py:510)。
- 誤っていた場合に何が壊れるか: 「consumerで非ゼロを明示要求した」という記述だけが増え、0件を拒否する新しい実効境界は増えない。scopeと変異予算が恒真 assertに使われる。
- 親が何を測れば決着するか: 各関数へ0 count viewを渡し、nonzero helperが発火するか、先にskip/errorになるかをcall ledgerで確認する。先に落ちるなら配線を削るか、単なる重複assertと明記する。

**A-07**

- 主張: `autonomous_trial_completeness` の予定 gateも現行 production経路では休眠している。producerは常に通常の `layer3_report.render()`で non-certifying reportを作る一方、chain validatorは persisted `certifying_input` と launch値の不一致を新 helperより先に拒否する。現行出力にも `certifying_input=true` は見つからなかった。
- 根拠の file:line: producer [p3_autonomous_workload_trial.py:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/p3_autonomous_workload_trial.py:2827)、先行一致gate [autonomous_trial_completeness.py:4955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/autonomous_trial_completeness.py:4955)、提案位置 [s2-plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:109)。
- 誤っていた場合に何が壊れるか: M9はsynthetic fixtureだけでkillしても、実在経路を守る証拠にならない。
- 親が何を測れば決着するか: 現行producerから `launch_admission.certifying=True` の完全chainを作り、新 helper到達まで進めるか測る。到達不能なら、本waveへ残すには「future entrypointも実在consumerに含める」という裁定が必要。

## 変異候補の検査

**A-08**

- 主張: M1、M3、M6、M7、M8、M10は狙う意味が明確である。M4、M5は正規 issuerの受理ではなく、module-private constructorのsynthetic境界だけを検査する。M2は変異内容が曖昧で、filter除去により全recordへ単数helperを呼ぶ形なら最初の非commitで `TypeError`になり、予定したcount整合assertまで到達しない。M9は「条件除去」と「反転」を1変異に束ね、かつA-07の休眠経路を対象にしている。
- 根拠の file:line: mutation表 [s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:157)。非commitを拒否する先行gateは [artifact_admission.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:656)。M8対象の直接APIは [layer3_report.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:682)。
- 誤っていた場合に何が壊れるか: mutation matrixが「期待した保証が発火した」証拠にならず、別の先行例外やsynthetic fixtureだけによるkillを正しさ証拠として数える。
- 親が何を測れば決着するか: M2を「単数helper呼出対象を全recordへ変更」と「countだけ全record化」に分割し、期待例外とnodeを別登録する。M9も無条件化、反転、helper除去を別変異にする。各変異で最初に発火したgateとexact diagnosticを記録する。

## 親 brief の実測と一般化の検査

**A-09**

- 主張: 30 WAL、commit 0件が2件という値はrepository内の有効な `output/campaigns` 母集合については再確認できた。ただし「既存 certified 成果物全体」への一般化はできない。discover APIとLayer3/S8Bは明示的な外部 `output_root` を受理する。さらにtracked corpusの30 lockは現状v2 authorityを持たず、repository内にはそもそもE1 certified corpusが無いので、「既存certified値は変わらない」はほぼ空集合についての結論である。
- 根拠の file:line: briefの母集合 [brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:21)。外部rootを受ける [replay.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/replay.py:129)、[layer3_report.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:475)、[s8b_oracle_report.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/s8b_oracle_report.py:475)。campaignとしてはlockとWALの両方が必須 [artifact_admission.py:1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:1021)。
- 誤っていた場合に何が壊れるか: 別official namespaceや外部trial rootのE1・0 commit campaignが影響を受けても、「既存値不変」と誤報する。
- 親が何を測れば決着するか: trial registry、official namespace marker、実運用で指定される絶対 `output_root` を列挙し、その全rootでlock/WAL pair、epoch、commit件数を集計する。できなければ結論を「tracked repository corpusでは未発火」に限定する。

**A-10**

- 主張: 126 node probeは提案案と同じ受理集合を再現していないという限定自体は正しい。ただし126を「提案案で壊れるnode数の上界」とは呼べない。提案はconstructor必須引数、direct helperの移動、spy target変更、A-03の受理拡大を含み、テスト失敗数は一律gateの126を超えうる。上界なのは「admissionで0 commitを一律拒否した場合に生じた、そのprobe内の意味的棄却」だけである。
- 根拠の file:line: probeと限定 [brief.md:27](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:27)、[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:41)。提案の広い変更面 [s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:30)、[s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:47)、[s2-plan.md:130](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:130)。
- 誤っていた場合に何が壊れるか: 126未満であることを期待して、実装後の多数の赤を異常と誤分類するか、逆に126未満なら意味同値と誤認する。
- 親が何を測れば決着するか: 実装commit後に、baselineとの差を「意図した0 commit追加拒否」「interface追従漏れ」「predicate差」「無関係」に分類する。件数ではなく各nodeの最初の拒否述語で比較する。

**A-11**

- 主張: 「編集を止める発効済みB4 pinは無い」は正しいが、pin在庫の説明は不完全である。`artifact_admission.py` は24-path closure、B4 projection closure、保存済み admission receiptの `validator.identity + sha256`、S1 figureのgeneration-time validator pinに含まれる。B4の期待値は未記入なので停止pinではない。S1 pinは過去値を保存しつつlive hashを別比較するため編集禁止ではない。一方、新しい `artifact_admission.py` bytesでLayer3を再生成すると `validator_sha256` が変わるので、プランの「再構築物のbytesも変わらない」という一般化は誤りである。
- 根拠の file:line: 24-path closure [campaign_lock.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/campaign_lock.py:47)、B4 closureとrole path [p3_b4_closed_critic.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/p3_b4_closed_critic.py:623)、[p3_b4_closed_critic.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/p3_b4_closed_critic.py:656)、未記入欄 [phase3-b4-reflux-ablation-preregistration.md:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/docs/phase3-b4-reflux-ablation-preregistration.md:158)。動的validator hash [artifact_admission.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:1039)、Layer3への保存 [layer3_report.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:662)、S1の歴史pin分離 [test_s1_9pair_figure_provenance.py:654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_s1_9pair_figure_provenance.py:654)。
- 誤っていた場合に何が壊れるか: 保存済みreportとfresh rebuildの比較がvalidator SHA差で拒否され、commit件数fieldをreceiptへ出していないのに「値は不変」と誤報する。
- 親が何を測れば決着するか: cleanな実装commit前後で同じcampaignの `build_report()` を再生成し、`admission_decision.validator.sha256`を含むbyte diffを取る。保存済み7件のLayer3について [autonomous_trial_completeness.py:5001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/autonomous_trial_completeness.py:5001) のfresh比較も実測する。

**A-12**

- 主張: briefの再集計値「`CERTIFIED_ACCEPTANCE` 20 file、単数helper 9 file、和集合22」は現checkoutと一致する。ただしP3本文の「production 10 file」は古いままで、プランも不明な1件を残している。また名前和集合外に `verifier/commit_receipt.py` という `CertifiedCampaignView` consumerがある。これはexact COMMIT source recordを必須にするためnonzero helper不要だが、全数照合表には載せるべきである。
- 根拠の file:line: 正しい再集計 [brief.md:45](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:45)、古いP3 [brief.md:120](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:120)、プランの未解決 [s2-plan.md:179](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:179)、取り残された型consumer [commit_receipt.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/verifier/commit_receipt.py:387)、source recordのCOMMIT拘束 [artifact_admission.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:97)。
- 誤っていた場合に何が壊れるか: 「22 fileで全数」と誤認し、別名 import、型だけのconsumer、中継consumerを未照合のままにする。
- 親が何を測れば決着するか: 名前grepに加え、`CertifiedCampaignView` annotation/import、`require_certified_campaign_view`、`view.records`中継をASTで列挙し、各行に「nonzeroが既存述語から含意されるか」を記録する。direct helper数は9へ統一する。

## scope の検査

**A-13**

- 主張: 必須countをconstructorへ追加するのに、プランのtest更新面が不足している。`test_artifact_admission.py`以外にも、`commit_receipt_support.py` と `test_t1286_commit_receipt.py` がtokenを使って `CertifiedCampaignView` を直接構築しており、必須引数追加後は追従しなければ失敗する。
- 根拠の file:line: プランのconstructor更新範囲 [s2-plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:120)、未列挙fixture [commit_receipt_support.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/commit_receipt_support.py:196)、[test_t1286_commit_receipt.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_t1286_commit_receipt.py:431)、[test_t1286_commit_receipt.py:531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_t1286_commit_receipt.py:531)。
- 誤っていた場合に何が壊れるか: commit receipt系testが新仕様と無関係なmissing argumentで落ち、mutation killや受入結果を解釈できない。
- 親が何を測れば決着するか: `_CERTIFIED_VIEW_TOKEN` と `CertifiedCampaignView(` の全call siteを再検索し、各fixtureへrecords由来の正しいcountを渡す。synthetic countを固定値で置かず、fixture recordsから計算する。

**A-14**

- 主張: D1246に基づく共通scan化はscope内だが、恒真なbackoff 3 gateと現行到達不能なautonomous certifying gateは仮想リスク向けの配線で、briefのscope外条件と衝突する。逆に本題を再発させないための型/docstring契約更新が抜けている。`CertifiedCampaignView`が「commit存在を保証しない」ことと、新helperだけが存在保証を与えることを明記すべきである。future-only `build_accepted_report`を実在consumerに数えるかは裁定事項である。
- 根拠の file:line: D1246 [verbatim-rulings.md:5](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/verbatim-rulings.md:5)、仮想リスク除外 [brief.md:105](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/brief.md:105)、曖昧な現行docstring [artifact_admission.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:331)、future entrypoint宣言 [layer3_report.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:689)。
- 誤っていた場合に何が壊れるか: 実効性の無いgateを追加しながら、次のconsumerが型名だけで存在保証を推測する同じ欠陥を再発できる。
- 親が何を測れば決着するか: 「production callerが無くても直接呼べるcertifying producerを実在consumerと数えるか」を裁定パッケージへ出す。裁定にかかわらず、viewの全称保証とnonzero helperの存在保証はdocstring/test名で分離する。

## 総括

**A-15**

- 主張: 現プランはそのまま実装へ進める状態ではない。方向性、すなわち「admissionで一律拒否せず、全称保証と存在保証を分ける」は妥当だが、起票の欠陥位置が不正確で、S1/S8Bの受理集合拡大、恒真gate、mutationの曖昧さ、constructor fixture漏れ、validator SHAによる再生成値変化が残る。
- 根拠の file:line: 主要なblocking箇所は [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:38)、[s2-plan.md:40](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:40)、[s2-plan.md:61](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:61)、[s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2127-empty-commit-loop/t2127-empty-commit-loop/s2-plan.md:157)。
- 誤っていた場合に何が壊れるか: 不変条件「受理集合を広げない」を破ったまま、空loop欠陥を閉じたと宣言することになる。
- 親が何を測れば決着するか: 実装前に少なくとも、S1/S8Bのevidence-universe差分fixture、全constructor call site、0 commit consumer到達表、Layer3再生成byte diff、分割したmutation期待nodeを確定する。その後に実装と実測へ進むべきである。

pytestは実行していない。以上は指定資料と現行コード、保存済み成果物に対する静的検査結果である。