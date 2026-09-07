## 裁定 14 行の実装状況

指定された ID は合計 16 件なので、全 16 件を判定した。

| ID | 判定 | 根拠 |
|---|---|---|
| A1 | 実装済み | exact `True` を要求する gate: [s8b_floor_campaign.py:466-475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:466) |
| A2 | 実装済み | public wrapper が承認を検査し、seam 分類へ含めず core へ渡す: [s8b_floor_campaign.py:7174-7228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7174) |
| A3 | 実装済み | private core 自身にも同じ gate が存在: [s8b_floor_campaign.py:7231-7307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7231) |
| A4 | 実装済み | zero-arity CLI flag: [s8b_floor_campaign.py:8396-8413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:8396) |
| A5 | 実装済み | CLI の未承認拒否と bool の下流転送: [s8b_floor_campaign.py:8606-8638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:8606) |
| A6 | 実装済み | module 説明と launch コメントを更新: [s8b_floor_campaign.py:42-46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:42)、[同:5163-5168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:5163) |
| B1 | 実装済み | usage、初期値、parser、実投入必須化、nonce export: [submit_floor.sh:7-87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:7)、[同:632-635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:632) |
| B2 | 実装済み | 未設定、空文字、不一致、一致を分離し、承認 env を unexport: [floor_campaign.sh:545-566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:545) |
| B3 | 実装済み | fixed official argv、一致時だけ flag を 1 個 append: [floor_campaign.sh:1216-1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:1216) |
| B4 | 実装済み | floor metrics、job-result mode、driver failure 文言を official 化: [floor_campaign.sh:1346-1351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:1346)、[同:1377-1399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:1377) |
| C1 | 実装済み | v1 経路の拒否を維持し、新しい理由へ更新: [s8b_holdout_freeze.py:932-942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:932) |
| C2 | 実装済み | v2 authority の責務を docstring に明記: [s8b_holdout_freeze.py:945-957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:945) |
| D1 | 実装済み | CLI、公的入口、private core、exact bool の正負例: [test_s8b_floor_campaign.py:7122-7396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7122)。非 seam 分類と順序 pin: [同:7644-7664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7644)、[同:7883-7905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:7883) |
| D2 | 実装済み | job 4 状態、実 argv、二重 append 防止: [test_pegasus_floor_tools.py:2196-2432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2196)。実 qsub export と投入器早期拒否: [同:2644-2691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2644)、[同:2842-2896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:2842)。job-result/failure golden: [同:4190-4250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:4190) |
| D3 | 実装済み | sink 4705 は実位置のまま、main sink は 8632 へ両所更新: [test_ccbench_spawn_sites.py:884-899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:884)、[同:2642-2670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:2642) |
| D4 | 実装済み | v1 拒否と新理由を固定: [test_s8b_holdout_freeze.py:1285-1314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_holdout_freeze.py:1285)。ratified fixture は monkeypatch でなく実引数を渡す: [test_s8b_ratified_freeze.py:940-963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_ratified_freeze.py:940) |

未実装、部分実装と判定した項目はない。

## scope 外の混入

混入なし。

- `$NONCE` 用の comma／改行専用 guard や専用テストは追加されていない。既存の生成値に対する 32 桁 hex 検査はそのまま残る: [submit_floor.sh:310-317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:310)。
- gate は `take_checkpoint_environment` の後のまま。checkpoint env 消費は 7259-7261、gate は 7307: [s8b_floor_campaign.py:7259-7307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7259)。
- `test_floor_driver_consumes_checkpoint_environment_before_core_dispatch` は差分に含まれず、不変: [test_pegasus_floor_tools.py:1337-1375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:1337)。
- raw `qsub` 用の failure-stage 精密化、W-3、docs、`test_official_perf_closure.py`、`conftest.py`、`admission_registry.json`、`hooks/` は変更されていない。

D926 が不変指定した 4 面も不変だった。

- 18 名集合: [s8b_floor_contract.py:42-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_contract.py:42)
- `_derive_refreeze_eligibility` の判定式: [s8b_floor_campaign.py:7118-7131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7118)
- submission receipt schema: [submit_floor.sh:693-712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:693)
- admission claim key 6 項目: [s8b_holdout_admission.py:753-771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_admission.py:753)

## 層分けの行順検算

投入器は裁定どおり。

`argv parse 完了:76` → `override 検証:78-82` → `承認 guard:84-87` → `staging root 検査:295-301` → `root mkdir:302` → `SUBMISSION_DIR mkdir:324` → `payload staging:524` → `claim root:559` → `qsub 構築:647` → `qsub 実行:665`

したがって非 dry-run の承認引数なしは、指定された全 staging、payload、claim、PBS 操作より前に rc=2 で止まる。

job script も裁定どおり。

- 未設定: `OFFICIAL_APPROVAL_BOUND=0` のまま通過し、append 条件が偽になる。
- 空文字: 554-558 の専用文言で rc=2。
- 不一致: 559-563 の別文言で rc=2。
- 一致: 564 で bound を 1 にし、1221-1225 で flag を 1 個 append。
- `${IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN+x}` により未設定と空文字を区別している。
- 拒否位置は 554-563。gflags build 開始は 1002、driver argv は 1216 なので、両方より前。
- 566 で承認 env の export 属性を外すため、driver 子 process へ ambient 値を流さない。

## 所見 (must-fix)

なし。RA ID を付す must-fix 所見はない。

- public API、private core、CLI、resume のいずれも、未承認 official から実行へ抜ける経路は見つからなかった。
- sub-command は campaign 実行経路と分離され、campaign parser の `--mode` は `pilot`／`official` の exact choices。別名から official gate を迂回できない。
- Python の既定値は `False`、gate は `is not True`。`None`、`False`、`1` は拒否される。
- shell の空文字同士一致は nonce 自身の既存 hex 検査で到達不能。未設定参照は `${VAR+x}` の内側だけなので `set -u` 下でも安全。
- shell parser で承認引数を複数回指定しても内部値は 1 のままで、export と driver append は各 1 箇所だけ。`argparse` の複数指定も bool `True` のままである。
- ambient approval env は投入器の引数を代替せず、Python CLI も env を既定値として読まない。
- 既存拒否や assert の実質的な弱化、skip、xfail はない。削除された旧 pilot／無条件 official の期待値は裁定された official 承認仕様の exact な正負例へ置換され、ゼロ書込み、下流未到達、実 argv 完全一致の検査は維持または強化されている。

## 所見 (nit)

なし。RA ID を付す nit 所見はない。

## 総括

静的レビュー上、段 5 の実装は裁定 §4 の列挙全 16 ID を完了しており、scope 外混入、承認 bypass、gate 恒真化、絶対規律 2 の違反は見つからなかった。

worktree 全差分は指定の 9 file のみで、差分 SHA-256 は author patch と双方とも `1cb745ee711bbe1a5fdaea9b0895c6833887fbda95e25688cd9654b5dd4ed055`。ハンク単位で完全一致しており、author patch 以外の書き手が実装面へ追加編集した痕跡はない。

pytest は実行していない。read-only の静的確認として、2 shell の `bash -n` と変更された 7 Python file の `ast.parse` は rc=0。レビュー中のファイル変更、commit は行っていない。