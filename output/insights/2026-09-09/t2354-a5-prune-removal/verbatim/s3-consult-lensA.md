## 総括

最重所見は、残置 receipt の書込み失敗を `|| true` で捨てるため、D1700 の機械可読な残置記録が保証されず、条件次第では job も成功終了できる点である。  
remove の rc 伝播そのものは、明示的な `return "$cleanup_rc"` により切れていない。  
兄弟登録 fixture は欠落 path を作るため、prune 再導入時に発火する設計であり恒真ではない。一方、remove 失敗 fixture は実際の残置を作っていない。  
pytest は実走しておらず、以下は静的検査結果である。

## real 所見

1. **残置 receipt の書込み失敗が握り潰され、D1700 を満たさない経路が残る。**

   根拠: plan の置換後は receipt 全体を `} >"$OUTPUT_ROOT/env/worktree-remove.rc" || true` とし、そのまま `return "$cleanup_rc"` する。`/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s2-plan.md:73-81`。cleanup 失敗時に呼ばれる failure receipt は `returncode/stage/line` 等だけで、残置 path を持たない。`tools/pegasus/a5_second_boot_backoff_sweep.sh:76-83`、同`:180-184`。

   何が壊れるか: `worktree-remove.rc` の open/write が失敗すると、remove 失敗時でも後続掃除主体が path を取得できない。remove が成功して `cleanup_rc=0` の場合は、receipt 欠落のまま job rc も 0 になる。

   **成果物影響:** `env/worktree-remove.rc` が欠落・部分化しても成功 job になり得て、remove 失敗時には非0 job rcだけが残り、残置 path が成果物から失われる。

   修正案: receipt の rc を明示的に捕捉し、少なくとも書込み失敗を `cleanup_rc` に合成する。remove 失敗時の path を保証するなら、`write_failure_receipt` に同じ typed path を渡すなど、独立した構造化 fallback も必要である。単に `|| true` を外すだけでは、関数が `remove_worktrees || cleanup_rc=$?` の左辺で実行されるため十分ではない。

2. **remove 失敗テストが「残置」を作らず、D1700 の意味を証明していない。**

   根拠: plan は `$JOB_CCBENCH` と `$JOB_REPO` に「登録されていない path」を渡し、remove を失敗させる。`s2-plan.md:210-223`。したがって receipt に書く path は、実際にはディレクトリも worktree 登録も残っていない入力である。

   何が壊れるか: 「任意の失敗入力 path を `remaining_*` と表示するだけ」の実装でもテストを通り、実際に残った登録を後続掃除へ渡せることを検査しない。

   **成果物影響:** 契約テストが緑でも、receipt の `remaining_*` が実在する残置登録を表すという受入証拠にならない。

   修正案: 二つの実 worktree を登録して lock し、単一 `--force` remove が失敗して登録・directory が残る fixture にする。実行後に両 path が `git worktree list --porcelain` に残ることと、receipt の path が一致することを同時に assert する。

3. **静的契約は prune 不在以外にも受理集合を狭める。**

   根拠: plan は prune 不在だけでなく、二つの remove command の完全な逐語を各1回に固定する。`s2-plan.md:145-160`。現行 `_assert_execution_shape` の他の契約は `orchestrator/tests/test_a5_second_boot_job_contract.py:273-318` にあり、現在は remove の逐語・回数を受理条件にしていない。positive node は同 helper をそのまま呼ぶ。同`:370-371`。

   何が壊れるか: `--` の追加、wrapper 化など、同じ自 path だけを安全に remove する等価実装まで拒否する。これは「prune 正例から prune 不在へ」という一変更ではない。

   **成果物影響:** 計測値は直接変えないが、D1700 を満たす等価な job body が契約違反となり、既存受理集合が余分に縮む。

   修正案: prune の実行可能な不在は静的検査と兄弟 fixture で固定し、自 path remove は runtime の directory／登録消失で検査する。逐語 count も契約にするなら、brief の「変更は1点だけ」を改訂して意図的な受理集合変更として明記する。

   T-1998 launcher test は job body の存在・再利用 path・qsub binding だけを検査しており、cleanup の逐語には依存しない。`orchestrator/tests/test_t1998_launcher_contract.py:56-79`。したがって同テストへの直接波及はない。

4. **M1 は二つの独立 KILL node に同時に拒否され、単一理由性を満たさない。**

   根拠: M1 は literal な `worktree prune` を注入し、静的 positive-contract nodeと実 git sibling nodeの二つを期待 KILL nodeに列挙している。`s2-plan.md:231-238`。静的 regex はこの変異を直ちに拒否し、同じ実行では sibling test も登録消失を拒否する。

   何が壊れるか: 「同じ意味上の理由だから二件でもよい」という plan の説明は、複数 gate が同時に赤なら登録しないという本依頼の単一理由性条件と一致しない。

   **成果物影響:** mutation 台帳の KILL 証拠が過剰決定となり、どちらの観測層が単独で効いたか判別できない。

   修正案: M1 は事前登録から外すか、例えば shell 連結で `pr""une` とするなど静的 regex を通過して runtime sibling nodeだけが殺す変異へ変更する。M2〜M4は記載された契約では別の静的 gateに捕まらず、各1 runtime nodeに収まる。

## 推測

1. **T-1998 の外部 preregistration が旧 script digest を保持している可能性。**

   repo 内に具体的な live 値はないが、consumer は `launcher_script_sha256` を必須の外部 preregistration 値として受け、reservation の digest と exact 比較する。`orchestrator/campaign/t1998_stock_inline_pair.py:132-150`、同`:169-173`、同`:916-918`。実際の preregistration が旧 digestなら、job body変更後の成果物は `launcher-script-identity-mismatch` で拒否される。

   確認対象: 次回T-1998判定へ渡す実際の `T1998PreregisteredIdentity` 記録または生成入口。repo 内には test fixture以外の生成 caller が見つからないため、外部状態は未確認である。

2. **path だけで後続 cleaner が安全に動作できるかは未確定。**

   `remaining_ccbench_path`／`remaining_repo_path` は「どの worktree pathか」を機械可読にする最小形としては十分で、D1700以上の schema は現時点では不要である。ただし node-local path が消えた後に stale gitdir 登録を掃除するなら、所有元の `$CCBENCH_BASE`／`$REPO_BASE` も必要になる可能性がある。

   確認対象: 後続の安全な掃除主体の入力契約。現在は A-5 receipt の runtime consumer 自体がない。

## nit

- remove rc の鎖は切れていない。両 git command は `|| command_rc=$?` で捕捉され、失敗時は path が空にされず、最後に明示的な `return "$cleanup_rc"` がある。`s2-plan.md:21-47`、同`:73-82`。`cleanup_worktrees` も `remove_worktrees || cleanup_rc=$?` で受け、元 job rc が0のときだけ cleanup rcへ置換する。`tools/pegasus/a5_second_boot_backoff_sweep.sh:172-184`。したがって懸念された `[[ ... ]] && VAR=""` が関数の最終 rcになる罠は、この置換形では発火しない。

- 兄弟 fixture は恒真ではない。兄弟 worktreeを登録した後、その directoryだけを削除し、登録が事前に存在することを assert する設計である。`s2-plan.md:191-205`。この unlocked・欠落登録には現在の `worktree prune --expire now` が作用する一方、自 pathの二つの removeだけでは作用しない。`tools/pegasus/a5_second_boot_backoff_sweep.sh:135-163`。

- 期待値の緩和、skip、test削除、現行 script hashの fixtureへの差込み、揮発値の焼込みはplanにない。旧 prune 正例の反転は意図された変更で、むしろ追加契約は強化方向である。

- `assert "prune_rc" not in job` はコメントや説明文字列まで禁止する語彙テストである。`s2-plan.md:145-149`。実行可能な prune 不在は regex と runtime fixtureで足りるため、これは削ってよい。

## 親 brief への反証

1. **exact hash の hit 内訳が不正確。**

   brief は旧 digest の hit を過去 submit 記録と reservationだけとする。`/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s1-brief.md:51-54`。しかし同じ digest はT-1998裁定の逐語にも記録されている。`output/insights/2026-09-08_t1998-stock-inline-parts/verbatim/s4-ruling.md:148-153`。これは歴史資料なので live literal pin ではないが、「hit は二種だけ」という列挙は誤りである。

2. **「live pinなし」は in-repo literal に限れば正しいが、pin閉包としては言い切れていない。**

   A-5 submitterとT-1998 submitterは現在の job bodyから digestを動的計算する。`tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:85-88`、`tools/pegasus/submit_t1998_balanced_stock_inline.sh:87-92`。一方、T-1998 consumerには外部 preregistrationとの exact digest gateが実在する。`orchestrator/campaign/t1998_stock_inline_pair.py:916-918`。したがって「repoに更新対象の固定値なし」は確認できるが、「外部を含む live pinなし」はrepo検索だけでは証明できない。

3. **「receipt consumer は2テスト」は runtime consumer としては誤り。**

   A-5契約テストは filenameや生成物を読まず、producerの `printf` 逐語を静的に見るだけである。`orchestrator/tests/test_a5_second_boot_job_contract.py:297-298`。実際に `env/worktree-remove.rc` を読む既存テストはB-10の1件だけである。`orchestrator/tests/test_backoff_extended_sweep.py:1752-1785`。plan自身も「追加 fixture が最初のA-5 runtime consumer」と訂正している。`s2-plan.md:123-130`。

4. **登録簿については反証なし。**

   entry は path keyと分類 metadataだけで、sha256 pinはない。`tools/pegasus/admission_registry.json:10-14`。既存 pathを保つ今回の変更ではentry変更不要というbriefの結論は正しい。