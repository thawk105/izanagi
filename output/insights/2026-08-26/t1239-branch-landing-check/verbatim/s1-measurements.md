# 親の実測 (base main = c83b5b2c、2026-08-25、機体 = Pegasus login node)

すべて親が `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check` で実行した。

## git version

```
git version 2.34.1
```
`git patch-id --help` に `--verbatim` の記載なし (grep hit 0)。

## 未マージ (ahead>0) branch — 20 本

```
worktree-dev-wave-t441-backoff-hole-grammar          ahead=8  behind=0
worktree-dev-wave-t1594-nonattributable-landing      ahead=6  behind=0
worktree-dev-wave-t1629-ratification-execution       ahead=5  behind=58
worktree-workload-policy-hint-impl-unitC             ahead=4  behind=1623
worktree-workload-policy-hint-impl-unitB             ahead=4  behind=1623
worktree-dev-wave-t425-d716-carry-note               ahead=4  behind=0
worktree-t1458-side-ccbench-provenance-fix           ahead=2  behind=1039
worktree-dev-wave-acceptance-parallel-dispatch       ahead=2  behind=58
worktree-agent-a9e73a59e1b7c38a8                     ahead=2  behind=912
t1484-backup-before-trailer-fix                      ahead=2  behind=603
worktree-rulings-20260825-adopt-p3                   ahead=1  behind=35
worktree-rulings-20260818-second                     ahead=1  behind=1854
worktree-rulings-20260818-floor-measurement          ahead=1  behind=1893
worktree-roadmap-workload-hint                       ahead=1  behind=1655
worktree-dev-wave-t1669-floor-ledger-recovery        ahead=1  behind=77
worktree-dev-wave-t1548-sigterm-sync-point           ahead=1  behind=141
worktree-dev-wave-t1484-floor-restart-registry       ahead=1  behind=500
worktree-dev-wave-t1176-t1230-role-diagnosability    ahead=1  behind=141
worktree-cleanup-branches-20260825                   ahead=1  behind=35
worktree-agent-ab4539bed30390c7f                     ahead=1  behind=1425
```

このうち worktree を持たない 9 本 (依頼の対象):
`t1484-backup-before-trailer-fix`, `worktree-agent-ab4539bed30390c7f`,
`worktree-cleanup-branches-20260825`, `worktree-roadmap-workload-hint`,
`worktree-rulings-20260818-floor-measurement`, `worktree-rulings-20260818-second`,
`worktree-t1458-side-ccbench-provenance-fix`,
`worktree-workload-policy-hint-impl-unitB`, `worktree-workload-policy-hint-impl-unitC`。

## 層 1: `git cherry -v main <branch>` の結果 (9 本)

```
t1484-backup-before-trailer-fix               - 39407cfd  [T-1505] attempt 状態機械のドメイン非依存 core を抽出し 8c を互換 facade にする
worktree-agent-ab4539bed30390c7f              - b3611129  docs(rulings): 索引出力形式の指示を表/ID主体から平易な段落形式へ是正
worktree-cleanup-branches-20260825            + 88114f94  docs(cleanup-branches): 掃除の記録と、状態クリーン化が変異観測を壊す near miss を残す
worktree-roadmap-workload-hint                + 15b5c389  workload descriptor に自由記述ヒントを任意で許すよう roadmap §1 を協議改訂
worktree-rulings-20260818-floor-measurement   - fe56f5f7  docs(rulings): /rulings 全件 第 7 回のユーザー裁定 15 件を fragment へ記録する
worktree-rulings-20260818-second              - a6a9f2b7  docs(rulings): /rulings 全件 第 8 回のユーザー裁定 12 件を fragment へ記録する
worktree-t1458-side-ccbench-provenance-fix    + 69935f09  docs(spool): 孤児化していたrulings fragmentをfold可能な状態へ運ぶ
worktree-workload-policy-hint-impl-unitB      + 15b5c389 / + 500f47a6
worktree-workload-policy-hint-impl-unitC      + 15b5c389 / + 500f47a6
```

`worktree-workload-policy-hint-impl-unitB` と `unitC` は `git rev-parse` が同じ
`500f47a6abadb540f785c5e516d0e0873366c209` を返す。内容は完全に同一の重複 branch。

## 層 2: spool fragment の `content_sha256` を `docs/spool/FOLDED.md` で照合

親が `git show <branch>:<path> | sha256sum` の値を `grep -F` で FOLDED.md に当てた結果。

```
worktree-cleanup-branches-20260825
  docs/spool/failures/2026-08-25-cleanup-branches-20260825-1.md    not-in-FOLDED 9ca6adeafc06
  docs/spool/worklog/2026-08-25-cleanup-branches-20260825-2.md     not-in-FOLDED ac0442a77070
worktree-roadmap-workload-hint
  docs/spool/decisions/2026-08-19-roadmap-workload-hint-2.md       not-in-FOLDED 4a72f7d5172a
  docs/spool/worklog/2026-08-19-roadmap-workload-hint-1.md         not-in-FOLDED 06a99ec1c7e4
worktree-t1458-side-ccbench-provenance-fix
  docs/spool/decisions/2026-08-21-rulings-...-measurement-1.md     FOLDED        5aca1641a15a
worktree-workload-policy-hint-impl-unitB
  docs/spool/decisions/2026-08-19-roadmap-workload-hint-2.md       not-in-FOLDED 4a72f7d5172a
  docs/spool/worklog/2026-08-19-roadmap-workload-hint-1.md         not-in-FOLDED 06a99ec1c7e4
worktree-agent-ab4539bed30390c7f
  docs/spool/worklog/2026-08-20-worktree-agent-...-1.md            FOLDED        e78f224170a1
worktree-rulings-20260818-second
  docs/spool/worklog/2026-08-18-rulings-20260818-second-1.md       FOLDED        563e4052135d
worktree-rulings-20260818-floor-measurement
  docs/spool/decisions/2026-08-18-...-floor-measurement-2.md       FOLDED        7a17a3319f21
  docs/spool/worklog/2026-08-18-...-floor-measurement-1.md         not-in-FOLDED d3e79733ec46
t1484-backup-before-trailer-fix
  docs/spool/decisions/2026-08-22-dev-wave-t1484-...-2.md          FOLDED        88817a06337f
  docs/spool/worklog/2026-08-22-dev-wave-t1484-...-1.md            FOLDED        2162d0a76896
```

**層 1 と層 2 が矛盾する実例が 2 件ある。**
- `worktree-t1458-side-ccbench-provenance-fix` は層 1 が `+` (未着地) だが、層 2 で fold 済み。
  fragment 本体は fold 後に main から削除されるので `git diff main...branch` は 18 行の追加に見える。
- `worktree-rulings-20260818-floor-measurement` は層 1 が `-` (着地済み) だが、
  fragment 2 本のうち worklog 側 1 本は FOLDED.md に無い。

## 層 3: 非 fragment file の blob / 逐語照合

`worktree-workload-policy-hint-impl-unitB` が触る 9 file を main tip の同 path と blob 比較:

```
docs/roadmap.md                                                 SAME-BLOB
orchestrator/campaign/autonomous_trial_completeness.py          DIFF
orchestrator/campaign/s8b_descriptor.py                         SAME-BLOB
orchestrator/campaign/s8b_descriptor_schema.json                SAME-BLOB
orchestrator/tests/test_autonomous_trial_completeness.py        DIFF
orchestrator/tests/test_layer3_report.py                        DIFF
orchestrator/tests/test_p3_autonomous_workload_trial.py         DIFF
orchestrator/tests/test_reflux_originless_compatibility.py      DIFF
orchestrator/tests/test_s8b_descriptor.py                       SAME-BLOB
```

DIFF 5 file について、branch の blob が main の履歴のどこかに存在したかを
`git log main --format=%H --find-object=<blob> --max-count=1 -- <path>` で調べた
(所要はいずれも 1 秒未満):

```
orchestrator/campaign/autonomous_trial_completeness.py          hit=NONE
orchestrator/tests/test_autonomous_trial_completeness.py        hit=627c5019
orchestrator/tests/test_layer3_report.py                        hit=NONE
orchestrator/tests/test_p3_autonomous_workload_trial.py         hit=e56c3c20 の commit d5b84350
orchestrator/tests/test_reflux_originless_compatibility.py      hit=NONE
```

hit=NONE の 3 file について、branch が merge-base から追加した行が main tip の同 file に
逐語で存在するかを `grep -qxF` で調べた:

```
orchestrator/campaign/autonomous_trial_completeness.py
  追加 1 行 ("5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549")  FOUND
orchestrator/tests/test_layer3_report.py
  追加 1 行 (同じ sha 値)                                                          FOUND
orchestrator/tests/test_reflux_originless_compatibility.py
  追加 1 行 (_PRE_WAVE_ORIGINLESS_BASELINE = json.loads(r"""{...}""") の巨大 1 行)  MISSING
```

**最後の 1 件が (P1) の根拠。** この行は originless baseline の不透明な JSON blob で、
main では別の値へ再生成済み。blob 一致もせず逐語一致もしないが、
「この branch の変更が未着地」ではなく「この層では照合できない」が正しい。

## worktree 占有 (`tools/check_worktree_occupancy.py`、絶対 path・wrapper なし)

16 本すべて `rc=0` / `status=unoccupied` / `scanned=2297`。
対象: `.codex/worktrees/` の `t1563-fix1`, `t1563-fix2a`, `t1563-fix2b`, `t1563-fix3a`,
`t1563-fix3b`, `t1563-fix4`, `t1563-fix5`, `t1563-fix6`, `t1563-fix7`, `t1563-unit-a`,
`t1563-unit-b`, `dev-wave-t1447-reason-mirror-author`,
`dev-wave-t1447-resume-integration-author`, `dev-wave-t1563-acceptance-nproc`、および
`.claude/worktrees/` の `dev-wave-t1484-floor-restart-registry`,
`dev-wave-t1675-official-floor-path`。

lock 理由が空文字の worktree: `t1563-fix*` 9 本、`t1563-unit-*` 2 本、
`dev-wave-t1484-floor-restart-registry`、`dev-wave-t1675-official-floor-path`。
`t1563-fix*` / `t1563-unit-*` は全て detached HEAD で branch を持たない。

directory mtime: `t1563-*` は 2026-08-25 14:53〜18:38、
`dev-wave-t1447-*` は 2026-08-24、`dev-wave-t1484-floor-restart-registry` は 2026-08-24 01:35、
`dev-wave-t1675-official-floor-path` は 2026-08-25 20:16。

## 既存ツールの入口

- `tools/audit_dangling_commits.py --repo --ref --offrepo-root --include-fold-trees`
  — help に「検出対象外: 既存ファイルへの変更・削除・同名別内容・gitlink 更新」と明記。
- `tools/dev_waves/git_state.py` (1157 行) — `verify_declared_fold_commit`,
  `_pending_fragment_paths`, `branch_tip`, `_is_ancestor`, `_rev_list`,
  `_landed_commit_diff`, `create_isolated_checkout` などを持つ。
  `tools/dev_wave_land.py` と `tools/dev_wave_cleanup.py` が consumer。
- `tools/check_worktree_occupancy.py <WORKTREE>` — 位置引数 1 個のみ。
  JSON に `issues` / `occupants` / `same_uid_cwd_unreachable` / `scanned` /
  `unreachable` / `status` / `worktree`。
