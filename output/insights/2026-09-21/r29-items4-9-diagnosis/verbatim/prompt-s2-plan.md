単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (起草の前提。守らずに点検してよい): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/brief.md
- 裁定の控え: /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full29-verdicts.md (項 3・4・9)
- 相談 A の原文: /work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921c/artifacts/consult-a-out.md (項 1・2・4)
- 契約・裁定の逐語 (親が現行 docs から切り出した): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/verbatim/contract/ の D325.md、D289.md、D130-D131.md、D2194-item8.md、DW-O26-O27.md、DW-O18.md、DW-C00-C01-STOP.md
- 前回診断 (repo 内、worktree path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/output/insights/2026-09-21/focus-run-count-diagnosis/README.md (§4〜§7) と同 dir の verbatim/focus_runs_table.md、verbatim/changed_files.txt、verbatim/aggregate.txt、verbatim/timeline.txt
- 受入赤の生 log (項 9 の 2 例): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/acceptance-child-final-1.log、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/acceptance-child-final-1.log
- コード (worktree、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-r29-items4-9-diagnosis/ の tools/run_tests.py、tools/pegasus/dispatch_compute.py、orchestrator/campaign/site_policy.py、hooks/guard_bash.py、orchestrator/tests/test_ccbench_spawn_sites.py、docs/ai-provenance.md

## 前置き — この依頼の性質

自分たちの開発運用手順 (dev-wave) の診断である。実装はしない (repo の runner・dispatcher・test・docs を変えない、新しい harness・目録基盤・gate・台帳も作らない)。
セキュリティでも攻撃でもなく、外部入力も扱わない。書込可能 tmp が無いので静的検査でよい — テスト・計算ノード job の実測は親が行う。git の読み取り (`git show`、`git log`、`git grep`) は使ってよい。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

背景: ユーザーは T-2832 (i) (D325 の字面 = 変更 test file ごとに「別 process の単独走」を受入前に 1 度) に運用を戻すと裁定し、実現手段は未定。
候補の 1 つ R2 = 「1 job 内で複数の pytest invocation (集合 process + 変更 test file の単独 process、held は env 分離)」。
ユーザーは R2 について (a) 既存走の置換で満たせない残件数、(b) 最小改修の範囲、(c) 同条件での効果、を測って再提示せよと裁定した。
また項 9 は「焦点走の探索から漏れた exact 目録 test の既知 2 例 (T-2737、T-2797) を既存の探索で拾う局所策と追加実行時間だけ」を調べる。

# 依頼 — file:line 粒度の起草 (plan)

次を起草せよ。各項に file:line と根拠 (逐語の引用は短く) を付け、推測と実測・コード根拠を分けて書け。

1. **(b) R2 の最小改修範囲。** `tools/run_tests.py` の `--force-dispatch` 経路は 1 起動 = 1 pytest invocation である (確認せよ)。
   1 job の中で「集合 invocation 1 + 単独 invocation k + (任意) env を分けた invocation」を走らせるための **最小** 改修を、
   表現 (argv / 入力 file の形)、login 側の受理・dispatch、計算ノード側の実行 (逐次 loop、各 invocation の cwd・env・nproc)、
   rc の集約、結果記録 (`_RecordingSession`・`_suite_identity`・task_run)、dispatch_compute の task 契約 (`TASKS["tests"]` の argv_policy / env_allowlist、D131 の閉集合)、
   held opt-in (`IZANAGI_RUN_GROWTH_HELD_TESTS` と token の検査) の各層で列挙せよ。触る関数と行、追随が必要な既存 test file (名前で grep、件数)、
   docs の exact pin (`tools/check_docs.py` や pin test が run_tests の使い方を literal で持つか) を挙げ、改修規模 (関数数・概算行数) を見積もれ。
   「単なる flag 追加ではない」(相談 A) の中身を具体化すること。受理集合 (受入形の判定 `_is_acceptance_run`、shard mode) を変えずに済む境界も示せ。
2. **改修なしの既存経路の実在確認。** 次の 2 経路が R2 と同じこと (1 job 内の複数 invocation、または dispatch 無しの単独 process) を今の道具で実現できるかを判定せよ。
   - (G) `python3 tools/pegasus/dispatch_compute.py --task generic -- bash -c '<run_tests.py を複数回>'`: generic の argv_policy (`generic-v1`)、`env_mode=clean` で落ちる env、
     job script の環境正規化 (D130 決定 (4) の PATH 問題が generic でも起きるか)、計算ノード上で `run_tests.py` が site を compute と判定して再 dispatch しないか
     (`site_policy.current_site` が clean env で何を見るか)、pytest-xdist の可否、`hooks/guard_bash.py` がこの Bash command を許すか、
     `docs/ai-provenance.md` の実装面の定義に照らして argv の `bash -c` 文字列が実装面に当たるか (file を作らない command line)、
     失うもの (task_run 記録、receipt、非受入警告、log 上の `[Pegasus dispatch]` 行や NQSV footer) を file:line で。
   - (L) login の bounded local: `--force-dispatch` 無しで単独 file を走らせたときの login admission (`_evaluate_login_admission`、`grant_budget`) の分岐と、dispatch へ退避する条件。
     D325 の理由欄「Pegasus では実行を伴う焦点走は必ず計算ノードへ dispatch される」が現行コードで成り立つかを判定せよ。
3. **(c) 同条件の実測 plan (親が走らせる)。** brief (P3)(P4) の腕 C (generic 1 job = t2797 の焦点集合 21 file + 変更 test 7 file の単独 7 invocation) と
   腕 S (`--force-dispatch` の集合 1 job + 単独 7 job を直列) を、同 SHA の別 worktree から同時刻に始める具体 command を起草せよ。
   t2797 の焦点集合 21 file は前回診断の verbatim から特定し (無ければ特定不能と書け)、7 file は changed_files.txt の t2797 行。
   各 job の 4 区間 (投入前 / ノード開始前の待ち / RUN / collection) と、腕 C 内の invocation 別所要 (bash の `date` 行など) をどう log から取るか、
   同一 worktree の dispatch 直列 (DW-C00 の orphan hold、rc=16) の機序が code のどこにあり、別 worktree なら並行が許されるか (D289)、
   2 本目の worktree の作成・submodule 初期化・lock・撤去の要件、を file:line で。腕の比較が「同条件」と言える範囲と言えない範囲 (node の違い、warm cache、腕どうしの資源競合) も書け。
4. **(a) 残件数の表の起草。** 前回診断の標本 12 wave (verbatim) で、wave ごとに k = 変更 test file 数、s = 既に単独走で確認済みの file 数、
   c = brief (P2) の定義で「単独走へ置き換えられる既存走」の本数、残件 = max(0, k − s − c) を表にせよ。c の各本は run 名で挙げ、置き換えると失う契約条件が無いことを根拠付きで。
   (P2) の定義そのものが D325 (「既に回す走行のうち 1 本を単独走に」) の読みとして妥当かも判定せよ。
5. **項 9: 2 例は既存の探索で拾えるか。** (i) 受入赤 5 node がすべて `orchestrator/tests/test_ccbench_spawn_sites.py` の node であることを log で確認。
   (ii) DW-O26 現行の consumer 探索 (変更 production の module 名で `orchestrator/tests/` を grep) が、赤の直前の tip で同 file を引けたか
   (T-2737 = 変更 production `tools/pegasus/run_ss2pl_lock_study.py` と `patches/ss2pl-lock-protocol-study.patch`、fix 前 commit は `134ea235c` の親。
   T-2797 = `orchestrator/campaign/b5_generator_contrast.py` ほか、fix 前 commit は `517fd5451` の親) を git grep で判定。
   (iii) T-2820 (D2194 項 8 = production を変えた wave は inventory 群に同 file を含める) が両 wave で発火するか (両 wave が production を変えたか)。
   (iv) 別の既存探索 (production directory を glob / rglob / iterdir / os.walk で列挙する test を拾う、memory の運用) なら何 file が選ばれ、同 file を含むか (件数と file 名)。
   (v) 追加実行時間の測り方 (同 file の単独走、t2797 集合から同 file を抜いた走と入れた走の差) の plan。所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` の同 file の値 (47 node、直列 224.5 秒、最長 node 100.0 秒) が丸め値・推定値でないかも確かめよ。
6. **過剰・削除。** brief の scope を超える作業 (新 harness、一般化、gate、台帳) を plan に入れていないか自己点検し、実測を減らせる所 (既存 log で足りる値) があれば挙げよ。

## 出力形式
- `## 1 (b) 最小改修範囲` / `## 2 既存経路 G・L` / `## 3 (c) 実測 plan` / `## 4 (a) 残件数表` / `## 5 項 9` / `## 6 過剰・削除` / `## brief への指摘` (brief の誤り・前提の覆り) / `## 総括` (必須)。
