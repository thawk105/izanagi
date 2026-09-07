## 凍結の順序

結論は「提示された commit 順を事実として受け入れるなら守られた。ただし、射影された証拠だけでは独立検証できない」である。

- 現在の事前登録ファイルの SHA-256 は `526d9384...ca495a` であり、解析器が要求する v2 hash と一致する。[解析器:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:23) 解析要約も同じ hash を記録している。[解析要約:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/analysis-summary.json:3) したがって、要約された結果が現在の v2 bytes を参照している点は確認できる。
- しかし `wave.diff` は commit header のない合成差分である。事前登録差分が先に、解析器差分が後に並んでいるのはファイル順にすぎず、commit 順や祖先関係を証明しない。[wave.diff:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:1) [wave.diff:160](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:160)
- 許可資料には結果 commit の ID、3 commit の親子関係、結果 commit に含まれる入力 hash 照合がない。解析要約にも commit identity と `inputs[].sha256` はない。このため、`1c977...` が `1c482...` と結果 commit の祖先か、段 4 が採用した「12 成果物の bytes が前 wave と同一」という追加証拠が実施されたかは、この射影からは確認不能である。[段4裁定:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:82)
- §0 の限界記述は、論理的な限界の説明としては十分である。commit DAG が証明できる範囲と、別経路での先行計算を証明できないことを明記している。[事前登録:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:43) ただし「誰も計算していない」は依然として証言であり、その直前の強い断言を暗号学的事実へ格上げしてはならない。

したがって、親 insight は「順序が証明済み」ではなく、「提示された commit DAG が確認できれば、v2 bytes が解析器より先に固定されたことまで示す。先行計算の不存在は自己申告」と書く範囲に限られる。

## 文書の内的整合性

主推定量については、§4、§7、`_run_difference` は同じ一つの推定量を指しており、ここは壊れない。

- §4 は raw event を `0,...,m_r-1` とし、`Y[r,i]` の域を `i=1,...,m_r-2` と固定する。[事前登録:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:149)
- 実装は `analysis_events = events[1:]` とした後、その隣接対を作る。current は raw `seq=1,...,m_r-2`、following は `seq=2,...,m_r-1` となる。[解析器:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:382)
- outcome は文書どおり `log(T[i+1]/T[i])` で、current の `assigned_invert` に振り分け、arm 平均差を取る。[解析器:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:407)
- 0 commit scan は `analysis_events`、すなわち `T[1],...,T[m-1]` 全体に掛かる。[解析器:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:399) これは全ての主 outcome に現れる窓の集合と一致する。
- 時間 block へ渡される `index` と `count` も位置除外後の outcome に rebasing されており、§6 と一致する。[事前登録:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:247) [解析器:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:667)

一方、次の内的不整合・曖昧さがある。

- **§0.1 の前向き性は v2 について偽である。** 「指定 outcome を一度も観測していない時点で §1〜§9 を固定した」と書く一方、同じ節の項目 4 は v1 の判定と 0 commit 内訳を観測したと明記する。[事前登録:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:59) [事前登録:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:78) 「前者は v1 だけを指す」と読めば整合するが、その限定が書かれていない。
- **§9 の hash 記述は二通りに読める。** 冒頭は各成果物が「本書の bytes」の hash を記録すると現在形で述べる。[事前登録:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:330) 後段は既存 12 件には v1、解析文書には v2 を要求すると述べる。[事前登録:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:342) 実装は後段の具体則を採用している。[解析器:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:263) 冒頭を現在の v2 bytes と読むと既存 12 件は全て不適格になるため、単なる文章上の小瑕疵ではない。
- **§0 の「outcome の式は不変」は限定しないと誤読を招く。** 点ごとの `log(T[i+1]/T[i])` は不変だが、添字域と推定対象は変更されている。[事前登録:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:21) §4 自身は v1 と推定対象が同一でないと正しく認めている。[事前登録:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:169)
- **副次層の 0 commit 規則は未指定である。** §7 は「主判定全体」を inconclusive にすると書くが、解析器は subgroup membership を適用する前に run 全体を scan する。そのため、当該 subgroup が 0 の窓を全く使わなくても、その run は全副次層で無効になる。[事前登録:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:278) [テスト:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:253) 解析要約で主層由来の sign、feasible、time block が全て理由付きになる挙動はこの読みである。[解析要約:135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/analysis-summary.json:135)
- **「この 12 件専用」は byte-level の受理条件ではない。** 解析器は最大 12 path と登録 seed/configuration を検査するが、既存 12 ファイルの hash allowlist は持たない。[解析器:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:567) テストが作る合成成果物も受理される。[テスト:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:270) 「v1 束縛・指定軸・指定 seed の cohort 向け」なら正しいが、「現物 12 bytes 以外を受理しない」は誤りである。
- **`not_certified` の事実記述が既に古い。** 文書は「本 wave では直さない」とするが、全差分は診断用文言への修正を含む。[事前登録:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:94) [wave.diff:679](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:679) 解析推定量には影響しないが、現物との参照不一致である。

§5 の検出力については、v1 の仮定を未再検証の条件付き仮定として継承しており、実装も 12 run 完備時だけ df 11 の区間を出す。ここに新たな矛盾はない。[事前登録:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:241)

## 結果の解釈で越権になるもの

- **11 run の集約推定値は出してはならない。** 事前登録の `theta` は 12 cluster の等重み平均であり、12 未満または無効 run があれば判定を出さない。[事前登録:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:283) さらに欠落理由は outcome の 0 なので、11 run の complete-case 選択は outcome 依存であり、MCAR を仮定できない。12-run estimand を別の11-run estimandへ無断で変えることになる。
- 解析器は内部では数値 run の平均を一時計算するが、無効理由があれば `theta_log` と `effect_percent` を出力しない。[解析器:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:466) [解析器:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:509) 解析要約の null が正しい成果物である。[解析要約:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/analysis-summary.json:18)
- **副次 5 層を主判定の代用にしてはならない。** それらは探索的で、多重比較補正なし、主判定を置換しないと明記されている。[事前登録:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:247) 5 点が全て正でも、「効果があった」「主仮説を支持した」「6 regime に一般化できる」とは読めない。書けるのは exact な診断条件で得た探索的点推定の記述までである。
- **11 個の個別推定値の公開自体は、凍結規則違反ではない。** ただし同じ 12 件は完全に unblind される。今後この値を見て endpoint、窓、観測長、seed、層を選べば、その追試計画は data-informed であり、同じデータの再利用を独立確認とは呼べない。新規データによる追試まで無効になるわけではないが、これらを pilot 情報として見た事実の開示が必要になる。
- 「等価」「推奨方向が実用優越」「反転方向が実用優越」「効果なし」「検出力不足だから実質ゼロ」は全て書くべきでない。
- trace 有効な診断系なので、throughput 性能改善、未計装 build への一般化、variant 採用根拠、直列性・正しさの証拠とも書けない。[事前登録:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:84)
- 疑似割当の物理過程からの独立性は未検証であるため、「形式的無作為化により因果効果が証明された」とも書けない。[事前登録:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:125)

## 残った 0 commit の意味

判定は **(c) どちらとも言えない** である。

`seq >= 1` の記録済み窓が 0 commit だった事実だけでは、真の一時停止、処置や先行処置が作った状態、window 境界、counter の記録方法、短い窓の確率的変動を区別できない。特に総 trace 長が短いことだけでは、既に記録された中間窓の 0 を直接説明できない。一方、窓長・窓の切り方が 0 の発生確率へ影響する可能性は残る。

また、`log(T[i+1]/T[i])` は 0 で定義できず、0 の run だけを落とすと outcome 依存選択になる。したがって「1 件発火したから規則が厳しすぎる」とは言えない。言えるのは、この測定設計では主判定が 1 run の 0 に対して脆弱だったことまでである。

正しい直近の一手は次の二段階である。

1. 同じ 12 件については、v2 の指示どおり `inconclusive` を最終結果として受理する。11-run 集約や副次への置換を行わない。[事前登録:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:281)
2. 原因を区別する必要があるなら、それは本解析とは別の診断・新規測定として扱う。新しい outcome を見る前に、観測長と窓構成を固定した独立 cohort で検証する。同じ 12 件向けの v2 を再改訂する話にはしない。

## 絶対規律

1. **規律 1、観測者効果: 抵触なし。** 文書は trace 有効な診断系の局所応答へ明示的に限定し、性能値へ昇格させない。[事前登録:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:86) ただし親 insight が throughput 改善へ読み替えた瞬間に抵触する。

2. **規律 2、正しさゲート: 抵触なし。** policy≠0 は未認証で、採用、fitness、選択結果に使わないと明記される。[事前登録:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:91) `not_certified` 修正も正の認証信号を追加せず、「検査していない」という負の事実を mode 別に正すだけである。

3. **規律 3、後付け禁止: 確認的主張に対して抵触する。** v2 の位置除外は `window_commits=0` の分布を見て選ばれたため、outcome を全く見ずに固定した確認計画ではない。[事前登録:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:27) v2 を revised theta の計算前に固定したことは、二度目の後付けを防ぐが、最初の outcome-informed 改訂を消去しない。透明な事前指定再解析としては成立するが、独立な確認的証拠には戻らない。

4. **規律 7、測定時点と現行コードの分離: 抵触なし。** 成果物には測定時点の v1 hash、解析文書には現行 v2 hashを別々に要求している。[解析器:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:20) 既存成果物を現行文書へ書き換えず、v1 記録を測定時点の事実として保持する実装である。

## 親の誤り

- brief の目的「確認的に出す」は強すぎる。改訂規則は粗い outcome の観測後に選ばれており、実結果も主判定 `inconclusive` である。[親brief:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:6)
- brief の「受理集合を広げない」は public 入力組について偽である。[親brief:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:70) 段 4 の R4 は成果物への射影だけに限定して正しく訂正している。[段4裁定:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:42)
- brief の whole-file pin 調査は誤りで、段 4 の R7 が自ら訂正している。[親brief:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:94) [段4裁定:76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:76)
- brief の「将来走行が v2 hash を記録することは正しい」は producer 単体では正しいが、本解析器がそれを拒否する点を欠いていた。[親brief:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:97) 段 4 の R5 はこれを訂正している。
- 段 4 R1 の「各 D、theta、SD、CI、decision のすべてが変わる」は過度な一般化である。[段4裁定:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:15) 実際、今回の `decision` は再び `inconclusive` で、集約値と CI も null のままである。[解析要約:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/analysis-summary.json:18) 正しくは「変わりうる」である。
- 段 4 R2 の「規則を結果より先に凍結した要求は満たせる」は、「結果」を revised theta、CI、decision に限定した場合だけ正しい。[段4裁定:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:25) outcome 一般を意味するなら、0 commit 内訳を見た後なので誤りである。
- 段 4 R6 の M1 を「rebasing test 1 本だけが殺す」とする単一理由性は現物と合わない。[段4裁定:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s4/s4-ruling.md:123) `analysis_events` は pairing と 0 scan の両方で共有されるため、`events[1:]` を `events` に戻すと rebasing test に加え、seq0-zero test も失敗する。[解析器:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:386) [テスト:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:315)
- 段 4 R5 の「この 12 件専用」は、運用意図としては理解できるが、受理集合の literal な説明としては強すぎる。現物 12 個の hash は pin されず、同じ契約を満たす合成成果物も受理される。

## 総括

- **[must-fix] 親 insight で v2 を確認的事前登録または独立確認証拠と呼ばない。**
  影響: JSON の値は変わらないが、`primary.decision` の証拠強度と参照区分が「確認的」から「outcome-informed な事前指定再解析」へ変わる。

- **[must-fix] 凍結順を「証明済み」と断言しない。**
  影響: 推定値は変わらないが、commit 祖先関係、結果 commit、入力 12 bytes 同一性の参照が未確認のままになる。

- **[must-fix] §9 の generic な「本書の bytes」ではなく、実際に適用した v1-artifact／v2-analysis の読みを結果説明で明示する。v2 自体の再改訂はしない。**
  影響: 読みを誤ると既存 12 件の受理集合が「全件受理」から「全件拒否」へ変わり、現在の `inconclusive` 自体が生成不能になる。

- **[must-fix] 11-run 集約と副次 5 層による主判定の代用を行わない。**
  影響: 違反すると `theta_log=null` が未登録の 11-run 数値へ変わり、要求 cluster 数が 12 から 11 へ事後変更される。

- **[must-fix] M1 の単一理由性主張を成果物の mutation 記録で採用しない。**
  影響: 解析値は変わらないが、M1 の kill 集合参照が「1 test」から少なくとも「2 test」へ変わる。

- **[real] 主推定量の添字域、位置除外、pairing、時間 block rebasing は実装と一致する。**
  影響: 修正対象はない。ここを変えると各 run の `D[r]`、副次 block membership、完全時の theta と CI が変わる。

- **[real] 規律 1、2、7 への実装上の抵触はない。**
  影響: 値と受理集合は変わらないが、性能・正しさ・現行 v2 測定済みという主張へ拡張すると参照範囲を逸脱する。

- **[未解決] `seq >= 1` の 0 が実現系の停止か測定窓の性質かは、許可資料だけでは判別不能である。**
  影響: 現成果物の `primary.decision=inconclusive` は変えられず、原因帰属だけが未確定のまま残る。

静的読解のみであり、pytest その他の検査は実走していない。