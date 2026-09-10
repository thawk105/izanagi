## 所見

1. campaign 付き admission 失敗 fixture は、plan の記述どおりでは producer 実在形にならない。

   - 対象 (file:line): `s2-plan.md:68-78`、`p3_autonomous_workload_trial.py:2843-2856,2998-3063,3468-3476,3817-3831,4181-4193`、`test_trial_registry.py:976-1068`、`test_autonomous_trial_completeness.py:5079-5106`
   - 何が問題か: `campaign.lock` を消して `_finalize_build_cell_admission` が `layer3_report.render` で失敗する実経路では、cell に `LAYER3_ADMISSION_DIAGNOSIS_KEY` が必ず追加される。さらに正常な最終 generation 後の admission failure は、final critic 実行前なので `pending_critic_disposition.count == 1`、最終 generation の critic 欠落、`partial-generation` accounting になる。一方、`_prepare_registered_build_report` は全 generation に critic を含む完全履歴を作る。これへ failure decision と `count=0` だけを足せば verifier は通り得るが、producer が発行しない組合せである。鎖も diagnosis の存在を必須にしていないため、この偽 fixture は `autonomous_trial_completeness.py:4857-4870,4911-4923` を通れる。
   - 裁定にどう効くか: P1 の設計自体ではなく、負例が DW-O13 を満たすかを左右する。現 plan のまま緑でも実入力を守った証拠にならない。
   - 性質 (real / refuted): real
   - 推奨する扱い: fixture で diagnosis を producer 形に含め、最終 critic と accounting、role query 数、journal projection を `count=1` の実履歴へ揃える。単体負例も `_campaignless_failure_cell` の decision/disposition だけを流用せず、campaign-backed producer cell の全値を固定する。

2. producer と consumer の二重 stub は無いが、`layer3_report.build_report` の直接観測は不足している。

   - 対象 (file:line): `s2-plan.md:51-60`、`test_trial_registry.py:1813-1831,1852-1861`、`autonomous_trial_completeness.py:4652-4670,5002-5007`
   - 何が問題か: 既存正例は実 `assert_campaign_layer3_chain` と実 `_fresh_layer3_for_comparison` へ委譲し、fresh 到達を観測しているため、両層を stub して緑になる懸念は refuted。一方、新単体正例は戻り値しか assert せず、既存正例も `_layer3_report.build_report` 自体の呼出しは記録しない。`_fresh_layer3_for_comparison` の本体が別実装へ置換されても fresh wrapper の観測だけは残る。
   - 裁定にどう効くか: 「実体を名指しする」という P1 の試験根拠は `_fresh_layer3_for_comparison` までは成立するが、依頼された最内側実体まで完全ではない。
   - 性質 (real / refuted): real
   - 推奨する扱い: 正常 acceptance 正例か新単体正例で `_layer3_report.build_report` を実関数へ委譲する wrapper に包み、対象 campaign への到達を assert する。

3. 変異候補のうち 2 件は単一理由にならず、no-build 変異は具体化不足である。

   - 対象 (file:line): `s2-plan.md:82-90`、`autonomous_trial_completeness.py:4895-4926`、`trial_registry.py:6080-6103`、`autonomous_trial_completeness.py:4363-4379`
   - 何が問題か: `add(campaign_id)` 削除、gate 常時発火は対象入力を他層が拒否せず、単一理由にできる。対して ID を `seen.add` 直後へ移す変異は、単体戻り値 assert と acceptance の message mismatch の双方で赤になり、acceptance 入力自体は既存 post-check `trial_registry.py:6086-6094` が引き続き拒否する。受入 gate 削除も同じ post-check へ落ちるため、拒否集合を守った証拠ではなく message 所有だけを測る。さらに post-check まで消した場合も、exact failure は cross-binding の `:4374-4379` で拒否される。`:4373` は非 failure decision 用である。no-build は期待 ID と返却 ID がともに空集合なので、単に `:6010-6013` の branch 境界を動かすだけでは空走 gate は発火せず、変異が survive し得る。
   - 裁定にどう効くか: 現 matrix を 5 件すべて「直接防壁の kill」と数えるのは DW-M01/F820 を満たさない。
   - 性質 (real / refuted): real
   - 推奨する扱い: `add` 削除と常時発火は維持する。早期 add は戻り値契約の単体変異として扱い、gate 削除は拒否理由の message 変異と明記するか単一理由 matrix から外す。no-build は実際に拒否を生む exact patch を事前固定できなければ外す。

4. 戻り値変更が production の他の呼出し元を壊すという懸念は成立しない。

   - 対象 (file:line): `p3_autonomous_workload_trial.py:3702-3709`、`autonomous_trial_completeness.py:5089-5096`、`trial_registry.py:6070-6077`
   - 何が問題か: production の呼出しはこの 4 箇所で尽きる。producer 1 箇所と standalone verifier 2 箇所は bare call で戻り値を捨て、受入だけが新 consumer になる。
   - 裁定にどう効くか: `frozenset[str]` 追加は D1460 の受入限定を破らず、producer の発行順序や standalone verifier の受理集合を変えない。
   - 性質 (real / refuted): refuted
   - 推奨する扱い: plan の caller 方針を採用する。producer、standalone verifier は変更しない。

5. T-524 との直接行重複は現物上見えないが、親の live scan を統合時まで一般化できない。

   - 対象 (file:line): `brief.md:52-55`、`s2-plan.md:102-113`、`trial_registry.py:2257-2339,3437-3570,6070-6120,6183-6200`
   - 何が問題か: 現 worktree では T-2120 の面は `:6070-6094`、attempt classification と registry 本体は `:2257-3570`、formal attempt acceptance は `:6108-6120`、receipt 内 attempt projection は `:6183-6200` であり、直接行重複はない。ただし T-524 の未 commit worktree diff は指定射影に含まれず、brief の「70 root 全走査」はその時点の観測にすぎない。同一関数内という合成リスクまで非重複と一般化できない。
   - 裁定にどう効くか: 設計上の所有競合は見つからないが、統合可能性を確定済みとは扱えない。
   - 性質 (real / refuted): real
   - 推奨する扱い: T-2120 の編集範囲は維持し、統合直前に T-524 の live diff と acceptance 内 hunk を再照合する。追加の防壁や台帳は不要。

6. 2 module の編集や commit だけで paper-story drift test が赤になる、という型は成立しない。

   - 対象 (file:line): `paper_story_a1_paired.py:167-180,4379-4404,7195-7219`、`test_paper_story_a1_job_contract.py:48-62,243-281,386-409`
   - 何が問題か: `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` に入るのは `trial_registry.py` だけで、`autonomous_trial_completeness.py` は入らない。前者も test 実行時の HEAD blob OID と現在 bytes から binding を再生成して同じ値へ照合する live-tree 型なので、commit 後の新 HEADでは追随して緑になる。drift test が赤にするのは生成済み binding の missing/OID/SHA 値を改変した場合である。
   - 裁定にどう効くか: pin 更新は T-2120 の必要作業ではない。brief の「2 production module を pin」という表現は refuted で、plan の補正が正しい。
   - 性質 (real / refuted): refuted
   - 推奨する扱い: tuple や paper-story test は変更しない。他の関連検査として、現在 bytes の関数名を AST 走査する `test_s8c_preregistration_invariant.py:246-269,351-359`、C09 の live call を見る `s8c_preregistration_evidence.py:2195-2219`、HEAD bytes を動的複製する `test_s8c_preregistration_predicates.py:153-195,252-275`、意味的 AST inventory の `test_official_perf_closure.py:520-570` と `test_reflux_formal_consumer.py:835-858` があるが、いずれも固定 bytes pin ではない。

7. 受入 API と receipt 停止には効くが、D863 の正式系列着手判定には自動反映されない。

   - 対象 (file:line): `trial_registry.py:6070-6104,6256-6267`、`s8c_preregistration_evidence.py:2195-2219`、`test_s8c_preregistration_predicates.py:231-248`
   - 何が問題か: 新 gate は `accepted.append`、attempt acceptance、receipt 発行より前に置かれるため、空走時の receipt 不発行には実効性がある。一方、C09 evaluator は live な chain call と文字列を確認した後も `EVIDENCE_UNDEFINED` を返す。現 snapshot test も satisfied は C10 のみと固定している。T-2120 の plan はこの層を触らないため、変更後も repo の機械的 readiness は D863 完了へ遷移しない。
   - 裁定にどう効くか: 実装完了をそのまま「8c 正式系列の着手条件が機械的に解除された」と報告してはならない。
   - 性質 (real / refuted): real
   - 推奨する扱い: T-2120 の実装 scope は広げず、コード、実在 fixture、変異結果をもって D863 を人手で閉じるのか、C09 の別 wave が必要かを裁定パッケージへ返す。

8. brief の現行拒否集合は正しいが、到達位置と既存被覆を過度に一般化している。

   - 対象 (file:line): `brief.md:30-51`、`trial_registry.py:5537-5648,6086-6094`、`test_autonomous_trial_completeness.py:5000-5076`、`test_trial_registry.py:2301-2359`
   - 何が問題か: 6 件すべて campaign-backed build なら materialized failure は鎖前の measurement-target `:5632-5648` で止まり、post-check へ届くのは no-build 等を混ぜた束だけである。zero-cell の最初の拒否は `:5557-5561`。既存の completeness tests は persisted report 残存と independent admission 成功の拒否を固定するが、`ArtifactAdmissionError` を捕捉して正常 return する `:4917-4923` は直接固定しない。また「全 file:line が現物」という主張に対し、producer cell literal は現在 `p3_autonomous_workload_trial.py:3817-3831`、zero-cell test は `test_trial_registry.py:2301-2327` である。
   - 裁定にどう効くか: 「3 形とも現状拒否」という結論は維持できるが、今回必要な新被覆と到達条件は plan の補正版を正本にする必要がある。
   - 性質 (real / refuted): real
   - 推奨する扱い: brief の受理集合結論だけを採用し、到達位置、既存 test 被覆、exact line は plan の補正に置き換える。

## brief と plan が正しかった点

- materialized admission failure は `autonomous_trial_completeness.py:4911-4923` で fresh rebuild を行わず正常 return でき、現状は後段検査へ依存して拒否される。
- 受理集合は campaignless failure、campaign-backed failure、zero-cell のいずれについても現状すでに閉じている。T-2120 の中心は拒否理由を Layer 3 空走へ直接帰属させる点である。
- 比較成功後だけ campaign ID を返し、受入側で期待 ID との差を hard failure にする P1 は、述語型より実体観測として強い。
- campaignless hard failure、既存 post-check、cross-binding、no-build 経路を残す方針は D1289、D536、D1460 と整合する。
- `test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` は実 chain と実 `_fresh_layer3_for_comparison` に委譲しており、正常 build の実体到達正例として有効である。
- all-build 束では measurement-target が先に拒否するため、負例を 1 build failure と 5 no-build で構成する plan の補正は正しい。
- source binding が固定 digest ではなく live-tree 追随型であるという plan の判定は正しい。
- producer と standalone verifier が新しい戻り値を捨てるため、production 挙動を受入限定に保てる。

## 総括

P1 の実体観測型は採用可能です。ただし現 plan の負例 fixture は producer の diagnosis、pending critic、最終 generation accounting を再現せず、DW-O13 を満たしません。変異 2 件も既存 post-checkとの競合で単一理由にならず、no-build 変異は exact patch が不足しています。

受入 API と receipt 不発行には実効性がありますが、D863 の機械的 readiness は変わりません。この点は scope を拡張せず裁定パッケージへ返すべきです。検査は静的に行い、pytest は実行していません。