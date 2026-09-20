単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/artifacts/s1-brief.md
- 段 4 裁定と plan v2・変異事前登録 (レビュー対象に含める): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s4-adjudication.md
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/author.md
- 統合後の差分 (着手時 local main 482f19b88 → wave tip 680d6136d、画像 2 file を除く全文。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/review-diff.patch
- 生成器 (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py
- test (commit 済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/orchestrator/tests/test_plot_b10_waiting_grid_forest.py
- figures README の fig13 節 (末尾の節。一覧表の fig13 行も): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/README.md
- 着地 provenance (caption の逐語を含む): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.provenance.json
- 着地 PNG (図そのもの。読めるなら見る): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/figures/fig13_b10_waiting_grid_forest.png
- caption_source の稿 (値・限定の出所。§0.2 判定しないこと、§2.2、§2.4、§2.7、§3 限定 1〜19、§4.1、§4.2): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md
- 事前登録 発効版 §3「何を主張し、何を主張しないか」・§8「報告に必ず含めるもの / 書いてはならないこと」の逐語 (git blob の写し): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/prereg-77b33e37d-s3-s8.md
- report provenance JSON (tracked、判定の一次権威。600 KB なので `json.load` 相当で key を見る): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json
- 作図規約: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/FIGURE_CONVENTIONS.md
- 段 6 の成果物影響の基準 (`DW-G05`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/docs/dev-wave/core.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo の**論文図 (fig13) の正しさ境界・限定の言い方・整合のレビュー**である。セキュリティ調査ではない。目的は、
(1) 図・caption・README が report の判定と稿の限定を正しく写し、事前登録 §3 の「書ける主張」の範囲を超えていないか、(2) 生成器の照合が「判定を作らない」を守り、fail-closed であるか、
(3) provenance の束縛 (tracked 2 file の pin、稿の caption_source、repo 外 2 file) と閉包 test が着地後の drift を実際に検出するかを点検することである。
差分は commit 済みで、図 3 成果物の生成 (login で実 evidence root に対して実走、rc=0) と README 2 file の編集は**親が実行済み**である。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。親は login で新 test の自走 (49 passed / 0 failed / 0 skipped) を済ませ、計算ノードで焦点走を投入中である。

# 依頼 — レンズ「正しさ境界・限定の言い方・事前登録 §3 逸脱」で実装と文書を点検する

## 点検項目

1. 言い方の逸脱: caption (provenance の `caption`、README の英文) と README の日本語キャプション正文・節本文・一覧表の行が、(a) 区間が ±3.0% の内側にあることを等価性の成立と読ませていないか、
   (b) 36 cell の個別有意差を判定していると読ませていないか、(c) 静的右 tail の 2 稿 / fig8 / fig8b と合成・比較していないか、(d) 機序 (脱同期・総待ち量) を述べていないか、
   (e) `binary` / ladder / 用量反応 / 直交切り分けの一般化を言っていないか、(f) 性能の認証・採用根拠・研究の成否・B-10 項目の閉鎖を言っていないか、(g) 検出力を言っていないか、
   (h) 事前登録 §8「書いてはならないこと」4 項に触れていないか。図中の文字 (panel 題、脚注、凡例) も同様。逸脱があれば逐語で示し、稿のどの限定に反するかを書く。
2. 値の写し: caption / README / panel 題の数値 (raw p の分数と小数、Holm p、和の符号と値、inside 32 / overlaps 4 / outside 0、負の点推定 1、区間下限が正 8、境界跨ぎ 4 cell の同定、条件、request、commit) が
   report provenance JSON と稿 §2.2 / §2.4 と一致するか。`sum of paired effects` の桁 (`:+.17g`) と稿の 5 桁 (+0.11203 等) の関係が誤解を生まないか。
3. 「判定を作らない」の検証: `_authority_data` の再計算 (differences、Holm、raw p 分母、cell 効果・区間、等価域の再分類、曝露) が report の値と一致を要求する**照合**であって、report に無い値を図・caption に出していないか。
   出しているなら何か (例: `sum_of_differences`、`direction`、`raw_p_numerator_2pow18`、`block_effects`、負の点推定数、区間下限が正の数) と、それが稿 §2.2 / §2.3 / §2.4 の本稿再計算と同じ地位 (転記の検算) と言えるか。
4. fail-closed と閉包: (a) `validate_repo_closure` が repo 外を読まずに provenance の全 key を再構成して照合しているか、drift (caption 1 字、artist 1 値、cells 1 値、summary、report の epoch) を検出するか、
   (b) 着地 test `test_landed_fig13_repo_closure_and_caption_when_present` が README の SHA 3 行と caption の逐語収録を実際に読んでいるか、bundle 欠落を skip にしていないか、
   (c) `test_document_values_match_report_json` / `test_pins_match_results_document` の parse が稿の表の列を正しく取っているか (列位置のずれ、`**\`different\`**` の装飾、`(= 6702 / 2^18)` の括弧)、
   (d) `_relation` の境界 (`>=` / `<=`) が report の分類と同じ向きか (report の 36 cell に境界上の値は無いが、fixture では踏んでいるか)、
   (e) receipt / job 結果の identity 照合で `job_script_sha256` を job 結果にも要求していない理由 (schema に無い) が正しいか。
5. 実寸 fixture (FIGURE_CONVENTIONS §10): fixture が 135 record / 36 cell / 3 族 / 参照点 3 種 / report .md の 2 節を production と同じ形で作っているか、境界跨ぎ・負の点推定・正の区間下限を各 1 以上含むか、
   本物の Figure を layout check へ通しているか。
6. 変異事前登録 m0〜m14: 各変異を実際に殺す test が author の表のとおりか、同じ入力を別の層が先に拒否して単一理由にならないものはどれか (author は m4 と m13 を挙げた)。再照準案を 1 行ずつ。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 所見
各所見を `B-1`〜 で採番し、種別 (must-fix / should / nit / backlog)、対象 (file と関数名または節名、caption なら逐語)、内容、放置時に成果物 (図・caption・README・受理集合) がどう変わるか (DW-G05 の 1 行) を書く。
## 値の写しの照合結果
上の 2 の結果 (一致 / 不一致を項目ごとに)。
## 変異事前登録への所見
上の 6 の結果。
## 総括
must-fix の件数と要旨、着地してよいかの判定 (GO / NO-GO) を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
