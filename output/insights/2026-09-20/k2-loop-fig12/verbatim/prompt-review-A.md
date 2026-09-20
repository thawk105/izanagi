単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s1-brief.md
- 段 4 裁定 (plan v2・JSON 内容の下書き・変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s4-adjudication.md
- 段 5 author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s5-author.md
- 段 5 の統合 patch (レビュー対象の差分そのもの): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s5-author.patch
- 生成器 (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/plot_k2_loop_flow.py
- 流れ JSON (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/k2_loop_flow_2026-09-20.json
- test (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/orchestrator/tests/test_plot_k2_loop_flow.py
- 親が実データで生成した provenance (drawn_items・arrows・caption の現物): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/scratch/fig12_k2_manual_loop_dataflow.provenance.json
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/FIGURE_CONVENTIONS.md
- 雛形 (先例、比較用): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/plot_arc_status.py
- caption_source の稿: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。書込可能 tmp が無いので pytest 緑は要求しない — 静的検査でよい。テスト実測は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 前置き — この依頼の性質

研究用 repo の**論文用の説明図 (matplotlib の模式図) の生成器・入力 JSON・単体 test** の敵対レビューである。セキュリティでも攻撃でもない。生成器は凍結済みの稿 (Markdown) から人が JSON へ写した「3 巡のデータフロー」を描くだけで、判定・値・認証を再計算しない。**性能値は図のどこにも出ない**設計である。親 brief と段 4 裁定自身も検査対象である。

# 依頼 — レビュー A: 過剰・削除レンズ + 図の過剰主張

## レンズ A (DW-S03 の「過剰・削除」)

1. **研究前進に対して過剰なもの**: 生成器・test・JSON schema のうち、brief の完了判定 (3 成果物・README 節・test 緑・変異・受入・land) に不要な機構、汎用化、将来のための抽象、fig3b の雛形に無い追加検査で研究前進に寄与しないもの。削除・局所化できるか、削除したら何が失われるかを 1 件ずつ書く。
2. **恒真な検査**: 生成器の検査 (schema・enum・anchor の一意性・role frontmatter の一致・自由文の数量・layout・矢印線分 × Text の交差・drawn_items の照合・no-clobber) のうち、入力を変えても赤にならない (恒真) もの、または test が生成器の実体を通さず (stub・monkeypatch・自前 bbox) 緑になっているもの。
3. **親 brief / 裁定の攻撃対象 (P1)**: 図に backoff の提案値 (20 / 25 / 20 / 10) と job id を描く裁定は、「性能値は載せない — 3 走の値は改善・退行の根拠にしない」という依頼の意図に反して**性能主張・軌跡 (値が下がっている) として読める**か。読めるなら、(a) 値を消す、(b) 値は残し caption / 凡例で「backoff literal であって結果ではない」を強める、(c) 提案の同一性を値でなく instance 名だけで示す、の択と推奨を書く。
4. **図の過剰主張**: drawn_items・arrows・caption の文言で、稿が書かないこと (性能の改善・退行、知識・診断の因果効果、B-6 の充足、同 job stock 対照の達成、critic が tool なし、certified が性能認証) を**言ってしまっている、または読める**箇所。逆に、稿の限定 1〜6 (§冒頭) のうち図・caption に**欠けている**もの。
5. **caption_source の束縛 (F36 の形)**: provenance が稿の SHA-256 を持ち稿が provenance hash を持たない形になっているか。稿以外 (insight README・role 定義・3 巡目の materials) を権威として読んでいないか (role 定義は frontmatter の一致検査だけが許される)。
6. **削除可能な test**: 同じ理由で赤になる test の重複、実寸描画の回数 (裁定の目安 ≤ 8 回・20 秒)。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。見出しはすべて H2)

## 所見 (must-fix)
番号付き。各所見に file:line (統合後の現物の行番号)、根拠 (現物の引用 1〜3 行)、放置時に成果物 (図・provenance・README・受入) がどう変わるか 1 行、推奨 fix 1 行。
## 所見 (should)
同上。
## 所見 (nit)
同上、短く。
## P1 の判定
3 の択と推奨、根拠。
## 恒真検査の一覧
検査ごとに「入力を変えて赤になるか」の判定と、その根拠 (test の nodeid または現物の行)。
## 削除候補
削除しても完了判定を満たすもの、失われるもの。
## 総括
GO / NO-GO と must-fix の件数、根拠を 5 行以内。
