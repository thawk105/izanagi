修正 1〜5 を指定の 2 ファイルへ実装しました。commit・docs 編集・テスト実走は行っていません。

## 修正内容

1. untracked を clean 述語から除外

- [tools/dev_wave_wait.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:49)
- [tools/dev_wave_wait.py:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:562)
- [tools/dev_wave_wait.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:930)
- [test_dev_wave_wait.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:38)

変更前は untracked を含む status で生成物も拒否しました。変更後は `_identity_preflight` と `prerun-clean` が共通定数を介して、指定どおり次の argv を使用します。

```python
("git", "status", "--porcelain", "--untracked-files=no", "--ignore-submodules=none")
```

untracked は無視し、tracked dirt と submodule dirt は引き続き拒否します。

作り替えたテストは次の 2 本です。

- `test_prerun_submodule_dirty_blocks_submission_and_releases`
  - [test_dev_wave_wait.py:1659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1659)
  - ` m external/ccbench` という submodule dirt を `prerun-clean` の負例にしました。
  - rc=70、stage=`prerun-clean`、command 不投入、lease release を検査します。
- `test_preflight_submodule_dirty_rejects_before_claim`
  - [test_dev_wave_wait.py:1929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1929)
  - 同じ submodule dirt を claim 前の負例にしました。
  - rc=2、stage=`preflight-clean`、claim・command・release なしを検査します。

2. provenance checker の Git discovery 環境を除去

- [tools/dev_wave_wait.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:136)
- [test_dev_wave_wait.py:2347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2347)

変更前は argv[0] が `git` の場合だけ `_GIT_ENV_KEYS` を除去していました。変更後は、直接 Git または argv[1] が `check_ai_provenance.py` の subprocess を同じ `git_discovery_stage` として扱います。

既存 Git 呼出しの挙動が変わっていない根拠は、直接 Git の判定が従来と同じ `values[0] == "git"` のままで、同じ `_GIT_ENV_KEYS` と同じ環境構築式を通るためです。`run_unbounded` の直接 Git も従来どおり環境だけ sanitize され、timeout は付きません。

3. provenance checker に 300 秒 timeout

- [tools/dev_wave_wait.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:146)
- [test_dev_wave_wait.py:2347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2347)

checker を既存 bounded stage と同じ `Popen(start_new_session=True)`、300 秒 timeout、process-group kill の対象にしました。timeout は既存 `_run_capture` 契約により rc=70、stage=`merge-message-provenance`、source_rc なしになります。

受入 command は `run_unbounded`／`stage_policy=False` のままなので、timeout は追加されていません。

4. M3/M4 を意味的経路で kill

- routing fake: [test_dev_wave_wait.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:354)
- submodule-aware fake: [test_dev_wave_wait.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:466)
- M4 対応テスト: [test_dev_wave_wait.py:1863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1863)

M3 は旧 argv と新 argv の両方を fake が理解します。旧 argvでは submodule dirt を空 stdout として見逃すため、変異時には以下の意味的変化が生じます。

- preflight: rc=2／claim なし → claim 後の `prerun-clean` rc=70
- prerun: rc=70／command なし → command 投入

M4 は routing fake に provenance 結果、`git commit --dry-run -F`、実 commit、postcheck、acceptance command の成功経路を登録しました。checker 削除時は argv 不一致ではなく、形式違反 message が commit と command 投入まで進むため赤になります。

既存の rc・stage・投入／release の期待値は緩和していません。対象テストでは exact event 列検査も維持しています。

5. production checker の実 Git 結合負例

- [test_dev_wave_wait.py:2864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2864)

一時 Git repo に production の `tools/check_ai_provenance.py` と必要な `site_policy` をコピーし、実際の merge state で形式違反 message を渡すテストを追加しました。次を検査します。

- rc=70、stage=`merge-message-provenance`、source_rc=1
- acceptance command 不投入
- HEAD が merge 前の SHA のまま
- `MERGE_HEAD` 消滅、tracked tree clean
- lease release 済み

## 所有外への静的な波及可能性

- `docs/pegasus-runbook.md`、F191、rollout 手順には旧述語や保証範囲の記述が残り得ます。親の更新対象です。
- `tools/run_tests.py` と `tools/dev_wave_land.py` の述語との一致は改善しますが、両ファイル自体は未編集です。
- checker のファイル名による stage 判定は、将来同名の別 checker を追加した場合にも適用されます。現在の argv は repo 内 production checkerへ固定されています。
- production checker が新しい import 依存を増やした場合、実 Git fixture にコピー対象の追加が必要になり得ます。
- レビュー B 所見 8 のうち、production checker の実 Git 経路は追加しましたが、submodule dirt 自体の「実 Git submodule」結合テストは未追加です。今回の指定は fake による意味的負例でした。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| レビュー A 1 | 親が対応 | merge 後 checker の意味的検出力は維持。docs の順序・契約整合は親担当 |
| レビュー A 2 | closed | checker に直接 Git と同じ環境 sanitization を適用 |
| レビュー A 3 | closed | checker を process group＋300秒 timeout 対象化 |
| レビュー A 4 | closed | M3/M4 を argv 不一致ではなく意味的経路で kill |
| レビュー B 1 | 親が対応 | A1 と同じ docs／裁定整合 |
| レビュー B 2 | 親が対応 | runbook の保証範囲修正 |
| レビュー B 3 | 親が対応 | F191 erratum |
| レビュー B 4 | 親が対応 | rollout barrier／waiter 再起動条件 |
| レビュー B 5 | closed | untracked を拒否対象から外し、実在 floor 生成物による停止を解消 |
| レビュー B 6 | 親が対応 | 段7 fragment と最終受入の順序 |
| レビュー B 7 | 親が対応 | message file の repo 外配置 |
| レビュー B 8 | partial | production checker 実 Git負例は追加。実 Git submodule 負例は未追加 |
| regressed | 0件 | 確認した範囲でなし |

## 検証状況

- `git diff --check`: 成功
- 2 ファイルの Python AST parse: 成功
- pytest／`tools/run_tests.py`: 未実行
- commit: 未作成
- docs: 未編集

**実装済み・未実走**です。

## 総括

- 編集ファイル:
  - `tools/dev_wave_wait.py`: worktree の対 HEAD 差分 `+40 / -6`
  - `orchestrator/tests/test_dev_wave_wait.py`: worktree の対 HEAD 差分 `+813 / -28`
  - この集計には作業開始時点から存在した段6差分も含まれます。
- closed: **4件**（A2、A3、A4、B5）
- 実走: **なし — 実装済み・未実走**
- 未解決・要判断:
  - docs 系 7 所見は親が対応
  - B8 の実 Git submodule 負例は partial のまま
  - regressed はありません。