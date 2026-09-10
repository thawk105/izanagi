F-1/F-2 を修正しました。段 6 worker 契約に従い、コード・テスト以外は編集せず、commit / add もしていません。

| 所見 | 判定 | 対応 |
|---|---|---|
| F-1 | partial（実装済み・未実走） | 比較偽装を専用 node に分離。未知文字列、`None`、整数、bytes、`str` subclass、欠落も引数なし独立 node 化 |
| F-2 | partial（実装済み・未実走） | index と `expected_names` を初回検査時に構築。失敗時は未キャッシュ、成功後のみキャッシュ。consumer import 回帰テストを追加 |
| regressed | なし（静的確認） | 受理集合・既存テスト期待値・凍結 bytes の変更なし |

主な変更箇所は [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:117) と [test_s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:160) です。M1 の期待 kill は `test_trigger_name_mask_binding_rejects_comparison_spoof_name` に固定されました。

検査結果:

- 実走 nodeid: なし。`pegasus02` ログインノードのため pytest は未実走
- `python3 -m py_compile`：変更4ファイルで成功
- `git diff --check`：成功
- テスト差分：HEAD 比で追加のみ（243行追加、削除なし）
- 禁止2ファイルと凍結 JSON：無差分
- 凍結 JSON の HEAD/worktree blob hash：ともに `18346a35a00a71f8986f47d54afc1a2392fbfb27`
- `trigger_gate_binding.py` から `s8a_trigger_sweep` の import：なし

変異経路は、M1 が比較偽装専用 node へ変わりました。M2〜M7 の事前登録済み期待 kill は変更していません。ただし全ファイルを M2（helper 先頭 `return`）で走らせる場合、新しい F-2 回帰 node も追加で赤になります。これは補助的検出であり、M2 の登録済み生成層/schema 層 kill 経路は不変です。

所有外への静的波及候補:

- caller：`s1_measurement_freeze`、`s1_verify_extime_calibration`、`s8b_oracle_driver`、`s1_direct_comparison`、`t080_freeze_migration`
- shared fixture/golden：`known_axes_freeze.json`、`s1_expected_goldens.py`、`test_frozen_artifacts.py`、`test_reflux_ir.py`
- consumer test：上記各 caller の test、および `test_s8b_holdout_freeze.py`
- scope 外の holdout/ratified/replay 迂回面は今回変更していません

## 総括

F-1 は比較偽装を含む無効名を独立 node 化した。  
F-2 は import 副作用を除き、初回検査で fail-closed にした。  
成功時のみキャッシュされることも回帰テストへ固定した。  
受理集合、既存期待値、凍結 bytes、禁止面は変更していない。  
残る不確実性は pytest・M1〜M7・consumer 全走が未実走である点のみ。