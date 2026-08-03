## 総括

作成したファイル:

- [t293_perf_site_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py): policy 候補、実コード解決、toolchain、perf smoke、サイト情報を JSON 化する probe。
- [t293_perf_site_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs): 計算ノード marker を先行作成し、probe の JSON・log・rc を保存する PBS job。

実コード呼び出し:

- `_executable("perf", policy["perf_candidates"])`: [t293_perf_site_probe.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:162)
- `prepare_toolchain(policy)`: [t293_perf_site_probe.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:176)
- policy の読み込みと `perf_candidates` 抽出: [t293_perf_site_probe.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:51)、候補の記録: [t293_perf_site_probe.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:136)

検査結果:

- `python3 -m py_compile .../t293_perf_site_probe.py`: 成功
- `bash -n .../t293_perf_site_probe.pbs`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- pytest: 未実走
- probe・perf・PBS job: ログインノードでは未実走
- policy SHA-256: `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`（不変）

`git status --short` は次の 2 行だけで、既存ファイルの変更、`git add`、commit はありません。

```text
?? tools/pegasus/probes/t293_perf_site_probe.pbs
?? tools/pegasus/probes/t293_perf_site_probe.py
```

静的な波及可能性:

- caller: 新規 PBS と、これを `qsub` する親 wave。既存の T-293 caller はありません。
- artifact consumer: 親が `marker`、`probe.json`、`probe.log`、`probe.rc` を回収します。
- 共有実装: `qualification.submission._executable`、`prepare_toolchain`、その import 先の contract／driver 変更が probe に波及します。
- 共有 policy consumer: `certify_calibration.sh`、`t126_qualification.sh`、`t141_region_profile.sh`、submission helper と同じ `perf_candidates` を参照します。
- shared fixture／consumer test: `test_pegasus_tools.py` の候補固定値、`test_t126_pegasus_tools.py` の fake perf/toolchain fixture が関連します。今回は受理 gate・期待値・fixture を変更していません。