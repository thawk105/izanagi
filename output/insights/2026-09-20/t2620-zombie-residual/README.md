# [T-2620] 残存数計数 (`_group_member_count`) のゾンビ除外について D2044 項 21 の確認手番 — 実 process で作った負例 4 種 (TERM 無視の生存子 / subreaper 下のゾンビ / 強制停止後のゾンビ / 混在) と receipt の合成負例 1 種で、現行の計数と Z 除外 (変異 M1) の receipt・sidecar・checker への映り方を固定した。現行は 4 種とも `process_group_residual ≥ 1`・`termination_verified False`・`accepted False`・`launcher_rc 1` で拒否する。Z 除外にすると **正常終了でゾンビだけが残る負例 (N2a) は clean と同じ受理 (residual 0 / verified True / accepted True / outcome accepted / rc 0) になり、receipt にも sidecar にも区別できる field が無い**。強制停止後のゾンビ (N2b) は residual 0 / verified True へ変わるが `limit_trigger` で不受理のまま。生存子 (N1) と混在 (N4) は Z 除外でも residual ≥ 1 で拒否が続く。「読取不能」は最終 unknown なら receipt の `null` + sidecar の source、途中 unknown→最終 0 は sidecar の `unknown_sources_seen` にだけ残る。除外の採否は諮る (§7)

一次資料 (wave `dev-wave-t2620-zombie-residual`、test 追加 commit `29a07dbc03eb30af69ce4d31fbb82b1cc767e992` → fix1 `2758e5eebe79005e57509969e4209f3baca19bdb` → fix2 `bf9ca498da1e772eadc67d83d9bdecfde18b2bef` → fix3 `238b8d9980ae6c96830cae87064a2006eb0cdbf5` (最終) = local main `b7f970dfa` + test file 1 本の差分、2026-09-20 07:12〜09:10 JST)。段 1・4 の逐語は同 dir の `s1-brief.md` / `s4-ruling.md` (段 6 レビュー裁定を含む)、段 3 相談・段 5 author・段 6 レビュー 2 本・fix1・fix2・fix3・焦点再レビューの逐語は `verbatim/`、生死 probe は `probe/`、変異の spec・結果・M1 の job stdout・DW-O19 局所走は `mutation/`、焦点走 log は `focus/`。`authority: none` / `default_effect: no-state-change` — 可変状態の正本ではなく、裁定用の凍結スナップショットである。**受理集合は変えていない** (production 差分ゼロ、変異は独立 clone で走らせ、局所走は `git checkout --` で復元し porcelain 0 を確認した)。

## 1. 依頼・不変条件・結論

依頼 (command 引数、起点 = 台帳 entry 1493 の T-2620 と D2044 項 21): 残存数の計数 (PGID 在籍、`/proc/<pid>/stat` の state `Z` を除外しない) について、ゾンビを除外した後も「実行中の子・読取不能・回収不全」を receipt の consumer と負例で区別できるかを実測で確かめ、結果を insight に残す。除外の採否は確認の後に裁定へ返し、本 wave では受理集合を変えない。実装面 (test の負例追加) は Codex author (D95)。新 gate・台帳・一般化は scope 外。

不変条件を守った: `tools/` は 1 byte も変えていない (4 commit の差分は `orchestrator/tests/test_codex_worker_launch.py` のみ)。Z 除外は変異 harness (独立 clone、固定 commit、復元検査つき) の M1 と、DW-O19 の局所走 (統合 commit 後の clean な木で 2 行を一時挿入 → 実走 → `git checkout --` → porcelain 0) としてだけ走らせた。`tools/dev_waves/worker.py` の同型走査 (`_group_members`、l.146、tuple を返す) は検査対象に含めたが変えていない。

結論:
1. **現行 (Z を数える) は 4 種の実 process 負例をすべて拒否する** (§4 表)。生存子 1・ゾンビ 1・強制停止後ゾンビ 1・混在 2。
2. **Z 除外 (M1) は、正常終了でゾンビだけが残る負例 (N2a) を受理へ変える** (§5 表)。receipt (`process_group_residual` 0 / `termination_verified` True / `accepted` True / `outcome` accepted / `stop_reason` completed / `launcher_rc` 0) と sidecar (`residual_observation.final_count` 0、unknown なし) のどの field でも clean な正常終了と区別できない。同時刻に harness は state `Z` の養子を実際に回収しているので、ゾンビは PGID に在籍していた。**「回収不全」は Z 除外後に receipt から消える。**
3. Z 除外でも **生存子 (N1) と混在 (N4) は拒否が続く** (residual 1 / 2→1)。ただし現行でも「生存子 1 本」と「ゾンビ 1 本」は receipt の残存 field では同じ 1 であり、区別しているのは test 側の外部真値 (harness が読む `/proc` の state) である — **現行の receipt も S と Z を識別していない** (相談所見 A2)。
4. 強制停止経路 (N2b、F973 の再現) は Z 除外で residual 0 / verified True になるが、`limit_trigger = wall_clock_admission_bound_s` により accepted False / rc 1 のまま。**「Z 除外で受理される」は正常終了経路に限る** (F973 が赤にした test は forced-stop 経路の `process_group_residual == 0` 断言であり、Z 除外はそれを緑にするが受理は変えない)。
5. 「読取不能」は実 process から作れない (本 host の `/proc` に hidepid 無し、probe では再現していない)。既存 unit test (T:4482〜4660、`proc_scandir_oserror` / `proc_stat_read_error` / `proc_stat_parse_error` / `pid_identity_unavailable`) と code から: 最終 unknown → receipt `process_group_residual: null` + `termination_verified False` + sidecar `final_unknown_source`。途中 unknown → 最終 0 → receipt は 0 で受理可、履歴は sidecar `unknown_sources_seen` にだけ残る (`test_transient_unknown_residual_requires_later_exact_zero`、`test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`)。Z 除外はこの経路を変えない (state 判定は parse 成功後、M1 の注入点は malformed 検査の後)。**途中 unknown は実環境で起きる**: 計算ノードで file 全体 (216 test) を並列に走らせた変異 baseline で N2a・N4 の sidecar に `unknown_sources_seen: ["proc_stat_read_error"]` が入った (`final_count` は 2 / 1 で正しく、`final_unknown_source` は None)。`_group_member_count` は `/proc` **全体**を走査するので、同居する無関係な process が読取中に消えると `read_text` が `OSError` を上げて一時的に `None` を返し、`_wait_for_group_exit` が再 poll して正しい最終値を得る (§8)。
6. consumer 側: `check-receipt` は受理済み receipt の `process_group_residual` だけを `null` / `1` に変えたものを rc 2 (`attempt.accepted semantic binding`) で拒否する (N3)。変異 M3 (束縛の削除) は N3 だけが検出する。

## 2. 現行の機構と consumer の閉包 (`tools/codex_worker_launch.py` の行番号、production は wave 中不変)

producer:
- `_group_member_count` (l.1692〜1743): `/proc` を走査し、`stat` の `)` 以降の field 5 (pgrp) が leader pid に一致する entry を **state を見ずに** 加算 (l.1722〜1723)。malformed は `on_malformed`、読取失敗は `on_unknown` + `None`。
- `_wait_for_group_exit` (l.1745〜1764): 0.01 s 間隔で timeout (normal 0.5 s / terminate 1.0 s) まで poll、0 か期限で返す。**期限到達時に残っていれば残存** (途中で 1 度 Z を拾っても、その後 0 を観測すれば通る)。
- `_normal_reap` (l.1854〜1868): `process.wait()` → `residual == 0` を `termination_verified` とする。
- `_terminate` (l.1809〜1851): worker.py の `_terminate_verified_group_observed` (SIGTERM → `_group_members` が空になるまで grace → `_verified_group_exists` → SIGKILL) → `process.wait` → launcher 側 `_wait_for_group_exit(1.0)`。**worker.py の `_group_members` (l.146) もゾンビを含む**が、最終値は launcher 側の計数である。
- attempt record (l.1984〜2035): `accepted = … and residual == 0 and termination_verified`。`process_group_residual` (int|None)、`termination_verified` (bool)。
- `_writer_truth` (l.2490〜2506): 最終 attempt が accepted なら `("accepted", "completed", 0)`、limit なら `("not_accepted", <limit>, 1)`、それ以外 `("not_accepted", "max_attempts", 1)`。`launcher_rc` は `tools/dev_wave_codex.py` がそのまま返す。
- sidecar `residual_observation` (l.700〜707、2431): `final_count` / `final_unknown_source` / `unknown_sources_seen` / `proc_stat_malformed`。**ゾンビ数の field は無い。**

consumer:
- `check-receipt` の `_validate_attempt` (l.3904〜3955): `residual is not None` なら `_strict_int`; `accepted` なら `process_group_residual == 0 ∧ termination_verified` を要求 (semantic binding、l.3949)。receipt の bytes は束縛しない (整形し直しても通る)。
- test helper `_assert_launcher_returncode`: failed_predicates に `process_group_residual` / `termination_verified` を列挙。
- 残存が非 0 でも normal reap 経路では launcher は group を殺さない (killpg は forced-stop 経路だけ)。`escaped_process_containment = not_attempted`。

## 3. 生死 probe (login node、07:19 JST、`probe/probe-zombie-group.md`、`probe/probe-result-login.jsonl`)

| 条件 | leader 終了 50 ms 後の PGID 在籍 | `_group_member_count` | `_normal_reap` | worker `_verified_group_exists` |
|---|---|---:|---|---|
| ゾンビ孫、subreaper 無し | 0 件 | 0 | (0, True) | False |
| ゾンビ孫、subreaper 有り (prctl 36、回収せず) | 1 件 state `Z` | 1 | (1, False) | True |
| 実行中の孤児 (TERM 無視)、subreaper 無し | 1 件 state `S` | 1 | (1, False) | True |

読み: subreaper が無いこの 1 走では孫ゾンビは 50 ms 後に残存なし (回収者が init か既存祖先かは記録していない)。subreaper 祖先が回収しない限りゾンビが PGID に残り、現行計数は 1 と数える (F973 の機序)。本 wave の test はこの harness を再現手段として採用した (他の作り方の否定ではない)。

## 4. 負例の設計と現行の観測値 (焦点走、計算ノード、file 単体 216 test 並列: fix3 commit `238b8d998` 216 passed / 14.03 s `focus/focus-4-238b8d998.log`、fix2 `bf9ca498d` 216 passed / 11.90 s `focus/focus-3-bf9ca498d.log`、fix1 `2758e5eeb` 216 passed / 11.61 s `focus/focus-2-2758e5eeb.log`、test 追加 `29a07dbc0` 216 passed / 11.55 s `focus/focus-1-29a07dbc0.log`)

test は `orchestrator/tests/test_codex_worker_launch.py` の `test_t2620_*` 5 本。fake codex の mode `orphan_running` / `orphan_zombie` / `orphan_mixed` (正常 evidence の後に残存を作って rc 0 で終了、ゾンビは `/proc` の state が `Z` になるまで wait せずに poll)、subreaper harness `_write_subreaper_harness` (prctl 36 → launcher を子として起動し pid を file へ → launcher だけ `waitpid` → 終了後に `/proc` から養子 (ppid == harness) の state を記録 → 非 Z を SIGKILL → 全部回収 → stderr に `adoptees` / `reaped` / `unreaped` の JSON)。4 本とも harness 下で走らせ、外部真値は harness の `adoptees` から取る。観測値は 1 つの dict にまとめ 1 回の等値比較 (相談所見 B3)。test の finally は launcher・leader・child・zombie の pid を全部 SIGKILL し生存者を 1 回で assert する (レビュー所見 A2/B2)。

| 負例 | 作り方 | 経路 | `process_group_residual` | `termination_verified` | `accepted` | `outcome` / `stop_reason` | `launcher_rc` | `limit_trigger` | `codex_exit_code` | sidecar `final_count` | 外部真値 (harness `adoptees`) |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---|
| N1 生存子 | leader が TERM 無視の子を残し rc 0 | normal reap | 1 | False | False | not_accepted / max_attempts | 1 | None | 0 | 1 | 子 `S/R`、回収済み |
| N2a ゾンビ | leader が孫を `Z` にしてから rc 0 (wait しない) | normal reap | 1 | False | False | not_accepted / max_attempts | 1 | None | 0 | 1 | 孫 `Z`、回収済み |
| N2b 強制停止後ゾンビ (F973 再現) | `sigterm_ignore` (leader も子も TERM 無視) → wall 3 s | forced stop (`_terminate`) | 1 | False | False | not_accepted / wall_clock_admission_bound_s | 1 | wall_clock_admission_bound_s | -9 | 1 | 子 `Z`、回収済み、signal 列 SIGTERM→SIGKILL |
| N4 混在 | 生存子 1 + ゾンビ孫 1、rc 0 | normal reap | 2 | False | False | not_accepted / max_attempts | 1 | None | 0 | 2 | 子 `S/R` + 孫 `Z`、回収済み |
| N3 合成負例 | 受理済み receipt の `process_group_residual` だけを `null` / `1` に | check-receipt | — | — | — | — | — | — | — | — | checker rc 2 (`attempt.accepted semantic binding`)、元 receipt は rc 0 |

sidecar は 4 種とも `final_unknown_source None` / `proc_stat_malformed False`。`unknown_sources_seen` は焦点走 3 走では空だったが、並列負荷下で `proc_stat_read_error` (無関係 process の消滅) が一時的に入るので (§8)、test は「`proc_stat_read_error` 以外を含まない」の真偽値で固定する (fix2)。harness 4 例は `launcher_rc 1`、`unreaped []`。

## 5. Z 除外の実測 (変異 M1: `_group_member_count` の PGID 判定の直前に `if fields[0] == "Z": continue`)

出典: 変異本走 (計算ノード、test 追加 commit の `mutation/mutation-final-results-29a07dbc0.json` の M1 と job stdout `mutation/M1-job-stdout-29a07dbc0.txt`、fix2 commit の `mutation/mutation-final3-results-bf9ca498d.json`、fix3 commit の `mutation/mutation-final4-results-238b8d998.json`) と、fix1 commit での DW-O19 局所走 (login、07:57 JST、`mutation/o19-m1-local-pytest-2758e5eeb.log`、差分 `mutation/o19-m1.diff.txt`、復元後 porcelain 0)。観測値はすべて一致。

| 負例 | residual 現行 → M1 | verified 現行 → M1 | accepted 現行 → M1 | outcome / stop_reason (M1) | launcher_rc 現行 → M1 | sidecar final_count (M1) | 区別できる field |
|---|---|---|---|---|---|---:|---|
| N1 生存子 | 1 → 1 | False → False | False → False | not_accepted / max_attempts | 1 → 1 | 1 | 変化なし (拒否が続く) |
| N2a ゾンビのみ (正常終了) | 1 → **0** | False → **True** | False → **True** | **accepted / completed** | 1 → **0** | 0 | **無し** — receipt / sidecar とも clean な正常終了と同値。harness の `adoptees` は同時刻に `[[pid, "Z"]]` |
| N2b 強制停止後ゾンビ | 1 → **0** | False → **True** | False → False | not_accepted / wall_clock_admission_bound_s | 1 → 1 | 0 | `limit_trigger` (残存とは別の理由)。residual / verified は clean と同値 |
| N4 混在 | 2 → **1** | False → False | False → False | not_accepted / max_attempts | 1 → 1 | 1 | 残存数が 1 減るだけ (生存子 1 = N1 と同値)、拒否が続く |
| N3 合成負例 | — | — | — | — | — | — | 変化なし (checker は計数に依存しない、M1 で PASSED) |

M1 の局所走の結果: 5 本中 N2a・N2b・N4 が赤、N1・N3 が緑 (3 failed / 2 passed、16.64 s)。

## 6. 変異 matrix (新旧両走、DW-M08、`mutation/`)

| ID | 位置 (`tools/codex_worker_launch.py`) | 変異 | 旧 HEAD `b7f970dfa` (新 test 無し) | 新 test 側の期待 KILLED node | test 追加 commit `29a07dbc0` | fix1 commit `2758e5eeb` | fix2 commit `bf9ca498d` | fix3 commit (最終) |
|---|---|---|---|---|---|---|---|---|
| M0 | `_group_member_count` の `count = 0` | `count = int(0)` (等価、harness の SURVIVED 正例) | SURVIVED | (空) SURVIVED | SURVIVED | baseline 赤で中止 | SURVIVED | SURVIVED |
| M1 | 同 PGID 判定の直前 | `Z` を skip (= 除外案の代理) | SURVIVED | N2a, N2b, N4 | KILLED、完全一致 | 同上 | KILLED、完全一致 | KILLED、完全一致 |
| M2' | `_normal_reap` の return | 非 0 の残存を 0 / True に化ける | SURVIVED | N1, N2a, N4 | KILLED、完全一致 | 同上 | KILLED、完全一致 | KILLED、完全一致 |
| M3 | `_validate_attempt` の accepted 束縛 | `process_group_residual == 0` を削除 | SURVIVED | N3 | KILLED、完全一致 | 同上 | KILLED、完全一致 | KILLED、完全一致 |

各 run 32〜43 秒 (baseline 含め 5 run / 走、fix2 commit の baseline は 91 秒、M1 は queue 待ちを含み 402 秒)。旧 HEAD 側は 4 変異全 SURVIVED = 検出しているのは新 test だけ。fix1 commit の走は baseline (変異なし) が N2a・N4 の sidecar `unknown_sources_seen` で赤になり中止 (`mutation/mutation-final2-results-2758e5eeb-baseline-red.json`) — 自分起因の負荷依存で fix2 で解消 (§8)。

kill の意味 (DW-M03、レビュー所見 A3 の erratum): M1 のうち **N2a は受理集合の変化** (accepted False→True、launcher_rc 1→0)。**N2b と N4 は受理集合が変わらず、receipt field (`process_group_residual`、N2b は `termination_verified` も) の変化で赤になる** — DW-M08 の「構造化シグナルの pin」に当たり、診断文字列だけの赤ではない。M2' は 3 本とも受理集合の変化 (N1/N2a/N4 が accepted True / rc 0 へ)。M3 は checker の fail-closed (rc 2 → 0) の変化。事前登録 (`s4-ruling.md`) の「M1/M2' は受理集合が変わる」は N2b/N4 について不正確だったので、ここで訂正する (期待 node 集合は不変)。

## 7. 裁定パッケージ (ユーザーへ)

争点: `_group_member_count` が state `Z` を残存から除くか (T-2620、D2044 項 21 の続き)。

| 択 | 内容 | 得るもの | 失うもの |
|---|---|---|---|
| (a) 在籍数の契約を維持 (現状) | 変更なし | subreaper 化・reparenting の変化を receipt が検出する (F973 で実際に検出した)。回収不全が残存として見える | reparenting を変える将来の変更 (T-2622 の subreaper 案) は、計数側を変えない限りゾンビの窓で赤になる |
| (b) Z だけ除外 | M1 と同じ 2 行 | 「残存 = 実行中」の契約に近づき、subreaper 下でも正常終了が受理される | 回収不全の情報が receipt から消える (N2a が clean と同値、§5)。`X`/`x` は残る。受理集合が広がる (規律 2 の射程、裁定必須) |
| (c) 非 Z 残存数と Z 数を分けて記録 | `process_group_residual` は据え置き、sidecar (または receipt) に `zombie_count` を足す。受理条件を非 Z に結ぶかは別途 | 区別を保ったまま (b) の契約へ移れる。D705 (占有検査は zombie を非占有としつつ件数を保持) と同型 | field 追加 = schema 改版、consumer (`check-receipt`、`_assert_launcher_returncode`) の更新、test の pin 更新 |

推奨: (c) を採るなら受理条件の変更は別裁定にし、まず記録だけ足す (受理集合不変)。(b) は「回収不全を receipt から消してよい」という判断そのものなので、T-2622 の設計 (subreaper を再導入するか) と一緒に決めるのが筋。`Z`/`X`/`x` を除外する案は (b) の別形 (worker.py の `_CHILD_EXITED_STATES` は停止 handshake 用で、採用根拠にはならない)。先例 D464 / D705 は別 contract (生存者による排他 / cwd 占有) の参考であり、本件の採用根拠ではない。

## 8. 限界・未実測 (レビュー所見 A4/A5)

- 「読取不能」の e2e は作れていない (hidepid 無し)。consumer 側の合成負例 (N3) と既存 unit test で代替。
- transient ゾンビ (subreaper 無しで init が回収するまでの窓) が受入負荷で期限まで残るかは未実測。F973 の 44 走緑は subreaper 無しの安全証明ではない。probe は 50 ms 後の観測。
- 3 語 (実行中・読取不能・回収不全) は相互排他の分類ではない。`T`/`t`/`D`/`X`/`x`、PID namespace は実 process で再現していない (code 上は現行も M1 も数える)。
- 受入負荷 (48 worker、3 shard) での決定性は 1 走 (land の受入) だけ。焦点走 4 走 (計算ノード、file 単体 216 test 並列)、変異 baseline 2 走 (緑 2、赤 1 = fix2 前)、局所走 1 走。期限ごとの赤になる条件 (焦点再レビュー S1):

| 期限・窓 | fix 後も赤になる条件 |
|---|---|
| fake の PID 登録・Z 確認 poll 各 5 秒 | 期限までに子の起動 / 孫の Z 化が進まなければ rc 66 (N4 は 2 つの待機が直列) |
| 正常系 `max_wall` 10 秒 | 起動・I/O・2 つの poll の累積で正常終了前に limit が発火すると `limit None` / rc 0 の前提が崩れる |
| N2b `max_wall` 3 秒 | 既存 `sigterm_ignore` と同じで readiness handshake が無い。TERM 無視・子生成・PID 登録の前に limit が発火すると rc -9 / 残存 1 / 回収 pid の期待が崩れる |
| launcher の `_wait_for_group_exit` 0.5 / 1.0 秒 | harness が Z を保持するので回収との競争は無い。**期限を越えた最後の走査が `None` (無関係 process の消滅) なら final unknown → 不受理** (下記) |
| harness の回収上限 3 秒 | SIGKILL 後も子が waitable にならず期限後の `waitpid` が 0 を返せば終了 (`unreaped` に残る) |
| test の finally の消滅待ち 3 秒 (全 pid 共通) | 外部祖先の回収保留・停止の遅延で登録 pid が残れば赤 |
| 外側 timeout 20 秒 | 起動・走査・launcher 終了・harness 回収の累積超過。この経路では harness が先に SIGKILL され、養子の回収は次の祖先 (通常 init) に落ちる (焦点再レビュー F2、本 wave では直さない) |

- prctl の fork 非継承は code の前提であり読み戻して検査していない (harness は独立 process なので兄弟 test の孤児を引き取る祖先関係にはならない)。回収を保留する祖先 subreaper が居る環境では finally の消滅待ちが赤になりうる (現行の計算ノード job には無い、F973 で撤去済み)。
- 故障注入 (launcher timeout・receipt 不在・rc 97) の実走はしていない (finally の経路は静的レビューのみ)。回収済み pid への再 SIGKILL は OS の pid 再利用窓 (20 秒以内) で別 process を止めうる (nit、発生証拠なし)。養子の列挙は 1 回で、養子が生きた孫を持つ構造 (本 wave の fake には無い) は対象外。
- **一時 unknown の実測と、現行 launcher の負荷依存の潜在的な偽拒否 (scope 外、記録のみ):** fix1 commit `2758e5eeb` の変異 baseline (計算ノード、216 test 並列、`mutation/mutation-final2-results-2758e5eeb-baseline-red.json`、job stdout `mutation/baseline-red-job-stdout-2758e5eeb.txt`) で N2a・N4 が sidecar `unknown_sources_seen: ["proc_stat_read_error"]` により赤になった (final_count は正しい)。test 側は fix2 で `unknown_sources_seen` を「`proc_stat_read_error` 以外を含まない」の真偽値に正規化し、`final_count` / `final_unknown_source` / `proc_stat_malformed` の逐語固定は維持した。code 上の含意: `_wait_for_group_exit` の**期限到達時の走査**で無関係な process の消滅に当たると `residual = None` → `termination_verified False` → 不受理 (launcher_rc 1) になりうる。窓は最終 poll 1 回分 (ms 級) で、本 wave では観測していない (途中 poll だけ)。ゾンビ除外の争点とは独立で、直すなら別起票 (走査を PGID の候補 pid に絞る、ESRCH を「消滅」として扱う等)。

## 9. 工数・再現

- codex 8 本 (consult 1 = 7 call / 178 s、author 1 = 4 分、review 2、fix 3 (各 2〜4 分)、焦点再レビュー 1)。計算ノード job: 焦点走 4、変異 5 走 (旧 HEAD 1、新 4 のうち fix1 commit は baseline 赤で中止、各 ≤ 5 run)、provenance 監査 3、受入 1 (land)。login: probe 1、DW-O19 局所走 1。段 6 は fix 3 巡 (DW-O16 の上限) で、fix3 後は焦点再レビューを重ねず親の焦点走と変異で閉じた。
- 再現: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_worker_launch.py -k t2620 -q -rf`。Z 除外の観測は `mutation/mutation-spec-final.json` の M1 を `tools/mutation_worktree.py` で (`s4-ruling.md` の登録どおり)。
