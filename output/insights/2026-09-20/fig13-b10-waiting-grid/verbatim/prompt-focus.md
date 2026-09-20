単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (所見の採否と処置の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s6-adjudication.md
- review A の所見: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/review-A.md
- review B の所見: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/review-B.md
- fix1 (Codex) の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/fix1.md
- fix1 統合後の差分 (review 時点 680d6136d → 現 tip 46e3c0a4d、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/fix1-integrated-diff.patch
- 生成器 (現 tip): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py
- test (現 tip): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/orchestrator/tests/test_plot_b10_waiting_grid_forest.py
- figures README の fig13 節 (現 tip): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/README.md
- tools/plotting README の fig13 節 (末尾、縮約後): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/README.md
- 着地 provenance (再生成後): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.provenance.json
- 着地 PNG (再生成後。読めるなら見る): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.png
- report provenance JSON (`calibration` / `preregistration.spec.workloads` / `spec.execution` の実値の出所。600 KB なので `json.load` 相当で key を見る): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json
- producer の等価域分類規則の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/producer-2a338449b-relation.md
- 作図規約 (§6): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/FIGURE_CONVENTIONS.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

段 6 の敵対 review 2 本 (A: 過剰・削除、B: 正しさ境界・限定) の所見に対し、親が裁定 (採用 / 不採用 / refuted) を下し、Codex fix1 が B-1 (must-fix) / B-2 を、親が docs 所見 (A-1 / B-3、A-5) を直した。
これはその**焦点再レビュー**である (DW-O16)。セキュリティ調査ではない。読み取り専用 sandbox なので pytest 緑は要求しない。親は login で新 test の自走 (53 passed / 0 failed / 0 skipped) を済ませ、図を再生成 (rc=0) している。

# 依頼 — 所見ごとの closed / partial / regressed を判定する

## 点検項目

1. 所見対応表: A-1〜A-6、B-1〜B-3 のそれぞれについて closed / partial / regressed / not-adopted (親裁定どおり) を判定し、根拠 (file と関数名・節名、または差分の行) を 1 行で書く。
   特に B-1: (a) `calibration.records` == 1,000,000、`calibration.threads` == `execution.threads` == 48、skew "0.9" × 3、rratio 5 / 50 / 95、rmw "0"、max_ope "10"、extime_s 3、performance_reps 5 を report JSON の実値と照合し、
   (b) caption の `Conditions:` 文と図の脚注に records / skew (/ rratio) が出ているか、(c) README の日本語キャプション・§6 の項・拒否条件が実装と一致するか、(d) 親が書いた派生値 (「1,000,000」「0.9」「5 / 50 / 95」「3 秒」) を原データから照合する。
   B-2: 端点 test の 7 ケースが producer の逐語 (`>=` / `<=` inside、`<` / `>` outside) と同じ向きか。fixture 経由の端点 cell の test が生成器の経路を実際に通るか。
   A-2 (refuted): 親の refute 根拠 (producer の語彙・規則と同一) が正しいか。
2. 回帰: fix1 で固定文 8 文・禁句・図の形 (axes 3、μ 6 行、帯、空丸、四角)・閉包 2 関数の契約・pin・既存 key が変わっていないか。caption の新しい `Conditions:` 文が禁句や事前登録 §3 の逸脱を持ち込んでいないか。
   README の縮約 (tools/plotting) で必要な参照 (fig13 節・FIGURE_CONVENTIONS) が残っているか。
3. 変異 final に向けて: 段 4 の m0〜m14 と、裁定の m13a / m13b 分割、fix1 で足された条件検査 (records / threads / skew / rratio) に対する追加変異の要否 (fix1 は直接呼び出しで 4 件 KILLED と報告) を 1 行ずつ。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く)

## 所見対応表
id / 判定 (closed / partial / regressed / not-adopted) / 根拠 1 行。
## 回帰
上の 2 の結果 (無ければ「無し」と根拠)。
## 変異への所見
上の 3 の結果。
## 総括
regressed / partial の件数と要旨、着地してよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
