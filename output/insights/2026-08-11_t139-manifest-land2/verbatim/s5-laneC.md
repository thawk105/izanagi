## 総括

実装済み・未実走です。緑／closed は申告しません。

- [approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-c/orchestrator/preregistration/approval_payload.py:112)
  - 固定 `F_r:docs/decisions.md` を `read_pinned_blob` で取得
  - D282・対象 fence の一意性、delimiter 長、入れ子を検査
  - exact-key grammar、7 三つ組、6 role、erratum 順序を fail-closed 検証
  - 旧 record-items root は commit なし
  - alpha reservation は台帳を読まない literal descriptor
  - import 時の Git 実行なし
- [test_t139_approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-impl-c/orchestrator/tests/test_t139_approval_payload.py:92)
  - 固定 `F_r` の正例と、指定された各拒否条件の独立負例を追加
  - plain-runner harness 付き

検査結果:

- `py_compile`: 成功
- 実走 nodeid: なし
- 試行範囲:
  - `orchestrator/tests/test_t139_approval_payload.py` 全体
  - `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- いずれも collection 前に Pegasus dispatch infrastructure failure、`qstat -Q rc=1`、runner `rc=16` で停止

赤の内訳:

- pytest finding: 未観測
- infrastructure failure: 上記 `rc=16`
- 事前指定した許容赤は、親統合時の lane A 承認 v2 pin／合成 digest 未反映と lane B `BlobRef` subclass 防御未反映のみ。それ以外は回帰扱いですが、今回は実走されていません。

波及可能性:

- 後続の manifest parser、`resolve_effective_preregistration` は `load_approval_payload` を caller とする必要があります。
- 共有 fixture は「target 1 + approved 6」「旧 root は二つ組」「alpha は証明ではなく descriptor」を維持する必要があります。
- 将来の receipt validator、submit/PBS、certified selector、report、試行台帳 consumer test は payload との exact 比較が必要です。
- 現在の所有外 caller は存在せず、`__init__.py` export も追加していません。

変更は指定された新規 2 ファイルのみです。docs 編集、`git add`、commit は行っていません。