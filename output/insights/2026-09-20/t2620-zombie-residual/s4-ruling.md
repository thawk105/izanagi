# 段 4 裁定 — [T-2620] 確認手番 (2026-09-20 07:30 JST、親)

main は wave 開始時から不変 (b7f970dfa)。spool に T-2620 の未 fold fragment なし。

## 相談所見の裁定 (real / refuted、採否、scope)

| # | 判定 | 採否 | 内容 |
|---|---|---|---|
| A1 | real | 採用 (scope 内) | forced-stop 経路 (`_terminate` → worker.py `_verified_group_exists`/`_group_members` → launcher `_wait_for_group_exit`) が N2 に無い。**N2b** = 既存 `sigterm_ignore` mode を subreaper harness の下で走らせる (= F973 の再現そのもの)。worker.py の実装は触らない (検査対象化のみ) |
| A2 | real | 採用 (scope 内) | 3 語は相互排他の分類でなく代表負例。**N4 混在** (TERM 無視の生存子 1 + Z 1、正常終了) を足し、現行 2 / Z 除外 1 を示す。外部真値 (test が `/proc/<pid>/stat` の state を読む) を観測表に併記 |
| A3 | real | 採用 (scope 内) | N3 は「読取不能の e2e」でなく **consumer 入力の合成負例**: 受理済み receipt の `process_group_residual` だけを `null` に (他 field 不変) → `check-receipt` rc 2。`1` 版も対で。「途中 unknown→最終 0」は sidecar `unknown_sources_seen` にだけ残る事実を既存 test (T:4915、T:5172) と code から insight に書く (新 test は足さない) |
| A4 | should | 採用 (insight 文言) | poll 0.01 s / timeout 0.5 s・1.0 s、期限到達時に残る場合だけ拒否、F973 の 44 走緑は subreaper 無しの安全証明でない、probe は 50 ms 後の走査。「init が即回収」→「この 1 走では 50 ms 後に残存なし」 |
| B1 | real | 採用 | harness の順序固定: prctl 成功 → launcher 起動 → launcher だけを `waitpid` → 終了後に `waitpid(-1)` で養子回収 → launcher rc で exit。fake は対象 PID の `Z` を有限期限 (5 s) で poll してから exit 0。test は `limit_trigger is None`・`codex_exit_code == 0` を前提検査に置く。pytest worker 自身へ prctl を立てない |
| B2 | real | 採用 | 起動直後から `try/finally` で所有。N1/N4 は子の pid 登録後 finally で SIGKILL + `_assert_pid_gone`。N2 は harness が回収した pid を stderr に出し、test が「養子回収済み」を検査。launcher timeout・receipt 不在でも同じ後始末 |
| B3 | real | 採用 | 観測値 (receipt の residual / termination_verified / accepted / launcher_rc / stop_reason、sidecar `residual_observation`、外部 state) を 1 つの dict に集めてから **1 回の等値 assert** にする (変異時の失敗本文に全 field が出る)。M2 は既存 T:4627 も kill するので **M2' へ差し替え** (下の事前登録)。launcher path は `_ROOT` 解決なので変異 worktree 内で test を走らせる |
| B4 | should | 採用 (裁定パッケージの択) | M1 の注入点は malformed 検査の後・PGID 判定の前。裁定パッケージは (a) 在籍数の契約を維持 / (b) Z だけ除外 (回収不全の情報を失う) / (c) 非 Z 残存数と Z 数を分けて記録し受理条件への結び方は別途 / 注記: Z/X/x 除外は別案、D705 は「非占有扱いでも zombie 件数を保持」の参考先例 |
| B5 | nit | 採用 (文言) | `_group_members` は tuple、hidepid 不在は「本 probe では再現していない」、「subreaper 下でだけ」→「この harness で採用する再現手段」 |

scope 外 real 所見: なし。研究前進・実測欠陥を示す新規起票もなし。

## plan v2 (実装面 = `orchestrator/tests/test_codex_worker_launch.py` のみ、production 差分ゼロ)

1. `_write_fake_codex` に mode を 2 つ足す (既存 mode 分岐 l.1543〜1583 の隣):
   - `orphan_running`: 正常 flow (thread.started・token・output) の後、`child_sleep(ignore_term=True)` で TERM 無視の子を残し **正常終了 (rc 0)**。
   - `orphan_zombie`: 正常 flow の後、`os.fork()` で孫を作り孫は即 `os._exit(0)`。親 (leader) は孫の pid を `pid_dir/zombie.pid` に書き、`/proc/<gc>/stat` の state が `Z` になるまで 5 s を上限に poll (wait しない) してから正常終了。
   - `orphan_mixed`: `orphan_running` + `orphan_zombie` の両方 (生存子 1 + Z 1)。
2. `_write_subreaper_harness(path)`: python script。`prctl(36, 1)` (ctypes、失敗なら rc 97 で即終了) → `subprocess.Popen(argv[1:])` → `waitpid(launcher)` → `waitpid(-1, 0)` loop で全養子を回収し reaped pid と `/proc` から読んだ state を stderr へ 1 行 JSON で出す → launcher の rc で exit。
3. test 5 本 (名前は author に委ねるが `t2620` を含める):
   - N1 `orphan_running` (harness 無し): receipt residual 1 / termination_verified False / accepted False / stop_reason `max_attempts` / launcher_rc 1、sidecar final_count 1・unknown なし、外部 state `S` (or `R`)。finally で子 KILL。
   - N2a `orphan_zombie` + harness: residual 1 / verified False / accepted False / launcher_rc 1、sidecar final_count 1、外部 state `Z` (harness 回収前に test が読む — harness は launcher 終了後すぐ回収するので、**fake が書いた zombie.pid の state は harness の stderr JSON (回収直前に読む) を真値にする**)。前提検査: `limit_trigger is None`、`codex_exit_code == 0`。
   - N2b `sigterm_ignore` + harness (F973 再現): residual 1 / verified False / accepted False / limit_trigger `wall_clock_admission_bound_s`、sidecar に SIGTERM/SIGKILL の記録。
   - N4 `orphan_mixed` + harness: residual 2 / verified False / accepted False。finally で生存子 KILL。
   - N3 consumer 合成負例: `normal` で受理された receipt の `attempts[0].process_group_residual` だけを `null` → `check-receipt` rc 2 (stderr に `attempt.accepted semantic binding`)。`1` 版も同 test 内で対にする。
4. 観測値は dict にまとめて 1 回の `==` assert (B3)。既存 test の期待値は変えない。既存 helper (`_run_case`、`_base_command`、`_read_launcher_diagnostics`、`_assert_pid_gone`、`_leader_pids`) を再利用。harness 経由の起動は `_run_launcher_subprocess(command=[sys.executable, harness, *command], ...)` の形。
5. N1/N2a/N4 の `max_wall` は "10" (fake は 1 s 以内に終わるが負荷余裕)。N2b は既存 test と同じ "3"。

## 変異の事前登録 (DW-M01、単一理由、両走 = 旧 HEAD と新 test)

| ID | 位置 (tools/codex_worker_launch.py) | 変異 | 旧 HEAD の期待 | 新 test の期待 KILLED node |
|---|---|---|---|---|
| M1 | `_group_member_count` の `if int(fields[2]) == identity.pid:` の直前 (malformed 検査の後) | `if fields[0] == "Z": continue` を挿入 (**= Z 除外案の代理、本題の実測**) | SURVIVED (既存 `test_sigterm_ignoring_child_is_killed` を含め全緑) | N2a、N2b、N4 (residual が 1→0 / 2→1) |
| M2' | `_normal_reap` の `return residual, residual == 0` | `return (residual if residual is None else 0), residual is not None` (非 0 の生存残存を 0・verified True に化ける) | SURVIVED (T:4627 は None→(None, False) 不変、T:5172 は 0→(0, True) 不変) | N1、N2a、N4 (normal reap で residual ≥ 1 の 3 本) |
| M3 | `_validate_attempt` の accepted 束縛 `and attempt["process_group_residual"] == 0` | この 1 行を削除 | SURVIVED (既存の truth-table test は limit_trigger だけ) | N3 |

kill の意味 (DW-M03): M1/M2' は受理集合 (accepted / launcher_rc) が変わる。M3 は checker の fail-closed (rc 2 → 0) が変わる。診断文字列だけの赤は kill に数えない。
期待 node が完全集合でなければ初回を probe とし erratum を残して再登録 (DW-M08)。

## 不変条件の再確認
- production は 1 byte も変えない (変異は harness の固定 commit worktree で走らせ復元)。受理集合不変。worker.py 不変。新 gate・台帳・一般化なし。
- 段 6 は review 2 本 (正しさ境界 / 過剰・削除) 並列 (DW-S06-A)。

## 段 6 レビュー所見の裁定 (07:50 JST、親)

| # | 判定 | 採否 | fix |
|---|---|---|---|
| A1 (+B3) | real | 採用 must-fix | harness が launcher 終了後に養子 (ppid == harness) を列挙し state を記録 → 非 Z を SIGKILL → 全部 `waitpid` で回収 → 報告 (`adoptees` [[pid, state_at_exit]]、`reaped`、`unreaped`)。固定 3 秒待機を無くす。N1 も harness 下へ揃える (subreaper 無しの生存子は probe §3) |
| A2 = B2 | real | 採用 must-fix | harness は env `IZANAGI_T2620_LAUNCHER_PID_FILE` の path へ launcher pid を書く。test の finally は launcher pid・leader-*.pid・child.pid・zombie.pid を全部 SIGKILL → 生存者を集めて 1 回の assert (途中で止めない) |
| A3 | real | 採用 (erratum、再走不要) | M1 の kill 意味: N2a = 受理集合の変化 (accepted/rc)、N2b = residual 1→0 と termination_verified False→True (受理は limit で不変)、N4 = residual 2→1。期待 node 集合 {N2a, N2b, N4} は不変。DW-M08 の「構造化シグナルの pin」として N2b/N4 を別枠に記録 |
| A4 | should | 採用 fix | observe は `launcher_rc` と harness stderr JSON (無ければ `"missing"`) を先に記録し、receipt / sidecar は欠落を `"missing"` で表す。1 回の等値 assert は維持 |
| A5 | should | 採用 (insight §8 に条件表) | 受入負荷での決定性は未測定と明記。N2b の readiness handshake 不在は既存 `sigterm_ignore` と同型 |
| B1 | real (must-fix → should) | 採用 fix | `_run_launcher_subprocess` の変更を戻し、T-2620 の起動 (subprocess.run + TimeoutExpired → `_assert_launcher_returncode(exc, …)`) を `_assert_t2620_residual_case` 内に閉じる。observe → `_assert_launcher_returncode` の順 |
| B4 / A6 | nit | 不採用 (author.md は逐語保存、insight は統合後行番号) | — |

期待値 (現行の観測値) は一切変えない。test 名も変えない。fix 後: 焦点走再走 → 統合 commit 2 → 変異本走を fix commit で再走 (走行中の final は probe 扱い)。

## 焦点再レビュー所見の裁定 (08:43 JST、親、fix 3 巡目 = DW-O16 の上限)

| # | 判定 | 採否 | 対応 |
|---|---|---|---|
| F1 harness の `/proc` 走査が `FileNotFoundError` しか捕まえない | real | 採用 must-fix → fix3 | `except (OSError, ValueError): continue`。fix2 の契機と同じ消滅競争が harness を殺し、回収と JSON 出力に到達しない経路を塞ぐ |
| F2 外側 timeout では harness が先に失われ、養子の回収が外の祖先に落ちる | real | 不採用 (限界として明記) | 成果物 (負例表・裁定パッケージ) を変えない (DW-G05)。launcher 自身の admission 上限 (wall 10 / 3 s、finalization 60 s) で有界。fix3 で test の comment と insight §8 に明記 |
| S1 決定性の結論を期限条件付きに限定 | should | 採用 (insight §8 の条件表を更新) | 「期限を越えた走査の結果が None なら final unknown」「N2b の readiness handshake 不在」を追加 |
| N1 PID 再利用窓 / N2 養子列挙は 1 回 | nit | 採用 (insight §8 に限界として) | code は変えない |
| A1/A2/B2 partial | — | F1 で A1 を閉じる。A2/B2 の timeout 側は F2 と同じ扱い | — |

fix3 後は焦点再レビューを重ねず (3 巡上限)、親が焦点走 + 変異本走 (final4、fix3 commit) で裏取りして閉じる。
