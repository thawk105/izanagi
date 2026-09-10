## 所見 1

- (a) `configuration_id`、`holdout_id`、`retry_ordinal` が、adapter 発行時と replay 時に実際の v2 slot へ再束縛されていない。
- (b) [s8b_terminal_evidence.py:713](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:713) は呼び手の `reservation.slot_id` と照合するだけで、[s8b_attempt_registry.py:1324](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_registry.py:1324) の durable 再検査対象は `cell_id`、`records`、`threads` などに限られる。[同:1340](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_registry.py:1340) は claim と slot を照合するが、証拠内の三 field を slot と比較していない。
- (c) 契約 1.5 (a) は三 field の権威を v2 slot に置く。実装では、実 slot の binding、attempt、schedule digest を使いながら、偽の `reservation.slot_id` で異なる三 field を持つ draft を作れてしまい、adapter の検査を通過できる。帳簿 identity の虚偽が proof chain に入る。
- (d) `_assert_terminal_durable_identity()` で `campaign_record.configuration_id == slot.configuration_id`、`holdout_id == slot.freeze_holdout_key`、`retry_ordinal == slot.attempt_ordinal` を明示検査し、発行時と durable replay の双方に移植負例を置く。
- (e) 重大度 — `blocker`

## 所見 2

- (a) `failure.stage == "capture"` と非ゼロ `launch_failures_count` の矛盾を証拠 validator が受理する。
- (b) [s8b_terminal_evidence.py:500](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:500) の相互整合検査は、failure 時の計測不在と `exec_failures == reps_expected`、および [同:526](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:526) の `launch_failures_count > 0 ∧ exec_failures == 0` だけを検査している。
- (c) 契約 1.2 は capture failure なら `launch_failures_count == 0` と明記する。副作用なしの直接 probe では、capture failure、count 1、exec failures 3、reps 3 の文書が受理された。矛盾した draft を adapter が昇格できる。
- (d) `_assert_mutual_consistency()` に capture stage 専用の count 0 検査を追加し、leaf と durable replay の両方で正負対を置く。
- (e) 重大度 — `blocker`

## 所見 3

- (a) v2 の正当な pre-probe 競合枝が、ScalePoint 座標検査で terminal 化前に拒否される。
- (b) [s8b_floor_attempt_launcher.py:915](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:915) で競合時は capture を省略するため measurement は `None` になるが、[同:963](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:963) から [同:977](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:977) は `failure is None` のため `None` の座標を検査して例外を送出する。
- (c) 契約 4.1 の枝 1と 5.2 の観測前競合形は `measurement_environment_conflict` の sealed terminal になる必要がある。現状は durable classification 後に launcher error となる。
- (d) 座標検査を「capture を実行した failure 無しの経路」に限定し、pre-probe competing の統合正例を追加する。
- (e) 重大度 — `must-fix`

## 所見 4

- (a) `OSError` のサブクラスが契約の exact 3 語へ正規化されず、捕捉済み terminal が leaf で拒否される。
- (b) launcher は [s8b_floor_attempt_launcher.py:929](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:929) で `OSError` 全体を捕捉するが、[同:429](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:429) は Timeout だけを正規化する。[s8b_terminal_evidence.py:320](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:320) は exact 3 語以外を拒否する。直接 probe でも `FileNotFoundError` と `PermissionError` はそのまま残った。
- (c) Python の `except OSError` はこれらのサブクラスを含む。契約 4.2 の launcher 捕捉値域と evidence の受理値域が一致せず、正当な枝 2 が terminal 化できない。
- (d) v2 では `subprocess.TimeoutExpired`、`OSError`、`RuntimeError` の順に `isinstance` で exact 名へ正規化する。代表的な `OSError` と `RuntimeError` サブクラスを検査する。
- (e) 重大度 — `must-fix`

## 数値・pin・consumer の確認

- `campaign_record`: 証拠側 30、`_JOURNAL_KEYS["session"]` 30、集合等値。
- draft binding: exact 9。三 digest key との積集合は空で、null ではなく欠落。
- validated binding: exact 12。
- digest 綴り: `classification_receipt_sha256`、`classification_event_sha256`、`observation_event_sha256`。行側だけ `observation_start_event_sha256` で、[s8b_attempt_profile.py:614](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_profile.py:614) が明示対応している。
- E2: exact 4 語。v1 retryable 集合は 0。
- v1 terminal は 24 key、v2 terminal は 27 key、差集合は指定の 3 key。
- E1 自体の枝順は [s8b_terminal_evidence.py:469](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:469) で契約順。`assess_session` には [同:455](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:455) から元の `reps_expected` を渡している。opened の和の不変条件も [同:513](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:513) にある。
- 既存 8 file の base と HEAD の whole-file SHA-256 を tracked tree 全体で検索し、golden hit は双方とも各 0。
- perf semantic inventory は実測 43 file 対 reviewed 43 file で集合等値。新 leaf は inventory に入っていない。
- reflux AST は `aborted=False` keyword 0 件、`OriginSealed(False, ...)` 0 件。
- claim v4、`_AttemptState.mode`、core 公開 API への capability 引数追加は 0 件。
- 新 test basename は insight 文書以外の登録簿に出現しない。`pytest.ini:13` の test tree 収集対象には自動的に入る。acceptance ledger entry は 0 だが、[conftest.py:1534](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/tests/conftest.py:1534) が未知 duration を許容するため登録漏れによる非収集ではない。それ以外の登録簿は見つからなかった。
- 既存 test の削除は、許可された `test_v2_profile_is_rejected_before_any_registry_side_effect` の置換だけ。もう一つの許可箇所だけが E2 期待値を反転している。その他は callback 引数追加、必須 fixture field 追加、検査追加であり、skip、xfail、golden 更新、期待値緩和はない。

## 総括

- 判定: `no`
- pytest は制約どおり実行していない。静的検査と副作用なしの関数 probe のみ。

| 契約条項 | 判定 | 主な担い手 |
|---|---|---|
| 1.1 | 担い手あり | `s8b_terminal_evidence.py:92-199,754-850`; `s8b_attempt_registry.py:3220-3228` |
| 1.2 | 条文と相違 | `s8b_floor_attempt_launcher.py:534-657,909-1024`; capture/count 不変条件欠落 |
| 1.3 | 担い手あり | `s8b_terminal_evidence.py:75-91`; `s8b_attempt_profile.py:611-616` |
| 1.4 | 担い手あり | `s8b_terminal_evidence.py:447-458,513-514,624` |
| 1.5 | 条文と相違 | `s8b_terminal_evidence.py:92-167,713-723`; adapter の三 identity 再束縛欠落 |
| 2 | 条文と相違 | `s8b_terminal_evidence.py:500-527`; capture/count 矛盾を受理 |
| 3 | 担い手あり | `s8b_terminal_evidence.py:15-18,619-622` |
| 4.1 | 条文と相違 | E1 は `s8b_terminal_evidence.py:469-498`、統合経路は launcher `:971-977` で枝 1 を遮断 |
| 4.2 | 条文と相違 | launcher `:420-435,929-932`; leaf `:60-64,320-322` |
| 4.3 | 担い手あり | `s8b_attempt_profile.py:539-552`; leaf `:492-498` |
| 5.1 | 担い手あり | `attempt_registry_core.py:197-219,1449-1453`; `s8b_attempt_profile.py:717-746` |
| 5.1.1 | 担い手あり | `attempt_registry_core.py:1086-1110` |
| 5.3 | 担い手あり | `attempt_registry_core.py:1077-1085,1111-1118` |
| 5.4 | 担い手あり | `s8b_attempt_profile.py:494-507`; `attempt_registry_core.py:2097-2114` |
| 6.1 | 担い手あり | `s8b_terminal_evidence.py:75-91,541-582`; `s8b_attempt_registry.py:1137-1185` |
| 6.2 | 担い手あり | `s8b_attempt_registry.py:282-318`; launcher `:1047-1100` |
| 6.3 | 担い手あり | `s8b_terminal_evidence.py:541-582,859-873`; adapter `:1382-1389` |
| 7 | 担い手あり | `s8b_attempt_registry.py:1128-1134,1394-1458,2114-2149,3211-3228`; profile `:603-625` |
| 8 | 担い手あり | claim 定数 `s8b_attempt_registry.py:54-56`、`_AttemptState :166-187`、core API 差分 |
| 9 | 担い手あり | leaf docstring `:9-18`; launcher perf gate `:624-647`; semantic inventory 集合等値 |

呼出し閉包の実測値:

- `_atomic_update_locked`: production 2。報告値 2 と一致。
- `_atomic_update`: production 7。報告値 7 と一致。
- `_atomic_update_with_consumption_marker`: production 2。報告値 2 と一致。
- transition callable: production 7、test 4、合計 11。報告値と一致。
- core `record_attempt_terminal`: production 4、test 6、合計 10。報告値と一致。production には adapter の 3 call と `trial_registry.py:3442` の関数値 consumer を含む。
- `DomainProfile`: production constructor 4、test constructor 0。
- `_assert_null_matrix`: production 1、test 4。
- adapter 自身の `record_attempt_terminal`: production consumer 1、test consumer 2。公開 signature は不変。

重大度件数:

- blocker: 2
- must-fix: 2
- nit: 0