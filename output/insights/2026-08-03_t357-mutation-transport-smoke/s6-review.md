本レビューではテストを実行していない。以下の `PASSED` / `KILLED` は既存 ledger の field を引用したものである。

結論を先に言うと、両 ledger から「今回の3変異の限定射影が一致した」ことは確認できる。しかし `compare_verdicts.py` の `GO` は、親文書がいう「完全一致」や transport だけを変えた同値性を証明していない。

## 比較器の実像

| 区分 | field / 条件 |
|---|---|
| 合否に入る | spec の mutation ID の重複・集合・件数、両 ledger の top-level `repo_head` / `spec_sha256` の相互一致、両 `baseline.status == "PASSED"`、各 ID の `id` / `status` / `failed_nodes` / `matches_expectation` の相互一致 |
| 観測だけ | `procedure.collection.collected_nodes` の件数と集合。欠損・差分とも `WARNING` だけで合否に入らない |
| 明記された除外 | `runner_mode`、`receipt_path`、`job_stdout_path`、`duration_s`、`runner_sha256` |
| 実際には黙って除外 | `schema`、`runner_identity`、`tool_sha256` / `tool_identity`、`test_command`、timeout、registration、collection の status/rc/hash/artifact、baseline の rc/failed_nodes/timed_out/artifact、mutation の expected fields/rc/timed_out/artifact_error/injection evidence/test-output hash、`summary`、`nonterminal_history` など |

`EXCLUDED` は表示用の定数にすぎず、比較ロジックを制御していない。[compare_verdicts.py:13](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:13) [compare_verdicts.py:114](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:114)

順序については、`failed_nodes` は list のまま比較される。一方、mutation record は ID 辞書へ変換されるため ledger 内順序は消え、collection は集合比較になる。[compare_verdicts.py:35](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:35) [compare_verdicts.py:146](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:146)

## 実測 ledger の突き合わせ

| field | leg 1: dispatch | leg 2: bundle/local |
|---|---:|---:|
| `repo_head` | `ea6ca433...` | 同一 |
| `spec_sha256` | `1d13164c...` | 同一。実 spec の実ハッシュとも一致 |
| collection | `PASSED`, normalized 5281 | `PASSED`, normalized 5281 |
| collection `duration_s` | 31.973 | 2.084 |
| baseline | `PASSED`, rc=0, failed_nodes=[] | 同左 |
| baseline `duration_s` / stdout 内所要 | 272.589 / 247.68 | 249.048 / 248.54 |
| G01 | `KILLED`, 期待 node 1件、match=true | 同左 |
| G01 `duration_s` / stdout 内所要 | 492.708 / 247.52 | 243.115 / 242.62 |
| G03 | `KILLED`, 期待 node 1件、match=true | 同左 |
| G03 `duration_s` / stdout 内所要 | 267.418 / 246.36 | 249.573 / 249.08 |
| G04 | `KILLED`, 期待 node 1件、match=true | 同左 |
| G04 `duration_s` / stdout 内所要 | 502.767 / 238.80 | 248.378 / 247.87 |
| mutation 順序 | G01, G03, G04 | 同一 |
| `test_command[0]` | `/usr/bin/python3.10` | `/bin/python3.10` |
| runner executable SHA-256 | `7d51cd6b...` | `d6bca2b8...` |
| pytest distribution / entrypoint hash | 同一 | 同一 |

親要約の status / failed nodes / match は ledger と一致する。一方、[RESULT.md:6](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:6) の「test command は両 leg で byte 一致」は ledger と食い違う。両実行の既存 stdout は Python 3.10.12、pytest 9.1.1、48 workers、5282 items を記録しているが、実効 inner Python の byte identity は ledger にない。

collection の生 stdout には両方とも5282個の nodeid が同一順序で存在した。しかし `_normalize_node()` が nodeid 全体の `\` を `/` に変換し、次の2 caseを同じ keyへ潰している。

- `...[output//x]`
- `...[output\\x]`

したがって ledger の5281は「収集 test case 数」ではなく「衝突後の key 数」である。[mutation_harness.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:798)

所要の再計算は次のとおり。

| 量 | leg 1 | leg 2 |
|---|---:|---:|
| ledger `duration_s` 合計 | 1567.455 s | 992.198 s |
| baseline + 3 mutation の stdout 内所要 | 980.36 s | 988.11 s |
| collection stdout 内所要 | 7.84 s | 1.55 s |
| 全 inner 所要 | 988.20 s | 989.66 s |
| 外側との差 | 579.255 s | 2.538 s |
| 投入から終了まで | 1571 s | 1249 s |
| 実測差 | colspan | 322 s |

親の1567.5 / 992.2、980.4 / 988.1、wall差322秒は合う。ただし587.1 / 4.1は collection の実作業7.84 / 1.55秒を丸ごと overhead に数えた値で、「scheduler overhead」という名称は不正確である。

## 所見

| # | 所見 | 根拠 (file:line または ledger の field) | これが real なら成果物 (変異台帳の verdict / 結論 / 裁定材料) が何にどう変わるか | 深刻度 | 提案する最小の対処 |
|---:|---|---|---|---|---|
| 1 | 【確認】「除外は5 fieldだけ」は虚偽で、意味論的 identity を大量に捨てている。実 ledger でも `test_command` と executable hash が異なる。`runner_sha256` 全体を除外すると、mode固有差だけでなく Python/entrypoint/pytest identity まで一括で失う。 | [compare:13](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:13)、[RESULT:22](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:22)、両 ledger の `procedure.test_command` / `runner_identity` | 結論は「transport verdict 完全一致」から「異なる runner identity 下で4-field射影が一致」へ狭まり、恒久実装への GO 材料としては不十分になる。 | blocker | schema・tool・registration・timeout・expected fields・共通 runner identity を比較し、mode固有 pathだけを局所的に除外する。実効 inner interpreter identity も outer envelopeへ記録する。 |
| 2 | 【確認】比較器は恒真ではないが、共同故障を合格させる。実 spec が3件なので両 ledger 空は拒否される一方、両側の比較 field が型不正な同値、`matches_expectation=false`、baseline の `status` だけ偽装、同じ誤った head/hash、collection 両欠損は GO になり得る。 | [compare:59](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:59)、[compare:130](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:130)、[compare:138](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:138)、[compare:164](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:164) | `compare.txt` の rc=0を mutation effectiveness や ledger integrity の証拠として使えなくなる。 | must-fix | spec非空、実spec hash、anchor、exact schema/types、baseline rc=0/failed=[]、全 mutation `matches_expectation is true`、collection status/rc/nodesを合否条件にする。transportだけの同値判定なら「両falseも同値」と別名称で出す。 |
| 3 | 【確認】「spec順の順序付き完全一致」は実装されていない。mutation はID辞書化、collectionは件数＋集合であり、順序と一部の多重度を失う。さらに node正規化が5282 caseを5281 keyへ衝突させる。今回だけは生5282列も完全一致していた。 | [compare:47](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:47)、[compare:170](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:170)、[harness:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:798) | 現成果物の狭い verdict は維持できるが、「比較器が順序を保証した」「collection 5281 tests」は撤回が必要になる。 | must-fix | ledger の ID列を spec ID列と直接比較する。path部分だけを正規化し parameter id は変更しない。collection は生 canonical node列または衝突しない multiset hashで比較する。 |
| 4 | 【確認＋推論】collection 並列度差が verdict に効かなかったのは、集合が同じだったという実測だけではない。`_collect_expected_nodes` は期待 node の存在確認後、collection hashを記録するだけで、`_observed_status` は mutation stdout の rc/failed setしか見ない。非期待nodeの collection 差は構造的に verdictへ届かず、比較器でも WARNING 止まりである。 | [collection command:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:928)、[collect:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:976)、[status:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:1177)、[stage4:80](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage4-ruling.md:80) | `-n 0`対既定48が安全だという結論は出せず、collection driftがあっても同じ GO が出る。 | must-fix | 両経路の collection 並列度を同一に固定するか、事前裁定どおり collection 差を NO-GO にする。 |
| 5 | 【確認】時間表の outer/inner 合計は概ね正しいが、overhead の因果ラベルと43走外挿が誤っている。旧T-243の9161.633秒は41 mutation＋baselineの42走分で、collection 226.653秒を除外しているため「43走の総 overhead」ではない。 | [RESULT:27](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:27)、[RESULT:40](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:40)、[stage4:64](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage4-ruling.md:64)、T-243 ledger各 `duration_s` / `artifact.stdout` | 実測結果は「ledger内575.257秒、投入から322秒短縮」。約2.5時間はqueue、collection実作業、長時間bundleの単発queueを分離できない条件付き推定へ落ちる。 | must-fix | 表を「harness外側との差」に改名し、collection内所要も引く。9161.6秒を「42 execution runsのpaired差」と訂正し、41規模は予測値として区間・前提を付ける。 |
| 6 | 【確認】attempt 1 は baseline で停止し、mutation writeへ到達していない。したがって [RESULT.md:62](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:62) の「この失敗で復元も正しく働いた」は refuted。確認できたのは baseline fail-closed と、もともと clean な tree が維持されたことだけである。 | attempt1 `baseline.status=FAILED`, `mutations=[]`、[main loop:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:2040)、mutation開始は [main loop:2048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:2048) | walltime/signal後の復元材料は増えておらず、裁定材料から「attempt 1による復元確認」を削除する必要がある。 | must-fix | 「fail-closedを確認」に限定する。正常 mutation 後の clean は別証拠、signal/walltime復元は未確認のまま扱う。 |
| 7 | 【確認】恒久実装を止めた判断自体は逃げではない。D105はtaskを2種へ固定し、D117は第3 taskをユーザー裁定へ返すと明記する。ただし予定裁定パッケージは、option共通の必須契約を落としている。shared/legacy lock移行、durable outer envelope、attempt対応、login直local拒否、canonical full argv等が stage4 で「scope外」に追いやられた。sealed wrapperにも clean env/stdin/cwd/rc 契約は必要である。 | [D105:4710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:4710)、[D117:5551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/docs/decisions.md:5551)、[stage4:51](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/stage4-ruling.md:51)、[handoff:149](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/handoff.md:149) | ユーザーが(a)/(b)を選んでも、不変条件を満たさない恒久実装が「裁定済み」と扱われ得る。 | blocker | option別ではなく共通 prerequisite matrixを付ける。stage3の(b)推奨とattempt1の(a)有利材料を明示的に再裁定し、推奨案を1つ示す。cross-node flock・walltime signalの短い実測は設計択一前に完了可能な別gateとする。 |
| 8 | 【確認】後片付け手順は証拠を壊す。leg1の5 submissionの receipt/stdout/request/result は disposable worktree内にあり、`worktree remove` すれば ledger の `receipt_path` / `job_stdout_path` が全て dangling になる。READMEは比較結果とschedulerログの記録しか前提にしていない。 | [README:80](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/README.md:80)、[RESULT:92](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:92)、leg1各 `artifact.receipt_path` | cleanup後は `_validate_artifact` による再検証が不能となり、現在のGOの一次transport証拠が消える。 | blocker | remove前に5 submission directory一式とbundleの `.o/.e` を永続 evidenceへ固定コピーし、hash manifestでledgerへ結ぶ。その後だけworktree remove/pruneする。 |
| 9 | 【確認】実走は disposable worktreeを対象とし、HEAD・tracked status・diffは cleanだった。しかし driverは `G01_WORKTREE` 環境変数で任意のanchor worktreeへ差し替え可能で、mainも理論上対象にできる。また `git worktree add` とsubmodule initは共通 `.git/worktrees/worktree` を変更する。mainの事後statusはdriverで検査されていない。 | [run_leg1:5](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/run_leg1_dispatch.sh:5)、[README:23](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/README.md:23)、[RESULT:98](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:98) | 現実走の変異先は安全だったが、「mainや他worktreeを1 byteも変えない」というdriver保証にはならない。 | must-fix | overrideを削除またはresolved pathを `$ROOT/worktree` に固定し、SOURCE/main/disposableのpre/post statusを保存する。common Git admin変更はtracked content不変と分けて報告する。 |

## 攻撃して崩れなかった点

- 両最終 ledger の `status`、`failed_nodes`、`matches_expectation`、mutation列は実際に一致している。
- collection の生5282 node列も、この実走については件数・集合だけでなく順序まで一致していた。
- 比較器は壊れたJSON、非object、重複ID、実specに対する空record、missing head、baseline非`PASSED`を拒否するため、完全な恒真ではない。
- [RESULT.md:68](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/RESULT.md:68)–90 は cross-node flock、walltime kill、resume、`total_deadline` / qdel、恒久dispatcher、3変異・単一subsystem・単一KILLED型、41規模未実測をすべて明記している。この射程但し書き自体は十分である。
- D105/D117に照らし、ユーザー裁定なしに恒久taskを追加しなかった点は妥当である。

## 残留物の実査

| 対象 | 現在確認できた状態 |
|---|---|
| disposable worktree | `g01/worktree` がまだ存在し、detached worktreeとして登録中。HEADはanchor、tracked status/diffはclean |
| leg1 dispatch | `output/pegasus-dispatch/` にcollection＋baseline＋3 mutationの5 submission directory。各receipt/request/result/script/`.o`/`.e`が残存 |
| bundle scheduler logs | attempt1の `.o/.e` と最終request 878510の `.o/.e` が `g01/` 配下に残存 |
| `/tmp` lock | login側で `/tmp/izanagi-mutation-0f7beb04f399c6015b87.lock` の空inodeを確認。bnode側はnode-localなので未確認。同じrepo pathなら同名になるという点は推論 |
| submodule clone | ccbench、shirakami、googletestがdisposable worktree内に初期化済み。gitdirは共通repoの `.git/worktrees/worktree/modules/` 配下 |
| main / 他worktree | mutationの実走先がmainだった証拠はない。共通Git管理領域はworktree登録により変化している。main statusに既存の複数worktree untracked表示があり、G01起因とは帰属できない |

## 前段所見との対応

| 前段所見 | 状態 | 査定 |
|---|---|---|
| A1 smoke walltime不足 | closed | 45分へ拡大し、実ジョブは上限未到達 |
| A2 `total_deadline` / active qdel | partial | 文書化・smokeでは迂回。恒久修正なし |
| A3 kill window / dirty resume | partial | disposable worktreeで被害を隔離。機能自体は未解決 |
| A5/B cross-node flock | partial | 未確認と明記しただけで実測なし |
| A6/B12 targeted走 | closed | smoke commandはcanonical全走。ただし変異型・subsystem偏りは残る |
| A7 collection並列度差 | regressed | 実測したが、事前条件に反して差をWARNINGへ落とす比較器になった |
| A10選択バイアス | partial | 41 recordを再集計したが、43走総overheadの表示でcollectionを脱落 |
| B14未実在事前登録 | closed | 恒久matrix対象外。smoke specは実在anchor/nodeを使用 |
| B1/B2 D105/D117 | partial | 実装停止は正しいが、裁定パッケージの共通prerequisiteが不足 |
| B3 env allowlist | partial | attempt1で実害を観測し使い捨てscriptは修正。恒久経路は未実装 |
| B5 sanctioned path追加 | closed | production変更なし |
| B8 transport証拠の非永続性 | regressed | 問題を認定したのに、cleanupがleg1 receiptを削除する手順のまま |
| B4/A6 canonical command固定 | partial | smokeだけ全走。恒久validatorなし |
| A4/A9/B6–B11 | partial | real認定後scope外化され、裁定材料への取り込みが不十分 |

## 総括

- 信じてよいのは「この3変異の最終 `status/failed_nodes/matches_expectation` が一致した」という限定観測だけである。
- `compare_verdicts.py` のGOを「transport完全同値」や恒久実装GOとして信じてはいけない。
- 必須但し書きは「実効runner identityを同一に拘束せず、比較器もrunner/test/evidence fieldの大半を検査していない」。
- 裁定パッケージには共通prerequisite matrix、推奨案、lock移行、durable evidence、attempt/resume対応が欠けている。
- leg1のreceipt群を永続化するまでdisposable worktreeを削除してはならない。