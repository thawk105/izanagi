## 正しさ境界の所見

- **blocker — 実装予定は certified sink に接続されていない。** 変更対象は新規 module と単体 test だけで、`layer3_report.py` 等は参照専用である。[plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:21) [plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:52) 現行 `build_accepted_report()` は B-4 decision/report を入力に持たず、receipt と campaign view だけで `certifying_input=True` を生成する。[layer3_report.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:682) [layer3_report.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:743)  
  **成果物影響:** 新 module が欠落・破損・常時例外でも既存 certified 経路の受理集合、report、台帳は一切変わらず、「接続済み」という台帳記録だけが事実と食い違う。

- **must-fix — 規律 2 は public API の truthiness で破れる。** 予定返値は `__bool__` を持たない dataclass なので、具体的には正常な CLI 生成 report root に対して `if evaluate_b4_certified_selection(report_root=root): certified_select()` と書くと、`admits_certified_selection=False` でも decision object 自体は真になる。[plan.md:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:65) 実 sink が無いため現在は未発火だが、これは予定 API を接続した瞬間に成立する入力である。  
  **成果物影響:** naïve な接続先では全 valid report が certified 受理集合へ入り、field の `False` と実際の選択結果が逆転する。

- **must-fix — 3 file 束縛は内容整合だけで、対象・発行者・配置を束縛しない。** report B の三ファイルを report A の root に丸ごと置く、または valid JSON の `rows` を 402 個の任意 object に差し替え、Markdown の JSON digest と marker の二 hash を再計算すれば、予定検査を通る。plan は `len(rows)=402` までしか検査せず全 leaf を再導出せず、decision に publication/campaign identity も無い。[plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:68) [plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:123) producer 自身も coordinated rewrite と外部 pin 不在を非保証としている。[p3_b4_prerun_issuer.py:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_prerun_issuer.py:8)  
  **成果物影響:** certified boolean は False のままだが、decision の digest と後続台帳参照が別 publication、捏造 rows、または別 campaign の report を正規成果物として指せる。

- **must-fix — D1378 型の配置 fail-open が再発する。** producer は campaign root の三方向交差を検査し、復元が partial なら危険配置を追加拒否する。[p3_b4_material_report.py:1099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:1099) しかし予定 consumer は `campaign_disjointness` を再検証せず、生成後に三ファイルを campaign 配下へ移した入力も受理する。marker は path を束縛しない。  
  **成果物影響:** writer が拒否した配置の report に valid decision が発行され、report/台帳の配置保証が fail-open になる。

## 恒真・到達不能・自己 oracle の所見

- **blocker — 中核保証は候補集合に含意された恒真述語である。** 成功返値の型が `Literal[False]`、実装方針も「True の code path なし」なので、`admits_certified_selection is False` を偽にする成功入力は存在しない。[plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:75) [plan.md:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:95) 不正入力で例外になることは、この certified 保証を非恒真にはしない。  
  **成果物影響:** 単体 test は緑になり得る一方、実際の certified 受理集合や既存 report/台帳には何の防護も追加されない。

- **must-fix — 自己申告を許可権威にはしていないが、artifact の正当性と理由コードの権威にはしている。** plan は repository の §5 を読まず、`report_scope.preregistration_section_5`、`floor`、`certification_scope` を report.json 自身から読む。[plan.md:104](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:104) [plan.md:171](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:171) `verify_repository_preregistration_contract()` が検証するのは §5.1.1 と 5-file closure であり、§5 の発効状態ではない。[p3_b4_analysis_prereg_consumer.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1027)  
  **成果物影響:** caller-authored「§5 未発効」bundle が valid decision と `material_report_has_no_certified_selection_authority` の台帳根拠になり、参照の正当性が自己申告へ置換される。

- **must-fix — JSON、Markdown、marker は独立 oracle ではない。** 三者とも同じ report producer/caller が再生成でき、予定 consumer は selected fields の相互一致しか見ない。producer の Markdown 自体も同じ report object から status/verdict/rows を描画する。[p3_b4_material_report.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:849) [p3_b4_material_report.py:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:897)  
  **成果物影響:** 三者を協調差替えした bundle が valid report として decision/台帳へ入り、検査は改竄ではなく不整合だけを検出する。

## 層の mask と変異の帰属

- **must-fix — C07 は Markdown 層に mask される。** `certifying=True` の JSON guard を削除しても、予定 Markdown validator は non-certifying 表示を要求し、producer の固定行も non-certifying である。[plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:129) [plan.md:187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:187) [p3_b4_material_report.py:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:870)  
  **成果物影響:** C07 無効化後も入力は後段で拒否され、赤は受理集合の拡大ではなく reason/order の変化しか示さない。

- **must-fix — C08 は Markdown floor 層に mask される。** JSON floor guard を削除しても Markdown は `floor: unavailable` を固定検査する。[plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:188) [p3_b4_material_report.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:862)  
  **成果物影響:** C08 の killer は floor guard の必要性を証明せず、report は別 reason で拒否されたままになる。

- **must-fix — C09 は Markdown verdict 層に mask される。** evaluated guard を削除しても planned Markdown 検査は `protocol_violation` / `not_evaluated` に閉じる。[plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:113) [plan.md:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:189)  
  **成果物影響:** C09 無効化後も `established` は後段拒否され、赤の帰属は evaluated guard 一つに絞れない。

- **must-fix — C01 は standalone field の変異で、接続の変異ではない。** exact bool assertion は赤になるが、実 sink が decision を参照しないため production の受理結果は変わらない。[plan.md:181](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2139-b4-certified-connection/artifacts/dev-wave-t2139-b4-certified-connection/plan.md:181)  
  **成果物影響:** C01 は単体 object の値だけを変え、certified report や台帳の受理集合に変異を伝播させない。

## 親 brief の前提に対する反証

- **blocker — 「下流 consumer は実在しない」は一般化が広すぎる。** 最終 certified-selection consumer 不在という docstring はあるが、同じ file に receipt-bound report builder、exact certified campaign view の要求、`certifying_input=True` の生成・永続化が実装済みである。[layer3_report.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:682) [layer3_report.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:701) [layer3_report.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/layer3_report.py:743) [artifact_admission.py:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/artifact_admission.py:1315) 正確なのは「B-4 material report を読む consumer が無い」「現在の権威 producer から certifying input を発行できない」である。  
  **成果物影響:** 誤った一般化により実在する certified 境界が scope から外され、standalone validator を接続済みと誤記する。

- **must-fix — 現在の usable authority を `LaunchAdmissionRederivation.certifying` とする読みも不正確である。** origin binding はその値が False でなければ拒否し、production authority も発行不能である。[reflux_origin_binding.py:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/reflux_origin_binding.py:598) [reflux_origin_binding.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/reflux_origin_binding.py:602) Layer3 が直接要求する `VerifiedAcceptanceReceipt.certifying` も parser が常に False に閉じる。[s8c_acceptance_receipt.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/s8c_acceptance_receipt.py:420)  
  **成果物影響:** 将来接続時に誤った authority object を束縛し、許可条件または台帳 provenance が実際の発行境界と一致しなくなる。

- **must-fix — 「到達可能 verdict は 1 つ」は material-report CLI に限れば正しいが、分析経路全体への一般化は偽である。** material report は確かに `floor=None` を固定する。[p3_b4_material_report.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:224) 一方 public production path `evaluate_b4_artifacts()` は valid floor を受けて全 verdict 関数へ到達し、具体的に `floor=0` の正規 registry/manifest/raw input が `ESTABLISHED` になる構成も source test にある。[p3_b4_analysis_path.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:349) [test_p3_b4_analysis_path.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_analysis_path.py:274) [p3_b4_analysis_contract.py:712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_contract.py:712)  
  **成果物影響:** brief の一般化を台帳へ残すと分析契約の実在受理集合を誤記し、将来の正規 analysis report を到達不能値として拒否する根拠になる。

- **blocker — P1 の常時不許可関数は「接続」ではなく、検証付き非認証 projection である。** certified sink に結果を渡さず、入力ごとの差は「返るか例外か」だけである。  
  **成果物影響:** certified 選択、persisted report、台帳のどれにも B-4 判定が合流せず、成果物は接続未実装のままになる。

- **nit — P2 の docstring そのものは記録との矛盾ではない。** 文面は “This module” の scope 外と言っており、別 module に責務を置いても文章上は真である。[p3_b4_analysis_path.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_path.py:11) ただし worklog に「5 語目を埋めた」と書くことは、上記 sink 未接続のため別理由で誤りになる。  
  **成果物影響:** docstring を残すだけでは値は変わらないが、「接続完了」という worklog/台帳記録だけが実装を過大表示する。

- **must-fix — P4 の tmp CLI 正例は reader の到達可能性しか証明しない。** 現行 CLI test は三ファイル生成と marker hash を確認するだけで、certified sink の発火を含まない。[test_p3_b4_material_report.py:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_material_report.py:903)  
  **成果物影響:** 発火済みと記録しても live certified 受理集合は不変で、report/台帳から接続の運用実績を誤って参照する。

## scope 外だが real な指摘 (裁定パッケージ候補)

- **blocker — certified sink 統合層を別 wave に切り出すか、成果物名を validator に降格する裁定が必要。** sink は B-4 decision 欠落・typed rejection・`False` のすべてを fail-closed に扱い、boolean field を明示比較する必要がある。  
  **成果物影響:** 裁定なしでは certified 受理集合は変わらず、「connection 完了」という台帳だけが虚偽になる。

- **must-fix — report subject/issuer 層が必要。** expected publication/campaign identity、追跡済み issuer capability、または一次 artifact からの再導出のどれを権威とするか裁定し、三ファイルの協調差替えと移設を閉じる必要がある。  
  **成果物影響:** 未裁定のままでは decision/台帳が別 publication や捏造 rows を参照できる。

- **must-fix — §5/floor 発効状態の authority 層は T-2140 側で必要。** 現 prereg consumer は §5.1.1 の意味・source closure を検証するだけなので、§5 未発効を reason に使うなら専用 consumer/receipt が要る。  
  **成果物影響:** 未実装のままでは report の自己申告が floor 状態の台帳値になる。

- **must-fix — durable decision と end-to-end mutation 層が必要。** decision の canonical wire、対象 identity、sink receipt への hash 束縛、および「C01 で実 sink の受理が変わる」試験が scope に無い。  
  **成果物影響:** process-local dataclass の値しか残らず、report・台帳から実際に使われた判定を再検証できない。

## 総括

**結論は blocker。** この plan は「B-4 material-report の厳格な non-certifying validator」としては成立し得るが、certified-selection connection ではない。中核の False 保証は恒真、三ファイルは自己整合しか証明せず、実 sink・対象権威・台帳束縛が scope 外である。

静的読解のみ実施し、pytest は実走していない。