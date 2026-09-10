### 所見 1

- **主張** `origin_terminal_projection` は v2 receipt の許可 field だが、parse 後の型から脱落し、`VerifiedAcceptanceReceipt` でも report・lifecycle との一致を検証しない。
- **根拠** `orchestrator/campaign/s8c_acceptance_receipt.py:66-67` は field を許可する一方、`AcceptanceReceiptTrial` は保持せず (`:95-107`)、構築時にも読まず (`:370-400`)、full verifier も `arm_execution` だけを照合する (`:627-711,851-867`)。producer は検証済み projection を receipt に書く (`orchestrator/campaign/trial_registry.py:2897-2903`)。既存 test は raw JSON 同士の一致だけを調べ、parsed capability が保持・再検証することを確認しない (`orchestrator/tests/test_trial_registry.py:1182-1215`)。
- **成果物影響** receipt 内の `formal_receipt_sha256`・`evidence_root_sha256` 等を report/lifecycle と異なる値へ変えて commit しても verified capability が成立し、receipt 台帳の origin proof 参照と実 report が食い違う。
- **GO / NO-GO** **NO-GO**。field を型へ保持して report・lifecycle と照合するか、v2 schema から受理しない形にし、改変負例を追加する必要がある。

### 所見 2

- **主張** 新設 meta-test は machine 条件内でも解釈できない `reachable_from` root を記録せず捨てるため、裁定済みの `t822.m8-meta-silent-skip` を塞いでいない。
- **根拠** helper は `root.isidentifier()` かつ既に module に実在する名前だけを `checked` へ入れ、それ以外を記録せず通過する (`orchestrator/tests/test_s8c_preregistration_invariant.py:181-188`)。その後の assert は `checked` 21 tuple と `missing` だけである (`:275-280`)。現契約だけでも C04 の `run_trial crash handler` / `run_trial preflight` (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:168-177`) と、C10 の別 module に置かれた `assert_trial_registry_acceptance` (`:394-415`) がこの経路で黙って除外される。負例は C09 の有効 identifier 改名だけである (`test_s8c_preregistration_invariant.py:283-304`)。
- **成果物影響** machine 条件へ非 identifier root や誤 module rootを追加して contract hash pinを更新すると meta-test が緑のままになり、g6/g7 の `evidence_contract_sha256` と `protected_sha256` が未検査の consumer 宣言を正当な契約として固定する。
- **GO / NO-GO** **NO-GO**。検査対象外 tuple と除外理由も exact pin するか、非 identifier root を明示 allowlist なしでは赤にする必要がある。

### 所見 3

- **主張** U3 の docs 更新範囲は不足しており、裁定に列挙された四面だけを直すと T-1311 前の別記述が規範 g6/g7 に残る。
- **根拠** U3 は §6 条件2、衝突(d)、「現在地」、§1 の理由落ち説明だけを指定する (`/work/1/SFC/tanab/dev-wave-jobs/t822-c02-receipt-v2/s4-adjudication.md:177-184`)。しかし規範文書には以下も残る。
  - terminal report が measurement HEAD を持たないとの記述 (`docs/phase3-8c-preregistration.md:53-55`)。実装は report と run-start に記録する (`orchestrator/campaign/p3_autonomous_workload_trial.py:2684-2693,3513-3522`)。
  - arm を campaign ID 自体へ埋め込む旧要件 (`docs/phase3-8c-preregistration.md:83`)。現実装は arm/digest の共通 namespace と、別 field の campaign binding を使う (`p3_autonomous_workload_trial.py:760-790`; `trial_registry.py:2758-2777`)。
  - evaluator 数が 6 のまま (`docs/phase3-8c-preregistration.md:261-265`)。実装は C02 を含む 7 件 (`orchestrator/campaign/s8c_preregistration_evidence.py:1760-1772`)。
  - journal/report の二ファイルしか anchor が無いとの説明 (`docs/phase3-8c-preregistration.md:373-376`)。v2 receipt は双方の hash と descriptor 再導出を追加している。ただし bundle 全体の捏造限界は別途残る。
- **成果物影響** これらを残すと `normative_body_sha256`、条件2の個別 hash、`protected_sha256` が旧事実を凍結し、契約 JSON・判定結果・規範本文が異なる arm-binding 状態を台帳へ記録する。
- **GO / NO-GO** **NO-GO**。上記全文脈を U3 の更新対象へ追加すべきである。hash 閉包自体は `prepare_revision` が `section6_condition_hashes`、`normative_body_sha256`、contract hash、protected hashを再導出する (`orchestrator/campaign/s8c_preregistration.py:1823-1831`)。contract の逐語 pinも既に新値へ更新済み (`orchestrator/tests/test_s8c_preregistration_core.py:1158-1161`)。

### 所見 4

- **主張** 「U3を最後に1回だけ」は、U3生成後からlandまでに並行waveが先行landするraceを扱っていない。
- **根拠** 裁定は受入前に一度だけ生成し、先行landが既に見えた場合だけg7へ作り直す (`s4-adjudication.md:93-103`)。しかし標準landはstaleを検出するとfresh contextで新mainを固定SHA mergeして受入を再走する (`docs/dev-wave/operations.md:149-158`)。このraceがU3後に起きると、自waveのg6は既に存在し、相手のg6を通常mergeできないという同裁定の禁止 (`s4-adjudication.md:96-99`) と衝突する。
- **成果物影響** 誤ってmergeすればg6重複または不正な `supersedes_sha256` でfreeze chainとactivationが壊れ、規律どおり停止すればこのwaveはland不能になる。
- **GO / NO-GO** **NO-GO**。U3後のstale時は自wave生成recordを成果集合から外し、新main統合後に次世代を再生成し、全受入を再走する、と明記する必要がある。「1回」は各確定main snapshot当たりと定義すべきである。

### 所見 5

- **主張** C03/C07/C08 の旧名をscope外に残す裁定と、非機械条件をmeta検査対象外にする実装は整合している。
- **根拠** C03/C07/C08 の `accept_trial` は契約に残る (`s8c_preregistration_evidence_contract.v1.json:112-146,282-290,318-354`)。meta helper は `machine_checkable is not True` を明示的に除外する (`test_s8c_preregistration_invariant.py:161-166`)。別テストが machine 集合を C01/C02/C04/C09/C10/C11/C12 のexact集合として固定する (`orchestrator/tests/test_s8c_preregistration_predicates.py:1921-1942`)。
- **成果物影響** このscopeのままなら現在の受理集合・12条件の判定値・certified選択は変わらず、旧名の影響は将来C03/C07/C08を機械化するwaveに限定される。
- **GO / NO-GO** **GO**。ただし machine 条件内の黙ったskipは所見2の別問題である。

### 所見 6

- **主張** 所見1を除く公開定数・型・allowlistのlive callerはv2/legacyへ追随しており、新規test fileの自走harnessも自動発見される。
- **根拠**
  - `MANDATORY_NON_CERTIFYING_REASONS`、`SCHEMA_VERSION`、`LEGACY_SCHEMA_VERSION` のproduction callerは parser/verifier自身と `trial_registry.py:2905-2915`。legacy fixtureは `test_s8c_acceptance_receipt.py:95-128` と `test_layer3_report.py:306-323`、v2 producer/consumerは `test_trial_registry.py:972-1038,1179-1187,1533-1548` へ分離済み。
  - `AcceptanceReceipt` / `VerifiedAcceptanceReceipt` の外部production consumerは `layer3_report.build_accepted_report` (`orchestrator/campaign/layer3_report.py:569-600`)。`AcceptanceSummary` は `trial_registry` 内のproducer・CLI serializerだけ (`trial_registry.py:241-247,2940-2959`)。
  - `DECIDER_VERSION` はv3でrecord生成とruntime一致判定へ流れ (`s8c_preregistration.py:50,1735-1746,1817-1831`)、外部参照は関連testのみ。g5のv2はU3の次世代発行まで意図的に旧tipである。
  - `MACHINE_CHECKABLE_CONDITION_IDS` と `SATISFIABLE_CONDITION_IDS` は evaluator registry・runtime allowlist・predicate testsだけ (`s8c_preregistration_evidence.py:1760-1772,1871-1886`)。`NEGATIVE_CONTROL_CASES` は同test file内だけで、7件のexact集合・全parametrizeへ流れる (`test_s8c_preregistration_predicates.py:1921-1948`)。
  - 新規fileは `pytest.main([__file__])` を実行する (`test_s8c_acceptance_receipt_v2.py:328-329`)。plain-runner meta-testはdirectoryの全 `test_*.py` を列挙し、`pytest.main` をharness signalとして認識する (`test_plain_runner_coverage.py:25-46,60-86`)。
- **成果物影響** 追加修正なしでもlegacy receipt受理、v2発行、v3 decider、7 negative controls、CLI summaryの値は旧挙動へ黙って退行しない。
- **GO / NO-GO** **GO**。pytestは制約どおり未実走であり、緑とは記録しない。`git diff --check` の静的検査のみ成功した。

## 総括

**NO-GO**

must-fix:

1. v2 receiptの `origin_terminal_projection` をverified型へ保持し、report・lifecycleと再照合する。
2. machine contract meta-testの除外集合と理由をexact pinし、非identifier・誤module rootの黙ったskipを止める。
3. U3の規範文書更新を、measurement HEAD、§3のarm要約、7 evaluator、§7のhash anchor説明まで広げる。
4. U3後に並行waveがlandした場合のrecord破棄・次世代再生成・受入再走手順を明記する。