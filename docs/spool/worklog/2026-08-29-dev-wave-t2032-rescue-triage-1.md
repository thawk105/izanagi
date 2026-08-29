---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2032-rescue-triage
seq: 1
title: 救出対象 impl-dev-wave-t2032-axis1-search-author の 5 file を T-2033 の重複と判定し、撤去は locked 条項で引き渡した (docs のみ、branch worktree-dev-wave-t2032-rescue-triage、実装面の差分ゼロにつき変異 matrix 免除)
---

## 本文

- 依頼は「T-2033 axis1-retake が稼働中なら重複判定へ切替える」という条件付きだった。
  **T-2033 は稼働中だったので切替えた。** 変異 harness (pid 1252211) が
  `.codex/worktrees/dev-wave-t2033-axis1-retake` で `test_axis1_search_catalog.py` と
  `test_axis1_search_runner.py` を対象に走行していた。
- **救出 branch には commit が 1 つも無い。** tip `7b4c992de` は merge-base と一致し main の
  祖先である。`git diff main...impl-dev-wave-t2032-axis1-search-author` は空を返す。
  5 file は untracked としてのみ存在していた。「main へ一度も着地していない」は正しいが、
  未着地なのは commit ではなく作業ツリー上の untracked bytes である。
- **材料は二重に保全されている。** worktree 内の 5 file と
  `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/t2032-axis1-search-author/` の 5 file は
  sha256 が全件一致した。撤去が worktree 側だけを消しても bytes は失われない。
- **両者は同じ 2026-08-27 事前登録の再登録であり、T-2033 が後発の版である。**
  T-2032 の registration epoch は `AX1-20260828-A1`、T-2033 は `AX1-20260829-E1` で、
  T-2033 の catalog は `supersedes` に同じ 2026-08-27 事前登録を挙げ、`outcome_informed: true`
  と改訂文書 path を持つ。T-2033 は T-2032 の定数をそのまま引き継いでいる
  (`retry_delays_s` = 3/6/12、`response_byte_limit` = 16777216、arXiv の 10,000 件天井)。
- **file 1 件ごとの処遇と理由は次のとおり。全件 破棄。**
  - `orchestrator/axis1_search_rerun.py` (76542 B) — 破棄。T-2033 の
    `orchestrator/axis1_search/{catalog,parsers,checkpoint,validator,runner}.py` (計 5704 行) が
    同じ責務を分割して実装し、fixture と quota 会計と DBLP pacing の永続化を足している。
    単一 module 版を残すと同一責務の実装が 2 つ並ぶ。
  - `orchestrator/schemas/axis1_search_catalog.schema.json` (8396 B) — 破棄。**T-2033 と path が
    同一で `$id` も同一。** 共存できない。しかも T-2032 版は
    `registration_epoch` を `{"const": "AX1-20260828-A1"}` と固定するため、後発 epoch を
    採る T-2033 の catalog を構造的に拒否する。
  - `orchestrator/schemas/axis1_search_receipt.schema.json` (4104 B) — 破棄。T-2032 固有の path
    だが、中身の `terminalReceipt` / `aggregateManifest` は T-2033 の
    `axis1_search_page_evidence.schema.json` の `bundle_manifest` と、validator の
    `evaluate_leaf` / `evaluate_aggregate` / `derive_axis_status` が担う。
    T-2033 側は申告値を読まず導出する分だけ強い。
  - `orchestrator/tests/test_axis1_search_rerun.py` (25188 B、22 test) — 破棄。T-2033 の
    `test_axis1_search_catalog.py` + `test_axis1_search_runner.py` (70 test) が同じ検査点を
    名前レベルで覆う (capacity echo、work_id 再出現、family 非重複、preflight で HTTP ゼロ、
    resume の outcome_unknown、host allowlist、byte 上限)。
  - `tools/run_axis1_search.py` (386 B) — 破棄。**T-2033 と path が同一。**
    T-2032 版は monolith を呼ぶだけの 16 行の薄い shim、T-2033 版は 183 行の本体 CLI である。
- **T-2032 固有に見えた 3 点はいずれも T-2033 が別機構で覆っていた。** (a) arXiv の 10,000 件窓は
  T-2033 では改訂文書の索引政策と登録 catalog に入っている (catalog 本文に `10000` が実在)。
  (b) `izanagi-axis1-registration-seal/v1` の seal は、T-2033 では `registration_commit` と
  128 path の凍結 predecessor 閉包へ置き換わっている (実 subprocess git での検査あり)。
  (c) anchor 系の定数は T-2033 の改訂文書が request 種別の観測として扱っている。
  **どれも T-2032 側にしか無い能力ではない。**
- **撤去は実行していない。`/cleanup-branches` §2 / §3 が二重に禁じる。**
  対象 worktree は `locked` で、lock 理由は `T-2032 T-2035 D95 Codex axis1 author active`。
  §2 は「foreign・locked・所有不明な worktree は inventory/report のみにする」と定め、
  §3 末は「occupied/locked worktree は、detach・unlock・branch/directory 削除・prune を
  行わず、そのまま引き渡す」と定める。さらに §2 の「クリーン (未コミット差分なし) のみ削除」も
  untracked 4 件で満たさない。branch も同 worktree に checkout されているため
  `git branch -d` は先に detach を要し、同じ禁止に触れる。
- **依頼が挙げた 2 つの阻止条件はどちらも成立しなかった。** (a) 損失: `check_branch_rescue.py`
  は rc=0、`deletion_loss_closure.commit_count = 0`、`complete: true` を返した。
  (b) 変異 harness: 稼働中の 2 本 (T-2033、T-2061) はいずれも `--repo` が自分の worktree で、
  `_assert_only_expected_dirt` は `repo` に閉じるため主 checkout を観測していない。
  **止めたのは第 3 の条件、locked である。**
- lock は事実として陳腐化している。`check_worktree_occupancy.py` は rc=0 /
  `status: unoccupied` / `scanned: 2275`、最終書込は 2026-08-28 11:12 JST (約 27 時間前)、
  branch reflog は作成 1 件のみ、`t2032` / `t2035` の稼働 process は無い。
  それでも §3 の locked 条項は無条件であり、lock 解除は所有境界の変更なので迂回しなかった。
- **T-2032 の task 実体は本救出とは別物である。** worklog の `[T-2032]` は
  「起動時に `--mode midflight` を明示すると包含と clean tree を検査しない緑が取れる」という
  ユーザー裁定待ち項目で、axis1 サーチ再走ではない。救出 branch は T-2032 を冠した wave が
  生んだ author worktree にすぎない。よって本 wave は T-2032 を完了にも見送りにもせず carry した。
- 同じ epoch の兄弟 worktree `t2032-midflight-author` と、wave 側 worktree
  `dev-wave-t2032-axis1-search-rerun` は依頼の対象外なので触れていない。
- 実装面の変更は無い。commit・push・T-2033 への介入・lock 解除は行っていない。

## 次の一手差分

### carry

- [T-2032]

### 新規

- {{T:stale-lock-release-authority}} **P2・新規・ユーザー裁定待ち**: 陳腐化した worktree lock を
  誰が解除してよいかが決まっていない。`/cleanup-branches` §2/§3 は locked worktree を無条件に
  引き渡しとするため、占有 rc=0・稼働 process なし・最終書込 24h 超が揃っても撤去できず、
  救出系の依頼が構造的に完了しない (2026-08-29 に
  `impl-dev-wave-t2032-axis1-search-author` で実測)。択は (a) 占有検査 rc=0 と最終書込からの
  経過時間の 2 条件で AI の解除を許す、(b) 解除はユーザー専任のまま残し救出 command の終端を
  「判定 + 記録 + 引き渡し」に改める、(c) lock 理由文字列へ有効期限を書かせ期限切れを
  機械判定する。親の推奨は (b) — lock は他 session の所有主張であり、(a) と (c) はどちらも
  「lock を置いた側がもう居ない」ことの推定に依存する。実害は救出が 1 手ぶん遅れることに
  留まるので、所有境界を緩める側の変更に見合わない。
