単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。§2.4 と §2.5 が本単位 (A3) の実装仕様、§3 の M13 / M14 / M18 が本単位の変異。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s5-author-A1.md` — **A1 (core module) の報告。§「台帳 schema と handshake の確定形」と §「波及」の「job body (A3) が新 CLI に渡すべき引数」を正とする**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s2-plan.md` §9 (job mode と launcher)、`.../codex/s3-consult-B.md` B4 / B5 / B9 (TJ の更新箇所・launcher の `-v` 明示・pin 閉包の追加面) — 参考 (裁定が上書き)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md`、`.../brief-addendum-1.md` — 背景
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a3/tools/pegasus/p3_s4_loop_pegasus.sh` — **編集対象** (621 行、全文を読む)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a3/orchestrator/tests/test_p3_s4_loop_job_contract.py` — **編集対象** (1934 行、全文を読む。特に `_assert_static_job_contract` :176–474、`STOCK_PINS`、変異 :635–816 / :698–704 / :939–951、stage order :548–585、実 shell helper :1178–1360、driver 呼出し回数 :1866–1915、`__main__` :1927–1934)
- 読むだけ (触らない): `.../orchestrator/campaign/b5_generator_contrast.py` (A1 が作った CLI: `run-series` / `run-block-stock` の引数)、`.../tools/pegasus/README.md:331–430` (job body の env 契約と qsub 例)、`.../tools/pegasus/admission_registry.json` (job body :112 と login 側 tool の class の先例)、`.../tools/pegasus/dispatch_compute.py:4010–4030` (qsub argv の先例)、`.../tools/pegasus/fetch_third_party.py` (login 側 tool の CLI の型)、`.../orchestrator/tests/test_pegasus_tools.py:530–570` (SH の逐語 pin)、`.../orchestrator/tests/test_hooks.py` (job body / tool の分類 test を `p3_s4_loop_pegasus` で grep)、`.../orchestrator/tests/test_plain_runner_coverage.py`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/qsub-submit-pair.sh` (親の投入 script の現物、`-v` の形)。

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a3` とする。上記以外も repo 内を読んでよい。

## この単位 (A3) の仕事

裁定 §2.4 を実装し、M13 / M14 / M18 が**独立した根拠**で kill される test を書く。編集するのは次の 4 file だけ:

1. `tools/pegasus/p3_s4_loop_pegasus.sh` — B-5 mode (`IZANAGI_S4_B5_MODE` ∈ {series, block-stock}、`_ARM` / `_WORKLOAD` / `_SERIES` / `_BLOCK` / `_LEDGER_ROOT`) の受理と拒否 (rc=2、repository path 解決より前)、K2 env の条件 (arm=llm で必須、他 arm と block-stock で禁止)、`IZANAGI_S4_PROPOSAL_PATH` / `IZANAGI_S4_FIXTURE_VALUE` / `IZANAGI_S4_STOCK_CONTROL=1` との併用拒否、`:95–96` の proposal-path 必須条件の B-5 llm だけの例外、prebuild receipt の後・既存 3 分岐の**前**に B-5 分岐 1 箇所 (`"$PY" -B -m orchestrator.campaign.b5_generator_contrast <subcommand> ... || b5_rc=$?; exit "$b5_rc"`)。
2. `tools/pegasus/b5_contrast_launch.py` — **新設** (login 側 launcher)。`validate_submit_tree(repo, expected_head)` (HEAD full OID 一致、tracked clean (submodule 除外)、CCBench HEAD == `p3_s4_loop.PIN`、CCBench tracked clean、`.claude/worktrees/` / `.codex/worktrees/` 配下でない)、`pilot_jobs(...)` (4 job 固定: random / sweep-matched / llm / block-stock、workload 1 つ、series 1、block 1)、`build_job_environment(spec, tree)` (必要 env の dict)、`qsub_argv(spec, tree)` (`["qsub", "-v", "K=V,...", "-l", "elapstim_req=08:00:00" (block-stock は 03:00:00), "-o", <evidence>/job.stdout, "-e", <evidence>/job.stderr, "tools/pegasus/p3_s4_loop_pegasus.sh"]`、`-q` / `-A` / `-b` は script の指示行に任せる)、`PILOT_LOGICAL_SESSION_CAP` の検査 (`3*(1+10+5)+5 = 53 <= 60`、B / N_eval / block-stock 定数は `b5_generator_contrast` から import)、`--dry-run` (最終 argv と env を印字し qsub も mkdir もしない)、`--submit` (evidence dir を `mkdir` してから `subprocess.run(argv, cwd=repo)`、attempt dir に他の file を置かない)。shell 文字列を評価しない (argv list)。
3. `orchestrator/tests/test_p3_s4_loop_job_contract.py` — B5 pins (required に追加)、stage order (B-5 env 判定 → K2 判定 → path 解決、prebuild → B-5 分岐 → 旧分岐)、B-5 呼出し 1 箇所 (旧 module 呼出し 3 は維持)、既存変異 (:698–704, :939–951) の保持・更新、新 shell test (4 mode 各 1 起動・非零 rc の trap 転記・旧経路不実行・不正 env (設定済み空値 / 不正値 / 一部だけ / PROPOSAL_PATH 併用 / STOCK_CONTROL=1 併用 / K2 欠落 (llm) / K2 指定 (random)) の rc=2 が repository path 解決より前)。
4. `orchestrator/tests/test_b5_contrast_launch.py` — **新設**。`__main__` harness (TJ :1927–1934 と同型)。tmp の fake submit-tree (git init + 固定 HEAD + `external/ccbench` の fake) で `validate_submit_tree` の正例 / 負例、`qsub_argv` の固定期待値 (4 job、walltime、`-v` の key 集合と値)、cap test (M18: 5 job や B=11 を組めない)、dry-run が subprocess を呼ばない (fake runner)。

必ず守る点:

1. **触らない file:** `orchestrator/campaign/**` (A1 / A2 の所有)、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_b5_generator_contrast*.py`、`orchestrator/tests/test_pegasus_tools.py`、`orchestrator/tests/test_hooks.py`、`orchestrator/tests/test_official_perf_closure.py`、`tools/pegasus/README.md`、`tools/pegasus/admission_registry.json` (登録は親が行う。あなたは登録 class の候補と理由を報告に書く)、`tools/pegasus/dispatch_compute.py`、`docs/**`、`hooks/**`、`.claude/**`、`.codex/**`、他のすべての file。新規 file は上記 2 つだけ。job dir へ書かない。
2. **絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` / `git rm` を実行しない。commit は親が行う。**
3. **既存 3 経路 (fixture / proposal / stock-control) の argv と rc は bytes 不変。** 既存 TJ test の期待値を変えない (変えてよいのは裁定 §2.4 が名指しした pin の追加・stage order への B-5 位置の追加・`k2-proposal-required` の条件を含む pin への更新と、それに対応する既存変異の同期だけ)。`#PBS -l elapstim_req=03:00:00` の pin は不変。
4. **B-5 mode の判定は `${IZANAGI_S4_B5_MODE-}` の**未設定だけ** off** (設定済み空値・他値は `refuse` rc=2)。B-5 mode の必須 env は全部非空を要求し、部分設定・空値は rc=2。`set -Eeuo pipefail`・EXIT trap・compute-result schema・python 解決・prebuild は不変。B-5 分岐は `"$PY" -B -m orchestrator.campaign.b5_generator_contrast` を 1 回だけ起動し、A1 の CLI (series: `run-series --arm A --workload W --series R --block B --ledger-root L --fetchcontent-prebuild-receipt "$prebuild_receipt" [--knowledge-manifest M --knowledge-classification C --knowledge-de-novo-claim N]`; block-stock: `run-block-stock --workload W --block B --ledger-root L --fetchcontent-prebuild-receipt "$prebuild_receipt"`) に渡す。A1 報告の CLI 名・引数名が本 prompt と違えば A1 報告を正とする。
5. **launcher の env:** job body の required env (`IZANAGI_S4_REPO_ROOT` / `_EXPECTED_HEAD` / `_EVIDENCE_ROOT` / `_THIRDPARTY_SOURCE_ROOT`) + B-5 env + (llm のみ) K2 env 4 つを `-v` に**明示列挙**する (環境の継承に頼らない)。値に `,` や空白を含む path は拒否 (NQSV の `-v` は `,` 区切り)。
6. **テストを甘くしない:** 実 shell (`bash`) で job body を stub 環境 (fake `qstat` / `hostname` / `PY`) で走らせる既存 helper (`_run_actual_job_body_through_driver` :1178–) を拡張して B-5 経路を実走し、driver の argv 履歴と rc を検査する。static 文字列検査だけで済ませない。期待値へ揮発 payload を焼き込まない。
7. **変異 (裁定 §3) の kill を単位内で:** M13 (B-5 mode で旧候補分岐へも落ちる) は実 shell test の driver 呼出し回数 = 1 で殺す。M14 (設定済み空値の拒否除去) は rc=2 test で殺す。M18 (cap 60 → 61 / 4 job → 5 job) は launcher の cap test で殺す。既存の TJ 変異 runner (static failure ちょうど 1 個) に B-5 pin の fragment / replacement を追加する。
8. 規模の目安: SH +60〜100 行、launcher 250〜400 行、TJ +250〜400 行、新 test 200〜350 行。
9. **実走:** `cd <repo root> && PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B orchestrator/tests/test_p3_s4_loop_job_contract.py`、同 `test_b5_contrast_launch.py`、`python3 -B -c "import sys,pytest; sys.exit(pytest.main(['orchestrator/tests/test_pegasus_tools.py','-q','-rf','-k','p3_s4_loop or job_body']))"`、`test_hooks.py` の job body 分類 (`-k p3_s4_loop`)。実走 nodeid・件数・結果を報告に列挙。走らないなら「実装済み・未実走」。
10. **報告に:** `tools/pegasus/README.md` §7 への差分案 (B-5 env 表・qsub 例・launcher の使い方、親が書く)、`admission_registry.json` の launcher 登録 class の候補 (既存 login 側 tool の先例と理由)、所有外への波及。新 test 名は ASCII。docs を書かない。報告は最終メッセージ本文。予算が尽きそうなら途中結論を出力形式どおり書いて終わる。
11. **現行の受理・拒否挙動を scope 前に明記:** 変更前の job body が `IZANAGI_S4_B5_MODE=series` (未知 env) をどう扱うか (無視して fixture 経路へ落ちる) を 1 行で書く。

## 出力形式

- 見出しはすべて `##`。節: `## 変更の要約`、`## 既定挙動不変の確認` (3 経路の argv・rc・既存 pin)、`## launcher の使い方` (dry-run 出力例 1 本、`-v` の key 一覧)、`## 新 test 一覧` (名前・根拠・殺す変異)、`## 実走結果`、`## 波及` (README 差分案・登録 class 候補・所有外)、`## 未了・懸念`、`## 総括`。
