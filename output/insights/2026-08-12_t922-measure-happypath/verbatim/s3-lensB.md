静的検査結果は **NO-GO**。pytest は未実施。指定された「開」5件（brief #3〜#7）はすべて現行 production に未実装で、重複実装は確認できなかった。一方、計画には層の抜け、guard の未解決、fixture・変異帰属の漏れがある。指定範囲に未確認箇所はない。

### BLOCKER — S-C の guard producer は「実装不能」ではなく、現計画では未解決

根拠：

- coordinator config は7 fieldのみで、`tools/pegasus/t810_coordinator.py:474-479`
- guard evaluator は qstat transcript、owner、phase、B job identity を要求するが、production caller がない。`tools/pegasus/t810_guard.py:333-387`
- receipt は qsub 前に読む。`tools/pegasus/t810_coordinator.py:686-694`
- B job identity は `submit_group()` 後に初めて得られる。`tools/pegasus/t810_coordinator.py:807-829`
- そのため、receipt を dataclass に詰め替えるだけでは偽の `allow` を通す。`tools/pegasus/t810_coordinator.py:357-386`

configを増やさず、内部のqstat snapshot provider、submit後のB identity取得、pre-release再評価、deny時のwithdrawを2相化する設計は可能。ただし新API・順序・receipt schemaが必要で、現在の計画のままでは実装できない。

budgetだけ実ledger照合してguardを形式検査にするのは、部分実装としては可能だが、S-C全体を完了とは書けない。`reserve_budget()`後に検証するなら、検証後のledger再変更を防ぐロック範囲も必要。`tools/pegasus/t810_budget.py:486-574`、`s2-plan.md:141-175`

親が撤回すべき主張：

- 「S-Cをこのwaveでproduction結線できる」
- 「guard/budgetを実施済みとして台帳に転記できる」
- 「guard producerは実装不能なので裁定だけでよい」という断定。正しくは「現APIのままでは未解決で、2相設計の裁定が必要」。

### BLOCKER — effect boundary に直接 bypass が残る

S-Bを `coordinate()` にだけ置く計画では、`_coordinate_authorized()` が受け取る caller supplied `repository_roots` と `prepare_group()` のmkdir・ファイル生成を迂回できる。

- `tools/pegasus/t810_coordinator.py:1458-1467`
- `tools/pegasus/t810_coordinator.py:657-662`
- `tools/pegasus/t810_coordinator.py:572-582`

また、S-Aの再ハッシュを `_scheduler_effect()` にだけ置くと、直接呼べる `_subprocess_scheduler()` がその検査を通らず `subprocess.run()` する。

- `tools/pegasus/t810_coordinator.py:773-804`
- `tools/pegasus/t810_coordinator.py:1634-1654`

現行の非テストcall graphに隠れた別callerはないが、private名はcapability boundaryではない。これは既存判断 D331（`docs/decisions.md:14857-14871`）とも一致する。

親が撤回すべき主張：

- 「coordinateに結線すれば全production入口を覆える」
- 「S-A/S-Bで全effect層が閉じる」

検査は共通effect boundaryへ寄せるか、直接入口を明示的に非production・非capabilityとして封じる必要がある。

### MAJOR — S-Dはproduction正例経路ではなく、低層fixture統合に留まる

計画のS-Dテストは `_prepared` → `prepare_group()` / `submit_group()` → `t810_pbs_wrapper.main()` であり、top-level `coordinate()` や coordinator CLI `main()` を通らない。

- `s2-plan.md:201-234`
- `orchestrator/tests/test_t810_coordinator.py:258-273`
- 現在の coordinator `main()` のテストは異常系のみ。`orchestrator/tests/test_t810_coordinator.py:487-497`
- wrapper CLIの正例テストは存在しない。

したがって、artifactからwrapper CLIまでの境界テストとしては有用だが、「production正例経路を1本通す」というheadlineは過大。

親が撤回すべき主張：

- 「S-Dでproduction正例経路が確立する」

`coordinator artifact → wrapper CLI integration` と呼ぶか、top-level coordinator経路を追加する必要がある。

### MAJOR — `pbs_wrapper.__file__` authority案はwrapperには効くが、executable authorityを解決しない

coordinatorは既に `t810_pbs_wrapper` をimportしているため、`pbs_wrapper.__file__` の実bytesをauthorityにする案は、P1/D328と矛盾しない。fixtureの `package/wrapper.py` は「たまたま一致」ではなく「一致必須」になり、wrapperについては強化になる。

ただし、production側に `package/wrapper.py` を生成・stagingするproducerは確認できない。`wrapper_path` のproduction producerも見当たらず、fixtureだけではproductionの結線を証明しない。

さらにexecutableについては、

- runner policyがcaller slotの `binary_sha256` から生成される。`tools/pegasus/t810_runner_policy.py:60-77`
- preregistration projectionに独立したbinary bytes authorityがない。`orchestrator/campaign/t810_validator.py:634-658`

したがって、自己整合した任意executableはなお排除できない。

親が撤回すべき主張：

- 「module bytes authorityだけでwrapperとexecutableの両方が閉じる」
- 「S-D fixtureがproduction stagingを証明する」

### MAJOR — fixture波及一覧に漏れがある

`wrapper_sha256|binary_sha256` の意味単位で見ると、計画の20件だけでは不十分。

漏れ：

- coordinator共通 `_config` のconsumer  
  `orchestrator/tests/test_t810_coordinator.py:702-714`
- wrapper側 `_request` helper  
  `orchestrator/tests/test_t810_pbs_wrapper.py:269-364`
- 同helperを使う直接wrapper実行群  
  `orchestrator/tests/test_t810_pbs_wrapper.py:421-597`

特にwrapper test fixtureは `wrapper_sha256=H` を持つが、実際の `package/wrapper.py` を作っていない。

一方、`orchestrator/tests/test_mutation_fanout_contract.py:306` の `wrapper_sha256` は別schema・別責務であり、T-922のfixture波及には含めない。ただし、その除外理由は計画に明記すべき。

親が撤回すべき主張：

- 「20テストでfixture影響範囲を全列挙した」

### MAJOR — 変異の単独帰属が成立しない検査がある

- `--request`をcanonical scriptから削除する変異は、既存の  
  `orchestrator/tests/test_t810_coordinator.py:465-475`  
  が既にwrapper argument parserで検出する。新S-Dテスト単独の証拠にはならない。
- `_read_regular_bytes()` / wrapper `_sha256_file()` のbefore/after fingerprintを削除する変異を単独で殺すテストが計画にない。  
  `tools/pegasus/t810_coordinator.py:169-196`、`tools/pegasus/t810_pbs_wrapper.py:527-537`
- `prepare_group()` のwrapper検査は、後段の `publish_wrapper_request()` でも拒否され得る。後段で拒否されたことだけを確認するテストは先取りされる。
- wrapper側のbinary hash検査は、既存のrunner policy digest照合にも依存する。`tools/pegasus/t810_pbs_wrapper.py:341-368`

親が撤回すべき主張：

- 「S-A〜S-Dの各検査に、その検査だけを殺すテストがある」

各境界について、後段検査を無効化した状態でも対象検査だけで副作用を止めるテストが必要。

### MAJOR — 台帳転記は1件不足。その他のactive行には追加漏れなし

focusのactiveな partial/regressed 行は次のようにS-A〜S-Dへ対応している。

- A-1 → S-C
- A-2 → S-A
- A-7 → S-B
- A-8 / B-4 → S-A
- B-3 → S-D

B-9はbrief上で現行mainでは閉鎖済みなので、追加の未転記とは数えない。

ただし、focusのA-2/A-8に含まれる「callerと独立したauthorityがないため、自己整合した任意wrapper/executableを拒否できない」という核心問題が、T-922の実装項目・裁定項目として明示転記されていない。計画には未greenの preregistration test として現れるだけである。`s2-plan.md:89-96`

親が撤回すべき主張：

- 「focus reviewのmust-fix 7件がT-922へ完全転記済み」

wrapper authorityとexecutable authorityを別々の裁定パッケージ候補として台帳に追加すべき。

### MINOR — 所有分割は可能だが、author-2先行は必須ではない

author-1とauthor-2のproduction file ownership自体は分離できる。budget verifierのAPI署名を先に合意すれば、author-1はその契約に対してcoordinator/testを並行実装できる。

必要なのは：

- API契約の先行合意
- 最終fixture・integrationの直列化
- guard producerは裁定前にdead APIとして実装しないこと

親が撤回すべき主張：

- 「author-2のpatchをauthor-1へ展開するまでauthor-1を起動できない」

これは実装上の必須依存ではなく、統合時の依存。

### MAJOR — 現計画の一waveは過大

概算では、guardを除くS-A/S-B/S-D＋budget verifierでも、production変更・schema・fixture・integrationを含めて約250〜450行規模。guardを2相化し、snapshot provider、post-submit identity、withdraw、receipt schemaまで含めると、さらに約150〜300行以上と新しい裁定が必要になる。

したがって、

1. wrapper/executable authority、S-A、S-B、S-Dの境界を先に裁定・実装
2. guardの2相producerとbudget実ledger結線を別waveへ分離

が妥当。少なくとも現在の「S-A〜S-Dを一括でproduction保証にする」というscopeは撤回すべき。

## 総括

**NO-GO。BLOCKERは2件。**

- S-C guard producerが未解決で、形式receiptだけでは実効性がない。
- coordinator内の低層effect入口（特に `_subprocess_scheduler()`）が新検査を迂回できる。

「開」5件の既存実装見落としは確認できず、重複実装ではない。ただし、現計画をそのままlandすると、guardの実施済み詐称、production正例の過大主張、fixture誤帰属、変異の先取りが残る。