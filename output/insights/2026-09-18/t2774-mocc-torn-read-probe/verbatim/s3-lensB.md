## 判定と確認範囲

**must-fix は5件です。** hydrate 修正案自体は局所的で、既存 test の marker と両立します。主な問題は、終端ファイルに関する現物との不一致、後段の実走被覆、腕 B の時間予算、集計・因果主張の上限です。

以下、`pilot` は `tools/pegasus/mocc_trace_pilot.sh`、`submit` は `tools/pegasus/submit_mocc_trace.sh`、`discriminator` は `orchestrator/campaign/mocc_g2_discriminator.py` を指します。指定資料・現物・対象ファイルの変更履歴を静的に確認しました。編集、pytest、build、compute 実走は行っていません。

## must-fix

**M1 — 「G2 走は failure.json のみ」は、今回使う T-1943 経路では誤り。**

- **根拠:** plan:97–99、運用事実「job の成果物」に対し、pilot:2238–2291 は T-1943 モードで verifier rc=0/1 を受け入れます。`:2333` の非ゼロ終了はその `elif`、すなわち通常モード側です。T-1943 receipt は `:2985` でも rc=0/1 を許容し、`:3303–3383` で job-result を生成します。
- **成果物への影響:** G2 と job 失敗を同一視すると、有効な G2 の分子・分母、完了分類、待機対象が変わります。
- **是正:** 今回の腕 A は、**G2 の有無にかかわらず後段が成功すれば job-result.json、処理失敗なら failure.json**と記述してください。plan の `--done-file …/job-result.json` と会計の OR 完了は適切です。request ごとに1待ち手、6投入なら6待ち手でよく、結果を見る前に G2 用の done-file を選ぶ必要はありません。verifier rc、discriminator 結論、job 終了状態は別々に集計します。

なお、job-result の生成後にも worktree cleanup があるため、**退避・次の編集開始は会計終端まで待つ**のが適切です。done-file は論理的完了の証拠であり、process 終了そのものではありません。

**M2 — 生死確認の成功条件が discriminator 到達までで、既知の未実走後段を覆っていない。**

- **根拠:** plan:69–74 は verifier/discriminator 到達を成功条件としています。しかし T-1943 の既知失敗は、その後の分類検査でした。現行経路には分類、T2195 finalization、receipt、job-result、cleanup が続きます。
- **成果物への影響:** 生死確認を通過しても、42走すべてが後段で失敗し、受入用成果物を揃えられない可能性が残ります。
- **是正:** 既存の再生死確認1本について、**verifier の結果とは独立に、分類・receipt・job-result・会計終端まで確認する**ことを成功条件にしてください。検査を新設する必要はありません。途中までの raw 観測は保存してよいものの、後段未到達を「鎖が通った」と数えません。

変更履歴と実走被覆は次の区別が必要です。

| 段・変更 | 現物／commit | 指定証拠で確認できる被覆 |
|---|---|---|
| 投入時 policy・compiler mapping 捕捉、job 側照合 | `33d88a6b3`、`891136281`。submit、pilot:796–1269 | 4936 が hydrate に到達したため、今回の入力に対する先行経路は通過。拒否分岐全体の実走証明ではない |
| T1718 compiler gate | `0e8272d3a`、pilot:1493–1525 | **hydrate より前**。4936 では通過済み |
| hydrate と gflags/glog の調達順変更 | `0165027e0`、`b9187e920`、pilot:1528–1656 | hydrate で停止。job-private source を使う static configure/build/install は未到達 |
| detach materialization | `7cf109b6e`、pilot:1660–1683 | 診断 OID を policy から解決する最終形の今回の compute 確認は未了 |
| CMake、TRACE=0→checker→absence→TRACE=1 | pilot:1685–1902 | 4936 では未到達。T-548 の新しい依存 source 経路との組合せは未確認 |
| TRACE=0 文言変更 | `9b4a06d68` | コメントと分類理由の変更。新しい実行 gate ではない |
| workload・witness・discriminator | `d8a6410da`、pilot:1973–2332 | T-1943 の旧 source では no-g2 1走が到達。G2 入力の compute 実績ではない |
| verifier 起動条件 | `e4c949f08`、pilot:2229–2231 | 後から `--protocol mocc --ccbench-root` を追加。8月の実走だけでは現行 argv を証明しない |
| artifact classification | `267741106`、pilot:509–633、2384–2390 | `Path.stat` から `os.lstat` への修正は関連 test の証拠。修正後の compute 完走証拠は指定資料にない |
| policy finalization・receipt・job-result | T2195、pilot:2392–3383 | 4936 は未到達、旧 T-1943 も分類段で停止。今回確認が必要 |

「T-548 **以降に変更された**部分」と「T-1943 実走後に変更され、T-548 時点でも実走未確認だった部分」は別です。後者を含めても、推測で追加修正する理由にはなりません。

**M3 — 腕 B の verifier timeout と90分枠が整合していない。**

- **根拠:** plan:277、304、316 は timeout を分類対象にしますが、秒数を固定していません。参照 driver は `s3_mocc_lock_coverage.py:46,391` で300秒です。各 node は12ペア＝24走です。
- **成果物への影響:** 遅い verifier を含む後半の走が walltime で欠測になり、arm ごとの分母と比較結果が変わります。最終一括保存なら途中の有効結果も失われます。
- **是正:** verifier timeout を300秒と明示し、各走終了時に raw JSON・rc・時間・分類を job dir に保存してください。推奨枠は**各 job `02:30:00`**です。

時間の区別は以下です。

- verify 120秒を仮定した通常見積: `24 × 123秒 = 49.2分`、これに依存準備・二つの build・退避。
- verify 300秒を使い切る場合: `24 × 303秒 = 121.2分`、これに準備・build・退避。
- よって通常見積は約55–65分、300秒枠での予算は約130–150分。ただし build 時間も未実測で、150分は保証値ではありません。

`--queue-wait-timeout 3600 --overall-grace 4200` は、queue 60分＋後処理10分を見込む指定として整合します。walltime を150分に変更すると、投入起算の overall 枠は220分です。90分を維持するなら、K=24完走を前提にせず、予定走数と欠測を明記する必要があります。

**M4 — 親 brief の「0/K で必要性確認・根因へ昇格」は撤回が必要。**

- **根拠:** brief「研究前進」「scope 2」、`:26–30`。plan:306–314、352–354 は既にこの主張を適切に弱めています。
- **成果物への影響:** insight が、有限標本の未再現を機構の必要性・根因確定として報告してしまいます。
- **是正:** plan の限定を親 brief と最終判定にも適用してください。二箇所同時変更、競合時間・abort・再試行の変化、同じ patch で別機序も消える可能性があるため、有意な率差が出ても根因確定にはなりません。

独立 Bernoulli、stock の真の率を歴史値 `5/42` と仮定した計算は次のとおりです。

| 量 | 値 |
|---|---:|
| 腕 A、N=24で1件以上 | 95.23% |
| 腕 A、N=42で1件以上 | 99.51% |
| 腕 B、stock K=24の期待件数 | 2.86件 |
| 診断 0/24 の片側95%二項上限 | 11.735% |
| stock 3/24 対 診断 0/24、片側 Fisher | 0.1170 |
| stock 4/24 対 診断 0/24、片側 Fisher | 0.05461 |
| stock 5/24 対 診断 0/24、片側 Fisher | 0.02482 |

**K の下限は目的ごとに異なります。** 既知の固定率0.119より0/Kの片側上限を下げるだけならK=24ですが、推定値5/42を既知定数扱いして同時対照比較を代替できません。診断の真の率を0とした理想条件でも、等標本数の片側 Fisher、α=.05の検出力はK=24で約14.9%、K=42で約57.1%。80%を目標にするなら**各 arm K=56**が下限になります。node 内相関等を含まない条件付き計算です。

今回は**各 arm K=24の探索的対照**を推奨します。率差検証を目的に変更する場合のみ、開始前にK=56以上と費用を再設定してください。結果を見て有意になるまで延長する設計にはしません。

結論文の上限は、例えば次です。

> 固定 cell で stock は k/K、診断 build は0/Kだった。診断 build による未再現は、追加した読取・validation 条件が G2 発生に関係するという仮説と整合する。個々の間隙の寄与、必要性、根因は確定しない。

**M5 — discriminator の判定不能と G2 検出の欠測を分離する集計規則が不足。**

- **根拠:** plan:99–103 は別列化を指示していますが、分母規則は未確定です。discriminator:491–624 は、blocker が一つでもあれば comparisons を空にして `indeterminate` にします。
- **成果物への影響:** 識別不能な G2 を分子から除くと G2 率が過小になります。逆に verifier 自体の判定不能を確定 no-g2 にすると分母が誤ります。
- **是正:** verifier に基づく G2 検出集計と、discriminator の識別成功率を別にしてください。G2 が確認された走は discriminator が indeterminate／未生成でも G2 として保持します。verifier 判定不能・未完了は別計数し、N、判定可能数m、G2数k、欠測、`k/m`、全投入に対する範囲を記載します。

今回、現実に立ちうる blocker と経路の違いは以下です。

| 条件 | 現物の発火条件・扱い |
|---|---|
| `verifier-anomaly-list-truncated` | `total_cycles != len(anomalies)`。既定 `--max-report 20` のままなので多 cycle 走では成立しうる。T-1892 は各1 cycleだっただけ |
| `verifier-non-g2-anomaly` | 報告 anomaly に G2 以外を含む。G2との混在でも識別全体が判定不能 |
| `verifier-g2-edge-outside-rw-only-shape` 等 | G2でも全辺・理由が規定のrw形でなければ発火。歴史的5件の形が今後の全走を束縛するわけではない |
| witness の欠落・重複・orphan | lineage と全read、store と全write の対応不一致。対象cycle以外の欠落でも発火 |
| `witness-producer-orphan` | stamp のproducerがcommit集合または当該keyのwriterに存在しない |
| `rw-reason-multiplicity-mismatch` | 複数cycle等で同じreader/key/version理由が重複した場合にも成立しうる |
| integrity・frame・identity不一致 | trace不完全、重複、版不一致等。固定 workload だけでは不発を保証しない |

ただし、**witness file／manifest 不在・digest不一致などは blocker 到達前の入力拒否**になり、discriminator.json が生成されない場合があります。また verifier rc=2/3 は pilot:2239–2242 で止まるため、discriminator 内の `verifier-verdict-indeterminate` 分岐まで到達するとは限りません。「四結論」に「未実行／入力拒否」も別列で添えてください。

## should

**S1 — 腕 B の base_dir と実行場所を具体化する。**

- **根拠:** plan:254 は `<submodule repo>` のままです。`patchharness.checkout:360–364` は指定baseから `git worktree add` します。
- **成果物への影響:** computeから不可視、または診断OIDを持たないbaseを選ぶと、腕 B 全体が走行前欠測になります。
- **是正:** このwaveの `external/ccbench`、またはその解決済みgit directoryを明記してください。今回ローカルでは次の**両方**で full OID `e9e477ca1b55348ab4530de0b1cf663ce4555290` を解決できました。
  - `/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-t2774-mocc-torn-read-probe/modules/external/ccbench`
  - `/work/1/SFC/tanab/izanagi/.git/modules/external/ccbench`

computeからの可視性は未実測です。worktree側の既存repoを第一候補とし、実行時に解決できたpath/OIDを既存の実行記録へ残せば十分です。共有checkoutの切替は不要です。

**S2 — 単独性と selftest の具体例をrunner仕様に落とす。**

- **根拠:** generic は clean env（dispatch:348–359、1442–1452）で `PBS_JOBID` も独自envも渡しません。生成scriptとqsub argvは `-b 1` を指定しますが、指定資料だけでは、それを他job不在の証拠にはできません。参照driverは各走前にも `_assert_single_tenant()` を呼びます（`:418`）。
- **成果物への影響:** 同nodeの競合があれば stock／診断の曝露条件が変わり、比較の解釈が弱まります。分類実装の誤りは欠測・G2件数を直接変えます。
- **是正:** cache・scratch・出力先はplanどおりargvで渡し、witness directoryはrunnerがargv由来の実行root配下に作ります。子processには `IZANAGI_MOCC_G2_WITNESS=1` とdirectoryを両armで明示します。単独性は既存運用の確認を使い、新しい共通gateは作りません。

selftest の最小例は、正常rc=0/no-g2、正常rc=1/G2、G2＋discriminator判定不能、rcとverdictの矛盾、JSON不正・空trace・timeoutです。腕 A 集計用には、**job-resultを持つG2正例と、verifier結果を持つ後段失敗例**も必要です。どれも本runnerの集計被覆であり、computeのimport/build成功を証明するものではありません。

masstree warm-up は、同じhydrate出力に対して依存buildより前に実施し、二つのbuildを直列にするplanで整合しています。

## nit

**N1 — 「素のpython3によるrepo importは1534だけ」は誤り。ただし一括置換は不要。**

- **根拠:** pilot:1493の素の `python3` が、`:1504` で `orchestrator.campaign.toolchain_binding` をimportしています。親の失敗証拠にある「他heredocはstdlibのみ」は不正確です。
- **成果物への影響:** 4936はこのgateを通過してhydrateで停止しているため、この行を変更しないことで今回の成果物が変わる証拠はありません。DW-G05に従いnitです。
- **是正:** 「確認された3.10未満での断線はhydrate」と訂正し、compiler gateは通過実績を記載します。他のstdlib処理やこの呼出を一括置換しません。

**N2 — marker・fake interpreter・変異の被覆は概ね適切。実測済みとは書かない。**

- **根拠:** plan:122–182、契約test:1408–1418、1515以降、1994以降、2087以降。
- **成果物への影響:** 提案配置で既存受入が変わる静的根拠は見つかりません。
- **是正:** `HYDRATE_PY` 専用blockを`:1533–1534`間へ置く現在案を維持します。

`'  CHECKER_PY=""'`、`"\n  CHECKER_RC=0"`、`'  VERIFIER_PY=""'`、`"\n  verifier_rc=0"`を複製せず、job-private root の唯一の `--staging-root` と後続CMake optionの順序も維持します。引用・subshell・if/fiの静的読解ではshell構文上の問題は見つかりませんが、`test_mocc_trace_pilot_shell_syntax` の合格は未実測です。

3負例の期待nodeは、いずれも新設予定の次の1件です。

`orchestrator/tests/test_mocc_trace_job_contract.py::test_mocc_trace_hydrate_interpreter_gate_selects_and_fails_closed`

| 負例 | KILLED に必要な検査 |
|---|---|
| hydrateを素のpython3へ戻す | 実hydrate呼出のinterpreter/argv検査 |
| version比較を外す | probe argvの明示的version条件検査 |
| rejected追記を外す | 全候補拒否時の候補一覧検査 |

既存testだけではこれらをKILLEDと断言できません。特にfakeが名前に応じた固定rcを返す方式は、**3.9の推移import例外を実行再現しません**。選択と呼出配線を検査する方式です。planがこの限界を明記している点は適切です。

**N3 — scope は局所修正＋実験に留め、記録の重複を減らす。**

- **根拠:** brief scope制約、plan:103、165–182、338–364。
- **成果物への影響:** failures fragmentの有無だけでG2率や識別結論が変わるとは言えません。
- **是正:** hydrate回帰の契約test1本は実在欠陥の修正確認であり、仮想リスク向けのgate新設には当たりません。job-dirの集計/selftestも本題に直接必要です。failures fragmentは既知障害の短い記録に留め、「4件目」のような未提示集計や新しい一般台帳・検査へ広げません。decisionsは原則0本、通常の記録はinsight/worklogで足ります。

仮説cellは今回は省くplanを支持します。`EXACT_WORKLOAD`外ではdiscriminatorを使えず、各arm6走程度の追加では頻度差の結論も弱い一方、verify300秒なら1cell12走で約61 node-minutesかかります。

## 腕 A の共有資源と順序

| 対象 | 静的評価 |
|---|---|
| 同一submoduleへの並行worktree追加 | scratch pathはjob別、Git管理領域は共有。T-1892は7batch各6投入、実測peak最大6、materialization失敗0。全batchが実行時6並列だった証拠ではない |
| job-staging | raw `PBS_JOBID` を使用しcreate-only。scratchではcolonをunderscoreへ変換。両者を混同しない |
| attempts | 128-bit nonce＋create-only directory（submit:321–335）。並行投入形として妥当 |
| job-dirの `--attempts-root` | repo外なので追加 `owned_prefixes` は不要。repo内の標準job-stagingは既存prefixで許容。tracked変更は許容されない |
| PBS stdout/stderr | submit:379–384でnonce別directoryへの絶対pathを指定。共有ファイルへの上書きではない |
| source固定 | unit1の修正・test・commit→clean固定→再生死確認→batch、というplanは適切。腕 Bを含む全jobの終端までtracked編集・commit・切替をしない |

新しい共有資源gateを加える必要はありません。既存の失敗記録と、全requestを落とさない集計で扱えます。

## 親 brief の数値・断定の証拠水準

`未実測` は今回の条件への一般化を指します。

| 主張 | 評価・訂正 |
|---|---|
| 「T-1943は151秒でdiscriminatorまで到達」 | 運用事実の開始→failure時刻差が151秒。discriminatorはそれ以前に完了していたので、**151秒以内に到達**という1走の証拠。discriminator単体時間や現行経路の完走時間ではない |
| 「1job ≈3〜10分」 | **未実測の一般化。** 提示一次表はbatch span 102–689秒で、個別jobの所要分布ではない |
| 「腕 A 42走は12〜81分」 | 過去のbatch最小・最大を7倍した条件付き見積。予測区間ではなく、queue・現行build差を保証しない |
| 「build2分、verify≤2分」 | **今回未実測。** 二つのbuild、新調達経路、診断armのcommit量を含む上限ではない |
| 「hot読みは本cellで稀」 | 提示briefにこの逐語は見当たらない。一次資料にもhot/cold比率の実測なし。採用不可 |
| 「小value／hot keyで頻度が上がる」 | **未実測。** 静的存在例から頻度の方向は導けない |
| 「supported／contradictedはいずれも実装由来」 | **識別範囲を超える断定。** reader-versionとstampの対応を比較するだけでhook全体・writer版・commit順を証明しない |
| 「G2ならfailureのみ」 | **現行T-1943経路と不一致。M1参照** |
| 「T-548後はcompute未実走」 | 現在は4936による**失敗実走あり、hydrate後は未到達**と書く |
| 「fakeでcompute旧Pythonを再現」 | 配線の模擬であり、実interpreterの互換性実証ではない |

## 総括

**must-fix 5件。** 終端ファイルの説明、最終化までの生死確認、腕 B のtimeout・保存・時間枠、根因主張、判定不能の集計を修正してください。

- **腕 A:** N=42、6投入×7batch。再生死確認1本は別枠。歴史値による本体見積12–81分＋再生死確認＋queue。現行経路の所要は未実測。
- **腕 B:** 各arm K=24の探索的対照、2jobに各12ペア。通常約55–65分を仮置きし、verifier300秒を許容する予算は各job約130–150分、推奨walltime **02:30:00**。率差の80%検出力が目的なら、理想条件でも各arm K=56が必要。
- **scope逸脱:** hydrate局所修正、契約test1本、実験runner・集計は逸脱なし。python呼出の一括置換、新しい共通gate・台帳、不要な仮説cell追加は採らない。failures記録は既知障害の最小記述に留める。

**現状のままbatchへ進める計画としては未充足ですが、修正範囲を広げずに是正可能です。**
