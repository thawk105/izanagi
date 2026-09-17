## 変更した file と差分の要約

変更は指定された次の 2 file のみです。合計 **464 行追加・36 行削除**。commit は作成していません。

- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_real_repo_serialization.py`

`git diff --check` は通過しました。

## gate の実装 (conftest)

- `.gate` の open に既存 `_open_real_repo_lock` を再利用。
- fresh reader は fork reset 後、process の保持 state が空の場合だけ、全対象 gate を SH で検査して即解放。
- fresh writer・昇格 writer は gate EX → main EX → gate 解放。昇格前に main SH を明示解放。
- gate fd を取得中だけ `state.gate_fd` に登録し、例外経路でも close。fork reset は継承 fd を unlock せず close。
- reader 検査と最初の resource、writer の gate/main は deadline を共有。245.0／0.05、安全検査、取得順、降格処理は維持。

変更前は、既存 reader と共有可能な新規 reader が入り続け、writer は reader が途切れるまで待ちました。変更後は、fresh writer・昇格 writer が gate を保持している間、何も保持していない fresh reader が gate で待ちます。

## test の実装と既存 test の更新

- N1／N2：legacy 競合と、異なる legacy・共通 common の競合を検証。別 process の production 経路で要求・競合・取得・解放を通知します。
- P1：A 解放前の B 取得通知で SH overlap を検証。
- P2：第三者 gate 保持下の昇格待ち、先行 SH 解放、gate 保持下の降格・入れ子 reader、fd 同一性・参照数・最終 state 空を検証。
- 境界：writer／reader の deadline 共有、3 種の失敗時 fd cleanup、取得中 fork の継承 fd cleanup を追加。
- 既存模擬：path→fd 対応と gate EX 成功による cohort 入場停止へ更新。main 取得時刻は legacy=6、common=9。UN／close の順と定数 literal を固定。
- closure mutation 群の期待値は変更不要でした。

## 実走結果 (nodeid と結果、未実走の列挙)

指定された `PYTHONPATH=. python3 -c "...pytest.main(...)"` 形式で実走しました。

**最終焦点走：22 passed、84 deselected、8.17 秒。skip／error はありません。**

以下はすべて `orchestrator/tests/test_real_repo_serialization.py::` が接頭辞です。

| nodeid | 結果 |
|---|---:|
| `test_real_repo_writer_drains_overlapping_reader_stream[legacy/common]` | 2 passed |
| `test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy/common]` | 2 passed |
| `test_real_repo_readers_overlap_without_writer` | passed |
| `test_real_repo_gate_and_main_share_deadline[writer/reader]` | 2 passed |
| `test_real_repo_gate_timeout_closes_fds[gate-timeout/main-timeout/open-rejected]` | 3 passed |
| `test_real_repo_fork_reset_closes_inflight_gate_fd` | passed |
| `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` | passed |
| `test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture` | passed |
| `test_real_repo_closure_mutations` | 全 9 parameter passed |

初回の構文エラーと、新設した fixture 参照数 assert の誤りは修正済みです。

file 全走、所有外 consumer test、受入全走、`test_protocol_builder_repo_tree_guard_is_wired_to_real_root` は未実走です。今回の緑には含めません。

## 変異 M0〜M6 の anchor と killer node

anchor はすべて `conftest.py` 内。変異後は元の本文へ復元しました。

| ID | anchor／変異 | 実測 |
|---|---|---|
| M0 | L1360 `# Writers hold the gate only while acquiring main; fresh readers` の comment のみ変更 | **SURVIVED**。N1／N2 の 4 node 通過 |
| M1 | L1491 `if not _REAL_REPO_PROCESS_LOCKS:` → 検査省略 | **KILLED**。N1 `[legacy]`／`[common]` |
| M2 | L1362 `if target_mode == "write":` → `and not created` | **KILLED**。N1 両 parameter、既存 priority 模擬 |
| M3 | 同 anchor → `and created`。昇格の UN・gate を省略 | **KILLED**。N2 両 parameter |
| M4 | L1378–1379 の `state.fd,` に続く `deadline=deadline,` → 現時刻＋timeout | **KILLED**。deadline test `[writer]`／`[reader]` |
| M5 | L1387 `os.close(state.gate_fd)` を例外経路だけ省略 | **KILLED**。cleanup test `[main-timeout]` の EBADF 検査 |
| M6 | L1491 の保持なし条件 → 常時検査 | **KILLED**。P2 fixture 昇格 test |

M6 は killer が実測できたため登録可能です。

## 波及可能性の静的列挙

- `_real_repo_locks`：conftest の receipt／oracle prewarm、`_acceptance_timed_real_repo_locks`、fixture context が直接 consumer。protocol 経由で `REAL_REPO_ACCESS_BY_NODE` の全登録 node に波及します。
- `_real_repo_file_lock`：`_real_repo_locks` と serialization test が直接 consumer。
- `_RealRepoProcessLockState`：同 process 互換判定、path context、fork reset、serialization test の状態検査が consumer。
- `real_repo_fixture_lock`：
  - `test_s8c_preregistration_invariant.py` の `repository_candidate_commit`
  - `test_s8c_preregistration_predicates.py` の `current_commit_snapshot`／`repository_candidate_commit`
  - `test_campaign_import_invariant.py` の `repository_scan`
  - 上記 fixture を利用する consumer test 全体
- `test_run_tests_shards.py`：lock context の差替え、取得・解放失敗時の非記録、interval 記録順序を検査しています。未変更・未実走です。
- `tools/acceptance_shards.py::record_real_repo_lock_interval`：記録開始は全 lock 取得後、終了は解放後のままです。追加した gate 待ちは取得前待機に含まれ、記録形式は変わりません。

## 未完・懸念

指定された実装・焦点検証は完了しています。所有外 consumer と受入全体の検証は親側に残ります。

FIFO、公平性、gate 取得前からの厳密な優先、旧コード reader に対する飢餓防止は保証しません。昇格失敗後の既存 state 不整合と一般的な multithread fork 問題は裁定どおり scope 外です。

## 総括

指定 2 file に実装を残しました。焦点走 **22 件通過**、M0 は生存、M1〜M6 は赤化を確認し、変異は復元済みです。commit・統合・受入全走は未実施です。
