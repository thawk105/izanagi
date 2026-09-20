## 変更の要約

指定3ファイルだけを変更し、差分をworking treeに残しました。HEADは`800178b39`、stagingは空です。

- [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl/orchestrator/campaign/s8b_ratified_freeze.py)：journalのexact key・型・構造検査、導入区間helper、世代文書導入`{G}`、保証境界の説明を実装。**+99／−10行**。
- [test_s8b_ratified_verify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl/orchestrator/tests/test_s8b_ratified_verify.py)：fixture optionと新規17関数・63ケースを追加。**+309／−3行**。共通helperとparametrizeにより目安より小さい差分です。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl/orchestrator/tests/test_s8b_oracle_driver.py:131)：指定commentとrefusal第2要素だけを更新。**+7／−5行**。

## 受理集合の変化

| 対象 | 変更前 → 変更後 |
|---|---|
| reservation | 未知eventとして拒否 → campaign前の高々1件を受理 |
| binding付きcampaign | exact key不一致 → 同値binding付きreservationとの組を受理 |
| artifact導入 | 全pathが`G`で導入 → 各pathの一意・非merge導入`C ≤ i ≤ G`を受理 |

journalは裁定§2-1項6の2形だけを追加しています。片側claim、key片欠け、型不正、不一致、多重・後置reservation、他eventへのbinding keyは拒否します。

lineageは裁定§2-2項5どおり、`i=C`、`i=G`、中間導入、分岐後の合流を受理します。上限検査は重複検査と明記し、実時間順やPBS jobの外部認証は保証していません。

## 不変の確認

静的比較で以下を確認しました。

- 既存production関数で本文を変更したのは`_validate_journal`と`_launch_validate`だけ。
- 段階4全体、cert検査block、scan exemption、導入履歴helper、批准側検査はbyte不変。
- 既存全eventの集合は不変。`session` pinも維持。
- 既存test本文・期待値は不変。wrong_g=Aの`generation-introduction`、C=Gの`cert-lineage`を維持。
- fixtureの追加optionをFalseとして分岐を畳むと、変更前のASTと一致。
- refusal第1要素は不変、第2要素は`p3-before-g1.json`の`refusals[1]`とbyte一致。
- 指定された編集禁止ファイル、docs、hooks、設定、outputへの差分なし。
- `git diff --check`はrc=0。

## 新 test 一覧

以下のnodeid共通prefixは  
`orchestrator/tests/test_s8b_ratified_verify.py::test_t2810_` です。全63ケースが通過しました。

| suffix／件数 | 独立した根拠・対応変異 |
|---|---|
| `launch_positive[default,certificate,bound,unbound]`／4 | P-a〜P-d、実Git導入点とpublic launch。M1・M2・M14 |
| `fixture_conflicting_options`／1 | fixtureの矛盾option拒否 |
| `unknown_journal_event`／1 | N-6、未知event拒否 |
| `binding_one_sided_claim`／2 | N-7、両方向のclaim欠落。M3 |
| `binding_campaign_without_reservation`／1 | reservation不存在のclaim拒否。M3 |
| `binding_missing_key`／4 | N-8、各event×各key、`schema-keys` |
| `binding_invalid_type`／12 | N-9、各event単独と両event同値の不正型。M4 |
| `binding_value_mismatch`／2 | N-10、各binding値の不一致。M5 |
| `reservation_invalid_integer`／21 | N-11、7数値field×0／bool／str。M6 |
| `reservation_invalid_other_type`／3 | N-11、formulaとbool field。M6 |
| `reservation_duplicate`／2 | N-12、binding有無。M7 |
| `reservation_after_campaign`／2 | N-13、binding有無。M8 |
| `other_event_binding_rejected`／1 | 他eventの未知key拒否 |
| `artifact_lineage_rejected[before-cert,merge,multiple]`／3 | N-1〜N-3、実Git DAG・endpoint一致。M9・M10・M11 |
| `artifact_interval_positive[intermediate,branch-join]`／2 | 裁定で一般化した区間の正例 |
| `generation_introduction_independent`／1 | N-4の独立fixtureによる追加確認。M12 |
| `artifact_upper_bound_helper`／1 | N-14、重複上限検査の単体試験。M13のみ |

各journal負例はcommit前に変形し、同じ構築経路の無変異対照がpublic launchを通ります。N-5は既存`test_certificate_same_commit_as_generation_rejected`で確認しました。

メモリ上のproduction AST変異probeでは、**M0はSURVIVED、M1〜M14はKILLED**。M3〜M11とM13は`DID NOT RAISE`、M12はexact cause assertionの赤化、M1・M2・M14は正例の拒否で検出しました。M13の証拠はhelper単体だけです。親の独立cloneによる正式matrixは未実施です。

## 実走結果

指定の`PYTHONPATH=. python3 -c "...pytest.main(...)"`経路で実行しました。

| 対象node／選択 | 件数・結果 | rc |
|---|---:|---:|
| verify：`-k 't2810 or certificate_same_commit_as_generation_rejected'` | **64 passed** | 0 |
| verify：最終版全件 | **151 passed、101 failed／全252件** | 1 |
| verify：`test_floor_source_introduction_must_be_exact_generation_commit`単独 | fixture構築失敗、validator未到達 | 1 |
| oracle：`-k 'activated_g1 or refusal'` | prewarm後も完了結果なし、中断。成功件数未確認 | 130 |
| plain-runner全3件＋下記静的3件 | **6 passed** | 0 |
| plain-runner＋preregistration両file＋session pin＋直接構築禁止 | 237 passed、5 skipped、1 setup error | 1 |

静的3件のnodeは以下です。

- `test_s8c_preregistration_invariant.py::test_machine_contract_function_names_exist_and_checked_set_is_exact`
- `test_s8b_terminal_evidence.py::test_campaign_trust_root_equals_ratified_exact_thirty_keys`
- `test_s8b_ratified_freeze.py::test_no_production_module_constructs_ratified_freeze_directly`

全件回帰の確認済み失敗は、sealed snapshotのsocket送信が`PermissionError: Operation not permitted`となり、`snapshot cleanup failed`へ至るものです。**既存回帰の検査本体を通せておらず、全件緑とは扱いません。**

広いmeta走のsetup errorは`test_repository_candidate_uses_real_s8c_budget_module`のGit処理rc=128です。5 skippedは既存growth holdによるものです。

直接呼出しでも次を確認しました（rc=0）。

- `test_t2810_launch_positive(bound)`：`DIRECT_CALL_PASS`
- `test_t2810_generation_introduction_independent`：`DIRECT_CALL_PASS`
- `test_t2810_artifact_upper_bound_helper`：`DIRECT_CALL_PASS`
- `test_certificate_same_commit_as_generation_rejected`：`DIRECT_CALL_PASS`

## 波及

- `_validate_journal`のproduction callerは`_launch_validate`。他callerはverifyのrequired-consumer試験と、ratified-freezeのperf-preflight試験です。
- `_validate_result`は`journal["records"]`からcampaign全体をwall_ledgerへ再導出します。binding keyは保持しています。
- `verify_floor_artifact_with_live_admission(..., sessions=...)`はsession系recordだけを抽出するため、reservation追加は入りません。
- `journal["campaign"]`のhash・receipt consumerは不変です。
- `_launch_validate`の2 caller、`launch_validate`／`reverify_published_freeze`へ共通修正が伝播します。live policy分岐は不変です。
- driftguardsの共用定数参照2箇所（287、326行）は無編集です。
- 独立fixtureの既存callerは、admission拒否3件、時刻配線2件、protocol／closure raw hash配線2件、cert raw hit、C=Gの計9関数。すべてoption defaultのままです。

## 未了・懸念

- sandboxで到達できなかった既存回帰、特にproduction-emitter版wrong_g=Aは親環境で再実走が必要です。
- oracle焦点走は未完了。refusal更新の確認は本段では静的byte比較までです。
- 親の正式変異matrix、実repoのloader・historical reverify・live P3再検証は残っています。
- 独立fixtureの成功はlaunch coreの証拠です。loader込みの成功、live launch成功、W-4／W-5開始許可、旧checkoutへの移植結果は主張しません。

## 総括

**指定3ファイルの実装を完了し、新規63ケースと既存C=G負例が通過しました。** 差分は未commitで残しています。全件回帰はsandbox制約下で失敗が残り、oracle・正式matrix・実repo受入は親での検証待ちです。