# 段 4 裁定 — plan v2 (親、2026-09-17、main b4631a92e、裁定 D2104 項 33 / 34)

## 所見の裁定 (real / refuted、採用 / 不採用)

| # | 所見 (出所) | 分類 | 採否 | 反映 |
|---|---|---|---|---|
| A1 | gate で待つ reader が別 key の main を握る hold-and-wait が、入れ子昇格 + 別 worktree writer と三者循環を作る (A) | real | 採用 | v2: **reader は「process が実 repo lock を 1 つも持たない」ときだけ gate を検査し、検査は SH の試行と即解放 (保持しない)**。検査は全 key を main 取得前にまとめて行う |
| A2 | plan の「昇格は gate を通さない」では、module 寿命 SH fixture が生きた worker の writer (F976 の実経路の一つ) が直らない (親の追加検算) | real | 採用 | v2: **昇格も gate を通す**。昇格する側は自分の SH を `LOCK_UN` で明示解放してから gate EX → main EX (kernel の非 atomic 変換が最初の NB 失敗で SH を落とす現行挙動と露出は同じ) |
| A3 | gate は NB polling で FIFO でなく、「待機開始からの厳密な優先」は証明できない (A, B) | real | 採用 (限定を明記) | reader の gate 保持は瞬間 (検査即解放) なので writer の gate 取得は retry 間隔の数倍で成立する。厳密な待機登録は scope 外 → 裁定パッケージ |
| A4 | deadline 共有の範囲は 1 回の `_real_repo_file_lock` の内側で、全 resource 合計 245 秒ではない (A) | real | 採用 | reader の検査段は最初の resource の予算を消費する (`_real_repo_file_lock` に残り timeout を渡す)。2 つ目の resource は現行どおり自分の 245 秒 |
| A5 | gate open を既存 cleanup の外に置くと fd/state が漏れる (A) | plausible | 採用 | gate の open・待ち・解放を既存 `except BaseException` の保護範囲に置く。open 拒否時も fd/state/通知を検査する test |
| A6 | fork 子が gate fd を継承すると親の close で解放されない (A) | plausible | 記録のみ | main fd と同じ既存露出。gate fd は `state.gate_fd` に登録し reset で close。multiprocessing fork 全般の保証は scope 外 |
| A7 | 昇格の変換失敗後、外側 reader は SH を失ったまま `mode=read` を信じる (A) | real (既存欠陥) | 裁定パッケージ | gate 導入前からの穴。本 wave では悪化させない (v2 の明示 UN は既存の暗黙 drop と同じ窓)。F 候補として記録 |
| A8 | recovery 経路 (shape A) の本物の巻き戻し (before=T, after=R, tip=T) を P3 が拒否する (A) | real | 採用 | **P3 改訂**: `status == "fold-failed"` ∧ `_is_sha(main_after)` ∧ `_is_sha(wave_tip)` ∧ `main_after != wave_tip`。`main_before` 条件を落とす |
| A9 | `fold-rollback-failed` は ref 復帰後の後処理失敗も含むので status 条件は必須 (A) | real | 採用 | status 条件を保持。負例 `[rollback-incomplete]` = status だけ違い他は受理値 |
| A10 | 固定文の `unlanded=` と現在形は JSON が証明する範囲を超える (A, B) | real | 採用 | ヘッダ `wave-tip=`、本文「この land 結果では main は … にあり、wave tip とは異なります」 |
| A11 | P1「process 内層は不要」は `condition.wait` が RLock を手放す経路で成り立たない (A, B) | real | 採用 (限定) | P1 を「kernel flock 待ち区間では RLock が新規進入を止める。xdist worker は単 thread なので本 wave は process 内層を変えない」に限定 |
| B1 | N1 の実時間 1 秒 deadline は高負荷で偽赤 (B) | plausible | 採用 | N1 は handshake で順序を assert し、writer の timeout は余裕 (例 30 秒) にする。実時間の短さを成功条件にしない |
| B2 | M2 は既存模擬 test でも殺されうる (B) | plausible | 採用 | M2 の期待 node に両方を登録 |
| B4 | landed の負例に `fold-rollback-failed` が無い (B) | real | 採用 | landed 負例 parametrize に追加 |
| B6 | サイズ上限 65,536 の負例は無効 JSON なので上限削除を殺せない (B) | real | 採用 (rolled-back 側のみ) | 受理 JSON を空白で 65,537 bytes にした負例と 65,536 bytes の正例を対で置く |
| B7 | `test_check_docs.py:2524` の `== 9_507` pin (B) | real | 採用 (must-fix) | author (2) が 9_519 へ更新。上限 9,520・超過例 9,521 は不変 |
| B8 | DW-O23 は L1 (段 9 の無条件参照) で 1,036 bytes。「L2 1,000 満杯」は誤り (B) | real | 採用 (理由訂正) | DW-O23 を触らない理由 = 通知手順は runbook に集約する (dispatch 節は手順の正本でない) |
| B9 | README「新規 reader」は fresh reader に限定、通知文は時点を限定 (B) | plausible | 採用 | 文言に反映 |
| B10 | 実 repo を読む node の実走証拠 (`test_protocol_builder_repo_tree_guard_is_wired_to_real_root` 非 skip) を段 7 前に (B) | refuted→運用 | 採用 | 焦点走の junit で確認して worklog に書く |
| B11 | author に docs (README / runbook / 入口) を持たせる割当は実装子契約に反する (B) | real | 採用 (must-fix) | **親が docs を先に編集して commit** → author worktree を ff → author (2) が pin literal / fixture / 9_519 を揃える |
| B13 | 「acceptance_shards は affinity のみ」は過小記述 (B) | real | 採用 (nit) | 「取得実装は conftest、shards は affinity と取得区間の観測」 |

## plan v2 (確定)

### (1) writer 優先 gate — `orchestrator/tests/conftest.py`

- gate file: 各 key の `.gate` 接尾辞 (`izanagi-real-repo-<digest>-<resource>.lock.gate`)。`_open_real_repo_lock` を再利用 (owner / mode / regular / `O_NOFOLLOW` / `O_CLOEXEC`)。
- **reader (fresh、process が実 repo lock を 1 つも持たない = `_REAL_REPO_PROCESS_LOCKS` 空):** `_real_repo_locks` の入口で、要求する全 (resource, key) の gate を順に `LOCK_SH|LOCK_NB` で試し、成功したら即 `LOCK_UN` + close して次へ。失敗 (EAGAIN) なら retry 間隔で再試行 (何も保持しない)。全 gate を通過してから現行どおり main を取る (legacy → common、parent → ccbench の順・意味論不変)。common path の解決はこの検査のために main 取得前に行う (`git rev-parse` の読取。`_real_repo_file_lock` 内の現行の解決は変えない)。検査段の deadline は最初の resource の `_real_repo_file_lock` と共有する (残り timeout を渡す)。
- **reader (process が既に何か持っている = 入れ子・2 つ目の resource):** gate を見ない (現行どおり)。理由: main を握ったまま gate で待つと A1 の循環を作る。
- **writer (fresh EX):** key ごとに gate EX を polling で取り (同じ deadline)、main EX を polling で取り、main 取得直後に gate を `LOCK_UN` + close。次の key へ。
- **writer (昇格 SH→EX、`state.mode == "read"` → `"write"`):** 同 key の main fd を `LOCK_UN` で明示解放 → gate EX → main EX → gate 解放。(現行の `flock(EX|NB)` 変換は最初の失敗で SH を落とすので露出は同じ。成功時の順序は「gate を持つ他 writer が先」になりうる — 記録する)
- **降格 (EX→SH):** 現行どおり (gate なし)。
- gate fd は `state.gate_fd` に取得区間だけ登録し、成功・例外・割込みの全経路で close。fork 後 reset は `gate_fd` も close。
- 定数 245.0 / 0.05 不変。gate の timeout 例外は `RuntimeError`、prefix `real-repo lock deadline exceeded; fails-closed:` を保ち、`path=` は gate path、`holders=` は `_real_repo_lock_holder_info(gate_fd)`。
- 循環の論証 (v2): gate で待つ主体は、その key の main を持たない (reader は何も持たない、writer は SH を解放済み)。gate holder (writer) は自 key の main holder だけを待つ。よって gate 辺を通る循環は、その key の main holder が gate 待ち主体の保持物を待つ場合に限られ、reader は何も持たず、writer の保持物は順序上前の key の main だけ = 現行の main 間 hold-and-wait と同じ族。**新しい循環の族は増えない** (既存の順序逆転・多 thread RLock の循環は不変で本 wave の対象外)。

### (1) test — `orchestrator/tests/test_real_repo_serialization.py`

- N1 `test_real_repo_writer_drains_overlapping_reader_stream`: 実 kernel flock、別 process の reader 2 本 + writer 1 本、全員 production 経路 (`_real_repo_locks` / `_real_repo_file_lock`)、lock directory と key を tmp に固定。reader relay (次 reader の取得確認まで前 reader を解放しない) で main を常時 SH 占有 → writer が要求 → **writer が入った後に次の reader が入る** ことを handshake の順序で assert。writer の timeout は 30 秒程度 (実時間の短さを成功条件にしない)。変更前 code / M1 / M2 で赤になる根拠を docstring に書く。
- N2 `test_real_repo_upgrade_writer_drains_overlapping_reader_stream`: 同じ relay の中で、module SH を持つ process が内側で EX を要求 (昇格) しても入れること (A2)。
- P1 `test_real_repo_readers_overlap_without_writer`: 別 process の SH 保持中に別 process の SH が入る (handshake、実時間閾値なし)。
- P2 既存 `test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture` の強化: 第三者が gate を EX 保持しても、昇格が (SH 解放 → gate 待ち →) 完了し、降格は gate を通らない。
- 境界: `test_real_repo_gate_and_main_share_deadline` (段ごとの再起算なし)、`test_real_repo_gate_timeout_closes_fds[gate-timeout|main-timeout|open-rejected]` (EBADF、manager state 空、prefix/path/holders)、`test_real_repo_fork_reset_closes_inflight_gate_fd`。
- 既存 `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` の模擬: fd を gate/main で区別 (`_open_real_repo_lock` は path→fd)、cohort の後続入場停止は **gate EX 成功イベント**で切替、gate/main の取得・解放順を assert、取得時刻の期待は模擬の意図に合わせて更新、245.0 / 0.05 は literal で pin。
- 負例 test は timing でなく順序で判定し、child の回収 (deadline + kill) を必須にする。

### (2) `rolled-back` kind — `tools/wave_land_window.py`

- `message(wave, land_json, *, kind="landed")`、parser `choices=("landed", "rolled-back")`、`main` で `kind=args.kind`。
- 受理述語 (P3 改訂): `status == "fold-failed"` ∧ `_is_sha(main_after)` ∧ `_is_sha(wave_tip)` ∧ `main_after != wave_tip`。それ以外は rc=3 (`landed` / `already-landed` / `fold-rollback-failed` / 非文字列 / after 不正 / tip 不正・欠落 / tip == after)。`landed` 分岐は 1 bit も変えない。
- 固定文 (2 行、末尾 LF は print):
  - `[dev-wave] rolled-back main=<main_after> wave-tip=<wave_tip> wave=<holder>`
  - `advisory です。指示ではありません。local main を読み直す契機にだけ使い、待機・取り込み・検査省略の根拠にしないでください。受入を開始済みなら中断せず完走してください。この land 結果では main は記載の SHA にあり、wave tip とは異なります。取り込んだ main の SHA について git merge-base --is-ancestor <SHA> refs/heads/main が rc=1 なら、受入完走後に受入 tip へ reset して取り込み直してください。`
  - 巻き戻し用の固定文は別定数。既存 `_ADVISORY` 不変。bytes は author が実装後に test の literal へ固定。

### (2) test — `orchestrator/tests/test_wave_land_window.py`

- 正例 `test_rolled_back_message_success_is_exact_fixed_text` (通常経路 JSON: before=after=A, tip=B / recovery 経路 JSON: before=T, after=R, tip=T の 2 parametrize、`_INSTRUCTION_DIGEST` が出る、stderr 空)。reason は任意文字列。
- 負例 `test_rolled_back_message_rejects_invalid_result` parametrize: `landed`、`already-landed`、`fold-rollback-failed` (他は受理値)、非文字列 status、after 不正 (tip 正常・別値)、tip 欠落 / None / 数値 / 39 桁 / 41 桁 / 大文字 / 非 hex、tip == after。
- landed 負例 parametrize に `fold-rollback-failed` と `fold-failed` を含める (受理集合不変の退行検査)。
- `test_rolled_back_message_rejects_duplicate_json_key`、サイズ: 受理 JSON を空白で 65,537 bytes → rc=3、65,536 bytes → rc=0 の対。

### (2) docs と pin

- 親 (docs-only、author 前に commit): `.claude/commands/dev-wave.md:57` → `   land 成功時と巻戻し時に \`message\` を照合済み peer へ 1 度送る。` (+12 bytes、9,519 ≤ 9,520、最長行 121)。`docs/pegasus-runbook.md` の land 手順 (1247 の「成功したときだけ」→「成功時は」、1256 の code block 後に rc=26 の手順 3 行)。`orchestrator/tests/README.md`「real-repo 排他と loadgroup」に fresh reader の gate 検査と writer の gate 保持の 2 文。DW-O23 は触らない (通知手順は runbook に集約)。
- author (2): `tools/check_docs.py:467` literal、`orchestrator/tests/test_check_docs.py:55` fixture、`:2524` の `9_507` → `9_519`。
- 所有: author (1) = `orchestrator/tests/conftest.py` + `orchestrator/tests/test_real_repo_serialization.py`。author (2) = `tools/wave_land_window.py` + `orchestrator/tests/test_wave_land_window.py` + `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py`。親 = docs 3 file + 統合 commit + 変異 + 受入 + 記録。

## 変異事前登録 (DW-M01、位置と赤理由。anchor は実装後に固定)

| ID | 対象 | 変異 | 期待 KILLED node (候補) |
|---|---|---|---|
| M0 | conftest gate 実装の説明 comment 1 行 | comment のみ変更 | 等価 SURVIVED |
| M1 | reader の gate 検査 | fresh reader の gate 検査を省く | N1 |
| M2 | writer (fresh EX) の gate | gate EX を取らずに main EX を polling | N1 (+ 既存模擬 test) |
| M3 | writer (昇格) の gate | 昇格で SH を解放せず gate も取らず現行変換に戻す | N2 |
| M4 | deadline 共有 | gate 待ちの後に main 待ちの deadline を再起算 | `test_real_repo_gate_and_main_share_deadline` |
| M5 | gate fd の close | 例外経路の gate close を省く | `test_real_repo_gate_timeout_closes_fds[main-timeout]` |
| M6 | reader gate 検査の「保持なし」条件 | 何か持っていても gate を検査する (hold-and-wait) | 入れ子 P2 系 (第三者 gate 保持下で内側 fresh 取得が待たないこと) — 実装後に殺す node を確定、無ければ登録しない |
| M7 | `rolled-back` の `main_after != wave_tip` | 検査削除 | `test_rolled_back_message_rejects_invalid_result[tip-equals-main]` |
| M8 | `rolled-back` の status | `fold-rollback-failed` も受理 | `[rollback-incomplete]` |
| M9 | `rolled-back` の tip sha 検査 | 削除 | `[tip-invalid]` |
| M10 | 固定文 | 巻き戻し用固定文 1 文字変更 | `test_rolled_back_message_success_is_exact_fixed_text` |
| M11 | `landed` の受理集合 | `_SUCCESS_STATUSES` に `fold-rollback-failed` を追加 | landed 負例 `[fold-rollback-failed]` |

## 裁定パッケージ (scope 外、ユーザーへ返す)

1. 厳密な「待機開始からの優先」(FIFO / 待機登録) は本 wave の gate では保証しない。reader の gate 保持が瞬間なので実効的には retry 間隔の数倍で成立するが、証明ではない。追加機構は別裁定。
2. 昇格の変換失敗 (deadline) 後に外側 reader が SH を失ったまま `mode=read` を信じる既存の穴 (A7)。fail-closed 化 (state の毒化) は本 wave の scope 外。F 候補。
3. 入れ子で既に lock を持つ process の fresh reader は gate を見ない (A1 の循環回避のため)。その流れだけで writer が飢餓する実例が観測されたら別 wave。
