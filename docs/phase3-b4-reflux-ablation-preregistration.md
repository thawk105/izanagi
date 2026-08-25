# B-4 還流 on/off ablation 事前登録 — 発効前 draft

論文 `docs/paper-story/2026-08-23.md` §8 の **B-4「規律 3 の還流 on/off ablation」**の事前登録である。
主張は「構造化された正しさシグナルが次の合成を改善する」。還流の入口までは実走済みで、改善の実証が無い。

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

- **状態 = 発効前 draft。** §5 の数値欄が埋まり、§6 の前提条件がすべて充足し、
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

広い主張 (correctness feedback 全体の on/off) を名乗るには §6 の前提条件 3 が要る。
**それが未充足のまま広い主張を書くことを本書は禁じる。**

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
- **新架構 (本書の対象外):** 還流の担い手は機械 (失敗から制約を導く) であり critic は還流チャネルでない。
  切替点は「機械が導いた制約を適用するか」へ移る。8c 用の定義は新設される。
  **その機構は現時点で存在しない。**

**本書は段 4 の架構だけを対象とする。** 新架構の還流 ablation は別実験・別事前登録とし、
両者の結果を統合しない。

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

- **対象 driver と軸**: §2.3 の架構択一がユーザー裁定で確定するまで記入しない。
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

## 6. 実走の前提条件 (1 つでも未充足なら実走しない)

1. §5 の全欄が記入済みで、その版が commit されている。
2. §2.3 の架構択一がユーザー裁定で確定している。
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
   **ただし前提条件 3 はこれで完了しない。** 段 4 driver への必須配線は行っておらず
   (legacy の `Agent(subagent_type='critic')` 経路は依然使用可能)、§5 の欄は未記入で、
   その事前 commit も済んでいない。**「機構は用意された。正式経路への採用と §5 の事前 commit は
   未了」が現在地である。**
4. **API 直呼びと `policy_hint` の規律が守られている。** `run_one_iteration()` の戻り値には
   reject 時に `digest`、certified/aborted 時に `records` (WAL payload 一式) が載る。
   sanctioned CLI はこれを表示しないが、Python API を直接呼ぶ controller には見える。
   実走は sanctioned CLI 経路に限り、`policy_hint` は absent か両アーム byte 同一に固定する。
5. **`prior_critic_reverse` の供給規則が確定している。** 同値は proposal JSON から読まれるだけで
   arm・digest・critic invocation receipt と束縛されていない。かつ `check_stop` の
   `reverse-exhausted` を単独で発火させ、次 synthesis の有無を変える。
   本書の primary は paired 1-step (§4 と §5.1) なので停止差は primary に入らないが、
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
- **off アームの遮断は機械的な閂ではない。** §6 の前提条件 3・4 が列挙する経路
  (critic role の Bash、digest CLI、`run_one_iteration` の戻り値、`policy_hint`) は
  いずれもテストで閉じられない。負の対照 (§8) が固定するのは
  **harness が生成する critic digest における loader 非呼出**までである。
  **[T-1697] の閉じた起動形は、この 4 経路のうち専用 route 内の 2 つ
  (critic role の Bash、digest CLI) だけを、その route を通る限りにおいて閉じる。**
  `run_one_iteration` の戻り値と `policy_hint` は開いたままであり、legacy route も開いたままである。
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

- §2.3 の架構択一 (ユーザー裁定待ち)。
- 広い主張を成立させる実装 — 閉じた critic invocation の**正式経路への必須配線**
  (機構自体は [T-1697] で用意した。段 4 driver がそれを要求する配線は未了)、
  role-facing の型付き結果 projection、`prior_critic_reverse` の receipt 束縛。
- file-drawer の機械強制 (manifest・append-only registry・完全性 consumer)。
- 第 3 アーム reason-only による「構造化された帰属」と「赤の存在の通知」の弁別。
- 新架構 (機械が導いた制約の適用 on/off) の還流 ablation。
