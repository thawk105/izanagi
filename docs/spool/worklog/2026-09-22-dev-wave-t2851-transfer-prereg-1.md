---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2851-transfer-prereg
seq: 1
title: [T-2851] 未知条件への転移の事前登録 v1 を作った — 錨 3 点の周りで 1 因子ずつ動かす留保 23 条件 (Silo の balanced × read-modify-write は既知別枠)、比較対象 (stock・p2_2_flag_opt・錨で選んだ静的設定・各手法の選択結果)、同等幅 ln(1.03)・n = 32・cohort ごとの Bonferroni 同時区間・両 cohort 一致、別日別割当ての追試、留保の効力は着地時点 (docs のみ、branch worktree-dev-wave-t2851-transfer-prereg)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request-t2851.md`): 生成・選択に使わない条件 (read/write 比・競合・スレッド数・トランザクション長・アクセス集合の重なり) の具体値、比較対象 (stock・強い静的設定・各手法の選択結果、`p2_2_flag_opt` を外さない)、同等幅・信頼区間・別日別割当ての追試規則を、既存の事前登録の作法で固定する。選択結果を使う評価走・計算投入・gate / 検査 / 台帳の追加は scope 外。成果物 = `docs/unseen-condition-transfer-preregistration.md`、記録 = `output/insights/2026-09-22/t2851-transfer-prereg/README.md`、設計判断は {{D:t2851-transfer-reservation}}。
- 起点 = local main `8fd2a2f5c` (fresh worktree、開始 gate rc 0 は 08:52 JST)。軽量版で段 2 を省き (親の brief を plan とした)、設計択一が割れるので段 3 の Codex 相談 2 本と段 6 の read-only review を残した。実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。計算ノードの使用 0。
- 使ったユーザー裁定: D2212 (項 1・2・4・5)。段 4 直前に裁定 inbox を再走査し、/rulings 第 31 回 (08:43) の項 3 (目標投稿 2027-02-01) は本件の設計に影響しないと判断した。
- 段 1 の事実集めは読取り専用の Claude 調査子 2 本 (sonnet、workload 引数・比較対象・対測定 / 既知結果の棚卸し) に任せ、親が要所を file で検算した。最初の起動は model 未指定で hook `guard_agent` に拒否され、model を明示して投げ直した。棚卸しで、Silo の balanced × read-modify-write (8b の未採用候補 H4 と同じ点) に stock と ability-probe 変種の性能測定があることが分かり (T139 の silo_ladder_rung1、2026-07-29)、この cell を既知別枠にした。
- 段 3 (Codex read-only、reasoning medium、09:31 起動・09:35 / 09:36 完了): 相談 A (統計設計) は must-fix 7 / should 3、相談 B (留保の漏洩・HARKing・凍結契約・過剰) は must-fix 6 / should 6。22 件すべて real と判定し採用した (refuted 0)。主な変更は、n を 8 から 32 へ (n = 8 では同等をほぼ宣言できない)、cell 単位の無補正 + 追試一致を「cohort ごとの Bonferroni 同時区間 + 両 cohort 一致」へ (追試一致は多重性の代わりにならない)、主張を登録点での局所転移と別日・別割当ての再現確認に限定、不使用義務を値・結果・派生した指示と設定へ広げ解禁を全手法・全独立探索の凍結後に、TPC-C の登録期限を生成・探索・選択の開始前に、など。
- 段 6 (Codex read-only review 1 本、19:55〜20:02): NO-GO、must-fix 2 (欠測した block を落とすと遅い走を落とした候補が優越側へ偏る、再投入でも単独性違反が残った job を主要解析へ戻せる) / should 5 / nit 2。すべて real と判定し、親が docs を直した。焦点再レビュー 1 巡目 (20:08〜20:11): GO、must-fix 0。残った F1 (§10 の追記の証拠の追跡性) と F2 (使えた block が 0 個・1 個のときの記述) は main の取り込み後に直した。
- 親が段 6 の走行中に見つけた本文の誤り: 「rh の強い静的設定 (無 backoff) は stock と同じ build」と書いていたが、本書の stock (CCBench の上流既定) は BACK_OFF=1 で、A-2・A-6 の記録が stock と呼ぶ arm (BACK_OFF=0・他は既定) とは別 build だった。その arm の flag の組は balanced・write-heavy の `p2_2_flag_opt` (B0-L-W0) と同じである。現物 (CCBench の `cmake/Options.cmake`、A-2 / A-6 の certification JSON、`output/s1-freeze/known_axes_freeze.json`) で確かめて直した。段 8 で {{F:stock-names-different-builds}} に記録した。
- 親の自分起因の誤り (near miss): handoff 更新の command に正規化 script の再実行を誤って混ぜ、insight の `verbatim/NORMALIZATION.json` を除去 0 件の誤った記録で上書きした。段 6 の修正 commit の差分統計で気づき、`7d9c95fa3` で元の内容へ戻した (差分 0)。段 8 で {{F:non-idempotent-normalization-record}} に記録した。
- 三軸語の走査器 (`s8b_holdout_freeze search`) は 3 回とも rc 1 だが、hit は main に既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけで本 wave の file は 0 件、陽性対照は 234 件。1 回目の直後のユーザー発言 (逐語「もっか嫌ってみ」) を「もう一回やってみて」の打ち間違いで走査の再実行の依頼と解釈して再実行し、同じ結果を得た。
- 記録前に local main `eef04f5a7` を固定 SHA で取り込んだ (merge `33a13d503`、45 commit、競合なし、全史の provenance 監査 rc 0・新規違反なし)。取り込みで [T-2849] の比較基盤の設計書 (学習条件 = 本書の錨と同じ 3 workload、転移は本書に委ねる) が木に入り、本文 §10 の照合元にした。
- 時刻: 段 4 (09:39) から最初の commit (19:54) までの間に、本文の起草と、親の処理が止まっていた時間を含む (実測時刻だけを書いた)。
- 工数: Codex 子 = consult 2 本、review 1 本、焦点再レビュー 1 本。Claude 子 = 調査 2 本 (sonnet)。計算ノード 0。

## 次の一手差分

### 更新

- [T-2851] **P1 (VLDB 差分分析 P4: 未知条件への転移と再現)**: 事前登録 v1 `docs/unseen-condition-transfer-preregistration.md` を作り、
  留保の効力は本書の着地時点で生じる ({{D:t2851-transfer-reservation}})。残りは 4 つ。(1) 測定の発効: 対象探索群 ([T-2850] の選択結果) の名指し、
  全手法・全独立探索の候補凍結記録、MOCC の扱いの 3 択 (参照を固定 / 記述専用 / 含めない)、発効束 (§13.1) の実値を揃え、凍結した候補数で
  費用を見積もり直してユーザーの計算確認を取り、決定に記録する (§12 の試算は 1 cohort の性能だけで約 9.5〜616 node 時間、検証は約 19〜64 node 時間、
  cohort は 2 つ。D2212 項 4)。(2) runner の実装 (§11 の欠ける部品、Codex author)。(3) 性能 2 cohort と検証の実施。
  (4) TPC-C の留保条件を、TPC-C の生成・探索・選択が始まる前に別の登録で固定する (必須の未完項目、D2212 項 2)。前提 = [T-2850] の選択結果。
  一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P4、記録 `output/insights/2026-09-22/t2851-transfer-prereg/README.md`。
  base: 6649b4bdcd29a09bf2add74b3e390263bf57bf0606af3bf77e7e4de4cbe665d7
- [T-2850] **P1・新規 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 手法ごとに探索を独立にやり直し
  (候補を測り直すこととは別)、費用と成果の曲線を取る。候補評価数を揃えた比較と経過時間を揃えた比較を分け、有効候補率・最初の有用候補までの時間・
  検証時間・node 時間・人間の介入を記録する (複製候補・compile 失敗も費用に含める)。規模の案 (Codex): 試走 = 2 プロトコル × 2 課題 × 5 手法 ×
  3 独立探索 × 8 候補 = 480 候補評価 (B-5 からの換算で約 68 node 時間)、本比較 = 3,600 候補評価 (約 510 node 時間、LLM は直列で約 120〜156 時間)。
  本比較の規模は試走の探索間分散から決める。既存の有限空間での LLM / random / sweep の対照 [T-2797] (B-5、D2200 項 1 の段階認可) との関係は
  本項の設計で整理する。前提 = [T-2848] の空間と [T-2849] の基盤。試走と本比較の時期は目標投稿 2027-02-01 (概要 2027-01-25、D2219 項 3) から
  逆算して置く。本比較の規模を決める時点で、計算ノードの H100 で open-weight LLM を動かす案の再提示条件 (LLM の直列時間が律速か、D2219 項 6) を
  評価する (成立しても実装の許可ではなく、改めて諮る)。計算: 試走・本比較とも、それぞれ node 時間と LLM の直列時間の見積りを示してユーザー確認後に投入し、
  一括承認にしない (D2212 項 4)。**生成・選択には [T-2851] の留保条件を使わない** (`docs/unseen-condition-transfer-preregistration.md` §2.3・§3、
  {{D:t2851-transfer-reservation}}): 学習条件は同書 §2.1 の錨 3 点の部分集合にし (外れる場合は生成の開始前に別の登録が要る)、留保条件の値・結果・
  それから作った指示や設定を生成器・選択へ入れず、各手法の生成器が repo の docs を読めたかを記録する。一次資料
  `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 2。
  base: bca45ed970c8f2c30edc1ddfd0e2ef579d38d4f41dafc848b26d58a6ee43948b
