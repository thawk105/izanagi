# 段 4 裁定 — [T-2665] (親)

裁定 inbox 再走査: main は b4631a92e (第 20 回 rulings は **D2104 項 32** として fold 済み、worklog carry は「実装手番」)。wave worktree へ ff-only で取り込み済み。

## 所見の裁定 (real / refuted、採否、scope)

| id | 判定 | 採否 | 扱い |
|---|---|---|---|
| A1 保証範囲の明記 | real | 採用 must-fix | 「親」= launcher 自身。転送する signal は **TERM / INT / HUP** の 3 つ (同一経路、HUP は SSH 切断の道連れ)。launcher PID 単独への SIGKILL・上位 shell だけの kill は保証外として docstring と JSON summary の `cancel_signal` で表す。brief 完了判定 (b) は「launcher が TERM/INT/HUP を受けたとき子も止まる」に訂正 |
| A2 有界待機と共通取消経路 | real | 採用 must-fix | pipe を使わず子の stdout/stderr は **tempfile (TemporaryFile)** へ。主 loop は `poll()` + 50 ms sleep の有界 loop。handler は flag のみ。spawn / PGID 検査 / 出力の例外も含め、**全異常経路が同じ取消関数** (生存子へ signal → 5 秒 poll → KILL → 1 秒 poll → 未回収は unknown) を通る |
| A3 成功境界 | real | 採用 must-fix | 全子 reap 後に **全 path を lstat で再確認** (ENOENT だけ absent、他は unknown)。成功境界 = 再確認 + cancel flag 最終確認 + stdout flush 成功。flag が一度でも立てば rc 2。境界後の signal は害がない (子は無い) と docstring に書く |
| A4 ptrace 案の競合 | real | 採用 (ptrace 案を不採用) | 中断負例は **自己停止 wrapper** (下記) で同期。親の実測 (`probe_selfstop.py` / `probe_signals.py`): T 状態 6 ms、ShdPnd 観測、CONT 後 rc -15/-2/-1、対象残存、正例は委譲で消える |
| A5 path 保証の限界 | real | 採用 must-fix | docstring に「検査時点の名前空間に依存し、検査後の symlink 置換・配下 mount は防がない。所有・取込・占有は §1〜§3 が担う」を書く。`--one-file-system` は足さない。brief の「受理集合不変」は「§1〜§3 の削除述語は不変、launcher の入力表記制約は狭める」へ訂正 |
| A6 / B5 根拠の言い換え | real (nit) | 採用 | 新規 tool の根拠 = 「固定した起動・取消・集約を実装し検査可能にする」。guard probe は当該入力・site=None の許可事実に限定して記録 |
| A7 / B7 変異の帰属 | real (nit) | 採用 | M-h は単独 kill 不能 → **両層 (M-a+M-h) で登録**し test 側の独立 pgid 観測で殺す。M-d / M-e は判定関数直呼び node が killer で、CLI 経路の迂回変異まで証明したと書かない |
| B1 §3 の順序 | real | 採用 must-fix | 文案 v2 (下記) に「全対象の 1・2・占有検査の後」「前景 1 回 (setsid・nohup・& 禁止)」を入れる。byte 勘定 6201 / 6204 |
| B2 「親」の分離 | real | 採用 must-fix | A1 と同じ扱い。Bash tool / session 終了時の配送契約は未証明として worklog に残す (実測しない) |
| B3 wrapper の許容 | real | 採用 (条件付き) | wrapper は「実物へ委譲する観測 wrapper」(DW-O14) に当たると裁定。条件: (i) 子を増やさず同 PID で `exec /bin/rm "$@"`、(ii) T → pending 観測 → CONT の順、(iii) 子 rc は `-signum` 必須 (KILL の -9 は赤)、(iv) skip は受入成功に数えない (skip 条件を作らない)、(v) wrapper なしの実 rm 正例を別 node で持つ。launcher の `rm` は **PATH 解決** (`Popen(["rm", ...])`)、docstring に運用上の信頼境界と明記 |
| B4 tools/README.md の分類 | real | scope 外 (記録) | 分類実測はユーザー手番 (tools/README.md 1)。先例: `dev_wave_cleanup.py` / `dev_wave_land.py` は未登録で login 運用。registry へ無断追加しない。worklog に「分類は運用者手番、機能は §3 の手動 rm -rf と同じ資源」と書く |
| B6 timeout 既定・時間 | real | 採用 (一部) | `--timeout-seconds` 既定 3600 は運用仮値と docstring に明記。猶予 5 秒 / 1 秒は定数 (CLI に出さない)。KILL 経路を通る test は 1 node に限る。tmp_path は `/tmp` 既定 (repo 外) |

## plan v2 (author への確定仕様)

### S1 `tools/cleanup_remove_dirs.py`
- argv: `[--timeout-seconds S] -- <abs path>...`。検証は plan §argv の 7 項目 (空/NUL、絶対・正規形、途中 symlink、実在 dir、realpath 一致、包含 (component 単位)、cwd) と option 検証、違反は **rc 64**、起動前に全件。
- 子: `subprocess.Popen(["rm", "-rf", "--", path], stdin=DEVNULL, stdout=<TemporaryFile>, stderr=<TemporaryFile>)`。`start_new_session` / `preexec_fn` / `shell` を渡さない。全 path を連続起動。起動直後 `os.getpgid(pid) == os.getpgrp()` を実測、不一致・取得失敗は unknown + 取消経路。
- signal: `SIGTERM` / `SIGINT` / `SIGHUP` の handler は最初の signal 番号を記録するだけ。主 loop (50 ms poll) が flag を見て取消経路へ。
- 取消経路 (唯一): 生存子へ受信 signal (取消起点が timeout / 内部障害なら TERM) → 最大 5 秒 poll → 残存へ SIGKILL → 最大 1 秒 poll → 未回収は unknown。`killpg` 不使用。
- timeout: 子ごと起動時刻から `--timeout-seconds`。超過 → 当該子へ TERM → 同じ取消経路 → interrupted (回収成功) / unknown。
- 判定: `removed` (pgid 一致・取消なし・rc 0・最終 lstat ENOENT)、`failed` (rc>0、または rc 0 で残存)、`interrupted` (取消・timeout で回収済み、rc<0、未起動)、`unknown` (spawn 失敗、pgid、OSError、未回収、lstat の ENOENT 以外)。rc<0 は failed より先。
- 最終集約: 全子 reap → 全 path lstat 再確認 → flag 最終確認 → JSONL 出力 (1 path 1 行 + summary 1 行) → `sys.stdout.flush()` 失敗は rc 2。rc は最後の 1 箇所で決める: 0 = 件数一致・全件 removed・取消なし、1 = failed ありで interrupted/unknown/取消なし、2 = それ以外、64 = usage。
- docstring: 目的 (D2104 項 32)、保証範囲 (launcher 自身への TERM/INT/HUP → 子へ転送、killpg は直接届く、launcher PID 単独 SIGKILL は届かない、PDEATHSIG は scope 外)、path 保証の限界 (A5)、`rm` は PATH 解決、timeout 既定は運用仮値、prune/detach/branch を行わない。
- 出力: stdout = JSONL のみ。stderr = 診断 (子の stderr 先頭 4 KiB を path 付きで)。

### S2 `orchestrator/tests/test_cleanup_remove_dirs.py`
- helper: `_launch(paths, *, env, cwd, timeout=None)` (実 CLI を `sys.executable` で起動、cwd は対象外)、`_read_results(stdout)` (行数・path 一意・summary 件数一致・rc 一致)、`_state(pid)` (`/proc/<pid>/stat` の状態)、`_shdpnd(pid)`、`_children(launcher_pid)` (`/proc/<pid>/task/*/children`)、`_wait_until(pred, deadline)` (全待機に期限)。
- fixture `stopping_rm_bin(tmp_path)`: `bin/rm` = `#!/bin/bash\nkill -STOP $$\nexec /bin/rm "$@"\n` を作り PATH 先頭へ足した env を返す。**repo 内に一時物を作らない**。
- 正例 1 `test_two_dirs_removed_without_wrapper`: 実 PATH、2 dir → rc 0、両 path 不在、両 removed、summary 一致。
- 正例 2 `test_children_share_parent_pgid_then_remove`: wrapper 付きで 2 dir 起動 → 2 子が同時に T → **test 自身が** `os.getpgid(child) == os.getpgid(launcher)` を両子で確認 → 両子へ CONT → rc 0、不在、removed。
- 負例 `test_launcher_signal_is_forwarded_before_removal[TERM|INT|HUP]`: wrapper 付き 1 dir (sentinel 入り) → T 観測 → launcher PID だけへ signal → 子の ShdPnd に同 bit を期限内観測 (無ければ赤) → 子へ CONT → launcher rc 2、path 行 `interrupted`、子 returncode == -signum (KILL の -9 は赤)、sentinel 残存。finally で子を CONT+KILL、launcher を回収。
- 負例 `test_timeout_is_interrupted`: wrapper 付き、`--timeout-seconds 0.5` → T 観測 → ShdPnd に TERM を観測 → CONT → rc 2、`interrupted`、残存。
- 負例 `test_failed_path_does_not_hide_other_removal`: 親 dir chmod 500 の対象 + 通常対象 → rc 1、`failed` と `removed`。`os.geteuid()==0` は skip (理由付き) だが受入証拠に数えない。
- 負例 `test_usage_rejects_paths_without_removal[nested|duplicate|relative|missing|symlink|mid-symlink|file|root|trailing-slash|dotdot|empty]` → rc 64、stdout 空、対象は残る。
- 負例 `test_usage_rejects_cwd_inside_target[exact|descendant]` → rc 64。
- 負例 `test_usage_rejects_invalid_options[...]` → rc 64。
- 単体 `test_zero_returncode_with_existing_path_is_failed` / `test_nonzero_returncode_with_absent_path_is_failed` / `test_summary_never_succeeds_for_incomplete_results` (実関数を直接呼ぶ、差し替えなし)。
- 自走 harness: `test_dev_wave_cleanup.py` 末尾の形式。allowlist は触らない。parametrize id は ASCII のみ。
- 各 node の待機期限は 10 秒以内、KILL 経路 (5 秒猶予) を通る node は作らない (timeout test も CONT で -15 にする)。

### S3 docs (`.claude/commands/cleanup-branches.md`) — 文案 v2 (exact、改訂全文 6201 bytes / sha256 `a6380f90dcaf8e5e5ac21cc9af0619e000697816257f3e3e8a8844595dad1f26`)
- 手順 1 の ` (branch を解放)` を削る (-19 bytes、`checkout --detach` と §0 で意味は保存)。
- 手順 3 を次の 5 行へ差し替え:
```
3. 全対象の 1・2・占有検査の後、dir 撤去は
   `python3 tools/cleanup_remove_dirs.py -- <絶対path>...` を前景 1 回 (setsid・nohup・& 禁止)。
   rc0 (全件 removed) 以外は停止。detach・branch 削除・prune は直列。rc0 後
   `git worktree prune --dry-run --verbose` の全候補＝今回所有確認済み対象なら
   `git worktree prune`。余分・不明候補時は real prune せず引渡し
```
- pin: `tools/check_docs.py` `CLEANUP_COMMAND_SHA256` → 上記 sha。`orchestrator/tests/test_check_docs.py` の `_EXPECTED_CLEANUP_COMMAND_SHA256`、`_SYNTHETIC_CLEANUP_COMMAND` (全文同一)、`test_cleanup_command_budget_is_pinned_and_enforced` の `6_203` → `6_201` (2 箇所)、oversized fixture → `original + "\n" + "x" * 3` (= 6205)。TextLimit(6_204, 110) は不変。

## 変異事前登録 (段 6 本走の候補、期待 node は probe 走で確定)
| id | category | 変異 | 期待 |
|---|---|---|---|
| M0 | positive | docstring の 1 行だけ変更 (等価) | SURVIVED |
| M1 | negative | `Popen(...)` に `start_new_session=True` | KILLED (pgid 正例、転送負例の pgid 検査) |
| M2 | negative | handler の signal 転送 (生存子への `os.kill`) を削除 | KILLED (転送負例 ×3: ShdPnd 未観測) |
| M3 | negative | 取消時の判定 `interrupted` を `removed` に、rc も 0 | KILLED (転送負例・timeout 負例) |
| M4 | negative | 最終 lstat 再確認を削除 (残存でも removed) | KILLED (単体 rc0 残存 node) |
| M5 | negative | 子 rc>0 を removed 扱い | KILLED (単体 rc>0 node、chmod 負例) |
| M6 | negative | 包含 (nested) 検査を削除 | KILLED (usage nested) |
| M7 | negative | cwd 検査を削除 | KILLED (usage cwd ×2) |
| M8 | negative | timeout 超過の TERM 送信を削除 (待ち続ける) | KILLED (timeout 負例、hang_risk のため期限を短く) — dispatch で孤児化するなら matrix から外し login probe を証拠にする |
| M9 | both-layers | M1 + pgid 検査の恒真化 | KILLED (pgid 正例の test 側独立観測) |
| M10 | negative | HUP を handler 登録から外す | KILLED (転送負例 [HUP]) |
