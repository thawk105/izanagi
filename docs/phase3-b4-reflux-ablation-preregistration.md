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
|アームあたり block 数 n と検定単位|未記入|
|primary outcome の演算定義 (純関数)|未記入|
|floor (対象動作点で再実測した between-run floor) の artifact パスと hash|未記入|
|校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash|未記入|
|総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限|未記入|
|env_tag (実測環境)|未記入|
|model snapshot / prompt hash / projection hash|未記入|
|実行責任者・開始時刻|未記入|

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
  `--no-build` 経路も §3.1 の切替点を通らない (digest を生成しない) ため probe にならない。
  その条件を満たす sanctioned CLI が無い場合は、用意されるまで
  対象 driver と軸を記入しない。(i) と (ii) は実走開始前に完了させ、実走開始後は差し替えない。**
- **赤 precursor の母集合**: B-4 の出力を見る前に freeze する。赤が出なかった block も
  除外・差替えせず「treatment 未発火」として全件報告する (§7)。
- **n と検定単位**: 検定単位は **block** とする (試行は path-dependent で独立でない)。
  n は B-4 データを含まない凍結済み母集合と事前固定した最小重要効果から検定力を概算して決める。
  **予算上 n を確保できないなら「記述統計に留め有意性を主張しない」と本書に先に宣言してから実走する。**
- **primary outcome**: 純関数として固定する。次をすべて定義してから記入する —
  参照点 (precursor 基準か arm 内前後か)、tie の扱い、欠測の順位、非 certified 同士の順位、
  certified と非 certified の順序、確率優越 A の定義。**secondary (certified 到達までの
  iteration 数・certified 率) は primary 判定に使わない。**
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

したがって本書に基づく成果は、**未知結果に対する confirmatory ではなく、
既知結果に informed された登録追試**として報告する。

## 10. 本書が閉じないこと

- **§5.1 (ii) を満たす非標本 probe。現時点で、その条件を満たす sanctioned CLI は存在しない。**
  build を伴う経路は次の synthesis と outcome を生成するため probe にならず、`--no-build` 経路は
  §3.1 の切替点を通らない。probe は §5.1 (ii) の 4 検査 (候補 driver で切替点を通ること、
  on で赤詳細が出現すること、off で §8 の項目 1・2 が成立すること、on/off の campaign identity が
  分離すること) を、**next synthesis と primary / secondary outcome を生成も閲覧もせずに**
  行えなければならない。§5.1 (i) の先行 freeze (候補集合・exact command・証拠 path と hash・
  0 件/複数件の決定規則・記入者・レビュー者) も依存条件である。
  **これが用意されるまで「対象 driver と軸」の欄は埋められず、したがって本書は発効しない。**
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
