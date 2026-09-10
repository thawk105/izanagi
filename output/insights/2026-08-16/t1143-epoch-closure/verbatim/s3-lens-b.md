```text
### 所見 1: exact 12 のままでは実際の verifier dispatch が閉じない
- 深刻度: blocker
- 根拠: out/s2-plan.md:3,41-52、orchestrator/campaign/pipeline.py:30,1055-1083、orchestrator/verifier/__init__.py:16-20、orchestrator/verifier/report.py:42-76
- 成果物影響: pipeline は4実装を直接呼ばず package shim から verify_trace_dir を解決する。__init__.py の差し替えだけで vr.certified の供給元を変更でき、anomaly を含む variant が certified 選択へ入る。report.py が未束縛なら rejection payload と verifier report だけを変更できる。
- 提案: 段4で exact 12 か exact 13 かを裁定する。最低限 __init__.py を加えて exact 13 とする。report.py まで correctness report の同一性に含めるなら exact 14。exact 12 を維持するなら shim 経路は scope 外で未束縛と明記する。

### 所見 2: s8b の epoch consumer が依存 census から抜け、scope 変更が certified 選択へ届かない
- 深刻度: blocker
- 根拠: out/s2-plan.md:31-39、orchestrator/campaign/layer3_schema.json:57-66、orchestrator/campaign/s8b_oracle_artifacts.py:167-200、orchestrator/campaign/s8b_oracle_judge.py:221-239
- 成果物影響: schema と oracle artifact validator は scope を空でない文字列としか検査せず、judge は state=E1 と certified_eligible=true だけで epoch_eligible_campaign_ids に加える。旧 exact 8 scope や任意の scope を持つ E1 artifact が新 closure の certified 選択集合へ混入し、report の epoch 参照も適用規則を一意に指せない。
- 提案: s8b_oracle_artifacts.py と s8b_oracle_judge.py を consumer census に追加し、現行 scope の完全一致と旧 scope の拒否を固定する。cross-version を扱うなら closure version を wire に追加する。

### 所見 3: D268 の recorded HEAD fixture 回避は、実 repo を使う certified consumer まで届かない
- 深刻度: blocker
- 根拠: orchestrator/tests/campaign_lock_test_support.py:10-20,23-46、orchestrator/campaign/artifact_admission.py:781-793、out/s2-plan.md:91-113、orchestrator/tests/test_t671_source_binding.py:320-346、orchestrator/tests/test_p3_s4_loop.py:124-131、orchestrator/tests/test_critic.py:243-246
- 成果物影響: shared helper は記録 HEAD blob で lock を作るが、後段の certified gate は live closure と比較する。artifact_admission.py は既存8 pathの一つで、今回 scope/docstring を編集するため、commit 前は recorded-current-closure-mismatch となる。正例 fixture の test node が source drift として赤になり、related acceptance で report が生成されず、実装の certified 選択を検証できない。
- 提案: test_t671 のように全 certified fixture consumer を clean な一時 repoへ向け、記録 blob と live bytes を一致させる。実 repo での dirty 拒否を検査する node は別に分離し、期待された赤と fixture 側の赤を混ぜない。既存 campaign の32本の v1 corpus は test_artifact_admission.py:747-789 で不変だが、この問題は動的 fixture の受入走に残る。

### 所見 4: path-removal 変異の赤理由が一意に決まらない
- 深刻度: blocker
- 根拠: orchestrator/tests/test_t671_source_binding.py:119-144,179-193,207-219、orchestrator/tests/test_campaign_lock_codec.py:166-179、out/s2-plan.md:83-103,107-111
- 成果物影響: production tuple から1 pathを外すと、全体一致 test が落ち、各 parametrize node の同じ tuple assertion も一斉に落ちる。一方 codec の missing parameter は production tuple から導くため、外した path の node 自体が消える。したがって、どの path の除去が certified 受理集合を縮めたのか、また失敗が codec・fixture・中央 gate のどこかを特定できない。
- 提案: 独立した期待 tuple を parameter にし、各 node で対象 path の membership を個別に検査する。parameterized node 内の全体 tuple assertion は分離し、除去変異では対象 nodeだけが exact reason を返す focused matrix にする。

### 所見 5: T126 qualification の identity closure は verifier 4 file を追随しない
- 深刻度: major
- 根拠: prompts/s1-brief.md:35-38、orchestrator/qualification/contract.py:38-75、orchestrator/qualification/identity.py:130-144、orchestrator/qualification/t126_driver.py:355-368、out/s2-plan.md:31-39
- 成果物影響: qualification の code_identity は verifier/core.py だけを含むため、dsg.py、model.py、parse.py が変わっても series-identity.json と qualification receipt の code_identity 集合・参照値は変わらず受理される。campaign epoch 自体とは別だが、qualification 成果物が旧 correctness 実装を指し続ける。
- 提案: T126 qualification まで threat scope に含めるなら4 pathを追加し、exact set、golden、receiptを更新する。含めないなら本 wave の scope 外と明記し、T126 identityを certified verifier の証拠として使わない検査を追加する。

### 所見 6: domain /v1 据え置きで旧8と新12の E1 namespace が区別できない
- 深刻度: major
- 根拠: out/s2-plan.md:54-69、orchestrator/campaign/artifact_admission.py:63,738-747、orchestrator/campaign/s8b_oracle_artifacts.py:174-200、orchestrator/campaign/s8b_oracle_judge.py:235-239
- 成果物影響: 旧 generator と新 generator はともに E1:<sha256> を発行する。現 corpus は v2 lock 0件でも、rollback、旧 binary、複製済み observation が混ざれば、旧8 path の E1 が新 closure の certified 選択集合へ入り、report と台帳の epoch 値だけでは preimage 定義を判別できない。
- 提案: cross-version を脅威に含めるなら domain と wire-visible version を E2 等へ上げ、schemaと全 goldenを更新する。/v1を維持するなら旧 scopeを oracle validator で明示拒否する裁定が必要である。

### 所見 7: 親の「0件」は direct campaign_lock pin に限定しないと過剰な主張になる
- 深刻度: minor
- 根拠: orchestrator/campaign/silo_ladder_rung1.py:262-286、output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:79-121、orchestrator/tests/test_silo_ladder_rung1_evidence.py:1251-1274、docs/failures.md:748-755
- 成果物影響: campaign_lock.py の live ledger pin 0 は維持されるが、凍結 runtime_modules は verifier 8 file 全部を hash pin し、verifier_module という role key でも report.py を pin している。今回 verifier bytes は不変なので値は変わらないが、将来の verifier 編集では frozen report と受入 test が stale になる。
- 提案: 0件の主張を campaign_lock.py の direct live pin 0 に限定し、runtime_modules、role key、出力形状、生成時 hash を逆向きにも列挙する。silo 成果物自体は変更しない。

### 所見 8: D268 と failures.md の exact 8 記述が現行の意味を誤る
- 深刻度: major
- 根拠: docs/decisions.md:12355-12367,12371-12374,12392-12396、docs/failures.md:777-787、out/s2-plan.md:36-39
- 成果物影響: decision と failure ledger が closure を8 pathとして参照し続けるため、実装後の epoch scope、certified report、source pin audit の読み手が実際の12 pathを誤認する。D268 の historical transition と T1143 の現行契約の参照が混線する。
- 提案: D268本文を無言で改変せず、T1143のsupersede fragmentを追加し「既存8 + verifier/core,dsg,model,parse = exact 12」と記録する。名乗りの exact 8、受理集合の exact-8、dirty拒否の8 pathをそれぞれ exact 12へ更新する。P1でexact13を採る場合は全て13とし、__init__.pyを列挙する。
```

## 総括

NO-GO。exact 12/13 の dispatch 境界、s8b consumer、fixture isolation、変異帰属が未確定である。  
既存32本の v1 成果物は静的には不変だが、動的 certified fixture は commit 前に偽の赤を作る。  
/ v1 の旧新混在と qualification 別閉包も、受理集合と参照値の意味を弱める。  
docs は T1143 の supersede 記録が必要であり、現状のまま land すべきでない。