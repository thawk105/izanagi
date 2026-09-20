単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める。末尾の追記は変異経路の訂正): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s5-author.md
- 統合後の差分 (着手時 local main b7f970dfa → wave tip 04ae82a1c、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_b7_fixed5_regression.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/orchestrator/tests/test_plot_b7_fixed5_regression.py
- figures README の fig10 節 (末尾の節。一覧表の fig10 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/README.md
- 着地 provenance: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.provenance.json
- caption_source の稿 (値・判定・限定の出所): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/FIGURE_CONVENTIONS.md
- 段 6 の成果物影響の基準 (`DW-G05`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/dev-wave/core.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo に足した**論文図 (fig10) の生成器・test・README の設計レビュー**である。セキュリティ調査ではない。目的は、
(1) 依頼の scope (「本題の作図だけ — gate・検査・台帳・一般化の追加は scope 外」、図が言えるのは稿の床値判定まで) を超えた実装・文書・主張が入っていないか、
(2) 削除・局所修正で済むのに足された物が無いか、(3) 親 brief / 裁定自身の前提・実測値の一般化に誤りが無いかを点検することである。
差分は commit 済みで、図 3 成果物の生成 (login で `plot_b7_fixed5_regression.py` を実 durable root に対して実走、rc=0) と README 3 file の編集は**親が実行済み**である。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。

# 依頼 — レンズ「過剰・削除」で plan v2 と実装を点検する

## 点検項目

1. scope 超過: 依頼文 (brief 冒頭) と D2162「scope 外 = certification の昇格・新 protocol・追加 gate」「床値判定はコードに入れず稿で計算」に照らし、生成器・test・README が
   新しい判定経路・gate・台帳・一般化 (他 attempt / 他 study への流用口、CLI からの leaf 差替え等) を足していないか。`RECORDED_JUDGMENT` との整合検査は
   「判定を作る」に当たるか当たらないかを、裁定 (P2) の根拠込みで評価する。
2. 主張の過剰: caption・README fig10 節・一覧行・paper-story README の文言が、稿 §0.4 / §4 の限定を超えて何かを言っていないか
   (B-7 充足・有意差・優越・昇格・機序・同一 binary・同時実行・anomaly 0 の出所)。逆に稿が言う限定のうち caption が落としているものがあれば指摘する。
3. 削除候補: 生成器・test・README の中で、無くても成果物の値・受理集合・参照が変わらない部分 (冗長な検査、重複文、fig9 からの流用で本図に無意味な項目)。
   各候補について「削除しても DW-G05 の意味で何も変わらない」か「変わる」かを 1 行で書く。
4. 親 brief / 裁定の点検: 前提 (P1)〜(P3)、実測値 (SHA-256、標本の所在、matplotlib の版) と一般化、軽量版で段 2・3 を省いた判断、変異事前登録 13 件の単一理由性
   (F820: 同じ入力を前後・内側の別の層が拒否して赤理由が 1 つに絞れないもの) を点検する。
5. 文書の置き場: README の記述が正本 (FIGURE_CONVENTIONS、稿、decisions) の逐語再掲になっていないか、逆に正本を指すべき所で独自定義をしていないか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `A-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## 削除候補
上の 3 の結果。
## 親 brief / 裁定への所見
上の 4 の結果。単一理由性が疑わしい変異 id を列挙。
## 総括
must-fix の件数と要旨、plan v2 をこのまま採ってよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
