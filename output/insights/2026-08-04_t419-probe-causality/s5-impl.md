実装を完了しました。既存の受理・拒否述語、較正 bytes、pin、既存テスト、docs は変更していません。commit も未作成です。

静的な波及先は PBS wrapper、path-import テスト、全新規テストを検査する `test_plain_runner_coverage.py` です。共有 fixture や既存 caller はなく、`env_contract` と `env_attestation` は実行時の読み取り専用 consumer です。親 docs 未 land による期待赤は 0 件です。

pytest はログインノード禁止のため、実行 nodeid は 0 件です。親は計算ノードで新規テストと meta-test を実走し、PBS を絶対 `-o/-e` 指定で投入して、qstat・会計痕跡・manifest hash・競合判定を確認してください。

## 総括

- 作成: [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py) — 2,084 行。
- 作成: [t419_probe_causality.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs) — 98 行。
- 作成: [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py) — 70 行。
- 閾値は driver の [定数群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:34) に固定: busy 1 tick、0.95、0.05、46/48。
- canonical inclusive 判定は [canonical_pass](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:102)、INVALID 含意は [evaluate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:568)。
- `python3.10 -m py_compile` 対象 2 ファイル: rc=0。
- `/proc` 非参照 `--self-test`: 合成 fixture 8 件、rc=0。pytest: 0 件。
- 親実測: 計算ノード pytest＋meta-test、PBS 完走、48 CPU、単独性、診断 completeness、raw 3 件、parser crosscheck、会計証拠。