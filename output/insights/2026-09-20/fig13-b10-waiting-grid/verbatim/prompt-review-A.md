単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/artifacts/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/author.md
- 統合後の差分 (着手時 local main 482f19b88 → wave tip 680d6136d、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/orchestrator/tests/test_plot_b10_waiting_grid_forest.py
- figures README の fig13 節 (末尾の節。一覧表の fig13 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/README.md
- 着地 provenance: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.provenance.json
- 着地 PNG (図そのもの。読めるなら見る): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.png
- caption_source の稿 (値・限定の出所。§0.2、§2.2、§2.4、§3 限定 1〜19、§4.1、§4.2): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/FIGURE_CONVENTIONS.md
- 段 6 の成果物影響の基準 (`DW-G05`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/dev-wave/core.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo の**論文図 (fig13) のための生成器・test・README の設計レビュー**である。セキュリティ調査ではない。目的は、
(1) 依頼の scope (「本題の作図だけ — 仮想リスク向けの gate・検査・台帳の追加は scope 外。README の results 表は触らない」) を超えた実装・文書・主張が入っていないか、
(2) 削除・局所修正で済むのに足された物が無いか、(3) 親 brief / 裁定自身の前提・実測値・一般化に誤りが無いかを点検することである。
差分は commit 済みで、図 3 成果物の生成 (login で実 evidence root に対して実走、rc=0、PNG は author の probe と bit 一致) と README 2 file の編集は**親が実行済み**である。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。親は login で新 test の自走 (49 passed / 0 failed / 0 skipped) を済ませ、計算ノードで焦点走を投入中である。

# 依頼 — レンズ「過剰・削除」で plan v2 と実装を点検する

## 点検項目

1. scope 超過: 依頼文 (brief 冒頭) に照らし、生成器・test・README が新しい判定経路・gate・台帳・一般化を足していないか。特に (a) `REPORT_SUBMITTED_EPOCH` / `REPORT_COMPLETED_EPOCH` の定数化
   (repo 外 bytes の値を生成器の定数に写して repo closure でも要求する) は必要最小か、それとも過剰か、(b) `RELATIONS` に実例の無い `outside-equivalence-range` を持つことの是非、
   (c) `report .md` の Holm 3 行・cell 36 行の parse 照合は依頼の範囲か、(d) `_relation` の再分類・Holm 再計算・raw p の 2^18 整数性は「判定を作らない」と両立するか (照合であって生成でないか)。
2. 削除候補: 生成器・test・README の中で、無くても成果物の値・受理集合・参照が変わらない部分 (冗長な検査、重複文、fig10 / fig11 節からの流用で本図に無意味な項目、到達しない分岐、
   `crosschecks` の恒真 field)。各候補について「削除しても DW-G05 の意味で何も変わらない」か「変わる」かを 1 行で書く。
3. 図の形 (P1) の過剰: 3 block の灰色 tick、constant 参照の空丸 18 個、panel 題 3 行、凡例 5 項目、脚注 2 行は依頼「1 枚の forest 型の図」に対して過剰か。読み取りを妨げる要素があれば指摘。
4. 親 brief / 裁定の点検: 前提 (P1)、実測値 (SHA-256、field の実在、値域)、軽量版で段 2・3 を省いた判断、変異事前登録 m0〜m14 の単一理由性 (F820: 同じ入力を前後・内側の別の層が拒否して赤理由が 1 つに絞れないもの。
   author は m4 を「定数照合と CI 式の分割」、m13 を「境界正例と負例が同一 test」と報告した)。再照準案を 1 行ずつ。
5. 文書の置き場: README の記述が正本 (FIGURE_CONVENTIONS、稿、decisions) の逐語再掲になっていないか、逆に正本を指すべき所で独自定義をしていないか。
   「稿の限定 11「論文図は無い」は起草時点の事実」「results 表は触らない」の書き方が絶対規律 7 (当時の事実と現行の適合を分ける) と整合するか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `A-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## 削除候補
上の 2 の結果。
## 親 brief / 裁定への所見
上の 4 の結果。単一理由性が疑わしい変異 id を列挙し、再照準案を 1 行ずつ。
## 総括
must-fix の件数と要旨、plan v2 をこのまま採ってよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
