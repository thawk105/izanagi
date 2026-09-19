単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md (段 4 裁定と plan v2、§3 変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/brief.md (段 1 brief と前提実測。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/rulings-verbatim.md (D2148 項 12・D1877・D1936 項 43・F945・DW-S05 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/author-u1.patch (レビュー対象の差分 = commit 4208bf332 の全内容、base 8fd1eecf9。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/author-u1-out.md (実装子の最終報告。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py (差分適用後の production probe 全体。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py の 1〜100 行と 605〜650 行 (fixture と負例。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/orchestrator/tests/t1259_scan_bound.py と test_t1259_scan_bound.py (新規 2 file。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/orchestrator/tests/conftest.py の 660〜710 行と 2161〜2177 行 (real-repo memo work unit と接尾除去。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout (branch worktree-dev-wave-t2790-t1259-scan-timeout、HEAD 4208bf332 = 差分は commit 済み) である。read-only。

# 依頼 — 段 6 敵対レビュー A: 正しさ境界・整合・実効性

親が実行済みの検査: 計算ノードでの焦点走 `test_t1259_scan_bound.py` + `test_t1259_qsub_env_delivery_probe.py` = 54 passed / 11.7 秒 (request 11285.nqsv)。
全史 provenance 監査 11635 件・新規違反なし。consumer/meta-test の焦点走 (`test_acceptance_schedule_order.py`、`test_plain_runner_coverage.py`、
`test_paper_story_a1_headline.py`、`test_real_repo_serialization.py`) は投入済み・結果未着。受入全走・変異走行・`check_docs.py` は未実施。
sandbox は read-only で pytest を走らせられないので静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 攻撃してほしいこと (プランを守らず検査する。親の brief と裁定自身も対象)
1. **production 不変の実効性**: `_run_git` / `_repo_is_detached` / `_repo_snapshot` の keyword 引数追加で、production の呼び出し
   (`observe()` 内 `before` / `after`、他に `_run_git` や `_repo_is_detached` を呼ぶ箇所があるか全列挙) の timeout が 30.0 のままか。
   `subprocess.run(..., timeout=git_timeout_seconds)` で `None` や負値が渡りうる経路はあるか。
2. **走査対象・例外型・返り値の不変性**: diff が argv 4 種・`GIT_OPTIONAL_LOCKS=0`・`check`・返り値 dict・`ProbeError` 条件を
   1 byte も変えていないか。`TimeoutExpired` を包まないという不変条件が helper でも成立するか。
3. **拒否能力**: 負例 `test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-…]` の検出経路が
   fixture 変更で弱まらないか。module fixture が `tracked_status` / `untracked_paths` を上書きして捨てている事実 (adjudication §3 注)
   のもとで、この wave が「拒否能力を維持した」と主張してよいか、主張の限界をどう書くべきか。
4. **新 test の妥当性**: spy が本物の `subprocess.run` へ委譲しているか (stub でないか、F649)。`test_fixture_snapshot_uses_local_candidate_bound`
   の `FIXTURE_GIT_TIMEOUT_SECONDS == 120.0` の literal pin は、採用値の判定 (段 6 実測後) と矛盾する固定化にならないか。
   `snapshot == production` の比較が tmp repo の `untracked_paths` を含む点で脆くないか。test 3 の代役が production を緩めていないか。
   新 file の自走 harness が `test_plain_runner_coverage.py` の `_self_runnable()` 条件を満たすか (該当 file を読んで判定条件を示せ)。
5. **変異事前登録 (§3) の kill 帰属**: M1 (`FIXTURE_GIT_TIMEOUT_SECONDS = 0.0`) と M2 (`fixture_repo_snapshot` が固定 dict) を、
   `test_t1259_scan_bound.py` だけを runner 対象にしたとき、期待 KILLED node 集合が「test 2 のみ」で完全一致するか
   (test 1 / test 3 は生き残るか)。赤理由が 1 つに絞れるか (DW-M01 / M03)。等価変異の危険 (走査を一部省く変異は fixture 側では検出不能) を
   記録の限界としてどう書くべきか。
6. **consumer への波及**: 新 nodeid 3 本が `acceptance_duration_ledger.json` の G5 (90% 被覆) を割るか、conftest の real-repo inventory・
   `test_real_repo_serialization.py` の golden・`test_hooks.py` の静的分類・`REAL_REPO_PROCESS_MEMO_NODES` に触れるべき箇所が残っていないか。
   新 helper module `orchestrator/tests/t1259_scan_bound.py` が pytest の collection・他 meta-test (module 一覧を数えるもの等) に当たるか。
7. **D2148 項 12 との整合**: 「production の timeout まで一律に変えない」「走査対象・拒否能力を維持」「120 秒は候補値で確定値にしない」に
   反する箇所・表現はないか。commit message の主張と実体の食い違いはあるか。

## 出力形式 (H2 見出し、最後の `## 総括` は必須)
- `## 所見` — 番号付き。各所見に `real | refuted | 不明`、`must-fix | should | nit`、根拠の file:line、放置時に成果物 (受入の受理集合・
  fixture の fail-closed・F945 台帳の主張) がどう変わるかを 1 行 (DW-G05)。
- `## 通る正例` — 各 must-fix に、直した後に通るべき正例を 1 つ。
- `## 主張の限界として記録すべき文` — insight / F945 追補に書くべき限界の文案 (箇条書き)。
- `## 総括` (5 行以内、GO / NO-GO とその条件)
