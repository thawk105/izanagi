## 総括

NO-GO。producer 5 件と現行 S8C prereg の exact 3 は支持するが、certified report/read 層と qualification ledger 検証が未閉包。  
32 件の lock bytes は全て v1 だが、独立した 14-key fixture/golden は存在する。T-396 も closure pin を同時編集する。  
歴史 raw の扱い、qualification schema、所有権を確定してから land 可。

### [B-1] producer 集合は独立導出で 5 件に閉じる

- 分類: refuted
- 場所: `orchestrator/campaign/pipeline.py:1243-1311`, `orchestrator/campaign/guided.py:131-141`, `orchestrator/qualification/artifacts.py:749-784`
- 攻撃または欠落: `wal.log → wal.append`、`event_sink.emit → append_jsonl`、test-only の直接 `wal.append`、recovery の `_append_records_locked` まで辿った結果、production は campaign WAL 3 件＋qualification 2 件の計 5 件で、追加 producer は見つからない。`s8b_oracle_driver.py:721-724` は `SESSION_STAGE`、recovery は `STAGE_ABORT` のみ。
- 成果物影響: producer の受理集合に plan が未列挙の production 経路は残っていない。
- 最小修正: `test_t674_qualification_contract_lanes.py:277-329` とは別に、5 producer と test-only bypass を固定する repo-wide census を追加する。

### [B-2] certified report/read 層が receipt を再検証しない

- 分類: real
- 場所: `orchestrator/campaign/s1_report.py:314-365,385-424`, `orchestrator/campaign/wal.py:652-704`, `tools/plotting/plot_backoff.py:114-145`
- 攻撃または欠落: S1 は `CERTIFIED_ACCEPTANCE` の lock-only epoch gate 後に WAL を直接読み、`STAGE_COMMIT` の存在だけで sample を採用する。tools の plot は `HISTORICAL_RAW` で同じく commit だけを certified bench として扱う。plan の B 所有ファイルにはこの層がない。
- 成果物影響: receiptless・改変 COMMIT が S1 sample、fitness、plot の母集合へ入り、certified 選択・レポート値が増える。
- 最小修正: `wal.py:652-704` に目的別 receipt 検証を追加し、`artifact_admission.py:937-1048` と `s1_report.py:424` から呼ぶ。`HISTORICAL_RAW` は明示的に非認証出力へ限定する。

### [B-3] qualification sink の schema/replay 閉包が不足

- 分類: real
- 場所: `orchestrator/qualification/artifacts.py:749-784,854-955`, `orchestrator/qualification/t126_evaluation_event_schema.json:14-37`
- 攻撃または欠落: qualification receipt を外側 event に追加すると strict schema と `validate_member_evidence()` が拒否する。payload 内へ隠すと現行 validator は receipt の lock identity・verdict・一回性を検証しない。`append_jsonl()` も read→append 全体を lock していない。
- 成果物影響: qualification の 2 producer は書けないか、receipt 風の偽 event が ledger・qualification result に残る。
- 最小修正: `artifacts.py:749-784,854-955`、`t126_evaluation_event_schema.json`、`select_source_pair():801-851` を同時更新し、receipt 検証から append までを flock 下に置く。

### [B-4] test helper の receiptless COMMIT 集合が未列挙

- 分類: real
- 場所: `orchestrator/tests/test_artifact_admission.py:583-590,665-681`, `orchestrator/tests/test_screening_driver.py:114-116,153-156,238-240`, `orchestrator/tests/test_s8b_oracle_report.py:594-598`
- 攻撃または欠落: plan の「既存 test files の機械的 fixture 移行」だけでは、post-policy fixture と legacy raw fixture の区別が不明。低層 gate を通すために bypass を作るか、fixture を壊す危険がある。
- 成果物影響: 新しい negative control が receiptless helper によって恒真化し、receipt gate の失敗をテストが検出できなくなる。
- 最小修正: receiptless COMMIT の全 test file を列挙し、legacy raw writer と新規 receipt helper を明示的に分離する。

### [B-5] 32 件 v1 lock から fixture/golden 無影響を一般化できない

- 分類: real
- 場所: `orchestrator/tests/test_artifact_admission.py:45-60,367-400,1111-1119`, `orchestrator/campaign/campaign_lock.py:27-44`
- 攻撃または欠落: 32 件の `campaign.lock` は全て `authority` 無しで、既存 lock bytes が無効化されない点は確認できる。しかし `_EXPECTED_E1_CLOSURE_PATHS` は独立した exact 14 fixtureであり、`len(...)=14` も残る。逆に `approval_d291.py:271-278` や `test_s8c_preregistration_predicates.py:382-392` の 14 は別契約である。
- 成果物影響: fixture を更新しないと exact-20 E1 の受理検査が落ち、全ての `14` を置換すると無関係な publication/evidence 契約を壊す。
- 最小修正: closure 専用の `test_artifact_admission.py:45-60,994-995,1118` と関連 doc だけを exact 20 へ更新する。

### [B-6] `CONTRACT_LOADER_RELATIVE_PATHS` consumer census は一致する

- 分類: refuted
- 場所: `orchestrator/campaign/campaign_lock.py:29,167-185`, `orchestrator/campaign/contract_loader_binding.py:15,72-85,324-377`
- 攻撃または欠落: production 3 file＋test/support 9 file の計 12 fileを独立に検索すると、plan の列挙と同じ集合になる。`campaign_lock_test_support.py:10-20` など動的 helper も漏れていない。
- 成果物影響: path constant の consumer 漏れによる stale map・codec key 受理の追加経路は確認できない。
- 最小修正: 現行 12 file を固定する静的 inventory を追加し、無関係な exact-14 契約を置換対象から除外する。

### [B-7] 判定器 exact 3 は preregistration scope では妥当

- 分類: refuted
- 場所: `orchestrator/campaign/s8c_preregistration.py:43-50,1661-1773`, `orchestrator/campaign/s8c_preregistration_evidence.py:18`
- 攻撃または欠落: `CORE_MODULE_PATH`・`EVALUATOR_MODULE_PATH`・`PROJECTION_MODULE_PATH` が hash/activation の権威集合で、evaluator は core のみを importし、projection は pure leaf。`s8b_oracle_judge.py` は S8B であるため追加は過剰。`s8c_acceptance_receipt.py` も自身を non-certifying と定義する。
- 成果物影響: 現行 `DECIDER_VERSION` の preregistration proof は exact 3 で閉じ、S8B や非認証 receipt の編集で全 campaign を不必要に停止しない。
- 最小修正: exact 3 の根拠を test と裁定文書へ固定する。formal Layer3 acceptance を同じ closure に含める場合は別裁定にする。

### [B-8] 段5は test file で重なる

- 分類: real
- 場所: `s2-plan.md:395-424`, `orchestrator/tests/test_env_contract_activation.py:307`, `orchestrator/tests/test_artifact_admission.py:1323-1654`
- 攻撃または欠落: revised plan では A が `test_env_contract_activation.py` を所有する一方、C の「その他 closure consumer tests/support」に同ファイルが含まれる。B の receiptless fixture 移行は `test_artifact_admission.py` を触り、C も同ファイルの closure fixture を所有する。元案の `ident.py` 衝突は C 所有へ移したことで解消する。
- 成果物影響: 並行 land で receipt fixture または exact-20 map の片方が失われ、単独では緑でも統合後の受理集合が変わる。
- 最小修正: `test_env_contract_activation.py` は A、`test_artifact_admission.py` は C の単独所有にし、B は helper API を先に提供して C を直列化する。

### [B-9] P5 の 762→1286→1287→1252 は技術的必須ではない

- 分類: refuted
- 場所: `s2-plan.md:430-447`, `orchestrator/campaign/ident.py:249-258,469-483`
- 攻撃または欠落: T-762 の activation wrapper と T-1286 の WAL/qualification receipt は独立して実装できる。T-1287 の批准 entryだけが、T-1252 と全 enforcement bytes 確定後でなければ失効する。
- 成果物影響: 親順序を維持しても certified 値は改善せず、不要な直列化だけが wave を遅延させる。
- 最小修正: A/B を並行、C を最終統合、exact-20 digest 算出と人間批准を最後に固定する。

### [B-10] 既存 AST 設計テストの `len` は変更してはいけない

- 分類: refuted
- 場所: `orchestrator/tests/test_campaign.py:7024-7079`, `orchestrator/tests/test_t674_qualification_contract_lanes.py:277-329`
- 攻撃または欠落: `test_evaluate_commit_writes_are_syntactically_verify_gated` の `len(commit_calls)==2` は `pipeline.evaluate` 内の WAL writer だけを pin し、T674 の `len==4` は WAL 2＋qualification 2 を pin する。これを全 producer の 5 件へ変更すると、既存診断の関数スコープを失う。
- 成果物影響: verify 前 COMMIT の既存検出が弱まり、誤った writer の追加が別の repo-wide census に隠れる。
- 最小修正: 既存 assertion は維持し、guided・低層・qualification の全数検査を別テストとして追加する。

### [B-11] T-396 は contract 面で実質衝突する

- 分類: real
- 場所: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t396-hole-allowlist/s2-plan.md:256-260,368`, `orchestrator/tests/test_t671_source_binding.py:37-41`
- 攻撃または欠落: T-396 は新 module を `campaign_lock.py` と `qualification/contract.py` の trust closure に追加し、`test_t671_source_binding.py` を更新する計画である。本 wave C も同じ closure constant・exact-list pin・資格 identity を編集する。
- 成果物影響: branch 差分が現時点で clean でも、並行 land の順序次第で exact-20 path、T-396 の追加 path、known-good digest のいずれかが欠落する。
- 最小修正: closure pin 関連 file を共有編集面として予約し、どちらかを先に land してから rebase・exact-list 検査・digest 再算出を行う。

## 裁定パッケージ候補

- `s1_report.py` と `tools/plotting/plot_backoff.py`、`p2_2_report.py`、`backoff_repro.py` を「歴史 raw 専用」とするか、receipt 検証を要求するか決定する。前者なら certified selection へ渡せない型・ラベルを追加する。
- `qualification/contract.py:39-77` と `silo_ladder_rung1.py:262-286` は独立した identity root である。T-1287/T-1252 の exact-20 closure に含めるか、campaign lock scope 外として明記する。
- `s8c_preregistration_evidence_contract.v1.json:248-274` が宣言する将来の `s8c_result_judge.py` と、`trial_registry.py:2556-2640`／`autonomous_trial_completeness.py:2837-3005` の formal acceptance を、現 wave の preregistration decider scope に含めるか裁定する。
- `hooks/README.md:138-140` と `hooks/guard_write.py:8-13,248-253` は COMMIT の唯一経路を `pipeline.evaluate()` と記載するが、実際には `guided.py:141` も書く。runtime gate の代替ではないことを明記し、文書・保護面の ownership を割り当てる。