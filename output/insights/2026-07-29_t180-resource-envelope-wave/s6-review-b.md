pytest・変異本走は実施していない。以下は静的検査と、T-179 実 rollout に対する read-only ledger 実走の結果である。既知の manifest 一意制約は所見から除外した。

## 所見

### [must-fix] post-spawn 失敗で process と receipt が消える

検出できないもの: spawn 後の rollout 読取例外、binary 変化、manifest append 失敗時に、Codex process が残存し、費消済み session が receipt から欠落する経路。

`_attempt_loop` の `finally` は stdout/stderr を閉じるだけで process を終了しない。さらに既存 manifest の wave_id は preflight では照合せず、worker 完走後の append で初めて拒否する。外側は rc=2 を返すだけで launcher-error receipt を作らない。[tools/codex_worker_launch.py:949](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:949)、[同:1292](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1292)、[同:1344](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1344)、[同:1910](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1910)。テストは foreign wave で receipt 不在を正解として固定している。[test_codex_worker_launch.py:693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:693)

成果物影響: 費消済み job/session/token が試行台帳から消え、残存 process が workspace を変更しても certified output から参照できない。

### [must-fix] R1 の「wall-clock hard cap」は job 全体を hard-cap していない

検出できないもの:

- timer は manifest・prompt・executable hash・最大 5 秒の `codex --version` 完了後に始まる。
- output 公開、receipt 書込み、self-check も計測外。
- `setsid()` で逃げた子が生存中でも job を accepted にする。

[tools/codex_worker_launch.py:1225](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1225)、[同:1310](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1310)、[同:1837](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1837)。特に setsid 正例は rc=0 のまま escaped PID の生存を確認している。[test_codex_worker_launch.py:821](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:821)

receipt の `escaped_process_containment="not_attempted"` は正直だが、「job の wall-clock hard cap」という名称とは両立しない。実体は「preflight 後の verified process-group supervision deadline」である。

成果物影響: `accepted` receipt が発行された後も job 由来 process が走り続け、receipt の wall-clock 値より長く資源消費・workspace 変更が継続しうる。

### [must-fix] 最終 drain 後の上限超過を accepted として公開してから self-check で落とす

検出できないもの: 自然終了を確認した後、最終 drain・reap・fsync により wall-clock または累積 usage が上限を超える race。

上限判定は最終 drain 前。[tools/codex_worker_launch.py:977](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:977)。その後に再度 rollout を読み、wall-clock を確定する。[同:1051](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1051)。しかし `_seal_attempt` は確定値を上限と再比較せず accepted を決める。[同:840](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:840)

さらに output と accepted receipt を公開した後で checker を呼ぶ。[同:1376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1376)。checker は超過を検出するため、最終状態が「process rc=2、公開 output あり、receipt 内 launcher_rc=0/outcome=accepted」になりうる。

成果物影響: 同じ job が caller からは失敗、receipt からは accepted となり、certified 選択がどちらを信じるかで受理集合が分岐する。

### [must-fix] M1〜M16 の変異帰属は 16 本中少なくとも 7 本が未証明

検出できないもの: duplicate gate による別理由赤、非一意 operator、call-site bypass、非決定的並列化。以下は静的判定であり、実際の変異本走結果ではない。

| ID | 静的帰属 | 期待 node と該当 file:line |
|---|---|---|
| M1 | **MASK / 別理由赤**。acceptance gate が `_seal_attempt`、writer、checker に三重化。最初を外すと writer が launcher error にし、他の一層だけを外す変異は生存する | `test_limit_stop_is_never_accepted`; launch:858, 1105, 1496, 1635 |
| M2 | **operator 非一意**。0 event は `model_calls==0`、`usage is None`、terminal 不一致の三条件で拒否される。単一 conjunct 削除は生存し、early return だけが kill | `test_missing_metering_evidence_is_not_accepted`; launch:726–740 |
| M3 | **部分的**。CLI-reported 定義・終了済み判定・実行中判定・attempt 後判定に複製。単一箇所の `input_tokens` 化は経路次第で生存 | `test_token_cap_uses_cli_reported_definition`; launch:549, 1003, 1019, 1361 |
| M4 | KILL 可能だが **対象実装二本に anchor がない**。SIGKILL は共有 helper 側 | `test_sigterm_ignoring_child_is_killed`; `tools/dev_waves/worker.py:181,201` |
| M5 | 単一理由 KILL。別の wall cap は発火するが exact `stop_reason` が偽 kill を防ぐ | `test_cumulative_limits_do_not_reset_between_attempts`; test:563–569 |
| M6 | 単一理由 KILL。attempt 数・counter・PID 数を固定 | `test_max_attempts_never_spawns_extra_attempt`; test:591–597 |
| M7 | 単一理由 KILL。rc=2、receipt 不在、未 spawn を固定 | `test_workspace_write_retry_is_refused`; test:600–611 |
| M8 | **生存余地あり**。barrier は fake 起動前半にあり、manifest の load/replace critical section にはない | `test_parallel_jobs_preserve_both_manifest_entries`; fake:73–83、test:614–660、launch:462–517 |
| M9 | **登録どおりの call-site 変異は生存**。テストは helper を直接呼ぶだけで、receipt writer が helper を迂回しても緑 | `test_partial_receipt_never_visible_at_final_path`; test:663–677、launch:1385 |
| M10 | **部分的**。published output hash 削除は kill するが、attempt output hash 再計算だけの削除は生存 | `test_check_receipt_detects_output_tampering`; launch:1785, 1822、test:680–690 |
| M11 | **MASK / 別理由赤**。append の wave_id gate を外しても checker が rc=2 にする。manifest は既に foreign entry で汚染済み | `test_manifest_refuses_foreign_wave_id`; launch:473, 1760、test:693–715 |
| M12 | 単一理由 KILL | `test_manifest_missing_session_fails_without_strict`; ledger:1033–1036, 1105–1109 |
| M13 | 単一理由 KILL。fixture の issue は cached 超過だけ | `test_cached_exceeding_input_is_malformed`; ledger:212–225、test:485–506 |
| M14 | 単一理由 KILL | `test_empty_manifest_is_rc2`; ledger:298–302、test:1168–1186 |
| M15 | line 752 の total count 変異なら単一理由 KILL | `test_job_count_is_distinct_job_id_under_manifest`; ledger:751–760、test:1189–1242 |
| M16 | 単一理由 KILL | `test_inconsistent_metering_is_not_accepted`; launch:726–740、test:718–729 |

特に M1、M8、M9、M11 は現状の mutation matrix で KILLED と記録してはいけない。M2、M3、M10 は exact old→new anchor の再登録が必要。

成果物影響: matrix が全 kill と記録されても、limit 非採用、token cap、atomic receipt、manifest 一意追記の受理集合は証明されない。

### [must-fix] fake は live tail を検査しておらず、実 CLI event 形も pin していない

検出できないもの: rollout が作成後に段階的に伸びる実挙動で、初回だけ読んで以後 tail しない変異。

fake は rollout を `session_meta → turn_context → token_count` まで全件書き、各行 `flush+fsync` してから待機する。[test_codex_worker_launch.py:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:93)、[同:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:112)。したがって「発見時に一度だけ読む」実装でも token/model cap テストを通しうる。

実 CLI probe2 は token_count が 12/20/29/37/39 秒に逐次増加している。[probe/README.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/probe/README.md:37)。また実 stdout には `turn.started`、`item.started/completed`、`cache_write_input_tokens` があるが、fake は省いている。[probe/events2.jsonl:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/probe/events2.jsonl:1)。probe 自身も buffering/fsync の一般性は未証明と明記している。[probe/README.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/probe/README.md:8)

成果物影響: live model/token cap が死んでも wall-clock 停止だけで rc=1になり、receipt の `stop_reason` と resource actuals が誤帰属する。

### [must-fix] R3 の `possible_unobserved_overshoot` は存在するだけで意味が拘束されていない

検出できないもの: metering missing/inconsistent なのに `false` と記録する receipt、および receipt 改変による true/false 反転。

writer は model/token limit が実際に trigger した場合だけ true にする。[tools/codex_worker_launch.py:1191](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1191)。従って token event を一件も観測できない attempt は、不可視 overshoot を最も否定できないのに false になる。checker は bool 型だけを検査し、attempt/metering/limit と再束縛しない。[同:1559](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1559)。テストも true の一方向しか pin していない。[test_codex_worker_launch.py:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:479)

成果物影響: report の overshoot 証拠が「不可視消費なし」と誤読され、T-184 の policy 比較入力が変わる。

### [must-fix] R6 の `termination_verified` が identity 未取得時に恒真化する

検出できないもの: `read_pid_identity()` が失敗した高速終了 process が同一 group の子を残す場合。

identity 取得失敗は `None` に落ちる。[tools/codex_worker_launch.py:962](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:962)。その後 `_group_member_count(None)` は無条件 0、`_normal_reap` は `termination_verified=True` を返す。[同:763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:763)、[同:819](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:819)。この経路を作るテストはない。

成果物影響: group の消滅を観測していない receipt が `termination_verified=true` で accepted となり、certified output と process 生存状態が食い違う。

### [nit] R19 の CLI version は checker で再束縛されない

検出できないもの: receipt の `codex_version` 文字列だけを改変する操作。

validator は non-empty string だけを要求し、checker は executable hash のみ再計算する。[tools/codex_worker_launch.py:1527](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1527)、[同:1766](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_launch.py:1766)。現行テストも binary hash 変化しか扱わない。[test_codex_worker_launch.py:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/orchestrator/tests/test_codex_worker_launch.py:879)

成果物影響: report が参照する CLI version を改変しても `check-receipt` が受理する。

## 正例・T-179 整合

- P1 は静的には accepted に到達する。P1 テストは outcome、exact stop_reason、metering、termination、PID 消滅まで assert している。
- P3 は自然終了側が `actual > limit` だけを超過とし、checker が `<=` を許すため、model_calls=1 / cli_reported=60 の境界は accepted になる。pytest は未実施。
- 旧形への現在の過剰拒否は確認しなかった。stdout の実 CLI 固有 `cache_write_input_tokens` は未知 field として無害に無視し、欠落した `reasoning_output_tokens` は 0 扱いする。
- T-179 実 rollout 10 本について、全434件の `total_token_usage` と `last_token_usage` を走査した結果、`cached > input` は0件だった。
- 10個の distinct job_id を持つ manifest を標準入力から与え、現行 ledger を `--manifest ... --json --strict` で read-only 実走した。rc=0、`issues={}`、10 session / 434 model_calls / 2,757,982 cli_reported、および stage別6値は凍結 README と全一致した。したがってR4は現行T-179データを malformed にしない。
- 一方、P2テスト自体は synthetic・legacy `--cwd-contains` 経路であり、manifest 実データ整合の証拠ではない。今回の実走がその不足を補ったが、回帰テストとしては固定されていない。

現行コードで実効なのは R2、R4、R7、R8、R10〜R12、R16、R20。部分実装は R1、R3、R6、R9、R13〜R15、R19。R18 の probe package は存在するが、fake 回帰への反映が不足している。

## 総括

**NO-GO**

最重要3件:

1. post-spawn 例外・foreign manifest 失敗で process cleanup と fail-closed receipt の双方が欠落する。
2. wall-clock hard cap の射程が過大で、escaped child 生存や最終 drain raceにより accepted artifact と実資源状態が食い違う。
3. M1/M8/M9/M11 が単一理由 kill でなく、fake も実 CLI の incremental tail を再現しないため、変異 matrix の検出力を認証できない。