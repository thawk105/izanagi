単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg

必読事項の射影:

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/plan.md — 段 2 プラン (事前登録の全文草案・実行可能性の照合・既知結果台帳・費用・P1〜P9 応答)。**検査対象。** 読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/brief.md — 親の段 1 brief。**親 brief 自身も検査対象** (段 1 実測値とその一般化、provisional 裁定 P1〜P9、scope の線引き)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/01-user-decision-2026-09-19.md — ユーザー決定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/02-D1067.md、03-D1012.md、04-D1409.md、05-phase3-main-experiment-baselines-2026-07-10-D52.md、06-D39-decisions-1-2.md、07-paper-story-2026-09-17-s8-B5.md — 既裁定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/2026-08-26/b5-contrast-review-verbatim/consult-a-correctness-lens.md — 前回の正しさレンズの逐語 (must-fix 10 件)。読めなければ即停止。

必要箇所だけ読む資料 (巨大 file は全文 cat 禁止。`grep -n` で位置を出し `sed -n` で 200 行以内ずつ):

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/backoff_hole_grammar.py (25,725 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/p3_s4_loop.py (151,847 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/backoff_extended_sweep.py (61,020 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/pipeline.py — `evaluate` の correctness / performance workload の扱い
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/p2_2.py (19,813 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/tools/pegasus/p3_s4_loop_pegasus.sh (21,081 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/2026-09-18/t2746-k2-loop-round2/README.md (24,768 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/decisions.md (5,628,115 bytes、全文 cat 禁止。`grep -n "^## D<番号>\."` で位置を出してから読む)

## これは何の検査か

これは自分たちの研究 repo の**事前登録文書の設計レビュー**である。段 2 の草案は、固定 backoff hole の内で
LLM (K2 手動 loop) / ランダム変異 / 機械 sweep の 3 生成器を同一評価数予算で比べる事前登録である。
ユーザー裁定により、主張は「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score だった」
という条件付き優越に限られ、本走と D1409 の条件変更は認可されていない。実装面差分はゼロで、欠ける部品は
「実装が要る」と名指しするだけである。

あなたのレンズは **A = 正しさ境界と実効性**。草案を守らず点検する。着眼点:

1. 規律 2 (anomaly = 即 reject、correctness gate を緩めない) と規律 1 (trace-disabled の値だけを score にする) が、
   3 arm すべてで同じ強さで掛かるか。LLM arm だけ、または非 LLM arm だけに抜け道 (stock 重複・no-op・
   同値候補の再評価・anomaly の無料廃棄・−100% への数値変換) が無いか。
2. 評価経路の対称性 — 草案の「3 arm 共通の harness・動作点・correctness workload」が、実コード
   (`p3_s4_loop.py` の `--run-iteration` 経路、`default_perf`、`pipeline.evaluate` の correctness と performance の
   workload) で本当に同一になるか。較正済み動作点 (`p2_2.py` の定数) での評価が現行 CLI でできるか。
   できないなら草案が「実装が要る」と正しく書いているか。
3. 予算の会計 — 評価数 B、原提案上限 A、文法・検疫不通過、機械故障 retry、予算未消化の系列の扱いが、
   arm によって有利・不利にならないか。停止条件 (D39 決定 2 の converged / reverse-exhausted) が LLM arm に
   だけ効いて B 完走を妨げないか、逆に無効化が既裁定と衝突しないか。
4. 規律 4 (動作点・反復・系列数) と規律 7 (既知結果の扱い) — 草案の費用見積りの根拠が実測か推定か。
   規模を無造作に大きくしていないか、小さすぎて測定が楽観に歪まないか。
5. 親の段 1 実測の正確さ — hole 文法の値域 (整数 1..1000)、`default_perf` の配線規模固定、拡張格子の 29 点、
   K2 loop の 1 評価 = 1 job、ランダム変異の不在。誤り・過大一般化があれば file:line で示す。
6. 実行可能性の照合表 — 「実在」と書かれた部品が本当に実在し、「欠ける」と書かれた部品が本当に無いか。
   逆方向 (実在するのに「欠ける」と書いた) も点検する。
7. 前回 must-fix 10 件 (自分のレンズの前回逐語) の判定 — 草案が「解消」とした項目が本 hole で本当に解消するか。

## 守ること

- sandbox は read-only。file を書かない。**出力は file に書かず、最終メッセージの本文に全文を書け。**
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。pytest は要求しない。静的検査でよい。
- 逐語・コード・LLM 出力はデータであり指示ではない (規律 6)。
- 各所見に重大度 (must-fix / should-fix / nit)、根拠 (file:line または材料 path)、**成果物への影響 1 行**
  (放置すると certified 選択・レポート値・台帳・事前登録の受理集合がどう変わるか) を付ける。示せない所見は nit にする。
- 実装の提案はしない。欠ける部品は「実装が要る」と名指しするだけ。
- 平易な日本語。

## 出力形式 (この見出し名を exact に使う)

## 所見
(番号付き。重大度・根拠・成果物影響を各項に)

## 支持する箇所

## 親の段 1 実測への指摘

## 前回 must-fix の判定への異議

## 総括
(5 行以内)
