## 総括

焦点走は queue preflight の `rc=16` で開始できなかったため、全件を `partial（実装済み・未実走）` とします。

| 所見 | 状態 | 対応箇所 |
|---|---|---|
| F1 | partial | waiter を exact `child_rc == 1` に限定し、receipt invariant と land でも再照合。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1288)、[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_land.py:579)、拒否回帰 [test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1460)、[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_land.py:789) |
| F2 | partial | new-file preflight に明示的 symlink 拒否を追加。receipt、log、checker receipt、probe root の回帰を追加。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:732)、[test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1797) |
| F3 | partial | cleanup 3 ケースへ checker 呼び出しを追加し、診断 argv を sentinel assertion から除外。E2E slug を実 branch 末尾 `codex-one` に修正。[test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:3644)、[test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:4600)、[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_land.py:938) |
| F4 | partial | SHA-256 を 1 MiB 固定 chunk の逐次 update に変更。`_Effects.sha256_file` 注入 seam と既存 fake の `read_bytes` fallback を維持。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:294)、[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1341)、[test_dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1416) |

変更後の挙動:

- `child_rc == 0`: 従来どおり `child-green`。
- `child_rc == 1`: checker を起動し、`non-attributable-only` の厳密照合時だけ receipt を発行。
- `child_rc` が `2 / 13 / 16 / 23 / signal由来の負値`など: checker を起動せず、`acceptance-command` で fail-closed。
- land は非帰属 receipt の `child_rc != 1` を `RC_AUDIT=23` で拒否。
- dangling symlink は claim 前に rc 2 で拒否。

検査結果:

- `py_compile`：4 ファイル通過。
- `git diff --check`：通過。
- 焦点走：`python3 tools/run_tests.py ...` が `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`、終了コード 16。pytest 本体は未実走で、緑とは申告しない。

静的な波及可能性:

- receipt の schema・field 集合・`LandResult` は変更なし。
- `_Effects` の新 field は末尾の optional field で、既存 shared fake は従来の `read_bytes` 注入を継続可能。
- `check_acceptance_reds.py` は無変更で、今後は child rc 1 の場合だけ呼ばれる。
- dangling path を再利用していた外部 caller は claim 前 rc 2 になる。
- `tools/wave_land_window.py` の lease cleanup/release 契約は変更なし。
- `docs/pegasus-runbook.md` の既存未コミット変更は他者所有として触れていない。

裁定外で判断した実装詳細:

- hash chunk を 1 MiB とした。
- rc 1 以外の child failure は `acceptance-command`、raw return code を `source_rc` とした。
- F1 と F3 を同時に満たすため、cleanup 3 fixture の child rc を 5 から 1 にし、cleanup の最終 rc 74 は維持した。
- dangling probe root が同時に log の欠落 parentでもある場合、より早い `acceptance-log-preflight` で拒否する。既存 directory symlink は `acceptance-red-check-preflight` で拒否する。

docs 編集・commit は行っていません。