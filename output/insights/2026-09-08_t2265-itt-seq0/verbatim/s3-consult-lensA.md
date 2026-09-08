## 事前登録として成立するか

結論は、**同じ 12 成果物に対する前向きな確認的事前登録とは言えない**。正確な呼称は「v1 の outcome と欠測構造を見た後に凍結した、透明性のある同一データ再解析計画」である。

理由は次のとおり。

- v2 は v1 の `inconclusive` と、`window_commits = 0` が 57 件、そのうち `seq = 0` が 55 件という分布を見てから、その 55 件を無効化する規則を選んでいる。[origin-verbatim.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/origin-verbatim.md:9) [origin-verbatim.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/origin-verbatim.md:15)

- この計数は単なる「構造」ではない。`window_commits` は `T[r,i]` の分子そのものであり、0 か否かは outcome の粗い観測である。[backoff-counterfactual-preregistration.md:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:117) [backoff-counterfactual-preregistration.md:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:221)

- v1 自身が「結果を見た後に `seq = 0` を落とすのは後付け」と明記している。[origin-verbatim.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/origin-verbatim.md:20) 正確な v2 推定値をまだ計算していないことは、追加の探索自由度を減らす価値はあるが、すでに越えたこの一線を元には戻さない。[origin-verbatim.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/origin-verbatim.md:24)

したがって、v2 が成立するのは次の限定された意味だけである。

- 見た情報を漏れなく開示する。
- v2 の theta、分散、CI、最終判定をまだ見ていないことを明示する。
- 以後、同じ 12 成果物について規則を再変更しない。
- 結論を「部分的に outcome を開示した後の事前指定再解析」と呼び、独立な確認試験と同格に扱わない。

完全な前向き確認として成立させるには、この規則をまだ見ていない独立データまたは真に未開封の holdout に適用する必要がある。

`seq = 0` 除外と「`seq >= 1` の 0 commit も落とす」改訂には、因果的には原理的な差がある。前者の選択指標は全 run に共通する位置で、個々の `assigned_invert` や outcome 値を直接見ない。後者は処置後の `window_commits` に条件づけて失敗窓を選択的に削除し、群別の outcome 分布そのものを変えるので ITT を壊す。

ただし、この差は**個々の event を選ぶ規則の因果的危険度**を分けるだけで、同じデータで規則を選んだ時点の後付け性を消さない。「改訂後の正確な theta をまだ見ていない」だけを基準にすると、`seq >= 1` の 0 commit 除外も同じ論法で正当化できてしまう。その基準では境界を引けない。

## 位置除外は処置前か

辿れるのは、解析器が採用している対応関係までである。

- schema 検査は `seq = 0,1,...` の連続性、時刻の単調性、窓統計、`assigned_invert` が 0/1 であることを確認する。[backoff_counterfactual_analysis.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:130) [backoff_counterfactual_analysis.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:160)

- 推定器は `current` の割当で `following/current` の log 比を群分けする。[backoff_counterfactual_analysis.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:381) [backoff_counterfactual_analysis.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:397)

この対応を採る限り、`seq = 0` について正しい分解は次である。

- event 0 に記録された窓 `T0` は `Z0` より前に閉じる。
- しかし event 0 は同時に最初の割当 `Z0 = assigned_invert` を持つ。
- v1 の `Y0 = log(T1/T0)` は、その最初の割当の直後 outcome である。v1 文書も `Z[i]` が event `i+1` の窓を支配するとしている。[backoff-counterfactual-preregistration.md:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:124) [backoff-counterfactual-preregistration.md:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:126)

したがって、**「seq 0 の窓は処置前」は辿れるが、「seq 0 の event 全体は処置と無関係」は成り立たない**。`events[1:]` にすると、処置前 baseline だけでなく、最初の割当 `Z0` の直接比較 `Y0` を推定対象から落とす。

さらに `T1` は新しい最初の outcome `Y1 = log(T2/T1)` の分母として残る。`T1` は `Z0` の影響を受けうるため、event 0 の影響が解析列から因果的に完全消去されるわけでもない。v1 は持ち越しと、pre-state が先行割当の結果であることをすでに認めている。[backoff-counterfactual-preregistration.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:63) [backoff-counterfactual-preregistration.md:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:132)

処置群・対照群の選択については、規則自体は全 run から一律に最初の位置を落とすので、outcome 条件つき削除ではない。しかし、実際に 1 件減るのは `Z0` が属した側の arm である。段 2 プランも fixture の割当数が `12/12` から `11/12` になると予告している。[s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:84) 12 seed の最初の bit が偏っていれば、複数 run で同じ arm が多く減る経路はある。

しかも解析器は、artifact seed と genome の結合は検査するが、各 `assigned_invert` がその seed の LCG 列と一致するかは検査しない。event 検査は 0/1 だけである。[backoff_counterfactual_analysis.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:138) [backoff_counterfactual_analysis.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:260) テスト fixture も LCG ではなく単純な `index % 2` である。[test_backoff_counterfactual_analysis.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:73)

よって、producer の順序を含む主張はこの射影だけでは決着しない。決着に必要なのは、`patches/cicada-adaptive-counterfactual.patch` の割当・更新・trace 出力順と、`tools/pegasus/probes/t2187_adaptive_const_probe.py` の parser が各 field を event に対応づける箇所である。前者は v1 冒頭、後者は測定条件に名前だけ現れる。[backoff-counterfactual-preregistration.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:3) [backoff-counterfactual-preregistration.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:104)

## 判定不能に戻る経路

成果物を開かずに言える範囲は次のとおり。

- **残る 2 件の 0 commit:** 2 件が `policy 2 / write-heavy / 48 threads` のどれかの run にあれば、v2 の残存全 event scan により主判定は `window_commits_zero` で `inconclusive` になる。主層はこの exact 行だけから集められる。[backoff_counterfactual_analysis.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:593) 段 2 プランの v2 scan は `analysis_events` 全体を対象とするため、seq 10/11 が最後の event や層外の current でも逃げない。[s2-plan.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:27)

- **主層かどうか:** 一次資料は 2 件の workload、threads、seed を開示していないため決められない。主層外だけなら、その workload/threads の副次層は判定不能になるが、主判定はそれだけでは壊れない。

- **副次 9 層への波及:** 2 件のどちらかが主層 run にあれば、`recommended_delta_sign`、`both_actions_feasible`、time block の各層も、membership に入った event だけでなく run 全体の zero scanを受ける設計なので広く判定不能になる。[backoff_counterfactual_analysis.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:639) [backoff_counterfactual_analysis.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:660)

- **missing arm:** `seq = 0` が、v1 の paired current 集合における片方の arm の唯一の event だった run は、除外後に `missing_assignment_arm` となる。[backoff_counterfactual_analysis.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:403) schema は両 arm の存在を admission 時には保証しない。さらに zero 検査が missing-arm 検査より先なので、seq 10/11 の zero と missing arm が同じ run にあれば、表面に出る理由は zero だけになりうる。[backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389)

- **12 cluster:** 前 wave の報告上は主層 12 cluster がすでに揃っている。[origin-verbatim.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/origin-verbatim.md:9) 同じ bytes を再利用し admission を変えなければ、位置除外そのものは cluster 数を減らさない。ただし v1/v2 SHA の分離を誤ると artifact load が例外で停止し、`inconclusive` の JSON にすら到達しない。現行コードは解析文書の hash をそのまま artifact に要求している。[backoff_counterfactual_analysis.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:570) [backoff_counterfactual_analysis.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:581)

草稿 §7 の「そのまま報告し、同じ 12 件について再改訂しない」は正しい。[prereg-v2-draft.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s3/prereg-v2-draft.md:41) 再度規則を変えれば、残る障害に合わせた三度目の選択になる。ただし、その態度を守っても v2 が前向き確認へ昇格するわけではない。報告上は「凍結した再解析規則による inconclusive」とするべきである。

## 推定量と検出力

**推定量の意味は変わる。** 原子的な outcome 式 `Y = log(T[i+1]/T[i])`、log scale、cluster 等重み、等価域は維持できるが、平均を取る割当機会の集合が変わる。

v1 は raw index `i = 0,...,m-2` を明示している。[backoff-counterfactual-preregistration.md:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:114) v2 は raw `i = 1,...,m-2` だけになる。したがって推定対象は「後続 event を持つ更新の ITT」から「初回更新を除き、後続 event を持つ更新の ITT」へ変わる。初回は唯一、pre-state が過去の policy 2 割当に汚染されていない機会でもあるため、単なる機械的な 1 件減少とは限らない。

草稿の「推定対象、outcome 定義を 1 字も変えていない」は誤りである。[prereg-v2-draft.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s3/prereg-v2-draft.md:5) 段 2 プラン自身が、analysis version を上げる理由として「推定対象集合」が変わると認めている。[s2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:88)

草稿は §0、§7、§9 だけを提示しているが、最終 v2 では少なくとも §4 の添字域と §6 の time-block 母集団を明記し直す必要がある。段 2 プランもその変更を予定している。[s2-plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:116) [s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:119) §4 が v1 のままなら、文書内で「i=0 を含む」と「最初の対は 1,2」が競合し、凍結した推定量が一意にならない。

自由度については、12 run がすべて有効なら cluster 数 `R=12` は変わらず、`df=11` と `T90_DF11` / `T95_DF11` はそのままでよい。推定器も event 数ではなく 12 個の `D[r]` の標本分散を使う。[backoff-counterfactual-preregistration.md:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:134) [backoff_counterfactual_analysis.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:459) missing arm や zero があれば CI 自体を作らないので、異なる df へ切り替える問題でもない。

一方、検出力の `cluster SD = 0.032` は revised `D[r]` にも同じ SD が成り立つという追加仮定を要する。1 件減る arm が run ごとに異なり、初回効果が後続と異なれば、`D[r]` の分散も変わる。v1 の 82.3% はもともと未観測の計画仮定に全面依存すると明記されている。[backoff-counterfactual-preregistration.md:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:177) [backoff-counterfactual-preregistration.md:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:193)

従って v2 で直すべきなのは critical value ではない。「v2 の revised cluster estimate にも SD 0.032 を仮定する限り計画上の判定力は同じであり、その仮定は再検証していない」と限定し、実測 `s_D` と CI 半幅に判定を委ねるべきである。

## 凍結の証拠

commit DAG で検証できるのは次までである。

- v2 文書の exact blob が祖先 commit に存在する。
- 解析器 commit と結果 commit がその子孫である。
- 解析器が exact な v2 文書 hash を検査した。
- 結果が入力 artifact の SHA-256 を記録した。現行解析器も preregistration と各入力を hash 化して返す。[backoff_counterfactual_analysis.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:570) [backoff_counterfactual_analysis.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:577) [backoff_counterfactual_analysis.py:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:673)

一方、commit 順だけでは次を証明できない。

- v2 commit を作る前に、別 script、REPL、コピーで v2 推定値を計算していないこと。
- commit を後から組み直していないこと。ローカル commit の author/committer 時刻は変更可能で、最終的な DAG だけを見た第三者には分からない。
- 「誰も計算していない」という否定命題。前 wave README と草稿の記述は証言であり、暗号学的証明ではない。[prereg-v2-draft.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s3/prereg-v2-draft.md:17)

また、artifact が v1 hash を記録していることは「測定時点では v1 が発効していた」証拠にはなるが、同時に v2 が測定後の解析規則であることも示す。[prereg-v2-draft.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s3/prereg-v2-draft.md:22)

追加実装なしで強められる証拠は次である。

- v2 文書だけの commit を、解析前に既存 remote へ公開し、remote 側の受領時刻と immutable commit hash を残す。その後の解析器・結果を descendant とする。
- 新結果がすでに出す `inputs[].sha256` を、前 wave の committed `analysis-result.json` の入力 hash と比較する。これで 12 成果物の bytes が同一であることは示せる。
- `git diff` で v2 文書 commit から結果 commit まで事前登録文書の bytes が不変であることを示し、結果内の preregistration hash と照合する。
- 既存の署名手段があるなら v2 commit を署名する。ただし署名は内容と署名者を強めるだけで、未計算の証明にはならない。

## 親 brief の誤り

**P1 は §0 の現物を過読している。** brief は「文書 §0 が in-place 改訂を定める」とする。[s1-brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:51) しかし §0 が定めるのは「旧版を Git 履歴に残す」「新しい commit」「理由と時点を明記する」だけで、同一 file への in-place 改訂か addendum かは定めていない。[backoff-counterfactual-preregistration.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:13)

**目的の「結果より先」は過度な一般化である。** brief はこの表現を wave の目的に置くが、v1 の主判定と 57/55 件の outcome coarsening はすでに見ている。[s1-brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:8) 正しくは「v2 の exact theta、CI、decision より先」であり、「結果一般より先」ではない。

**P3 の「event 0 を完全に外す」は計算上のみ正しく、因果的には過大である。** raw event 0 は pair から消えるが、`Z0` が支配した `T1` は新しい最初の pair の分母に残る。[s1-brief.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:59) 従って event 0 の直接対比を落とすとは言えるが、event 0 の処置影響を完全除去するとは言えない。

**P4 は現物と一致する。** 現行 zero scan は raw `events` 全体であるため、v2 で集合を替えなければ seq 0 の 55 件が発火し続ける。[s1-brief.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:61) [backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389)

**P5 はこの射影から検証不能である。** 性能 artifact identity と producer は必読対象に含まれていない。従って、性能文言を 1 byte も変えられないという結論を本回答で現物確認済みとは扱えない。[s1-brief.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:63)

**P6 の条件文自体は正しいが、棚卸しとして不完全である。** seq 10/11 が主層なら zero で止まるが、位置除外後の missing arm も独立した停止経路である。また同一 run に zero があれば検査順により missing arm が報告上隠れる。

**pin 閉包は部分的にしか確認できない。** 射影された現物で確認できる固定値は解析器の単一 SHA 定数と、テストの独立 literal である。[backoff_counterfactual_analysis.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:17) [test_backoff_counterfactual_analysis.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:21) brief の repo 全 hit、`check_docs.py`、producer、歴史記録まで含む「閉包」は、それらの現物が射影されていないため再検証できない。[s1-brief.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:80)

**DW-O10 には将来経路の不整合がある。** brief は将来 producer が v2 SHA を記録するのは正しいとする。[s1-brief.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s1-brief.md:99) 一方、段 2 プランは artifact admission を v1 literal 専用にし、v2 artifact を受理しない設計である。[s2-plan.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:39) [s2-plan.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s2/s2-plan.md:50) これは既存 12 件だけを読む一回限りの analyzer としては成立するが、将来正しく生成された v2-bound artifact は同 analyzer に拒否される。「producer 変更不要」は本 wave の既存 cohort に限定しなければ過度な一般化である。

## 総括

- **must-fix — v2 を前向き確認と呼ばない。**  
  影響: JSON の theta は変わらないが、`primary.decision` を確認的証拠として受理できる範囲と README の主張が変わる。

- **must-fix — §4 に revised index 集合を明記し、「推定対象不変」を撤回する。**  
  影響: raw `i=0` を含むか否かで各 `D[r]`、`theta_log`、`cluster_sd`、CI、最終 decision が変わる。

- **must-fix — 「seq 0 の窓が処置前」と「seq 0 の割当効果を落とす」を区別する。**  
  影響: 位置除外を因果的に受理する根拠と、推定対象の参照記述が変わる。

- **real — seq 10/11 zero、missing arm、SHA 分離失敗は別々の停止経路である。**  
  影響: `confirmatory_complete`、`theta_log`、`decision`、`reasons`、または結果 JSON を生成できるか自体が変わる。

- **real — 12 cluster の df=11 と critical value は維持できるが、82.3% の power は revised cluster SD に条件づく。**  
  影響: `T90_DF11` / `T95_DF11` は変えず、検出力表の参照条件だけを限定しなければならない。

- **real — commit DAG は content の順序を示すが、未計算を証明しない。**  
  影響: preregistration hash と input hash は検証できる一方、第三者が「結果を見る前」として受理できる範囲は remote 公開時刻までに限定される。

- **real — v1-only artifact pin と将来の v2 producer 出力は閉じていない。**  
  影響: 現在の 12 artifact の受理集合は保てるが、将来の正しい v2-bound artifact は同じ analyzer の受理集合から外れる。

- **未解決 — producer における window closure、割当、backoff 適用、trace 出力の順序。**  
  影響: 数値計算式は変わらないが、「位置除外は処置前」という因果上の受理根拠を確定できない。

指定された 7 ファイルの静的読解だけを行った。12 件の凍結成果物は開かず、ファイル変更、commit、pytest 実行はしていない。