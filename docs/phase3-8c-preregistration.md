# Phase 3 段 8c 正式系列 事前登録 — 発効前 draft

段 8c の正式系列 (holdout H1 / H2 × descriptor on/off/swapped) の事前登録文書である。
事前登録の本体は **git commit した 1 枚の文書**であり、8b が採る承認 record・active pointer 型の
凍結機構は導入しない (D116)。ただし**条件文そのものの改竄を検出するため**、条件契約
(§6 の前提条件・§5 の欄名・規範本文・発効ポリシー) の hash 世代台帳だけを持つ (§6 の
「発効の判定と条件契約の凍結」)。

**発効状態はこの文書に書かれた宣言ではなく、判定器が commit ごとに導出する。**
発効前の版を祖先に持つだけでは、事前登録の効力 (§1) は生じない。

**この文書は 8b 設計を書き換えない。** holdout の条件、arm の定義、correctness gate、
判定基準、crash 時の扱い、探索予算の単位は `docs/phase3-8b-descriptor-design.md` が正本である。
本書はそれらを**再掲せず参照**し、8c 固有の事項 (実行 harness、generation 予算、全件報告の
機械強制、発効手続き) だけを定める。8b が凍結する項目を変えるには同文書 §8 の再凍結 +
ユーザー承認が要り、本書はそれを迂回しない。

**条件 2 (非干渉性) は未解決である。** 現行の条件 2 の証拠契約は、production の sink における
arm binding の単射性を要求するが、**非干渉性を表す field を持たない**。したがって、arm 束縛が
機械的に証明されたことを、非干渉性が成立したことと読んではならない。同条件の充足判定器も
非充足を返し続ける。D911 により証拠契約はこのまま据え置き、改訂は非干渉性の各領域の意味が
確定したあとに**一度だけ**行う。そのとき `DECIDER_VERSION` の bump と次世代 record の発行を
まとめる。本節は限界の明記であり、条件契約 (§5 の欄名、§6 の前提条件、規範本文、発効ポリシー)
を変更しない。

## 0. 表記の規約 (機械検査との自爆回避)

holdout 条件を書くときは 8b 設計と同じく `ycsb_` 前置を外して書く (`rratio=80` のように)。
未既知性の三軸検索は同一ファイル内の canonical 綴り 3 種の conjunction を hit と数えるため、
canonical 綴りで書くと**この文書自身が hit となり**、未既知性検査が fails-closed で落ちる。
本書で canonical 綴りを使ってはならない。

## 1. 事前登録の効力とその限界

- **版の同定**: 実走成果物は測定に使った checkout を併記する (F41 / D59)。
- **仮説が結果より先であること**: 発効版の commit が結果 commit の**祖先**であることによる。
- **その限界 (重要)**: ancestry が証明するのは「その bytes の文書がその時点に存在したこと」だけである。
  数値欄が空の版を祖先に持つだけでは、**結果を見てから数値を埋めた版**を後で commit しても
  ancestry 条件を満たしてしまう。よって本書は次を要求する。
  - 数値欄 (§5) をすべて埋めた版を **実走開始前に** commit する。
  - 実走成果物は、その**発効版の commit hash を記録**する。記録がない実走は事前登録された
    実験として扱わない。
  - **受理の条件は次の両方である** — (i) 記録した commit `C` が測定 HEAD・結果 commit の
    **祖先である**こと、(ii) その `C` **において発効している**こと。ancestry は必要条件であって
    十分条件ではない。未充足のまま測定し、後から不足機構を実装して現在の checkout で発効させても、
    `C` 時点の判定は false のままである (§6 の発効ポリシー)。
  - 発効後の変更は旧版を git 履歴に残したまま新しい commit で行い、変更理由と変更時点を
    本書へ明記する。**結果 commit より後に書かれた変更は事前登録として数えない。**
- **内容 commit と発効 commit を分ける (二段束縛)。** manifest の bytes は commit 識別子の入力で
  あるため、manifest が自分を含む commit の識別子を持つ形は原理的に構成できない。したがって
  本書は次の 2 つを別の識別子として定める (D438 決定 (4))。
  - **内容 commit `P`** (`prereg_content_commit`) — 6 cell manifest の bytes を導入する commit。
    **manifest は `P` の識別子も、manifest 自身の digest も持たない。**
  - **発効 commit `C`** (`prereg_effective_commit`) — `P` の直子であり、発効束縛 record
    (`prereg-effective-binding.v1.json`) だけを導入する commit。この record は
    `prereg_content_commit` と manifest の path・bytes hash を持ち、**`C` 自身の識別子は持たない。**
  - **祖先での代用の禁止は、`C` が `P` の子孫であることではなく「`C` の親集合が exact `{P}`」で
    維持する。** ff-only の取り込みと後続の追記は `C` の親集合を変えないため両立する。
  - 実走成果物 (run-start、terminal report、追記専用 registry) は `P` と `C` を**別の欄**として
    記録する。単一の `prereg commit` 欄で兼ねる形は使わない — 同名識別子が 2 つの意味を持つ。
- **成果物への commit 記録は部分実装である。** 現行 supervisor の terminal report と run-start は
  measurement HEAD を持つ ([T-822] 2026-08-18 実測)。内容 commit と発効 commit を**別の欄**として
  持つ二段束縛は依然として未実装であり、この binding の実装は前提条件 (§6) に含む。

## 2. 主張の型と scope

- **位置づけ**: 8b 設計 §7 の段階 2「generation/search 実験」に対応する。段階 1 の selector 実験
  とは独立であり、selector の成否を本系列の根拠にしない。
- **主張の型は 8b 設計 §1 が正本**である。本書はそれを弱めない。
- **主張しないもの**: headline 性能、他 CC 実装との比較、統計的有意。本登録版に束縛された系列では
  仮説検定を行わず、8b §6 の効果量と全件記述だけを報告する (§4 の「標本設計」)。
  YCSB A/B/C の配線 pilot は operational であり、成功しても本系列へ昇格させない。
  この非昇格は pilot の成否と無関係であり、pilot の trial id・結果・材料を本系列の
  6 cell へ混入させない。
- **generation 予算 (裁定済み)**: 本系列は全 cell を `G=2` で実行する (§4)。
  `G=1` の結果は「ワークロード特化合成」の証拠に数えない。この点は
  T-244 のユーザー裁定で確定しており、budget=1 を根拠に本系列の主張を立てることは、
  裁定の有無に関わらず本書が禁じる。承認上限そのものの正本は §4 とする。

## 3. holdout・arm・correctness gate・判定基準・停止規則

いずれも **`docs/phase3-8b-descriptor-design.md` が正本**である。

下の表の左 2 列は**正本の所在を指すポインタであり、内容の定義ではない**。
条件・列名・成立条件・判定不能条件は必ず 8b 側を読むこと。8b が再凍結された場合、
本表の要約語が古くなっても**8b が勝つ**。右列だけが本書の定めである。

|項目|正本|8c 固有の補足|
|---|---|---|
|holdout の条件と未既知性の確認手続き|8b §3|実走開始前に同手続きを再実行し、証跡 (a)〜(e) を §5 へ記入する|
|on / off / swapped の arm と derangement|8b §4|8c では descriptor は planner / coder への入力である。arm が選ぶ実入力 bytes から content digest と arm binding digest を導き、descriptor・campaign identity・proposal bytes/path・invocation namespace・run-start・terminal report・provider payload の 7 sink がこれを消費する ([T-1311])。arm 名を identifier へ書き足すだけの形は採らない (§6 の前提条件 2)|
|correctness gate (legacy + S2)、build 分離|8b §5.2 / CLAUDE.md 絶対規律 1・2|8c の diff quarantine と禁止識別子 gate は driver 側を authoritative path とする。supervisor 側 preview を判定根拠にしない|
|判定基準の表|8b §6 (§10 が 2026-08-18 に条件 3 と結論を上書き)|本書で列・成立条件・判定不能条件を書き換えない|
|crash 時の扱い|8b §10.5 (事前割当 attempt registry。§9 項 8 の再走全拒否を上書き)|8c supervisor の現行 state machine はこれに従っていない (cell 単位の停止 + 新 trial id での再走)。整合は §6 の前提条件 4|
|探索予算の第一単位 (累積ベンチ実時間)|8b §5.2|generation 予算は 8c 固有として §4 に置く。generation cap は bench 秒予算の代替にならない|

## 4. 8c 固有の事項

- **generation 予算**: 全 arm 同一とし、全 cell を正確に `G=2` とする。性能による早期停止、
  `G=1` への短縮、`G>=3` への延長のいずれも認めない。generation cap は
  累積ベンチ実時間予算の代替ではない。承認上限は 3 入口 (CLI・`run_trial()`・`_run_workload()`) で
  機械強制する。**起動側の既定値は `G=2` ではないため、本系列の投入は世代数を明示的に
  指定する形でのみ行う** (§7 の起動形)。`G=2` を宣言だけで満たしたと見なさない。
- **role が真の workload を識別できないこと (非干渉性)**: role へ渡す payload と、provider へ
  実際に送る bytes は、**真の holdout を跨いで byte 同一**でなければならない (`off` arm)。
  これは payload の key 集合から作業種別名を除くことでは満たされない — 値・識別子・path・
  binding digest・whiteboard・baseline・designated source context・provider envelope の
  いずれからも真の対象を復元できず、対象間を安定に区別するラベルにもならないことを要求する。
  比較対象は次の 3 領域へ分解し、**領域ごとに個別に規定する**。(i) role が受け取る最終的な
  入力 bytes — 例外なしで byte 同一。(ii) provider へ送る request の本体 — 例外なしで byte 同一。
  (iii) role からも provider の応答からも不可視な transport の metadata — 比較対象外とするが、
  除外する field を事前登録に**列挙**し、それが対象別のラベルになりえない根拠を書く。
  列挙されていない field を除外根拠なしに (iii) へ分類してはならない。
  この性質が破れている間、6 cell の on/off 差と swapped 追従を descriptor 効果として解釈しない。
  **本書の発効時点でこの性質は成立していない** — role payload の閉じた key 集合が作業種別名を
  含み、descriptor binding の digest が真の holdout と arm から導出される。是正は §6 の
  前提条件 2 に含め、充足するまで本系列を起動しない。
- **世代間で運んでよいものの閉じた集合**: 次の 3 群だけを次世代 role 入力へ運ぶ。
  1. workload ごとに世代ループ前に生成した descriptor とその binding。同じ bytes を全世代で用い、
     前世代の結果で更新しない。
  2. abstract whiteboard。過去世代分のみを狭義単調順で運ぶ。
  3. critic の第二層射影。critic の自由文 (attribution / recommend / avoid) と
     勝ち筋の値そのものは運ばない。診断値は critic の主張ではなく supervisor が
     実測 metrics から機械的に再構築する。
- **還流の情報量 (「閉じている」と書かない理由)**: 上の閉包は**キー集合の閉包であって
  情報量の遮断ではない**。`G=2` で次世代へ渡る結果依存チャネルは、whiteboard の離散状態、
  真偽 2 値、および浮動小数の診断値からなる。診断値を倍精度とみなすと合計は数百 bit 規模になる。
  さらに勝ち筋の値は第二層射影の直接値からは落ちるが、critic の入力には渡るため、
  真偽 2 値を介して次世代へ間接的に伝播しうる。本書は「還流を遮断した」とは主張せず、
  **運ぶチャネルの種別と、それが結果依存であること**を登録する。
  実走成果物は、この 3 群以外が世代を跨いだ形跡が無いことを検査結果として報告する。
- **標本設計**: 事前列挙した 6 cell を報告単位とし、欠測 cell を補完・除外しない。
  **再走は 8b §10.5 の事前割当 attempt registry の範囲だけで許す** — 落ちた構成の同じ反復に
  ついてのみ次の事前割当 slot を消費し、無傷の構成と成功済みの観測値を巻き込まない。
  **本登録版では仮説検定・p 値・統計的有意を用いず**、8b §6 の効果量と全件記述で報告する。
  **検定を加える改訂には、8b §10.2 の数値パラメータの確定、8b §8 の再凍結、ユーザー承認、
  および結果を見る前に commit された新しい本書の版がすべて要る。**
  これらを欠く改訂を当該結果の事前登録として数えない。
- **報告母集団は 6 cell に縮約しない**: 6 cell は報告の**単位**であって母集団ではない。
  全件報告の母集団は 8b §3.3 が凍結する範囲 (全 holdout × 全 arm × 全 variant × 全試行の行、
  全 attempt、全 reject、全 screen 棄却、提案 universe) であり、本書はこれを狭めない。
  成功した提案だけを 6 cell へ集約して失敗・棄却・retry 消費・欠測を落とす報告を作らない。
- **乱数と標本順序の固定**: `master_seed` は結果を見る前に一度だけ選び再抽選しない。
  ただし **seed 単独では標本を束縛しない。** schedule generator の版、生成済み schedule の bytes、
  arm 順序を同時に固定して初めて標本が定まるため、§5 の `master_seed` 欄は
  それらを束縛する機構 (§6 の前提条件 5) が満たされる時点で、同じ改訂単位で記入する。
- **cell 数**: 2 holdout × 3 arm = 6。全 cell を実走前に manifest として列挙する (§6 の前提条件 3)。
- **停止**: 固定世代数で停止する。性能目標による早期停止を置かない
  (Best-of-N と選択的報告になるため)。role 応答の schema 違反は再試行しない。
- **wall budget**: `--max-wall-seconds` は hard wall ではない (時刻検査は workload と generation の
  先頭だけ)。予算の強制手段として使わず、予算判定は累積秒の台帳で行う。
- **arm の outcome 単位**: generation/search 実験で 1 arm の outcome とするのは
  **`G=2` の最終世代の canonical variant** である (2026-08-27 のユーザー裁定 D1066。正本は
  `docs/phase3-8b-descriptor-design.md` の同裁定による再凍結節であり、判定 3 条件の読み替えも
  そこが定める。本書で条件の列・成立条件・判定不能条件を書き換えない)。8c 固有の補足は次の 2 点である。
  (i) 最終世代は世代番号の列が厳密に `[1, 2]` であることを実走成果物で確認したうえで採り、
  列が欠落・重複・順序不正の cell は補完せず判定不能として報告する。
  (ii) **outcome 単位は報告母集団ではない。** 全 proposal・全 attempt・全 reject・全 screen 棄却は
  上の「報告母集団は 6 cell に縮約しない」がそのまま支配する。outcome 単位を理由に
  提案 universe の行を落とす報告を作らない。

### §5 の記入規約と欄別の解除条件 (規範。§5 の値セルには書かない)

**この規約を §5 の値セル側へ書いてはならない。** §5 の値は凍結対象ではないため、
そこへ置いた解除条件は次世代の条件契約なしに緩められる。規範にする文言は本節に置く。

- **記入の形式**: 記入済みの欄は、単一の code span 内に収まる canonical JSON でなければならない。
  未記入の欄は placeholder 語そのものだけを置く。**説明文・条件・空でない container を
  値セルへ書いてはならない** — 前者は不正、後者は「記入済み」と判定され、
  未確定のまま §5 の関門を通す。
- **累積ベンチ実時間の上限**: 実 consumer (§6 の前提条件 6) と、正式 workload の事前コスト計画が
  揃うまで記入しない。arm ごとの上限は対称とし、holdout ごとの上限の和が総上限に一致する形で、
  結果を見る前に固定する。
- **env_tag**: 正式系列の実行 site、環境契約、schedule、実行責任者が確定した時点で記入する。
  対象別 floor の再実測は解除条件ではない (8b §10 が床値を判定の基礎から外した)。
- **反復単位対比の判定パラメータ**: 8b §10.2 の解除条件がすべて成立するまで記入しない。
  値は同節の制約 (`n` は 2 以上の整数、下限は有限の正、上限は有限の非負、単位と向きを同時固定) を
  満たさなければならず、満たさない値は本書を未発効へ倒す。**本書の発効判定は値の型・単位・範囲を
  検証しない**ため、この制約の現在の担保は欄が空であることだけである。したがって同欄を記入して
  よいのは、それらを機械検証する consumer が実在するときに限る。
- **master_seed**: schedule generator の版・schedule の bytes・arm 順序を束縛する機構
  (§6 の前提条件 5) と同じ改訂単位で記入する。seed だけを先に固定しない。
- **検定 4 点**: 本登録版は仮説検定を行わない。再開条件は本節「標本設計」に従う。
  **§5 の当該値セルに残る `reopen_requires` / `reporting` は非権威である** — 値セルは凍結範囲外で
  あり世代 record に記録されないため、再開条件と報告義務の正本は本節だけとする。値セルの記述が
  本節と食い違う場合は本節が勝つ。値の是正は、正式記入を行う次の改訂で同時に行う。
- **未既知性再確認の証跡**: 8b §3.1 の手続を**実走開始の直前に**再実行して記入する。
  先に記入して実走まで持ち越さない。**証跡は自己参照してはならない** — 検索式の canonical 綴りを
  本書または検索対象 tree 内の追跡ファイルへ書くと、その記述自身が三軸の一致となって
  手続が fails-closed で落ちる。同時に、検索対象 tree の外へ式を置くと結果後に差し替えられる。
  したがって式は**検索対象から除外された追跡パス**に置き、本書には
  そのパス・bytes hash・検索対象 dir 一覧・一致 0 件の出力 hash・positive control の hit 数・
  確認者だけを記入する。
- **swapped 対応表**: 8b §4 により対応表は実走者とエージェントへ非公開である。
  人間の管理下で排他的に作成した bytes と時刻を得たうえで、hash と時刻だけを記入する。
- **6 cell manifest**: arm binding (§6 の前提条件 2) と registry (同 3・同 4)、および §1 の
  二段束縛を実際に消費する起動・registry・受入の配線が揃うまで記入しない。契約と規範本文が
  二段束縛の形を取ったことだけでは解除しない。8b §10.5 の事前割当 slot を消費し、
  観測値の差し替えと第二 registry を拒否する consumer も解除条件に含む。
- **実行責任者・開始時刻**: 正式投入の枠と責任者が決まった時点で、開始前の時刻を固定する。

## 5. 実走前に数値で埋める欄 (空欄のまま実走しない)

|欄|値|
|---|---|
|累積ベンチ実時間の総上限と arm ごと・holdout ごとの上限|未記入|
|env_tag (実測環境)|未記入|
|反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)|未記入|
|master_seed|未記入|
|検定 4 点 (n / 検定単位 / 検定力 / 総予算)|`{"mode":"no_hypothesis_test","n":"not_applicable","power":"not_applicable","reopen_requires":["floor_remeasurement","8b_refreeze_and_user_approval","new_pre_run_8c_revision"],"reporting":["effect_sizes_per_8b_section_6","all_predeclared_cells"],"test_unit":"not_applicable","total_budget":"not_applicable"}`|
|未既知性再確認の証跡 (a) 検索対象 dir 一覧 / (b) 検索式 / (c) 一致 0 件の出力 hash / (d) positive control の hit 数 / (e) 確認者|未記入|
|swapped 対応表の固定日時と bytes hash|未記入|
|実走前に確定する 6 cell manifest (trial id、arm、holdout、campaign id)|未記入|
|実行責任者・開始時刻|未記入|

## 6. 実走の前提条件 (未充足のものが 1 つでもあれば実走しない)

1. **H1 / H2 の workload 定義**と、1m records / 48 threads の規模が 8c supervisor に実装されている。
   現行の `WORKLOADS` は rr50 / rr95 / rr100 の 3 点だけで、records と threads も
   `_campaign_for` / `_perf_for` / `_descriptor_for` に 100k / 4 で hard-code されている。
2. **off / swapped arm** が実装され、arm が journal・report・campaign ID・proposal file 名・
   invocation ID の識別子に入っている。あわせて §4 の非干渉性 — `off` の role payload と
   provider へ送る bytes が真の holdout を跨いで byte 同一であること — が成立している。
   **識別子に arm 名を書き足すだけでは足りない。** arm が選ぶ実入力 bytes から content digest を
   導き、その digest を上記 sink が消費していることを要求する。[T-1311] が二層 digest
   (content digest と domain 分離した arm binding digest) と同一 holdout 内 pairwise 非同一検査を
   入れ、7 sink が同じ digest を消費する形にした。**本条件は 2026-08-18 時点で
   機械検査対象である** (証拠契約 C02)。ただし C02 の評価器の終端は現在も
   「機械検査可能な充足証明が無い」であり、C10 だけを開いた現行の充足可能集合に C02 は含まれない。
3. **実走前の 6 cell manifest** と、それに対する append-only の trial registry が存在し、
   manifest 外の trial を結果へ混入させず manifest 内の trial を黙って落とさない。
   manifest の bytes は内容 commit `P` が導入し、発効束縛 record が `P` と manifest の
   bytes hash を指す (§1 の二段束縛)。registry は内容 commit と発効 commit を別の欄で持ち、
   manifest の cell 集合との完全一致を欠落・余剰の両方向で拒否する。
4. **crash 時の扱い**が 8b §10.5 の事前割当 attempt registry に整合している。すなわち
   freeze 全体の全 (holdout, 構成, 反復, attempt) slot が最初の観測前に閉じた集合として
   割り当てられ、追記専用 registry へ束縛されている。落ちた構成の同じ反復についてのみ次の
   事前割当 slot を消費でき、slot の後出し追加・成績を見た後の再走選択・観測済み値の差し替え・
   成功済み構成の再測定を拒否する。再走を許す失敗理由は閉じた集合であり、信頼側が当該 attempt の
   性能出力を読める前に確定する。freeze ごとに master registry root は 1 つだけで、slot は
   schedule 行・run-start 受領証・process identity・raw output hash・terminal status へ
   一対一に束縛される。割当の枯渇は当該対比を判定不能にする。
5. **schedule・master seed・arm 順序**が実走前に生成・固定され、全 arm が同一の search space と
   同一の開始状態から出発することが機械的に保証されている。
6. **累積ベンチ実時間の予算**に実 consumer があり、予算不足時に未実施 arm を**対称に**判定不能へ
   倒す停止が実装されている。値の欄 (§5) だけを埋めて consumer を作らない形は、
   8b が拒否する恒真保証である。
7. **反復単位対比の判定パラメータ**が H1 / H2 について §5 に記入され、manifest の schedule 行が
   持つ反復添字と observations 側の schedule 添字から**完全 block** を復元でき、
   全 cell の観測反復集合が §5 に登録した `n` と exact に一致する。さらに、
   対差の有限な平均と有限な標本 SD だけを主量として 8b §6 の 3 条件を計算する judge と、
   `descriptive_only` の順位表・三値 `official_status` を持つ公式性能表 (この 2 つが性能主張の
   二層である)・独立した第三の表である選択評価表の**計 3 表**を分離して 6 セル分を出力する生成が
   実装されている (現行 supervisor は成功判定を計算しない)。あわせて、§5 の判定パラメータの
   型・有限性・符号・単位・向きを検査する validator が production 経路から到達可能でなければ
   本条件を充足しない。**床値 artifact は本条件の入力にしない。**
8. **内容 commit・発効 commit・measurement HEAD の三者束縛**が実走成果物に焼かれ、機械検査できる。
   run-start・terminal report・registry のいずれもが内容 commit と発効 commit を**別の欄**で持ち、
   発効 commit の親集合が内容 commit ただ 1 つに一致すること、発効束縛 record の digest が
   内容 commit 側 manifest の bytes に一致すること、発効 commit が measurement HEAD の
   祖先であることを、いずれも歴史 bytes の再読で確かめる。**発効 commit の祖先を
   発効 commit の代用にしない。**
9. **層3 材料レポートの生成と検査**が本系列の acceptance の必須経路に配線されている
   (現状は任意実行の CLI)。
10. **proposal / raw response / provider envelope / build 成果物 / bench 結果**と
    supervisor / campaign WAL の cross-binding があり、正式 proof chain の authority が
    決まっている (現状 `output/autonomous-trials/` は「正式 proof chain ではない」)。
    本条件の機械的な充足が確立するのは、commit 内 source に対する**静的な readiness**である。
    verifier module に単一定義の `verify_s8c_cross_binding` と `read_and_verify_bytes` があり、全必須 field 名の
    live な出現と authoritative reader の live な exact call が存在し、`assert_trial_registry_acceptance` から
    契約 path 上の verifier への live な exact call が到達可能で、その call が catch-and-continue で
    握り潰されない場合に限る。
    この充足は次を確立しない。

    - 実行時の再束縛 (`globals()[...]` 代入、module 属性代入、置換デコレータ) が無いこと。
    - 定数でない述語による、意味的に常に偽の guard が無いこと。
    - 呼び出しの結果が検査へ実効的に寄与したこと。
    - 呼び出しが `getattr` や高階関数を経由しないこと。これらを経由する実装は閉じた検査対象の
      構文部分集合に入らず、本条件を充足しない。
    - 必須 field 名が authoritative reader の引数へ実際に束縛されること。検査が要求するのは
      live な位置への field 名の出現までである。
    - reader が実際に bytes を読み digest を照合すること。検査が拒否するのは、非 docstring の
      `pass` / `...` だけからなる本体までである。

    本番 verifier が空でないことは `orchestrator/tests/test_autonomous_trial_completeness.py` の実走回帰検査
    (全 field 束縛の正例と各 field を破壊した拒否) が担う。この実走回帰検査は C10 の充足証拠ではない。
11. **generation 予算に関するユーザー裁定** (§2 の限界) が済んでおり、承認上限の定数、
    3 入口 (CLI・`run_trial()`・`_run_workload()`) の予算 validator、および世代間で運ぶものを
    固定 key 集合へ閉じる第二層射影とその production 配線が、いずれも commit された
    consumer 経路として実在する。**禁止の裁定それ自体は補助証拠にすぎない。**
    これらの機構が強制するのは承認**上限**であって世代の下限ではない — 各 cell を正確に
    `G=2` で起動することは §4 と §7 が定める起動形の責務である (D438 決定 (2)(3))。
12. **計測環境の allocation binding** が campaign launch 前に消費されている。すなわち
    予約 record を読む consumer と、現在の PBS job ID・boot ID・予約期限までの残時間を
    照合する consumer が、8c supervisor の起動経路から到達可能である
    (Pegasus の場合は環境専用 runbook に従う)。**本条件は単一 allocation / node / process での
    完遂も、resume 経路の拒否も要求しない** — 第 4 世代でその要求を落とした (下記 衝突 (e))。
    現行 (2026-08-17) の実装には両 consumer が実在するが、8c 起動経路からの到達が無いため
    本条件は未充足である。予約 record の parse は job ID・boot ID・期限のほかに
    要求時間・scheduler 開始時刻・host・script hash・nonce も要求するが、これらは
    record 読取の依存であって本条件が証明する binding ではない。

本書は事前登録の**内容**を確定するものであり、それ自体は実走の開始を意味しない。
充足状態は下記の判定器が commit ごとに導出する。この静的な文は判定の根拠ではない。

### 発効の判定と条件契約の凍結

**発効は宣言物ではなく導出値である。** ある commit `C` について次がすべて成り立つとき、
かつそのときに限り、本書は `C` において発効している。

- 条件契約の凍結が `C` の履歴で妥当である (下記「凍結される範囲」と「改訂手続き」)。
- §5 の全欄が記入済みである。記入済みとは、値が単一の code span 内の canonical JSON であり、
  placeholder (`未記入` とその変種)・`null`・空文字列・空 container のいずれでもないことをいう。
  欄ごとの型・単位・範囲の検証は本手続きの対象外である。
- §6 の前提条件 1〜12 のそれぞれについて、機械証拠が充足を示す。

判定は `orchestrator/campaign/s8c_preregistration.py` が `C` 時点の git blob だけから再計算する。
**都度の承認コマンド・承認 record・active pointer は要求しない** ([T-327] ユーザー裁定)。
1 つでも欠ければ未発効であり、判定未実施・証拠未定義・評価エラーも未発効として扱う (fail-closed)。

**凍結される範囲 (= 条件契約)**: §1〜§4・§6・§7 の規範本文、§5 の**欄名**集合、本ブロック、
および証拠契約 `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の意味内容。
§5 の**値**は記入されるため凍結対象ではない (値の束縛は実走 manifest 側の責務である)。

**改訂手続き**: 凍結範囲を変更するときは、同じ commit で `output/s8c-preregistration/condition-freeze/`
へ次世代の record (`condition-freeze.v1.gN.json` 形式、N は連番) を追加する。世代 record は
直前世代の bytes hash・変更理由・**裁定の参照** (`docs/decisions.md` の決定見出し) を持つ。
新たに発行する世代 record は schema v2 とし、判定器の版 (`DECIDER_VERSION`) を持つ。既存の
schema v1 record は版を持たない legacy として改変せずに残す。判定器・評価器・射影のいずれかで
受理集合・拒否理由・射影された判定入力の意味を変える変更は、bytes 差の有無に関わらず
`DECIDER_VERSION` を bump し、その版を持つ新世代の record を発行しなければならない。整形など
意味が変わらない変更では bump しない。版の一致検査が止めるのは、明示的に bump したあとで
古い版の record を使い続けることだけであり、bump の忘れは機械検出しない (D458)。
`SATISFIABLE_CONDITION_IDS` へ条件 id を追加するには、次の 3 要件をすべて満たさなければならない。

- **(a) 充足証明**: 当該 §6 条件と証拠契約の `required_evidence` / `consumer_requirement` を評価器が
  commit blob 上で検査し、実 repository と実体を持つ正例 fixture の双方で `SATISFIED` を返す。
  併せて、その証明が確立しない事項を当該条件本文へ列挙する。
  この充足証明に用いる証拠は静的解析に限らず、実行可能な証拠を含めてよい (D1386)。これは証拠の種類を
  増やす許可であって、(a)〜(c) のどの要求も置き換えない。
- **(b) 負例**: 登録済み `negative_control_id` の変異を含む負例を、同じ test の中で正例の
  `SATISFIED` と対にし、変異後は条件別 reason で非充足を返す。
- **(c) 世代更新記録**: `DECIDER_VERSION` の bump と次世代 record を同じ commit に入れる。
  record の `ruling_reference` が指す決定は、その commit より前に台帳へ着地していなければならない
  (D439)。着地していなければ、決定だけを先に land する wave と、世代記録・契約改訂・境界テストを
  同じ commit で land する wave に分ける。

今回この手続きで追加するのは C10 だけである。他の 11 id は、許可外の `SATISFIED` を `ERROR` へ
倒す既存の関門で守られたまま残る。この手続きのための新しい機械 gate は追加しない。
無記録の変更、記録のない差し戻し、
世代を伴わない条件文の変更、世代だけを増やす空改訂は機械検査で赤になる。改訂は事前登録の改訂で
あり、結果を見た後の改訂を当該結果の事前登録として数えない (§1)。8b が凍結する事項を変える場合は
8b §8 の再凍結 + ユーザー承認を別途要する — 本手続きはそれを迂回しない。

**現在地 (重要)。** 機械検査対象は 10 条件
(1・2・4・5・6・7・9・10・11・12) であり、充足可能集合は exact `{"C10"}` である。
C10 は上記の静的 readiness を満たす実 repository と実体ある正例 fixture に
`SATISFIED / cross-binding-readiness-satisfied` を返す。他の 11 条件はすべて非充足であり、
§5 の未記入欄も残る。発効は 12 条件すべての `SATISFIED` を要求する連言なので `false` のままである。

履歴上、第 3 世代 (D438 決定 (1)) は評価器が実在した 6 条件 (1・4・9・10・11・12) だけを
機械検査対象とし、当該 6 条件を評価器へ dispatch 可能にした。2026-08-18 の [T-822] 改訂は
条件 2 を加えて 7 条件とし、判定器の版を `s8c-decider/v3` へ上げた。当時の 7 評価器には
充足を返す経路がなく、評価器を持たない 5 条件は機械検査対象外だった。
同改訂で、許可外の条件へ評価器が充足を返した場合に実行時へ fail-closed で落とす関門を足した
(それ以前は充足可能集合が宣言されるだけで dispatch 後に照合されていなかった)。
dispatch された条件が返す理由は一様ではない — 登録済みの負の対照が壊す形については条件別の
不充足を返すが、証拠 blob そのものが存在しない場合は不充足ではなく別の評価不能理由になる。
いずれも非充足であり、この区別を充足側へ倒す根拠に使ってはならない。したがって §6 の 12 機構を
すべて実装し §5 を埋めても、**残る 11 条件の充足判定器を実装しない限り本書は発効しない**。
残る 11 条件について、条件ごとの充足判定器 (production consumer を実証するもの) の実装は
後続タスクである。

**2026-08-18 改訂で生じた、条件本文と証拠契約のずれ (第 6 世代)。** 本改訂は条件 4 と条件 7 の
**規範本文だけ**を変え、証拠契約 `s8c_preregistration_evidence_contract.v1.json` と条件別評価器を
変更していない。したがって条件 4 の機械証拠は依然として「実験全体を判定不能にし再走を禁じる」
経路を要求し、条件 7 の機械証拠は依然として床値 artifact を要求する。**両条件は引き続き非充足で
あり、本改訂で受理集合は 1 bit も広がらない。** 証拠契約・評価器・負の対照を新しい規範へ追随させる
wave は、受理意味を変えるため `DECIDER_VERSION` を bump し、その版を持つ次世代 record を発行
しなければならない (D458)。追随が済むまで、条件 4 / 7 の本文が新しいことを充足の根拠に使っては
ならない。

**2026-08-19 [T-1355] 改訂で条件 7 の証拠契約・評価器が規範本文へ追随した (第 8 世代)。**
条件 7 の証拠契約は `machine_checkable` を true へ改め、評価器 `_evaluate_c07` を
`_MACHINE_EVALUATORS` へ登録し、負の対照 `nc_c07_floor_or_result_cell_removed` を有効化した。
**条件 4 の証拠契約・評価器は本改訂の対象外であり、上記 2026-08-18 時点の記述のとおり変更して
いない。** 条件 7 は追随後も、床値・ratified freeze 参照・judge 条件 3 種を満たす repo 状態が
現時点で存在しないため充足を返さない。この改訂時点では `SATISFIABLE_CONDITION_IDS` は空集合で、
いずれかの評価器が誤って充足を返しても実行時に不充足へ倒す関門が働いていた。
現在は D1026 に従って C10 だけが充足可能集合へ追加され、他の 11 条件には同じ関門が働く。
**したがって当時の改訂では受理集合は 1 bit も広がらなかった。** 証拠契約・評価器を新しい規範へ追随
させる本改訂は受理・拒否理由の意味を変えるため、`DECIDER_VERSION` を `s8c-decider/v4` へ bump し
第 8 世代 record を発行した (D458)。裁定本文 digest と 8b bytes の非束縛 (下記) はいずれも
本改訂では是正せず現状維持とした — 理由は D458 の粗い provenance 方針との整合、および
本 wave 自身の裁定は fold まで `## D<N>.` 見出しを持たず record の `ruling_reference` から
構造的に参照できないため (下記「世代 record の裁定参照の限界」と同型)。

**本改訂の発効は仕様だけを対象とし、測定を認可しない (epoch 境界)。** 第 6 世代 record と
8b §10 が揃っても、判定器・証拠契約・attempt registry・結果 judge が追随するまで本系列は
起動しない。追随前に走った run は legacy・exploratory であり、後から formal へ昇格・再解釈・
混合しない。最終判定層の現用実装は依然として旧条件 3 (床値超) と scale gate を使う。

**世代 record の裁定参照順序。** 世代 record は単一の `ruling_reference` を持ち、検査は record を
導入する commit 時点の `docs/decisions.md` に当該決定見出しが存在することを要求する。D439 により、
参照先の決定は record 導入 commit より前に台帳へ land 済みでなければならない。未着地の決定を参照する
必要がある場合は、決定だけを先に land し、その後の wave で世代 record・契約改訂・境界テストを
同一 commit に入れる。第 6 世代が D496 を参照した説明は D439 確立前の履歴であり、現行手続きの
先例にしない。検査が見出しの存在だけを見て本文 digest や条件単位の対応を束縛しない限界は残る。

**世代 record は 8b の bytes を束縛しない。** record が照合するのは本書と証拠契約だけであり、
本改訂が依存する 8b §10 の内容は含まれない。したがって record 生成後に 8b を書き換えても record は
stale にならない。本改訂では両文書を確定してから record を 1 度だけ生成する運用でこれを補うが、
それは機械閉包の代替ではない。

この改訂の実利は受理側にはなく、**条件別の負の対照が初めて拒否能力を持つ**ことにある。
契約が「機械証拠を定義していない」と記す限り、評価器は呼ばれず、対照の期待値は fixture の
内容と無関係に一致してしまう。すなわち「負例あり」という契約表示が恒真であった (F341)。
静的な到達可能性は完了の証明ではない — この点を、充足側へ倒す根拠に使ってはならない。

**既知の構造衝突 (2026-08-15 実測、2026-08-17 第 4 世代で更新)。** 下は「実装が足りない」型では
なく、契約・裁定・git の性質が互いに矛盾している型である。**いずれも、未定義・エラーを
充足側へ倒して解いてはならない。** (a)〜(c) は第 3 世代 (D438) が**受理集合を 1 bit も広げずに**
解消し、残った欠落を各項へ明記した。(e) は第 4 世代が同じく受理集合を広げずに要求を縮小した。
(d) は未解消である。

- **衝突 (a) 評価器の到達不能 — 第 3 世代で解消した。** 旧契約は 12 条件すべてを機械検査対象外と
  記していたため、条件別の評価器が実装に存在しても 1 本も呼ばれなかった。第 3 世代は評価器が
  実在する 6 条件だけを機械検査対象とし、閂を外した。**ただし解消したのは到達可能性だけで
  あり、6 評価器の終端は依然として「機械検査可能な充足証明が無い」である。**
  到達可能になったことを充足の根拠に使ってはならない。
- **衝突 (b) 条件 11 と裁定の食い違い — 第 3 世代で解消した。** 旧契約は作らないことが確定した
  2 つの方針成果物を必須としていたため、条件は構造的に永久未充足だった。第 3 世代は証拠を
  既存の実装機構 (承認上限の定数と 3 入口の予算 validator、および世代間で運ぶものを固定 key
  集合へ閉じる第二層射影とその production 配線) へ差し替えた。**これらを独立 4 機構と数えない**
  — 上限定数と 3 入口 validator は 1 機構、射影と production 配線は 1 機構であり、
  負の対照は開発テストであって commit 証拠に入らない。差し替えにより本条件は
  「証拠が欠けている」から「機械検査可能な充足証明が無い」へ移る。どちらも非充足であり、
  受理集合は広がらない。**残る欠落**: 削除した方針成果物が持っていた世代**下限**は、
  既存機構では代替されない (機構が持つのは上限だけである)。exact `G=2` の強制は §4 と §7 の
  起動形の責務であり、それを機械で確かめる受入 consumer は未実装である。
- **衝突 (c) 条件 3 / 8 の commit 自己参照 — 第 3 世代で契約の形を解消した。** 旧契約は、
  発効候補 commit の tree に含まれる manifest がその commit 自身の識別子を持つことを要求して
  おり、manifest の bytes が commit 識別子の入力である以上、構成不能だった。第 3 世代は
  §1 の二段束縛 (内容 commit と発効 commit を分け、祖先代用の禁止を親集合の完全一致で維持する)
  へ改めた。**解消したのは契約と規範本文の形だけである。** 実行 registry・起動・terminal report・
  受入は依然として単一の事前登録 commit 識別子を要求しており、二段束縛を消費しない。
  したがって条件 3 / 8 は機械検査対象外のまま残す — 配線されるまで、実装したふりをしない。
- **衝突 (d) arm の未束縛 — [T-1311] と [T-822] で解消した。** 旧本文が記したとおり、実行 payload と
  campaign identity に arm が入っておらず、宣言された arm が実際に走ったことを機械的に証明できなかった。
  [T-1311] が arm の選ぶ実入力 bytes から二層 digest を導いて 7 sink へ消費させ、[T-822] が
  条件 2 を機械検査対象へ載せ、受領証 v2 が**自身の参照 bytes から digest を再導出**して
  arm 束縛を確かめる形にした。**解消したのは宣言と実行の乖離だけである。**
  受領証が非認証理由から `c02-arm-binding-unproven` を落とせるのは、受領証が名指して hash した
  bytes から digest を再導出できたときに限る。**これは事前登録条件 2 (C02) の充足ではない** —
  同条件の評価器は依然として非充足を返す。両者を同一視してはならない。
  bundle 一式を捏造する攻撃は受領証層では落ちず、事前登録 commit 束縛と追記専用 registry の
  射程に残る。
- **衝突 (e) 条件 12 の実在しない allocation 述語 — 第 4 世代で契約の要求を縮小した。**
  旧契約は、実装に存在しない述語名 (単独性の要否を判定する名前) と、8c launcher が
  single-process 違反と resume 経路を launch 前に拒否することの証明を要求していた。
  名前は実在せず、当時の到達判定は同一 module 内しか辿らなかったため、正しく cross-module
  実装しても充足しえなかった (D441)。**ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回、択 (c))
  により、要求を実在する予約 binding — PBS job ID・boot ID・予約期限までの残時間の照合 —
  だけへ縮小した。** これは保証を弱める方向の改訂であるため、消えたものを名指しする。
  **この改訂後、条件 12 は次を要求も証明もしない。** (i) 正式 8c が単一 allocation / 単一 node /
  単一 process で完遂されること。(ii) launcher が multi-process の同居を launch 前に拒否すること。
  (iii) launcher が resume 経路を launch 前に拒否すること。**したがって、他プロセスと同居した
  計測や resume で継続した世代を、条件 12 は拒否しない。**
  縮小によって**新たに拒否されなくなった実行は無い** — 旧要求は構成上充足不能であり、
  1 度も発火していなかったからである (D441 決定 (3))。消えたのは事前登録された**意図**であって、
  現に成立していた保証ではない。
  **残る欠落 (縮小後も未充足)**: 8c の起動経路から予約 binding へ到達する production consumer は
  実装されていない。第 4 世代は判定の順序も改め、実 repository に対する条件 12 の理由が
  誤診断 (環境契約 consumer の不在) ではなく実在の欠落 (allocation consumer の不在) を指すようにした。
  **この判定は may-reach である** — 同一 binding が呼び先へ渡ること、launch を支配する位置に
  あること、例外が握り潰されないことは証明しない。静的な到達可能性を充足の根拠に使ってはならない。
  なお環境専用 runbook は単独性を**運用要件**として引き続き課している。条件 12 が要求しないことと
  runbook の運用要件が廃止されたことを混同してはならない — 両者は別の scope である。

**本手続きが主張しないこと。** 判定器は campaign 起動と trial registry 受入の両方へ結線済みで、
各 consumer は commit と判定結果を再検証する。ただし発効は 12 条件すべての充足との連言であり、
残る 11 条件が非充足なので成功不能である。実行した bytes の同一性、可変入力一式の同時改変、
git 履歴そのものの再構成は本手続きの外にあり、外部 anchor も確立しない。このため本書は
「発効に必要な全保証を強制した」とは主張しない。

## 7. 全件報告規則と、その機械強制の現在地

**規則の正本は 8b §3.3** である。本書では再掲しない。8c 固有の補足は次のとおり。

- 実走した trial id は**すべて** §5 の manifest 欄と結果へ載せる。台帳に載せない run を作らない。
- 提案 universe (全 attempt、全 reject、全 quarantine 棄却) も全件報告の対象とする。

### 機械強制が現在どこまで効くか (正直な現在地)

`orchestrator/campaign/autonomous_trial_completeness.py` は、8c supervisor の terminal report を
書く前に supervisor journal との完全性検査を行い、通らなければ report を書かない。
これが塞ぐのは次である。

- journal に残った role attempt が terminal report の一次配置から**脱落**する
- report 本体に journal にない role event が**混入**する / 同一 attempt が**重複**計上される
- 異常終了した cell の generation が report から**黙って消える**
  (ただし journal に role event が 1 件も入る前に落ちた generation は、消えても検出できない)
- 未知の event 種別が journal に入る
- 何も走らせていない空 cell を並べて `status="complete"` を名乗る
- `run-start` と terminal report の trial 同一性 (trial id / provider / 予算 / do_build) の食い違い

**これで塞がらないもの (残る file-drawer)。** 本書はこれらを「塞いだ」と主張しない。

- **どの trial を台帳へ入れるかの選択** — 検査は「terminal report まで到達した単一 trial の内側」
  しか見ない。trial 全体を commit しない、別の `--run-root` へ出す、report 書込み前に落とす、
  といった経路は検査の外である。前提条件 3 の registry が要る。
- **campaign 層 (WAL / whiteboard ↔ 層3 材料レポート)** — `layer3_report` は production 経路から
  自動生成されず、CLI か verifier を手で走らせた場合にだけ効く。
- **proposal / raw response / provider envelope / build 成果物 / bench 結果** — supervisor は
  path と hash の文字列を持つが、実ファイルの bytes を dereference していない。
- **persisted 層3 レポートの値の改変** — 既存の `_assert_bijection` は source-ref の対応しか
  見ないため、WAL を変えずに材料レポートの性能値を書き換えても通る。新 verifier の
  `--campaign-output-root` 経路は fresh rebuild との深い一致を要求してこれを塞ぐが、
  `layer3_report` 自体は変更していない。
- **層3 レポートの `generated_from_head`** — 上の深い一致から**除外している** (layer3 自身が
  この field を決定論比較の対象外と定めているため)。形式が正しい別の git object ID への
  差し替えは通る。どの checkout で材料レポートを生成したかを機械的に保証する仕組みは無い。
- **journal と report の同時改変** — 両方から同じ attempt を削って journal hash を再計算すれば
  整合する。`AttemptJournal` の append-only は実行中の `O_APPEND` であって、永続的な
  immutable registry でも hash anchor でもない。**supervisor 層では入力が可変な 2 ファイルだけである
  以上、これは情報理論的に検出できない** — 外部の immutable な anchor (registry、commit、署名) が要る。
  受入層では 2026-08-18 の受領証 v2 が git HEAD へ束縛された第 3 の anchor になり、両ファイルの
  hash に加えて report 内 descriptor からの digest 再導出を要求する。ただしこれが効くのは
  受入を通った trial だけであり、上記の supervisor 層の限界は解消していない。
- **supervisor の `harness` 値と campaign WAL の値の個体 cross-binding** — 未実装。
- **公開直前の再 hash から atomic replace までの極小の競合** — 検査後に journal bytes を
  もう一度照合してから report を書くが、その照合と `os.replace` の間は塞いでいない。

### D116 決定 (3) との関係 (判断はユーザー裁定へ返す)

D116 決定 (3) は「層3 双射検査の適用範囲を H1/H2 へ広げることで足りる」と断定している。
本書はこの裁定を書き換えない。本書が記録するのは**実測した事実**だけである。

- `layer3_report` は production 経路から自動呼び出しされない (呼び出し元は自 CLI とテストのみ)。
  実測: tracked な campaign WAL が 30 件に対し、tracked な層3 レポートは 7 件。
- 本 wave が新設した検査は supervisor 層 (journal ↔ terminal report) を対象とし、
  campaign 層との連結は CLI 経由の任意実行である。
- 上に列挙した残穴は、前提条件 3 (registry) と 8 (commit binding) を満たしても
  すべては閉じない (前提条件 9 の層3 必須配線、10 の cross-binding と正式 proof chain の
  authority、および外部 immutable anchor)。

**これらの事実のもとで D116 決定 (3) が履行済みと言えるか、追加の実装を要するかは未裁定である。**
本書はどちらとも決めない。裁定を得るまで、本系列について「file-drawer を塞いだ」と主張しない。

### 正式系列の起動形と依存関係

本節は**本系列をどの形で起動するか**を事前に確定する。ここに書かれていない形で起動した実行を
本系列の試行として数えない。

1. **発効候補 commit の要件**。同一の履歴 tree から、妥当な条件契約世代・§5 の全欄記入・
   §6 の 12 条件の機械証拠がすべて揃うこと。3 つは同じ commit で揃える。この commit が
   §1 の**発効 commit `C`** であり、その親集合は 6 cell manifest の bytes を導入した
   **内容 commit `P`** ただ 1 つに一致していなければならない。`C` は発効束縛 record だけを
   導入し、自分自身の識別子を持たない。
2. **起動側の再計算義務**。起動器は候補 commit の発効状態を自分で再計算し、その結果と、
   同じ commit へ束縛された 6 cell manifest および追記専用 registry だけを消費する。
   判定結果を運ぶ値そのものを信頼境界として扱わない。
3. **世代数の明示**。各 cell を正確に `G=2` で起動する。起動側の既定値は `G=2` ではないため、
   世代数を明示的に指定しない起動を本系列の試行として数えない。
   性能による早期停止を置かず、全 arm で同一の探索空間・開始状態・予算規則を用いる。
4. **manifest の全数実行**。manifest 外の試行を結果へ混入させず、manifest 内の cell を
   黙って落とさない。欠測・crash・不一致は 8b の規則に従って判定不能とする。
5. **受入の順序**。correctness gate、予算、反復単位対比とその分散を計算する judge、
   結果表 3 表 (二層の性能主張 = 順位事実と公式性能、および独立した選択評価)、
   層3 材料レポート、cross-binding の
   すべての consumer を通過した後にだけ正式受入へ渡す。**certified な選択を作る consumer は
   公式性能表の三値 `official_status` だけを受理し、順位表 (`descriptive_only`) を根拠にしない。**
6. **現時点で起動できないことの明示**。実測 (2026-08-15) では、現行の受入経路は
   本系列を certified として発行する形になっておらず、現行の workload 定義は
   H1 / H2 を正式 workload として起動できない。**したがって本節の起動形は、
   現時点の production では実行可能ではない。**
7. **配線 pilot との区別**。YCSB A/B/C の live pilot を再投入する作業は operational であり、
   本系列ではない。pilot は本系列とは別の workload 集合を対象とし、arm も揃っていない。
   **本系列の投入は、本節の依存をすべて閉じる別タスクとして起票する。**
   pilot の完了をもって本系列の起動条件が満たされたと見なさない。
