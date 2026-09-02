## 所見

該当なし。blocker 0、must-fix 0、nit 0。

## 攻撃 6 項目それぞれの判定 (破れあり / 破れなし + 根拠)

1. **E0 拒否: 破れなし**

   production で E0 になるのは、exact `bytes` が UTF-8 JSON object に decode され、`schema_version` と予約済み `a1_non_certifying` key を持たない入力である。任意の `authority` key が JSON 内にあっても、schema がなければ v1 とされ、decoded authority は `None` になる。[campaign_lock.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:334) [campaign_lock.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/campaign_lock.py:363)

   この集合は `_recorded_campaign_verifier_epoch` で必ず `E0 / v1-authority-absent` となり、局所分岐で必ず `CampaignVerifierEpochRejected` になる。[artifact_admission.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:898) [s1_report.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:302)

   E0 拒否にならない入力集合は次のとおり。

   - 非 bytes、非 UTF-8、非 JSON、非 object、不正 schema、非 canonical v2、予約 key 入り schema-less objectは、E0 導出前に `ArtifactAdmissionError`。
   - loader commit または 24 path blob map が不正な v2 は、purpose 判定前に `ArtifactAdmissionError`。
   - 保存済み binding が正しい v2 は E1 となり、`HISTORICAL_RAW` から返る。

   変更前に E0 以外で拒否されていたのは、正しい v2/E1 に対して現行閉包取得が `ContractLoaderBindingError` になる集合だけである。[artifact_admission.py:957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:957) これは D1387 が許可した緩和そのもの。lock から `E1-stale` を直接生成する production 経路はなく、それ以外の緩和は見つからない。

2. **負例の実 callee 到達: 破れなし**

   `report` の import は line 17、`_REAL_CAMPAIGN_VERIFIER_EPOCH_FROM_LOCK_BYTES` の保存は line 31、autouse fixture の定義は line 36。fixture の実行前に production 関数を保存しており、lambda ではない。[test_s1_report.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:15) [test_s1_report.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:31)

   `_fixture` が各 lock に書くのは `{"fixture": "s1", "role": role}` だけで、`schema_version` と `authority` はない。[test_s1_report.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:155) したがって `rejected_lock` は production decoder 上の v1 であり、production の記録 epoch 導出で E0 になる。

   `e0` は拒否生成に使われていない。使用箇所は既存 expected dict の `identity_scope` と `excluded_scope` の assert だけである。[test_s1_report.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:503)

3. **正例の実効性: 破れなし**

   helper は HEAD commit の各対象 blob を読み、その SHA-256 を authority に入れて production v2 encoderを通す。[campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/campaign_lock_test_support.py:10) 検証側も同じ記録 commit と対象 path の blob を読み直して照合するため、正例は `_verify_committed_loader_binding` を通る。[artifact_admission.py:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:880) [contract_loader_binding.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/contract_loader_binding.py:386)

   `capture_call_count` の 1 回は line 585 の明示的な失敗 probe だけである。対象 call closure 内の `capture_contract_loader_binding` 呼出しは certified purpose 分岐の line 970 だけであり、記録 binding 検証側にはない。[test_s1_report.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:580) [artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/artifact_admission.py:963) certified に戻れば 2 回目が例外になり、test は epoch assert 前に失敗する。

   spy も有効。`s1_report` は import 済み関数名ではなく `artifact_admission._require_verifier_epoch_for_purpose` を実行時に参照しているため、同 module 属性への monkeypatch が捕捉する。[s1_report.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:305) [test_s1_report.py:587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:587)

4. **追加 import の副作用: 破れなし**

   `sys.path` 操作は既存の line 12-13 だけで、新規 import はその後にある。`artifact_admission` は従来も `s1_report` の依存、`contract_loader_binding` はその依存なので、新規明示 import は初期化時点を前へ移すだけである。[s1_report.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/campaign/s1_report.py:33)

   `campaign_lock_test_support` の module top level は import と関数定義だけで、HEAD/blob 読取や `authorize` は helper 呼出し時まで起きない。[campaign_lock_test_support.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/campaign_lock_test_support.py:7) production module から test helper へ戻る import もなく、循環 import、追加の `sys.path` 依存、外部書込みはない。

5. **xdist 並列安全性: 破れなし**

   `_REAL_...` は worker process ごとの module global であり、worker 間では共有されない。同 worker 内では production 関数を fixture setup 前に一度保存し、その後再代入していない。[test_s1_report.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2124-s1-epoch-historical/orchestrator/tests/test_s1_report.py:31)

   autouse fixture と各 test の monkeypatch は function scope で teardown 時に復元される。1 worker 内の node 順序が変わっても保存済み production 参照は変わらず、worker 間で monkeypatch が漏れる状態もない。

6. **既存 node の期待値: 破れなし**

   patch で既存 test から削除されたのは、合成 E0 例外を投げる 1 行だけで、保存済み production callee 呼出しへ置換されている。[author.patch:43](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/author.patch:43)

   既存 assert の反転・緩和・削除、既存 node の削除、skip、xfail はない。assert の差分は新規正例に追加された 4 本だけである。[author.patch:98](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2124-s1-epoch-historical/author.patch:98)

## 未確認事項

なし。指定どおりテストは再実走せず、親が提示した 27 passed、2 passed、18 passed を前提事実として扱った。

## 総括

E0 の production 拒否経路は v1 入力集合全体に残っている。  
変更前から外れた拒否集合は、D1387 が許可した正しい v2/E1 の現行閉包取得不能だけである。  
負例と正例はいずれも実 production 経路を通り、恒真な保証にはなっていない。  
certified 選択、S-1 レポート、試行台帳を誤って広げる破れは静的検査では見つからなかった。