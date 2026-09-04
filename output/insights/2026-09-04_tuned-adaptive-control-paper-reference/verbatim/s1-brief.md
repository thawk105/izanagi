# 段 1 brief — [T-2186] / [T-2239] 調整済み adaptive を実際の対照として論文側から参照できるようにする

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control`
branch: `worktree-dev-wave-t2186-t2239-tuned-adaptive-control`
基準 commit (local main と一致): 39086303b

## ユーザーが確定させた裁定 (wave 引数、逐語)

「[T-2186] を主、[T-2239] を同一単位で。調整済み adaptive backoff を正式な対照へ組み込む。D1475
に従い、既存の比較・図・論文ストーリーのうち既定 adaptive を単独基準線に使っている箇所を洗い出して
差し替える。[T-2239] のとおり、「呼称の限定」でなく**実際の対照として同じ図に並べる**ところまでを行う。
作図は tools/plotting/FIGURE_CONVENTIONS.md を正本とし計測機の外で行う。新しい測定は本 wave では
行わず、既取得の値だけで差し替える (測定値は main の進行を跨いで生きるので取り直さない)。正本は
worklog carry [T-2186] (entry 1187) / [T-2239] (entry 1215) と D1475。起動時に稼働 wave との
編集面重複を検査する。規律 2 を緩めない。Codex author = D95。本題の差し替えだけ。仮想リスク向けの
gate・検査・台帳・一般化の追加は scope 外。」

## 親が起動検査で実測した、引数・carry の前提を覆す新事実

1. **調整済み adaptive の定数は D1475 の値ではない。** D1475 の「刻み 0.5µs / 上限 50µs」は
   後続の D1505 / D1506 が置き換えており、現行は **刻み 1µs / 更新間隔 2560µs / 上限 1000µs**。
   律速は刻みではなく更新間隔である (D1505)。
2. **[T-2186] の差し替えは既に完了して main へ着地している。** 実体は D1505 / D1506 と、
   既定 adaptive を単独基準線にしていた 10 単位の差し替え
   (`output/insights/2026-09-02_default-adaptive-baseline-replacement.md`)。
   `tools/plotting/FIGURE_CONVENTIONS.md` §5 も差し替え済み。worklog の持ち越し行は stale。
3. **[T-2239] の「同じ図に並べる」は、既に描かれた図が存在する。**
   `output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis`
   が、無 backoff (`cell=none`) / 既定 adaptive (`cell=s100-u10`, `is_stock_control=true`) /
   調整済み adaptive (`cell=s1-u2560`) を含む 5 セルを、3 負荷 × 8 スレッド数 (6〜48)、
   7 反復、Student-t 95% 信頼区間つきで**同じ軸に**描いている。単一環境
   (`env_tag=pegasus`, `ccbench_commit=511c953`, `patches/cicada-adaptive-params.patch`)。
   親が provenance JSON の `primary_values` を実際に集計して確認した。
   carry の「新規計測が要る」は**旧 `linux-baremetal` の図へ足す場合**に限った話である。
4. **carry の前提条件 (1) は既に不採用裁定済み。**
   `orchestrator/tests/test_backoff_figure_provenance.py` の `BASELINE_BY_GENOME` 拡張は
   T-2186 の段 4 が 3 つの理由で不採用としている (3 定数を出す producer が実在しない・
   要求すると既存 campaign が描けなくなる・ユーザーの「仮想リスク向けの gate 追加は scope 外」)。
   本 wave が使う経路 (`tools/plotting/plot_t2187_adaptive_consts.py`, provenance schema
   `izanagi-t2187-adaptive-const-figure-provenance/v1`) はこの対応表を通らない。
5. **carry の前提条件 (2) は未了。** 調整済みの値は trace-disabled のみで直列性未検査。
   検査は [T-2189] の担当で、現在 live wave が走行中。
6. **論文側のどの文書も、対照を描いた図を指していない。** `docs/` (archive / spool を除く) からの
   参照は `output/insights/2026-09-02_cicada-adaptive-three-constants.md` という**解説文**への
   ものだけで (`docs/decisions.md:46941`, `docs/paper-story/README.md:104`,
   `docs/paper-story/figures/README.md:203`)、図そのものへの参照は
   `git grep -n "three-constants-figures\|t2187_stage" -- docs/` で **0 件**。
7. **図を論文図の置き場へ移すことは前 wave が意図的に見送っている。**
   `output/insights/2026-09-02_cicada-adaptive-three-constants.md` が
   「論文図の場所 (`docs/paper-story/figures/`) には置いていない — 本測定は直列化検証を
   通しておらず、論文図として使える段階にない」と明記する。

## scope

論文ストーリーと図の台帳から、調整済み adaptive を**実際に描いた対照図**へ到達できるようにする。
あわせて、既定 adaptive を単独の適応基準線として扱っている残余を独立に再走査する。
新規計測なし・新規描画なし・既存図の bytes を動かさない。

## 不変条件

- 調整済みの値は trace-disabled のみで直列性未検査。**variant 採用の根拠に使わない** (絶対規律 2)。
  新しく書く参照箇所すべてに未認証である旨を残す。
- `docs/paper-story/figures/` の PNG / PDF / provenance、および各版 snapshot
  (`2026-07-03` / `2026-07-10` / `2026-08-23` / `2026-08-26` / `2026-09-02`) と
  `docs/paper-story/claim-evidence/` は凍結物。触らない。
- Pegasus の値と旧 `linux-baremetal` の図を同じ図・同じ時系列・同じ再現判定へ畳まない。
- 既存図を再生成しない (bytes を動かさない)。作図を走らせない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない (ユーザー明示)。

## 成果物の形

- `docs/paper-story/figures/README.md` — 調整済み対照の**現物の所在**と、論文図へ昇格する条件を持つ節。
- `docs/paper-story/README.md` の「今後の基準線」段落 — 散文だけの基準線主張を、描かれた対照図への
  参照へ差し替え。
- `docs/spool/` の fragment (worklog、必要なら decisions)。
- 実装面 (コード・テスト・実行可能 script・機械設定) の差分は 0 を想定。必要と判明したら
  Codex `role=author` を立てる (D95)。親は実装面を直接編集しない。

## (P1) 親の provisional 裁定 — これが段 3 の攻撃対象である

- **(P1-a)** 対照図を `docs/paper-story/figures/` へ**昇格させない**。台帳から指すだけにする。
  根拠: 昇格は前 wave が絶対規律 2 を理由に意図的に見送った判断であり、[T-2189] 未了の今それを
  覆す新事実がない。**攻撃対象:** 「指すだけ」ではユーザーの「実際の対照として同じ図に並べる
  ところまで」に届かないのではないか。
- **(P1-b)** `tools/plotting/FIGURE_CONVENTIONS.md` は変更しない (§5 は D1506 に沿って差し替え済み)。
  **攻撃対象:** 規約は基準線 2 本を要求するのに、それを満たす図の所在を規約が持っていない。
- **(P1-c)** `BASELINE_BY_GENOME` を拡張しない (新事実 4)。
  **攻撃対象:** 前 wave の不採用理由が現時点でも成立しているか。

## DW-G05 成果物影響

放置すると、論文執筆時に「基準線は無 backoff と調整済み adaptive」という規約 (D1506 / 作図規約 §5) を
満たす図へ到達できず、執筆者は既定 adaptive を単独の適応側に置いた `fig2b` / `fig2c` を引く。
これは D1506 が「機構の優劣を何も言っていない」と定めた比較を論文の主張へ入れることになる。

## 分割方針

docs-only の軽量版。ただし絶対規律 2 の防壁に触れる択一があるため、段 2 プランと段 3 敵対相談は省かない。
