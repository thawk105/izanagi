# 親の追加実測 (段 2 投入後、2026-08-25)

measurements.md の続き。**段 2 のプラン起草者はこれを見ていない。**
段 3 のレビュアは、プランがこの型を扱えるかを必ず検討せよ。

## 層 2 (FOLDED.md の content_sha256 照合) は、単独では偽の「未着地」を出す

measurements.md は 5 本の fragment を `not-in-FOLDED` と報告した。
そのうち **3 本は実際には着地済み**だった。層 2 だけを見ると誤判定する。

### 型 A — fragment が別 wave 名へ re-home されてから fold された

`worktree-roadmap-workload-hint` の
`docs/spool/decisions/2026-08-19-roadmap-workload-hint-2.md`
(`content_sha256 = 4a72f7d5…`) は FOLDED.md に無い。しかしその本文は
`docs/decisions.md` の **D568** として逐語で着地済みである
(`## D568. workload descriptor に人間の自由記述方針ヒントを任意で許す (roadmap §1 協議改訂) (2026-08-19)`)。

経緯は `docs/failures.md` の F82 「再発: 2026-08-19 (4 度目)」に記録がある。
別 wave `workload-policy-hint-impl` がこの fragment を継承し、
`docs/spool/README.md` の「identity は (wave, namespace, slug)」規則に従うため
`git mv` で自 wave 名へ re-home した。frontmatter の `wave:` 行が変わるので
**whole-file の sha256 が変わる。** FOLDED.md には re-home 後の sha
(`ae26f17f…`, `wave: workload-policy-hint-impl`, `D:workload-policy-hint → D568`) が載っている。

**この fragment を今 fold すると D568 が二重採番される。**

### 型 B — 内容が canonical 台帳の archive 側へ着地している

親が各 fragment の本文から 40 文字超の distinctive な行を 3 本抜き、
`docs/worklog.md` / `docs/decisions.md` / `docs/failures.md` / `docs/archive/` を
`grep -rlF` で当てた結果:

```
roadmap-workload-hint      worklog fragment   2/3 hit  docs/archive/worklog-phase3-0819-710.md
rulings-20260818-floor-measurement worklog    3/3 hit  docs/archive/worklog-phase3-0819-670.md
cleanup-branches-20260825  failures fragment  0/3 hit  (どこにも無い)
cleanup-branches-20260825  worklog fragment   0/3 hit  (どこにも無い)
```

**真に未着地なのは `worktree-cleanup-branches-20260825` の 2 本だけ**である。
`docs/worklog.md` は定期的にローテーションされ `docs/archive/` へ移るため、
現行 worklog だけを見る照合は着地済みを未着地と誤判定する。

## この実測が設計へ課す要求

1. 層 2 の `not-in-FOLDED` を `not-landed` の根拠にしてはならない。層 3 へ落ちること。
2. 層 3 の逐語照合の探索範囲に `docs/archive/` を含めること。
3. spool fragment は whole-file sha だけでなく、frontmatter を除いた本文でも照合できること
   (あるいは、whole-file sha が外れたら本文照合へ落ちること)。
4. 「3 行中 2 行 hit」のような部分一致をどう扱うかを決めること。
   全一致でなければ `not-landed` と言い切ってよいのか、`indeterminate` か。

## 層 3 を全 9 本へ手で当てた結果 (親の正解データ)

`docs/spool/` を除く全 file について、branch の blob が (a) main tip の同 path と一致するか、
(b) `git log main --find-object -- <path>` で main の履歴に存在したかを測った。

```
t1484-backup-before-trailer-fix        12 file 全て一致 (6 が tip 一致、6 が履歴一致)
worktree-agent-ab4539bed30390c7f        1 file 履歴一致 (d2337813)
worktree-roadmap-workload-hint          1 file tip 一致
worktree-workload-policy-hint-impl-unitB/C
    9 file 中 4 が tip 一致、2 が履歴一致、3 が blob 不一致。
    blob 不一致 3 のうち 2 は追加行が main tip に逐語で存在。
    残り 1 (orchestrator/tests/test_reflux_originless_compatibility.py) は
    不透明な originless baseline の巨大 1 行で、blob も逐語も一致しない。
```

補助的な意味照合として、この branch が導入した識別子 `policy_hint` の分布を測った。

```
branch で policy_hint を含む file 集合 ⊆ main で policy_hint を含む file 集合 (差分は空)
出現数: branch 17、main 95
```

すなわち機能自体は main へ着地し、さらに拡張されている。
`test_reflux_originless_compatibility.py` の 1 行は main の状態に追随して再生成される
不透明 blob であり、**定義上、逐語では決して一致しない。**

### ここに設計上の緊張がある。段 3 で裁定してほしい

(P2) の連言規則をそのまま適用すると、この 1 file のせいで
`worktree-workload-policy-hint-impl-unitB` / `unitC` は branch 全体が `indeterminate` になる。
一方、先行の手作業 (`worktree-cleanup-branches-20260825` の記録) はこれを
「内容としては main へ着地済み」と結論している。

- 保守的に `indeterminate` へ倒すのは、削除の可否を決める用途では正しいのか。
- それとも再生成される不透明 blob を層 3 の対象から外す規則が要るのか。
  外すなら、その規則が「都合の悪い file を除外する」抜け道にならないと言えるか。
