静的検査のみ。pytest・実測・Web検索は行っていない。親 brief の P1/P3 は、そのまま採用できない。

### B-01 — blocker

主張: 親 brief の時間計測の説明が、現行実装と食い違う。

根拠:

- `AttemptState.started_ns` は `Popen` 直前ではなく、起動前 hook 検証より前に設定される。[`tools/codex_worker_launch.py:1347`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1347)、[`tools/codex_worker_launch.py:1403`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1403)
- `evidence_deadline_ns` と attempt の `wall_clock_s` は同じ `state.started_ns` を起点にする。[`tools/codex_worker_launch.py:1427`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1427)、[`tools/codex_worker_launch.py:1540`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1540)
- 一方、receipt の `actuals.wall_clock_s` は `_sum_attempts` の値を job 起点からの経過時間で上書きしている。[`tools/codex_worker_launch.py:1702`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1702)、[`tools/codex_worker_launch.py:1703`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1703)
- したがって brief の「attempt は Popen 後だけ」「job clock は receipt に無い」という説明は、[`brief.md:51`]( /work/1/SFC/tanab/dev-wave-jobs/t1005-acceptance-flake-attribution/brief.md:51)、[`brief.md:73`]( /work/1/SFC/tanab/dev-wave-jobs/t1005-acceptance-flake-attribution/brief.md:73) の時点で誤っている。

規律 3、親の P1、O1/O2/O3 に該当する。M1 と M2 は共通の attempt 起点を持つため、「独立した 3 原因」と断定できない。

推奨: まず brief の機序を訂正する。O1 は重複計装ではなく、既存の曖昧な `actuals.wall_clock_s` を明示名にし、起動前・attempt・evidence の各時計を分離する補完として扱う。

### B-02 — blocker

主張: O2 の一括した予算引き上げは、production argv を変えなくても、テストが受け入れる実装集合を広げる。

根拠:

- テスト fixture は `max_wall=3`、evidence `1.0`、termination `0.05` を共通注入している。[`test_codex_worker_launch.py:961`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:961)、[`test_codex_worker_launch.py:1038`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:1038)
- 受理条件は limit、evidence、metering、exit code、residual、termination の全 conjunct である。[`tools/codex_worker_launch.py:1256`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1256)
- production の wall 既定は `3600` だが、これは test suite の受理条件が変わらないことを意味しない。[`dev_wave_codex.py:20`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/dev_wave_codex.py:20)

3 秒から 6 秒へ上げれば、3〜6 秒の本物の劣化をテストが緑として通す。F57 の `-n 8` 緑も発火率低下に過ぎず、恒久保証ではない。[`docs/failures.md:1877`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/docs/failures.md:1877)

規律 2、O2 に該当する。

推奨: 一括変更は却下。条件付きで採用するなら、次を分離する。

- 環境耐性用の relaxed integration fixture と、wall/evidence 境界を検査する固定 fixture を分ける。
- 境界テストは旧値を明示指定し、時計注入で deterministic にする。
- termination grace は起動時間分布から決めず、終了処理の分布から別に決める。
- 「正常制御が新予算内」だけでなく、予算超過が必ず reject される負の対照を残す。

### B-03 — blocker

主張: O3 は production の受理集合を変える。

根拠:

- 現在は import 時刻を `launcher_started_ns` として保持している。[`tools/codex_worker_launch.py:35`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:35)、[`tools/codex_worker_launch.py:3143`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:3143)
- `_run_supervised` は preflight 後、attempt 前にその時計で上限を判定する。[`tools/codex_worker_launch.py:2005`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:2005)
- 現行テストも version preflight の遅延を wall-clock に含める契約を明示している。[`test_codex_worker_launch.py:2705`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:2705)

起点を後ろへ動かすと、旧来 reject される「preflight に時間を使い切った job」が受理されうる。3600 秒は有限値であり、preflight 全体に対する上限・不変条件ではない。「大きいから安全」は恒真ゲートである。

規律 2、O3 に該当する。

推奨: O3 単独は却下。採用するなら、起動全体の外側に旧来の hard cap を残し、別名の work clock を追加する二重時計に限る。ただしそれでは今回の false red を受理集合を変えずに消せないため、裁定が必要。

### B-04 — blocker

主張: O4 が観測失敗を termination verification の成功側へ移すなら、残留 process の見逃し穴になる。

根拠:

- `_group_member_count` の `None` は観測不能を意味する。[`tools/codex_worker_launch.py:1137`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1137)
- 現在は `None` を `termination_verified=False` とし、受理にも `residual == 0` を要求する。[`tools/codex_worker_launch.py:1204`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1204)、[`tools/codex_worker_launch.py:1263`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1263)
- 既存テストは unknown residual を verified にしてはならないと固定している。[`test_codex_worker_launch.py:2590`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:2590)
- SIGTERM 無視の同一 group 子については、KILL 後に residual 0 と子 PID 消滅を確認している。[`test_codex_worker_launch.py:2498`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:2498)
- setsid 脱出テストが守るのは「全 descendant を contained と主張しない」性質であり、receipt は `escaped_process_containment=not_attempted` と明記する。[`test_codex_worker_launch.py:4079`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:4079)

規律 2・3、O4 に該当する。

推奨: O4 の「観測理由を別 field に出す」部分だけ条件付き推奨。`unknown` を残留なしとして受理してはならず、`termination_verified=False` と受理条件は維持する。O4 の危険な解釈は却下。

### B-05 — must-fix

主張: O5 は恒久対応ではなく、発火率を下げて同じ欠陥を隠す運用緩和である。

根拠:

- F57 は単独走・低負荷・子なしでも非決定赤が出ることを記録している。[`docs/failures.md:1860`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/docs/failures.md:1860)
- 48 worker から `-n 8` に下げると緑になった事実も、欠陥の除去ではない。[`docs/failures.md:1877`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/docs/failures.md:1877)
- F57 はテスト再試行で緑にすることを規律 2 違反として明示的に禁止している。[`docs/failures.md:1739`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/docs/failures.md:1739)

規律 2、O5 に該当する。

推奨: 恒久対応としては却下。暫定の資源保全策として使う場合も、`-n 8` の緑を修正済み・受入済みとは数えず、production の並行 launcher 局面を未解決として返す。

### B-06 — must-fix

主張: O1 だけでは赤も非決定性も直らない。

根拠:

- 診断側は既に予算と receipt actuals を表示している。[`test_codex_worker_launch.py:372`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:372)
- receipt には limits と job 相当の actual wall が既にある。[`tools/codex_worker_launch.py:1748`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1748)
- それでも受理条件や process scheduling は変わらない。[`tools/codex_worker_launch.py:1256`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1256)

O1 を最優先にする論拠は、規律 3 に従い誤帰属を止め、O2/O3/O4 の選択を証拠に束縛できることだけである。修正完了の根拠にはならない。

規律 3、O1 に該当する。

推奨: 条件付き推奨。追加するなら `job_wall_clock_s` の別名だけでなく、receipt に exact な evidence/termination grace と `/proc` 観測理由を束縛する。現在の `limits_assertion=self_asserted` のままなら、計装値を外部検証済みと扱ってはならない。[`tools/codex_worker_launch.py:2792`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:2792)

### B-07 — must-fix

主張: 第 6 案「仮想時計 + 実 process テストの分離」は成立するが、現存 seam だけでは不十分。

根拠:

- `_monotonic_ns` は明示的な seam である。[`tools/codex_worker_launch.py:30`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:30)
- 既存テストも preflight、receipt staging、audit の時計を差し替えている。[`test_codex_worker_launch.py:2244`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:2244)、[`test_codex_worker_launch.py:2796`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/orchestrator/tests/test_codex_worker_launch.py:2796)
- しかし cleanup の期限は直接 `time.monotonic()`、待機は直接 `time.sleep()` を使う。[`tools/codex_worker_launch.py:1192`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1192)、[`tools/codex_worker_launch.py:1204`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/tools/codex_worker_launch.py:1204)

従って `_monotonic_ns` だけを monkeypatch しても、実 child、`/proc`、signal、sleep の揺らぎは残る。

規律 2・3、新規 O6 に該当する。

推奨: 条件付き推奨。wall/evidence/receipt の政策テストは fake process・fake clock・fake observer で deterministic にし、setsid・SIGTERM・`/proc` の少数 integration test は実 process のまま残す。全テストを仮想化して process containment の性質を失わせてはならない。

### B-08 — must-fix

主張: 「本 wave では機構を変更せず裁定へ返す」という scope 自体は正しいが、未解決のまま緑や land を許してよいという意味ではない。

根拠:

- brief は実装差分ゼロを明示している。[`brief.md:5`]( /work/1/SFC/tanab/dev-wave-jobs/t1005-acceptance-flake-attribution/brief.md:5)
- 放置時の land 可否・変異判定の非決定性も既に成果物影響として記録されている。[`brief.md:89`]( /work/1/SFC/tanab/dev-wave-jobs/t1005-acceptance-flake-attribution/brief.md:89)
- `DW-STOP` は検査赤・裁定待ち・前提を覆す新事実で fail-closed に停止させる。[`docs/dev-wave/core.md:20`]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1005-acceptance-flake-attribution/docs/dev-wave/core.md:20)

規律 2、3、scope、O1〜O6 に該当する。

推奨: 今 wave ではコードを直さず、P1/P3 を未確定へ戻し、全走の赤を緑として数えず、変異 MISMATCH を成功扱いせず、裁定 package で停止するのが最小の安全策。恒久対応は新しい実装 wave へ送る。

## 総括

- O1 — 条件付き推奨: 診断基盤としてのみ優先し、修正完了とは扱わない。
- O2 — 条件付き推奨: 固定された境界テストと relaxed integration を分離する場合のみ。
- O3 — 却下: 起点移動は production 受理集合を変える。
- O4 — 却下: unknown を verification 成功側へ移す案は residual 見逃しになる。
- O5 — 却下: 恒久対応ではなく発火率の隠蔽である。
- O6 — 条件付き推奨: 仮想時計テストと実 process containment テストを分離する。