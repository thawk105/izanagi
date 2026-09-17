## 変更前の受理・拒否挙動

initial・provenance 後・fold gate 後で累積 180 秒の lock 待機予算を共有し、再取得失敗時は証拠を破棄して `RC_LOCK_BUSY` を返していました。無関係 child も open・admin binding 検証の対象でした。active fold の recovery は元 request の origin を照合し、provenance を起動しない経路でした。

## 実装の要約 (関数・行)

編集は指定の 2 ファイルだけです。commit は作成していません。

[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py:305)：

- 970／1190：受入検証を static／locked authority に分割。
- 1662：protected child だけを open・binding 検証。
- 2780〜3118：FD 生存判定、seq 継承、非横取り grant、原子的引渡し、死亡票の完了照合。
- 4626：runner を一度だけ実行し、成功 payload を順番期限まで保持。非ゼロ provenance は即終端。
- 5134／5319・5348／6200：apply／shape B／ff 直前の所有確認。
- 5506：`land()` へ登録・順番待ち・二層予算・終端処理を接続。

[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py:3540)：

- 指定の land 側 node、死亡票照合、recovery、非接触、TTL 跨ぎ CLI test を追加。
- 3980：thread＋token scheduler。監査・gate の実 callable は main thread で実行する構成。
- receipt path を request ごとに分離。scheduler 内の acceptance wave も一意化。
- **すべて実装済み・未実走です。**

## 変異 anchor 表 (M0〜M13 → 実装後の位置)

以下の行は `tools/dev_wave_land.py`。KILLED 判定は未実施です。

| ID | 実装後の anchor |
|---|---|
| M0 | 2617 `_land_lock_now` |
| M1 | 5597 `land` の `_wait_land_turn` |
| M2 | 2906 `_register_land_turn` の既存 seq 継承 |
| M3 | 2780 `_turn_live` |
| M4a | 6200 ff 前 `_land_turn_mutating` |
| M4b | 5134 apply 前 `_land_turn_mutating` |
| M4c | 5319／5348 shape B の `before_mutation` |
| M5 | 2844 `_turn_select`、3001 `_observe_dead_land_turn` |
| M6a／b | 4626 `_run_outside_land_lock`、3118 `_acquire_land_lock_until_turn` |
| M7a／b | 5702／5986 fingerprint 比較 |
| M8 | 1724 protected でない child の `continue` |
| M9 | 3190 `_verify_land_lock_binding` の自 wave inode 比較 |
| M10 | U2 所有。cleanup の実装後位置は未確認 |
| M11 | 5575 登録前 `_verify_acceptance_static` |
| M12 | 2997 `_finish_land_turn` の同一更新内引渡し |
| M13 | 4636 非ゼロ provenance の早期終端 |

## 実走した test と結果

**pytest 子プロセスは一度も開始されていません。**

次を `tools/run_tests.py` 経由で試行しましたが、すべて `qstat -Q preflight rc=1`、runner rc=16、`child_started=false` でした。

- `test_dev_wave_land.py::test_provenance_gate_accepts_tip_zero_and_lands`
- `test_dev_wave_land.py` 全体と、`test_plain_runner_coverage.py`／`test_pytest_collection_config.py`／`test_flaky_test_holds_contract.py`
- `test_dev_wave_land.py --collect-only`

成功した検査：

- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 両編集ファイルの構文検査・import 確認
- `git diff --check`

import 確認では test 関数を実行していません。

## 既存 test の期待値変更

- 非接触の指定 5 test を成功期待へ変更し、名前・説明も更新。
- lock timeout と累積待機 test の reason・取得回数・結果を二層予算へ更新。
- 自 wave 差替え・incoming 衝突の拒否期待は維持。
- `test_exploration_external_root_keeps_wave_clean` は改名していません。

## 所有外 caller と波及

- `tools/acceptance_shards.py:46,218`、`test_run_tests_shards.py:1993`：`_CONTROL_CONTAINERS` は不変更。
- `tools/check_docs.py:789`：helper path 契約は不変更。checker は成功。
- `tools/dev_wave_wait.py`、window／wait／cleanup consumer tests：未実走。
- 共有 `_Repo` fixture：receipt ファイル名の生成方法が変更。
- `acceptance_duration_ledger.json`：改名した 5 node の旧名が残っています。所有外なので未編集。
- spool fold／fold gate／recovery consumer tests：追加検証が必要です。

## 未了・赤の内訳

- 実走不能の原因は dispatch infrastructure failure です。テスト本体の赤とは区別しています。
- 既存の `test_provenance_checker_infrastructure_rc_is_retryable_and_retains` と `test_provenance_checker_signal_returncode_is_retryable_and_retains` は、新裁定の「非ゼロ payload は非 retryable」と期待が不一致です。指定された期待値変更範囲を越える flags の変更は行っておらず、**赤が見込まれますが未実走**です。
- 旧 tree probe、変異検査、全走、scheduler の実動作確認は未了です。
- cleanup 2 test と subprocess 死亡 test は U2／親の担当として未実装です。

## 総括

指定 2 ファイルに実装差分とテストを用意しました。ただし、pytest 未実走と既存期待の不一致が残っており、**完了・closed・受入可能とは申告しません**。親側で実走・修正・統合が必要です。
