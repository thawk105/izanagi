単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/artifacts/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/author.md
- 統合後の差分 (着手時 local main 947fd160a → wave tip ffcee706b、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/plot_a2_certification.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/orchestrator/tests/test_plot_a2_certification.py
- figures README の fig11 節 (末尾の節。一覧表の fig11 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/README.md
- 着地 provenance: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json
- fig6 (A-2) の着地 provenance (A-2 不変の基準): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json
- caption_source の稿 (値・限定の出所): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/results/2026-09-18-a6-certification-reject.md
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/FIGURE_CONVENTIONS.md
- 段 6 の成果物影響の基準 (`DW-G05`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/dev-wave/core.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo の**論文図 (fig11) のための生成器一般化・test・README の設計レビュー**である。セキュリティ調査ではない。目的は、
(1) 依頼の scope (「本題の作図だけ — 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」) を超えた実装・文書・主張が入っていないか、
(2) 削除・局所修正で済むのに足された物が無いか、(3) 親 brief / 裁定自身の前提・実測値の一般化に誤りが無いかを点検することである。
差分は commit 済みで、図 3 成果物の生成 (login で `plot_a2_certification.py` を A-6 の実 durable root に対して実走、rc=0) と README 2 file の編集は**親が実行済み**である
(`tools/plotting/README.md` の 1 行は受入直前に親が足す予定で、まだ差分に無い — これは欠落ではない)。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。親は login で焦点走 (111 passed) と全史 provenance 監査 (違反なし) を済ませている。

# 依頼 — レンズ「過剰・削除」で plan v2 と実装を点検する

## 点検項目

1. scope 超過: 依頼文 (brief 冒頭) に照らし、生成器・test・README が新しい判定経路・gate・台帳・一般化 (第 3 の study への流用口、CLI からの leaf 差替え、
   N=0 や N≥3 の受理、legacy profile の A-6 受理等) を足していないか。`STUDY_PROFILES` exact 2 件と `6 × N` 閉包は「必要最小の一般化」か、それとも過剰か。
2. A-2 不変の検証: A-2 (fig5 / fig6 / fig7) の caption・artist・provenance 射影が byte 単位で不変であることを、差分と fig6 provenance から静的に確かめる。
   `_study_label` の「`study` key が無ければ A-2」という互換既定が、A-6 の着地 provenance の改竄 (study key 削除) を A-2 として通す経路にならないか
   (`validate_repo_closure` の caption 再構成と tracked_inputs の caption_source 行の照合を追って評価する)。
3. 削除候補: 生成器・test・README の中で、無くても成果物の値・受理集合・参照が変わらない部分 (冗長な検査、重複文、fig10 からの流用で本図に無意味な項目、
   `'four' if len == 4 else 'two'` のような到達しない分岐)。各候補について「削除しても DW-G05 の意味で何も変わらない」か「変わる」かを 1 行で書く。
4. 親 brief / 裁定の点検: 前提 (P1)〜(P3)、実測値 (SHA-256、標本の所在、file 数、request 数) と一般化、軽量版で段 2・3 を省いた判断、
   変異事前登録 m0〜m9 の単一理由性 (F820: 同じ入力を前後・内側の別の層が拒否して赤理由が 1 つに絞れないもの。author は m6 に producer 側の拒否層があると報告した)。
   (P1) 「稿 bytes を変えず README の追補で限定 11 を更新する」が依頼文「単独稿の限定 11「図は無い」を更新」を満たすか、満たさないなら何が要るか。
5. 文書の置き場: README の記述が正本 (FIGURE_CONVENTIONS、稿、decisions) の逐語再掲になっていないか、逆に正本を指すべき所で独自定義をしていないか。
   paper-story README の追補段落が results 系列の append-only 規則と矛盾しないか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `A-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## 削除候補
上の 3 の結果。
## 親 brief / 裁定への所見
上の 4 の結果。単一理由性が疑わしい変異 id を列挙し、再照準案を 1 行ずつ。
## 総括
must-fix の件数と要旨、plan v2 をこのまま採ってよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
