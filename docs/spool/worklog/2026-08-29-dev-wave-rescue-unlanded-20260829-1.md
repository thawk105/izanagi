---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-rescue-unlanded-20260829
seq: 1
title: 未 land と報告された記録 5 件を fold receipt で照合し、4 件を重複、1 件を stale として破棄した (docs のみ、branch worktree-dev-wave-rescue-unlanded-20260829、実装面差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。「未 land の spool fragment と handoff を救出し、正しければ land、既に別経路で
記録済みなら重複として破棄と判定する。破棄が既定で、land させるなら『これが無いと次に何を踏むか』を
1 行で書く」。**5 件すべてを破棄と判定した。** 判定根拠は
`output/insights/2026-08-29_rescue-unlanded-fragments/` に残す。

- **依頼の前提が覆った。「未着地 commit」は 1 件も無い。** 対象 2 branch の
  `git rev-list --count main..<branch>` はどちらも 0 で、両 branch は main の祖先である。
  残っていたのは worktree の未 commit 変更 4 件と、未 tracked file 1 件だけだった。
- **T-1840 の 3 fragment は既に fold 済みだった。** `docs/spool/FOLDED.md` の receipt 3 件の
  `content_sha256` (`37b6b208…` / `72d6937a…` / `f4a055d9…`) は、branch
  `worktree-dev-wave-t1840-b4-launcher-codex-resume` (`d29d3e3a`) の blob と 3 件とも完全一致する。
  F739〜F743、D1236〜D1240、[T-2065] / [T-2066] は採番済みで、worklog は archive entry 1064 として
  着地している。**`docs/spool/` に file が無いのは fold が fragment を GC した正常な結果**であり、
  未 land の証拠ではない。`.claude/commands/cleanup-branches.md` §1 が既に
  「spool の不在は fold で正常」と明記しており、手順の欠落ではないので failures への新規追記はしない。
- **worktree 版は着地済み版の部分集合だった。** 着地済み版との差分を取ると、failures fragment と
  decisions fragment は worktree 固有行が **0 行**である。worklog fragment の固有行は 3 行だけで、
  その中身は旧 title と「`ff10013b1` で変異 18/18 KILLED」という主張である。
- **その 3 行は、着地済みの entry 1064 自身が反証している。** 同 entry は
  「旧 dirty の `ff10013b1` 変異は 18/18 KILLED だが、resume focus が M08〜M10 の単一理由性を
  refute したため最終証拠には使わない」と書く。**land すれば反証済みの主張を台帳へ戻すことになる**ので、
  破棄は安全なだけでなく必要である。
- **`mutation-ledger.json` の worktree 版を land すると権威ある成果物を破壊していた。** worktree 版は
  `repo_head=ff10013b1` の resume 前実行で、main の
  `output/insights/2026-08-27_t1840-b4-launcher-chokepoint/mutation-ledger-pre-resume-ff10013b1.json` と
  **byte 完全一致 (`f8031d37…`)** する。既に正しい名前で保存済みである。一方 main の
  `mutation-ledger.json` は `repo_head=035e97129` の取り込み後 broad 実行で、entry 1064 が
  最終証拠と定めたものである。同名で上書きすれば、権威ある版を反証済みの版で置き換えていた。
- **未 tracked の `mutation-ledger-merged-contaminated.json` も main と byte 完全一致だった**
  (`01c082dc…`)。F743 の一次資料として既に着地している。純粋な重複である。
- **T-1998 の handoff だけが main に無い内容を持っていた。それでも file は破棄した。** 追記分は
  2026-08-28 の実装 wave (中断) の段 1 brief と段 4 裁定要約である。破棄の理由は 2 つで、
  (1) 追記版は `状態: 作業中` と書くが当該 wave は 2026-08-28 以降停止しており、**main へ入れると
  起動時に全 session が読む handoff 集合へ事実でない状態表示を置くことになる**、
  (2) handoff は正常終了時に worklog へ吸収して削除する一過性の file であり、死んだ wave の
  handoff を台帳の代わりに main へ据えるのは器の取り違えである。main には precheck 版
  (`状態: 中断`) が既にあり、そちらは触っていない。
- **破棄と引き換えに、追記分で唯一導出できない知見を [T-1998] の次の一手へ移した。**
  D1244 の第 1 部品 (producer evidence の read-only 到達性監査) を中断 wave が実施し、
  「producer schema の拡張は不要」と裁定していた事実である。これが無いと、再開 wave は
  第 1 部品を白紙からやり直し、既に不要と裁定された producer schema 拡張を再び設計に入れる。
  中断 wave が名指しした `CertifiedCampaignView` と public `admit_replay_evidence()` は
  現行 repo に実在することを確認した。ただし**この裁定自体は独立監査を受けていない**ので、
  再開 wave は前提として受け取らず反証する形で確かめる。
- **撤去の関門は記録前に全部通した。** `tools/check_branch_rescue.py` を全対象 1 回で通し、
  `deletion_loss_closure` は `complete=true` / `commit_count=0` — **撤去で最後の耐久 root を失う
  commit は reflog 込みで 0 件**である。`not_landed` も `indeterminate` も 0。rc=2 の理由は
  並行 session による `root-snapshot-moved` と、本 wave が作ったものではない既存の
  unledgered dangling commit 通知であり、どちらも損失の測定結果ではない。
  `tools/check_worktree_occupancy.py` は対象ごとに絶対 path・wrapper 無しで
  `status=unoccupied` / `scanned=2233` / rc=0。
- **変異 harness は主 checkout も対象 worktree も観測していなかった。** 2 本が稼働中だったが、
  `/proc/<pid>/cwd` で実測するとどちらも `--repo` が自分の隔離 worktree である。
- 対象 worktree は未 commit 差分を持つので `.claude/commands/cleanup-branches.md` §2 の clean 条件は
  満たさない。entry 1094 の先例に従い、**未 commit 内容を 1 件ずつ main の blob と hash 照合し、
  全件が重複または反証済みと確定させた**うえで撤去可と裁定した。撤去自体は本 wave の終端操作で、
  隔離 worktree からは機械防壁が git 操作を拒むため、land 後に主 checkout 側で実行する。
- 新しい measurement、build、正式測定、push、次 wave 起動は行っていない。

## 次の一手差分

### 更新

- [T-1998] **P2・裁定済み → 実装待ち (第 1 部品は中断 wave が実施済みの可能性あり)**: D1244 が最小 3 部品
  (producer evidence の read-only 到達性監査、既存 backoff sweep を呼ぶ薄い sanctioned launcher、
  事前登録で固定した 2 点だけを読む consumer) の実装を採用している。3 部品の着地後、正式測定認可は
  自動で進めず改めてユーザーへ諮る (D1267)。**2026-08-28 の実装 wave (中断・未 land) は第 1 部品の
  到達性監査を実施し、`orchestrator/campaign/artifact_admission.py` の `CertifiedCampaignView` と
  `orchestrator/verifier/commit_receipt.py` の public `admit_replay_evidence()` で verifier receipt を
  再検証できるため producer schema の拡張は不要、と裁定していた。** 同 wave の handoff は破棄したので、
  再開 wave はこの結論を前提として受け取らず、**反証する形で第 1 部品を確かめてから**第 2・第 3 部品へ進む。
  base: 92e41d2fabf46b7df59fc02f12ff35457790e26edddbc9685b44b3cf579c9cd3
