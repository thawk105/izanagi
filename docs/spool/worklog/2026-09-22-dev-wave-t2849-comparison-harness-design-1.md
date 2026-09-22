---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2849-comparison-harness-design
seq: 1
title: [T-2849] 5 手法比較基盤を計算なしで設計した — 共通化は候補 identity・評価要求・結果分類・費用計上の 4 契約、具体化は silo の backoff 値空間だけ、主構成は参照値を生成器へ渡さない R0・K0 LLM・系列ごとの共通初期点、BO と進化は逐次 GP-EI と (1+1) の再実装、MOCC は pin 前進後に literal 材料化が成立する場合の差し込み口 (docs のみ、branch worktree-dev-wave-t2849-comparison-harness-design)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): random・sweep・BO・進化・LLM を同じ口に通す形、観測・stock・`p2_2_flag_opt`・初期候補の揃え方、B-5 の生成器 arm の再利用範囲、BO / 進化の実装の出所、費用の計上単位 (複製候補・compile 失敗を含む)、MOCC の差し込み口を計算なしで定める。実装・投入・gate・検査・台帳・一般化は scope 外。記録 = `output/insights/2026-09-22/t2849-comparison-harness-design/README.md`、設計判断は {{D:five-method-comparison-harness}}。
- 起点 = local main `8fd2a2f5c` (fresh worktree、開始 gate rc 0 は 08:54:15 JST)。軽量版で段 2 を省き (親の骨子を plan とした)、設計択一が割れるので段 3 の Codex 相談 2 本と段 6 の read-only review を残した。実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。
- 使ったユーザー裁定: D2212 項 4、/rulings 第 31 回 (2026-09-22 08:43) の項 1・6・8。wave 開始後に裁定 inbox の新着なし (段 4 直前に再走査)。
- 段 1 の事実集めは読取り専用の Claude 調査子 3 本 (sonnet、コードの口・裁定と後続 T・MOCC) に任せ、親が要所を file で照合した。調査子の最初の起動は model 未指定で hook `guard_agent` に拒否され、model を明示して投げ直した。
- 段 3 (Codex read-only、reasoning medium): 相談 A (比較の公平性・情報の漏れ・正しさ境界・統計単位) は must-fix 8 / should 3、相談 B (実効性と過剰・削除・再利用の実在) は must-fix 7 / should 3。21 件すべて real と判定し採用した (refuted 0)。主な訂正は、S3 の具体設計と汎用 runner・汎用台帳を削って S1 に絞ったこと、共通入力と消費 field を分けたこと、初期点を系列ごとに fresh に測って endpoint 候補に含めたこと、A を候補提出機会にして無料の内部計算を狭めたこと、小予算で退化しない逐次 GP-EI と (1+1) にしたこと、MOCC で macro の値だけを流用すると backoff の意味が変わる (合成枝の既定式が千の位で形を切り替える) のを patch の式で確かめて literal 材料化を条件にしたこと。
- 段 6 (Codex read-only review 1 本、事実の再抽出と設計択一の 2 レンズ、09:38〜09:43:14): NO-GO、must-fix 4 / should 3 (段 3 の 21 件は closed 11 / partial 10 / not-closed 0)。7 件すべて real と判定し (refuted 0)、親が docs を直した: LLM への拒否履歴と初期点の渡し方 (R1)、endpoint が無いときの fallback と品質欠測の優先を B-5 の実装どおりに分けた (R2)、進化の支持集合を親の近傍に直し失敗点を使わないと定めた (R3)、`p2_2_flag_opt` (BACK_OFF=0) を測る参照 genome の入口を実装単位に足した (R4)、K0 と K2 の差は coder の契約も含む (R5)、不在の断定を検索範囲つきにした (R6)、D2214 の項番号と insight の節番号の取り違えと「非 LLM の 3 手法」の誤り (R7)。
- 段 6 焦点再レビュー 1 巡目 (09:49〜09:52:18): NO-GO、must-fix 2 / should 1 / nit 1 (R1〜R7 は closed 4 / partial 3 / regressed 0)。4 件とも real。R1 で入れた「whiteboard の iteration を提出機会の順にして投入前の拒否を rejected と写す」案は、空出力・不正出力の拒否に有効な planner 出力が無く 5 field の行を作れない (F1) ので撤回し、whiteboard と継承照合は B-5 のままにして初期点と投入前の拒否を 1 つの閉じた兄弟 key で渡すことにした。機械故障の retry 上限超えは endpoint の有無を問わず系列を終えて score 欠測にした (F2、B-5 §3.3 と実装)。MOCC_SPACE は直接参照だけを数えた (F3)、`CURRENT_PIN` は 7 桁 prefix と書いた (F4)。
- 親の実測: login の `/usr/bin/python3` 3.10.12 で import を確かめた numpy・scipy・sklearn・optuna のうち、使えたのは numpy 2.2.6 だけ。BO・進化の語の検索 (orchestrator/ と tools/ の .py) は 1 件で、無関係な文字列だった。pin は e9e477ca (`CCBENCH_FULL_SHA` は完全 SHA、`CURRENT_PIN` は 7 桁 prefix `e9e477c`) で、候補 C の短縮 SHA を含む .py は test 1 本だけ。Polyjuice (OSDI 2021) が方策学習に EA を使い整数 cell を [−λ, λ] の一様幅で変異させることを Web で確認した (原典 PDF と arXiv 2105.10329)。
- 親の時刻の誤記 2 件 (段 4 裁定の時刻と相談の投入時刻を推定で書いた) を、`date` と file の mtime で直した。
- 工数: Codex 子 = consult 2 本 (A 198 秒、B 251 秒)、review 1 本、焦点再レビュー 1 本。Claude 子 = 調査 3 本 (sonnet)。

## 次の一手差分

### 更新

- [T-2849] **P1 (VLDB 差分分析 P2: 公平な比較基盤と第 2 プロトコル)**: 設計は {{D:five-method-comparison-harness}} と insight
  `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` で済んだ。残りは 3 つ。(1) 実装 (insight §11 の単位 1〜7、Codex author、S1 = silo の
  backoff 値空間から): B-5 接頭辞から外した機械生成 slot、5 arm と初期点の系列制御 (B-5 の module は編集せず兄弟に置く)、BO / 進化の生成器、K0 LLM の入口
  (D2155 の射影を K0 へ、初期点と投入前の拒否を渡す閉じた兄弟 key)、`p2_2_flag_opt` (BACK_OFF=0) を測る参照 genome の入口と全系列の endpoint 集約、
  費用 field、並列に流すなら node-local bench lock。(2) [T-2858] の pin 前進の後の MOCC の差し込み (§9、単位 8)。
  (3) 第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload、検証だけで約 8〜16 node 時間、準備・build・性能測定は別)。有限空間だけで LLM が負けても
  コード合成一般の結論にしない ([T-2848] が要る理由)。B・A・系列数・費用上限と比較の族は [T-2850] の事前登録で決める。完了 = 5 手法が同じ口で走る
  基盤 (S1) と第 2 プロトコルでの疎通。計算: 実装に伴う開発の検査 (受入・焦点走・変異) を含め、1 タスクの job 合計が 2 node 時間以上なら、job Elapse の
  実測単価で見積りを示してユーザー確認後に投入する (D2212 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2。
  base: 8c930861ad4d82e2caa0ee68edb8ae2b12a69d94472728f52efe5400c674de1a
