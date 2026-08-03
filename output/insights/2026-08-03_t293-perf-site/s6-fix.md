## 総括

F-1〜F-7 をすべて実装しました。commit・git add・対象外編集は行っていません。

- **F-1 — closed:** `ok` を binding 一致・全測定層 `attempted:true`・control 未解決に限定。候補未解決や smoke 不合格は正常な否定結果として rc 0 を維持し、import／内部例外は非 0。[probe.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:23)、[probe.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:367)、[probe.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:605)
- **F-2 — closed:** 全 policy candidate を独立測定し、path record、`--version`、模擬 `perf stat`、production 相当の `functional` 判定を記録。[probe.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:249)
- **F-3 — closed:** `python` / `cc` / `cxx` / `cmake` / `perf` ごとに実物 `_executable` を呼び、個別結果を記録。[probe.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:33)、[probe.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:508)
- **F-4 — closed:** 必須 64hex／40hex 引数、測定前の policy/HEAD 照合、probe・PBS・submission の SHA-256 記録を追加。[probe.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:128)、[probe.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:650)、[probe.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:7)、[probe.pbs:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:43)
- **F-5 — closed:** job 固有 dir、marker、log、rc、done-marker を create-only 化し、末端 dir と親の symlink を拒否。marker／done-marker の役割もコメントで分離。[probe.pbs:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:12)、[probe.pbs:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:31)、[probe.pbs:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:52)
- **F-6 — closed:** 同一 run 内で存在し得ない候補を production resolver に渡し、解決時は `ok:false`／非 0。[probe.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:28)、[probe.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:589)
- **F-7 — closed:** hostname・epoch・policy SHA に限定した一標本であり、全 bnode／将来 allocation へ一般化しない旨を JSON に記録。[probe.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:158)

検査結果:

- `python3 -m py_compile tools/pegasus/probes/t293_perf_site_probe.py`: 成功
- `bash -n tools/pegasus/probes/t293_perf_site_probe.pbs`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- pytest: **未実走**（Pegasus login node のため）
- probe／perf／PBS job: **未実走**
- 静的照合時の HEAD: `1a3604b126c853fc98426f0dbf67b7dde96fa3da`
- policy SHA-256: `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`

`git status --short`:

```text
?? tools/pegasus/probes/t293_perf_site_probe.pbs
?? tools/pegasus/probes/t293_perf_site_probe.py
```

波及可能性:

- qsub caller は `EXPECT_POLICY_SHA256` と `EXPECT_HEAD` を `-v` 等で必ず渡す必要があります。
- artifact consumer は marker 単独で受理せず、done-marker、probe.rc、parse 可能な JSON、`ok:true`、binding、各 `attempted` を確認する必要があります。
- NQSV の `.o/.e` 配置は job 本体から制御できないため、qsub caller が `-o/-e` を指定する責務が残ります。
- `submission.py` の private `_executable`、例外型、`prepare_toolchain` 候補列を変更すると probe に波及します。
- 共有 fixture では `orchestrator/tests/test_t126_pegasus_tools.py` が submission/perf 候補を構成します。直接 probe を参照する既存 fixture／test は静的検索ではありませんでした。
- policy の既存 consumer (`t141_region_profile.sh`、`certify_calibration.sh`、`t126_qualification.sh`) と `test_pegasus_tools.py` は未変更です。