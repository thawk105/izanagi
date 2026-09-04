## 現行の受理・拒否挙動

| cell の形 | 現行経路 | 結果と message |
|---|---|---|
| campaign 無し失敗 | `trial_registry.py:5565-5567` が complete bundle から除外。鎖は `autonomous_trial_completeness.py:4879-4884` で `_fresh_layer3_for_comparison` を呼ばず `continue` | 鎖から戻った後、`trial_registry.py:6080-6085` が `[campaign-chain] campaignless failure fallback bypassed Layer-3 validation for cells [0]` で拒否 |
| campaign 付き admission 失敗 | persisted Layer 3 が無く、独立 admission も失敗する場合、鎖は `autonomous_trial_completeness.py:4911-4923` で `_fresh_layer3_for_comparison` を呼ばず `continue` | 束に no-build 等があり `complete_build_bundle=False` なら、`trial_registry.py:6086-6094` が `[campaign-chain] build cell has no persisted reports/layer3_report.json after Layer-3 chain` で拒否 |
| 同上、6 件すべてが campaign-backed build 扱いの束 | `trial_registry.py:5537-5593` が欠落 Layer 3 を収集し、complete bundle のまま | 鎖より前の `trial_registry.py:5632-5648` が `[measurement-target] complete build bundle requires exactly 6 readable layer3 reports; found ...` で拒否 |
| zero-cell (`do_build=True`, `cells=[]`) | 最初の measurement-target prepass の `trial_registry.py:5551-5561` | `[campaign-chain] do_build=True requires a non-empty report.cells list` で拒否。後段の同型検査 `:6014-6019` には到達しない |
| 正常 build | `autonomous_trial_completeness.py:4941-5007` で campaign、persisted report、admission を検査し、`:5002-5007` で実 `_fresh_layer3_for_comparison`、`:5016-5033` で比較 | `trial_registry.py:6086-6094` の post-check と `:6095-6104` の cross-binding を通り、`:6256-6267` で receipt を発行して受理 |
| no-build (`do_build=False`) | prepass は `trial_registry.py:5548-5550`、本ループは `:6010-6012` で鎖を呼ばない | 現行どおり受理。`:6218-6220` で `no-build` reason を積む |

鎖全体が `_fresh_layer3_for_comparison` を一度も呼ばず正常 return する経路は次の 3 つです。

- `report.cells=[]`: `autonomous_trial_completeness.py:4820` の後、loop を 0 回通って `:5033` の後へ fall-through。
- sole cell が exact campaignless fallback: `:4879-4884`。
- sole cell が campaign identity を持つ exact admission failureで、persisted report が無く、`require_admitted_campaign` が `ArtifactAdmissionError` を返す場合: `:4911-4923`。

複数 cell のうち正常 cell が一つでもあれば、その cell は `:5002-5007` を通るため鎖全体の空走ではありません。

## 変更案

| file:line | 変更内容 | なぜそれが D1460 / D1289 を満たすか | 変更後に新しく拒否される report / 受理が変わらないことの根拠 |
|---|---|---|---|
| `autonomous_trial_completeness.py:4815-4823` | **主案 (P1)**: 戻り値を `None` から `frozenset[str]` にし、実体検証済み campaign ID の局所 set を初期化 | predicate ではなく、鎖自身が実行した検証を受入へ返す | 既存の例外、検査順、`continue` 条件には触れない |
| `autonomous_trial_completeness.py:5002-5033` | `_fresh_layer3_for_comparison` が成功し、persisted/fresh 比較も一致した後だけ `campaign_id` を set に追加。loop 後に `frozenset` を返す | 「関数を呼んだ」ではなく実 `_fresh_layer3_for_comparison` を通過した campaign だけを観測する | campaignless と materialized failure は空集合。正常 build はその campaign ID を返す。鎖単体の受理・拒否集合は不変 |
| `trial_registry.py:6069-6085` | 戻り値を `validated_campaign_ids` として受ける。既存 campaignless hard failure の後で、report の campaign identity 付き cell の ID 集合との差を取る | D1460 の閉鎖場所は `assert_trial_registry_acceptance` のまま。D1289 が却下した「記録だけ」ではなく `_fail("campaign-chain", ...)` で停止 | 現行で post-check により拒否される materialized failure の拒否理由が直接の空走 failure に変わる。現行受理集合自体は縮まらない |
| `trial_registry.py:6085` 直後 | 欠落 ID があれば、例えば `[campaign-chain] Layer-3 validation empty-run for trial 'trial-X': 1 of 1 campaign-backed build cells did not reach fresh rebuild; campaign_ids=['...']` で拒否 | 何が空走したか、何件中何件か、campaign identity を明示し、規律 3 を満たす | 正常 build は returned set と期待 set が一致。no-build はこの branch に入らない。campaignless は既存 `:6080-6085` が先に止める |
| `trial_registry.py:6086-6094` | 既存 post-check をそのまま残す | 戻り値契約や将来の退行があっても persisted file 不在を引き続き fail-closed にする | D1289 の二重防壁を弱めない |

推奨は **(P1) 実体観測型**です。追加位置を比較成功後の `autonomous_trial_completeness.py:5033` より後へ限定すれば、「実 `_fresh_layer3_for_comparison` を通した」という事実だけを返せます。

対案の述語型は、`trial_registry.py:6022-6050` で `is_exact_cell_admission_failure_decision` に一致する campaign-backed cell を記録し、`:6085` 後で拒否する一ファイル変更です。現行の鎖では failure decision が必ず `:4911-4923` で fresh rebuild を迂回するため結果は同じですが、report の宣言を検査しているだけです。将来、failure cell を実体検証する実装になっても拒否し続け、逆に predicate の候補集合と期待集合が同じ導出なら恒真化し得るため推奨しません。

(P1) gate が実行されない条件は、complete build bundle の欠落検査が先に拒否する `trial_registry.py:5632-5648` です。ただし、その場合は鎖が「正常 return した空走」ではなく鎖呼出し前の hard failure です。新しい負例は残り 5 件を no-build にしてこの prepass を越えさせるべきで、prepass 自体は変更しません。

## 呼び手への影響

repo 内 grep で確認できる production の全呼出し元は次の 4 箇所です。

| 呼出し元 | 現行の戻り値利用 | 変更後の影響 |
|---|---|---|
| `p3_autonomous_workload_trial.py:3702-3709` | bare call で破棄 | 戻り値は引き続き破棄。`:3710-3716` の検査、report 発行順序、診断契約は不変 |
| `autonomous_trial_completeness.py:5089-5091` | standalone verifier の campaign-output-root 経路で破棄 | 受理・拒否、例外、呼出し順序は不変 |
| `autonomous_trial_completeness.py:5093-5096` | campaignless standalone 経路で破棄 | 空の `frozenset` を破棄するだけで、campaignless 診断の受理は不変 |
| `trial_registry.py:6070-6077` | 現在は破棄 | 唯一の新 consumer。受入だけが結果を hard failure 判定に使う |

既存テストの直接呼出しも成功値を `None` と比較していません。`test_trial_registry.py:1818-1821` と `:2341-2344` の wrapper は既に実関数の結果をそのまま返すため、新しい戻り値を受入へ透過します。`test_autonomous_trial_completeness.py` の既存 direct calls は成功値を捨てるか `pytest.raises` 内で使う形です。

## テスト案

正例:

- `orchestrator/tests/test_autonomous_trial_completeness.py::test_campaign_chain_returns_freshly_rebuilt_campaign_ids`
  - `test_autonomous_trial_completeness.py:3551-3620` の `_layer3_campaign` と `:4436-4443` の `_campaign_report` を使う。
  - `assert_campaign_layer3_chain(...) == frozenset({cell["campaign_id"]})` を assert。
  - `_fresh_layer3_for_comparison` と、その実体である `layer3_report.build_report` (`autonomous_trial_completeness.py:4666-4670`) は stub しない。

- 既存 `test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` (`:1781-1861`) を無変更で正例に残す。
  - 実 chain と実 `_fresh_layer3_for_comparison` を包んで委譲し、6 trial、6 campaign の到達を既に assert している。
  - 新 gate が正常な returned ID を消費して receipt まで到達することも同時に固定できる。

- 既存 `test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance` (`:1651-1741`) を無変更で残す。
  - `_base_report` の `do_build=False` は `:559-575`。
  - D536 の no-build 受理と `"no-build"` reason を固定する。

負例:

- `orchestrator/tests/test_trial_registry.py::test_s8c_acceptance_rejects_campaign_backed_admission_failure_layer3_empty_run_after_chain`
  - 残り 5 report は `_reports(..., complete=False)` (`test_trial_registry.py:1545-1553`) で no-build にし、measurement-target prepass を越える。
  - 対象 1 件は `_prepare_registered_build_report` (`:1281-1390`) で descriptor、campaign identity、WAL、arm binding を備えた実 fixture を作る。
  - `_registered_layer3_report_path` (`:1393-1399`) の persisted report と campaign の `campaign.lock` を消す。これは既存の unadmitted campaign 作成方法 `test_autonomous_trial_completeness.py:5400-5403` と同じ。
  - failure decision、pending critic disposition、partial status、`observation_sha256=None`、`primary_value=None`、run-finish の `cell_admission_failures` を producer 形へ揃える。projection は `autonomous_trial_completeness.py:370-385` を再利用する。
  - 実 chain を委譲する wrapper と実 `_fresh_layer3_for_comparison` を委譲する wrapper を使い、chain 到達 1 回、fresh 到達 0 回、上記 exact `[campaign-chain] ... empty-run ...` message、receipt 不在を assert。
  - **新しい観測 gate が消える、failure campaign ID を誤って検証済みに数える、または空走を具体化しない message に戻ると赤になる。**

- `orchestrator/tests/test_autonomous_trial_completeness.py::test_campaign_chain_returns_empty_for_campaign_backed_admission_failure`
  - `_layer3_campaign` と `_campaignless_failure_cell` (`:5079-5106`) の exact decision/disposition 部分を再利用し、persisted report と `campaign.lock` を除去。
  - 鎖が例外を出さず `frozenset()` を返すことを assert。これにより `:4911-4923` の既存受理を変えず、観測結果だけを固定する。

既存 campaignless test (`test_trial_registry.py:2330-2359`) と zero-cell test (`:2301-2327`) の期待値は変更しません。変更の必要もありません。

## 変異候補

| 変異内容 (file:line) | 殺すはずのテスト | 正例 / 負例 |
|---|---|---|
| 比較成功後の `validated_campaign_ids.add(campaign_id)` を削除 (`autonomous_trial_completeness.py:5033` 後) | `test_campaign_chain_returns_freshly_rebuilt_campaign_ids`、正常 build acceptance | 正例 |
| ID を `seen.add` の直後 (`:4897`) に追加し、failure branch の `continue` 前でも検証済みにする | campaign-backed empty-run acceptance 負例、empty-return unit test | 負例 |
| 受入の returned-ID 差分 hard failure を削除 (`trial_registry.py:6085` 後) | campaign-backed empty-run acceptance 負例 | 負例 |
| returned set にかかわらず空走 gate を常時発火させる | 既存正常 build acceptance `:1781-1861` | 正例 |
| `do_build=False` も空走として拒否するよう branch 境界を移す (`trial_registry.py:6010-6013`) | `test_p5_six_complete_terminal_reports_pass_acceptance` | 正例 |

## 親 brief の誤り

| brief 箇所 | 照合結果 |
|---|---|
| `brief.md:35-42` | campaign 付き admission failure が常に鎖後 post-check まで到達する、という記述は条件不足。全 6 件が campaign-backed build 扱いなら `trial_registry.py:5632-5648` の measurement-target が先に拒否する。no-build 等を含む混在束なら記載どおり post-check へ到達する |
| `brief.md:41` | 挙げられた `test_autonomous_trial_completeness.py:5038 / :5072` は、persisted report が存在する場合と独立 admission が成功する場合の拒否テスト。`ArtifactAdmissionError` を捕捉して `continue` する `autonomous_trial_completeness.py:4917-4923` の正常 return は直接固定していない |
| `brief.md:43-44` | zero-cell の最初の拒否位置は `trial_registry.py:5557-5561`。`:6015-6018` は同じ message の後段検査だが現行フローでは到達しない |
| `brief.md:45-47` | 「3 形すべて現状でも拒否」は正しい。上記のとおり materialized failure と zero-cell の最初の拒否位置には補正が必要 |
| `brief.md:48-51` | `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` は `paper_story_a1_paired.py:167-173` で `trial_registry.py` を含むが、もう一方の変更候補 `autonomous_trial_completeness.py` は含まない。「2 production module を pin」と読むなら誤り |
| pin 方式 | 固定 digest 型ではなく live tree 追随型。`:4379-4404` が指定 HEAD の blob OID と working SHA-256 をその場で作り、`:4420-4430` が binding 化、`:7195-7219` が同じ HEAD と現在 bytes に再照合する。テストも `test_paper_story_a1_job_contract.py:391-409` で現在 HEAD から binding を導出するため、編集を commit した新 HEAD では再導出されて緑になる |
| `brief.md:52-55` | brief 記載の T-524 区間 `trial_registry.py:65-3413` および `6193/6360` と、主案の `6070-6094` は行区間上は重ならない。`autonomous_trial_completeness.py:4815-5034` も brief が挙げる T-524 面外。ただし射影に T-524 worktree の diff は無いため、未 commit 現物の独立再走査は親が行う必要がある |
| (P1)〜(P4)、分割方針 | 上記の prepass 到達条件を補えば妥当。producer、standalone verifier、post-check、no-build branch を変更する必要はない |

静的検査のみで、pytest は実行していません。

## 総括

- 推奨は、比較成功後の campaign ID を鎖から返し、受入だけが不足 ID を hard failure にする (P1) です。
- campaignless の既存 message、zero-cell、no-build、正常 build、既存 post-check は変更しません。
- 現行受理集合は変わらず、campaign 付き admission failure の拒否理由だけが file 不在から直接の Layer 3 空走へ変わります。
- `trial_registry.py` の source pin は live tree 追随型ですが、`autonomous_trial_completeness.py` はその tuple に含まれません。
- 親は campaign-backed failure fixture の pre-chain 整合性、exact message、正常 build/no-build 回帰、T-524 live diff の非重複を実測してください。