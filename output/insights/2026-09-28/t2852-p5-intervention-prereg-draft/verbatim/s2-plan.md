## 1. 草稿の節立て

草稿は [P3 の事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/search-repetition-trial-preregistration.md) の予算・endpoint・欠測規則を明示的に継承し、介入固有の規則を次の節で固定するのがよい。

| 節 | 書く内容と根拠 |
|---|---|
| 冒頭・§0 版と効力 | **v1 起草版、未発効**。起草中は改訂履歴を残して本文を改められる。実装、発効束、ユーザーの規模・計算確認が揃った後、日付付き D 番号と本文 raw bytes の SHA-256 で発効する。生成・測定は発効後だけ。発効後の訂正と事後改訂を区別する。[草稿の先例 §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/silo-policy-generator-contrast-preregistration.md)、P3 §0。 |
| §1 主張と限界 | 「S1-wh、同じ探索予算・実行基盤の下で、**LLM に渡す明示的な workload 記述**と critic 診断の構成差が endpoint score にどう対応したか」と書く。verifier、anomaly の即 reject、構造化失敗理由の返却は全 cell で維持し、それら各々の因果効果は推定しない。LLM 一般、他課題、未知条件への一般化もしない。[差分分析 §4 P5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-21/vldb-direction/gap-analysis.md:123)、比較基盤 §1.3、P3 §1。 |
| §2 課題 | **Q＝{S1-wh}**、真の評価 workload は全 cell で固定する。元案の「成功・失敗を代表する少数の課題」は、この登録では**課題間対比として実現しない**。成功・失敗の出力例を後から選んで課題数に数えない。[D2265 項3・4](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/verbatim/rulings-D2265.md)、P3 追補3 §4。 |
| §3 介入と cell | 正／伏せ／入替を、coder 文脈の Measurement Setup、critic に渡す `operating_point`、repo 外の LLM 親 prompt の**三経路それぞれ**で定義する。正は wh の現行表示。伏せは workload 名と読み比率を中立の固定表現にする。入替は表示だけを錨 bal または rh の**事前指定した一方**の名称・読み比率へ替え、実測 workload は wh のままにする。入替先を結果から選ばず、留保条件の rr25・rr75 等も使わない。錨の他のパラメータは同じ。[巡 tool 30–65、205–219 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/tools/t2849_llm_round.py:30)、[転移登録 §2・§3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/unseen-condition-transfer-preregistration.md)。critic は file を読めるため、操作の保証対象は**渡す入力**までと記す。static な役割文書や観測値から真の workload を推測できる余地も開示する。 |
| §4 critic 無し | critic の LLM 呼び出しとその解釈文だけを省く。評価後には同じ verifier／WAL から、閉じた schema の機械的な構造化失敗 digest を作り、次の planner・coder に同一 bytes で渡す。cycle・integrity・liveness を混同せず、検証結果や入力欠測を捏造しない。現行は評価2以降に critic 診断を要求するため、後続実装で入力契約と継承照合を変更する必要がある。[比較 harness 430–449 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/t2849_comparison_harness.py:430)、[digest 1186–1216 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/p3_s4_loop.py:1186)、比較基盤 §4.1。 |
| §5 予算・配置・順序 | P3 から B＝10、A＝30、初期点2、系列開始 stock、endpoint の fresh 5 session、A/B の消費、失敗・fallback、系列を統計単位とする規則を継承する。新 cohort・seed preimage・block 内の固定順序鍵を発効前に記す。各 block に各 cell 1 独立系列と block job 1 本を配置し、真の wh を全 cell で使う。試走 v2 の系列は標本に入れず、全 cell を同じ新 commit で走らせる。[P3 §§3–4、§8.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/search-repetition-trial-preregistration.md)、追補3 §5。 |
| §6 endpoint・score | 主 outcome は P3 の **E_B**：B 到達時に選んだ資格ある候補を fresh 5 session で再計測した median の対数 score。A 枯渇、anomaly、品質欠測、機械故障、fallback の優先順位も継承する。E_T を主族に増やすなら checkpoint と費用を別途登録する必要があるため、本草稿では時刻を副 outcome に留める。P3 §6・§7、比較基盤 §4.6。 |
| §7 族・推定・分類 | 六 cell 案なら、登録した三対比を明記する。記述二対比は critic 水準を平均した「正−伏せ」「正−入替」、critic 対比は三記述水準を平均した「あり−なし」。各 block の対比値の平均と標本 SD を使い、M＝3 の Bonferroni 両側 t 区間、δ＝ln(1.03) で優越・退行・実用上同等・判定不能を分類する。全 n block の必要 score が揃わない対比は判定不能。**交互作用があり得るため、周辺平均だけで各記述水準での critic 効果を断定しない**。P3 §7、転移登録 §6.2。 |
| §8 規模と費用 | §2 の表を発効前の択一とし、node 時間、LLM 直列時間、機会数、計画半幅を並記する。半幅は保証でも効果量の予測でもない。新介入 cell の分散は未測定で、P3 の `s_plan` 流用は感度分析と明記する。計算確認は規模ごとで、一括投入認可としない。P3 §8、D2212 項4（親 brief）。 |
| §9 副 outcome | 提案値 `ln v` の分布と最初の提案、A・B の実消費、有効候補率、拒否理由、重複、初めて有効候補／改善閾値に到達した時間・A・B、未到達の打切り数、node 時間と LLM 待ちを記述する。**追加の検定族を作らない**。初到達は探索時の noisy な観測で、真の改善とは呼ばない。P3 §5・§7、比較基盤 §5.6。 |
| §10 出力の人手分類 | **原提案機会**を単位に、提出された coder `implementation` と採否理由を保存する。カテゴリは、(a) 発効前に凍結した既知候補集合と同一の値／identity の再発見、(b) 値・意味が変わらない、又は文法・検疫で有効変更にならない無効変更、(c) backoff 値以外の動作を変えようとする機構変更、(d) 判読不能・提出なし、の相互排他的な優先順を事前に定める。既知候補集合は既存の初期点・格子・既知静的設定などの**列挙と版**を発効束で固定する。二名が cell 名・順序・score を隠したランダム順で独立評定し、混同行列と一致率／κを報告、不一致は原評定を残して協議結果を別欄にする。S1 では受理候補は `double now_backoff = <数値>;` に制限され、機構変更は**受理候補では構造上0**。試みを数えるなら拒否された逐語出力を別母集団にする。[coder 79–87 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/.claude/agents/coder-v4-autonomous.md:79)、[文法拒否 879–906 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/p3_s4_loop.py:879)。 |
| §11 既知結果・HARKing | 起草者には wh の既知 backoff 地形、試走 v2 の費用・待ち・拒否6/36、`s_llm` と `s_plan`、D2273 の axis 修正が既知と列挙する。親 brief の記載では**この起草の親は score を見ていない**。一方、T-2850 追補3 の親は当時 score を見た事実があるため、人・時点を分けて書く。試走系列を標本に混ぜず、見た結果に応じた規則変更は事後改訂として報告する。[試走 v2 §1–3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-27/t2850-trial-v2-analysis/README.md)、P3 追補3 冒頭。 |
| §12 未解決事項 | D2272 項2 の三点を対応づける。① S1 の値1個ではコード分類と機構説明が弱く、n を増やしても射程は広がらない。② T-2869 の axis 拒否は LLM の A だけを消費し、介入間の比較も汚す。D2273 の新 prompt を全 cell に同じ commit で適用する選択と、その後の拒否率は未確定。③ LLM 待ちは node 上に残り、429 が出ると欠測と費用増が同時に起こり得る。暦の上限は出せない。[D2272 項2](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/verbatim/rulings-D2272.md)、[D2273](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/verbatim/rulings-D2273.md)。 |
| §13–§15 実装・発効束・改訂履歴 | 後続 author wave に、三経路の表示切替、critic 無しの機械 digest と継承照合、親 prompt の固定、入力・逐語出力の保存、分類用の伏せた資料、集計器を列挙する。発効束に commit・CCBench pin・実 workload・三水準の exact bytes・model/settings・順序鍵・block/系列数・walltime・費用・raw SHA-256 を載せる。ユーザーには六／四 cell と n の**規模の択一**、費用と限界を一束で示す。草稿先例 §§12–15。 |

## 2. 見積りの表

以下は [`estimate_p5.json`](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/estimate_p5.json) の値。node 時間と LLM 直列時間は **最小実績／中央値外挿／最大実績**、機会数は試走の系列あたり11〜14を外挿した範囲。四 cell は「正＋critic、伏せ＋critic、入替＋critic、正＋critic 無し」の三対比案であり、六 cell の要因主効果と**推定対象が違う**。計画半幅は `s_plan＝0.03894` を使う M＝3 の最大対比半幅である。

| 設計 | n | B 評価 | node 時間 | LLM 直列時間 | 原提案機会 | 最大計画半幅 |
|---|---:|---:|---:|---:|---:|---:|
| 六 cell | 2 | 120 | 41.9／48.2／62.6 h | 25.7／32.0／46.3 h | 132–168 | 0.744 |
| 六 cell | 3 | 180 | 62.8／72.3／93.8 h | 38.5／48.0／69.5 h | 198–252 | 0.122 |
| 六 cell | 4 | 240 | 83.7／96.4／125.1 h | 51.4／64.0／92.7 h | 264–336 | 0.0669 |
| 六 cell | 5 | 300 | 104.6／120.5／156.4 h | 64.2／80.0／115.9 h | 330–420 | 0.0488 |
| 四 cell | 2 | 80 | 28.3／32.5／42.1 h | 17.1／21.3／30.9 h | 88–112 | 1.052 |
| 四 cell | 3 | 120 | 42.5／48.8／63.2 h | 25.7／32.0／46.3 h | 132–168 | 0.172 |
| 四 cell | 4 | 160 | 56.6／65.1／84.3 h | 34.2／42.6／61.8 h | 176–224 | 0.0946 |
| 四 cell | 5 | 200 | 70.8／81.3／105.4 h | 42.8／53.3／77.2 h | 220–280 | 0.0690 |

一次資料の「120〜240 評価、17〜34 node 時間、LLM 直列20〜52時間」に対し、六 cell・n＝2〜4 は**48.2〜96.4 node 時間、直列32.0〜64.0時間**。node 時間は約2.8倍。主因は実測で LLM 待ちが系列 job を占有し、六 cell 外挿では node 時間中央値の約66%になること。費用は実測の三系列の幅に基づく外挿で、critic 無しの短縮・失敗や429による増加は測れていない。n＝2 は t 分位点が極端に大きく、分類目的には弱い。[試走 v2 §1–3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/output/insights/2026-09-27/t2850-trial-v2-analysis/README.md)、[`estimate_p5.py`](/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/estimate_p5.py)。

## 3. brief の実測への指摘

1. **「三経路」のうち LLM 親 prompt は、指定された repo 内コードだけでは裏取りできない。** [`t2849_llm_round.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/tools/t2849_llm_round.py:1) は役割 prompt を作るが、親 prompt は repo 外 glue と brief が述べる。発効前にその exact bytes と差替え位置を確認する必要がある。

2. **「伏せ＝読み比率と workload 名だけを伏せる」は完全な盲検ではない。** coder 文脈には backoff と contention の説明が残り、planner には最新性能・leading indicators が届く。critic は digest、WAL、系列台帳を読める。したがって測るのは「明示表示の介入」であり、「真の workload 情報を遮断した効果」ではない。[coder 文脈 27–49 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/src/coder-leakproof-context.md:27)、[巡 tool 116–133・205–219 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/tools/t2849_llm_round.py:116)。

3. **「構造化失敗理由は critic 診断だけ」は、現行の次回 LLM 入力については概ね正しいが、元データが無いという意味ではない。** `make_critic_digest` は rejection の構造化情報を既に作り、文法拒否も rule ID 等の digest を持つ。critic 無し cell はこの元データを機械射影する設計が可能。ただし現在の継承照合は評価2以降の `k2_critic_diagnosis` を必須にしている。[digest 1186–1216 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/p3_s4_loop.py:1186)、[比較 harness 439–449 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/orchestrator/campaign/t2849_comparison_harness.py:439)。

4. **計画半幅の SD 仮定は実測ではない。** `s_plan` は試走の random–sweep 対から作った保守的入力で、六つの新 LLM cell の対差 SD や block 内共分散を測った値ではない。`√2·s_llm` 案も critic 無し／誤記述 cell の SD を観測していない。表の半幅を実測精度と呼ばない。[追補3 §2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2852-p5-prereg/docs/search-repetition-trial-preregistration-addendum-3.md)、`estimate_p5.py` の `s_pair_opts`。

5. **費用の四／六 cell 比較には構成依存の未測定分がある。** `estimate_p5.py` は全 cell に現行の critic 有り LLM 系列の Elapse・待ち・機会を同じ単価で掛ける。critic 無しは通常その分を省けるが、機械 digest 生成や提案失敗の変化もあり、節約額は確定できない。また六 cell の「主効果」の半幅は、対差が独立で同程度という仮定で `1/√2`・`1/√3` に縮めている。相関が不明なので、その数字は感度分析である。

## 4. 親 provisional 裁定 (P1〜P5) への代案

- **P1:** 六 cell を主設計として残すなら、三つの周辺対比に加え、記述×critic の cell 別差を**記述のみ**で必ず示す。四 cell は費用を抑える選択肢として明示するが、critic 効果は「正しい記述の下」に限定され、交互作用は見られない。六 cell を選ぶ理由と費用をユーザーへ示す。
- **P2:** 機械 digest の方向は妥当。ただし既存の critic 文の空欄を埋めるだけにはせず、**別 schema の元 verifier データ**として planner・coder に同一射影を渡す。解釈文を生成しないこと、失敗型と欠測を保つことを固定する。
- **P3:** 全 cell を fresh な同一 commit で走らせる案を支持する。D2273 の新 prompt の適用は T-2850 本比較の固定 commit を変えず、この新 cohort の構成として発効前に固定する。新 prompt の拒否率は未測定と書く。
- **P4:** E_B と δ、M＝3 は妥当。ただし n＝2〜5 の `s_plan` 半幅では強い同等主張は難しい。**分類不能も正規の結果**として受け入れ、n を結果から増やさない。E_T は費用と規則が増えるので主族に含めず、副 outcome とする。
- **P5:** 二名独立評定を支持する。受理された S1 候補の機構変更は構造上0なので、受理候補と**拒否された逐語出力中の試み**を別母集団で数える。既知候補集合、判読不能、盲検化、混同行列、不一致処理を発効前に固定する。

## 総括

- 推奨は S1-wh の六 cell 要因配置を草稿の主案とし、四 cell を費用縮小の択一として示すこと。
- 主張は明示的な workload 表示と critic 解釈の構成差に限定する。
- verifier と構造化失敗理由は全 cell で維持する。
- 六 cell・n＝2〜4 の中央値外挿は約48〜96 node 時間、LLM 直列32〜64時間。
- n＝2〜5 の分類精度は弱く、費用と研究上の限界を併記して規模を確認する。
- 実装と発効は後続 wave と D 番号の決定に委ね、本走は投入しない。