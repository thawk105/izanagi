単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/artifacts/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/author.md
- 統合後の差分 (着手時 local main 947fd160a → wave tip ffcee706b、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/plot_a2_certification.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/orchestrator/tests/test_plot_a2_certification.py
- figures README の fig11 節 (末尾の節。一覧表の fig11 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/README.md
- paper-story README (results 表の 2026-09-18 A-6 行と、results 系列の規則直後の「A-6 単独稿の限定 11 への追補」段落): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/README.md
- 着地 provenance: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json
- caption_source の稿 (値・判定・限定の出所。§0 主判定文、§1.4、§2.1〜§2.3、§3.1、§3.4、§4 限定 1〜12、§5.1〜§5.2): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/results/2026-09-18-a6-certification-reject.md
- A-6 権威 bytes: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json
- A-6 raw manifest: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json
- 論文ストーリー 2026-09-20 版の §8 A-6 (「第 2 — A-6 (read-heavy)」で検索): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/2026-09-20.md
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/FIGURE_CONVENTIONS.md
- 段 6 の成果物影響の基準 (`DW-G05`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/dev-wave/core.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo の**論文図 (fig11) の caption・README・provenance が一次資料 (稿・権威 bytes) と整合しているか、正しさの境界を守っているかの設計レビュー**である。
セキュリティ調査ではない。差分は commit 済みで、図 3 成果物の生成と README 2 file の編集は**親が実行済み**である (`tools/plotting/README.md` の 1 行は受入直前に親が足す予定で、
まだ差分に無い — これは欠落ではない)。読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。親は login で焦点走 (111 passed) と全史 provenance 監査 (違反なし) を済ませている。

# 依頼 — レンズ「正しさ境界・一次資料との整合・実効性」で実装と文書を点検する

## 点検項目

1. caption と稿の整合: 着地 provenance の `caption` の各文を稿 §0 主判定文・§2.1〜§2.3・§3.1・§3.4・§4 限定 1〜12 と突き合わせ、
   (a) 稿が言わないことを caption が言っていないか (有意差・優越・機序・再現・研究の成否・read-heavy 一般への外挿・B-10 との pool)、
   (b) 稿の限定のうち caption が落としているもの、(c) 値 (attempt / request / host / 時刻 / 効果 −5.7841% / median / abort 率 / 条件 / pin / cell 数) が権威 bytes と一致するか。
   時刻 `2026-09-07T16:29:41…+00:00` (UTC) と稿の「2026-09-08」(JST) の関係も点検する。
2. 性能と正しさの分離 (D1993 項 2、絶対規律 1・2): caption・suptitle・脚注・README が「性能の reject」と「別走行の正しさ certified」を 1 文に畳んでいないか、
   正しさの certified を性能の認証や採用根拠へ滑らせていないか、逆に性能の reject を正しさ証拠の欠落と読ませていないか。
3. 受理集合と fail-closed: 生成器の一般化 (`STUDY_PROFILES`、`6 × N`、`N` 一意、`2 × N` axes、`_study_label` の互換既定、caption_source 追加) が
   偽の受理 (改竄 provenance・study 欠落・legacy A-6・第 3 study・重複 request) を通す経路を作っていないか。着地 test `test_landed_fig11_…` が README の
   「## 着地 bytes の SHA-256」3 行と現物、caption の逐語収録、caption_source の現 SHA-256 を実際に照合しているか (恒真になる書き方が無いか)。
4. fixture の実寸性 (FIGURE_CONVENTIONS §10): A-6 fixture が production 入力と同じ形 (1 workload × 2 cell × 5 標本、verify 12 記録、receipt 2 frame × 2 cell、6 file) で、
   本物の Figure を layout check へ通しているか。fixture が甘い (現行 hash 差し込み・依存先 stub・過剰決定で単一理由にならない) 箇所。
5. README (figures / paper-story) の事実命題: fig11 節と追補段落の日付・SHA-256・file 数・値・裁定番号 (D12 / D1993 / D1637 / T-2430) が一次資料と一致するか。
   「稿 bytes 不変」「凍結物」「append-only」の扱いが results 系列の規則と矛盾しないか。図の一覧行の記述が他行 (fig6 / fig10) の型と整合するか。
6. 親 brief / 裁定自身: (P1)〜(P3) の前提と実測値、変異事前登録 m0〜m9 のうち殺せない・単一理由でないもの (author は m6 に producer 側の拒否層があると報告した) と再照準案。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `B-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## caption と稿の対応表
caption の文ごとに、出所 (稿の節番号 / 権威 bytes の field) と判定 (一致 / 過剰 / 欠落) を 1 行。
## 親 brief / 裁定への所見
上の 6 の結果。単一理由性が疑わしい変異 id を列挙し、再照準案を 1 行ずつ。
## 総括
must-fix の件数と要旨、GO / NO-GO を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
