## 総括

主要7項目を検査し、**崩せた3点、崩せなかった4点**だった。

- 親の中核結論――「`77db32c` を指す元の ref は、ユーザー承認後の対話的 `git branch -D` で削除された」――は維持してよい。
- ただし「08:07時点の消失原因として一意」「拾う中身は完全にゼロ」という断定形は維持できない。brief の修正が必要である。
- 「検査なしに消した」は反証できる。ただし親が引用した自己申告ではなく、削除セッション内の実コマンド結果とT-193裁定を根拠にすべきである。

| 検査点 | 判定 |
|---|---|
| 元 ref を `git branch -D` が実際に削除した | 崩せず |
| ユーザー承認が先行した | 崩せず |
| UTC/JST変換と消失窓 | 崩せず。ただし存在観測は22:58でなく22:55 |
| 同名ref再作成・再削除を排除した一意性 | 崩した |
| 親自身による一次資料の独立裏取り | 崩した |
| insight 37件がmainに保存済み | 崩せず |
| 「コード3ファイル／拾う中身ゼロ」 | 部分的に崩した |

## 経路帰属

`git branch -D` の因果は強い。同一 command が次を連続して記録している。

1. 削除直前の full SHA `77db32cbd02a8848902dd9165c9f78a651daa676`
2. `Deleted branch codex/dev-wave-improve (was 77db32c).`
3. 直後の `codex/*` 本数 `0`

[tool call](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:401>)、[tool result](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:402>)

したがって、少なくとも「元の ref をこの invocation が削除した」ことは崩せなかった。別プロセスが直前に削除していたなら通常この成功結果にはならない。

承認は `14:10:58.778Z`、tool call は `14:12:08.774Z`で、差は69.996秒だった。[承認記録](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:384>)。ただし実際の削除処理時刻は、callとresultの間の `14:12:08.774Z〜14:12:19.266Z` と表す方が正確である。

一方、一意性は証明できない。削除直後の不在は確認できるが、その後に同名refを再作成し、08:07までに別経路で再削除した可能性はGitの現存状態から排除できない。

- 可視なClaude transcript、Codex session、bash historyにはその操作は見つからなかった。
- しかし手動shell、変数で組み立てたcommand、script、別ホストは網羅されない。
- branch削除後は当該refのreflogも残らないため、同名refの再作成・再削除は同じ最終状態を作れる。

従って、「直接観測された元refの削除経路」とは言えるが、「08:07の不在を生んだ唯一の全履歴」とまでは言えない。

## 時刻窓

UTC/JST変換は崩れなかった。mtime推定に依存する必要もない。

- 実際のGitによる存在観測は `13:55:33.867Z`。同じ結果内の `date` は `now 22:55`、branchはahead=4だった。[存在観測](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:345>)
- `13:58:52.100Z`は再観測ではなく、その測定を受けたセッション文章である。
- 消失観測は `23:07:42.794Z`。同じ結果内の `date` は `2026-08-04 08:07:42`で、`git branch -a`に対象branchがない。[消失観測](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/aba6f3e3-d723-4489-b2a7-6a3211942a11.jsonl:139>)
- 続く `rev-parse --verify` も失敗している。[確認](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/aba6f3e3-d723-4489-b2a7-6a3211942a11.jsonl:144>)

したがって窓は正確には「08-03 22:55 JST存在 → 08-04 08:07 JST不在」。削除はその中の23:12 JSTにある。

## 「検査もあった」の強度

親のbriefは11:57の自己申告だけを根拠にしており、親自身の独立裏取りは不足していた。段1 transcriptで確認できるのは、`main...rescue-t213` のpath列挙と、`docs/decisions.md`でT-193をgrepしただけである。後者はD111中の言及1行しか返していない。[親のgrep結果](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi--claude-worktrees-dev-wave-t495-branch-deletion-path/1ba2ef34-84f2-41b6-a85d-caffa9bf25db.jsonl:319>)。T-193専用のD節はなく、実際の裁定正本はworklog・phase doc・裁定insightにある。

ただし、削除セッション自身は発言前に実検査を行っていた。

- 4 commitと60 pathのdiffstatを確認。[transcript](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:237>)
- mainに旧実装pathがないことを確認。[transcript](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:243>)
- T-193の「mainを正本にする」裁定を読んでいる。[transcript](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:255>)
- branch側37件、main側38件、branchだけにあるinsightが0件と実測。[transcript](</home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/9f45e239-5665-414b-b92f-c373f681bf95.jsonl:260>)

従って「独立検証済み」ではないが、「検査なし」は事実ではない。

## `rescue-t213` のtree検査

検査時のmainは `86178e4ac637f4f4d034eced7f3e3aa9b6f3a2ff`。`rescue-t213`は4 commit、tipは指定どおり `77db32cbd02a8848902dd9165c9f78a651daa676`だった。

`git diff --name-only main...rescue-t213`の60 pathを`git cat-file -e`とblob IDで分類すると、

- mainとblob同一: 37
- mainに存在するが内容が異なる: 16
- mainに存在しない: 7

mainにない7 pathは次のとおり。

```text
orchestrator/tests/test_pegasus_policy.py
orchestrator/tests/test_pegasus_test_dispatch.py
tools/pegasus/run_tests_job.sh
tools/pegasus/submit_tests.py
tools/pegasus/test_dispatch.py
tools/pegasus/test_dispatch_policy.json
tools/pegasus_policy.py
```

したがって「コード3ファイル」は不正確である。少なくとも実装・補助5 pathとテスト2 pathがmainにない。

一方、insight 37件はすべてmainとblob同一で、mainには裁定記録 `s9-t193-ruling.md` がさらに1件ある。裁定はbranchの実装50 pathをlandせず廃棄すると明記している。[裁定](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md:3>)。理由も、branch側dispatcherが`policy_path`を含むdataclass比較により本番でsubmit/resume不能になるFR-1として記録済みである。[FR-1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md:16>)

ただし、branchで得られた`Group Name`束縛の知見はゼロではない。これは`[T-222]`へ分離され、現在もmainの`_accounting_present()`はRequest ID・Started・Ended・Elapseしか検査していない。[closure記録](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/docs/archive/worklog-phase3-0801-91-92.md:263>)、[現行コード](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/pegasus/dispatch_compute.py:826>)

よって正確な結論は次である。

> 37件の記録は全てmainに保存済み。branch固有の代替dispatcher実装は既知欠陥とユーザー裁定によりland対象ではない。ただし7 pathはmainに存在せず、branch由来の未移植知見`[T-222]`も残るため、「拾う中身は完全にゼロ」ではなく「直接land／cherry-pickすべき実装はない」と表現する。

静的・読み取り専用の検査のみを行い、ファイル変更とテスト実行はしていない。