# B-4 還流 on/off ablation 事前登録 — D903 架構選択反映済み・発効前 draft

論文 `docs/paper-story/2026-08-23.md` §8 の **B-4「規律 3 の還流 on/off ablation」**の事前登録である。
論文が掲げる主張は「構造化された正しさシグナルが次の合成を改善する」(§8 の逐語)。
**ただし本書が事前登録する estimand は D824 決定 1 によりこれより狭く (§2.1)、論文の広い主張そのものは検証しない。**
還流の入口までは実走済みで、改善の実証が無い。

**この文書は `docs/phase3-main-experiment.md` の bytes を書き換えない。** 同文書は S-1 freeze
(`output/s1-freeze/known_axes_freeze.json`) が sha256 で bytes を pin する事前登録であり、
1 byte の編集で closure 検査が破れる (F78。過去に同型の追記が受入を赤にし、編集を撤回した)。

**ただし bytes 非接触は「実験契約を変えていない」を意味しない。正直に書く。**
旧文書は B-4 相当の ablation について (i) 切替点を「critic の機序帰属の on/off」と述べ、
(ii) 第 3 アーム reason-only を段 6 で判断すると留保し、(iii) 試行予算を
「10 iteration または 3600 秒」と固定している。本書はこれに対し (i) estimand を
「詳細 anomaly の増分効果」へ狭め (§2.1)、(ii) reason-only を**採らない**と決め (§3.3)、
(iii) primary の検定単位を **paired 1-step** に変える (§4)。
**これは参照ではなく別の operationalization である。**

したがって本書は次の 2 つを区別し、**後者をユーザー裁定へ返す。**

- **本書が単独で決めてよいこと:** 本書に基づく実験を、旧登録とは**別実験**として実施し、
  その結果を旧登録の B-4 として報告しない。
- **本書が決めてはならないこと:** 旧登録の B-4 記述を本書が **supersede するかどうか**。
  旧文書は bytes 凍結されており、supersede は事前登録の差し替えである。
  裁定が下りるまで、本書の成果は「旧登録とは別の operationalization による結果」としてのみ報告する。

**本書は D37 / D39 決定 4 が定めた合流点の位置を動かさない。**

---

## 0. 状態と表記の規約

- **状態 = D903 架構選択反映済み・発効前 draft。** §2.3 の架構択一は D903 で確定したが、
  §5 の数値欄が埋まり、§6 の前提条件がすべて充足し、
  その版が commit されるまで発効しない。**本書に書かれた宣言では発効しない。**
- 未記入の欄には placeholder 語だけを置く。値セルに説明文・条件を書かない。
- **例外は「実行責任者・開始時刻」欄 1 行だけである。** この欄は独立に決まる 2 値を 1 セルに
  持つため、片方が確定し片方が未確定の状態を取りうる。確定した値と placeholder 語を
  `名前 = 値` の形で並べてよい。説明文・条件は書かない。placeholder 語が 1 つでも残る限り
  実走前検査は閉じたままである。他の 9 欄へこの例外を広げない。
- 本書が定める規範は §5.1 と §7 に置き、§5 の値セルへは書かない
  (値セルは凍結範囲外であり、そこへ置いた解除条件は次世代の契約なしに緩められる)。

## 1. 事前登録の効力とその限界

- **版の同定**: 実走成果物は測定に使った checkout を併記する。
- **仮説が結果より先であること**: 発効版の commit が結果 commit の**祖先**であることによる。
- **その限界**: ancestry が証明するのは「その bytes の文書がその時点に存在したこと」だけである。
  §5 の数値欄が空の版を祖先に持つだけでは、結果を見てから埋めた版を後で commit しても
  ancestry 条件を満たしてしまう。よって次を要求する。
  - §5 の欄をすべて埋めた版を**実走開始前に** commit する。
  - 実走成果物にその発効版の commit hash を記録する。記録がない実走は事前登録された実験として扱わない。
  - 発効後の変更は旧版を git 履歴に残したまま新しい commit で行い、変更理由と変更時点を本書へ明記する。
    **結果 commit より後に書かれた変更は事前登録として数えない。**
- **本書は 8c 正式系列の事前登録ではない。** §2.3 を参照。

## 2. 主張の型と scope

### 2.1 estimand (狭めた形。ここが本書の中核)

**主張:** 段 4 自律ループにおいて、critic へ**構造化 rejection の詳細**を還流するアーム (on) は、
還流しないアーム (off) より、同一の赤 precursor から行う**次の 1 synthesis** の結果が良い。

**この estimand は「構造化された正しさシグナル全体の on/off」ではない。**
両アームは次を**共通で**受け取るため、測っているのは「coarse な correctness outcome を共通にした
うえでの、**詳細 anomaly の増分効果**」である。

- `whiteboard.result` の `success` / `fail` / `rejected` (3 値の outcome ラベル。機序・形状を持たない)
- 緑 leading-indicators (trace-disabled build 由来、規律 1)

広い主張 (correctness feedback 全体の on/off) を名乗るには、§6 の前提条件 3 と
role-facing の型付き結果 projection の両方が要る (D824 決定 1)。
**この 2 つは必要条件であって十分条件ではない。本書は、その充足状態にかかわらず広い主張を禁じる。**
**両方が将来実装されても本書の estimand は広がらず、広い主張を名乗るには別の事前登録と
ユーザー裁定が要る。§10 に列挙する実装項目も、この必要条件としての意味で読む。**

### 2.2 主張しないこと

- **LLM の因果的必要性 (B-5) を主張しない。** ベースライン 3/4 とは独立である。
- **「構造化された帰属が効いた」と「赤が存在するという事実を知らせるだけで効いた」を分離しない。**
  分離には第 3 アーム reason-only が要る。本書はそれを採らない (§3.3)。
- **headline 主張をしない。** 対象軸が headline 適格かは `docs/phase3-main-experiment.md` の
  軸適格性規則に従う。B-4 は機序証拠であり headline 比較ではない。

### 2.3 本書が対象とする架構 (重要な限定)

2026-08-03 のユーザー裁定 (`docs/archive/worklog-phase3-0803-125-126.md`) は、還流の切替点を
2 つの架構に分けた。

- **段 4 の架構 (本書の対象):** critic 出力が次候補の方向指示として生成側へ直接流れるため、
  赤の射影を切ることが還流チャネルの ablation として正しい、と裁定されている。
  事前登録 (D39 決定 4) は凍結のまま歴史として残る。
- **新架構 (2026-08-03 裁定の記録。本書の対象外):** 還流の担い手は機械 (失敗から制約を導く) であり
  critic は還流チャネルでない。切替点は「機械が導いた制約を適用するか」へ移る。8c 用の定義は新設される。
  **D903 裁定時点で、その機構は存在せず、treatment と負の対照も固定されていない。**

**D903 により、本書は段 4 の既存架構だけを事前登録する。新架構は本書へ事前登録しない。**
新架構の還流 ablation は、その機構が実在し treatment と負の対照を固定できた時点で、
別実験・別事前登録案としてユーザーへ再提示する。
**両方を同時に事前登録せず、両者の結果を統合しない。**

## 3. アーム定義

### 3.1 2 アーム

|アーム|critic へ渡す digest|campaign identity|
|---|---|---|
|on|緑 leading-indicators + 赤 rejections (verify-red / liveness / other / diff-quarantine) + verify abort 統計|`search_config["reflux"]="on"`|
|off|緑 leading-indicators のみ|`search_config["reflux"]="off"`|

- **切替点:** `orchestrator/campaign/p3_s4_loop.py` の `make_critic_digest(reflux=)`。
  ここ以外でアームを切り替えない。
- **これは「critic digest 生成の合流点」であって、「off role が赤に到達する全経路の遮断点」ではない。**
  到達経路の現在地は §7 に正直に書く。
- **物理分離 (限定つき):** `reflux` は `search_config` に焼かれ campaign identity を変える。
  **sanctioned CLI が使う ID 由来 layout (`exploration_campaign_layout(campaign_id(cfg))`) の上では**、
  両アームは別 campaign となり WAL・checkpoint・digest を共有しない。
  **この保証は標準経路に限る** — layout を直接注入する controller や、誤った `--campaign-dir` を
  与える読み手には及ばない。その場合の block は off 汚染として判定不能 (§7.1) とする。

### 3.2 treatment に含めないもの (明示除外)

- **screening rejection (`load_screen_rejections`)。** 現行の `make_critic_digest` は
  screening を**どちらのアームにも渡さない**。したがって screening reason は treatment の
  差分ではない。「全 structured rejection の還流」とは書かない。
- **verifier の reject 判定そのもの。** §4 を参照。

### 3.3 第 3 アーム reason-only は採らない

規律 5 (段階導入・盛らない) による。採らない代償は §2.2 に主張限界として書いた。
D39 残存リスク (b) が求める「off が rejection を一切見ないことの妥当性の再検証」には、
本書は**主張の縮小**で応える。第 3 アームによる弁別は将来の別事前登録へ送る。

## 4. 正しさゲートは両アーム同一 (規律 2 / 規律 3)

**ablation が切るのは「検出結果を critic へ合流するか」だけである。**

- verifier、correctness reject、diff 検疫、auditor gate、build/verify/bench の順序、WAL schema は
  両アーム**同一**である。anomaly を検出した variant は off でも reject される。
- **off でも赤は WAL へ構造化して保存する。** 沈黙させない (規律 3)。
- reject に fitness を付けない。
- アームによって verifier policy・受理集合・再試行・校正値を変えた block は protocol violation とし、
  **削除せず報告する**。

**この不変条件のうちテストが固定するのは一部だけである (正直に書く)。**
§8 の T4 が固定するのは **base driver の diff-quarantine reject 1 経路**についての
「off でも reject する / WAL に赤が残る / whiteboard が `rejected` になる / on と WAL payload が同形」
だけである。T4 は `do_build=False` で走るため、**verifier・auditor gate・build/verify/bench の順序は
通らず、したがって固定していない。** sort / trigger driver の auditor 経路も対象外である。
これらは**機械強制されていない protocol 規範**であり、アームによって変えた block は
§7.1 に従い protocol violation として報告する。

## 5. 実走前に数値で埋める欄 (空欄のまま実走しない)

|欄|値|
|---|---|
|対象 driver と軸|base (silo-backoff-magnitude); evidence_set=t2341-eligibility; base.json sha256=d282c246e0b4f4d2542d28dd15850bbff650a8fc018e617bcd7ecec4be9ef237; sort.json sha256=9008aaace2bf1b9a2be508d068dcaac1222487041554b9cf540325f6132e3d72; trigger.json sha256=eb7f7cf1f48e0d7d65620932a7a26a42e0bec8bebb21bc7a9768f9e4635518f2; 記入者 = レビュー者 = thawk105 (D1266、D1638)|
|赤 precursor の母集合 (workload・赤形状・初期 proposal)|未記入|
|アームあたり block 数 n と検定単位|n = 201、検定単位 = block|
|primary outcome の演算定義 (純関数)|orchestrator/campaign/p3_b4_analysis_contract.py sha256=528ee2fa5795bf36fcd966bed47efb025b24a070c8c4e4303c8615957893d2a3; orchestrator/campaign/p3_b4_analysis_adapter.py sha256=cf056566a7bc2c23b0a5af14a537450fe4d160b042eda9df26fd41ad200cc0b6; orchestrator/campaign/p3_b4_analysis_ledgers.py sha256=71393e8d3ffc60e8af3421c1caf80abc1cf2395551173d96524b724ab5785cda; orchestrator/campaign/p3_b4_analysis_path.py sha256=eeb397fcf8cfebf454bdacc00af9943010b53b59c6cf64dcdded0acf3217ea86; orchestrator/campaign/p3_b4_analysis_prereg_consumer.py sha256=fe3aeb804fc09733434c8974500bba9f46cbd942e39bd33b2c6063134d96b31a|
|floor (対象動作点で再実測した between-run floor) の artifact パスと hash|未記入|
|校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash|未記入|
|総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限|未記入|
|env_tag (実測環境)|未記入|
|model snapshot / prompt hash / projection hash|未記入|
|実行責任者・開始時刻|実行責任者 = thawk105、開始時刻 = 未記入|

### 5.1 欄別の解除条件 (規範。§5 の値セルへ書かない)

- **対象 driver と軸**: §2.3 の架構択一は D903 で確定したので、裁定待ちを理由に空欄のままにしない。
  記入は次の順で行う。(i) 候補 driver の集合、適格性を測る sanctioned CLI command、証拠の保存先
  path と hash、合格 0 件・複数件のときの決定的な選択規則、記入者とレビュー者を **別 commit で先に固定する**。
  **記入者とレビュー者はいずれも `thawk105` を指名する (D1266)。レビュー者は独立検査者ではなく、
  記入内容が事前登録の要求を満たすことの確認責任者であり、独立性を要求しない。
  この指名が固定するのは (i) の項目のうち記入者とレビュー者だけであり、(i) の充足を意味しない。**
  (ii) 各候補について、sanctioned CLI 経路が §3.1 の切替点を通ること、on で赤詳細が出現すること、
  off で §8 の項目 1・2 が成立すること、on/off の campaign identity が分離することを実測する。
  (iii) (ii) に合格した driver と軸だけを記入する。**(ii) は next synthesis と primary / secondary
  outcome を生成も閲覧もしない配線 probe に限る。「正式標本ではない」と分類して outcome を先に
  生成・閲覧することを禁じる。**build を伴う sanctioned CLI 経路はこの probe にならない** —
  同経路は次の synthesis を実行して primary / secondary outcome を生成するためである。
  **`--no-build` 経路が probe にならない理由は driver ごとに異なる (2026-08-27 実測、[T-1769])。**
  base と trigger では切替点が `do_build` の内側にあり到達しない。**sort では切替点が無条件であり
  `--no-build` でも到達する。** それでも sort の `--no-build` は probe にならない — iteration を
  実走して checkpoint と whiteboard 結果を書き、synthesis 記録を生成するためである。
  **(ii) を実行する sanctioned CLI は `orchestrator/campaign/p3_b4_wiring_probe.py` として実在する
  (2026-08-27 新設)。** ただし CLI の実在は (i) を充足せず、§5 の欄を埋める権限も与えない。
  候補集合・各 exact command・証拠 path と hash・0 件/複数件の決定規則・記入者・レビュー者を
  人間の指名を含む別 commit で先に freeze しない限り、対象 driver と軸を記入しない。
  (i) と (ii) は実走開始前に完了させ、実走開始後は差し替えない。**
  **(i) の固定は §5.1.0 に置く (2026-09-05、D1641 の委任)。**
- **赤 precursor の母集合**: B-4 の出力を見る前に freeze する。赤が出なかった block も
  除外・差替えせず「treatment 未発火」として全件報告する (§7)。
  **母集合を決める適格性述語・順序・選択関数・完全性要件は §5.1.1 で凍結済みである。**
  この欄を埋めてよいのは、その規則から一意に決まる `analysis_manifest` が実在し、
  **その artifact path と sha256 と行数、および `scheduled_attempt_registry` の
  artifact path と sha256** を値として書けるときだけである。規則への参照だけで埋めてはならない
  — 中身の実在なしに実走前検査を通す経路になる。
  生成後の追加・削除・並べ替え・driver の差替えは、§5.1.1 に従い `design_not_feasible` とする。
- **n と検定単位**: 検定単位は **block** とする (試行は path-dependent で独立でない)。
  n は B-4 データを含まない凍結済み母集合と事前固定した最小重要効果から決める。
  **導出は §5.1.1 が正本である。** 近似ではなく、そこで凍結した統計モデルのもとで
  **厳密検定の検出力そのもの**から求め、pilot を使わない。値は §5 の欄に記入済みである。
  **予算上 n を確保できないなら「記述統計に留め有意性を主張しない」と本書に先に宣言してから実走する。**

  **追記 (2026-09-14、[T-2547]、D1936 項 8)。この宣言を先に行う。**
  2026-09-10 のユーザー裁定に従い、**本書に基づく B-4 の報告は「記述統計に留め有意性を主張しない」**
  とする。ここでの「記述統計」は本書に基づく B-4 の on / off 結果の報告形式を指し、下に記す
  在庫の集計を指さない。「有意性を主張しない」は将来の報告に対する拘束であって、
  「非有意だった」という観測結果ではない。本追記は旧登録の B-4 記述を supersede しない
  (本書冒頭と §10 のとおり、その裁定は下りていない)。
  **発火した条件は §5.1.1 の「適格な block を 201 件確保できない場合」であり、直上の
  「予算上 n を確保できないなら」ではない。** §5 の総計測予算欄は未記入であり、予算不足は
  確認していない。

  **在庫 (2026-09-14 に記入者が現物を読んだ観測)。** 合成ループ 3 campaign の
  `loop_state.json` の whiteboard は合計 7 行で、すべて `success`、`rejected` は 0 行だった。
  よって §5.1.1 の適格性述語の第 1 項を満たす行が無く、**適格な赤 precursor は 0 件**である。
  別 campaign の rejections digest には赤が 3 件あるが、同 campaign は whiteboard を持たないため
  第 1 項を満たさず算入しない。調査範囲は repository 内の campaign 成果物であって、全世界の
  在庫調査ではない。読んだ file と出力の逐語は
  `output/insights/2026-09-14_t2547-b4-descriptive-erratum/` に保存した。

  **この選択は、本書に基づく B-4 の on / off 結果を見る前に行った。** その正式標本は 1 件も
  生成していない — repository には B-4 の実走 marker も `analysis_manifest` も
  `scheduled_attempt_registry` も存在しない。**ただしこれは「起草者が何も見ていない」という意味では
  ない。** §9 が開示した 2 件の既知結果は本書の起草時点で閲覧済みであり、同節が定める
  「正式標本へ算入しない」扱いと「既知結果に informed された登録追試」という位置づけを、
  本追記は変えない。

  **本追記は実走の許可ではない。** §5.1.1 の選択関数 (適格行が n 未満なら
  `design_not_feasible` とし実走しない)、§5 の未記入欄、§6 の前提条件はいずれも残り、
  本追記はそれらを 1 つも解消しない。適格行が 201 件に満たないまま実走してよいとは読まない。

  **変えないもの。** 母集合の供給源 (合成ループ campaign の whiteboard) と §5.1.1 の
  適格性述語・順序・選択関数・完全性要件を変えない。D1880 の 201 行、§5 の `n = 201`、
  および現行の解析 consumer が要求する block 数も変えない。少数行を受理可能にしたとは扱わない。
  成功例への置換、n の無言の切り下げ、母集合を作るための追加基盤は採らない。
  「合成ループから得た適格な少数の赤 precursor を使う」という方針は維持するが、
  **その利用は本追記では実現していない。** 適格 0 件であることに加え、少数の適格赤を得たときに
  §5.1.1 の選択関数 (適格行が n 未満なら実走しない) とどう両立させるかが未解決だからである。
  この未解決点はユーザー裁定へ返し、本追記では解かない。

  **本追記が限定する範囲。** 限定するのは、人が本書に基づく B-4 について報告に書いてよい
  主張の上限だけである。機械が生成する材料レポートの値・分類・参照は本追記で 1 つも変わらない。
  §7.1 の 4 分類も変わらない — 「有意性を主張しない」は観測された非有意ではないので、
  機械の判定を「判定不能」へ畳む根拠にはならない。正しさゲートと受理集合は緩めない。
- **primary outcome**: 純関数として固定する。次をすべて定義してから記入する —
  参照点 (precursor 基準か arm 内前後か)、tie の扱い、欠測の順位、非 certified 同士の順位、
  certified と非 certified の順序、確率優越 A の定義。**secondary (certified 到達までの
  iteration 数・certified 率) は primary 判定に使わない。**
  **6 点はすべて §5.1.1 で定義済みである。** それでもこの欄はまだ埋めない。
  実走前検査は値セルの型・意味・参照先の実在を検査しないため、定義への参照だけで埋めると、
  **実装が無いまま他の欄が揃った時点で関門が開く**経路になる。
  この欄を埋めてよいのは、raw な試行記録から §5.1.1 の入力型を作る経路が実装され、
  その実装が §5.1.1 の定義と一致することを検査する consumer が実在し、
  **その artifact path と sha256 を値として書けるとき**だけである (§6 の前提条件も参照)。
  **追記 (2026-09-08、[T-2140]、D1812 (a))。** 上の「その artifact」は、consumer が成功時に返す
  receipt ではなく、**分析 source file の閉包 5 member** — `p3_b4_analysis_contract.py`、
  `p3_b4_analysis_adapter.py`、`p3_b4_analysis_ledgers.py`、`p3_b4_analysis_path.py`、
  `p3_b4_analysis_prereg_consumer.py` (いずれも `orchestrator/campaign/` 配下) — の
  repository path と sha256 を指す。したがって §5 の既存記入は維持し、差し戻さない。
  **確定したのは読みだけである。** raw な試行記録から §5.1.1 の入力型を作る経路が実装されて
  いること、その実装が §5.1.1 の定義と一致することを検査する consumer が実在すること、
  記入した 5 値が記入時点の bytes と一致することは、引き続き要求する。
  **本追記は primary outcome 欄のこの出現だけを対象とする。** 同じ §5.1 の「赤 precursor の
  母集合」欄が要求する `analysis_manifest` と `scheduled_attempt_registry` の artifact へは
  及ばない — そちらは実体そのものの path・sha256・行数を要求しており、source file で
  代替できない。
- **floor**: `docs/phase3-main-experiment.md` の流用禁止規則に従う。既存の 3.0% (D19) と
  48 スレッド動作点の calibration を**流用しない**。対象動作点で再実測し保守側 (最大) を採る。
  発効手続きの案と、床値を得るための測定計画は §11 にある。**§11 は D1383 に基づく未裁定の案であり、
  本欄の解除条件を 1 つも緩めない。記入の権限も実走の許可も与えない。**
  **追記 (2026-09-07、D1694 / D1695)。** §11 のうち 2 点は裁定済みである。床値測定の
  **window ごとの標本数は n = 62** (1 campaign・1 セルあたり。24 時間以上離した 2 campaign で
  合計 124。D1641 の n = 59 を D1695 が改めた)。**§11.2 が名指しした専用 driver は実在する**
  (D1694、§11.2 の erratum)。**それでも本欄の解除条件は 1 つも緩まない** — 記入してよいのは
  対象動作点で再実測した床値の artifact path と hash を値として書けるときだけであり、
  この追記は記入の権限も実走の許可も与えない。
  **追補 (2026-09-13、D1936 項 7)。** D1855 の案 B を採る。床値は **workload ごとに 1 つの凍結 spec**
  で測り、その 3 つの結果 (floor-pair summary) を **1 つの集約成果物**へまとめる。本欄が受ける pin は
  従来どおり 1 件の文法のままとし、その 1 件がこの集約成果物を指す。集約の規則を次に固定する。
  (a) **集約値は保守側の最大である。** 対象は D1641 決定 3 が凍結した「セル集合 × 2 時間窓の全部」で
  あり、平均・中央値・最小を採らない。上限が 1 以上になったら切り詰めず「この動作点では床値を
  生成できない」とする (§11.2「値域」)。
  (b) **対象集合は結果を見る前に閉じる。** 集約する spec の相対 path と sha256 の列は**呼び出し側から
  明示的に受け取り、入力 summary から導出しない**。その期待列から導いた窓・層・セル・標本の閉包と、
  入力 summary が実際に報告した閉包の exact 一致を要求する。欠落・重複・余剰・不一致・非生成 status・
  値域外は集約全体を拒否する。**正常な入力だけに間引いて続行しない。**
  (c) **窓と identity。** 各 spec が宣言する窓の数はちょうど 2 とし、全入力で一致することを要求する
  (D1641 決定 3 の「2 時間窓の全部」)。`env_tag`・protocol・スレッド数は全入力の一致を要求し、
  workload と campaign は和を取って識別子を導く。
  (d) **出所と限界を落とさない。** 全入力の summary と spec の path・sha256、各入力の exact な値、
  各入力の非保証欄 (節と項目の両方) を集約成果物へ保存する。最大値を与えた入力だけを残さない。
  (e) **create-only を維持する。** 既存成果物の削除・上書き・改名による再発行を認めない。
  (f) **本追補が保証しないこと。** 機械検査が示すのは「渡された期待 spec 列と入力 summary の閉包が
  一致すること」だけである。**その期待列が結果を見る前に選ばれたことは証明しない** — これは
  発行器が既に逐語で述べている限界そのものである。**期待列が本書の対象集合と意味的に一致すること、
  および 1 campaign・1 セルあたり n = 62 と 24 時間以上の分離が満たされていることも、機械検査では
  確かめない。** 後者は §11.1 の手順 8 が証拠確認者の責任として残しているものであり、
  **この 3 点を機械保証として表示しない。**
  **本追補は §5.1 の解除条件を 1 つも緩めない。** 本欄を記入してよいのは、対象動作点で再実測した
  床値の集約成果物の path と hash を値として書けるときだけであり、本追補は測定の開始も §5 の記入も
  本書の発効も許可しない。**別の集約基盤・台帳・manifest 形式を新設しない** (D1936 項 7)。
- **校正済み `PerfConfig`**: `p3_s4_loop.default_perf()` は自ら「性能比較用 calibration ではない」と
  宣言している (配線規模)。calibrator が決めた値へ差し替えるまで記入しない。
- **総計測予算**: arm ごとに対称とする。失敗した role query と reject も予算を消費する。
  再試行・差替えは禁止。
- **model snapshot / prompt hash / projection hash**: 両アームで同一であることを確認して記入する。
  **本欄は独立した 3 種の値を 1 セルに持つ。§0 の原子性により、すべてが確定するまで
  `未記入` のままにする。** 部分記入の例外は「実行責任者・開始時刻」欄だけであり、本欄へ広げない。
  記入は固定順・固定 tag・区切り `; ` の次の形に限る。
  `expected_claude_model_snapshot=<slug>` に続けて
  `expected_effective_critic_prompt_sha256=<hash>`、
  `expected_closed_critic_projection_closure_sha256[base]=<hash>`、
  同 `[sort]`、同 `[trigger]` を並べる。
  `<slug>` は `claude-opus-` で始まり、以降が英数字と `.` `_` `-` の区切りだけからなる文字列。
  `<hash>` は小文字 16 進 64 桁。**大文字・全角・互換文字を使わない** — 値セルの raw bytes が
  この形と一致しない行は、正規化後に一致して見えても実走前検査が拒否する。
  - **projection は 3 driver 分をすべて書く。** 1 driver 分だけを書ける形にすると、どの driver で
    走るかを結果を見た後に選べる。値は `p3_b4_closed_critic.projection_sha256(kind)` が
    記入時点の checkout から機械導出したものを base / sort / trigger の順で書く。
  - **記入後に閉包 member の bytes が変われば 3 値は同時に無効になる。** 登録は一度きりの行為ではなく
    継続的な不変条件である。変わったら本欄を書き直す。実走前検査はこの陳腐化を拒否する。
  - **prompt hash は repository の bytes から導出する** — 未改変の `.claude/agents/critic.md` の本文と
    mediated projection contract から作る effective prompt の sha256 である。
  - **model snapshot は repository の bytes から導出できない。** 実行時に観測される exact slug と
    照合される事前宣言であり、宣言そのものが値を拘束する。したがって本欄を埋める前に、
    **(a) 結果に依存しない宣言源、(b) 宣言を承認する人間の識別子、(c) 宣言の時点、
    (d) 観測 slug が宣言と食い違ったときの扱い**を別 commit で先に固定する。
    (d) を「宣言を書き換えて同じ実走を続ける」と定めてはならない — 実行時照合が拘束でなくなる。
    4 点が固定されるまで本欄を埋めない。**この 4 点は人間の指名を含むため AI が確定できない** (§10)。
- **env_tag (実測環境)**: 選択した driver と実行 site が確定し、その site の環境契約の exact tag と
  一致することを**同じ site resolver から機械導出して**確認してから記入する。同一 driver でも site に
  よって tag が分かれるため、driver・site・tag の 3 つ組で固定し、環境契約の artifact path と hash、
  確認者を発効版へ併記する。**別 tag の環境で開始した block は削除せず `protocol violation` とする**
  (`判定不能` ではない。事前条件違反であり、差し替えも禁じる)。
- **実行責任者**: 実走前に 1 名を指名し、不変の識別子で記入する。実走後に差し替えない。
  **この欄は計測に依存しないので、計測待ちを空欄の理由にしない。** 指名がないまま実走しない。
- **開始時刻**: timezone 付きの**予定**開始時刻を記入し、「この時刻より前に実走を開始しない」と読む。
  実際の開始時刻は実走成果物側に別途記録し、**本欄を後から実測値へ書き換えない。**
  **追記 (2026-09-08、[T-2140]、D1812 (b)。D1649 決定 2 の本文反映)。** 上の
  「timezone 付きの**予定**開始時刻を記入し、この時刻より前に実走を開始しない」という拘束は、
  2026-09-05 の D1649 決定 2 で撤廃された。同決定の逐語は「欄は `未記入` のままでよく、
  実際の開始時刻は実走成果物側の記録 (既存) だけを正本とする」である。D1812 (b) はこれを承けて
  **固定日時を指名しない**ことを確定した。実投入の順番は D1477 が定めるとおり計算資源の空きで
  決め、実投入時刻は投入時に実走成果物側へ記録する。
  **変わったのは予定開始日時を事前登録する義務だけである。** 実行責任者を実走前に不変の
  識別子で指名する義務、実走後に差し替えない義務、実際の開始時刻を実走成果物側に記録する義務は
  変わらない。**本追記は §5 の値セルを変更せず、行 label も変えない**
  (D1649 が `p3_b4_admission_record.py` の行 label 集合を変えないと定めている)。
  **本追記が決めないこと。** 本欄が `未記入` のままでよいことと、§0 が「placeholder 語が
  1 つでも残る限り実走前検査は閉じたままである」と定めることの関係は、本追記では決めない。
  発効版でこの欄をどう書くかは未裁定であり、ユーザー裁定へ返してある。
  **D1641 が認可したのは床値 (between-run floor) の測定であって、本書に基づく B-4 正式標本の
  実走ではない。** 正式標本の実走には §5 の全欄と §6 の全条件が別途要る (§1、§6)。
  **追補 (2026-09-16、[T-2464]、D1871。開始時刻の受理条件への反映)。** 上の追記が
  「本追記では決めない」と留保した論点 — 本欄が `未記入` のままでよいことと、§0 が
  「placeholder 語が 1 つでも残る限り実走前検査は閉じたままである」と定めることの関係 — は、
  D1871 (2026-09-09) で確定した。**開始時刻を発効条件から外す。** 受理側をこの裁定に合わせ、
  本欄の値に既存の正規化 (セル外周の空白除去と NFKC 正規化) を施した結果が
  `実行責任者 = <値>、開始時刻 = 未記入` へ**全体一致**し、かつ `<値>` が読点・等号・改行を含まず、
  前後の空白を除いて非空であり、既存の予約 sentinel に該当しない場合に限り、
  開始時刻の `未記入` を受理する。この構文は D1871 が定めたものではなく、
  同裁定を実装するために本追補が定める形である。
  **§0 の「placeholder 語が 1 つでも残る限り」は、本欄の開始時刻に置かれた `未記入` には
  適用しない。** 行 label 集合は変えず、他の 9 欄に適用する §0 の原子性・sentinel 規則は
  そのまま維持する。実行責任者を実走前に不変の識別子で指名する義務、実走後に差し替えない義務、
  実際の開始時刻を実走成果物側へ記録する義務は、いずれも変わらない。
  **本追補が決めないこと。** 本追補は受理側への裁定反映を記録するものであり、§5 の欄を埋める
  権限を与えず、値セルを変更せず、本書の発効も B-4 正式標本の実走も認可しない。
  本追補の時点で §5 には本欄以外に 6 つの `未記入` が残っており、実走前検査は閉じたままである。

#### 5.1.0 「対象 driver と軸」の (i) 凍結 (2026-09-05、D1641 / D1266 / D1638)

本小節は §5.1 (i) の項目だけを固定する。番号が 5.1.1 より若いのは、5.1.1 の bytes を
`orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py` が「5.1.1 の見出しから §6 まで」の範囲で
pin しており、その範囲に小節を挿し込めないためである。(ii) の実行と (iii) の記入は本小節を含む commit の
**後続 commit** で行い、本小節の内容は (ii) の実行後に差し替えない。本小節は §5 の値セルを変えず、
発効版ではない。**本小節を読む機械検査は無い** — `orchestrator/campaign/p3_b4_admission_record.py` は
§5 の値セルが非空で sentinel を含まないことだけを見る。以下の規則の履行は記入 commit と insight に人が書く。

- **候補 (driver, 軸) の対 (exact 3、列挙順が優先順):**
  `base = silo-backoff-magnitude`、`sort = silo-writeset-sort`、`trigger = silo-backoff-trigger-gating`。
  driver 名は `orchestrator/campaign/p3_b4_wiring_probe.py` の `_DRIVER_MODULES` と
  `orchestrator/campaign/p3_b4_admission_record.py` の `B4_PROJECTION_DRIVER_KINDS` の共通部分で、
  両者が exact 3 で一致しなければ (ii) を開始しない。軸は各 driver module の `MARKER_ID` であり、
  probe が証拠の `run.axis` へ機械記録する値と上の対が exact 一致しなければ不合格とする。
- **適格性を測る sanctioned CLI command (driver ごとに exact 1 回、別 process):**
  `python3 tools/pegasus/dispatch_compute.py --task generic -- python3 -m orchestrator.campaign.p3_b4_wiring_probe --driver base --evidence-set-id t2341-eligibility`
  (`sort`、`trigger` は `--driver` だけを替えた同形。dispatch 側の運用 flag (`--walltime`、
  `--queue-wait-timeout`、`--overall-grace`) は `--` より前に足してよく、`--` より後の probe argv は exact)。
  実行 site は Pegasus 計算ノード (gen_S)、cwd は repository root、env は dispatch の clean 既定。
  **前提:** 本小節の commit が実行時 HEAD の祖先であること、3 driver 分の証拠 target (JSON と sidecar) が
  いずれも不存在であること、3 command を同じ HEAD から投入すること。login node で得た証拠は採用しない。
  infra 失敗 (dispatch rc=16 等) は「不合格 0 件」ではなく手続き未完了として停止し、証拠を作らない。
- **証拠の保存先と hash:** `output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/` 直下の
  `<driver>.json` と detached sidecar `<driver>.json.sha256` (probe が同時に書く)。sidecar は
  `<64 桁小文字 hex><空白 2 つ><driver>.json` の 1 行で、値は JSON bytes の sha256。CLI は既存 target を
  拒否するため、同じ evidence-set-id では再走できない (1 回性)。**合否を問わず 3 driver 分の JSON と
  sidecar を削除・改名せず tracked にする。** base / sort の証拠は site を記録しないので、3 件の dispatch
  receipt (request ID と compute marker を含む) を insight に tracked にし、記入 commit の message から参照する。
- **合格述語 (すべて満たすときだけ合格。部分点は無い):**
  (a) command が rc=0 で終わり、JSON と sidecar が実在し、sidecar の値が JSON bytes の sha256 と一致する。
  (b) `run.driver` と `run.axis` が上の対と exact 一致し、`run.evidence_set_id` が `t2341-eligibility`、
  `run.argv` が `["--driver", "<driver>", "--evidence-set-id", "t2341-eligibility"]` と exact 一致する。
  (c) `source.repository_head` が本小節の commit を祖先に含む。
  (d) `result.passed` が `true`、`result.pass_rule` が
  `all-four-checks-and-zero-interdiction-or-protected-root-violations`。
  (e) `checks.campaign_identity.site_projected_cfg` が `null` でない driver (現行では trigger) について、
  その `status` が `measured` かつ `site` が Pegasus 計算ノード。
- **決定規則 (証拠を見る前に固定し、結果を見た後で変えない):** 3 候補すべてを判定した後、合格集合から
  列挙順 `base → sort → trigger` の最初の 1 件を選ぶ。合格 0 件なら「対象 driver と軸」欄は `未記入` の
  まま残し、insight に 3 件の証拠 path と不合格理由を列挙して実走へ進まない。
- **記入の形 (§5 の値セル 1 行。3 候補すべての証拠を束縛する):**
  `<driver> (<軸>); evidence_set=t2341-eligibility; base.json sha256=<64hex>; sort.json sha256=<64hex>; trigger.json sha256=<64hex>; 記入者 = レビュー者 = thawk105 (D1266、D1638)`。
  path root は上の保存先に固定する。
- **記入者とレビュー者:** いずれも `thawk105` (D1266)。レビュー者は独立検査者ではなく、記入内容が本小節と
  §5.1 (ii)(iii) を満たすことの確認責任者である。操作は D1638 の委任により AI が `thawk105` 名義で行い、
  記入 commit の message に本小節の commit hash と採用した証拠の sha256 を書く。

#### 5.1.1 分析契約の一括凍結 (D1082)

D1082 に従い、**赤 precursor の母集合・最小重要効果・n・primary outcome の純関数を
同じ変更単位で凍結する。** 最小重要効果は pilot と独立に固定する。

**何を凍結し、何が後に残るかを取り違えない。**

- **今この変更単位で確定するもの:** 最小重要効果の値、n の値、primary outcome の演算と
  実験 verdict の関数、そして母集合を決める適格性述語・順序・選択関数・完全性要件と
  割当の無作為化要求。**4 項目とも、後日の裁量判断へ先送りしない。**
- **後に残るもの:** 母集合の**実体** (`analysis_manifest` の bytes) と、それが依存する
  §5 の他欄 (対象 driver と軸、校正済み `PerfConfig`、floor)。
  これらは本節の規則と §5.1 の解除条件から**一意に決まる**。
  実体の生成は凍結済み規則の機械適用であって、新たな凍結判断ではない。
- **禁じるもの:** 規則の外で母集合を選び直すこと。項目ごとに別の時期へ凍結を先送りすること。
  実体を見てから規則を変えること。

**本節の規則は、それ自体では何も機械強制しない。** 本節末の発効条件を参照する。

##### 赤 precursor の母集合 (適格性述語・順序・選択関数)

**台帳を 2 つに分ける。1 つの台帳に 3 つの役割を負わせない。**

- **`scheduled_attempt_registry`** — 予定した attempt を**全件**残す append-only の台帳。
  生成失敗・赤の非再現・重複・破損・screening のみの赤も、除外理由にせず固定 enum の理由を
  付けて残す。成功した attempt だけを載せる経路を禁じる。§7.1 の全件報告はこの台帳が担う。
- **`analysis_manifest`** — 上の台帳から適格性述語で選んだ分析対象。母集合はこの**全行**である。

**適格性述語** (結果を見る前に固定する。これ以外の理由で行を落とさない):

- `whiteboard.result` が `rejected` であり、かつ §3.1 が digest へ載せる 4 クラス
  (verify-red / liveness / other / diff-quarantine) の少なくとも 1 件を持つ。
  **screening だけの赤は適格でない。** §3.2 のとおり screening は**両アームとも** digest に
  載らず treatment の差分ではないため、構造的に treatment が発火しえない。
  これは結果を見る前の定義上の除外であり、事後の間引きではない。
- workload が、その driver の校正済み `PerfConfig` が定める workload に属する。
  **その workload を全件使う。** 結果を見てからの部分集合化を禁じる。
- 初期 proposal が、事前に固定した bootstrap 集合に属する。実走開始後に足さない。
- 後述の共通参照点 (`reference`) が一意に定まる。
- precursor を作った走行が**どちらのアームの digest も受けていない**。
  片アームの digest を受けた precursor から作った block は pair として成立しないので、
  適格でないとし、`scheduled_attempt_registry` には protocol violation の理由で残す。

**順序と選択関数:**

- `analysis_manifest` の行は、`scheduled_attempt_registry` の canonical 順序 (registry へ
  追記された順。同着は attempt id の辞書順) を保って並べる。
- 適格行が n 未満なら `design_not_feasible` とし、実走しない。**n を予算へ合わせて切り下げない。**
- 適格行が n を超える場合は、上の順序で**先頭 n 行**を採る。結果を見てから選び直さない。

**割当の無作為化 (帰無分布の前提):**

- 各 block について、on / off を実行 slot へ割り当てる 2 通りのうち 1 つを、**確率 `1/2` ずつ、
  block ごとに独立に**、**実走前に**選び、その schedule を `analysis_manifest` へ固定する。
  この無作為化が、後述の検定が使う「block 内でアーム label を交換してよい」という
  sharp な帰無仮説を成立させる。無作為化なしでは帰無分布は二項分布にならない。
- schedule を実走後に変えた block、および schedule どおりに実行されなかった block は
  protocol violation とする。**遵守の結果を verdict 関数の入力に含める。**
- この無作為化は測定順序の効果も同時に扱う。**逆順 1 本による順序効果の否定は行わない** (D1095)。

**完全性:**

- `analysis_manifest` は生成器と `scheduled_attempt_registry` から再生成でき、
  行集合と順序が exact に一致することを確かめられなければならない。
  **hash を記録するだけでは完全性の証明にならない。**
- 生成後の**追加・削除・並べ替え・driver の差替え**は `design_not_feasible` とし、実走しない。
- **registry 側の protocol violation を manifest から外して洗い落とせない。**
  `scheduled_attempt_registry` に protocol violation の理由を持つ行が 1 件でもあれば、
  その件数を verdict 関数の入力に渡し、実験全体を protocol violation とする。
  違反 attempt を後続の適格行で置き換えて成立を得る経路を、この規則が塞ぐ。

##### 最小重要効果 (pilot と独立に固定)

**最小重要効果は確率優越 `A_min = 0.60` とする。** 無次元、尺度は 0 以上 1 以下、
大きいほど on が良い。差なしは `A = 0.50` であり、検出対象の差は `0.10` である。
これは tie を半分ずつ数えた後で、on の勝ち率が off の勝ち率を 20 percentage point 上回ることに等しい。
これより小さい改善を B-4 の機序証拠として重要とは扱わない。

**この値は次のいずれからも導いていない** — §9 の既知結果、pilot、算出した n、総計測予算、
対象 driver、対象軸、赤形状の頻度、欠測率、観測された `A`。
本書の estimand は狭い機序主張 (§2.1) であり、大効果を主張する実験ではないので、
慣用的な大効果の閾値をこの estimand の重要性へ流用しない。
**実行可能性を理由に `A_min` を上げない。** 後述のとおり `A_min` を上げるほど必要 block 数は
減るため、実行可能性で選べば必ず上げる方向へ倒れる。その方向の変更を禁じる。

**`A_min` は必要 block 数の導出にだけ使う。判定の閾値にしない。**
標本値が `A_min` に届いたことを成立の条件にすると、真値がちょうど `A_min` のとき成立確率が
おおむね半分で頭打ちになり、n をいくら増やしても目標検出力に到達しない。
代わりに、成立と報告する走行では `A_hat` の点推定、tie 件数、非 tie 数 `m`、および
後述の `theta` の厳密な信頼区間を必ず併記し、
点推定が `A_min` を下回る場合は**「最小重要効果に満たない効果」と明記する**。

##### n と検定単位

検定単位は **block** とする。1 つの block 内の on / off は同じ precursor に対する pair であり、
iteration や session 内 rep を独立な検定単位へ昇格させない。

**pilot を置かない。分散の推定に標本を使わない。**
必要 block 数は、下に定める厳密検定そのものの検出力から直接求める。**正規近似を使わない。**
これは pilot が「必要 block 数を小さくする」自由度を持たない形であり、
D1082 が最小重要効果を pilot から切り離した理由をそのまま n へも適用したものである。
**本契約は pilot を持たない。** pilot を導入するなら、結果を閲覧する前に、
本節の 4 項目すべてを同時に凍結し直す新しい事前登録が要る。現発効版へ遡及適用しない。

**検出力を計算する統計モデルを先に固定する。**

- block は母集合から**独立同分布**に引かれるものとする。
- 各 block は、on 上位を確率 `a`、tie を確率 `t`、off 上位を確率 `1 - a - t` で取る。
- 対立仮説は「真の `A = a + t/2` が `A_min = 0.60`」とする。`t` は固定しない。
  `A` を保つ `t` の全域 (`p = a / (1 - t)` が 1 を超えない範囲) について検出力を要求する。
- 検定する帰無仮説は、**各 block 内でアーム label を交換してよい**という sharp null である。
  §5.1.1 の割当無作為化 (2 通りの割当を確率 `1/2` ずつ、block ごとに独立) がこれを成立させる。

導出は次のとおりである。

- 片側の有意水準は**方向ごとに `0.025`** (両方向あわせて `0.05`)、目標検出力は `0.80` とする。
- **`t` を動かすと検出力は単調には動かない。** 非 tie 数が減る効果と、非 tie 上の on 勝率
  `(A - t/2) / (1 - t)` が上がる効果に加え、棄却境界が離散に動くためである。
  したがって「tie 率 0 が最悪」と仮定せず、**許容する `t` の全域での最小値**で n を決める。
- この条件で厳密符号検定の検出力が全域で `0.80` 以上になる最小の block 数は **`n = 201`**
  である。最悪は `t` が約 `0.009` のときで、そのときの検出力は約 `0.8017`。
  参考までに `t = 0` では約 `0.8104`、`t = 0.1` では約 `0.8354` である。
- 棄却境界は実走後に観測された非 tie block 数から同じ規則で決める。n から先に固定しない。

**適格な block を 201 件確保できない場合、n を予算に合わせて切り下げない。**
その場合は実走前に「記述統計に留め有意性を主張しない」と本書へ明記してから実走するか、
実走しない。この分岐の判定は結果を見る前に行う。

##### primary outcome の純関数

**入力**は次の 4 つだけである。関数はこれ以外を参照しない。

1. `floor` — §5 の凍結 artifact から読んだ値。関数の**引数として渡す**。関数内で導出しない。
   値域は `0` 以上 `1` 未満の有限値。範囲外・非数・欠落は下の `analysis_invalid` とする。
2. `contract_binding` — 凍結側の期待値。次を持つ。
   - `manifest_sha256`、`registry_sha256`
   - block ごとの期待値: `block_id`、`reference_tps`、`reference_snapshot_hash`、
     `reference_receipt_hash`、割当 schedule
   - `expected_block_count` (= n)
   **観測側の値はこの期待値と exact に一致しなければならない。**
   一致検査を関数の外へ出さない。外に出すと参照点や違反件数の差替えを関数が検出できない。
3. `registry_violation_count` — `scheduled_attempt_registry` 上で下の理由 enum のいずれかを
   持つ行数 (`0` 以上の整数)。負値・非整数・欠落は `analysis_invalid` とする。
   **registry の protocol violation 理由 enum** は次で固定する —
   `arm_digest_contaminated_precursor` (precursor がどちらかのアームの digest を受けた)、
   `assignment_schedule_violated`、`arm_asymmetric_gate` (§4 のアーム非対称)、
   `env_tag_mismatch` (§5.1 の env_tag 規範違反)、`manifest_mutated_after_freeze`。
4. block の列。各 block は次を持つ。
   - `block_id` — `analysis_manifest` の canonical id
   - `reference_tps` — 後述の共通参照点の throughput (有限の正)
   - `reference_snapshot_hash`、`reference_receipt_hash` — 参照点の出所。
     `analysis_manifest` に固定された値と一致しなければならない。
   - `assignment_followed` — 無作為化 schedule どおりに実行されたかの真偽値
   - **アームごと**に `precursor_hash`、`status`、`throughput`、`treatment_fired`、
     `contaminated`、`protocol_ok`
   - `status` の値域は `certified` / `rejected` / `aborted` / `missing` のちょうど 4 値。
     `certified` のときだけ `throughput` を有限の正として持ち、他の 3 値では値を持たない。
   - `treatment_fired` は**そのアームで treatment が発火したか**を表す真偽値である
     (on では赤詳細が digest へ載ったこと、off では載らなかったことが確認できたこと)。
   - `contaminated`、`protocol_ok`、`assignment_followed` は真偽値。
   - `duplicate`、`dry-pass`、実行前の停止、crash、終端記録の不在は、すべて `missing` へ写す。
     **行そのものを落とさない。**
   - 真偽値が真偽値でない、field が欠落している、`block_id` が `analysis_manifest` に無い
     場合は下の `analysis_invalid` とする。

**共通参照点** `reference_tps` は、その block の precursor から祖先方向へ辿って最初に現れる
certified snapshot の session-level throughput とする。**参照点はこれ 1 つとし、
arm 内前後の別基準を使わない。** 該当する祖先が無い、複数の候補が同着で並ぶ、
対応する throughput の receipt が `PerfConfig` と `env_tag` の一致で特定できない場合は、
その block を適格でないとする (実走前に判明するため `design_not_feasible` の対象であり、
実走後に判明したら protocol violation とする)。**代替基準へ切り替えない。**
参照点の出所 (`reference_snapshot_hash` と `reference_receipt_hash`) は
`analysis_manifest` に固定し、分析時に差し替えられないようにする。

**アームの順位**は次で固定する (良い順)。

1. `certified`
2. `rejected` と `aborted` — **この 2 つの間だけが常に tie である。**
3. `missing`

`certified` は throughput にかかわらず、すべての非 certified より上とする。
`missing` は `rejected` と `aborted` の**下**であり、tie ではない。**除外もしない** (§7.1)。
`rejected` と `aborted` を互いに tie とするのは、§4 が reject に fitness を付けないと定めるため、
性能に類する量で両者を並べないからである。

両アームが `certified` の block では、アームごとに
`利得 = throughput / reference_tps - 1` を取り、
2 つの利得の差の絶対値が `floor` 以下なら tie、それ以外は利得の大きいアームを上位とする。
境界値は tie に含める。

block score `X` は、on が上位なら `1`、tie なら `1/2`、off が上位なら `0` とする。

**確率優越 A** は、母集合から事前規則どおりに選ばれた 1 block について
`A = P(on が上位) + (1/2) * P(tie)` と定義する。標本推定値 `A_hat` は全 block の `X` の
相加平均であり、有理数として exact に計算する。**`A` は母数、`A_hat` は標本値であり、
判定文では取り違えない。**

**純関数性** — 入力は上の 3 つだけであり、file system・時刻・環境変数・乱数・
network・model・global state を参照しない。同じ入力から常に同じ値を返す。

**入力検証を先に完了させる。** 下の理由 enum の判定を**すべて**行い、1 つでも当たれば
`analysis_invalid` を返して終わる。**verdict の分岐評価はその後に始める。**
検証前に値を読んで分岐しない (負の値や不正な型が分岐へ流れ込まないようにするため)。

**`analysis_invalid` の理由 enum** (いずれかに当たれば、行を除外せず出力全体を無効とする):

- `block_count_mismatch` — block 数が `expected_block_count` と異なる
- `duplicate_block_id` / `unknown_block_id` — id の重複、`contract_binding` に無い id
- `precursor_hash_mismatch` — 同じ block の両アームの `precursor_hash` が一致しない
- `reference_binding_mismatch` — 参照点の `reference_tps`・`reference_snapshot_hash`・
  `reference_receipt_hash` のいずれかが `contract_binding` の期待値と一致しない
- `reference_value_domain_error` — `reference_tps` が有限の正でない
- `status_domain_error` — `status` が値域外
- `throughput_contract_error` — `certified` なのに `throughput` が無い、
  または `certified` でないのに `throughput` がある、値が有限の正でない
- `floor_domain_error` — `floor` が値域外・非数・欠落
- `violation_count_domain_error` — `registry_violation_count` が負・非整数・欠落
- `binding_domain_error` — `contract_binding` の hash・id・期待値が欠落、型違反、
  または `expected_block_count` が正の整数でない
- `field_missing_or_ill_typed` — 上のいずれにも分類されない欠落または型違反 (受け皿)

**この enum は全域である。** 受け皿を含むため、入力契約に反する入力は必ずどれかに当たる。

`analysis_invalid` の実験としての扱いは次節で定める。

**検定**は、tie でない block だけを取った**厳密な符号検定**とする。
アーム label の block 内交換で値が変わるのは tie でない block だけなので、
帰無分布は非 tie block 数 `m` を試行数とする対称二項分布に一致する。
**この一致は、上で定めた実走前の無作為な割当が成立している場合にだけ言える。**
無作為化されていない割当では、block ごとの勝率が不均一なとき帰無分布は二項分布にならない。
割当が事前無作為化されていない走行は protocol violation とする。
**全 label 交換の逐一列挙は要求しない** (block 数に対して実行不能になるため)。

方向ごとに 2 つの片側 p 値を定める。`W` を on が上位の非 tie block 数として、
`p_on` は `Bin(m, 1/2)` の上側 `P(W' >= W)`、`p_off` は下側 `P(W' <= W)` とする。
**方向ごとの有意水準は `0.025`**、両方向あわせて `0.05` とする。`m = 0` のときは
`p_on = p_off = 1` とする。多重比較は B-4 独立の族で Holm 補正する (§7.1)。
primary は 1 つなので補正後の値は未補正値と一致する。

##### 実験 verdict は全域関数とし、§7.1 の 4 分類へ写す

`A_hat` と p 値だけで判定しない。**入力検証を先に完了させたうえで**、
次を上から順に評価し、**最初に当たった分岐で確定する**。
どの入力でも必ず 1 つに当たる (全域関数)。

1. 出力が `analysis_invalid` — **protocol violation**。理由 enum を併記する。
   入力契約に反する解析は成立とも不成立とも読めず、事前条件違反なので §7.1 の
   protocol violation に当たる (判定不能ではない)。
2. `registry_violation_count` が `0` より大きい、いずれかの block でいずれかのアームの
   `protocol_ok` が偽、または `assignment_followed` が偽 — **protocol violation**。
   §7.1 は protocol violation を独立の分類として持つので、判定不能へ畳まない。
   個々の block も全件報告する。
   **`protocol_ok` は汚染を含まない。** 汚染は次の分岐が扱う。両方が同時に真の場合は、
   上から順の評価によりこの分岐が先に当たり、**protocol violation が優先する**。
   事前条件違反は、汚染の有無にかかわらず解析の前提を壊すためである。
3. いずれかの block で `contaminated` が真 — **判定不能**。
   §7.1 が off 汚染を判定不能と定めるため、その分類に従う。
4. 両アームとも `treatment_fired` が真である block の数が n に満たない — **判定不能**。
   §7.1 の「n 不足」「treatment 未発火」がここに当たる。
5. `p_on` が `0.025` 以下 — **成立**。`A_hat` の点推定、tie 件数、`m`、
   下の `theta` の信頼区間を必ず併記する。
   `A_hat` が `A_min` を下回るなら「最小重要効果に満たない効果」と明記する。
6. `p_off` が `0.025` 以下 — **不成立**。
7. それ以外 — **判定不能**。**「還流に価値なし」とは書かない** (§7.1)。

分岐 5 と 6 は排他である (同じ `m` に対して両側の尾がともに `0.025` 以下にはならない。
2 つの尾の和は必ず 1 を超えるため)。

**信頼区間**は、非 tie block 上の `theta = P(on が上位 | tie でない)` に対する
Clopper-Pearson の厳密両側 95% 区間とする。**これは `theta` の区間であって `A` の区間ではない。
本書は `A` の信頼区間を定めない。** 報告では `A_hat`、tie 件数、`m`、`theta` の区間を
並べて書き、取り違えない。`m = 0` のときは区間を `[0, 1]` とし、`theta` は推定不能と書く。

##### 本節が発効の条件として要求すること

本節は文面であり、それ自体は何も機械強制しない。**次が実在するまで本書は発効しない。**
現在どこまで閉じているかという可変の現在地は §7.2 と §10 が正本であり、ここへ再掲しない。

- raw な試行記録から本節の入力型を作る経路 (adapter) と、その実装が本節の定義と一致することを
  検査する consumer。
- `scheduled_attempt_registry` と `analysis_manifest` の生成器と、再生成による完全性の検査。
- 実走前の割当無作為化 schedule と、それが実走で守られたことの検査。

**`n = 201` は総計測予算を超える見込みが高い。** その場合の分岐は上に事前宣言したとおりである。

## 6. 実走の前提条件 (1 つでも未充足なら実走しない)

B-4 prerun publication root (repo 相対): `output/b4-prerun-publication`

上の 1 行が本書における publication root の名指しである (D1881)。発行器はこの repository root
から解決した場所だけへ発行し、それ以外の root での発行を拒否する。呼び手は発行先を選べない。
**ここでいう repository root は、import された発行器の file を置く、本書を同梱した source checkout
である。** 呼び手の作業ディレクトリを基準にしない。本書を同梱しない配置から import した場合、
発行器は名指しを読めないので発行を拒否する。
**名指しが閉じるのは発行器を経由する発行だけである。** loader と bootstrap 束縛は呼び手から
受け取った root をそのまま使うので、別の checkout で名指しどおりに発行した bundle を
別の呼び手が絶対 path で指す経路は本項では閉じない。

1. §5 の全欄が記入済みで、その版が commit されている。
2. **D903 が確定した架構と一致している。** 本書と実走は critic への赤の可視性 on/off だけを扱い、
   機械が導いた制約の適用 on/off を含めない。
3. **閉じた critic invocation が用意されている。** 現行の `.claude/agents/critic.md` は critic に
   `Bash` を与え、`python3 orchestrator/critic/digest.py --campaign-dir` の自己実行を
   **明示的に許可**している。同 CLI は reflux 引数を持たず、screening を含む赤の全節を常に描画する。
   **この critic role を使う実走は off アームとして数えない。**

   **現在地 (2026-08-26、[T-1697]):** 実験専用の閉じた起動形を
   `orchestrator/campaign/p3_b4_closed_critic.py` に置いた。role file は 1 byte も変えていない
   (D904)。同 module は未改変の `critic.md` を runtime `tools=[]` へ落とした projected provider へ
   渡し、payload を `projected_digest` と coarse な `result` の 2 key に限り、campaign path /
   campaign_id / repository root の exact literal が payload の canonical JSON bytes に
   現れないことを 3 view で検査し、on/off を別 controller・別 provider・別 context・別 session で
   起動して receipt を残す。
   **現在地の更新 (2026-08-26、段 4 driver への必須配線):** [T-1697] の機構を、段 4 の 3 driver
   (base / sort / trigger-gating) が**要求する**形へ配線した。閉じた範囲は次に限る。

   - 3 driver の `default_cfg()` に、campaign identity へ残る exact な B-4 protocol marker を
     opt-in で足した。**marker 不在の通常走行の campaign identity と proposal 契約は変えていない**
     (本 wave 前の実測値を golden として固定した)。
   - marker 付き走行の継続は、certified な閉じた invocation の terminal receipt を必須とし、
     campaign id・arm・iteration・live WAL bytes・live checkpoint bytes・再生成した digest・
     driver 種別・authoritative layout のすべてが一致しなければ、iteration を進める前に停止する。
     layout は呼び手が渡した値でなく campaign id から再構成した値だけを使う。
   - 同一 receipt の 2 度目の消費を拒否し、gate が発火した事実を campaign 成果物へ残す。
   - `prior_critic_reverse` の自己申告を marker 付き走行で禁じ、receipt の
     `decision_reverse_recommended` から取る。

   **前提条件 3 はこれでも「off の全経路が閉じた」ことを意味しない。正直に書く。**

   - **閉じたのは「閉じた critic invocation が実在し、この campaign・arm・iteration・digest に
     束縛されて一度だけ消費された」ことまでである。**
   - **「その critic の決定で次の合成を行った」ことは閉じていない。** proposal が持つ receipt hash は
     proposal 作成者の**自己申告**であり、legacy critic の出力から作った proposal に valid な
     receipt hash を書き写せば通る。閉じるには決定を入力とする sanctioned な proposal producer が
     要り、閉じた critic module は設計上 proposal を書かない。**§10 に未了として残す。**
   - legacy の `Agent(subagent_type='critic')` 経路は、B-4 の正式標本としては不適格になったが、
     走ること自体は止まらない。marker は自己申告であり分類の権限を証明しない (§7.2)。
   - §5 の欄が未記入でその事前 commit が済んでいないことは**前提条件 1 の未充足**であって、
     本条件の問題ではない。
4. **API 直呼びと `policy_hint` の規律が守られている。** `run_one_iteration()` の戻り値には
   reject 時に `digest`、certified/aborted 時に `records` (WAL payload 一式) が載る。
   sanctioned CLI はこれを表示しないが、Python API を直接呼ぶ controller には見える。
   実走は sanctioned CLI 経路に限り、`policy_hint` は absent か両アーム byte 同一に固定する。
5. **`prior_critic_reverse` の供給規則が確定している。** 同値は proposal JSON から読まれるだけで
   arm・digest・critic invocation receipt と束縛されていない。かつ `check_stop` の
   `reverse-exhausted` を単独で発火させ、次 synthesis の有無を変える。
   本書の primary は paired 1-step (§2.1 と §5.1) なので停止差は primary に入らないが、
   **供給規則を書かずに実走しない。**
6. 対象動作点の floor が再実測済みで、その artifact が本書から参照されている。
7. 負の対照 (§8) が緑である。
8. 実行環境が確定し、単独性が確認されている。
9. **§5.1.1 の分析契約を実行する経路が実在する。** raw な試行記録から §5.1.1 の入力型を作る
   adapter、その実装が §5.1.1 の定義と一致することを検査する consumer、
   `scheduled_attempt_registry` と `analysis_manifest` の生成器と再生成による完全性検査、
   実走前の割当無作為化 schedule とその遵守検査が、いずれも実在する。
   **文面だけの分析契約で実走しない。** 実走前検査は値セルの型・意味・参照先を検査しないので、
   この条件は機械では代替されない。

## 7. 全件報告規則と、その機械強制の現在地

### 7.1 規則

- **全 block・全アームを無条件に完走する。** 途中結果による除外・差し替え・停止をしない。
- **停止理由・未到達・crash・treatment 未発火・protocol violation を含め全件を報告する。**
  走らせた block が報告に現れないこと (file-drawer) を禁じる。
- 各行に arm、campaign id、初期 snapshot hash、model/prompt/projection hash、WAL path/hash、
  停止理由、予算消費、verdict、anomaly class、性能値の有無を持たせる。
- **勝ったアームだけを headline にしない。** 差が floor 以下なら「差なし」と報告する。
- **判定は 4 分類に分ける。** 成立 / 不成立 / 判定不能 / protocol violation。
  **非有意は「判定不能」であって「還流に価値なし」ではない。** n 不足・treatment 未発火・
  off 汚染はいずれも判定不能とする。同等性を主張するなら事前固定した equivalence margin と
  十分な検定力を別途要求する。
- 多重比較は **B-4 独立の族**で Holm 補正する。凍結済みの S-1〜S-3 族へ後付けで追加しない。

### 7.2 機械強制の現在地 (正直に書く)

**上記はいずれも規範であり、機械強制されていない。** 現時点で次が開いている。

- **file-drawer は開いている。** manifest・append-only registry・完全性 consumer は存在しない。
  不都合な campaign を別 root へ出す、report 前に止める、台帳に載せない経路が残る。

  **追記 (2026-09-08、[T-2140]、D1812 (d))。** 上の「manifest・append-only registry・
  完全性 consumer は存在しない」という一括断言は、現在の実装を表さない。
  `orchestrator/campaign/p3_b4_analysis_ledgers.py` に、issuer 束縛の batch receipt からのみ
  封印できる scheduled registry の型、封印済み prefix を保ったまま protocol violation を
  追記する純関数、analysis manifest の生成器、生成物を厳密に再生成して照合する完全性検査が
  実在し、`orchestrator/campaign/p3_b4_prerun_issuer.py` がその完全性検査を呼んで
  create-only の bundle を発行する。
  **実在するのはここまでである。** 権威ある producer は作成も同定もされておらず
  (`p3_b4_analysis_ledgers.py` が自らそう宣言している)、正式 launcher への必須配線も無く、
  2026-09-08 時点で B-4 issuer が発行する固定名の成果物
  (`scheduled-attempt-registry.jsonl`、`analysis-manifest.json`、`prerun-issuer-receipt.json`) は
  `output/` 配下に 1 件も無い。
  **したがって上の結論は変わらない — file-drawer は開いている。** 不都合な campaign を
  台帳に載せない経路も、別 root へ出す経路も残る。本追記は §7.1 の全件報告規則を実効化せず、
  §5 の「赤 precursor の母集合」欄を記入済みとも扱わない。
- **off アームの遮断は、1 経路についてだけ閂になった。残りは開いている。**
  負の対照 (§8) の項目 1〜5 が固定するのは、**harness が生成する critic digest における
  loader 非呼出**までである。項目 6 (必須配線、2026-08-26 に追加) が足したのは、
  **marker 付き sanctioned continuation を通る限りにおいて**次が成立することである —
  閉じた critic invocation が実在し、この campaign・arm・iteration・digest・driver 種別に
  束縛され、一度だけ消費されたこと。停止挙動を変える `prior_critic_reverse` が自己申告でなく
  receipt 由来であること。

  **依然として開いている経路 (1 項も削らない):**

  - **「その決定で次を合成した」ことは閉じていない。** proposal が持つ receipt hash は
    proposal 作成者の**自己申告**であり、legacy critic の出力から作った proposal に valid な
    receipt hash を書き写せば通る。**本書の関門は「閉じた critic が併存した」ことまでを示す。**
  - `run_one_iteration()` の Python API 直呼びは、**2026-08-27 の専用起動器で列挙した境界について
    閉じた** — 3 driver の `default_cfg` / `run_one_iteration` / `drive_iteration`、
    production factory、certified sink の COMMIT 合流点である。閉じた根拠は、
    exact marker を持つ campaign がこれらの境界で、起動器だけが鋳造できる封印済みの起動 context と、
    権威 layout に置かれた起動記録との一致を要求することである。
    **ただし、marker を持たない campaign を報告時だけ B-4 と名乗る経路は開いている。**
    **COMMIT の後に campaign lock を書き換えて B-4 と名乗り直す経路も開いている** —
    sink の関門は COMMIT の時点で exact marker が存在した経路だけを閉じる。
  - `policy_hint` は無加工で planner payload へ入る。
  - legacy の `Agent(subagent_type='critic')` route は、B-4 の正式標本としては不適格になったが、
    走ること自体は止まらない。
  - **B-4 protocol marker の自己申告は、一部だけ閉じた (2026-08-27)。**
    **閉じたのは「封印されていない marker の作成」である** — sanctioned な 3 driver の
    `default_cfg` は、起動器だけが鋳造できる封印済みの起動 context が無ければ marker を作らない。
    試験用の封印でも marker は作れるが、標本を生む境界 (反復・駆動・certified sink・
    production factory) はすべて production の封印を要求するため、試験用の封印から
    certified な標本は 1 つも作れない。
    **閉じていないのは次である。marker 不在の campaign を報告時だけ B-4 と名乗ること。
    COMMIT の後に lock を書き換えて B-4 と名乗り直すこと。**
    **marker は依然として必要条件であって十分条件ではない。**
  - **certified の実行主体は認証されない。** production factory は `PATH` 上の `claude` を
    解決するだけで、その binary の identity を認証しない。PATH 上に schema 適合の偽 `claude` を
    置けば、任意の決定について `evidence_class=="certified"` の receipt を作れる。
  - **pair の完全性と receipt shopping。** 関門は receipt 1 枚を検証するが、on と off が同じ
    block・同じ precursor・同じ model/prompt から来たことを強制しない。複数の pair を作り
    都合のよい receipt を選ぶ経路が残る (同一 receipt の再消費だけは閉じた)。

  **起動器が保証しないこと (2026-08-27):** 同一 process からの closure 内省と module 属性の
  書換えに対する耐性は保証しない。Python では `__closure__` の走査を塞げないため、
  同一 process 内から封印と発行者へ到達できる。**閉じたとは書かない。**
  内省を要しない素直な経路 (任意の封印を受け取る生成関数が module の属性として見えること) は
  塞いである。

  同 module が保証しないことは receipt の非保証 field に列挙してある — 間接識別子
  (variant label / src token / genome label / WAL 由来自由文) の非開示、報告されない local な
  tool 使用の不在、同一 process からの module 属性書換えに対する耐性、進んだ WAL と
  一世代古い loop state の組合せの排除、storage failure 時の receipt 完全性。
- **既知の生存変異が 2 件ある** (§8 の末尾)。

## 8. 負の対照 (前提条件 7)

`orchestrator/tests/test_p3_s4_loop.py` に置く。固定する性質は次のとおり。

1. off アームで 4 loader (`load_rejections` / `load_liveness_rejections` /
   `load_verify_abort_signals` / `load_diff_rejections`) が**一度も呼ばれない**
   (call ledger 付き spy)。on では各 1 回呼ばれ固有 marker が出る。
2. off の戻り値が緑 digest と **byte 一致**する。fixture の中身によらず必ず出る見出し 2 種
   (`# rejections` / `# verify run の abort 統計`) が off に無く on に有る。
3. 3 driver の `default_cfg(reflux=True/False)` で `reflux` だけが異なり、
   `canonical_preimage` と `campaign_id` が異なる。
4. **規律 2 / 3 の正対照** — off でも `outcome=="rejected"`、WAL に `STAGE_ABORT` と
   diff-quarantine reason、checkpoint に `whiteboard.result=="rejected"`。
   on/off の正規化済み WAL payload が exact equality。
5. sanctioned CLI の stdout に赤詳細 field の sentinel が現れない。

6. **必須配線の関門** (2026-08-26 に追加。`orchestrator/tests/test_p3_b4_closed_critic.py` と
   `orchestrator/tests/test_p3_s4_loop.py` および sort / trigger の各 test file に置く)。
   marker 付き走行が certified な receipt を要求すること。campaign id・arm・iteration・
   live WAL・live checkpoint・再生成 digest・driver 種別・authoritative layout・layout の exact type の
   各照合が**それぞれ単独で**外れると赤になること。`test-only` evidence の拒否。
   proposal の receipt hash 不一致の拒否。`prior_critic_reverse` 自己申告の拒否。
   同一 receipt の再消費と並行二重書込みの拒否。bootstrap への receipt 供給の拒否。
   marker + `--no-build` の拒否。marker 不在の通常走行の campaign identity が
   本 wave 前の実測値と一致すること。

   **変異による裏取り:** 上記の各検査を 1 つずつ外す 15 変異を実装前に事前登録し、実走した。
   **baseline 緑、15 件すべて KILLED、生存ゼロ、MISMATCH ゼロ。** 期待ノードは probe 走で
   実観測した完全集合を使い、各変異は自分の狙ったテストだけを落とした (過剰決定なし)。

**このテスト群が証明しないこと (省略不可の限定):**

- **critic role の能力遮断を証明しない。** §7.2 の経路は閉じられない。
  [T-1697] が足した `orchestrator/tests/test_p3_b4_closed_critic.py` も同様で、そこが示すのは
  **専用 invocation の declared tools と、観測された envelope の事実**だけである
  (`declared_tools=[]`、`permission_denials==[]`、`server_tool_use` 全 0、`num_turns==1`)。
  critic role 自体の能力遮断も、他 route の遮断も示さない。
- **T4 は `do_build=False` で走るため、verifier・auditor gate・build/verify/bench の順序を
  検査しない。** 固定するのは base driver の diff-quarantine reject 1 経路である (§4)。
- **項目 3 が固定するのは campaign identity の分離であって、実 path の分離は
  sanctioned CLI の ID 由来 layout に限る** (§3.1)。
- **項目 6 が固定するのは「閉じた critic invocation が実在し、この campaign・arm・iteration・
  digest・driver 種別に束縛されて一度だけ消費された」ことまでである。**
  **「その決定で次の合成を行った」ことは固定しない** — proposal の receipt hash は自己申告であり、
  legacy critic 由来の proposal に書き写せば通る。加えて、実行主体の真正性 (PATH)、
  外部での並行 legacy query の不在、pair の完全性、WAL と checkpoint の論理世代の一致は
  いずれも証明しない。**変異 15 件が全件 KILLED であることは、登録した各検査が発火することを
  示すのであって、ここに列挙した未閉鎖を埋めるものではない。**

**既知の生存変異 (登録せず、開いていることを記録する):**
- `build_digest()` が別経路で abort payload を出す変異 — 編集面が `orchestrator/critic/digest.py`
  にあり、本 wave の編集面外。
- `orchestrator/campaign/loop.py` や pipeline に `reflux` 値で分岐を足す変異 —
  AST inventory の射程外。なお `orchestrator/campaign/wal.py` は `reflux` key を
  **存在判定のみ**で消費する (trigger campaign の分類)。値を見ず、両アームとも key が存在するため
  アーム非対称を生まない。

## 9. 改訂時点の既知結果台帳 (HARKing 境界)

**本書は前向き事前登録ではない。** 起草時点で、還流 on アーム相当の実走結果が既に存在する。
以下を閲覧したうえで本書を書いた。

|日付|一次資料|内容|扱い|
|---|---|---|---|
|2026-07-12|`docs/archive/worklog-phase3-0702-0713.md`|F 段 (trigger-gating 軸) の実 LLM 駆動 2 iteration。iteration 1 = certified (variant `e1785940172e`、275,614 tps、CV 1.65%)、critic はノイズ内で帰属不能 (+0.27% < floor 3.0%)・decrease 逆方向推奨 → iteration 2 の `prior_critic_reverse=true`。iteration 2 = certified (variant `ca5206c3dac5`、276,472 tps、CV 0.46%)、critic は真の tie・探索停止推奨。両 iteration とも verify legacy+S2 serializable・0 anomalies・auditor pass|**正式標本へ算入しない。** off アームの対照が無く、軸も本書の対象軸と一致するとは限らない|
|2026-07-06|D37|赤 2 本の実走 (fixture trace 注入の半実)。「赤 → 構造化 → critic が読んで形状別の方向を返す」まで実証|**正式標本へ算入しない。** fixture 由来|

**D1082 に基づく分析契約の凍結時点 (§5.1.1) について:** 上表の 2 件のほかに、B-4 の
next synthesis・primary outcome・secondary outcome を新たに生成も閲覧もしていない。
分析用の pilot も実施していない (§5.1.1 のとおり本契約は pilot を持たない)。
**凍結は、本書に基づく B-4 の正式標本より先である。**

したがって本書に基づく成果は、**未知結果に対する confirmatory ではなく、
既知結果に informed された登録追試**として報告する。

## 10. 本書が閉じないこと

- **§5.1 (i) の先行 freeze と人間の指名。** §5.1 (ii) の 4 検査 (候補 driver で切替点を通ること、
  on で赤詳細が出現すること、off で §8 の項目 1・2 が成立すること、on/off の campaign identity が
  分離すること) を、**next synthesis と primary / secondary outcome を生成も閲覧もせずに**行う
  sanctioned CLI は `orchestrator/campaign/p3_b4_wiring_probe.py` として実在する
  (2026-08-27 新設、[T-1769])。outcome を生成しないことは、certified writer authorization・
  loop state 永続化・whiteboard 射影の 3 権威点からの逆到達閉包を遮断集合とし、実 producer 9 本と
  実 CLI 経路を名指しした負例で発火を示す機構で保証する
  (変異 14 件: baseline 緑・KILLED 9・SURVIVED 5・MISMATCH 0)。
  **本 wave の実走は道具の dogfood であり、§5.1 (ii) の採用証拠ではない。**
  残るのは §5.1 (i) の先行 freeze — 候補集合・各 exact command・証拠 path と hash・
  0 件/複数件の決定規則・**記入者とレビュー者** — であり、**人間の指名を含むため AI が確定できない。**
  この先行 freeze を別 commit で固定し、その版に従って (ii) を実測するまで
  **「対象 driver と軸」の欄は埋められず、したがって本書は発効しない。**

  **追記 (2026-09-08、[T-2398]。この現在地はその後変わった。)** §5.1 (i) の先行 freeze は
  §5.1.0 として固定され、(ii) の実測と (iii) の記入も完了している。§5 の
  「対象 driver と軸」欄は `base (silo-backoff-magnitude)` として**記入済み**であり、
  上の「欄は埋められず」と、本節後段の「対象 driver と軸の選定そのもの」は現在の未決事項ではない。
  裏付けは `output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/` の 3 件で、
  各 JSON の sha256 は §5 の値セルに書かれた 3 値と exact 一致し、3 件とも `result.passed` が真、
  `result.pass_rule` が §5.1.0 (d) の凍結値、`run.axis` が §5.1.0 の対と exact 一致する
  (2026-09-08 に親が現物で照合)。§5.1.0 の決定規則 (列挙順 `base → sort → trigger` の先頭 1 件) が
  base を選ぶ。**本書がなお発効前であることは変わらない** — §5 の他の未記入欄と §6 の
  未充足条件が残るためであり、本追記はそれらを 1 つも解消しない。

- **probe が閉じないこと (2026-08-27 に実測して明記、[T-1769])。**
  - **承認経路は deny-only の legacy 台帳を読む。** `make_critic_digest` は
    `require_admitted_campaign` が発行する exact な型しか受け取らないため、この読みは迂回できない
    (迂回は正しさゲートの緩和になる、規律 2)。読むのは legacy campaign 3 件の承認 metadata であって
    B-4 の primary / secondary outcome ではなく、その 3 件の既知性は §9 が既に開示している。
    probe は読んだ台帳の path と sha256 を証拠へ記録し、それ以外の実 campaign artifact を
    1 件も読まないことを ledger で示す。
  - **遮断集合は生成器の完全目録ではない。** 3 権威点のいずれにも到達しない生成器はこの層では
    覆わない。閲覧側は隔離層 (保護領域の read/write 拒否) が受け持つ。
    **閉包は静的に解決できた呼び出し辺の上でだけ導かれるので、解析集合の内側にいても
    呼び出し束縛を静的に解決できない caller はこの層に入らない** (2026-09-01 に実測して明記)。
    ただしその caller が動的に権威点を呼んでも、権威点自身が遮断目録に入るため入口で遮断される。
  - **切替点通過の証拠は composite である。** 候補 driver の CLI 経路への静的到達性と、
    probe から実 `make_critic_digest` を on/off 各 1 回呼んだ観測を併せたものであり、
    **driver が runtime に切替点を通ったことは主張しない。**
  - **trigger の site 射影 identity は、計測契約を発行できる site でしか測れない。**
    login site では production が拒否するため「未測定」と記録する。
  - **publish 直前の違反 ledger 照合 5 か所は到達不能である。** ledger へ追記する箇所は追記の直後に
    必ず例外を送出するため、違反が記録されたまま publish へ到達する状態は起こらない。
    両層同時変異でも生存することを実測した。多重防御として残すが発火する保証には数えない。
  - **任意の native code や同権限 process による interpreter 改変は主張しない。**
- **`expected_claude_model_snapshot` の宣言源と承認主体 (2026-08-29 に実測して明記、[T-2005])。**
  同欄の値は repository の bytes から導出できない。実 CLI 応答の `modelUsage` が返す exact slug は
  走らせる時期で変わり (本 repo の成果物には `claude-opus-5[1m]` と `claude-opus-4-8` の
  両方が実在する)、role frontmatter の `opus` は snapshot slug ではない。
  D998 が定めるとおり本欄は「事前宣言 + 実行時照合」であって予測ではないので、
  値の指名は実験条件の決定である。§5.1 が要求する 4 点 — 結果に依存しない宣言源、承認する人間の
  識別子、宣言の時点、観測 slug が食い違ったときの扱い — は**人間の指名を含むため AI が確定できない。**
  §0 の原子性により、同じセルに入る prompt hash と projection hash も同時に記入できない。
  **したがって 3 driver の projection closure hash は、機構と規範が揃っても値としては未登録である。**
  機構の側 (3 driver 分を要求する行の文法、記入された 3 値すべてを起動器の bootstrap 経路と
  pair 生成点で実走前に live 値と照合する関門、invoke と最終 certification での 3 件再照合) は
  2026-08-29 に閉じた。**閉じたのは機構だけである。** 本欄が埋まるまでに残るのは、
  (i) §5.1 の 4 点を別 commit で固定すること、(ii) model・prompt・3 driver の projection を
  同じセルへ原子的に記入すること、(iii) その版を commit すること、(iv) その版へ束縛した
  admission record を driver ごとに発行することである。**本書の発効にはさらに §5 の他 9 欄と
  §6 の前提条件が要る** — 本項はそれらを一つも充足しない。
- 対象 driver と軸の選定そのもの (§5.1 の手順)。
- 旧登録の B-4 記述を本書が supersede するかどうかのユーザー裁定。
- **critic の決定と proposal 本文の因果的束縛。** 2026-08-26 の必須配線は、閉じた critic
  invocation の実在・束縛・一度きりの消費と、`prior_critic_reverse` が receipt 由来であることまでを
  閉じた。**proposal の receipt hash は自己申告のままであり、legacy critic 由来の proposal に
  書き写せば通る。** 閉じるには決定を入力とする sanctioned な proposal producer と、
  生成後の proposal bytes を含む handoff receipt が要る。
- 広い主張を成立させる実装 — role-facing の型付き結果 projection。
  (**正式経路への必須配線と `prior_critic_reverse` の receipt 束縛は 2026-08-26 に実装した。
  ただし marker 付き sanctioned continuation に限る。**この 2 つが揃っても本書の estimand は
  広がらない — §2.1 の但し書きに従う。)
- **certified の実行主体の trust root。** production factory は `PATH` 上の `claude` を解決するだけで
  binary の identity を認証しない。閉じるには AI が書けない領域の鍵と発行主体が要る。
- **pair の完全性と receipt shopping の遮断** (同一 receipt の再消費だけは閉じた)。
- **WAL と checkpoint の論理世代の束縛。**
- file-drawer の機械強制 (manifest・append-only registry・完全性 consumer)。

  **追記 (2026-09-08、[T-2140]、D1812 (d))。** 上の項目のうち、manifest・append-only registry・
  完全性 consumer の**機構が存在しない**という部分だけが陳腐化している。機構として実在する
  範囲と、それでもこの項目が閉じない理由は §7.2 の同日の追記に書いた。要点は、権威ある
  producer が作成も同定もされておらず、正式 launcher への必須配線も無く、B-4 issuer が
  発行する固定名の成果物が 1 件も存在しないことである。
  **file-drawer の機械強制は、本書が閉じない事項のままである。**
- 第 3 アーム reason-only による「構造化された帰属」と「赤の存在の通知」の弁別。
- 新架構 (機械が導いた制約の適用 on/off) の機構設計・実装と、treatment・負の対照を固定した後の
  別実験・別事前登録案の再提示 (D903)。**本書では事前登録しない。**

---

## 11. floor 欄の発効手続き案と測定計画 (D1383。未裁定の案であり規範ではない)

**本節は D1383 に基づく AI の起草であり、裁定されていない。** 本節のどの記述も、§5 の値セルを
埋める権限、§5.1 の解除条件を緩める効力、実走を許可する効力、コード変更を義務づける効力を
持たない。**誰がどの証拠で floor 欄を発効させるかはユーザーが決める。**
§0 の「本書が定める規範は §5.1 と §7 に置く」は変わらない — 本節は規範ではない。

**本節の読み方。** 各項に *事実* / *既決* / *案* のいずれかを付ける。*事実* は現物から確認した
現在地、*既決* は既に裁定で決まっている事項、*案* はユーザーが採用を裁定した場合に測定手順の
凍結へ書く内容の候補である。**案の側は、採用されるまで何も要求しない。**

### 11.0 なぜ手続きを先に用意するか (現在地)

**事実。** §5.1.1 の分析契約は `floor` を欠落・値域外・非数のとき `floor_domain_error` と判定し、
出力は `analysis_invalid` になる。verdict の全域関数は分岐 1 でこれを **protocol violation** へ写す。
**正規経路で材料レポートが到達できる分析 verdict はこの 1 つだけであり、§7.1 の 4 分類は
実効化していない。**

**事実 (重要な限定)。** この 1 分類は、§5 の floor 欄が `未記入` であることから動的に生じている
のではない。**材料レポートの生成器は本書を読まず、評価器へ無条件に floor 不在を渡す。**
これは D1377 が定めた設計であり、caller の自己申告を凍結値の位置へ入れないための向きである。
**したがって §5 の floor 行を埋めるだけでは正規経路は変わらない。** 権威ある floor 成果物を
検証して評価器へ渡す接続を材料レポート側に作るかどうかは、別の裁定と実装であり、本節は決めない。

**追記 (2026-09-08、[T-2424]。worklog entry 1336 で現在地が変わった。)** 上の段落のうち
「生成器は本書を読まず」「無条件に floor 不在を渡す」の 2 点は、現在の実装を表さない。
`orchestrator/campaign/p3_b4_material_report.py` は本書 §5 を読み、
`resolve_preregistered_authoritative_floor` へ渡して floor を解決したうえで評価器を呼ぶ。
**ただし非 `None` の floor が渡るのは、§5 の floor 欄に検証を通る権威ある成果物 pin が
書かれている場合だけである。** 欄が `未記入` のまま、あるいは resolver が pin を拒否した場合は
fail-closed で従来どおり floor 不在が渡り、分析 verdict は 1 種類のままである。
よって「§5 の floor 行を埋めるだけでは正規経路は変わらない」は、**「有効な pin でない記入では
変わらない」という形でなお真である。** 本追記は §5.1 の解除条件も §6 の前提条件も 1 つも緩めない。

材料レポートは Phase 3 主経路の片翼なので、ここが止まると主経路が止まる。これが floor 欄の
手続きを先に用意する理由である。**ただし floor 欄が埋まっても本書は発効しない。**
§5 の残り 9 欄と §6 の 9 条件が要る (§0、§6)。本節は 10 欄のうち 1 欄分の手続き案にすぎない。

### 11.1 発効手続きの案 (未裁定)

**以下には、既に裁定で決まっている事項と、未裁定の案が混在する。** 各項に *既決* と *案* を
付けて区別する。**案の側は、ユーザーが裁定するまで手続きとして発効しない。**

**誰が。**
*既決 (D1383)*: AI は発効手続きの案と、床値を得るために必要な測定計画を用意する。
**誰がどの証拠で発効させるかはユーザーが決める。AI が既成事実として値を埋めることはしない。**
*案*: ユーザーが少なくとも次の 3 者を、不変の識別子で指名する — 測定実行者、証拠確認者、
§5 記入・commit 担当者。兼務を許すかもユーザーが決める。AI は手順の起草、静的な検査、
機械計算の補助までとし、測定実行者・証拠の承認者・floor 欄の記入者にはならない。
**この役割の排除は D1383 が明文で定めたものではなく、本節の案である。**

**何を根拠に。**

- *案*: 測定前に commit された**測定手順の凍結**。凍結項目は下の割り当て表の候補による。
- *案*: 測定後の create-only 成果物とその sha256。成果物には raw なセッション値、共通参照点、
  各対照対の差、失敗した標本を含む全件、実行順、時刻、環境・source・build・起動コマンドの出所、
  および最終値までの導出過程を含める。**最終値を raw から再計算できることを要件に置く。**
- *既決 (D1060)*: **既存値を根拠にしない。** 3.0% (D19)、stock だけの calibration、
  48 スレッド動作点の calibration は採用根拠にしない。
- *既決 (D1377)*: **caller が渡した値と自由記述の出所を根拠にしない。**
- *案*: **採用裁定を永続的に束縛する。** floor 行を記入する commit の message に、その成果物を
  採用したユーザー裁定を D 番号で書く。値セルには成果物の path と hash しか残らないため、
  この束縛が無いと、後から commit と成果物だけを見て「発効済み」と既成事実化できる。

**どの順で (案)。**

1. 本節を足す commit を作る。この commit は §5 の値セルを変えず、**発効版ではない**。
2. ユーザーが、担当者・採用する証拠・統計関数・下の割り当て表の空欄を裁定する。
3. §5.1 (i)(ii) に従って対象 driver と軸を確定し、実行 site を選ぶ。
4. **同じ site resolver から env_tag を導出する。** これを校正より先に置く理由は、環境別成果物の
   帰属先がここで決まり、後から別 tag の値を混ぜられなくなるためである。
5. その環境で `PerfConfig` を校正し、成果物にする。
6. **結果を見る前に**、測定手順を別 commit で凍結する。
7. 指名された実行者が、凍結どおりに時間窓を分けた複数 campaign を実施する。
   既存成果物へ上書きせず、途中の値を見て標本数や campaign 数を変えない。
8. 証拠確認者が、全予定標本・失敗・hash・環境の一致・再計算可能性・保守側の選択を確認する。
   **確認結果だけでは §5 を変更しない。**
9. ユーザーの採用裁定の後、指名された担当者が floor 行だけを専用 commit で成果物の path と
   hash へ変える。測定手順の凍結 commit と成果物の commit は、その祖先に置く。
10. **この commit 単独では発効しない。** §5 の全欄と §6 の全条件を満たした版を実走前に
    commit して初めて発効し、実走成果物にその commit hash を記録する (§1)。

**凍結項目と決定主体の割り当て (案)。** 案として、**空欄を残したまま凍結 commit を作らない**、
**AI が起草した候補値を無裁定の既定値として凍結へ入れない**、の 2 点を置く。

|凍結項目|決定主体の案|
|---|---|
|対象 driver と軸|**D1266 により記入者・レビュー者とも `thawk105` に固定済み。本節は再裁定しない。** 手続きは §5.1 (i)(ii) に従う|
|実行 site|ユーザー|
|env_tag|site resolver から機械導出 (site 確定後は選択の余地を残さない)|
|校正済み `PerfConfig` の全項目|calibrator が決め、ユーザーが承認|
|対象 protocol・workload・contention セルの集合|ユーザー|
|共通参照点と対照対の厳密な定義|ユーザー|
|admission と単独性の条件|ユーザー (AI は候補を書いてよい)|
|標本数・campaign 数・時間窓の分離|ユーザー|
|統計関数 (分位・信頼水準・許容限界の規則)|ユーザー|
|保守側の最大を取る対象集合|ユーザー|
|成果物の書式と命名|ユーザー|
|欠測・非有限値・環境不一致・競合検出・予定外 retry の扱い|ユーザー|

**追記 (2026-09-07、D1695)。** 上表の「標本数・campaign 数・時間窓の分離」は決定済みである。
値は **1 campaign・1 セルあたり n = 62**、24 時間以上離した 2 campaign で合計 124 とする
(D1641 が n = 59 として確定し、D1695 が 62 へ改めた。理由は §11.2「標本数」の追記)。
上表が割り当てた決定主体は変えない。他の 11 項目についてはここでは何も述べない。

**追記 (2026-09-08、[T-2140]、D1812 (c))。** 上表の 12 項目は採否待ちではない。2026-09-05 の
**D1641 決定 3** が「凍結項目 12 行は §11.2 の案を採る」として各項目の具体値を確定し、
2026-09-07 の D1695 がそのうち標本数を n = 59 から n = 62 へ改めた。**これは本追記による
新規の採否ではなく、既に下りている裁定を本文へ反映する訂正である。**
**上表が割り当てているのは決定主体の案であって、確定した値そのものではない。** 12 項目の値の
正本は D1641 決定 3 の列挙であり、本書はそれを再掲しない。あわせて D1641 決定 1・2 は、担当 3 者
(測定実行者・証拠確認者・§5 記入担当者) をいずれも `thawk105` 名義とし操作を AI 委任とすること、
測定を認可すること、校正済み `PerfConfig` の承認と成果物の採用裁定を同じ委任の下で AI が行うことを
確定している。**上表の決定主体欄のうち承認・採用の主体は、この委任に従って読む。**
なお §11.3 は、担当者の指名・対象集合・統計関数・採用証拠の受理をユーザー手番として列挙したままである。
**本追記はその記述を訂正しない** — D1812 (c) が名指ししたのは §11.1 と §11.2 である。両者の食い違いは
ユーザー裁定へ返してある。
**追記 (2026-09-17、[T-2465]、D1887 / D1936)。** 上の食い違いは決着した。D1887 が担当者の指名と採用証拠の
受理を D1641 決定 1・2 の反映として、D1936 末尾が対象集合と統計関数を D1641 決定 3 の反映として、いずれも
追加授権なしの追記訂正と裁定したので、§11.3 へ同日に追記反映した。本追記は §5.1 の解除条件も §6 の前提条件も
緩めず、測定の開始も §5 の記入も本書の発効も許可しない。
**本追記は §5.1 の解除条件も §6 の前提条件も緩めない。** floor 欄を記入してよいのは、対象動作点で
再実測した床値の artifact path と hash を値として書けるときだけであり、本追記は測定の開始も
§5 の記入も本書の発効も許可しない。

### 11.2 床値を得るための測定計画 (未裁定)

**以下には、現物から確認した事実と、未裁定の案が混在する。** 各項に *事実* と *案* を付けて
区別する。**本節は測定を許可も要求もしない。** 案の側は、ユーザーが裁定するまで発効しない。

**追記 (2026-09-08、[T-2140]、D1812 (c))。** 本節に *案* と書かれた項目のうち、§11.1 の割り当て表
12 項目に対応するものは、2026-09-05 の D1641 決定 3 が既に採用している (標本数は D1695 が
n = 62 へ改めた)。以下に残る *案* の表記は起草時の履歴として読み、**12 項目の採否が現在も
未決であるとは読まない。** これは新規の採否ではなく既裁定の反映である。
**確定していないものは確定していないままである。** 12 項目に対応しない *案* は未決のままであり、
本追記は測定の開始も成果物の採用も本書の発効も許可しない。§11.3 が列挙する残りの手番については
本追記では何も述べない。

**測る量。**
*事実*: §5.1.1 が比べるのは、共通参照点に対する 2 つの相対利得
`gain = throughput / reference_tps - 1` の差 `D = |gain_1 - gain_2|` である。
一方、既存の between-run floor driver が返すのは単一構成の session-median の変動係数である。
独立・同分散という単純なモデルでも差のばらつきは片側のおよそ 1.41 倍になりうる。
*案*: 変動係数を床値へ流用せず、`D` を直接測る。

**対照対の作り方。**
*案*: treatment の差が無い対 (両側が byte 単位で同一の候補) を、独立した 2 つのセッションで測り、
順序を事前に無作為化する。両側は trace-disabled、同じ校正済み `PerfConfig`、同じ env_tag、
同じ admission と単独性の条件で測り、別プロセスの独立セッションとする。

**測定中の競合。**
*事実*: 現行の低水準な測定関数は測定中の競合検査を持たず、既存の between-run floor driver も
セッション開始前の確認しか行わない。既存の s8b floor campaign は
「事前 probe → 測定 → 事後 probe → journal」の形を持つ。
*案*: その形を必須経路として流用し、どちらかの probe が不確定または競合を示した標本を
fail-closed で落とす。**落とした標本を、値を小さくする方向の除外に使わない。**
落ちた数が凍結時の想定を超えたら campaign 不採用か再計画へ倒す。

**「対象動作点」を先に一意にする。**
*事実*: 現行の between-run floor driver は、レコード数 1,000,000 / スレッド 48 / 実行時間 3 秒を
`p2_2` から取り、1 セッション 5 反復、baseline を stock の `silo` と `mocc`、workload を 3 種に
固定している。「対象動作点」という文言のままでは、同じ名前から複数の測定集合が通り、
別々の床値が出る。
*案*: 凍結の前に次をすべて一意に決める — 選定された driver と軸、site と env_tag、
校正済み `PerfConfig` の全項目、workload と contention のセル集合、対照候補と参照 receipt の
決定規則、測定域の外にある将来の variant の扱い。

**標本数。**
*事実*: 分布自由な片側許容限界として標本の最大値を使う場合、95 パーセンタイルを信頼度 95% で
覆うには標本 59 個、99 パーセンタイルなら 299 個が要る。現行前例の 8 個では信頼度がそれぞれ
約 33.7%、約 7.7% にしかならない。
*案*: **8 という前例を根拠に採らない。** 実際の数はユーザーが決め、決めた数とその根拠を凍結へ
書く。**同じ campaign 内の連続した測定を、独立な機会として数えない。**

**追記 (2026-09-07、D1695)。** 実際の数は **1 campaign・1 セルあたり n = 62** に決まった
(2 campaign 合計 124)。**上の *事実* の 59 は書き換えない** — あれは欠測が 1 件も無いときに
95 パーセンタイルを信頼度 95% で覆う最小標本数であり、真である。D1695 が 62 を採ったのは、
D1641 が置いた 5% の欠測許容 (`dropped * 20 <= planned`) を維持する以上、n = 59 では
許容どおり 2 件落ちて 57 件になると被覆が約 94.6% へ下がり、設計が要求する 95% を割るためである。
n = 62 なら許容の上限が 3 件 (62 の 5% = 3.1) になり、59 件が残る。**許容を 0 へ戻す案は採らない**
— 1 件の欠測で window が全損になる。
**この算術がそのまま言えるのは 1 pair の場合だけである。** 5% の判定は campaign 合算であって
pair ごとの閾値ではないので、複数 pair では欠測が 1 つの stratum へ偏りうる。
**「n = 62 なら各 stratum に 59 件残る」「全セルで 95% 被覆が保たれる」とは読まない。**
pair ごとの閾値は足さない (D1697)。残存標本での被覆は対照対 driver も保証していない。

**費用の目安。**
*事実*: 本項は 2026-09-08 に [T-2414] / D1779 で現構成へ書き直した。書き直す前の記述と、そこに
載っていた派生値は下の erratum に残す。**各 campaign で n = 62 を取り、2 campaign 合計で
124 pair-sample** とすると、現行の対照対 driver は 1 pair-sample につき同一候補の独立した
2 つの side session を作り、各 session の中で候補と参照を 1 回ずつ測る。したがって
**1 pair・1 セルあたり 248 side session・496 測定 (候補 248・参照 248)** になる。
反復数は session ではなく測定ごとに掛かる — driver は測定ごとに `reps` を渡し、成果物 header へ
`measurements_per_session` と `reps_per_measurement` を別々に書く。起草時と同じ名目値
1 測定 = 5 反復 × 3 秒を置くと、名目の bench 時間は **7,440 秒 (約 124 分)** になる。
`PerfConfig` は未校正なので、これは実時間の保証ではなく、起草時の数字と比べるための名目値である。
**この数はセルあたり 1 pair を前提にする。** 1 セル・1 campaign が P 個の pair を持つなら、
pair-sample は 124P、side session は 248P、測定は 496P になる。
**(erratum (2026-09-08、[T-2414]、D1779)。書き直す前の派生値を残す。起草時 (n = 59、
2 campaign 合計 118) は候補 236 セッション・3,540 秒、参照 118 セッション・1,770 秒、
合計 5,310 秒だった。D1695 が n = 62 (合計 124) へ改めた後の旧構成は候補 248 セッション・
3,720 秒、参照 124 セッション・1,860 秒、合計 5,580 秒で、どちらも参照点を候補と別セッションで
測る構成に対する条件付きの目安だった。D1699 が候補と参照を 1 つの低水準セッションで測る形へ
設計を変えたため、内訳は「参照分を加算する」形ではなく、**同じ 248 セッションの中身が
1 測定から 2 測定になる組み替え**になった。候補側の 3,720 秒は変わらず、参照側が 1,860 秒から
3,720 秒になる。変わっていないのは n = 62、2 campaign、124 pair-sample、候補側 248 セッションで
あり、変わったのは 1 pair-sample あたりの参照が 1 件から 2 件になったこと、各 session の中身が
1 測定から候補 + 参照の 2 測定になったこと、名目の合計時間である。**書き直す前の本文は、この名目値を
「1 セッション 5 反復 × 3 秒」と session 単位で書いていた。**当時は 1 セッションが 1 測定だったので
同じ値を指すが、現構成では 1 セッションが 2 測定を含むため単位を測定側へ移してある。
本 erratum は §5.1 の解除条件も
§6 の前提条件も緩めず、校正済み `PerfConfig`・floor・総計測予算の記入を代替せず、測定の開始を
許可しない。)**
*案*: セル数を掛けた総額が §5 の総計測予算欄に収まるかを、凍結の前に確かめる。

**保守側の合成。**
*事実*: 全セル・全時間窓の最大が保守側になるのは、対象集合と各セルの上限統計が
**結果を見る前に閉じている**場合に限る。開いたままだと、測った部分集合の最大を、
測っていない対象まで含む最大として扱うことになる。
*案*: 最大を取る対象集合と各セルの上限統計を凍結で先に閉じる。

**値域。**
*事実*: 登録できる `floor` は 0 以上 1 未満の有限値である (§5.1.1)。差 `D` にはこの上界が無い。
*案*: **上限が 1 以上になったら丸めない。**「この動作点では床値を生成できない」と記録し、
動作点か手順の再設計へ戻す。切り詰めて登録すると、判定式が tie を過剰に生む方向へ黙って緩む。

**出力先。**
*事実*: 現行の between-run floor driver の出力名は環境 tag・protocol・スレッド数・workload だけで
決まり、campaign 識別子を含まない。同じ点の 2 度目は create-only で失敗する。
*案*: **既存成果物の削除・上書き・改名で回避しない。** 時間窓ごとに一意な出力先を凍結で先に決め、
確保できなければ測定を始めない。

**実行機構の現在地。**
*事実*: 現行 repo の sanctioned CLI では、上の測定を起動できない。B-4 の正式 launcher には
校正済み `PerfConfig` と対照対の入口が無く、各 driver は自ら「性能比較用の校正ではない」と
宣言する既定設定を使う。既存の between-run floor driver は動作点を定数で持ち、s8b の
floor driver が計算するのは絶対スループット基準の別量である。
*案*: 凍結した `PerfConfig` と閉じたセル集合を読み、対照対と共通参照点を束縛し、`D` とその上限を
再計算できる create-only 成果物へ出す専用の driver か adapter を作る。
**本節はその実装を要求しない。** 作るかどうか、作るならどの変更単位で作るかはユーザーが決める
(D1383 の範囲は案と計画までである)。既存の sanctioned な面だけで要件を満たせないなら、
測定を開始せずユーザー裁定へ戻す。

**erratum (2026-09-07、D1694)。** 上の *事実* は本節の起草時点 (2026-09-02、`e8ffa2ea`) の
記述であり、**現在は偽である。** *案* が名指しした専用 driver は D1453 の裁定を受けて同じ
2026-09-02 に `orchestrator/campaign/floor_pair_driver.py` として main へ着地しており
(`93181d56`)、2026-09-07 には D1641 第 3 項の欠測規則へ適合させてある (`b40414af`)。
したがって D1641 第 4 項が本節を引いて書いた理由文「現行の sanctioned CLI ではこの測定を
起動できない」は、**その裁定日 (2026-09-05) の時点で既に偽だった。** D1694 はこの前提だけを
追記で訂正し、**決定そのもの (欠測規則へ適合させてから測る) の効力は維持する。第 4 項が
命じた driver の「新設」は「適合」と読む。** 当時の記述は書き換えず残す (絶対規律 7)。
**本 erratum が述べるのは driver の実在だけである。** §5 の空欄も §6 の前提条件も 1 つも
免除せず、測定の開始を許可しない。

### 11.3 本節が閉じないこと

- 担当者の指名、対象集合、標本数、統計関数、採用証拠の受理 — いずれもユーザー手番である。
- §11.2 が名指しした専用 driver / adapter を作るかどうかと、その変更単位。
  **追記 (2026-09-07)。** 上の 2 項目のうち 2 点は決着している。**標本数は D1695 で
  n = 62 (1 campaign・1 セルあたり、2 campaign 合計 124) に決まった。専用 driver を作るか
  どうかも決着しており、D1453 の裁定で作られて main に着地済みである** (D1694、§11.2 の
  erratum)。残り (担当者の指名、対象集合、統計関数、採用証拠の受理、driver の変更単位) は
  本節に書いたままユーザー手番である。
  **追記 (2026-09-17、[T-2465]、D1887 / D1936 の反映)。** 上の「残り」のうち 4 点と driver の変更単位は
  決着しており、ユーザー手番ではない。**担当者の指名**は D1641 決定 1 が測定実行者・証拠確認者・§5 記入担当者を
  いずれも `thawk105` 名義とし、操作を AI 委任とした (兼務を許す。証拠確認者は独立検査者ではなく、凍結どおりに
  測られたことの確認責任者)。**対象集合**は D1641 決定 3 が「セル集合 = 選定された driver と軸の 3 workload ×
  §5 に列挙する contention セル」「保守側の最大を取る対象集合 = 凍結したセル集合 × 2 時間窓の全部」と確定し、
  workload 別 3 spec の結果を保守側の最大として 1 つに集約する (D1936 項 7、§5.1 の追補)。**統計関数**は
  同決定 3 が「分布自由の片側許容限界。標本最大値を 95 パーセンタイルの信頼度 95% の上限とする」と確定し、
  標本数は D1695 が 1 campaign・1 セルあたり n = 62 (2 campaign 合計 124) へ改めた (59 を予定標本数として
  復活させない)。**採用証拠の受理**は D1641 決定 2 が「採用裁定 (成果物を §5 へ記入するか) は測定後に AI が
  本委任の下で行い、D として記録する」と確定した — 確定したのは担当と採用の手順であり、個別の成果物が受理済み
  という意味ではない。**driver の変更単位**は D1641 決定 4 の「別の実装 wave」を、D1453 で作られ D1694 の
  erratum が実在を記す既存 driver への「適合」と読む。D1887 は対象集合と統計関数の 2 点が D1641 に覆われて
  いるか未確認としていたが、D1936 末尾が「D1641 決定 3 に記載されているため、追加授権ではなく追記反映とする」と
  閉じた。本追記は上の列挙を書き換えず、決定の効力も変えない。§5 の contention セルの具体列、凍結入力の充足、
  §5.1 の解除条件、§6 の前提条件、測定後の採用裁定は本追記で代替されず、測定の開始も §5 の記入も本書の発効も
  許可しない。
- **材料レポート側の接続。** 現行の生成器は本書を読まず無条件に floor 不在を渡す (D1377)。
  権威ある floor 成果物を検証して評価器へ渡す接続を作るかどうかは、別の裁定と実装である。

  **追記 (2026-09-08、[T-2424]。worklog entry 1336 で現在地が変わった。)** 上の 1 行は
  現在の実装を表さない。材料レポートの生成器は `orchestrator/campaign/p3_b4_material_report.py`
  で本書 §5 を読み、`resolve_preregistered_authoritative_floor` に渡して floor を解決する。
  接続を作るかどうかは決着済みであり、作られている。**ただし解決に成功して非 `None` の floor が
  評価器へ渡るのは、§5 の floor 欄に検証を通る権威ある成果物 pin が書かれている場合だけである。**
  欄が `未記入` のままなら、生成器は従来どおり floor 不在を渡す。したがって
  **この訂正は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、`未記入` を有効な floor と
  見なさない。** 上の項目のうち「接続が未実装」という部分だけが解消済みである。

  **追記 (2026-09-17、D2103 の反映。worklog entry 1595 で現在地が変わった。)** 上の追記が
  書いた「本書 §5 を読み」の読み方が変わった。材料レポート → floor artifact issuer の floor セル読取
  (`resolve_preregistered_authoritative_floor`) は、文書全体を floor 行の prefix で走査する形をやめ、
  `orchestrator/campaign/p3_b4_admission_record.py` の既存 §5 検査から切り出した固定表の解析
  (`## 5.`〜`### 5.1` の一意な見出し境界、fence / HTML comment の除外、12 非空行と exact header、
  10 label の集合一致、不可視文字の拒否) と、責任者行「実行責任者・開始時刻」の 1 セル受理述語 (D2079) を
  通してから、§5 固定表の floor セル 1 つだけを読む。不在と判定するのは strip 後の raw が `未記入` と
  一致する場合だけで、NFKC 異体は拒否される。他欄の sentinel と expectation 行は floor 経路で検査しない
  (現行文書は floor を含む 6 欄が `未記入` のままで、floor は不在)。D1377 が定めた向き (生成器は floor を
  caller から受け取らない) は変わらず、floor は §5 固定表の pin からしか入らない。**したがって上の追記の
  「有効な pin でない記入では変わらない」はなお真であり、加えて、§5 固定表の外に置かれた同名の行や、
  責任者行が `未記入` の文書は、pin の有無にかかわらず floor 経路で拒否される。** 本追記は §5.1 の
  解除条件も §6 の前提条件も 1 つも緩めず、`未記入` を有効な floor と見なさず、測定の開始も §5 の記入も
  本書の発効も許可しない。下の末尾の項が挙げる「材料レポート側の floor 接続が裁定され実装されていること」は
  [T-2424] と D2103 で満たされているが、他の条件 (§5 の全欄、§6 の全条件、発効版の commit、§5.1.1 の
  adapter と consumer) は満たされておらず、§7.1 の 4 分類は実効化していない。
- **floor 欄が埋まっても本書は発効しない。** §5 の残り 9 欄と §6 の 9 条件は 1 つも免除されない。
- **§7.1 の 4 分類が実効化するのは、次がすべて揃ったときである** — floor が発効し、§5 の全欄が
  埋まり、§6 の全条件が満たされ、その版が実走前に commit され、§5.1.1 が要求する adapter と
  consumer が実在し、**かつ材料レポート側の floor 接続が裁定され実装されていること。**
  consumer の実在は必要条件であって十分条件ではない。
