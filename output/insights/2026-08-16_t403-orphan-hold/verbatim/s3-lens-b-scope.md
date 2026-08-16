静的検査のみ。pytestは実走していない。結論として、3ファイルだけの変更では受入経路、qsub競合、異常終了窓を塞げない。

# 所見 1: 受入赤再走が孤児の作業木を強制削除する

判定 (real)

根拠 (file:line): `tools/check_acceptance_reds.py:920` は `run_tests.py --force-dispatch` を実行する。失敗時も `:1268-1282` で `_cleanup_probe` を呼び、`:824-835` が `git worktree remove --force` を実行する。dispatch artifact cleanupも先に `:386` で nonce directoryを削除する。

成果物影響 1 行: holdを検出して受入が赤くなっても、計算中jobが読むsourceとworktreeを消し、DW-G05の再現性を破壊する。

推奨対処: `orphan-hold.json`、dispatch timeout、dispatch制御出力、未回収receiptを検出した場合は probe worktreeを保持し、qstat確認後の人手復旧へ渡す。受入経路を今回の実装scopeへ追加する。

# 所見 2: qsub受理直後のsignal窓ではholdが発行されない

判定 (real)

根拠 (file:line): `tools/pegasus/dispatch_compute.py:1479` のqsub完了後、`:1497` で初めて `active=True` になる。qsub subprocess中にSIGTERMを受けると、例外経路 `:1786-1805` は `active=False` のためcleanupもhold発行も行わない。プランのhold発行位置も `s2-plan.md:142` からである。

成果物影響 1 行: scheduler側ではjobが生きているのに、receiptは初期qdel状態のままになり、source復元・worktree削除・次回投入が通る。

推奨対処: qsub結果が不明になった時点で保守的にholdを作る状態を導入し、qsub中signalを注入するテストを追加する。qdelは追加しない。

# 所見 3: hold検査とqsub・復元・teardownが非原子的

判定 (real)

根拠 (file:line): プラン自身が同一rootのTOCTOUを認めている `s2-plan.md:173-175`。現行の検査とqsubは `tools/pegasus/dispatch_compute.py:1350` と `:1479` に分離している。`mutation_harness` のflock (`tools/mutation_harness.py:2095-2110`) はharness同士だけ、`mutation_worktree` のlock (`tools/mutation_worktree.py:191-213`) は同じ`--out`だけを保護する。teardownもhold検査後に `:903-905` でrenameとrmtreeを行う。

成果物影響 1 行: hold作成と同時に別invocationがqsub、source復元、evidence退避、container削除を実行できる。

推奨対処: dispatch root単位の共有lockを導入し、hold検査・qsub・復元・teardownの判断を同じ排他契約で直列化する。再検査だけでは不十分。

# 所見 4: plan-onlyの例外fallbackが新しいteardown gateを迂回する

判定 (real)

根拠 (file:line): プランは `_should_teardown` へholdを渡す `s2-plan.md:285-298` が、例外fallback `tools/mutation_worktree.py:1167-1199` はplan-onlyなら直接 `_teardown` を呼ぶ。実際の削除は `:903-905` と `:919` にある。

成果物影響 1 行: hold検査の例外、権限エラー、異常終了がplan-only fallbackへ流れると、孤児jobのsource containerが削除される。

推奨対処: teardown許可判定を通常経路と例外経路で共有し、hold判定不能も保存側へ倒す。

# 所見 5: 親receipt実測の一般化が強すぎる

判定 (real)

根拠 (file:line): briefはreceiptのqdel field欠落を孤児なしへ写像している (`brief.md:31-55`)。しかしreceipt保存は `tools/pegasus/dispatch_compute.py:1279-1289` で失敗し得て、setup receipt (`:1883-1909`) にはqdel情報がない。さらに所見2のqsub中signalは135件の完成receipt集合に現れない。

成果物影響 1 行: 「135件中1件だけ」という観測を全jobの安全性へ一般化できず、未記録jobを見逃す。

推奨対処: receipt数ではなく、submission directory・qsub受理記録・schedulerのlive requestを突合する。過去receipt走査を権威にしない結論は維持しつつ、field欠落を安全証明に使わない。

# 所見 6: 回復手順がRUN・qdel・path情報を処理できない

判定 (real)

根拠 (file:line): hold schemaの回復情報は `s2-plan.md:28-38`、停止ledgerの手順は `:241-262` の「qstat終端確認 → checkout → hold削除」だけである。dispatch holdにはdirty pathや明示的なrepo rootがない。qdelの副作用、すなわちF47 latchが武装することは `brief.md:8-11` にあるが、hold recordの回復文言には入っていない。

成果物影響 1 行: RUN状態のjobを終端できず、ユーザーが誤ったworktreeやpathを復元し、holdだけを残す可能性がある。

推奨対処: RUN、QUE/HLD、qstat不明、終端済みを分けた手順を明記する。手動qdelを選択肢にするなら、F47武装と手動解除が必要になる副作用を明記する。

# 所見 7: プランのテストは主要な欠陥を殺せない

判定 (real)

根拠 (file:line): pure classifier試験は `s2-plan.md:322-325`、主な4点の検出力は `brief.md:109-115` に限られる。受入の既存試験 `orchestrator/tests/test_check_acceptance_reds.py:1674-1716` はroot内markerの削除失敗だけで、`_probe_nodes`からのforce removeを検証しない。qsub中signal、TOCTOU、plan-only fallback、stat異常の試験もない。

成果物影響 1 行: classifier呼出しを消してもunit testだけは緑になり、受入worktree削除という実害が未検出のまま残る。

推奨対処: qsub中signal、hold作成とqsubの同時実行、hold作成とteardownの同時実行、acceptance timeout後のworktree保持を実際の呼出し経路で試験する。stderr文字列だけでなく、qsub回数・復元bytes・worktree存在を検証する。

# 所見 8: 並行wave間のroot巻き込みは確認できない

判定 (refuted)

根拠 (file:line): dispatch rootは`repo_root`ごとに作られる (`tools/pegasus/dispatch_compute.py:1319-1326`)。fanoutもshardごとに別scratch・container・checkoutを作る (`tools/mutation_fanout.py:590-633`)。holdを含むshardはmerge前に停止する (`:1694-1730`)。過去evidenceのrehydrateは同じledgerの実行を再開する経路であり、無関係waveのroot scanではない。

成果物影響 1 行: 別worktreeのholdが無関係なwaveのdispatchを全面停止する事故は、現行path設計からは生じない。

推奨対処: 「holdはrepo rootまたはmutation container単位」「兄弟shardは継続するがmergeしない」をrunbookへ明記する。同じphysical rootを共有する手動経路は別扱いにする。

# 所見 9: F47・fanout契約・task_runとの直接衝突はない

判定 (refuted)

根拠 (file:line): F47は別fileを先に検査する設計 (`s2-plan.md:153-171`)。dispatch rootは`.gitignore:26`で無視され、fanout contractはwrapper rcが0/1以外、terminal ledger不成立、teardown不成立を拒否する (`tools/mutation_fanout_contract.py:1288-1307`)。`tools/task_run.py:1-16` はbootstrapのみで、qsub・qdel・source restore・worktree deleteを持たない。

成果物影響 1 行: `orphan-hold.json`自体が通常ledgerやGit dirty検査を壊す根拠はない。ただし受入root cleanupの問題は別途realである。

推奨対処: separate hold、create-only、非終端wrapper拒否は維持する。check_docsやruleopsを安全性の証明と誤認しない。

# 裁定パッケージ候補

## 候補 1: dispatch_compute外のqsub・復元・worktree削除

判定 (real)

根拠 (file:line): `tools/pegasus/submit_floor.sh:194-201` と `:420-439`、`submit_certify.sh:72-80` と `:166-185`、`submit_silo_ladder_rung1.sh:130-146` と `:411-439` はdispatch holdを検査せず直接qsubする。`orchestrator/campaign/patchharness.py:221-239` はsourceをcheckoutで復元し、`:374-383` はworktreeをforce削除する。

成果物影響 1 行: T-403を「repo内でsourceを共有するjob全体」の安全機構と呼ぶなら、これらは完全な未防護経路である。

推奨対処: T-403へ含めるか、対象を`dispatch_compute`の`tests`/`provenance`だけと明示して別裁定へ送る。後者なら「全job fail-closed」と報告してはならない。

## 候補 2: local run_testsとinventory完全性

判定 (real)

根拠 (file:line): `tools/run_tests.py:1751-1821` はlogin nodeの余裕があるとdispatchせずlocal実行する。`tools/check_docs.py:2135-2138` と `:2268-2271` はTASKSとrunbookのinventoryだけを検査し、`tools/hold_inventory.py:1-4` は未知のhold層を自動発見しない。`ruleops.py:2600-2621` もhold gateではない。

成果物影響 1 行: 「新しい操作経路がholdを消費している」という完全性を機械的に証明できず、local runnerを停止対象にするかも未裁定である。

推奨対処: local test実行まで停止対象に含めるかを裁定し、含めるなら共通hold checkerを追加する。含めないなら、source restore・qsub・worktree削除だけが保護対象だと明記する。

## 総括

最重は、受入経路がholdを見ずにnonceとprobe worktreeを削除することだ。  
次に、qsub中signalとTOCTOUが、receiptにもholdにも現れないjobを残す。  
親の135件実測は完成receiptの標本であり、未記録jobの不存在を証明しない。  
dispatch rootのwave間隔離は成立するが、手動qsub経路と同一root競合は未解決である。  
pytestは実走しておらず、上記は静的検査によるreal/refuted判定である。