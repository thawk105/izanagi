## 所見

1. **must-fix｜brief 7・13、plan 10｜三経路の差替えだけでは「伏せ」「入替」が成立しない。** 親 prompt の workload、`ledger root`、`materials root`、Agent の description に真の workload が残る。critic 入力には slot・digest path・系列台帳の path が入り、digest の rejection にも workload タグが出得る。根拠: `parents/header.md:7-9`、`parents/template-effective.md:39-55,68-70`、`tools/t2849_llm_round.py:205-219`、`orchestrator/critic/digest.py:1379-1383,1451-1455`。**直し方:** 三経路を操作対象として定義しつつ、親の起動値・path・description を含む実際の表示を発効前に列挙する。真の workload を隠せない面は残存曝露として記録し、「盲検」や workload 情報の遮断とは主張しない。新たな遮断 gate は要らない。

2. **must-fix｜brief 9・14、plan 11・45・54｜critic 診断を機械 digest に置けば「critic の有無だけ」が変わる、とは言えない。** 現行の次回入力にも `rejected_opportunities.reject_class` という構造化された投入前失敗分類が既にある。一方、`make_critic_digest` は緑の指標と赤の理由を*テキスト*へ描画する関数で、単一の verifier 構造化 object を返さない。critic 有りではその解釈文、無しでは生の理由を渡せば、情報の粒度と形式も変わる。根拠: `t2849_comparison_harness.py:417-425`、`t2849_llm_round.py:116-120`、`p3_s4_loop.py:1186-1216`、`digest.py:1342-1364`。**直し方:** 両水準で共通の機械的失敗データを同一 bytes で渡し、critic 有りにだけ追加の解釈文を渡す構成を第一案にする。critic 代替 digest 案を採るなら、推定対象を「二つの還流構成の差」と明記する。

3. **must-fix｜plan 11・20｜critic 無しの受理経路が実装一覧に足りない。** 現行 `cmd_inputs` と `cmd_proposal` は評価2以降に critic 逐語ファイルを読み、harness も `k2_critic_diagnosis` を必須とする。役割文書は同 key を critic 由来と定義している。根拠: `t2849_llm_round.py:118-120,192-198`、`t2849_comparison_harness.py:430-449`、`planner-v4.md:75-84`、`coder-v4-autonomous.md:52-67`。**直し方:** 後続実装の必要箇所に、親の critic 起動条件、入力生成、公開時照合、harness の継承照合、役割入力契約を明記する。別 key に由来と欠測を保持し、同じ証拠から同じ値を再計算して照合する。既存 key に機械文を偽装して入れない。verifier の判定・即 reject・既存の失敗分類は緩めない。

4. **should｜brief 13・18、plan 10｜錨 rh への入替自体は留保条件違反ではないが、到達可能性の扱いが不足する。** rh は明示された学習錨であり、留保 rr25・rr75 ではない。ただし規律は親・critic を含む全生成主体による留保設計や結果の使用を禁じ、docs を読める主体の到達可能性を記録する。根拠: `unseen-condition-transfer-preregistration.md:95-99,154-173`、`critic.md:3-4`、`parents/template-effective.md:59-64`。**直し方:** 入替先を rh と固定し、留保条件を参照して選んだものではないと記す。親・critic の docs 到達可能性と不使用の手順を登録し、構造的隔離とは呼ばない。

5. **must-fix｜brief 10・17、plan 17｜三分類の分母と優先順がまだ操作的でない。** 受理された S1 の実装は数値 literal の宣言に制限され、機構変更は受理集合で構造上0。一方、planner 拒否には coder 出力が存在せず、文法拒否には「機構変更の試み」と単なる書式誤りが混在する。`無効変更`を文法拒否全体に当てると、その試みと衝突する。根拠: `coder-v4-autonomous.md:71-81`、`t2849_llm_round.py:142-158,170-181`、`t2849_comparison_harness.py:545-553,573-587`。**直し方:** 「coder 原文がある機会」を評定分母にし、提出なしを別集計にする。受理候補は既知値の再発見／新しい有効値／値不変に分け、拒否原文の機構変更の試みは別母集団で評定する。既知集合は発効前に数値の exact な列挙で凍結し、identity と同一視しない。二名の盲検は cell・score を伏せる範囲までとし、原文や拒否理由からの推測可能性を開示する。

6. **should｜brief 15、plan 12・19｜D2273 の修正と新 cohort の境界をさらに明確にすべき。** 修正 prompt はこの worktree にあるが、D2273 は T-2850 本比較への適用を明示的に退けている。新実験で使うなら別構成として固定できるものの、試走 v2 の拒否率や単価がその構成を実測したかのようには扱えない。根拠: `rulings-D2273.md:5-15,20-24`、`t2849_llm_round.py:95-97`、`rulings-D2265.md:6-14`。**直し方:** 新 cohort・固定 commit・seed preimage と親 prompt の exact bytes を発効束に記し、試走単価の構成差を見積りの不確実性として示す。T-2850 の登録や標本は変更しない。

7. **should｜brief 3・19、plan 8・19・59-65｜S1-wh だけの研究価値を強く言い過ぎる余地がある。** S1 は値一個で機構変更を受理できず、D2272 は同空間の高費用な本比較を研究上弱いとして止めた。六 cell にしても課題間の成功・失敗対比は得られない。根拠: `rulings-D2272.md:40-53,64-73`、`coder-v4-autonomous.md:71-81`、`request.md:3-10`。**直し方:** S1 案を「表示と診断構成が数値探索に与える限定的な結果」と位置づけ、発効時には S1 で進める案と S3 の関数方策軸で機構を読む案を費用・成熟度・得られる主張とともに択一提示する。今回 S3 の実装や一般化は起こさない。

8. **nit｜plan 17・20｜必要な記録と scope 外の台帳追加が混同されやすい。** 逐語 coder 出力と採否は現行の materials と ledger に既に保存される経路がある。新しい分類用台帳や汎用集計器まで本タスクの発効要件に見せる必要はない。根拠: `parents/template-effective.md:39-45`、`t2849_comparison_harness.py:545-553,573-611`、`request.md:10-12`。**直し方:** 草稿には抽出・伏せ方・評定・集計規則を書く。後続実装欄は既存記録の再利用と介入に不可欠な差分に絞る。

## 総括

最大の問題は、表示三経路の操作を workload の遮断と誤認し得ること、そして critic 無しの cell が現行の入力・照合契約では動かないことです。機械的失敗データを両水準で共通化すれば、規律3を保ちながら critic 解釈の追加効果に近づけます。S1 の人手分類は受理候補と拒否原文を分けて登録すべきです。今回は草稿と見積りに留め、S1 で得られる限定的な知見と S3 で機構を調べる択一を、発効判断時に明示するのが妥当です。