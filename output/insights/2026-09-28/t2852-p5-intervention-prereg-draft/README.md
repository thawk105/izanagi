# [T-2852] VLDB 差分分析 P5 (介入による理由の説明) — 事前登録の草稿と、試走 v2 の実測単価による見積り (2026-09-28、計算投入 0)

- 依頼 (逐語): `verbatim/request.md`。段 1 brief `verbatim/s1-brief.md`、段 2 plan `verbatim/s2-plan.md`、段 3 相談 `verbatim/s3-consult-a.md` (統計・事前登録適合)・
  `verbatim/s3-consult-b.md` (実行可能性・規律・過剰)、段 4 裁定 `verbatim/s4-ruling.md`、段 6 レビュー `verbatim/s6-review.md`。開始 gate `verbatim/startup-gate.log` (rc=0、起点 local main `51f896352`)。
- 成果物: 草稿 `docs/workload-description-critic-intervention-preregistration.md` (以下「草稿」、未発効)。見積りの計算の逐語は `verbatim/estimate.md`。
- **repo のコード変更なし。計算投入なし。** 見積りは repo 外の job dir `/work/1/SFC/tanab/tmp/t2852-p5-prereg-20260928/` で計算した。

## 0. この文書が主張すること・しないこと

- 主張する: 草稿の設計判断の理由、起草時点のコードの実測 (§2)、試走 v2 の記録から計算した見積り (§3)、ユーザーが決める択一とその材料 (§5)。
- 主張しない: 見積りは将来の費用の保証ではない。計画半幅は達成される精度の予測ではない。本書も草稿も、実装・本走・計算投入の認可ではない。
- **起草者は試走 v2 の score を見ていない。** 使った集計は `section8.json` (費用・所要・失敗・s) と `failures-noscore.json` だけで、score を含む `aggregate.json` は開いていない。

## 1. 依頼と前提の確認

- 読んだ一次資料と既裁定: 差分分析 §0・§4 P5、Codex 見解の優先 4、D2212 (項 1〜8)、D2265、D2272 (項 1〜5)、D2273、P3 登録 §0〜§13、追補 3、転移登録 §2・§3.1、
  比較基盤 §1.3・§3.4・§4.1・§4.2、T-2867 の草稿 (書式の先例)、試走 v2 の分析。
- 依頼の前提は崩れていない。依頼が挙げた規模の案 (120〜240 評価、17〜34 node 時間、LLM 直列 20〜52 時間) は一次資料 (Codex 見解の優先 4) の値で、
  B-5 の単価からの換算である。本 wave で試走 v2 の実測単価に置き換えた (§3)。
- wave 開始時と段 4 直前に local main を見て、新着は 0 だった。

## 2. 起草時点のコードの実測 (worktree `dev-wave-t2852-p5-prereg`、base `51f896352`)

| 事実 | 所在 |
|---|---|
| planner の入力は current_perf・leading_indicators・whiteboard・`t2849_prior_observations`・(評価 2 以降) `k2_critic_diagnosis`。workload の記述は無い | `tools/t2849_llm_round.py:116-130` |
| coder の文脈 `leakproof_context` は `src/coder-leakproof-context.md` の Measurement Setup 節を `rr{rratio} ({workload})` を含む文で置き換える | 同 `:30-53`、`:132-133` |
| critic の入力に `operating_point` (workload・rratio ほか) が入る | 同 `:205-212` |
| LLM 親の header に `workload: {workload}`、指示文に役割を呼ぶときの説明ラベル | repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/parents/header.md:7`、`template-effective.md` (段 3 相談 B が行番号を引用) |
| 評価 2 以降に critic 診断が無いと継承の照合が例外 (系列が止まる)。critic を省く分岐は無い | `orchestrator/campaign/t2849_comparison_harness.py:439-442` |
| 構造化された失敗理由は critic digest の赤の節 (verify の失敗・liveness・差分の検疫) として critic へ渡る。planner・coder へは critic 診断経由だけ | `orchestrator/campaign/p3_s4_loop.py:1186-1216`、`tools/t2849_llm_round.py:116-133` |
| critic digest の緑の節は `build_digest(tag, {}, view)` で workload を空にして作る。赤の節は候補ごとに `workload:` 行を描きうる | `orchestrator/campaign/p3_s4_loop.py:1208`、`orchestrator/critic/digest.py:1382-1383,1454-1455` |
| S1 の coder 出力は `double now_backoff = <数値>;` の 1 行。他の形は backoff 文法で拒否 | `.claude/agents/coder-v4-autonomous.md:79-87`、判定 `orchestrator/campaign/p3_s4_loop.py:765-772,834-840`、拒否結果の組立て `:879-906` |
| D2273 の planner prompt の固定文は現行の巡 tool にある | `tools/t2849_llm_round.py:95-97` |
| 既知の格子 `EXTENDED_SWEEP_US` (29 点、0 を含む) | `orchestrator/campaign/backoff_extended_sweep.py:55-58` |

経路の最初の棚卸しは read-only の調査子 (Claude、sonnet) が行い、親が上の file:line を現物で読み直した。

## 3. 見積りの計算

### 3.1 単価 (試走 v2、S1-wh、`section8.json`)

| 量 | 値 |
|---|---|
| LLM 系列の job Elapse | 18,376・12,198・14,095 s (中央値 14,095) |
| block job の Elapse | 2,177・2,359・2,151 s (中央値 2,177) |
| 系列あたりの LLM の待ち (直列時間) | 13,904.4・7,703.2・9,594.9 s (中央値 9,594.9) |
| 系列あたりの原提案機会 | 11・14・11 (拒否は 1・4・1、すべて axis 名の揺れ) |
| LLM 系列の待ち以外の時間 | 4,472〜4,500 s |
| s_llm (LLM cell の ln score の SD、3 系列) | 0.00708 |
| s_plan (P3 登録の計画値、random–sweep の対) | 0.03894 |
| anomaly | 0 (`failures-noscore.json` の結果分類。15 系列と block job 3 本の全 600 記録 (投入と結果の両 event) が certified、うち 2 件は品質欠測。`section8.json` には anomaly の件数の欄は無い) |

### 3.2 式

- node 時間 = (系列数 × LLM 系列の job Elapse + n × block job の Elapse) / 3600。系列数 = cell 数 × n。最小・中央値・最大の単価でそれぞれ計算した。
- LLM の直列時間 = 系列数 × 系列あたりの LLM の待ち。原提案機会 = 系列数 × 11〜14。
- 計画半幅 h(n) = t(1 − 0.025/3, n − 1) × s_eff / √n。s_eff は対比の標準偏差の仮定で、s_pair ∈ {s_plan, √2·s_llm} に、6 cell 案の記述対比は 1/√2、
  critic 対比は 1/√3 を掛けた (周辺の平均に入る差が無相関と仮定した値)。相関 1 なら 1 を掛ける (4 cell 案と同じ)。t 分位点は T-2850 の
  `section8.py` と同じ標準ライブラリの不完全ベータ関数の実装で、t(0.975, 7) = 2.3646 で照合した。
- 表の値は草稿 §7.2。逐語の script と出力は `verbatim/estimate.md`。

### 3.3 一次資料の案との差

- 一次資料の 120〜240 評価は 6 cell 案の n = 2〜4 に当たり、中央値の単価で 48.2〜96.4 node 時間 (一次資料 17〜34 の約 2.8 倍)、LLM の直列 32.0〜64.0 時間 (一次資料 20〜52)。
- 2.8 倍は一次資料の換算と本書の外挿の比で、同じ構成の測り直しではない。差の主な理由は、LLM の待ちが node を占有する分を一次資料の換算が含まないこと。
  試走 v2 の実測の合計では、LLM の待ち 31,202.5 s は LLM 系列 3 本の job Elapse の和 44,669 s の 69.9%、block job を足した 51,356 s の 60.8%。
- 単価は D2273 の修正前・critic ありの構成で測った値で、草稿の cell の構成 (修正後の prompt、H・S の表示、critic なし、失敗理由の写し) では測っていない。

## 4. D2272 項 2 の 3 理由の効き方

正本は草稿 §12 (U1〜U3、ほかに U4〜U7)。要点だけ:

- 理由 1 (S1 で分類が弱い) は本書にもそのまま効く。s_plan を当てると、表のどの規模でも実用上同等を言うための計画上の目安 (半幅 ≤ δ/2) に届かず、S1 の出力は数値 1 行なので
  人手分類も機構を説明できない。
- 理由 2 (T-2869 の不公平) は、本書が LLM の cell どうしの比較なので手法間の不公平としては効かないが、cell によって拒否率が違えば効果と混ざる。
  全 cell に D2273 の修正を同じ commit で入れ、拒否を cell ごとに数える。
- 理由 3 (LLM の待ちが node 上) は、全系列が LLM 系列なので最も強く効く (node 時間の 6〜7 割、原提案機会は試走 v2 の 3.7〜11.7 倍)。

## 5. ユーザー確認の束 (発効の前にユーザーが決めること)

本 wave は本走を投げない。草稿の発効には、次の択一のユーザー確認が要る (D2212 項 4、一括承認にしない)。

| 案 | 中身 | node 時間 | LLM の直列時間 | 得られる主張 | 成熟度 |
|---|---|---|---|---|---|
| (a) S1-wh で本走 | 6 cell × n = 3 / 4 / 5 (4 cell × n = 3〜5 も可) | 72.3 / 96.4 / 120.5 (6 cell、中央値の単価) | 48.0 / 64.0 / 80.0 | 値 1 個の探索での表示と critic の周辺の差。s_plan を当てると、同等の分類と小さい差の識別は計画上難しい | 草稿 §13 の実装 (記述の切替・失敗理由の写し・critic なしの経路・役割文書の改訂 (ユーザー承認)・glue・集計) が要る |
| (c) S1 の本走は今は行わず S3 の後に回す | 介入と分類の手順を、S3 (関数方策軸、T-2867) の生成器対照の後に別の登録で行う | 未見積もり (S3 の単価は段階 F の生死確認の後) | 未見積もり | 機構の変更を読める空間での「なぜ」 | T-2867 の発効が先 |

**親の推奨: (a) は今は投入せず、(c) を本線にする。** 理由:
- (a) は最小でも 72 node 時間 (6 cell × n = 3、中央値の単価) で、D2272 項 2 が T-2850 の本比較を止めた 3 つの理由がすべて本書にも残る (§4)。
  値 1 個の LLM 対照は査読の決め手になりにくい (D2259)。
- (c) は研究上の問い (LLM がコードを書くときに、記述と critic が結果の理由になっているか) に最も近く、出力コードの分類が機構の違いを説明できる。
  ただし T-2867 の発効と S3 の単価の実測が先に要る。
- 推奨は択一の提示で、(a)・(c) のどちらの事前承認でもない。

## 6. 起草で読んだ既知結果

草稿 §11 の表のとおり。本 wave の親は試走 v2 の score を見ていない。入替先 rh の選択は、Pegasus の固定 backoff の記録 (rh で backoff が害) を見た後の選択である。

## 7. 段 2〜6 の経緯

- 段 2 (Codex plan、read-only、medium): 草稿の節立て 15 行・見積りの表・brief への指摘 5 件・P1〜P5 への代案。採用検査 rc=0。
- 段 3 (Codex consult 2 本、read-only、medium): A (統計・事前登録適合) 8 件 (must-fix 3・should 5)、B (実行可能性・規律・過剰) 8 件 (must-fix 4・should 3・nit 1)。
  採用検査は 2 本とも rc=0。
- 段 4 (親): 16 件すべて real・採用・scope 内 (docs の記述の修正)。主な反映は、P5 固有の規模の規則 (n ≥ 3、自動決定しない)、計画半幅を相関 0〜1 の幅と感度の値として示す、
  交互作用を探索的と明記、失敗理由の写しを両水準に同じ bytes で渡し `workload:` 行だけ表示規則に従わせる、表示の外に残る露出の列挙、人手分類を受理・拒否・原文なしの 3 母集団に分ける、
  critic なしの実装箇所の列挙 (親の起動条件・巡 tool の入力生成と公開時の読み込み・harness の継承の照合・役割文書)、「2.8 倍」「66%」の言い方の訂正 (実測の合計では 69.9% / 60.8%)。
  予備の観察 (当時は草稿 §10 の「予備段」) は段 2・3 を経ていない親の追加で、段 6 のレビュー対象に明記した。
- 段 5: 実装面の差分 0 のため無し。変異 matrix は免除 (DW-S04)。
- 段 6 (Codex review 1 本、read-only、事実の再抽出と過剰・削除の 2 レンズ): **NO-GO**、must-fix 2・should 2・nit 1 (`verbatim/s6-review.md`、採用検査 rc=0)。
  算術 (§7.2 の表・69.9%・60.8%・2.8 倍・h(5) の差・暦) と既裁定の引用には不一致なし。親は 5 件すべてを real と判定し、次を直した。
  (1) 試走 v2 の anomaly 0 件の出典を `section8.json` (件数の欄が無い) から `failures-noscore.json` の結果分類 (全 600 記録が certified、うち品質欠測 2) に直した。
  (2) 予備段を草稿の規則から外し、草稿 §10 は「発効の前に探索的な予備の観察を行った場合の開示」だけにした。手順は本書 §5 の (b) へ移し、
  親の推奨を「(a) は今は投入せず (c) を本線、(b) は任意の探索」に改めた (予備の結果で本走の実施・規模を選ぶ規則が未固定で、予備は S1 の分類の弱さも node 費用も解消しないため)。
  (3) 予備の所要の「上限」「4 並列」の見込みを外し、未測定の単純換算の例にした。(4) 計画半幅が ln 1.05 を超えるときの言い方を「同等の分類と小さい差の識別が難しい」に絞った
  (計画半幅は効果の大きさを含まないので、大きな差は分類されうる)。(5) file:line を判定の箇所 (harness :439-442、文法の判定 p3_s4_loop.py :765-772,834-840) に直した。
- 段 6 焦点再レビュー 1 巡目 (Codex review、read-only): **NO-GO**。所見 1・3・4・5 は closed (所見 1 は原データから再集計して確認)、所見 2 は partial
  (予備の観察がユーザーへの択一として残り、依頼の「草稿と見積りだけ」を超える)、新規 must-fix 1 件 (decisions fragment の理由が「critic の解釈の有無以外を揃えられる」と書き、
  草稿 §3.2 の「失敗情報の重複も差に含む」と食い違う)。逐語は `verbatim/s6-focus-1.md`。親は 2 件とも real と判定し、予備の観察を択一・確認事項・本書から外し
  (草稿 §10 は特定の案を指さない開示規則だけ)、decisions fragment の理由を草稿に合わせた。
- 段 6 焦点再レビュー 2 巡目 (Codex review、read-only): **GO**。前回の 2 件とも closed、新規所見なし (`verbatim/s6-focus-2.md`、採用検査 rc=0)。
  GO は草稿・insight・fragment の記述に対する判定で、見積りの将来の精度や草稿の規則の妥当性を保証しない。
- 逐語の正規化 (DW-S07 の可逆最小正規化、可視文字は不変): `verbatim/s6-review.md` は Codex の出力の 7 行 (7・8・11・12・15・18・21 行) の行末に
  Markdown の改行用の空白 2 個があり `git diff --check` に抵触したので、行末の空白だけを除いた。原文 SHA-256 `4be0a16fa61848ab814a60a50b2472fd7e03a959b284fde8d914a5c5665efaf3`
  (5,602 bytes) → 正規化後 5,588 bytes。復元はこれらの 7 行の行末へ空白 2 個を足す。原文は repo 外の job dir `s6/review.md` に残る。
- 三軸語の機械走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`): rc = 1。hit は既存の
  `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけで、本 wave の file は hit していない (本 wave に帰属しない既存状態)。
- 段 6 の Codex の費用 (receipt の観測値): review 14 call、焦点再レビュー 2 本。全段の Codex は model `gpt-6-sol`・effort medium。

## 8. 本 wave が閉じないもの

- 草稿の発効、本走の実施、草稿 §13 の実装。
- 記述の表示が coder の最初の提案を動かすかを記録入力から呼び直して見る予備の観察 (段 4 で親が足した案。段 6 で依頼の範囲外として外した)。
- 役割文書 (`.claude/agents/`) の改訂 (ユーザー承認事項)。
- S3 での同じ介入の登録。
