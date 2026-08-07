指定資料はすべて読めた。既知の Git `-z` 問題は除外し、pytest は実走していない。

R1-1 | must-fix | terminal ledger 検査が成功 gate になっていない。ledger が欠落・部分書込・読取 OSError で非 terminal でも、child rc=0/1 をそのまま返す。逆に checker は schema・commit・spec・ID を検証せず、`True == 1` も通るため偽 terminal にできる | `tools/mutation_worktree.py:674-703,750-761,887-908`; `s5-impl.md:19` | child rc=0＋`summary.recorded < registered` が wrapper 成功になる。部分台帳の `status`・`failed_nodes` が残り、レポート／certified 選択が未完走結果を完走として扱いうる。

R1-2 | must-fix | §2-3 は out を「生成 container 外」に要求するが、実装は checkout 外しか検査しない。`--out <scratch>/.izanagi-mutation-worktree/ledger.json` が通り、完走時に ledger と dispatch evidence を container ごと消す。その後 receipt 保存が同名 container を再作成する | `tools/mutation_worktree.py:286-305,353-384,735-747,794-803`; `orchestrator/tests/test_mutation_worktree.py:430-451` | mutation ledger の `summary`・全 mutation record・dispatch evidence が消失する一方、receipt は `teardown_completed=true`、`container_preserved=false` を残す。レポートは証拠を再検証できず、次回は再作成された container に阻止される。

R1-3 | must-fix | out lock は out だけに束縛されていない。lock directory が `tempfile.gettempdir()`、すなわち `TMPDIR` と host に依存するため、同じ out でも別 TMPDIR／別計算ノードなら別 lock になる。さらに TMPDIR を source 内に置くと snapshot 前に共有木へ lock file を書き、比較はその dirt を恒真にする | `tools/mutation_worktree.py:168-196,329-350,869-875`; `orchestrator/tests/test_mutation_worktree.py:326-338` | 二 producer が同じ ledger を後勝ち上書きし、`baseline`・各 `status`・`summary.recorded/matching` が実行順で変わる。source 内 lock は並行受入の偽赤も作るが wrapper receipt は `shared_snapshot_matches=true` になる。

R1-4 | must-fix | 未完了 container を wrapper 経由で resume する経路が存在しない。既存 container は常に拒否され、stderr が示すのは inner harness の直呼びである。この直呼びは out lock・snapshot・evidence 再退避・teardown・wrapper receipt 更新・GIT_* 除去をすべて迂回する | `tools/mutation_worktree.py:361-374,612-615,806-839,873-905` | resume 完走後も container/admin と dispatch evidence が残り、receipt は未完了値のままになる。別 scratch の wrapper と並走すれば repo-path lock が分裂し、同じ ledger の `status`・`summary` が last-writer-wins になる。

R1-5 | must-fix | SIGINT/SIGTERM handler は child の `wait()` 中だけ有効で、provision・evidence rehydrate・teardown 中は無防備である。SIGTERM は途中状態のまま即死でき、SIGINT は未捕捉の `KeyboardInterrupt` になる。また child exit と `killpg` の race で OSError が handler から漏れる | `tools/mutation_worktree.py:618-671,882-915`; `orchestrator/tests/test_mutation_worktree.py:420-427` | evidence rename、container 削除、admin 削除の途中状態が receipt／resume 指示なしで残る。保存済み mutation record は artifact 再読不能となり、レポート上 `KILLED` 等を証拠付き結果として数えられない。

R1-6 | must-fix | 一般の OSError／予期しない例外を rc=125 に正規化していない。`subprocess.run()` の起動 OSError や一部 `mkdir()` は裸で漏れ、main と `__main__` は `MutationWorktreeError` しか捕捉しない | `tools/mutation_worktree.py:124-148,553-565,909-957,963-968` | wrapper infrastructure failure が shell rc=1になる。rc=1は正常完走した「期待不一致 child」と同じ値なので、親が正当な mutation mismatch と誤分類し、receipt は `failure=null`／`container_preserved=false` のままになりうる。

R1-7 | must-fix | teardown の部分成功を state に反映できない。evidence を rename 後、container/admin 削除が失敗すると `_teardown()` が return せず、呼出側の `evidence_relocated` 代入も行われない | `tools/mutation_worktree.py:568-584,722-747,781-792,895-941` | evidence は実際には `<out>.dispatch-evidence` にあるのに receipt は `relocated=false` を記録する。検証 consumer は消えた旧 path を参照し、mutation ledger の artifact を無効化して report／certified 根拠から落とす。

R1-8 | must-fix | admin 以外の共有 Git 書込経路が開いている。`worktree add` は Git 定義の post-checkout hook・smudge/process filterを実行でき、partial clone では common object store を lazy-fetch できる。`submodule update --init` は未初期化時に common `.git/config` へ submodule 設定を書き、既存の custom update command も実行できる。これらを repo config から遮断していない | `tools/mutation_worktree.py:114-136,465-479,529-546`; snapshot の盲点は `tools/mutation_worktree.py:329-350` と `docs/mutation-restore-durability-design.md:424-435` | hook/filter/custom command は source/main working tree・index・config・refs・objectsを変更できる。ignored/skip-worktree dirtや config/refs/object変更は snapshot が見ず、別 bytesを読んだ baseline・`failed_nodes`・mutation `status` が正式台帳に入る。

R1-9 | must-fix | MW-04 の atomic ownership test は `mkdir(exist_ok=False)` に到達しない。test が事前に container を作るため、先行 `lstat()` 拒否だけで常に緑になる | `tools/mutation_worktree.py:361-374,397-408`; `orchestrator/tests/test_mutation_worktree.py:312-323` | MW-04 で `exist_ok=False` を無効化しても test は緑のままなので台帳は `MW-04=SURVIVED`、`summary.matching` は1減る。裁定が事前登録した ownership gate の検出力がゼロである。

R1-10 | must-fix | MW-06 は別理由で必ず赤になりうる。fixture の `_plain_repo` には `external/ccbench` がなく、HEAD 比較を無効化すると後続 submodule 検査が失敗する。例外 regex も不一致となるため node 自体は赤になる | `orchestrator/tests/test_mutation_worktree.py:52-59,341-346`; `tools/mutation_worktree.py:482-526` | HEAD gate を除去しても台帳は `MW-06=KILLED` と記録し、`summary.matching` と kill 率を1件水増しする。現行 commitを検査したというレポート根拠が偽になる。

R1-11 | should | spec と wrapper の派生 artifact 間に非 alias 条件がない。`--spec <out>.wrapper-receipt.json` は受理され、child が spec を読み終えた後に receipt が同じ file を上書きする | `tools/mutation_worktree.py:286-305,383-384,764-803` | ledger の `spec_sha256` が指す原文 bytesを失い、resume は spec hash 不一致で停止する。レポートの preregistration proof chain が再現不能になる。意図的な path 衝突を要するため D205 上 must-fix には上げない。

R1-12 | should (D205 backlog) | container/admin の所有は lexical path のままである。admin backpointer を検査してから evidence renameとcontainer削除を挟み、admin削除直前には再検査しない。この間に own admin を renameし、foreign adminを同じ pathへ移すと foreign adminを削除する。containerも同じ rename-and-replaceに弱い | `tools/mutation_worktree.py:397-408,706-747` | 別 worktree の admin消失により、その run の Git操作が `artifact_error`／`TIMEOUT` へ変わり、別 ledger・reportの値を壊す。ただし inode-bound teardown は段4で意図的に採らなかったため、本 sliceの must-fixではなく明示 backlog とする。

## 総括

1. must-fix は **R1-1、R1-2、R1-3、R1-4、R1-5、R1-6、R1-7、R1-8、R1-9、R1-10**。
2. 実装は段4裁定を **満たしていない**。特にプラン v2 の lock、生成 container 外 artifact、条件付き teardown／resume、fail-closed、および MW-04/MW-06 の単一理由性が破れている。
3. 探したが健全だった箇所は次の3点。

   - `tools/mutation_harness.py` は HEAD と同一 SHA-256で、無変更。
   - 大域 `worktree prune`、`worktree remove`、`submodule deinit` はなく、非競合の成功経路では evidence → container → own admin の順序になっている。
   - docstring/test文言は観測点間 bytes に限定され、§9.1 の6条件完了や §10 の物理永続性を主張していない。