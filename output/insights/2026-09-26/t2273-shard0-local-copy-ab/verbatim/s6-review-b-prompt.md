単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/verbatim/T-2273-origin.md — 依頼の逐語 (「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — 段 4 裁定。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s5-author-l-out.md、s5-author-p-out.md — 実装子の最終報告。
- 実装差分: wave 木 /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy の commit `eb65d322f` (`git show eb65d322f`)。
- 計測 probe (repo 外、land しない): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ と改作元 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/。

## 目的 (レンズ B: 過剰・削除)

段 6 敵対レビュー。実装を守る側に立つな。

1. 差分 (+100/−2) のうち、本題 (共有 builder の複製元を session 局所の写しへ) と段 4 裁定の正例・変異 kill に不要な行、より少ない行で等価にできる箇所、既存の仕組みと重複する箇所を挙げよ。逆に削ると M1〜M5 の kill や受理集合不変の証拠が失われる部分は残せと言え。
2. 仮想リスク向けの gate・検査・一般化・互換層が紛れ込んでいないか (例: source_root ごとの digest による写しの多重化は本題に必要か、必要なら理由)。
3. 新規 test が重すぎないか (受入の所要を増やさないか、実 repo を読まないか)。既存の実 builder 検査への追加 assert が test 所要を増やさないか。
4. 計測 probe の改作に、事前登録 (s4-ruling.md) にない判定・閾値・分岐が足されていないか。前回版から不要な台帳固有の処理が残っていないか。

read-only で書込可能 tmp が無いので静的検査でよい。テストの実測は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` (番号付き。重大度 must-fix / should / nit、根拠 file:line、放置時の影響 1 行、最小是正)
- `## 総括` (3〜6 行。GO / 修正後 GO / NO-GO)
