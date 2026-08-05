実装済み・未実走です。コードとテストだけを編集し、docs・no-touch 面・変異 spec・commit には触れていません。

| 所見 | 判定 | 対応 |
|---|---|---|
| F1 | partial | mask exact 検査を interval 待機直後へ移動。sleep 中に affinity を広げる負例を追加 |
| F2 | partial | primary failure と復元失敗を収集・合成。pin＋restore、read＋restore の同時失敗を追加 |
| F3 | partial | drift を CPU 99 追加方式へ変更。CPU-set と identity を独立 node に分割 |
| F4 | partial | fake に実走 CPU 状態を追加し、その CPU から高値ベクトルを生成。target 列検査を分離 |
| F5 | partial | quiet 正例を、全値が帯内ながら read ごとに異なる系列へ変更 |
| F6 | partial | pre/post 負例を別テストへ分割。実装側の二つの `if` は独立のまま |
| regressed | なし（静的確認） | pytest 未実走のため回帰なしの確定主張はしない |

主な変更箇所は [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:425) と [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:70) です。

検査結果:

- `python3 -m py_compile ...`: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 指定 pytest は2回とも `qstat -Q preflight rc=1`、rc=16 の dispatch 基盤エラー。実行 node はありません

静的な波及可能性:

- `execution_guard.py`、`tools/pegasus/run_probe.py`、calibrator CLI、`s8b_floor_campaign.py`、T126 が zero-argument `probe()` を呼びます。keyword-only 注入引数との互換性は維持されています。
- 復元同時失敗時の文字列は `run_probe.py` の失敗成果物へ、primary と restore の両理由を含んで記録されます。
- `_FakeCpuinfoRuntime` と `_patch_runtime_probe` は当該テストファイル内だけで共有されています。
- schema、comparator、env contract、凍結 manifest、登録較正、保存 profile consumer、旧 corpus は未変更です。
- 作業状態は2ファイルとも `MM`。段5差分は staged、本 fix は unstaged overlay で、commit は作っていません。

## 総括

F1–F6 はすべて実装・静的検査済みですが、Pegasus dispatch 障害のため契約上は全件 `partial` です。親環境で `python3 tools/run_tests.py orchestrator/tests/test_env_attestation.py -q` の再実走が必要です。