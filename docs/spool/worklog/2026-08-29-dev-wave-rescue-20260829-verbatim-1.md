---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-rescue-20260829-verbatim
seq: 1
title: [T-1874] 救出 3 branch の逐語を file 単位で処遇判定し、T-1874 の裁定パッケージだけを残した (docs のみ、branch worktree-dev-wave-rescue-20260829-verbatim、実装面差分ゼロ)
---

## 本文

- ユーザー裁定: 逐語は主張を支えるためのものであり、**破棄が既定**。残すなら「これが無いと何の
  主張が検証できなくなるか」を一行で言えることを条件とする。判定基準は研究が前へ進むかどうかで、
  provenance gate を満たすためだけに存在する逐語は破棄してよい。本 wave はこの基準を
  `rescue-20260829` の 3 branch・9 file へ適用した。
- 適用結果は **4 件を残し 5 件を破棄**。残したのは T-1874 の逐語 4 件だけである。

- **T-1874 (`worktree-dev-wave-t1874-s8c-section5-consumer`) — 4 件すべて残す。**
  2026-08-28 のこの wave は段 4 で fail-closed 停止し、段 5 実装子を起動していない
  (実装面差分ゼロ)。唯一の成果は「§5 値 gate の production consumer は現行 schema では実装
  できず、着手には 4 件のユーザー裁定が要る」という否定的結論であり、この結論も 4 件の裁定質問も
  worklog・decisions・insight のどこにも記録されていなかった (`s8c-section5-consumer` /
  `2026-08-28_t1874` の docs 全文検索で 0 件)。T-1874 は「次の一手」に (1058) から持ち越されて
  いる生きたタスクなので、記録が無いままでは次の担当が段 2・3 をまるごと再実行して同じ 4 件の
  blocker を再発見することになる。file 別の理由は
  `output/insights/2026-08-28_t1874-s8c-section5-consumer/README.md` の表を正本とする。
  - `verbatim/stage4-adjudication.md` — 無いと、何の裁定を待って止まっているのかを検証できない。
  - `verbatim/stage3-correctness.md` — 無いと、停止の根拠 (6xn 観測・raw-value attestation・
    H1/H2 別 params のいずれも既存 schema から供給できないこと) を production code の位置で
    検証できない。
  - `verbatim/stage3-effectiveness.md` — 無いと、裁定質問 1 を成立させる事実 (supervisor は
    `trial_registry` の caller ではない、C07 evaluator は production caller を検出しない) が失われる。
  - `verbatim/stage2-plan.md` — 無いと、段 3 が何を反証したのかを照合できず、
    `docs/phase3-8c-preregistration.md` の「欄別型検証は発効対象外」が新しい発効連言と矛盾する
    という唯一の指摘も失われる。
  - 逐語は bytes を変えずに移した。当時の worktree 絶対パスと行番号を含むが、先例の着地済み逐語も
    同じ形であり、書き換えると逐語でなくなるため訂正していない。README に「行番号は当時のもの」と
    断りを置いた。

- **T-2018 (`impl-dev-wave-t2018-condition-meaning-author`) — 4 件すべて破棄。**
  逐語 3 件 (`s5-author.md` / `s6-fix.md` / `s6-fix2.md`) は main の同 path と末尾改行のみの差で
  内容が一致していた。worktree に staged で残っていた実装 7 file と fixture 6 file も main と
  sha256 一致で、未追跡 insight 3 file も main に存在した。損失ゼロ。
- **T-2018 (`impl-dev-wave-t2018-acceptance-inventory-fix`) — 2 件とも破棄。**
  `acceptance-inventory-fix.md` は main と末尾改行のみの差。
  `orchestrator/tests/test_ccbench_spawn_sites.py` は救出版が古く (602 行、main は 610 行)、
  救出版固有の内容は `("campaign/paper_story_a2_certification.py", "<module>.run_workload"): 2`
  だけで、main は同じ key を `3` として数え、他に 4 件の spawn site entry を持つ。当てると
  CCBench 起動点の棚卸しが後退するため、救出ではなく退行になる。

- 3 branch とも main の祖先で ahead=0 (behind は 327 / 325 / 283)。未着地 commit はゼロで、
  失われていたのは worktree の未追跡・未 commit 分だけだった。
- 撤去の安全条件を実測した。稼働中の変異 harness 2 本はいずれも自分の worktree を観測しており
  (`--repo` が `dev-wave-t2033-axis1-retake` と `dev-wave-t2061-wal-admission`)、主 checkout は
  観測対象外だった。`mutation_harness.py` に `--source-repo` は無く観測 root は `--repo` だけで
  決まる。3 worktree の lock はいずれも完了済み wave の stale な手動 lock で、占有検査は
  unoccupied (scanned > 2200) だった。
- 落とし穴: `git worktree list` を `head -30` で切ると t2018 の worktree 2 件を「不在」と誤認する。
  全件で見て初めて 3 件とも実在すると分かった。

## 次の一手差分

### 更新

- [T-1874] **P2・ユーザー裁定待ち**: §5 値 gate の production consumer。段 4 で停止した裁定
  パッケージが `output/insights/2026-08-28_t1874-s8c-section5-consumer/` にある。再開前に同 README
  の「未解決 — ユーザー裁定を待っている 4 点」と「拒否された近道」を読み、段 2 から作り直さない。
  base: a07133acd2c8e6e20ab4d58ed50638e45ad3eec76347526de7e4999541842834
