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
|対象 driver と軸|未記入|
|赤 precursor の母集合 (workload・赤形状・初期 proposal)|未記入|
|アームあたり block 数 n と検定単位|n = 201、検定単位 = block|
|primary outcome の演算定義 (純関数)|未記入|
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
- **floor**: `docs/phase3-main-experiment.md` の流用禁止規則に従う。既存の 3.0% (D19) と
  48 スレッド動作点の calibration を**流用しない**。対象動作点で再実測し保守側 (最大) を採る。
- **校正済み `PerfConfig`**: `p3_s4_loop.default_perf()` は自ら「性能比較用 calibration ではない」と
  宣言している (配線規模)。calibrator が決めた値へ差し替えるまで記入しない。
- **総計測予算**: arm ごとに対称とする。失敗した role query と reject も予算を消費する。
  再試行・差替えは禁止。
- **model snapshot / prompt hash / projection hash**: 両アームで同一であることを確認して記入する。
- **env_tag (実測環境)**: 選択した driver と実行 site が確定し、その site の環境契約の exact tag と
  一致することを**同じ site resolver から機械導出して**確認してから記入する。同一 driver でも site に
  よって tag が分かれるため、driver・site・tag の 3 つ組で固定し、環境契約の artifact path と hash、
  確認者を発効版へ併記する。**別 tag の環境で開始した block は削除せず `protocol violation` とする**
  (`判定不能` ではない。事前条件違反であり、差し替えも禁じる)。
- **実行責任者**: 実走前に 1 名を指名し、不変の識別子で記入する。実走後に差し替えない。
  **この欄は計測に依存しないので、計測待ちを空欄の理由にしない。** 指名がないまま実走しない。
- **開始時刻**: timezone 付きの**予定**開始時刻を記入し、「この時刻より前に実走を開始しない」と読む。
  実際の開始時刻は実走成果物側に別途記録し、**本欄を後から実測値へ書き換えない。**

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

- **probe が閉じないこと (2026-08-27 に実測して明記、[T-1769])。**
  - **承認経路は deny-only の legacy 台帳を読む。** `make_critic_digest` は
    `require_admitted_campaign` が発行する exact な型しか受け取らないため、この読みは迂回できない
    (迂回は正しさゲートの緩和になる、規律 2)。読むのは legacy campaign 3 件の承認 metadata であって
    B-4 の primary / secondary outcome ではなく、その 3 件の既知性は §9 が既に開示している。
    probe は読んだ台帳の path と sha256 を証拠へ記録し、それ以外の実 campaign artifact を
    1 件も読まないことを ledger で示す。
  - **遮断集合は生成器の完全目録ではない。** 3 権威点のいずれにも到達しない生成器はこの層では
    覆わない。閲覧側は隔離層 (保護領域の read/write 拒否) が受け持つ。
  - **切替点通過の証拠は composite である。** 候補 driver の CLI 経路への静的到達性と、
    probe から実 `make_critic_digest` を on/off 各 1 回呼んだ観測を併せたものであり、
    **driver が runtime に切替点を通ったことは主張しない。**
  - **trigger の site 射影 identity は、計測契約を発行できる site でしか測れない。**
    login site では production が拒否するため「未測定」と記録する。
  - **publish 直前の違反 ledger 照合 5 か所は到達不能である。** ledger へ追記する箇所は追記の直後に
    必ず例外を送出するため、違反が記録されたまま publish へ到達する状態は起こらない。
    両層同時変異でも生存することを実測した。多重防御として残すが発火する保証には数えない。
  - **任意の native code や同権限 process による interpreter 改変は主張しない。**
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
- 第 3 アーム reason-only による「構造化された帰属」と「赤の存在の通知」の弁別。
- 新架構 (機械が導いた制約の適用 on/off) の機構設計・実装と、treatment・負の対照を固定した後の
  別実験・別事前登録案の再提示 (D903)。**本書では事前登録しない。**
