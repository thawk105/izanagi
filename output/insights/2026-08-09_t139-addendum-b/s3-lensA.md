## 所見

### 1. `b01 = 1` は許容されるが、正本から導出された値ではない [must-fix]

[判定] `K=1` と `a13` の無限 spending は矛盾しない。`a13` 自身が有限 cap と未使用 tail の廃棄を認めている。ただし exact bytes の候補が 1 本であることは、候補系列全体の cap を 1 にする数学的根拠ではなく、governance 選択にすぎない。

[根拠: addendum-a-reissue.md:894-914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:894) 「`domain: k = 1, 2, 3, …`」「候補数の上限を必要としない」「`b01` が有限 cap を置いても未使用の tail は捨て」。  
[根拠: package.md:153-159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/package.md:153) Q7 は「累積 alpha 台帳 + spending 関数 + 候補数上限」で、将来候補を跨ぐ仕組みとして書かれている。  
[根拠: s2-plan.md:34-36](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:34) plan は exact `modeX` 1 本から `K=1` を正当化している。

[成果物影響] `K=1` なら許容 ordinal は `{1}` だけとなり、第 2 候補は certified 選択・材料レポート・公表台帳の全てから除外される。累積機構が制御するのは、実質的には第 1 候補の失敗後の再利用・付替えだけになる。

[最小の直し方] `K=1` を「正本からの導出」ではなく「本 family を一候補で恒久閉鎖する governance 裁定」と明記する。新 core が単に次候補を扱うだけなら、同じ alpha family の根を維持する規則も併記する。

### 2. `b02 = 0.05` の FWER は cap と根の恒久性に条件付きである [blocker]

[判定] 有効な 6 個の周辺 p 値に Holm を適用し、同一 publication root の候補が恒久に 1 件なら、系列 FWER は `0.05` 以下になる。cap を後で上げる場合は `A_pub` の定義域外なので fail-closed にできるが、同じ科学的 family を「新 study・新 root」として再開すると全額 `0.05` を再取得でき、累積制御が破れる。

[根拠: s2-plan.md:55-68](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:55) 「`A_pub(1) = 0.05`」「`domain = {0, 1}`」「第 2 候補は許容されない」。  
[根拠: s2-plan.md:92-95](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:92) 「新しい正規の根を作れるのは、新 study を承認する canonical なユーザー裁定だけ」。  
[根拠: preregistration.md:246-253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:246) 「別々の累積台帳」「新しい親系列 ID の自己申告でリセットできない」。

[成果物影響] 同じ family を二根へ分け各根で `0.05` を使うと、独立な 2 候補なら少なくとも一つの偽公表をする確率は `1-0.95²=0.0975` になる。primary の certified 受理集合は本来不変だが、材料レポートの有意セル集合と公表試行台帳の累積量が誤る。B 未解決なら main admission が閉じるため、間接的には certified 選択も生成不能になる。

[最小の直し方] 「新 core」と「新 alpha family」を分離する。同じ問いの次候補は core が変わっても同じ publication root に属し、全額消費済みなら正の第 2 割当てはない、と固定する。異なる spending 形を primary と publication に置くこと自体は、別台帳なので問題ではない。

### 3. 6 セルは `{W1,W2} × {N,H,G}` に一意に閉じる [must-fix]

[判定] plan の「決まらない」は過剰に厳格で、(P1) が正しい。`D` は定義されているだけで、6 成分 family の一員とする逐語はない。一方 `N/H/G` は primary の三条件、planning vector、simulation の「6 成分」の全てで一致する。

[根拠: preregistration.md:97-107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:97) workload ごとの受理条件は `N > 0 ∧ H > 0 ∧ G > 0`。  
[根拠: addendum-a-reissue.md:630-634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:630) `Y_j = (N_W1,H_W1,G_W1,N_W2,H_W2,G_W2)`。  
[根拠: addendum-a-reissue.md:858-864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:858) 「成分 = 6 (W1/W2 × N/H/G)」。  
[根拠: addendum-a-reissue.md:757-764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:757) `N`・`H`・`G` は独立な線形汎関数で、`D=N+G`。

[成果物影響] `{D,N,G}` を採ると `H` の primary 条件が公表 family から脱落し、Holm の順位・調整済み p 値・同時区間の列が変わる。材料レポートと family identifier が別物になる。

[最小の直し方] B に新しい field として書かず、package で「core §4、`a10`、`a12` が一意に定める既存 family」として `{W1,W2}×{N,H,G}` を参照する。

### 4. 「公表用検定統計量が未固定」は半分 refuted、半分 real [blocker]

[判定] 周辺統計量と帰無方向は既に固定されているので、plan の全面的な「未固定」は誤りである。ただし `α_pub=0.05` をそのまま各 workload の `q(J,α)` に入れる読みは、二 workload 合算で `0.05` を保証せず、B が `q` を動かすため成立しない。

[根拠: addendum-a-reissue.md:686-699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:686) `T_k=√J·μ̂_k/s_k`、成分は明示された 6 個で、primary は `∩{T_k>q}` と一致する。  
[根拠: preregistration.md:219-221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219) 「帰無仮説は weak mean null を primary」。  
[根拠: addendum-a-reissue.md:783-797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:783) `q` は `J` と primary の `α_k` の関数。  
[根拠: preregistration.md:357-360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:357) 「追補 B は `q` に影響する量を一切持たない」。  
[根拠: preregistration.md:438-441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:438) §16 は「6 セルすべての調整済み p 値と同時区間」を要求する。

[成果物影響] 未調整 p 値・Holm の受理集合・同時区間が一意でなければ材料レポートを certified と呼べない。公表 alpha を primary `q` に流すと、primary の certified 受理集合まで変える禁止経路になる。

[最小の直し方] cap 1 に限り、既存の一側 `t_{J-1}` 周辺 p 値を 6 個へ Holm 適用し、同時区間は既存の `a11` 領域を既に固定された `α₁=0.025` で両 workload に使う、と解釈裁定する。各 workload の失敗確率が `0.025` 以下なので、二 workload の union bound は `0.05` 以下となり、B から `q` を変更しない。これを既存文の必然的導出と認められない場合にのみ新 core が必要である。

### 5. 「新 core だけが clean」は過剰 escalation [must-fix]

[判定] 「現在の説明のまま即発効できない」は妥当だが、「唯一の解が別 study」は強すぎる。family、統計量、帰無方向、Holm、既存同時領域を一意に接続する解釈裁定という、より小さい経路が残る。

[根拠: s2-plan.md:162-169](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:162) plan は既存 `T_k` の流用を「不十分」、新 core を「唯一の clean な解」とする。  
[根拠: addendum-a-reissue.md:812-815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:812) primary の権威と §16 公表用区間の関係が既に明記されている。  
[根拠: preregistration.md:313-316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:313) 新 core が必要なのは、閉集合外の変更が本当に必要な場合である。

[成果物影響] 不要な別 study は core/A/B、root、予約 ordinal、全 report reference を作り直し、現 study の certified 受理集合を空のまま停止させる。逆に曖昧な解釈だけで進めれば report の p 値・区間が非一意になる。

[最小の直し方] package を「既存規則からの一意な解釈を承認する案」を推奨、「その解釈を新規推論規則と判定する場合だけ新 core」を予備案とする二段階裁定へ直す。

### 6. (P3) の `δ_MC` 根拠棄却は正しい [must-fix]

[判定] plan の反論が正しい。`δ_MC=0.001` は 60 個の Monte Carlo 上側信頼限界が同時に正しい確率の誤り予算であり、検定可能な p 値の解像度でも名目水準の下限でもない。

[根拠: s1-brief.md:59-61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:59) (P3) は `α_pub_k/6 ≥ δ_MC` から cap を導く。  
[根拠: addendum-a-reissue.md:878-887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:878) `δ_MC/60` は Beta 上側限界の被覆へ使われる。  
[根拠: addendum-a-reissue.md:964-965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:964) 「familywise `1−δ_MC` の上側信頼主張」。

[成果物影響] (P3) を採ると調和 spending の仮定下で cap が 2 となり、ordinal `2`、その alpha、追加材料レポート行が受理集合へ入る。誤った単位比較で台帳の許容集合が変わる。

[最小の直し方] (P3) を撤回し、cap を governance 裁定としてのみ提示する。Monte Carlo 精度を根拠にするなら `B` と上側限界幅を用いた別の事前導出が必要だが、それでも公表 FWER の cap とは別問題である。

### 7. 3 field は値として pilot 非依存だが、選択時点が閉じていない [must-fix]

[判定] plan の表どおり、3 field の式に pilot raw を直接読む経路はない。しかし governance 値をいつ選んだかという選択経路は証明されていない。core は B を「本走前」としか要求せず、pilot 後の選択余地が文面上残る。

[根拠: s2-plan.md:121-125](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:121) 非依存の根拠は各 field の入力だけを列挙している。  
[根拠: preregistration.md:246-253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:246) B は本走前に必要で、その理由を「pilot の raw を見た後に…選べる経路を残さない」とする。  
[根拠: addendum-a-reissue.md:923-929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:923) primary ordinal は pilot 前の reservation を要求する一方、公表側 reservation の同じ期限は plan にない。

[成果物影響] pilot feasibility や共分散を見た後で cap・公表 alpha・root を選んだ疑いが残ると、main admission の proof chain が閉じず、certified 選択・材料レポートを事前登録結果として扱えない。試行台帳には裁定・予約の時刻関係が必要になる。

[最小の直し方] B の承認・commit と publication reservation を pilot 1 本目より前に行う。少なくとも「pilot raw 未閲覧」の canonical 記録と、primary reservation が publication allocation も不可逆に消費する規則を置く。

### 8. `b03` は恒久的な恒真条件ではないが、現状では評価器がない [nit]

[判定] 実装がない現在、拒否条件は真偽を評価されない。仮に今の空台帳へ evaluator だけを置けば「entry が無い」が常に成立して全拒否になるが、create-only entry を作る正経路があるので恒久的な constant deny ではない。

[根拠: s2-plan.md:99-109](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:99) primary entry 解決後に publication entry を予約する正経路と、欠落時の拒否が両方書かれている。  
[根拠: s1-brief.md:50-51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:50) 「resolver・producer・validator・consumer・台帳の実体化」は将来 wave の責務。  
[根拠: addendum-a-reissue.md:932-937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:932) 外部台帳が実在して初めて防壁になる。

[成果物影響] 現時点の admission 受理集合は実質空で、certified 選択・材料レポートは生成不能、公表台帳 entry も存在しない。ただし plan も未実装を認めており、新たな統計的破綻ではない。

[最小の直し方] B に「規範であって active gate ではない」と明記し、将来実装用に正例を 1 本だけ置く。canonical ledger の所有者・予約操作・digest bytes は実装 wave で固定する。

### 9. 親の実測 triple から publication root の正当性は導けない [must-fix]

[判定] 指定資料内では同じ triple が追補 A に反復されているが、私は digest・祖先関係を再計算していない。仮に値が正しくても、それが証明するのは core blob の同一性と当該 HEAD での祖先性までであり、publication family の規範的な根や将来 study の root 分割までは証明しない。

[根拠: s1-brief.md:33-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:33) 親の実測は path・commit・SHA-256 と「`F` は HEAD の祖先」。  
[根拠: addendum-a-reissue.md:40-49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:40) 同じ triple と、`F` が D234 の fold commit である旨を記す。  
[根拠: preregistration.md:408-411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:408) 実際の祖先性は future `measurement_head` を checkout から導出して検査する契約。  
[根拠: s2-plan.md:85-95](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:85) `(F, individual_publication)` という domain separation は plan が追加した governance 案である。

[成果物影響] 根の一般化を誤ると、試行台帳が同じ family を分割して alpha をリセットするか、別 family を誤って併合する。将来 checkout で祖先検査を省けば certified result の core reference 自体が不適格になる。

[最小の直し方] 「静的に報告された triple」「runtime で再検証する binding」「family root の governance 裁定」を別項目に分ける。新 core が同じ科学的 family の継続なら root を維持する条件を明記する。

### 10. 追補 A 自身が core §7 の weak-null 較正義務を満たしていない [blocker]

[判定] これは B より先に存在する独立 blocker である。「A の 13 field が発効済み」と「A が core の意味上の義務を満たした」は同値ではない。A は `a12` が core §7 を満たさないと明言している。

[根拠: preregistration.md:219-221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219) 「weak null の型 I 誤りは…事前 simulation で較正する」。  
[根拠: addendum-a-reissue.md:825-838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:825) 「本 field はその較正を与えない」「core §7 の義務を満たしたと扱ってはならない」「本 wave はこの差を解消していない」。  
[根拠: decisions.md:10999-11015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/decisions.md:10999) 完結するのは core と追補の組で、変更が必要なら別 study とする。

[成果物影響] exact-key resolver は `a12` の見出しが存在するだけで通る可能性があるが、weak-null 型 I 誤りは未較正のままである。したがって main の certified 受理集合、調整済み p 値、同時区間はいずれも統計的 proof chain を持たず、材料レポートを certified とできない。

[最小の直し方] B の発効判断より先に R2 を裁定する。pilot 前なら、独立 cluster データまたは妥当な較正法に基づく承認済み A 再発行が可能かを裁定し、不可能または既に study data を見た後なら新 core・新 study へ戻す。

## 総括

blocker 件数: **3 件**。  
最も重い 1 件: **追補 A が自ら認める core §7 weak-null 較正義務の未充足**。  
親が採るべき道: **まず R2 を閉じ、その後 `{W1,W2}×{N,H,G}`・既存 `T_k`・Holm・既存 `a11` 区間による小さい閉包を裁定し、成立しない場合だけ新 core へ戻す**。  
実走・build・test は一切行わず、指定資料の静的読解だけを行った。