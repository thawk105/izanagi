## 所見

1. 対象 `s2-plan.md:151-216`、`tools/check_docs.py:4166-4259,4590-4802`。同期対象の列挙自体は registry、`test_hooks.py` の二つの golden、runbook 投影、README 宣言表、tagged fence まで揃っている。ただし README 検査は registry 全件との完全一致ではなく、「README に現れた既知 path が宣言済みか」の検査である。README の行と節を両方消す mutant は `check_docs.py` だけでは赤にならず、計画中の `test_readme_tagged_qsub_fence_routes_stdout_and_stderr_outside_repo` だけが防壁になる。一方、本文を残して宣言行だけ消すと `tools/check_docs.py:4795-4800`、宣言行を残して fence を消すと `:4671-4679` で `test_check_docs.py:12475-12483` が赤になる。成果物影響: contract test が弱いか欠落すると、投入手順のない登録 entry を受入が許す。重大度: must-fix。

2. 対象 `s2-plan.md:251-258`、`hooks/guard_bash.py:1200-1210`。受入 command の `bash -n tools/pegasus/p3_s4_loop_pegasus.sh` は、登録後の login node では `dispatch-required` 実行体として構文検査より前に guard に拒否される。A-1 の手本のように job path を argv に渡さず、source を stdin に与える contract test 内の `bash -n` にする必要がある (`test_paper_story_a1_job_contract.py:1125-1131`)。成果物影響: 正しい job body でも計画された短走が guard 拒否となり、syntax の受理結果を得られない。重大度: must-fix。

3. 対象 `s2-plan.md:3-10,220-228,277,285`、`test_paper_story_a2_job_contract.py:81-85`。A-2 型の `if "q" + "sub" in source` を写すと、計画自身が要求する冒頭コメントの `raw qsub` で正しい job body が赤になる。逆に単純な文字列除外を緩めるだけでは、wrapper、絶対 path、変数間接呼出しを見逃す。`qstat` と説明文中の `qsub` を許す正例、および直接・`command`・絶対 path・変数間接の負例を持つ token-aware 検査が必要で、手本は `test_paper_story_a1_job_contract.py:1105-1203` にある。成果物影響: 偽赤になるか、job 内再投入を許して scheduler 上の実行集合を増やす。重大度: must-fix。

4. 対象 `s1-brief.md:17`、`s2-plan.md:17,224-225,239-240`。login harness は hostname stub が実際に呼ばれたことを確認せず、scratch と receipt の非生成だけを見る。bootstrap PATH sanitize が host gate より前へ移る mutant は、stub を PATH から外しても実 login host の `pegasus01` で同じ rc=2 と文言を返せるため緑になり得る。また git、Python、CMake が先に動いても artifact を残さなければ検出しない。この場合 harness が測るのは stub ではなくテスト実行機の実 hostname である。hostname の呼出し marker、host gate より前の PATH 順序、重い command の fail-fast sentinel を必要条件にすべきである。成果物影響: login node で重い前処理へ進む job body が contract を通過し得る。重大度: must-fix。

5. 対象 `s2-plan.md:31-36,233-234`、`docs/pegasus-runbook.md:124-149` 相当の射影。resolver harness は正しい `python3.10` だけを候補に置くため、3.10 未満の bare `python3` という実機条件を再現していない。production shim を消した mutant が ambient `python3` と同じ実体または互換版を拾えば緑になり得る。制御下の「正しい python3.10」と、呼ばれたら識別可能に失敗する「古い python3」を別 directory に置き、production の PATH sanitize、resolver、shim を一続きで実行する必要がある。成果物影響: job 本体は起動しても孫 process が 3.9 を拾い、既知の 19 failure 型で loop が値を生成できない。重大度: must-fix。

6. 対象 `s2-plan.md:220-285`。fragment 削除 mutant は「文字列が必要集合にある」ことしか証明せず、条件反転、rc=2 から rc=0、dead branch やコメントへの移動、同じ fragment の前置複製による順序検査の欺瞞、source directory の取り違え、sanitize 後の再 export、qsub script 引数後への `-o/-e` 移動を捕まえる保証がない。shim 負例も `cmake`、`c++`、`gcc` の注入だけで、禁止集合に掲げた `cc`、`g++`、`make` と動的生成を覆わない。成果物影響: wrong HEAD、dirty tree、login host、誤った prebuild receipt、repo 内出力を受理する job が静的 contract を通り、実行受理集合または証拠参照が変わる。重大度: must-fix。

7. 対象 `s2-plan.md:267-270`、`orchestrator/tests/test_plain_runner_coverage.py:35-41,60-74`。新規 test file には `_run()` だけでなく、`__main__` から実際に `_run()` または `pytest.main` を呼ぶ signal が必要である。計画はその block を逐語で要求しておらず、焦点走にも `test_plain_runner_coverage.py` が含まれていない。成果物影響: 新 contract file が plain runner で 0 件偽緑になるか、受入全走でメタテストだけが赤になる。重大度: must-fix。

8. 対象 `s2-plan.md:153-168`、`tools/pegasus_admission_registry.py:18-21,28-45,69-77,97-116`。提示 JSON は canonical relative path、4 field の順序、class 閉集合、辞書順の挿入位置を満たす。現 registry は 19,135 bytes で、新 entry 後も 1 MiB 上限から十分遠い。`test_hooks.py:3445-3453` は class map と4-field dictの両方を exact 比較するため、`reason` または `primary_gate` の変更も赤になる。成果物影響: 提示 entry を逐語で実装する限り loader または exact-entry 起因の受理差はない。重大度: nit。

## 親 brief への指摘

` s1-brief.md:16` の「登録簿 bytes を pin する golden は無し」は、固定 SHA や凍結 blob が無いという狭い意味では正しいが、「pin が無い」への一般化は誤りである。`test_hooks.py:3445-3453` が全 entry の意味内容を literal golden で固定し、`tools/check_codex_hooks.py:296-357` は作業 bytes と現 HEAD blob の一致を要求する。後者は永続 golden ではないが、未 commit の registry 編集を段 6 起動前に拒否する実効 pin である。

` s1-brief.md:17` の「stub で重い処理へ進まないことを見る」は、現計画の side-effect 非生成検査からは導けない。hostname stub の使用証明と、重い command の未呼出し証明が別途必要である。

`test_check_docs.py:272-369,1120-1139` の admission fixture は production registry の複製ではなく、5 entry の独立した手書き fixture である。したがって registry entry の純増だけで T-1458 型の 320 件連鎖赤にはならない。この型は checker の契約自体を変えた場合に発火する。production docs の同期漏れは `test_real_repo_clean` が別に捕捉する。

新 filename、role 名、xdist group、`known_violations`、duration ledger の key 側も検索したが、固定 hash や閉集合 pin は見つからなかった。`acceptance_duration_ledger.json` は新 test node をまだ持たないが、全件一致ではなく 90% 被覆 gate (`test_acceptance_schedule_order.py:704-716`) なので、現時点で更新必須とは言えない。

## scope 外だが real な所見

`tools/check_codex_hooks.py:41-46,296-357` により、registry を編集した未 commit 状態では review 子を起動できない。`s1-brief.md:29-30` の段 5 author から段 6 review の間に「親が registry を含む統合 commit を作る」を明記する必要がある。これは成果物の追加編集ではなく、既知の F677 を避ける実行順序である。

T-2301 の実差分は `docs/pegasus-runbook.md` §7.7 と A-1 job・tests で、registry、`test_hooks.py` golden、§7.0 投影表には触れていない。T-2320 も brief 上は `backoff_sweep.py`、extended driver、対応 tests と evidence が対象で、新規 Pegasus 実行体を明示的に scope 外としている。現状で同じ registry 行域への競合はない。T-2301 とは同一 runbook file だが §7.0 と §7.7 の別 hunkなので通常は自動 merge できる。

将来、二 wave が同じ anchor 前へ entry を追加する場合、alphabetical 挿入は canonical JSON の必須条件で最終順序を一意にするが、Git の同一 hunk競合そのものは防がない。registry、二つの `test_hooks.py` map、runbook 投影表を一組として再配置し、全三面の集合を再確認する必要がある。

## 総括

最大の欠陥は、login refusal harness が stub 使用も重い command の未呼出しも証明せず、実 host による恒真になり得る点である。
登録簿同期のファイル集合と JSON 逐語は妥当だが、README 完全性は新 contract test に依存する。
親は段 4 で hermetic な hostname・旧 python3 負例と、条件反転を殺す実行 harness を必須化すべきである。
あわせて registry 編集後、段 6 の前に統合 commit を置く順序を裁定すべきである。
pytest、`check_docs.py`、job body は実走しておらず、本回答は静的検査のみである。