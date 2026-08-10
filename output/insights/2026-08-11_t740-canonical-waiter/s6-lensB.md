# レンズ B レビュー

pytest は実行していない。親提示の `47 passed` / `114 passed` は実測済み前提として扱ったが、本レビューから緑は主張しない。

## 実運用トレース

- 現在の branch は `worktree-dev-wave-t740-canonical-waiter`。`--wave dev-wave-t740-canonical-waiter` に対する `branch.endswith(wave)` は真なので、強調された R2 branch 検査は通る。[tools/dev_wave_wait.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:366)
- tracked 差分はなく、新規 2 ファイルは untracked なので clean 検査も通る。untracked を除外するのは実装どおり。[tools/dev_wave_wait.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:372)
- 現在の `HEAD` は local `main` より 10 commit 遅い。したがって実走には事前作成済み `--merge-message-file` が必須だが、現在の job directory には該当ファイルがない。[tools/dev_wave_wait.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:523)
- lease の実運用 directory は `/work/1/SFC/tanab/dev-wave-jobs/land-lease`。[docs/pegasus-runbook.md:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:759) 解決順は `--lease-dir` が最優先、次に `IZANAGI_WAVE_LEASE_DIR`、両方なければ claim 前に rc=2。[tools/dev_wave_wait.py:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:588) 現在のレビュー shell では同環境変数は未設定だが、runbook は明示的な `export` を要求している。[docs/pegasus-runbook.md:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:764)
- `python3 tools/run_tests.py` は wave root を cwd として shell なしで走り、環境と stdout/stderr を継承する。[tools/dev_wave_wait.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:84) [tools/dev_wave_wait.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:550) `run_tests.py` 自身も自分の checkout を `_REPO` にして pytest を起動するため、裸形なら cwd は正しい。[tools/run_tests.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/run_tests.py:53)
- ただし `PYTEST_ADDOPTS` も継承される。非空なら `run_tests.py` は裸形でも acceptance shape と認めず、受入専用 preflight を無効化する。[tools/run_tests.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/run_tests.py:505) 現在は未設定だが、script はこれを検査しない。

## 所見

### RB1 — blocker

**主張:** 現行 runbook は canonical script を呼んでおらず、依然として `wave_land_window.py claim` を直接呼ぶ手順である。さらに成功時即 release と読める既存記述は、R1 の「land 終端まで保持」と衝突する。[docs/pegasus-runbook.md:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:764) [docs/pegasus-runbook.md:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:810)

**成果物影響:** land 後も手書き loop が使われ、exact claim・main 再検査・成功時 lease 保持を通らない受入結果が台帳へ記録され得る。

**提案:** land 前に §7.3 を、`--merge-message-file` を常時準備した `tools/dev_wave_wait.py acceptance -- ... python3 tools/run_tests.py` の裸形へ置換し、成功後の明示的な release 手順も併記する。これは実装報告でも未完了と明記済み。[s5-impl.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t740-canonical-waiter/s5/s5-impl.md:39)

### RB2 — must-fix

**主張:** 「lease is held until land termination」という成功出力は排他保証として不正確である。lease は取得から 2400 秒で stale になり、受入全走だけで 1055〜1273 秒を消費する一方、成功後は heartbeat せず release も飛ばす。[tools/dev_wave_wait.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:559) [tools/wave_land_window.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:28) [docs/pegasus-runbook.md:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/docs/pegasus-runbook.md:820)

**成果物影響:** 段 7〜9 が残り約 19〜22 分を超えると、親は保持中と思ったまま他 wave の受入・land と競合し、tested main/tip が stale になる。

**提案:** holder heartbeat/fencing を別裁定に上げるか、少なくとも残存期限を成功結果へ構造化出力し、その期限内に land できない場合は fail-closed にする。「land 終端まで保持」と無条件には表示しない。

### RB3 — blocker

**主張:** preflight で claim 前に拒否した場合でも `finally` が無条件に `release` する。release 権限は wave slug の digest だけなので、誤った cwd から実在 wave slug を指定すると、その wave が保持中の lease を削除できる。[tools/dev_wave_wait.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:509) [tools/dev_wave_wait.py:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:573) [tools/wave_land_window.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:747)

テストも preflight 拒否後の release を正として固定している。[test_dev_wave_wait.py:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:695)

**成果物影響:** 操作ミス一回で別 invocation の排他を解除し、並行受入による stale 結果や land race を台帳へ持ち込む。

**提案:** 「helper の claim を呼び始めた」状態を明示的に追跡し、それ以前の preflight/入力失敗では release しない。claim が lease を作った可能性のある経路だけ cleanup 対象にする。

### RB4 — must-fix

**主張:** acceptance の最大待機時間は claim loop にしか効かず、claim/Git/commit/受入 command の subprocess には timeout がない。また producer は既定無制限で、alive PID、zombie、pid-only 縮退後の PID 再利用では永久待機できる。[tools/dev_wave_wait.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:84) [tools/dev_wave_wait.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:264) [tools/dev_wave_wait.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:421)

**成果物影響:** 受入結果が永久に確定せず land 不能になり、保持中 lease は TTL 後に排他性だけ失う。

**提案:** helper/Git には短い stage timeout、受入 command には運用上限と process-group cleanup を設ける。producer の canonical 例では `--max-wait-seconds` を必須にし、`/proc` state `Z` も死亡として扱う。

### RB5 — must-fix

**主張:** preflight は「何らかの git worktree」と branch suffix しか確認せず、cwd が repo root か、Git がその cwd を指しているかを確認しない。全 git command は `GIT_DIR` / `GIT_WORK_TREE` 等を未消毒のまま継承する。[tools/dev_wave_wait.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:84) [tools/dev_wave_wait.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:354)

**成果物影響:** stale Git 環境下では別 worktree へ merge/commit しながら元 worktreeのテストを走らせ、誤った tip を受入済みとして扱い得る。

**提案:** Git 環境を `run_tests.py` と同様に allowlist 化し、`git rev-parse --show-toplevel` と resolved cwd の一致を claim 前に要求する。ユーザー提示の branch 規約を採るなら `branch == f"worktree-{wave}"` の exact 比較にする。

### RB6 — must-fix

**主張:** M2 の中心テストは mutated acquired 経路の後段を用意していないため、部分一致 mutant は偽投入の明示検出ではなく `_FakeEffects` の queue mismatch と cleanup rc=74 で赤くなる。`run_acceptance` が `AssertionError` を含む `BaseException` を握り潰すため、赤理由が一つに絞れない。[test_dev_wave_wait.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:374) [tools/dev_wave_wait.py:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:571)

**成果物影響:** M2 を KILLED と記録しても exact-JSON gate の実効検出力を証明できず、変異台帳が過大評価になる。

**提案:** `_claim_once` を直接呼び、diagnostic/nested の `"acquired"` を含む payload が厳密に `"held"` を返すテストを置く。E2E 側も mutant が後段 command へ到達できる fixture にして、投入回数の差で殺す。

### RB7 — must-fix

**主張:** 唯一の実結合テストは `feature-integration`、明示 `--lease-dir`、behind=0、`python -c` だけである。実 branch 形、環境変数 fallback、real merge/message、`run_tests.py` の cwd・環境・stream は一つも結合検査していない。[test_dev_wave_wait.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:737)

**成果物影響:** 47 tests が通っても、現場の merge/dispatch 経路だけが失敗し、受入全走と land が成立しない可能性が残る。

**提案:** `worktree-<slug>` branch、env 経由 lease、main を一 commit 前進、実 message file、cwd/env/stdout/stderr を検査する無害な child を組み合わせた実 Git 結合テストを追加する。

### RB8 — nit

**主張:** 現行 consumer はまだ存在しないが、予定された canonical invocation でも acceptance の poll/max override、`--lease-dir` override、message 省略、producer の直接 `--pid`、細分化 rc は通常使用されない。これらは裁定上残した面だが、運用正本から到達する branch は defaults + env + message + pid-file に限られる。[tools/dev_wave_wait.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:140)

**成果物影響:** 受入値は直接変えないが、未使用分岐が検査・保守面を増やす。

**提案:** 今回は削らず、runbook consumer land 後に使用実績を取り、到達しない override を後続整理候補にする。

## 手書き待ち手との 1 対 1 比較

| 手書き挙動 | 新 script | 判定 |
|---|---|---|
| `case "$out" in *acquired*)` で stdout 全体を部分一致。[run_acceptance.sh:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:20) | JSON object、duplicate key、state 型・既知値を検査し、`state == "acquired"` のみ受理。[tools/dev_wave_wait.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:401) | 構造的に改善。ただし M2 の変異証明が弱い。 |
| `seq 1 1200` × 10 秒で上限約 12000 秒。[run_acceptance.sh:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:16) | monotonic 7200 秒、30〜120 秒 poll。[tools/dev_wave_wait.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:429) | lease 待ちは bounded。subprocess と producer は未閉鎖。 |
| `.done` → exact PID death → artifact size の三点を表示。[wait.sh:9](/work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/wait.sh:9) | exact PID + starttime、死亡後 `.done` と artifact の regular-file 実在を最大30秒検査。[tools/dev_wave_wait.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:244) | pgrep 自己一致と死後欠落の永久待ちは閉じた。反面、`.done` rc、artifact 非空、byte数の表示を失った。 |
| claim、merge、acceptance、done/status を job files に永続化。[run_acceptance.sh:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh:19) | claim/Git は capture 後に捨て、child stream を継承し、成功時は一文だけ。 | 再現用ログと進捗可視性を失った。外側で redirect/receipt を作らないと最大2時間無出力になる。 |

## 無音死の残余経路

| 経路 | 実際の終端 |
|---|---|
| `held` / `queued` が続く | 7200秒で `claim-timeout`、release 後 rc=70。黙って永久には待たない。[tools/dev_wave_wait.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:437) |
| producer 死亡後に file 不足 | 最大30秒後 `producer-files`、rc=70。[tools/dev_wave_wait.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:289) |
| liveness が `EPERM` / 不明 | 即 `producer-liveness`、rc=70。[tools/dev_wave_wait.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:244) |
| alive PID、zombie、pid-only 縮退後の再利用 | producer 既定では黙って無期限待機。[tools/dev_wave_wait.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:274) |
| claim/helper、Git hook、署名、commit が停止 | subprocess timeout がなく黙って無期限待機。[tools/dev_wave_wait.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:84) |
| `run_tests.py` またはその子孫が停止 | command timeout がなく wrapper は返らない。child の出力だけは継承される。[tools/dev_wave_wait.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:554) |
| SIGTERM/SIGHUP/SIGINT | 通常は release 後 `128+signal`。ただし handler install/restore の極小窓では `_SignalReceived` が outer catch の対象外。[tools/dev_wave_wait.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:597) |
| SIGKILL / host停止 | script は検出も return もできず、lease は TTL 任せ。[tools/dev_wave_wait.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:597) |

## 総括

**blocker あり。NO-GO。** Branch suffix は実環境で通るので、そこは blocker ではない。NO-GO の直接理由は、canonical runbook 未結線（RB1）と、claim 前の preflight 失敗が既存同一-wave lease を release できる破壊経路（RB3）。RB2、RB4〜RB7 も land 前に閉じるべきである。

変異予測では `T` を `orchestrator/tests/test_dev_wave_wait.py::` と略す。

| 変異 | 予測される赤 nodeid | 検出力判定 |
|---|---|---|
| M1 | `Ttest_pid_probe_calls_kill_zero_for_exact_pid` | 赤。exact `(pid, 0)` と subprocess 不在を直接固定する。注入方法次第で producer 系の追加 error も出る。 |
| M2 | `Ttest_acceptance_ignores_acquired_outside_top_level_state`、`Ttest_acceptance_rejects_claim_json[duplicate-state]` | 赤になるが、queue mismatch→cleanup rc=74 でも赤くなるため単一理由でない。現状の KILLED 証拠は不十分。 |
| M3 | `Ttest_default_wiring_with_real_git_and_lease_helper`、`Ttest_merge_sequence_and_postcheck_are_exact` | 赤。前者が実 lease file の残存を直接検査するため理由は一意。 |
| M4 | `Ttest_nonzero_stage_blocks_submission_and_releases[postcheck]`、`Ttest_merge_sequence_and_postcheck_are_exact` | 赤。`[postcheck]` は本来の赤 postcheck を飛ばして command へ到達する差を検出する。 |
| M5 | `Ttest_merge_required_without_message_file_releases_before_submission` | 赤になる見込みだが、後段 fake が未準備で rc=74 化する可能性があり、赤理由が一つに絞れない。 |
| M6 | `Ttest_acceptance_command_red_is_propagated_after_release`、`Ttest_abnormal_path_always_releases[subprocess-error]`、`Ttest_abnormal_path_always_releases[keyboard-interrupt]`、各 nonzero/non-acquired case | 赤。release event と queue 残存で直接検出する。 |
| M7 | `Ttest_producer_dead_without_required_file_fails_closed[artifact]` | 赤。期待 rc=70 が rc=0へ反転するため理由は一意。 |
| M8 | `Ttest_identity_preflight_rejects_before_claim[wrong-branch--preflight-branch]` | 赤。ただし後段 fixture がなく、実際の最初の失敗は queue mismatch/cleanup failureにもなり得るため、失敗表示は単一理由にならない。 |