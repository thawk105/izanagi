修正対象 2 ファイルのみを編集しました。`git add`・commit・docs/test/policy の変更はありません。

## 総括

| 項目 | 状態 | 実装箇所 |
|---|---|---|
| G-1 二側 control | **closed** | 正負 control、起動時の負 control 不存在記録、`two-sided-ok` 判定: [probe.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:30), [probe.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:623), [probe.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:835), [probe.py:886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:886) |
| G-2 実行 bytes binding | **closed** | 5 要素の一致判定、必須 CLI、PBS 環境変数: [probe.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:194), [probe.py:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:997), [probe.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:7), [probe.pbs:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:68) |
| G-3 中間 symlink 拒否 | **closed** | workdir の `realpath -e` 一致と全 component 検査: [probe.pbs:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:15), [probe.pbs:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:20), [probe.pbs:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:42) |
| G-4 必須 field 完備性 | **closed** | ネスト済み必須一覧、書込み直前検査、完備 marker: [probe.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:53), [probe.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:914), [probe.py:956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:956) |
| G-5 模擬との差・整合性 | **closed** | version 20 秒、各候補の日本語 `limitation`、非致命的 `consistency`: [probe.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:34), [probe.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:403), [probe.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:486), [probe.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:831) |
| G-6 failure stage | **closed** | executable 順の機械導出と結果への格納: [probe.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:463), [probe.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:790) |

親が qsub 時に渡す環境変数は次の 5 個です。

- `EXPECT_HEAD`: 測定対象 checkout の期待 HEAD（現在値 `1a3604b126c853fc98426f0dbf67b7dde96fa3da`）
- `EXPECT_POLICY_SHA256`: policy bytes（現在値 `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`）
- `EXPECT_PROBE_SHA256`: probe bytes（現在値 `281aadc854cb450402f1803d01507d52ee6ddd192fa8774598713e97390cb624`）
- `EXPECT_PBS_SHA256`: PBS bytes（現在値 `afa4526aa7c7df0e87c21b1bc7a8bb0b8381e03c71a2a5eee71c1b7205bb4021`）
- `EXPECT_SUBMISSION_SHA256`: production submission bytes（現在値 `1c19581c176786080a65cffe580f0da54e42623ad260ff13b0ec26e64383cc69`）

`PBS_JOBID` と `PBS_O_WORKDIR` も必須ですが、これは PBS が設定する変数で、親が `-v` で渡す値ではありません。qsub 直前に上記期待値を再計算してください。

検査結果:

- `python3 -m py_compile tools/pegasus/probes/t293_perf_site_probe.py`: **成功**
- `bash -n tools/pegasus/probes/t293_perf_site_probe.pbs`: **成功**
- pytest: **未実走**
- probe／perf／PBS job: **未実走**
- `check_codex_agents.py`／`check_docs.py`／provenance: **未実走**（親の統合・受入工程に帰属）

`git status --short`:

```text
?? tools/pegasus/probes/t293_perf_site_probe.pbs
?? tools/pegasus/probes/t293_perf_site_probe.py
```

静的な波及可能性:

- 旧 qsub 呼出しは新しい SHA 環境変数 3 個がなければ exit 2 になる。リポジトリ内に別 caller は見つからなかった。
- probe の CLI および `run()` / `probe()` を直接呼ぶ外部 consumer は、新しい期待 SHA 3 個への対応が必要。
- JSON consumer は `positive_control_resolution`、`control_sensitivity`、`required_fields_complete`、`consistency`、`failure_stage` を受理判定へ取り込む必要がある。従来の `control_resolution` は負 control として維持した。
- symlink や非 canonical 表記を使う `PBS_O_WORKDIR`、出力経路中の symlink は意図的に拒否される。
- per-candidate の最悪待機時間は候補ごとに最大 10 秒増える。
- R4、R5、R6、B8 は今回の指定範囲外で未変更。特に Python 直接起動の login-node 防壁、requeue 時の create-only、NQSV `.o/.e` 収容は親側の残課題。