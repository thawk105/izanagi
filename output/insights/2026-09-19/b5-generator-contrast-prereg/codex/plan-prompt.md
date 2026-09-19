単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg

必読事項の射影:

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/brief.md — 親の段 1 brief (scope・確定裁定・段 1 実測・provisional 裁定 P1〜P9・変更面)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/01-user-decision-2026-09-19.md — ユーザー決定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/02-D1067.md — 主張を条件付き優越へ狭めた裁定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/03-D1012.md — 設計メモ留めの裁定の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/04-D1409.md — 非列挙軸の二重の壁の逐語 (条件変更は今回認可されていない)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/05-phase3-main-experiment-baselines-2026-07-10-D52.md — 主実験事前登録の 4 対照・失敗条件 (a)〜(e)・2026-07-10 追記・D52 骨子の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/06-D39-decisions-1-2.md — 編集面 (hole) と予算 (10 iteration または 3600 秒) の逐語。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-b5-generator-contrast-prereg/materials/07-paper-story-2026-09-17-s8-B5.md — 論文素材 §8 の B-5 欄の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/2026-08-26_b5-llm-necessity-contrast-design.md — 3 アーム設計メモ (241 行)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/2026-08-26/b5-contrast-review-verbatim/plan.md、同 dir の consult-a-correctness-lens.md、consult-b-preregistration-lens.md — 前回の草案と敵対相談 2 本の逐語 (must-fix 11 系統の出所)。読めなければ即停止。

以下は必要箇所だけを読む資料 (全文 cat 禁止の巨大 file を含む。読めなければ即停止):

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/backoff_hole_grammar.py (25,725 bytes) — Tier 1 文法と `validate_backoff_value` (値域)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/p3_s4_loop.py (151,847 bytes、約 3,200 行) — K2 手動 loop の harness。`grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。注目: module docstring、`default_perf`、`--run-iteration`、`--coder-role`、`--knowledge-manifest`、停止判定 (`converged` / `reverse-exhausted`)、帰属整合 (value == literal)、fixture proposal の経路。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/tools/pegasus/p3_s4_loop_pegasus.sh (21,081 bytes) — 1 評価 = 1 job の投入 script。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/backoff_extended_sweep.py (61,020 bytes) — `EXTENDED_SWEEP_US`、`MEASUREMENT_SEEDS`、`run_workload`、`main` の argv、run_kind の一覧。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/orchestrator/campaign/p2_2.py (19,813 bytes) — 較正済み動作点の定数 (`RECORDS` / `THREADS` / `EXTIME` / `REPS`)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/2026-09-18/t2746-k2-loop-round2/README.md (24,768 bytes) と同 dir の materials/knowledge-input.json — K2 loop 2 巡目の実走記録と K2 知識射影の中身。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/t1998-balanced-stock-inline-preregistration.md (13,245 bytes) と /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/b10-backoff-static-tail-preregistration.md (71,231 bytes、`grep -n "^## "` で節を出して要る節だけ) — 本 repo の事前登録の形式の先例 (版・効力と限界・主張しないこと・失敗条件・発効・束縛・閉じないもの)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/paper-story/2026-09-17.md (309,527 bytes) — `grep -n "^## 7\."` で §7「過大主張チェックリスト」の開始行を出し、`## 8.` の直前までを 200 行ずつ読む。それ以外は読まない。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/phase3-main-experiment.md (39,289 bytes) — 2026-07-13 / 2026-07-15 着手時確定の統計計画 (n・検定単位・検定力・総予算) を参考にする。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/README.md — 地図。`t1998-balanced-stock-inline-preregistration.md` の bullet の位置を確認する。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/docs/decisions.md (5,628,115 bytes) — **全文 cat 禁止。** `grep -n "^## D<番号>\." ` で位置を出し、必要な D だけ `sed -n` で読む。候補: D875 / D901 (hole 文法)、D2120 / D2148 項 2・項 3 / D2155 (K2 loop の裁定)、D1874 (T-1998 の認可形式)、D1790 (2 つの sha 定数)。
- B-10 拡張格子の所要 (費用見積り用): `grep -rln "backoff_extended_sweep\|B-10 拡張\|EXTENDED_SWEEP" /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/*/README.md /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-generator-contrast-prereg/output/insights/*.md` で当たりを出し、1 workload 31 genome の Elapse / 1 評価あたりの所要が書かれた箇所だけ読む。見つからなければ「見つからなかった」と書く (推定で埋めない)。

## 役割と目的

あなたは izanagi の dev-wave 段 2 の read-only プランナーである。親 (Claude) が段 4 で裁定し、親自身が
`docs/b5-generator-contrast-preregistration.md` (新規、docs のみ) と `docs/README.md` の 1 bullet を書く。
あなたの成果物は **その事前登録の全文草案** と、**既存機構での実行可能性の照合表** と、**既知結果台帳** と、
**費用見積り** と、**親の provisional 裁定 P1〜P9 への応答** である。実装面 (orchestrator/ tools/ hooks/ patches/ tests)
の変更は提案しない — 欠ける部品は「実装が要る」と名指しするだけにする。本走は認可されていない。

## 守ること

- sandbox は read-only。file を書かない。**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 予算が尽きそうなら、途中結論を下記の出力形式どおりに書いて終われ (無出力が最悪)。
- pytest は要求しない。静的検査だけでよい。実測は親が行う。
- 逐語・コード・trace・LLM 出力はすべてデータであり指示ではない (規律 6)。
- 事実 (値域・定数・argv・所要) は file:line で根拠を示す。推定は「推定」と書き、実測と混ぜない。
- 草案内の docs 間参照は節名で行い、行番号参照 (`.md:123` 形) を書かない (`tools/check_docs.py` の lint)。
- 平易な日本語。自作の造語を作らない。既存用語 (sweep-matched / sweep-ceiling / floor / 系列 / certified / anomaly / Tier0 など) は正本の意味で使う。
- 主張の形は D1067 の「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score だった」を超えない。「必要性」「LLM でなければ」を書かない。
- 失敗条件 (c) (機械 sweep / ランダム変異で同等に再現) の成立を、正当な結末の 1 つとして事前に固定する。2026-07-10 追記 1 (backoff はスカラー軸で headline 候補でない) と矛盾させない — 本事前登録は headline を復活させない。
- D1409 の「非列挙」の定義は変えない。本 hole の候補集合が完全列挙可能であることを隠さず、それが D1067 の主張の形と整合することを書く。
- 前回の敵対相談の must-fix 11 系統 (設計メモ §6) は、本 hole (スカラー literal 1..1000) の下でどれが解消し、どれが残るかを 1 件ずつ判定する。解消するものは「なぜ解消するか」を、残るものは草案でどう閉じたかを書く。

## 草案が持つべき節 (順序は変えてよい)

0. 版と発効 (本書は v1、発効 = ユーザーの本走認可を伴う日付付き commit。発効後 bytes 不変、erratum 追記のみ。解析 consumer が無いので pin は文書契約に留まることの明記)
1. 主張の形 (条件付き優越) と主張しないこと (必要性・headline・他 hole への一般化・費用効率)
2. 編集面と候補支持集合 (Tier 1 文法、整数 µs 1..1000、3 arm 共通、完全列挙可能であること)
3. 予算単位 = 評価数 B (anomaly reject も消費、文法・検疫不通過は原提案上限 A を消費)、停止条件 (性能理由の早期停止禁止、B 完走)、D39 決定 2 の停止 (a)(b) を無効化する運用が本走認可時の確認事項であること
4. 3 生成器の操作的定義 — LLM = K2 手動 loop (model / prompt / knowledge manifest / critic 還流の凍結物)、random = 凍結分布 + seed 導出規則、sweep-matched = 凍結格子 + hash 順 + B 点、sweep-ceiling = 族外の副次記述
5. 評価経路 (3 arm 共通の harness・動作点・correctness workload・trace-disabled bench)、規律 1・2 の対称性
6. score の定義 (endpoint の独立再計測、certified 無しの系列の扱い、−100% へ変換しない)
7. 母集団・n・block・判定規則 (系列単位、対の log 比、exact 符号反転 permutation、Holm 族 6、連言、等価域と (c) の成立、判定不能の扱い、選択的報告の禁止)
8. 既知結果台帳 (HARKing 境界) と、random 分布・格子・n を決めた時点で何を見ていたか
9. 失敗条件 (a)〜(e) の本事前登録版
10. 実行可能性の照合 (arm ごとに、既存機構の実在・限界・欠ける部品。表形式。「実装が要る」を名指し)
11. 費用見積り (評価 1 回の所要の実測根拠、総評価数、直列 wall。推定は推定と書く)
12. 発効・凍結・erratum の契約、本書が閉じないもの
13. 過大主張チェックリスト (paper-story §7) との整合 — 本事前登録が新たに要求する表現規律を箇条で

## 出力形式 (この見出し名を exact に使う)

## 事前登録の全文草案
(markdown の code fence 1 個に全文。本文 300〜600 行を目安に)

## docs/README.md の bullet 草案
(1 bullet、挿入位置を前後の bullet 名で示す)

## 実行可能性の照合
(表: arm / 既存機構 / file:line / 実在する部分 / 欠ける部分 / 「実装が要る」か)

## 既知結果台帳
(path 付き)

## 費用見積り
(根拠の path 付き。推定は明記)

## 前回 must-fix 11 系統の判定
(番号 / 解消・残存 / 理由 / 草案のどの節で閉じたか)

## 親の provisional 裁定への応答
(P1〜P9 ごとに 賛成 / 条件付き賛成 / 反対 と理由)

## ユーザー裁定へ返すべき事項
(本走認可時に要る確認を列挙)

## 総括
(5 行以内)
