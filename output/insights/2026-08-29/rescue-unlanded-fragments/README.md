# 未 land と報告された記録 5 件の照合と処遇 (2026-08-29)

ユーザー起票の救出 wave の一次資料。対象は 2 worktree に残っていた未 commit の記録である。
**5 件すべてを破棄と判定した。** 判定は fold receipt と main の現物への hash 照合で行い、
推測は使っていない。

## 対象 branch の着地状態

| branch | `git rev-list --count main..<b>` | 判定 |
|---|---|---|
| `worktree-dev-wave-t1840-b4-launcher` (`ff10013b1`) | 0 | main の祖先。未着地 commit なし |
| `worktree-dev-wave-t1998-balanced-stock-inline` (`7b4c992de`) | 0 | main の祖先。未着地 commit なし |

依頼が言う「未 land」の実体は commit ではなく、この 2 worktree の未 commit 変更 4 件と
未 tracked file 1 件だった。

## fold receipt の照合 (T-1840)

`docs/spool/FOLDED.md` は T-1840 の 3 fragment を fold 済みとして記録している。fold 元は本 wave の
対象 branch ではなく、resume 用の別 branch `worktree-dev-wave-t1840-b4-launcher-codex-resume`
(`d29d3e3a17ccc7e58f919f9499c4192049aa97a8`) である。

| ledger | FOLDED.md の `content_sha256` | `d29d3e3a` の blob sha256 | 一致 |
|---|---|---|---|
| worklog | `72d6937a32057257ed963238f8161bcbb7e4909a4dbf7461340462cdfea815bd` | 同左 | yes |
| decisions | `f4a055d965fe163257042c1d9f940dfbb14d25467143e022841c2cf131a018b2` | 同左 | yes |
| failures | `37b6b208726fd23feaf5b1fee2aa467a5c8e59812de262b244ce8ecb5e697ff7` | 同左 | yes |

fold が採番した ID と、canonical での所在:

- `F739`〜`F743`。うち `F743`「作業ツリーの clean を assert する検査が全変異の観測を一様に汚染した」は
  `docs/failures.md` に実在する。
- `D1236`〜`D1240`。うち `D1240`「B-4 分類と receipt は同一 lock snapshot へ束縛し、不在は明示 digest で表す」は
  `docs/decisions.md` に実在する。
- `[T-2065]` / `[T-2066]`。
- worklog は `docs/archive/worklog-phase3-0828-1064.md` の entry 1064 として着地している。

**`docs/spool/` に fragment file が無いのは、fold が fragment を GC した正常な結果である。**
`.claude/commands/cleanup-branches.md` §1 が既に「spool の不在は fold で正常」と明記している。

## file 1 件ごとの処遇

### 1. `docs/spool/failures/2026-08-27-dev-wave-t1840-b4-launcher-1.md` — 破棄 (重複)

着地済み版との差分で **worktree 固有行 0 行**。着地済み版は F739〜F743 の 5 件を持ち、worktree 版は
そのうち `F743` に相当する 1 件しか持たない。worktree 版は着地済み版の厳密な部分集合である。

### 2. `docs/spool/worklog/2026-08-27-dev-wave-t1840-b4-launcher-1.md` — 破棄 (重複 + 反証済み)

worktree 固有行は 3 行だけで、内容は旧 title と「`ff10013b1` で変異 matrix 18/18 一致・KILLED 18」
という主張である。着地済みの entry 1064 は同じ実行について
「旧 dirty の `ff10013b1` 変異は 18/18 KILLED だが、resume focus が M08〜M10 の単一理由性を
refute したため最終証拠には使わない」と書いている。**land すれば反証済みの主張を台帳へ戻す。**

### 3. `output/insights/2026-08-27_t1840-b4-launcher-chokepoint/mutation-ledger.json` — 破棄 (重複、かつ land は破壊的)

| 版 | sha256 | `repo_head` |
|---|---|---|
| worktree 版 | `f8031d37331fc5f153930064af55afc7df70ae97fc0cdc7445ff3bc029f43194` | `ff10013b1` (resume 前) |
| main の `mutation-ledger-pre-resume-ff10013b1.json` | `f8031d37331fc5f153930064af55afc7df70ae97fc0cdc7445ff3bc029f43194` | 同上 |
| main の `mutation-ledger.json` | `250b1771ee9879796814ec08138d956f3029afa8a8bbedc9e73effbbe5aedc53` | `035e97129` (取り込み後 broad) |

worktree 版は main の `mutation-ledger-pre-resume-ff10013b1.json` と **byte 完全一致**で、既に正しい
名前で保存されている。一方 main の `mutation-ledger.json` は entry 1064 が最終証拠と定めた
取り込み後の実行である。**同名で land すれば権威ある版を反証済みの版で上書きしていた。**

### 4. `output/insights/2026-08-27_t1840-b4-launcher-chokepoint/mutation-ledger-merged-contaminated.json` — 破棄 (重複)

未 tracked だが、main の同名 file と **byte 完全一致** (`01c082dc93c40e8a38c6a7d53490a8c61b13e5eeb4bcd3ea389702a130704d7f`)。
`F743` の一次資料として既に着地している。

### 5. `docs/handoff/2026-08-28-t1998-balanced-stock-inline-precheck.md` — 破棄 (器の取り違え、知見は移送)

**5 件で唯一、main に無い内容を持っていた。** 追記分は 2026-08-28 の T-1998 実装 wave (中断) の
段 1 brief と段 4 裁定要約である。破棄する worktree 版の全文を
`sources/2026-08-28-t1998-handoff-worktree-version.md` に逐語で退避した
(sha256 `ff82bf9efb6b2c31934b9ba7fb7d69904e6361b84d22ef4e92e93afae19dcff7`、1 byte も改変していない)。
main 側の precheck 版との差分は、先頭 3 行の状態表示と、`## dev-wave 改善候補（T-1998 実装 wave）`
以降に追加された 3 節である。破棄の理由:

1. 追記版は `状態: 作業中` と書くが、当該 wave は 2026-08-28 以降停止している。main へ入れると
   起動時に全 session が読む handoff 集合へ、事実でない状態表示を置くことになる。
2. handoff は正常終了時に worklog へ吸収して削除する一過性の file である。死んだ wave の handoff を
   台帳の代わりに main へ据えるのは器の取り違えである。main には precheck 版 (`状態: 中断`) が
   既にあり、本 wave はそれを変更していない。

**追記分で唯一導出できない知見は `[T-1998]` の次の一手へ移した。** D1244 の第 1 部品
(producer evidence の read-only 到達性監査) を中断 wave が実施し、「producer schema の拡張は不要」と
裁定していた事実である。中断 wave が名指しした 2 つの seam は現行 repo に実在することを確認した。

- `orchestrator/campaign/artifact_admission.py` の `class CertifiedCampaignView`
- `orchestrator/verifier/commit_receipt.py` の `def admit_replay_evidence`

**この裁定自体は独立監査を受けていない。** 再開 wave は前提として受け取らず、反証する形で確かめる。

## 撤去の関門 (記録前に実測)

- `tools/check_branch_rescue.py --ledger-check` を 2 branch + 2 worktree の 1 回で実行。rc=2。
  - `deletion_loss_closure`: `complete=true`, `commit_count=0`, `observed_commit_count=0`
    — **撤去で最後の耐久 root を失う commit は reflog 込みで 0 件。**
  - `decision_inputs`: `not_landed=0`, `indeterminate=0`, `landed=0`。
  - rc=2 の内訳は `root-snapshot-moved` (並行 session が worktree を増減させた) と
    `ledger_notification_due` (既存の unledgered dangling commit 通知)。**どちらも本 wave の
    撤去が作った状態ではなく、損失の測定結果でもない。** 前者は entry 1094 が
    「開始時 snapshot も陳腐化する」として実測済みの現象である。
- `tools/check_worktree_occupancy.py` を対象ごとに絶対 path・wrapper 無しで実行。
  両者とも `status=unoccupied`, `scanned=2233`, `issues=[]`, rc=0。
- 稼働中の変異 harness 2 本の `/proc/<pid>/cwd` を実測。どちらも `--repo` が自分の隔離
  worktree (`dev-wave-t2033-axis1-retake` / `dev-wave-t2061-wal-admission`) であり、
  主 checkout も本 wave の対象 worktree も観測していない。

## 新規 F を書かなかった理由

「fragment が main に無い」を未 land と誤読する型は、entry 1094 でも本 wave でも起きており
`DW-G03` の独立 2 例は満たす。しかし判定規則は `.claude/commands/cleanup-branches.md` §1 に
**既に明記されている** (「`+` 行は実在でなく内容で判定する (spool の不在は fold で正常)」)。
機構の欠落ではなく既存手順の未適用なので、失敗台帳への追記は過剰な記録として見送った。
