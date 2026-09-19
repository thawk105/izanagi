## 判定と検算範囲

**NO-GO。3 job の完走記録は裏付けられていますが、8 変数の値確認と signal 非配送の断定は修正が必要です。** 再測定や実装変更を求める所見ではありません。

以下、`R` はレビュー対象 README、`F` は worklog fragment、`J` は指定 job directory、`E/<nonce>` は指定 evidence directory を指します。

静的検算を実施しました。pytest・ジョブ投入・throughput の比較や解釈は実施していません。

- 「dry-run と実投入」表の **18 cell**、「完走の記録」表の **42 cell** を、receipt・meta・qstat・accounting・JSONL と照合。
- JSONL **3 本・378 行**を読み、`sha256sum`・`wc -l` でも独立検算。hash、0600、header の HEAD・plan hash、terminal の計数は一致。
- **372 session・744 測定・1,116 probe・3,720 rep rc** を検算。全 session complete、全 probe clear、全 rep rc 0、side 各62、drop 0。
- epoch 差 **4178 / 4141 / 4602 秒**、accounting Elapse **4182 / 4145 / 4607 秒**、Remaining、割合4.8〜5.3%は一致。表の時刻は小数1桁への丸めとして整合します。
- 実投入の指定証拠 **30 file**、submit の meta／rc／stdout／stderr **24 file**、初期 qstat **3 本**、launcher **6 本**を確認しました。

## 修正が必要な主張

**1. 「8 変数を値で確認」は成立しません。**

`floor_pair_campaign.sh:106` の `write_result` が payload に写す FP 変数は次の6個です。

| 環境変数 | job-result field |
|---|---|
| `FP_NONCE` | `nonce` |
| `FP_EXPECTED_HEAD` | `expected_head` |
| `FP_SPEC_RELPATH` | `spec_relpath` |
| `FP_SPEC_SHA256` | `spec_sha256` |
| `FP_MODE` | `mode` |
| `FP_WINDOW_ID` | `window_id` |

これらは3 job 全件で submit receipt と一致します。`FP_EVIDENCE_DIR` は出力先として使われ、指定 directory に receipt があることを確認できます。

一方、`FP_ELAPSTIM_REQ` は payload にありません。`walltime_seconds`（44行目）は形式と正値を検査するだけで、例えば `01:00:00` も通ります。通過をもって受信値 `24:00:00` の逐語一致とは言えません。scheduler の86400Sは scheduler 側の要求確認です。

R:114、F:20、HANDOFF:57を「6変数は値一致、evidence directory は出力先で確認、walltime 環境変数は非空・妥当形式の通過を確認したが受信値の直接記録なし」に直してください。既存証拠の限界を記録すれば足ります。

**2. `reason=completed` は「signal 配送なし」の証明ではありません。**

`run_driver` の176〜188行目が示すのは、設置した trap による観測が記録されなかったことです。F1012のSIG_IGN継承を否定できない以上、配送されても観測されない場合を排除できません。また、walltime 未到達はTERM/HUP/INT一般の配送契機を否定しません。

R:76、91、119、135、F:21の「配送なし」「配送される契機がない」「signal が来ない」は、「trap による signal 観測記録なし。walltime 未到達。配送有無・trap 発火能力は未検証」に限定してください。

## 親 brief と申し送り

HANDOFF の段1は **21:35 JST**、段4は **21:36 JST** と記され、実投入 **21:32:11〜22 JST** より後です。P1の「実行で確かめる」もplace完了後の時刻に置かれています。現存資料では、事前判断と事後転記を区別できません。**改ざんとは断定できませんが、事前記録の証拠としては使えません。** 時刻の誤記なら根拠を示し、事後整理ならそう明記する必要があります。

軽量版そのものは `docs/dev-wave/core.md:10` の一次資料から事実を抽出するdocs-only条項に整合します。repo外launcherを運用資材とする今回のscopeとも整合します。ただし、HANDOFF:22の「scriptを書かない」は現物6本と矛盾するため、「repo内実装変更なし、repo外運用launcher作成」と直すべきです。

条件dispatchでは、**DW-O09を「凍結bytesに触れない」だけで不成立とした理由が不適切**です。`docs/dev-wave/operations.md:71` はdocs-onlyでも成立し、docs pathも検索すると明記しています。今回、対象2 pathのtracked参照を `git grep` した結果は0件でしたが、これを親の着手前検査の実績にはできません。O10／O11／O13の非該当判断には、指定範囲から反証はありません。

P1はplace logとコードが支持します。P2は「qsubは順次、実行は3 node並走」が正確です。P3の所要見込みと実測の違い自体は誤りではありません。最初のterminalだけで3 job全件の確認が済むわけではありませんが、実際には3件とも確認されています。DW-G05の成果物影響の説明も妥当です。

w2／finalizeの同一HEAD、末端余裕、create-only、commit延期、証拠保全は契約と整合します。ただし、watcherはrequest ID・nonceだけでなく、**JSONL検索の`c1`も`c2`へ変更が必要**です。

## 総括

**判定：NO-GO。must-fix 2件の過大主張を修正してから公開してください。完走値を撤回する必要はありません。**

| 番号 | real/refuted | 重要度 | 根拠 file:line／field | 放置時の値・主張への影響 |
|---|---|---|---|---|
| 1 | real | must-fix | R:114、F:20、`tools/pegasus/floor_pair_campaign.sh:44,106` | 受信値を記録していないwalltimeまで「8変数の値一致」と断定する。 |
| 2 | real | must-fix | R:119,135、F:21、同script:176,188 | trap観測なしをsignal配送なしへ拡張する。 |
| 3 | real | should | `J/HANDOFF.md:15,30,44`、submit receipt:`prepared_epoch` | 実投入後のbrief／裁定を事前判断として読める。事後整理か誤記かを明示する。 |
| 4 | real | should | `J/HANDOFF.md:24`、`docs/dev-wave/operations.md:71` | docs-onlyにも適用されるDW-O09を誤った理由で免除した記録が残る。 |
| 5 | real | should | `J/HANDOFF.md:59`、`E/8b8dc69bffae50e5e14d574ea3e99153/scheduler.stderr:Elapse` | HANDOFFだけrr50 Elapseが4141Sのまま。正しくは4145S。Rの値は正しい。 |
| 6 | real | should | R:152、`J/run-watch.sh:27` | ID・nonceだけ更新するとw2監視でもw1の126行を報告する。 |
| 7 | real | should | R:63、F:19、初期qstat:`Entered Queue Time/Started Request Time` | 証拠は「queue投入から開始まで8秒」。その内訳を分離せず「queue待ちゼロ」と断定する。 |
| 8 | real | nit | R:74、`J/observations/qstat-f-*-initial.txt` | `qsub-f`という誤った証拠pathを案内する。`qstat-f`へ訂正。 |
| 9 | real | nit | R:148、dry-run各dir | 各dirには`pre-submit.json`もある。「status dry_runだけ」はfile構成の説明として曖昧。 |
| 10 | real | nit | `J/HANDOFF.md:22`、指定launcher6本 | 「scriptを書かない」が実際の運用資材作成と食い違う。 |
| 11 | refuted | should | `orchestrator/campaign/b4_binary_record.py:149,181`、`J/place.log` | place自身にsite検査があるという疑いは棄却。記載の変更不要。 |
| 12 | refuted | should | `orchestrator/campaign/floor_pair_driver.py:2228`、各JSONL:`header` | live環境／HEAD検査より先にheaderを書くという疑いは棄却。 |
| 13 | refuted | should | 実投入3dir:`scheduler.stderr`／`scheduler.stdout` | accounting出先の誤記という疑いは棄却。stderrに実在、stdoutは全件空。 |
| 14 | refuted | should | F:10,31,33,43、`docs/spool/worklog/README.md` | 指定文法違反はなし。H2は2個、更新1件、base1行、継続2 space。指定placeholderは所見対象外。 |
| 15 | refuted | should | `docs/dev-wave/core.md:10`、R:130,141、指定launcher | 軽量版の採用、集約・採用・§5記入・新gate混入の疑いは指定範囲では棄却。 |

**読めなかった必読資料：なし。** 検索時の仮定path `.claude/skills/dev-wave` は存在しませんでしたが、DW条項の正本を `docs/dev-wave/core.md`／`operations.md` で確認しました。

なお、fragmentのbase digestとland先台帳の一致、親のff-only実行、履歴上の事後改変の有無は、この静的照合では独立に確定していません。