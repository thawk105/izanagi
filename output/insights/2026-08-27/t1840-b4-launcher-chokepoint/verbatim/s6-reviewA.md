### 既存テスト1件の期待値が実装と逆になっている

深刻度: must-fix

根拠: `orchestrator/tests/test_p3_s4_loop.py:3099-3102` は `B4LauncherAuthorizationError / "marker creation"` を期待するよう変更された。しかし `orchestrator/campaign/p3_s4_loop.py:1609-1616` が `default_cfg` より先に `B4ProtocolError("...fixture run_one_iteration route")` を送出する。親実測も `s5-focus-result.md:15-31` でこの1件だけの失敗を確認している。

既存テスト改変の全量は次のとおり。

- assertion・例外型・match・spy の意味を変更した既存テストは、上記1件と、G7に合わせて全面置換された `test_r7_a10_thin_cli_drives_factory_both_arms_pair_gate_and_failure_rc`、`test_closed_critic_cli_has_fixed_marked_configs_for_all_drivers`、`test_closed_critic_cli_constructs_only_fixed_marked_base_configs` の計4件。後3件は `orchestrator/tests/test_p3_b4_closed_critic.py:2327-2338,2766-2822` にあり、旧CLIのfactory・両arm・pair gate・RC・stderr spy/assertionを、hard-failまたはconfig factory直接検査へ置換している。
- projection期待集合は、独立算出helperとexact-set assertionの両方へlauncherを追加した。`orchestrator/tests/test_p3_b4_closed_critic.py:1683-1688`。
- 入力だけを変更した箇所は、同fileの `_certified_pair_fixture`、`_capture_certified_pair_construction`、factory直呼び7箇所、public receipt positive、ならびに base の marker/bound decision/一回消費/並行消費/write failure/bootstrap/no-build/receipt-first、sort の marker/certified/shared-gate/no-build、trigger の marker/certified/resolved-gate/no-build。いずれも `_b4_launch_context` または `expected_driver_kind` の追加であり、差分位置は `s5-diff.patch:1252-1466,1722-1936,2268-2670,2713-2854,2896-3079`。
- 既存test関数の削除、skip、xfail、条件緩和は無し。

成果物影響: 焦点テストreportが `554 passed, 1 failed` のままとなり、既存fixture拒否境界を誤った例外型で報告する。

修正案: `test_b4_fixture_main_rejects_run_one_iteration_bypass_m13` の期待値を `pytest.raises(L.B4ProtocolError, match="fixture run_one_iteration")` へ戻す。

### G1がtest-only contextを正式に受理している

深刻度: must-fix

根拠: 裁定は `s4-ruling.md:114-116,125` でG1にproduction contextを要求し、G6でtest-onlyを全formal境界から拒否すると定める。一方 `orchestrator/campaign/p3_b4_launcher.py:167-194` の `require_b4_any_context` は `_B4_TEST_CONTEXT_SEAL` を明示的に受理し、base/sort/triggerの `default_cfg` はそれを使用する (`p3_s4_loop.py:903-910`、`p3_s4_loop_sort.py:271-278`、`p3_s4_loop_trigger_gating.py:566-573`)。実際、既存goldenテストもtest-only contextでmarkerを鋳造している。

成果物影響: 専用launcherを通らない呼出しでもB-4 markerを持つCampaignConfigとcampaign.lockを生成でき、B-4識別子の受理集合がG1裁定より広がる。

修正案: G1でも `require_b4_production_context` を要求し、golden検査は実 admission verifier とlauncher経路から得たconfigを観測する。

### production contextがcaller自身で鋳造でき、campaign束縛も存在確認だけである

深刻度: must-fix

根拠: production sealはmodule global (`p3_b4_launcher.py:44`)、context型は直接構築可能 (`:55-66`)、production鋳造関数もmoduleから呼べる (`:248-265`)。入力の `VerifiedB4AdmissionRecord` 自体も通常のdataclass constructorを持つ (`p3_b4_admission_record.py:115-127`)。さらに `require_b4_production_context` のcampaign検査は `campaign_id is None` だけ (`p3_b4_launcher.py:225-228`) で、現在のcfg/layoutとの一致を受け取らない。`_bind_b4_campaign` は任意の文字列を束縛できる (`:268-291`)。G4も `expected_driver_kind=context.driver_kind` と自己値を期待値にしており (`:394-400`)、driver検査は自動的に真になる。

成果物影響: valid admissionを持つ直接callerがcontext・sidecar・activationをlauncher外で再現でき、driver/armの異なるcontextでも正式launcher由来と同形のWAL COMMITとsidecarを作れる。

修正案: production seal・鋳造・activationをlauncher関数だけが捕捉するclosureへ閉じ、formal境界にはvalidatorだけを公開する。validatorはexpected campaign id・driver・armを外部のcfgまたはdecoded lockから受け取り、全てexact比較する。

### WALのB-4分類がfail-openで、marker定数も複製されている

深刻度: must-fix

根拠: `orchestrator/campaign/wal.py:411-424` は全COMMITでlockを再読込・decodeするが、`OSError` と `CampaignLockCodecError` を `False` に変換する。したがって読取不能または不正lockは「markerなし」と分類され、`:434-436` のG4を通らない。`UnicodeDecodeError` は捕捉対象外なので、通常COMMITにも新しい例外経路が増えている。また key/valueを `"b4_protocol"` / `"p3-b4-reflux-ablation/v1"` と複製しており、正本は `p3_s4_loop.py:116-117` にある。

成果物影響: 分類時の一時的読取失敗やmarker定数の更新差分により、marker付きCOMMITがsidecar/live-context検証を省略してledgerへ追記され得る。

修正案: marker定数をimport循環のない低層moduleへ移し、driverとWALが同じ定数をimportする。lockは一度だけ読み、decode失敗を明示的にfail-closedとし、その同じbytesをreceipt hashにも使う。

### M08〜M16の一部は登録した副作用帰属を証明していない

深刻度: nit

根拠: 裁定 `s4-ruling.md:142-150` は例外messageだけでなく、検査を外したときに後段副作用へ到達する入力を要求する。しかしM08/M09は非権威tmp layoutのままで、G3を外しても既存layout gate (`p3_s4_loop.py:1241-1243`) が先に拒否する (`test_p3_s4_loop.py:2580-2612`、`test_p3_s4_loop_sort.py:969-996`)。M10もT側のlayout resolverだけをpatchし、共有L側をpatchしていない (`test_p3_s4_loop_trigger_gating.py:2828-2860`)。M11〜M13はvalid commit receiptを渡さないため、G4を外しても既存receipt gateでCOMMITされない (`test_p3_b4_launcher.py:88-129`)。M14〜M16もmissing admissionを入力にしており、G5/G6を外すとadmission読取で拒否され、artifact不在は変わらない (`:132-198`)。M15には後段のcfg-kind guardもある (`p3_b4_closed_critic.py:1212-1218`)。

成果物影響: 現在のcertified選択・report・ledger値は変わらないが、変異結果が例外型だけに帰属し、副作用不在の証拠にならない。

修正案: M08〜M10は両resolverを対象layoutへ揃える。M11〜M13はvalid live commit receiptを渡す。M14〜M16はvalid admissionを用意し、verifier・artifact writer spyの到達差で単独帰属させる。

### Golden identity

無し。contextは3 driverともmarker追加前のguardにだけ渡され、`CampaignConfig`や`search_config`へ保存されない。`ident.canonical_preimage` も `CampaignConfig.search_config` だけを直列化する (`ident.py:150-177`)。base 2件、sort 1件、trigger 8件のpinは変更されず、marker付きon/off 6件も `test_p3_b4_closed_critic.py:2740-2794` の既存IDを維持している。

### 既存6拒否

無し。`require_b4_iteration_authorization` 本体は変更されておらず、6分岐は `p3_s4_loop.py:1235-1261` に残る。markerなしreceiptはG3を通らず従来拒否へ到達する。残る5件はG3が手前に入ったためcontextなしの旧入力ではG3拒否になるが、production contextを与えれば同じ既存拒否へ到達する (`test_p3_s4_loop.py:2702-2782`)。

### G7〜G10および所有外ファイル

無し。旧CLI hard-fail、実main objectのregistry、bootstrapでverifierがconfig/driverより先、launcherのprojection共通entryはいずれもコード上で対応している。`.claude/agents/critic.md`、`docs/`、`hooks/` の差分は無し。

## 総括

must-fixは4件: 既存テスト誤改変、G1のtest-only受理、caller鋳造可能なcontext、WAL分類のfail-openである。  
golden identity 17件の算出経路と既存6拒否そのものには変更を認めない。  
ただしM08〜M16の一部は裁定が要求した副作用による単独帰属を満たしていない。  
G7〜G10とregistry実main identity、所有外fileの非変更は確認した。  
pytestは実走しておらず、実走結果として記したのは親提供の `554 passed, 1 failed` のみである。