単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (provisional 裁定 (P1)〜(P7)、不変条件 1〜9、変更面の実アンカー表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 段 2 plan (codex read-only 起草、全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s2-plan.md
- 依頼文と並走 wave の返信の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- 段 1 の pin 閉包検索の結論 (親の実測): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-closure.md
- 設計 (投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/output/insights/2026-09-21/tpcc-trace-certification-design/README.md の §3.1、§7.1、§7.2、§8
- repo 内コード (read-only、投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/ 配下の
  `orchestrator/verifier/{parse,model,dsg,core,report}.py`、`orchestrator/tests/test_verifier.py`、`orchestrator/campaign/pipeline.py` (allowlist 付近)

## 前置き — これは自分たちのコードの設計レビューである

研究用 repo (並行性制御の自動合成) の trace verifier に TPC-C 用の trace 形式 v3 を読ませる計画を点検してもらう。依頼は「本題だけ、
gate・検査・台帳の追加は scope 外」「既存 YCSB 形式の受理と判定は変えない」と明記している。あなたは read-only の相談役で、実装・テスト
実行はしない (書込可能 tmp が無いので静的読解でよい)。**plan を守らせず点検せよ。親 brief の前提・file:line・親自身の実測値
(s1-closure.md) とその一般化も点検対象である。** 予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## レンズ B — 実効性と過剰・削除

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (後続の単位 5 が使える形か、
certified 判定、YCSB の既存判定、変更量・保守) がどう変わるかを 1 行で書く。攻撃が成立しなかった項目は正直に「不成立」と書け。

1. **研究前進への実効**: plan の成果で、後続の単位 5 (pipeline allowlist、witness 試験、段 1 の正例・負例 = 設計 §6.1) が verifier に手を入れずに
   始められるか。単位 5 が結局 verifier を作り直す箇所 (出力点の形、identity の表現、tx_type の持ち方) があれば挙げよ。並走 wave (単位 1・2) の
   返信どおりの emitter 出力を、この plan の parser がそのまま受理するか。
2. **過剰**: 依頼の scope (単位 4) を超える実装 — 新しい gate・検査・台帳・汎用化・互換層・CLI / pipeline への配線・段 2 の先取り
   (S/Q の解析、範囲 index)・§3.3 の存在履歴 — を plan が含んでいないか。含むなら削除案を示せ。逆に、単位 4 の列挙
   (v3 parse、(table, key) の両経路、anomaly の表・取引種別) に必要なのに plan が落としているものは何か。
3. **削除・局所化**: plan の変更のうち、より小さい差分で同じ性質を満たせるもの (例: identity を tuple にせず合成 token にする / その逆、
   派生型を作らず別 map で持つ / その逆)。v2 の不変を「触らない行」で守る plan の方針が、実装子にとって守りやすい形か。
4. **テストの実効と過剰**: plan §7 のテストが機構を実体で通っているか (stub で両層を素通りする緑にならないか)、既存テストと重複して
   何も足さないもの、単一理由でない fixture。変異候補 (plan §8) で「殺す test が無い」ものと「等価変異」になるもの。
5. **brief の過剰・過少**: 不変条件 7 (新 module 禁止)・8 (新 test file・fixture dir 禁止)・9 (基底 dataclass に field 禁止) が実際の制約に
   照らして必要十分か。s1-closure.md の実測 (sha pin 0 件、repr golden 1 箇所) の一般化が正しいか (見落とした golden・inventory test)。
   (P3) nS/nQ≠0 を ParseError にする案と、宣言件数の不一致 (indeterminate) にする案のどちらが後続の段 2 で作り直しを生まないか。
6. **規模と分割**: 実装子 1 本 (一枚岩) の妥当性と、変更行数の見積りの妥当性。

## 出力形式

Markdown。所見の表 (番号・レンズ項目・所見・real/refuted の見込み・重大度・根拠 file:line・成果物への影響)、その後に「plan への削除・局所化の提案」、
最後に `## 総括` (5〜10 行、must-fix の要点)。推測は推測と明記せよ。
