## 所見

- **[重大度: blocker] 現役設計文書の must-fix が未着地**
  - 主張: [T-2145] 自身が現役 runbook の旧保証記述を must-fix・親担当と裁定したのに、現在の `main` でも旧 D344 型の動的反例探索として記述されたままであり、「全要件が済んだ」は成立しない。
  - 根拠: `output/insights/2026-09-02_t2145-sort-oracle-ir/s6-review-adjudication.md:49-55`、`docs/phase3-s5-sort-runbook.md:190-205`、`docs/phase3.md:317-324`。正しい新保証は `output/insights/2026-09-02_t2145-sort-oracle-ir/README.md:60-64`。記録 commit `41740488a` は前二つの現役文書を変更していない。
  - 親 brief のどの主張を崩すか: `brief.md:43-48` の「残件は stale carry だけ」「依頼の要件は全て満たされ、新しい設計文書は不要」を崩す。
  - 成果物への影響: このまま閉じると、現役 runbook と phase 正本が新 IR 実験を旧 raw-C++ 実験の proof chain で説明し、候補 failure の帰属や s6 の対象範囲も誤ったまま残る。

- **[重大度: must-fix] D1355 の「逐語」コピーが末尾を欠く**
  - 主張: `verbatim/d1355.md` は canonical D1355 の最後の却下選択肢を欠いており、逐語コピーではない。
  - 根拠: `verbatim/d1355.md:22-28` はそこで終わるが、`docs/decisions.md:43162-43169` にはさらに「本 wave で設計へ着手する — 生死確認の前に機構を作ることになり DW-G01 に反する」がある。差分照合は不一致だった。
  - 親 brief のどの主張を崩すか: `brief.md:26` の「D1355（逐語: verbatim/d1355.md）」という資料同一性の主張を崩す。
  - 成果物への影響: 放置すると裁定資料が逐語と偽って設計着手順序に関する却下理由を脱落させ、台帳 closure の根拠追跡が不正確になる。

## 検査したが崩せなかった点

- `23565ae555f9aa7d02c285fd7f9194d0ada62f74` は実在し、件名も brief と一致する。`git merge-base --is-ancestor 23565ae55 main` は `rc=0` だった。記録 commit `41740488a` も `main` の祖先である。
- `.claude/agents/coder-v4-autonomous-sort.md:93-94` と `orchestrator/campaign/p3_s4_loop_sort.py:317-322` は brief の行番号・文言どおりで、「別実験」「D344 を supersede しない」を明記している。
- 設計資料そのものは存在する。特に insight の `README.md:6-8`、`s1-brief.md:16-19`、`verbatim/s2-plan.md:1-7`、`s4-adjudication.md:107-114` は設計内容と実験同一性の境界を具体的に記述している。したがって必要なのは第二の新規設計文書ではなく、上記 blocker の現役文書是正である。
- D344・D39・実験同一性・supersede を tracked Markdown/Python/text で横断検索したが、[T-2145] を D344 の supersede や D39 と同じ実験だと明示する現行記述は見つからなかった。
- admission は静的には縮小方向である。`sort_swo_oracle.py:789-846` が正準 token 列だけを受理し、`:906-914` の domain は 79 値、`p3_s4_loop.py:379-398` が正準形を再 materialize する。実 TU 不一致は `sort_swo_oracle.py:2981-2985` から `UNAVAILABLE` へ流れ、`:3476-3479` の PASS へ倒れない。
- D344、D1451、carry entry 1184、worklog entry 1214 の逐語コピーは canonical repo 文面と一致した。相違は上記 D1355 だけだった。
- worktree branch は reflog 上 `7013ea81f` の `main` から作成され、その後 `main` が進んでいるため、brief の fresh-worktree 前提は崩れなかった。
- [T-2145] は実装・記録とも着地済みで、entry 1214 では完了扱いとなり後続 carry から消えている。一方、現在の `docs/worklog.md:3416` に [T-2076] 自身だけが残る点も確認した。

## 確かめていない点

pytest、compile、実 TU、変異走は実行していない。したがって記録された「766 passed / 2 skipped」「11/11 KILLED」を独立の緑としては認定しない。実験同一性そのものの再裁定も行っていない。指定された射影資料と T-2145 insight 全内容は読めており、権限による未読範囲はない。

## 総括

親の (P1) はそのまま採用できない。新しい独立した設計文書をもう一本作る必要はないが、[T-2145] が自ら must-fix とした現役 runbook・phase 正本の是正が未着地であるため、「要件は全て満たされ、残件は carry だけ」という前提が偽である。D1355 の逐語コピーも修正が必要であり、それらを閉じる前に `[T-2076] remaining: none` として終了させるべきではない。