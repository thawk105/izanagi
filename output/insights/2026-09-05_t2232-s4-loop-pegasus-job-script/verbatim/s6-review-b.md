## 所見

1. 対象 `orchestrator/tests/test_p3_s4_loop_job_contract.py:150,335-353,607-655`、`tools/pegasus/p3_s4_loop_pegasus.sh:69-73`。worktree-container の pattern は固定されていますが、拒否本体は固定されておらず、rc=2 文言一覧にも含まれません。line 71 を `:` に置換しても login harness は host gate で先に停止するため全 target test を通過します。影響: `/.claude/worktrees/` または `/.codex/worktrees/` 配下の REPO_ROOT が受理集合へ入ります。重大度: must-fix。

2. 対象 `orchestrator/tests/test_p3_s4_loop_job_contract.py:195,324,589-604`、`tools/pegasus/p3_s4_loop_pegasus.sh:208-215`。C1 の `qstat_jobid=${PBS_JOBID#0:}` は exact fragment に含まれず、M5 test は scratch 用 path component しか検査しません。`qstat_jobid=$PBS_JOBID` へ変えても static/order/harness は赤になりません。影響: `qstat -f` が raw `0:<request>` を問い合わせ、reservation を作れる allocation の集合が変わります。重大度: must-fix。

3. 対象 `orchestrator/tests/test_p3_s4_loop_job_contract.py:310-332`。順序検査は raw source の最初の `source.index` だけを見るため、実際の `trap finish EXIT` を resolver 後へ動かし、元位置へ `# trap finish EXIT` を置く変異を受理します。同様に required fragment も comment/heredoc 内の複製で満たせます。影響: resolver 以前の失敗で `compute-result.json` を残さない job body が契約済みとして受理されます。重大度: must-fix。

4. 対象 `orchestrator/tests/test_p3_s4_loop_job_contract.py:306-412,589-604`、`s5-author.md:20-34`。M2/M3/M4/M6/M9/M10/M15/M16 を production に当てると、base static contract と line 408 の mutation-fixture 前提が別々に赤になり、「1理由」ではありません。また M5 の `mutant` は line 594 で作られるだけで、line 596-604 の subprocess は正しい式をハードコードしています。影響: 変異結果の failure 数と kill 理由が事前登録および author 報告からずれます。重大度: must-fix。

5. 対象 `tools/pegasus/README.md:342`。一次資料として示す `output/insights/2026-09-05_t2232-s4-loop-pegasus-job-script/README.md` は存在せず、同 directory にあるのは `s1-brief.md` と `s4-adjudication.md` だけです。`check_docs.py` の Pegasus path 検査ではこの参照を検出できません。影響: operator が実装契約の一次資料を参照できません。重大度: must-fix。

6. 対象 `s5-author.md:62-73`、`orchestrator/tests/test_acceptance_schedule_order.py:660-713`、`orchestrator/tests/acceptance_duration_ledger.json:19523`。所有外への波及から acceptance ledger gate が漏れています。新 file は 40 node を収集へ追加しますが ledger 登録は 0 件で、coverage の分母だけが 40 増えます。focus2 の対象にも `test_acceptance_schedule_order.py` は含まれていません。影響: acceptance ledger coverage 値と40 nodeのスケジュール優先度が変わります。重大度: nit。

## 変異 M1〜M16 の可殺性表

| 変異 | 可殺性 |
|---|---|
| M1 | 殺す: `test_p3_s4_loop_job_contract.py:649`。AI worktree 外で走る場合は `:652,655` も赤になり得る。 |
| M2 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M3 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M4 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M5 | 殺す: `:592` の exact fragment count。`:594-604` は作成した mutant を検査していない。 |
| M6 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M7 | 殺す: shim 作成削除なら resolver harness `:553`。final PATH literal も変える形なら extractor `:497` が先に error。test 内の狭い PATH mutant は `:583-586`。 |
| M8 | 殺す: `:307` → forbidden shim 判定 `:298-303`。 |
| M9 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M10 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M11 | 殺す: 置換形は `:307` → `:271-273`。追加形は `:288-289`。 |
| M12 | 殺す: `:465` の token 化 submitter 検査。 |
| M13 | 殺す: `test_p3_s4_loop_job_contract.py:666-671`、`test_hooks.py:3453`、さらに `check_docs.py:4432-4438,4781-4785`。多層赤。 |
| M14 | 殺す: 順序 `test_p3_s4_loop_job_contract.py:331-332` と hostname marker `:650`。二重赤。 |
| M15 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |
| M16 | 殺す: `:307` → `:271-273` と `:408`。二重赤。 |

登録済みの exact M1〜M16 に殺せないものはありません。ただし、M7 は適用形で赤理由が変わり、M2等は単一理由条件を満たしません。

## 判定

NO-GO。

最小編集集合は次のとおりです。

- `test_p3_s4_loop_job_contract.py` に、bnode stub で worktree gate まで到達する拒否 harness と、`qstat_jobid=${PBS_JOBID#0:}` の load-bearing mutant testを追加する。
- 順序 marker を executable surface と期待出現数へ束縛し、dead comment の前置複製を拒否する変異を追加する。
- line 408 の前提が外部 mutation 時の二重赤を作らない構成へ直し、M5 の実際の mutant source を検査する。
- `README.md:342` を実在する `s4-adjudication.md` へ直す。
- 修正後、既存 focus 集合に加えて acceptance ledger coverage node を確認する。ledger 更新は90% gateが赤の場合だけ必要。

登録簿は canonical 位置・field 順・class 閉集合を満たし、registry と `test_hooks.py:2590,2745-2749` の値も一致します。README の宣言行・タグ付き qsub 行・`-o/-e`、runbook 投影行も機械投影上は同期しています。qsub helper は A1 原本と等価で、heredoc 本文と comment を除外し、`qstat -f` を許可します。env tag 検査も `p3_s4_loop` と `site_policy` の実 importです。

author の実走主張は `attempt-0001.events.jsonl:84,90` で裏取りでき、2走とも実際に40 nodeを実行して rc=1、39 passed / 1 failedでした。docs 統合後の既存 `focus2.log:35` は対象5 file合計1120 passed / 4 skipped、`check_docs1.log:1` は違反なしです。本レビュー自身は pytest を実行していません。

## 総括

最大の欠陥は、worktree 拒否本体を消しても contract test が赤にならず、禁止 REPO_ROOT が受理集合へ入ることです。
順序検査も raw `source.index` のため、dead fragment の前置複製で欺けます。
親は fix 前に worktree gate の実到達 harnessと qstat job-ID 正規化の exact 束縛を必ず確認してください。
登録簿・golden・機械対象 docs の同期自体は成立しています。