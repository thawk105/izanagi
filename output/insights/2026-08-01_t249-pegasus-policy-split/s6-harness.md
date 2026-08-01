harness を作成しました。

成果物: [mutation_harness.py](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/mutation_harness.py)

主な実装内容:

- M1〜M7 を各 1 dispatch で実行。
- harness 自身の inode を `flock` し、二重起動を拒否。
- 累積置換ごとに anchor の一意性を検査。
- 注入前後の unified diff が空なら `INJECTION_FAILED`。
- `-rf` 出力から ANSI を除去し、failed node と assertion を記録。
- 期待 node 集合と assertion marker が一致した場合だけ `KILL`。
- 各変異を親側 `finally` で復元し、内容・index・porcelain・cached stat を照合。
- timeout 時は dispatcher に SIGTERM を送り、qdel 用猶予後のみ SIGKILL。
- M5 の HEAD baseline と M6 の HEAD 変異を `t249-mutation-head` で実行。
- F26 に従い、`git worktree remove` 拒否時のみ検証済み rmtree＋prune へフォールバック。
- 台帳は実行時に `mutation-ledger.json` へ原子的に出力。

親の実行コマンド:

```bash
cd /home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split
python3 /home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/mutation_harness.py
```

短い外側 timeout では包まず、harness 内部の各 dispatch timeout（既定 2700 秒）を使用してください。

静的検査はすべて成功しました。

- `python3 -m py_compile`
- anchor 一意性検査
- FAILED node parser 検査
- 排他 lock 二重取得拒否
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

harness・pytest は実行していないため、台帳はまだ生成されていません。repo 内にも harness 関連ファイルは作成していません。

## 総括

- M1〜M7 と HEAD 対照を実装した単一 harness を job tmp に配置した。
- 注入実在、意味的 kill、failed node/assertion、timeout を台帳化する。
- working tree と index は各変異の `finally` で厳密に復元する。
- HEAD worktree は既知の F26 cleanup 罠にも対応した。
- 静的検査は緑、変異本走は指示どおり未実施。