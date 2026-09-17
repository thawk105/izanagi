単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/parent-brief.md — 親 brief (検査対象。研究前進・scope・確定済み裁定・不変条件・provisional 裁定 P1〜P4)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/plan-out.md — 段 2 plan (検査対象)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/user-utterances.md — 本 wave のユーザー発話 3 件の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1373.md — 測定を許す protocol の判定 (規律 2 の関門)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1603.md — pin 前進は材料 3 点を揃えてから裁定。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D2083.md — 非 silo within-run floor の登録と between-run 未実施の必要条件。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D2104-head-and-item13.md — 今日の一括裁定 (冒頭 + 項 13)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D579.md — mocc trace-hook の編集面と変異探索面の線引き。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/D1360.md — 段 7 cross-protocol の実装残余。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/phase3-stage7-and-related.md — phase3.md 段 7・S1 must 行・[T-023]・[T-167]。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/b655f5fe/tmp/wave/spool-README.md — spool fragment 書式。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/orchestrator/campaign/between_run_floor.py — D1373 関門と BASELINES。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/orchestrator/campaign/pin.py — CCBench pin の正本と前進手順。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/docs/phase3-main-experiment.md — 主経路 (A-1 / A-2 / H1H2) の事前登録。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cross-protocol-scope-release/tools/check_docs.py — docs の exact pin・閉包検査。読めなければ即停止。

## 依頼 (レンズ B = 主経路との衝突・pin 前進の実害・実効性)

あなたは親 brief と段 2 plan を**守らず検査する**敵対相談役である。親 brief 自身も検査対象である。read-only で、pytest 実走は不要 (静的検査でよい)。

親は「silo 固定の解除」を docs-only の裁定パッケージとして起草し、pin 前進は D2104 項 13 のとおり別途再承認、pin 非依存の準備 T 鎖を起票する、としている。次を攻撃せよ:

1. **P2 — pin 前進は主経路を実際に壊すか:** D2104 項 13 の理由「主経路 (A-1 / A-2 / H1H2) は現行 pin で設計」について、CCBench pin の SHA (gitlink `511c9538…`) を束縛している file を grep で列挙せよ (`pin.py`、事前登録 (`phase3-main-experiment.md` と `orchestrator/prereg*`)、campaign.lock の identity_preimage、env_contract、凍結 evidence の manifest 等)。pin 前進が (a) 何も無効化しない、(b) 事前登録の再登録を要する、(c) 過去の certified 判定を遡って無効化する、のどれかを file:line で答えよ。規律 7 (現行コードとの差だけを理由に過去測定を無効にしない) と D297 (TRACE=0 正規化 preprocess + include 活性の同一性) を踏まえ、「silo の前処理出力が同一なら束縛は内容ハッシュへ移せる」という親の推測が成り立つか、成り立たないならどの束縛が SHA そのものを見ているかを示せ。
2. **D1373 関門の位置:** `between_run_floor.py` の `_protocol_source_has_trace_hook_evidence_only` と `BASELINES` の実際の行を読み、(i) mocc は pin 前進だけで通るか (hook branch の内容が SOURCES 列挙 file に 3 証拠を持つか、branch 名 `izanagi-t1943-mocc-g2-readfrom-witness` の存在を submodule で確認)、(ii) tictoc は BASELINES 追加 + hook 移植の両方が要るか、を答えよ。関門を迂回・緩和する提案は出すな (D2083 項 4)。
3. **pin 非依存の準備 T 鎖の実効性:** plan が挙げる各 T について「pin 前進なしで本当に完了判定まで到達できるか」を検査せよ。特に (i) D1603 材料 (2) の D297 同一性検査は現行 pin と候補 commit の両方を build する必要があり計算ノードを要するか、login node で足りるか、(ii) tictoc hook 移植は submodule branch への commit を要し、それは AI が行ってよい操作か (D16・「push は人間」の境界)、(iii) mocc を EVOLVE_BLOCK hole にする auditor-live 相当の機械実証 (D579) の設計だけで 1 wave になるか。到達できない T は「pin 前進要」に分類し直せ。
4. **D2104 項 13 を同日に覆す記録の書き方:** 今日ユーザーが「推奨通りで」と一括承認した 39 項の 1 つを、同日の直接発話で上書きする。decisions fragment にどう書けば (a) 一括承認の項が AI 起草の推奨であったこと、(b) 直接発話が優先すること、(c) pin 前進の再承認自体はまだ出ていないこと、が誤読なく残るか。逆に「発話は『〜かなと思う』の疑問形なので裁定ではない」と読む余地があるなら、その場合に親が採るべき最小の形 (裁定案の提示に留めるか、暫定裁定として記録し取り消し条件を書くか) を示せ。
5. **docs 変更の検査面:** plan が挙げる phase3.md / paper-story README / spool fragment の改訂が `tools/check_docs.py` のどの検査 (exact pin、閉包、状態語、handoff 古さ) に当たるかを静的に確認し、plan の見落としを列挙せよ。phase3.md の見送り台帳 [T-167] 行 (L2595) の本文が壊れている (fold の混入) ように見える点も検査せよ。
6. **段 4 裁定案:** 上を踏まえ、親が段 4 で採るべき裁定を P1〜P4 ごとに「採用 / 修正して採用 / 却下」で書き、修正なら修正文を書け。加えて、本 wave の scope に**実装面を 1 つも入れない**判断 (docs-only) が正しいか、最小の実装 (例: BASELINES の tictoc 追加、D1603 材料 (1)(3) の作成) を同 wave に入れるべきかを、費用と受入全走の観点で答えよ。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 所見の件数 (real / refuted の内訳)、P2 の結論 (a/b/c)、pin 非依存で完了できる T の本数、docs-only の可否)。続けて上の 1〜6 を見出しにして書く。各所見は「所見 → 根拠 (file:line) → 影響 (放置時に裁定パッケージ・主経路の何が変わるか) → 是正案」の 4 項で書く。
