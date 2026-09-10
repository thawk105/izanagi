## 所見 (real)

A1. 最重要: 計画中の負例は `_driver_configs` の変更に感応しない。`s2-plan.md:111-116` は未射影 config と射影済み config を手作業で作り、汎用の `require_b4_production_context` に不一致 ID を渡すだけである。変更点の `_driver_configs` (`orchestrator/campaign/p3_b4_launcher.py:147-174`) を通らないため、修正前後ともテストは成功する。さらに既存の `test_production_validator_requires_exact_campaign_and_arm` が同じ拒否力を既に検査している (`orchestrator/tests/test_p3_b4_launcher.py:808-831`)。したがって「base 射影を削除すると赤になる負例」にはなっていない。

A2. 3 node 全体でも、意図した三手射影のうち environment contract bind を欠く実装を検出できない。実機構は compute marker 追加に加えて `ident.bind_environment_contract` を行う (`orchestrator/campaign/p3_s4_loop.py:147-161`)。しかし計画の正例は `measurement_env` と campaign ID だけを検査し (`s2-plan.md:103-109`)、OTHER 例も ID と marker 不在だけを見る (`s2-plan.md:118-122`)。`bound_environment_contract` は campaign ID の正準 preimage に含まれない (`orchestrator/campaign/ident.py:196-218`)。よって base 分岐が marker だけを足し、契約を bind しない mutant でも3 nodeすべてが通り得る。返却された on/off config の `bound_environment_contract` が解決済み contract と一致することを compute と OTHER の双方で直接 pin すべきである。

A3. 正例は今回の launcher 分岐には感応するが、正式経路全体を覆うという主張には届かない。計画は registry の base driver を spy に置換し、spy 内で driver config を再構築する (`s2-plan.md:105-109`)。そのため実物の `main` の射影 (`orchestrator/campaign/p3_s4_loop.py:2589-2599`)、`drive_iteration` の再射影と境界 (`orchestrator/campaign/p3_s4_loop.py:2319-2356`)、resolved 境界 (`orchestrator/campaign/p3_s4_loop.py:1740-1752`) のいずれかが壊れても、この正例は緑になり得る。少なくとも「launcher 分岐の単体証明」と「正式 driver 経路の証明」を同一視してはならない。

A4. 計画の ID 照合 inventory は不完全である。三つの `require_b4_production_context` 以外にも、driver layout の再導出照合がある (`orchestrator/campaign/p3_s4_loop.py:2001-2003`)。また `Path(layout.root).name != expected["campaign_id"]` は WAL COMMIT 側ではなく、起動前の `write_sidecar` 検査である (`orchestrator/campaign/p3_b4_launcher.py:425-435`)。実際の COMMIT 用 G4 は `verify_launch_context` の context、layout、sidecar 三者照合である (`orchestrator/campaign/p3_b4_launcher.py:470-534`)。計画の正例は sidecar JSON を見るだけで、この実物 G4 を compute 射影済み ID で呼ばない。driver spy は active context 内で動くため、そこで実物 `verify_b4_launch_context` を呼べば同じ node 内で pin できる。

## 所見 (refuted)

A5. 修正後に正式経路へ ID 不一致が移るという懸念は refuted。launcher は射影済み selected config から context ID、layout、sidecar をすべて導く (`orchestrator/campaign/p3_b4_launcher.py:536-550,552-580,593-633`)。driver `main`、`drive_iteration` は同じ site/contract を再適用し、同一 contract の再 bind は元 config を返す (`orchestrator/campaign/ident.py:100-118`)。正式経路は `main` から `drive_iteration` へ進む (`orchestrator/campaign/p3_s4_loop.py:2693-2706`) ため、射影前に比較する公開 `run_one_iteration` の境界 (`orchestrator/campaign/p3_s4_loop.py:1894-1911`) には到達しない。layout 照合、resolved 境界、G4 も同じ射影済み ID になる。

A6. 授権防壁の受理集合が不当に広がる懸念は refuted。`require_b4_any_context` の exact seal、evidence class、driver kind 検査 (`orchestrator/campaign/p3_b4_launcher.py:287-314`) と、production seal、kind、arm、campaign ID 検査 (`orchestrator/campaign/p3_b4_launcher.py:316-364`) は変更されない。base の `_driver_configs` は新たに site admission と contract lookup を要求するため、その入口の受理集合は狭くなる。trigger は既存射影のまま、sort は未射影のままである。新しく通るのは、正当に発行された compute base context と driver の期待 ID が一致する意図した組だけである。

A7. `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` の新しい早期失敗が握りつぶされる懸念は refuted。両者は exact allowlist 外なので `_admit_env_contract` が `ExecutionGuardError` を送出する (`orchestrator/campaign/p3_s4_loop.py:133-144`)。`prepare_launch`、bootstrap、continuation、launcher CLI はその周囲に捕捉を持たない (`orchestrator/campaign/p3_b4_launcher.py:536-580,582-633,656-702`)。したがって未射影状態で静かに driver へ進まない。これは trigger の既存挙動とも整合し、安全側の前倒し拒否である。

A8. 計画した正例の修正前の赤理由と hostname seam は妥当。修正前の launcher は未射影 context と未射影 layoutを相互に一致させるため、`write_sidecar` では止まらず、spy 内の実物 production authorization で初めて campaign ID 不一致になる。conftest は setup 時に socket と `_has_nqsv` を中立化するが、test body の再差し替えが後から勝つ (`orchestrator/tests/conftest.py:239-255`)。また `_current_site` は `current_site` 関数の alias であり (`orchestrator/campaign/p3_s4_loop.py:123`)、その関数は呼出時に module の `socket` を読む (`orchestrator/campaign/site_policy.py:66-77`)。`bnode116` は `_has_nqsv` に依存せず compute になる (`orchestrator/campaign/site_policy.py:40-41`)。

A9. test-only context を使った campaign ID 値が標準 production launcher configへ一般化できないという懸念は refuted。context は `default_cfg` で seal/kind 検査にだけ使われ、その後 config へ保存されず、同じ B4 marker が追加される (`orchestrator/campaign/p3_s4_loop.py:1405-1428`)。campaign ID は config の5要素だけを覆う (`orchestrator/campaign/ident.py:196-235`)。したがって同一 worktree・同一 admission policy の正式 launcherでも親の ID 値になる。ただし `PEGASUS_SUSPECT` 自体は親 probe で実測されていない。実測扱いにするなら socket に非標準 `pegasus...` 名を与えるだけでなく `_has_nqsv=True` も固定する必要がある (`orchestrator/campaign/site_policy.py:42-45`)。`os.environ` は classifier が捨てる (`orchestrator/campaign/site_policy.py:30-36`)。

## scope 外だが real (裁定へ返す候補)

なし。公開 `run_one_iteration` の射影前境界は正式 launcher 経路外で、かつ不一致時は拒否側へ倒れるため、今回の安全性所見には数えない。

## 総括

コード修正案そのものは、正式 base 経路の ID、layout、sidecar、resolved iteration、COMMIT G4 を同じ射影済み campaign ID に揃え、防壁も弱めない。主要な欠陥はテスト設計にある。特に負例は変更機構を一切通らず既存 validator test と重複し、全3 nodeでも environment contract bind 欠落を検出できない。正例も launcher 分岐は検査するが、実物 driver 経路と G4 まで覆うという証拠にはならない。

静的検査のみ実施し、pytest は実走していない。編集、commit も行っていない。