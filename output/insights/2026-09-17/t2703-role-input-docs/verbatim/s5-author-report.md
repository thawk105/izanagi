## 変更した file と差分の要約

- `orchestrator/codex_roles/review_ledger.py`: 指定の 4 SHA と Reviewed 行を更新。実物の `sha256sum` は全件指定値と一致。
- `orchestrator/tests/test_reflux_originless_compatibility.py`: plan 編集案 8 の helper と呼出しを追加。3 タプルは完全な SHA literal。既存 helper・比較・baseline JSON は不変。

今回の差分は **2 files、47 insertions、4 deletions**。親の既存 7 file は SHA 照合で変更なしを確認しました。

## 自己検査の結果

Python 実行には、新規 bytecode 作成を防ぐ `PYTHONDONTWRITEBYTECODE=1` を指定しました。

- `sha256sum .claude/agents/<role>.md`（4 本）: rc=0、全件一致。
- `python3 tools/check_codex_agents.py`: **rc=1**。末尾は以下の 1 行のみです。

```text
ERROR: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2703-role-input-docs/.codex/role-adapters/coder-v4-autonomous-trigger-gating.json: rendered adapter byte parity drift。manifest/Claude sourceから再生成する
```

- `python3 -c "import orchestrator.tests.test_reflux_originless_compatibility as m; print('IMPORT_OK', len(m._PRE_WAVE_ORIGINLESS_BASELINE))"`: **rc=0、`IMPORT_OK 386`**。
- 新 helper 呼出しを一時コメントアウトして同じ import: **rc=0、`IMPORT_OK 386`**。byte 単位で復元後の import も同結果。
- 復元後の `git diff --stat`: rc=0。全体は親の既存 7 file＋今回の 2 file。対象 2 file に限定した stat も確認。
- `git diff --check`: rc=0。
- 指定の `git grep -n "SOURCE_FILE_SHA256\|_PRE_WAVE_ORIGINLESS_BASELINE\|_extend_t304_role_name_baseline"`: rc=0。
- pytest・変異のテスト実走: **実装済み・未実走**。

## 所有外への波及 (静的列挙)

- `orchestrator/codex_roles/spec.py:587`: source SHA 照合。`:771`、`:820` は semantic digest／adapter へ pin を反映。
- `tools/check_codex_agents.py:44`、`:224`: role 読込みと adapter 照合。親による再 render が必要。
- `orchestrator/tests/test_codex_agents.py`: ledger 集合、SHA、adapter、drift 検査の直接 consumer。
- `orchestrator/tests/test_p3_autonomous_workload_trial.py` の `t325_registered_trial`: originless テストが利用する共有 fixture。
- `orchestrator/campaign/p3_autonomous_workload_trial.py:680`: `FixtureRoleProvider` が role 本文を hash 化。
- baseline の直接比較は変更対象テスト内の L1409、1412、1419、1427。所有外の直接 caller は検索上なし。docs・過去成果物の参照は変更していません。

## 総括

指定の 2 file の実装と自己検査を完了しました。checker は未 render の adapter 不一致による期待赤です。adapter 再生成と pytest 実走は親へ引き継ぎます。commit・禁止された Git 操作は実行していません。