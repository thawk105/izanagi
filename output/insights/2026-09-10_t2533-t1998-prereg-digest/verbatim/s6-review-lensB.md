## 前提と読んだ資料

指定された 5 資料はすべて全文を読めた。指定外の checkout／worktree は読んでいない。

- `s4-adjudication.md`
- `AUTHORITATIVE-VALUES.md`
- `s5-author.md`
- `s3-lensB.md`
- `verbatim/D1790.md`

対象は commit `3b64ffd7b` と `d424c1fa0` の各差分として確認した。現在の `main` は共通祖先から 3 commit 先へ進んでおり、tree 比較の `git diff main..HEAD` には対象外の逆差分も混ざるためである。pytest・checker・mutation は実走しておらず、以下は静的検査結果である。

## 所見

重大度: must-fix — 新設した 2 つの Git subprocess site が、production process 起動の exact inventory に登録されていない。[consumer:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:349) と [consumer:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:373) は、campaign 全体を再帰 AST 走査する [test_ccbench_spawn_sites.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_ccbench_spawn_sites.py:374) に捕捉されるが、expected inventory [同:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_ccbench_spawn_sites.py:82) に T-1998 の 2 site がない。そのため [exact inventory node:2600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_ccbench_spawn_sites.py:2600) と [bounded-site node:3414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_ccbench_spawn_sites.py:3414) が静的に不一致となる。`s5-author.md` の「所有外への波及」は Git 依存自体を認識しているが、この exact registry consumer を取り逃がしている。  
放置時: 算出値や受理集合は変わらないが、受入全走は焦点外の 2 node が赤となり、この 2 commit を受理できない。

重大度: must-fix — 段 4 で KILLED 必須とした m1・m2・m7・m8 に、永続テストの killer がない。段 4 は measurement hash 不一致、CURRENT hash 不一致、二定数統合、重複 key 拒否をそれぞれ独立に要求している（`s4-adjudication.md:122-149`）。しかし measurement 負例は「異なる blob」ではなく文書が存在しない commit を選ぶ [test:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:161) ため、[blob 読取失敗:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:359) で止まり、measurement SHA 比較 [同:1375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:1375) を通らない。loader テストも raw/blob 不一致 [test:702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:702) と正例 [同:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_t1998_stock_inline_pair.py:715) だけで、CURRENT 比較 [consumer:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/campaign/t1998_stock_inline_pair.py:390) を単独では殺せない。重複 spec や、同値の二定数を一つへ統合した形を拒否するテストも存在しない。したがって `s5-author.md:112` の「必須 6 node は実装済み」は現物と食い違う。  
放置時: 段 4 の変異受入では少なくとも m1・m2・m7・m8 が SURVIVED となり、事前登録した acceptance を満たせない。

## 焦点走に入っていない層

- 静的に赤となる層:

  - `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
  - `test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites`

- 二段以上辿って確認した到達経路:

  - consumer path → `materializer_admission.MATERIALIZER_ADMISSION_REGISTRY` → `test_p3_build_authority_cli.py` の exact registry。既存 key は変わらず、ここは赤要因なし。
  - consumer path → `_REVIEWED_PERF_FILES` → `test_official_perf_closure.py` の全 production AST 走査。今回の Git call は tracked perf call でなく、赤要因なし。
  - `subprocess.run` → recursive process-site discovery → 上記 `test_ccbench_spawn_sites.py` 2 node。ここが取り逃がし。
  - test file → acceptance ledger consumer → 90% coverage gate。6 node は余裕内。
  - 新 docs の三軸 literal → `s8b_holdout_freeze.search_repository` → `test_s8b_repo_scan_invariant.py`。新文書は rr50 の陽性対照で、holdout rr80/rr20 hit は増やさない。
  - `tools/check_subprocess_bytecode_guard.py` は Python subprocess だけが対象で、今回の argv0 は `git`。違反対象外。

- 実行環境:

  - detached HEAD は `git rev-parse HEAD` が成立する。
  - `mutation_worktree.py --commit` は実 Git detached worktree を作成・検証するため成立する。
  - acceptance nproc の `/scr` 経路も local clone と detached checkout を作るため成立する。
  - submodule 未初期化は superproject の `rev-parse`／`show` に影響せず、正式 mutation worktree は事前に初期化を要求する。
  - `.git` または `git` executable のない source export では collection error になるが、その形で走る現行 repo harness は見つからなかった。

- 全文走査:

  - `test_t1998_stock_inline_pair.py` 末尾の禁止対象は replay admission imports と `argmax`。consumer に該当文字列はなく、`re` 自体も禁止されていない。
  - 新文書には `argmax` があるが、この検査は consumer source だけを読む。
  - `check_docs.py` の exact placeholder 3 語は追加文面にない。新文書は `LIVING_DOCS` や placeholder 対象族にも入らない。
  - hooks は repo 内容の禁止語／import を走査しない。`guard_read` は docs/output の 80 KB 超だけが対象で、新文書は 13,245 bytes。

## pin 閉包の結果

探した key:

- 新 path／basename、spec marker、schema literal
- `T1998_PREREGISTRATION_PATH`、measurement/current 定数名
- job body、gitlink、環境契約、両 arm source digest の先頭 12 桁
- 変更前後の consumer／test／docs README の whole-file SHA-256 と Git blob ID
- `file.py:line` 参照、docs 側参照
- exact site 件数、ledger nodeid、byte／最長行予算

見つかった pin:

- 新文書 SHA-256 `464e3af59a1e…719c` は consumer の measurement/current 定数にそれぞれ 1 回ずつ pin され、現物 bytes と一致する。
- consumer の subprocess site 数は `test_ccbench_spawn_sites.py` の exact inventory による pin があり、今回そこが未更新。
- consumer path／basename は `test_official_perf_closure.py`、`test_p3_build_authority_cli.py`、`materializer_admission.py` に membership pin がある。既存 membership は維持されている。
- test file の既存 30 nodeid は acceptance ledger にある。新 6 nodeidはない。

見つからなかった pin:

- consumer・test・docs README の変更前後 whole-file SHA-256／blob IDを固定する live golden。
- 新 path、marker、schema literalに対する既存の別 pin。
- live な行番号 pin。hit は過去 insight／凍結記録だけで、更新対象の executable gate ではない。
- 新文書専用の byte／最長行予算。13,245 bytesで hook の 80 KB 境界にも届かない。

## 受入台帳の見積り

台帳の現物は `duration_seconds_by_nodeid=22,157`、`nodeid_count=22,157`。対象差分は非 parameterized test を 6 件追加するので、静的 collection 見積りは 22,163 件となる。

`22,157 / 22,163 = 99.9729%` で、[coverage ≥ 0.90 gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-t1998-prereg-digest/orchestrator/tests/test_acceptance_schedule_order.py:704) を十分上回る。したがって6件の未登録によって赤になる node は **0 件**。台帳更新はこの gate を赤から緑へ変えない。

## 総括

現物値、文書 SHA、job body SHA、gitlink、環境契約 digest は正本と一致している。  
docs README・D1790・D1874・Pegasus runbook と事前登録文書の主張にも矛盾は見つからなかった。  
supported detached／mutation／`/scr` clone 環境は新しい Git 依存で壊れない。  
一方、焦点外の process-site exact inventory で 2 node が静的に赤となる。  
さらに段 4 の mutation acceptance は少なくとも m1・m2・m7・m8 の killer がなく未充足である。  
pytest・checker・mutation は実走しておらず、緑とは報告しない。