結論は **NO-GO** です。親案と段 2 案の双方に生きた防壁の削除があり、「削除候補が一致しない」問題の答えは **両方とも誤り**です。blocker は 7 件あります。

## 所見

### blocker 1 — `DW-S02` / `DW-S03` / `DW-S05-A` の stage gate は自己申告で迂回でき、現行裁定にも反する

段 2 案は `args.stage`・`args.reasoning`・`args.sandbox` の組だけを検査しますが、実作業が plan か author かという意味は prompt にあり、独立した成果物 field にはありません。[s2b-plan.md:213](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/s2b-plan.md:213)、[operations.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/dev-wave/operations.md:77)

具体的には、plan の prompt を `--stage author --reasoning high --sandbox workspace-write` として渡せば、提案 gate は有効な author tuple として静的に通ります。つまり機械化できるのは「自己申告 stage と引数の整合」だけで、「plan を read-only/max で実行する」義務ではありません。

さらに `DW-S02/S03` の prose pin 解除経路は D223 が三段階で限定しており、A/B は恒久見送りです。[decisions.md:10486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/decisions.md:10486)、[phase3.md:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/phase3.md:668)。D266 も S02/S03 の pin 維持と、S05-A の pin を意図的に追加しないことを再確認しています。[decisions.md:12259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/decisions.md:12259)、[decisions.md:12288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/decisions.md:12288)

したがって brief の P2 は過大です。新 gate を置くだけでは既存の解除裁定を代替できません。

### blocker 2 — `DW-M04` の機械代替は公式 harness にしか効かず、独自 harness が無防備になる

公式実装は累積 source を使い、anchor 数が 1 でなければ停止し、空 diff も拒否しています。[mutation_harness.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/mutation_harness.py:803)。負例も、二段目が一段目の出力を使うことと、anchor 0/2 件の拒否まで assert しています。[test_mutation_harness.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_mutation_harness.py:238)、[test_mutation_harness.py:755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_mutation_harness.py:755)

しかし契約は独自 harness も許可しています。[mutation.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/dev-wave/mutation.md:30)。削除後は、独自 harness が各置換を毎回 `originals[rel]` から適用しても公式コードもテストも発火しません。これは F33 で実際に偽 SURVIVED を出した入力そのものです。[failures.md:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/failures.md:829)

従って公式経路の機械代替は実在しますが、義務全体の代替ではありません。段 2 の 201 bytes 削除案は blocker です。[s2b-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/s2b-plan.md:184)

### blocker 3 — `DW-M06` は timeout 後の継続を殺す負例がない

実装は timeout を `TIMEOUT` として記録し、pending mutation の loop を継続します。[mutation_harness.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/mutation_harness.py:1404)、[mutation_harness.py:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/mutation_harness.py:2355)。しかしテストは timeout 変異が 1 件だけで、記録と復元しか assert していません。[test_mutation_harness.py:792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_mutation_harness.py:792)

例えば record 追加後に `if status == "TIMEOUT": break` を入れても、このテストは通り、後続変異は実行されません。「harness 全体を落とさない」の継続義務が未固定です。独自 harness の差集合も `DW-M04` と同様に残ります。F32 は timeout 隔離を恒久対応としており、発火履歴もあります。[failures.md:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/failures.md:752)

従って 139 bytes 削除案は blocker です。[s2b-plan.md:191](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/s2b-plan.md:191)

### blocker 4 — `DW-O23` の機械実装は実在するが、「発火実績なし」が偽

lock 内再照合、`--ff-only`、同じ lock 内 fold、no-op、fold 失敗時の非 landed 化は実装されています。[dev_wave_land.py:1273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_wave_land.py:1273)、[dev_wave_land.py:1931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_wave_land.py:1931)。負例も lock 保持、0 fragment、fold failure、残留 fragment、ff-only 面まで具体的に assert しています。[test_dev_wave_land.py:2212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_land.py:2212)、[test_dev_wave_land.py:2283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_land.py:2283)、[test_dev_wave_land.py:2838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_land.py:2838)

ただし D128 は、直近 40 merge 中 25 件の採番衝突、反実仮想 49 file-instance を根拠に、`ff-only` 成功後に「同じ協調 lock を保持したまま」fold することを逐語決定しています。[decisions.md:6277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/decisions.md:6277)。以前の予算監査でも同じ移管は非推奨と裁定されています。[worklog-phase3-0809-332-333.md:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/archive/worklog-phase3-0809-332-333.md:455)

段 2 自身が repo 全体検索をしていないと明記したまま、A 削除へ昇格したのが誤りです。[s2b-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/s2b-plan.md:5)。機械化後事故が見つからないことは、「発火実績なし」の代替ではありません。333 bytes 削除案は blocker です。

### blocker 5 — 親 P-b の `pgrep` 段落は pid-file に supersede されていない

`dev_wave_wait.py` の pid 経路は実在し、PID 生存、必須成果物、PID source 排他、pattern CLI 不在を負例で固定しています。[test_dev_wave_wait.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_wait.py:541)、[test_dev_wave_wait.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_wait.py:600)、[test_dev_wave_wait.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_dev_wave_wait.py:627)

しかしこれは当該 tool を使う経路だけです。`DW-M05` は独自 harness を許し、`pgrep` を使う場合の防壁を明示的に残しています。[mutation.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/dev-wave/mutation.md:30)。先行棚卸しも、この段落を「親の待機規律であり tool の射程外」と確定しています。[T291 README:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/output/insights/2026-08-01_t291-devwave-mechanization/README.md:20)

さらに F32 には 2026-08-10 の汎用待ち手で自己一致が再発した記録があります。[failures.md:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/failures.md:806)。親 P-b の根拠は範囲のすり替えであり、blocker です。[parent-inventory.md:44](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/parent-inventory.md:44)

### blocker 6 — 親 P-a は下流 guard を誤った層の argparse guard と数え、負例もない

`dev_wave_codex.py` の非空検査は `job_id is None` の枝だけです。[dev_wave_codex.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_wave_codex.py:149)。明示 `--job-id` と `--dry-run` の組では prompt を読まず、生成 argv を出して rc=0 の経路へ進みます。[dev_wave_codex.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_wave_codex.py:250)

実 launch は下流の `codex_worker_launch.py` が spawn 前に非空 UTF-8 regular file を要求するため、現時点では空 prompt を起動しません。[codex_worker_launch.py:1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/codex_worker_launch.py:1869)、[codex_worker_launch.py:1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/codex_worker_launch.py:1412)。ただしテスト fixture は常に非空 prompt を作るだけで、空 prompt により rc≠0 になる負例は見つかりませんでした。[test_codex_worker_launch.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/orchestrator/tests/test_codex_worker_launch.py:981)

F23 由来の防壁を削るには、少なくとも canonical 実 launch と明示 job-id 経路の負例が必要です。[failures.md:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/failures.md:345)。現状の 34 bytes 削除は blocker です。

### blocker 7 — 親 P-c/P-d の同時削除は reference 読取失敗時の bootstrap 防壁を消す

入口の読み込み契約は、参照先が不在・読取不能・非一意なら、その場で fail-closed 停止することを入口自身に保持しています。[dev-wave.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/.claude/commands/dev-wave.md:19)。`DW-STOP` は同じ内容を持ちますが、`core.md` 自身が読めない場合には自分の読取失敗を止められません。[core.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/docs/dev-wave/core.md:20)

従って P-c の削除は循環した保証になります。P-d は P-c を残すなら単独では意味重複として削除可能ですが、親案どおり両方消すと入口側の「参照不整合を迂回しない」文も同時に失われます。[parent-inventory.md:45](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/parent-inventory.md:45)

### real — 「機械権威は 3 行」は launch receipt 限定なら正しいが、全機械防壁の数ではない

`launch_authority.py` は確かに O01・S06-A・S06-C の三つだけを抽出し、可視 top-level 行を regex `fullmatch` し、認識済み次 H2 までの節全体を hash します。[launch_authority.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_waves/launch_authority.py:21)、[launch_authority.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_waves/launch_authority.py:253)、[launch_authority.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/dev_waves/launch_authority.py:369)

一方、`check_docs.py` は O01 の route・waiter 行と S02/S03 の reasoning も exact pin しています。[check_docs.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/check_docs.py:293)、[check_docs.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/check_docs.py:311)、[check_docs.py:4035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/check_docs.py:4035)。従って「receipt 権威は 3 行」は正しいものの、「機械的に守られた行は 3 行」への一般化は real な誤りです。

なお段 2 案の O01 追記位置は model regex 行を変えず、S02/S03/S05-A は S06 節境界の外です。節 digest は変わりますが、提案順序どおり commit 後に snapshot を取り直せば regex 自体は壊れません。

### nit — authority 更新後の追加 child は新しい job-id も必要

manifest v2 は authority commit/digest を session ごとに持つため、同じ wave 内で新 digest の別 job を追加できます。[codex_worker_launch.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/codex_worker_launch.py:242)。ただし同一 `job_id` の retry は authority digest を含む identity 完全一致が必要です。[codex_worker_launch.py:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/codex_worker_launch.py:758)

したがって plan の「commit 後に追加 review/fix」は、新 prompt または明示的な新 job-id を要求すると明記すべきです。[s2b-plan.md:330](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/s2b-plan.md:330)

## 反証されなかった点

- L0=9,500、L1=10,624、L1.5=9,564、L2 最大 O09=997 は静的 probe で再計算し、brief の値と一致しました。[brief.md:19](/work/1/SFC/tanab/dev-wave-jobs/t925-l15-budget/brief.md:19)
- preamble は L1 節を持つ core/mutation/operations が L1、workers が L1.5、L1.5 から L1 を差し引き、最後に `registered_pairs` と積を取る実装です。数え方に誤りはありません。[check_docs.py:3724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t925-l15-inventory/tools/check_docs.py:3724)
- `DW-M08`、`check_codex_output.py`、waiter、land の各引用位置も全て開き、段 2 が「部分代替」とした箇所はその範囲では正確でした。
- 段 2 の byte 算術自体は、削除を仮定すれば整合します。ただし原資となる削除が blocker のため、L1=221・L1.5=263 の余白は実現不能です。

検査は必須 3 成果物、dev-wave 4 文書全文、指定された launch authority 範囲と section helper、段 2 が挙げた全 `file:line`、対応する負例テストの assert、引用された F 項目だけを読みました。発火履歴は `docs/failures.md` 全文を読まず、repository 全体の意味検索で decisions・archive worklog・insights・runbook まで照合しました。

pytest、`check_docs.py`、provenance 監査はすべて **未実走**です。実行したのは read-only の byte probe と静的検索だけで、緑とは報告しません。

## 総括

**blocker あり。削除パッケージは採用不可です。**

- 危険で削除不可: `DW-O01` prompt 非空、`DW-M05` pgrep、入口 P-c、`DW-M04`、`DW-M06`、`DW-O23`、`DW-S02/S03/S05-A`。
- 条件付きで安全: 親 P-d は P-c を残す場合だけ単独削除可能。
- 安全と判断できる重複: 段 2 案の入口 `dev-wave.md:116-117` は、wave 開始時に必読の routing が `docs/skill-self-improvement.md:23-37` に残るため削除可能です。
- 全節削除で安全と確認できたものはありません。

したがって、親案と段 2 案を併合してはならず、現状で安全に回収できるのは L0 の重複文だけです。