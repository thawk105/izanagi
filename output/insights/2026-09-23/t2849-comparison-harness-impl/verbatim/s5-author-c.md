U-C の主要実装を追加しました。ただし **adapter 2ファイルの適用と試験実走が未完了**です。commit・branch 操作はしていません。

- K0 巡 tool：request 読取、両役割への観測・診断入力、通常 proposal 検査、材料・費用の publish、モデル記録を実装。
- job body：排他的な harness 分岐、prebuild 後の単一起動、rc 伝播、起動直前の node-local lock を追加。
- SHA pin：review ledger と互換試験を更新。`test_codex_agents.py` は ledger の pin を参照するため変更不要。
- 新規試験2本を追加。既存 shell 試験は環境初期化 stub だけ拡張し、期待値は維持。

変更前に存在しなかった T-2849 入口を追加しました。既存 proposal・B-5 の受理規則は変更していません。通常 schema 外・不正文法の出力は publish 前に拒否します。

検証結果：

- `python3 tools/check_docs.py`：違反なし。
- Python 構文確認・`git diff --check`：成功。
- 新規・指定回帰・inventory 試験は `PYTHONPATH=. python3 tools/run_tests.py -q ...` で起動を試みましたが、全件 `qstat -Q preflight rc=1` → runner rc=16。**pytest 実行 nodeid は0件**です。
- `python3 tools/check_codex_agents.py`：未更新 adapter の byte parity drift で失敗。

`.codex/role-adapters/{planner-v4,coder-v4-autonomous}.json` は renderer で生成できましたが、sandbox の読取専用設定により書込みが `Errno 30` で拒否されました。親側で次の正規 renderer による適用が必要です。

```python
from orchestrator.codex_roles import spec
for name in ("planner-v4", "coder-v4-autonomous"):
    spec.adapter_path(name).write_text(
        spec.render_adapter(spec.get_role_spec(name))
    )
```

## 総括

- 規模：production 追加307行、test 追加256行。
- 所有外の必要変更：静的調査ではなし。歴史記録の B-5 束・insight・図 provenance は更新していません。
- 波及先：U-B の request／slot producer、proposal／費用 consumer、adapter checker、互換試験、shell 共通 stub、plain-runner／perf／spawn inventory。
- 実装済み・未実走。adapter 適用、回帰試験、変異 kill 確認を残しており、closed とは扱いません。

| 変異 | 位置 | 必須 test nodeid（kill 未実走） |
|---|---|---|
| M23 | job body harness 分岐の lock 設定 | `test_t2849_job_contract.py::test_harness_bench_lock` |
| M24 | 同分岐の `exit "$harness_rc"` | `test_t2849_job_contract.py::test_harness_single_driver` |
| M25 | `RoundTool.cmd_inputs` の coder 観測入力 | `test_t2849_llm_round.py::test_prior_observations_both_roles` |