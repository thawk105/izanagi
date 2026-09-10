## 所見

- **[重大度: must-fix] 同じ着地で解消済みの [T-1700] も active のまま残っている**
  - 主張: [T-1700] の最新実体は「検証済み中間形式案を別変更単位で比較裁定へ回す」ことであり、その比較裁定 D1355 と実装 [T-2145] は完了済みなので、本 wave の同じ fragment で `[T-1700]` も `完了`、`remaining: none`、`base: eeb1ffd2fbafd98b7f69f79e29d067dcdcf0dabf30c2ecbd61a2fa2801f6e0b8` として閉じるべきである。
  - 根拠: `docs/archive/worklog-phase3-0825-956.md:706`、`docs/decisions.md:43141`、`docs/archive/worklog-phase3-0902-1214.md:1`、`docs/archive/worklog-phase3-0902-1214.md:64`、`docs/worklog.md:3306`、commit `23565ae55`
  - 親 brief のどの主張を崩すか: 「残っているのは [T-2076] の stale carry だけ」と、`完了` 節を `[T-2076]` 1 件だけにする成果物設計を崩す。
  - 成果物への影響: 放置すると候補由来の関係行列を trusted evaluator へ移す作業が未処理として残り、[T-2076] を閉じても active 集合と landed main の事実が食い違う。

## 検査したが崩せなかった点

- [T-2076] の carry 鎖は、worktree の `docs/worklog.md:3416` にある `(1237)` から各エントリを一段ずつ遡り、entry 1184 の実体本文 `docs/archive/worklog-phase3-0902-1184.md:355-357` に到達した。途中に別の実体更新はない。
- `tools/spool_fold.py --base-digest '[T-2076]'` は親の値 `38ba6031237b016617cf9bb0f33c2a575a467c010a286bd9ba306c94a3e473ab` を返した。検査中に local main は `39086303b` へ進んでいたが、main 側の実体本文も byte 同一で、同じ digest だった。
- 「別実験である」「D344 を supersede しない」は `.claude/agents/coder-v4-autonomous-sort.md:93-94` と `orchestrator/campaign/p3_s4_loop_sort.py:317-322` に明記されている。D344 自体も `docs/decisions.md:15206-15229` に残っている。
- [T-2076] を明示的に待っていた後続は [T-2145] だけだった。起票時の依存は `docs/archive/worklog-phase3-0901-1149.md:413-420`、完了は `docs/archive/worklog-phase3-0902-1214.md:64-66` で確認した。tracked worklog/archive の ID・意味検索でも、現在 [T-2076] を待つ別の active 項目は見つからなかった。
- [T-2237] は残っているが、IR 文法版を build cache key にも一般化するかという別の裁定事項であり、[T-2076] の残件ではない (`docs/archive/worklog-phase3-0902-1214.md:488-493`)。
- [T-2076] 自体には残件がないため、`更新` ではなく `完了` と `remaining: none` が正しい。
- fragment の中核形式も正しい。`完了` item には `remaining: none` と実体 digest の `base:` が必要 (`docs/spool/worklog/README.md:64-88`)。[T-2076] は現存 active item で同じエントリの `完了` に置くため、`title:` の先頭に `[T-2076]` を書ける条件も満たす (`docs/spool/worklog/README.md:101-106`)。
- [T-1700] の是正は新しい設計・一般化ではなく、[T-2145] の同じ着地に対する stale carry の修正であるため、本 wave の台帳是正 scope 内と判定する。

## 確かめていない点

- 親 brief には実際の fragment bytes がないため、ファイル名、frontmatter 全字段、`## 本文` と `## 次の一手差分` の二つの H2、末尾 newline は検査していない。実 fragment では `docs/spool/README.md:28-49` と `docs/spool/worklog/README.md:5-15` を満たす必要がある。
- `check_docs.py`、fold dry-run、pytest は実行していない。今回は read-only の静的検査と digest lookup のみである。
- [T-2145] のテスト結果は再実測していない。着地記録と commit 内容だけを検査した。

## 総括

(P2) は条件付きで採用してよい。[T-2076] については残件なしであり、`更新` ではなく `完了` (`remaining: none`) が正しい。ただし「stale carry は [T-2076] だけ」という部分は誤りで、同じ成果によって終端した [T-1700] も同じ fragment の `完了` 節で閉じなければならない。したがって親 brief と成果物設計は `[T-2076]` 1 件から `[T-2076]`・`[T-1700]` の2件へ修正が必要である。