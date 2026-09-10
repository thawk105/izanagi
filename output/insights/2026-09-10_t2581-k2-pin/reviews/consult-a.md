40桁限定案を採用してよいと判断します。変更対象は5ファイル。指定資料と当該ファイルを静的に確認し、pytest・実測・編集は行っていません。

1. **real：planの7桁互換は今回の契約より広い。**
   箇所：`plan.md:31`、`tools/pegasus/p3_s4_loop_pegasus.sh:234-250`。
   反例：PINを`511c953`へ戻しても7桁互換案なら通過し、同じcommitに別のpin文字列表現を許す。pinはcampaign identityへ入るため、完全40桁指定との不整合が成果物識別へ波及する。
   最小修正：既存述語を`^[0-9a-f]{40}$`へ変更し、拒否文言もfullへ合わせる。後段の解決・HEAD比較・clean検査は維持する。40桁同士のprefix比較は実質完全一致なので、その書換えは不要。

2. **real：fixture追随は実HEAD束縛の証明にならない。**
   箇所：`orchestrator/tests/test_p3_s4_loop_job_contract.py:1180-1234,1312`、`plan.md:34`。
   反例：helperはCCBenchへの全rev-parseに同じ架空HEADを返し、PIN importも固定文字列を返す。productionのPINが旧値のままでも、helperの2値だけ新SHAへ替えればK2 argv正例は通り得る。
   影響：この緑を「指定PINが実HEADへ束縛された証拠」と扱うとF27/F649に該当する。既存テストのargv配線確認としての効用はある。
   最小修正：fixture更新は維持し、報告を「40桁文字列でshell分岐を通り、stub driverへargvを渡した」に限定する。実束縛は親の専用checkoutによる既存実走証拠で補う。

3. **real：上流拒否や静的文字列検査によるmaskに注意。**
   箇所：`orchestrator/tests/test_p3_s4_loop_job_contract.py:281-290,610-623`、`tools/pegasus/p3_s4_loop_pegasus.sh:234-251`。
   反例：7桁を拒否しただけでは、HEAD不一致拒否の有効性は分からない。また比較文字列が存在しても、その分岐が実行された証拠にはならない。40桁限定時にはprefix比較自体も完全一致として働くため、解決後比較を外した変異が別比較で拒否され得る。
   影響：F28/F33の観点で、赤を個別比較の発火証拠へ誤帰属する恐れがある。
   最小修正：親の予定済み変異確認では、形式を通る40桁入力を用い、どの拒否理由へ到達したかを記録する。冗長比較の片方だけを外した結果から、単独の実効性を主張しない。新gateは不要。

4. **refuted：live golden更新が過去campaignの再ラベルになる。**
   箇所：`orchestrator/campaign/p3_s4_loop.py:1513,1554`、`orchestrator/tests/test_p3_s4_loop.py:590,603,5078,6447`、`orchestrator/tests/test_p3_b4_closed_critic.py:3081`。
   想定反例：新PINなのに旧campaignへ追記する。確認範囲では、PINが設定へ入り、束縛後のcampaign IDからlayoutを選ぶため、この反例を支持しない。列挙goldenは現在の設定factoryを検査する期待値で、過去出力そのものではない。
   影響・最小修正：通常on/offとB4 baseだけの更新は妥当。旧出力・manifest参照・他driverは保存する。plan記載の新hash値自体は今回は独立再計算していない。

5. **real：P1は到達可能性の仮説として残る。規律6違反は確認せず。**
   箇所：`brief.md:11`、`orchestrator/campaign/p3_s4_loop.py:1857,1946,1966,2770`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:1227-1229`。
   反例：PIN preflightとargv伝達が成功しても、実traceが再びparse errorになればverifier v2 terminal verdictは得られない。helperの`-m`処理はargv保存だけでdriverを実行しない。
   影響：PIN変更とテスト緑だけでK2の残条件成立を報告できない。対象driverは既存pipelineへ処理を委譲しており、今回の5ファイル検査からv2到達を独立保証することもできない。
   最小修正：親の1本実走で既存WAL・verdictを確認するまでP1を未確定とする。既存の値とimplementationの帰属検査、K2入力経路を維持し、前回材料は無変更で渡す。材料再利用と新規合成の主張を混同しない。

## 総括

40桁限定への整合と直接依存golden更新を支持します。主な問題は実装案そのものより証拠の射程です。fixtureの緑、個別gateの実効性、verifier v2到達を分けて報告し、最後は親の予定済み実走で確定してください。
