# 親 brief — [T-2076] sort SWO oracle の受理言語を検証済み IR へ縮める設計 wave

wave branch: `worktree-dev-wave-t2076-sort-oracle-ir-design`
wave worktree (この検査で読む repo): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2076-sort-oracle-ir-design`
基準 commit: `7013ea81f4be53706a186dcaa72c49cdeb3b6f7a` (local main と 0 commit 乖離)

## ユーザーからの依頼 (逐語)

> [T-2076] 設計 wave を起票する。裁定は「後発決定は先行決定の実験同一性の論点を supersede
> しない。ただし技術的な設計着手は妨げないので、別実験になる点を明示して起票してよい」で確定済み。
> 設計文書に「これは先行実験と別の実験である」ことを明示的に書き、既存の実験同一性の主張を
> 上書きしないこと。着地すれば順序依存の後続も解禁される。実装ではなく設計と起票までが scope。
> 正本は worklog carry [T-2076] (entry 1184)。着手直前の local main から fresh worktree を作る。
> 規律 2 を緩めない。Codex author = D95。本題の設計だけ。仮想リスク向けの gate・検査・台帳・
> 一般化の追加は scope 外。

## scope

依頼の残件を確定し、済んだ carry を台帳上で閉じる。docs のみ (spool fragment 1 本)。
実装面の差分は持たない。

## 確定済みユーザー裁定

- D1451 (逐語: `verbatim/d1451.md`)
- D344 (逐語: `verbatim/d344.md`) — 却下理由は有効なまま。上書きしない。
- D1355 (逐語: `verbatim/d1355.md`)
- worklog carry [T-2076] entry 1184 (逐語: `verbatim/worklog-carry-t2076-entry1184.md`)

## 親が実測で確定した「依頼の前提を覆す新事実」

依頼は「実装ではなく設計と起票までが scope」と書くが、**設計・実装とも既に local main へ
着地している。** 親の実測アンカーは次のとおり。

| 依頼の要件 | landed main の実アンカー | 親の判定 |
|---|---|---|
| 設計と実装 | commit `23565ae55` 「[T-2145] sort SWO oracle の受理言語を検証済み IR へ縮める」。`git merge-base --is-ancestor 23565ae55 main` が真 | 済 |
| 「先行実験と別の実験である」の明示 | `.claude/agents/coder-v4-autonomous-sort.md:93` / `orchestrator/campaign/p3_s4_loop_sort.py:317` の `spec_content` | 済 |
| 既存の実験同一性の主張を上書きしない | `.claude/agents/coder-v4-autonomous-sort.md:94` / `orchestrator/campaign/p3_s4_loop_sort.py:321` | 済 |
| 規律 2 を緩めない | 受理言語を 79 値の閉じた IR へ狭める変更。行列の出所を候補実行から trusted evaluator へ移し、不一致は PASS でなく UNAVAILABLE | 済 |
| 順序依存の後続の解禁 | 後続は [T-2145] 自身。着地済みで carry から消えている | 済 |
| 一次資料 | worklog archive entry 1214 (`docs/archive/worklog-phase3-0902-1214.md`、逐語コピー: `verbatim/worklog-entry-1214.md`)、`output/insights/2026-09-02_t2145-sort-oracle-ir/` | 実在 |

残っているのは **`docs/worklog.md` の carry `- [T-2076] (1237)` が stale なことだけ**という判定である。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 依頼の要件は landed main で全て満たされており、新しい設計文書を書く必要はない。
- **(P2)** 残件は carry の是正だけであり、`[T-2076]` を `完了` (`remaining: none`) で閉じてよい。

## 不変条件

- 既に着地した [T-2145] の設計判断・記録を書き換えない。歴史記述の遡及改変をしない。
- D344 を supersede した扱いにしない。landed main の当該 2 行に触れない。
- 規律 2 を緩めない。受理集合・gate・oracle の実装面に一切触れない。
- canonical 3 台帳を直接編集せず `docs/spool/` の fragment だけを書く。

## 成果物の形

`docs/spool/worklog/` に fragment 1 本。`次の一手差分` の `完了` 節で `[T-2076]` を
`remaining: none` 付きで閉じる。base digest は land 先 local main の現物から取得済み:
`38ba6031237b016617cf9bb0f33c2a575a467c010a286bd9ba306c94a3e473ab`

## 分割方針

軽量版。設計択一は割れず、正しさ防壁に触れず、受理集合を変えないため段 2 と段 6 review 子を省く。
ただし本 wave の成果物は「既に済んでいる」という単一の主張そのものなので、その主張だけを
検査する read-only の子を 2 本立てる。

## DW-G05 (成果物影響)

stale carry を放置すると、[T-2076] が未着手として再び dev-wave へ投入され、既に着地した設計と
競合する第二の設計文書が生まれる。台帳の active 集合が事実と食い違ったままになる。
