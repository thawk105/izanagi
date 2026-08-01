# Phase 3 段 8c 正式系列 事前登録 — 発効前 draft

段 8c の正式系列 (holdout H1 / H2 × descriptor on/off/swapped) の事前登録文書である。
凍結機構は使わず、**git commit した 1 枚の文書**で事前登録する (D116)。

**この文書はまだ発効していない。** §5 の数値欄が空で、§6 の前提条件が未充足だからである。
発効前の版を祖先に持つだけでは、事前登録の効力 (§1) は生じない。

**この文書は 8b 設計を書き換えない。** holdout の条件、arm の定義、correctness gate、
判定基準、crash 時の扱い、探索予算の単位は `docs/phase3-8b-descriptor-design.md` が正本である。
本書はそれらを**再掲せず参照**し、8c 固有の事項 (実行 harness、generation 予算、全件報告の
機械強制、発効手続き) だけを定める。8b が凍結する項目を変えるには同文書 §8 の再凍結 +
ユーザー承認が要り、本書はそれを迂回しない。

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
  - 発効後の変更は旧版を git 履歴に残したまま新しい commit で行い、変更理由と変更時点を
    本書へ明記する。**結果 commit より後に書かれた変更は事前登録として数えない。**
- **成果物への commit 記録は未実装である。** 現行 supervisor の terminal report は
  prereg commit も measurement HEAD も持たない。この binding の実装は前提条件 (§6) に含む。

## 2. 主張の型と scope

- **位置づけ**: 8b 設計 §7 の段階 2「generation/search 実験」に対応する。段階 1 の selector 実験
  とは独立であり、selector の成否を本系列の根拠にしない。
- **主張の型は 8b 設計 §1 が正本**である。本書はそれを弱めない。
- **主張しないもの**: headline 性能、他 CC 実装との比較、対象別 floor と検定数値が確定するまでの
  統計的有意。YCSB A/B/C の配線 pilot は operational であり、成功しても本系列へ昇格させない。
- **generation 予算に由来する限界 (未解決)**: 現行の承認上限は 1 世代 / cell である (D114)。
  1 世代では critic の出力が次世代の生成へ還流せず、探索も候補改善も起きない。
  D106 と 8c runbook は「正式系列は同一 generation budget を要求するので自動的に禁止側へ入る」と
  書いている。**budget=1 のまま本系列を「ワークロード特化合成」の主張へ使えるかは未裁定であり、
  裁定なしに実走してはならない** (§6 の前提条件 11)。

## 3. holdout・arm・correctness gate・判定基準・停止規則

いずれも **`docs/phase3-8b-descriptor-design.md` が正本**である。

下の表の左 2 列は**正本の所在を指すポインタであり、内容の定義ではない**。
条件・列名・成立条件・判定不能条件は必ず 8b 側を読むこと。8b が再凍結された場合、
本表の要約語が古くなっても**8b が勝つ**。右列だけが本書の定めである。

|項目|正本|8c 固有の補足|
|---|---|---|
|holdout の条件と未既知性の確認手続き|8b §3|実走開始前に同手続きを再実行し、証跡 (a)〜(e) を §5 へ記入する|
|on / off / swapped の arm と derangement|8b §4|8c では descriptor は planner / coder への入力である。arm を journal・report・campaign ID・proposal file 名・invocation ID の識別子に含める (§6 の前提条件 2)|
|correctness gate (legacy + S2)、build 分離|8b §5.2 / CLAUDE.md 絶対規律 1・2|8c の diff quarantine と禁止識別子 gate は driver 側を authoritative path とする。supervisor 側 preview を判定根拠にしない|
|判定基準の表|8b §6|本書で列・成立条件・判定不能条件を書き換えない|
|crash 時の扱い|8b §9 項 8 (択 (a) = 実験全体を判定不能、再走なし)|8c supervisor の現行 state machine はこれに従っていない (cell 単位の停止 + 新 trial id での再走)。整合は §6 の前提条件 4|
|探索予算の第一単位 (累積ベンチ実時間)|8b §5.2|generation 予算は 8c 固有として §4 に置く。generation cap は bench 秒予算の代替にならない|

## 4. 8c 固有の事項

- **generation 予算**: 全 arm 同一とする。現行の承認上限は 1 世代 / cell (D114 の
  `MAX_APPROVED_GENERATIONS`、CLI・`run_trial()`・`_run_workload()` の 3 入口で機械強制)。
  2 世代以上へ増やすには T-244 (還流設計) の裁定、D114 の定数と境界テストの同一変更単位での改訂、
  および本書の再事前登録が要る。
- **cell 数**: 2 holdout × 3 arm = 6。全 cell を実走前に manifest として列挙する (§6 の前提条件 3)。
- **停止**: 固定世代数で停止する。性能目標による早期停止を置かない
  (Best-of-N と選択的報告になるため)。role 応答の schema 違反は再試行しない。
- **wall budget**: `--max-wall-seconds` は hard wall ではない (時刻検査は workload と generation の
  先頭だけ)。予算の強制手段として使わず、予算判定は累積秒の台帳で行う。

## 5. 実走前に数値で埋める欄 (空欄のまま実走しない)

|欄|値|
|---|---|
|累積ベンチ実時間の総上限と arm ごと・holdout ごとの上限|未記入|
|env_tag (実測環境)|未記入|
|対象別 between-run floor (H1 / H2)|未記入|
|master_seed|未記入|
|検定 4 点 (n / 検定単位 / 検定力 / 総予算)|未記入 (検定を行う場合のみ)|
|未既知性再確認の証跡 (a) 検索対象 dir 一覧 / (b) 検索式 / (c) 一致 0 件の出力 hash / (d) positive control の hit 数 / (e) 確認者|未記入|
|swapped 対応表の固定日時と bytes hash|未記入|
|実走前に確定する 6 cell manifest (trial id、arm、holdout、campaign id)|未記入|
|実行責任者・開始時刻|未記入|

## 6. 実走の前提条件 (未充足のものが 1 つでもあれば実走しない)

1. **H1 / H2 の workload 定義**と、1m records / 48 threads の規模が 8c supervisor に実装されている。
   現行の `WORKLOADS` は rr50 / rr95 / rr100 の 3 点だけで、records と threads も
   `_campaign_for` / `_perf_for` / `_descriptor_for` に 100k / 4 で hard-code されている。
2. **off / swapped arm** が実装され、arm が journal・report・campaign ID・proposal file 名・
   invocation ID の識別子に入っている。現行 pilot は descriptor-on だけで、識別子は workload 名のみで
   あるため arm を増やすと path が衝突する。
3. **実走前の 6 cell manifest** と、それに対する append-only の trial registry が存在し、
   manifest 外の trial を結果へ混入させず manifest 内の trial を黙って落とさない。
4. **crash 時の扱い**が 8b §9 項 8 (実験全体を判定不能、再走なし) に整合している。
5. **schedule・master seed・arm 順序**が実走前に生成・固定され、全 arm が同一の search space と
   同一の開始状態から出発することが機械的に保証されている。
6. **累積ベンチ実時間の予算**に実 consumer があり、予算不足時に未実施 arm を**対称に**判定不能へ
   倒す停止が実装されている。値の欄 (§5) だけを埋めて consumer を作らない形は、
   8b が拒否する恒真保証である。
7. **対象別 between-run floor** が H1 / H2 について再実測され、§5 に記入されている。さらに
   floor の consumer、§7 の 3 条件を計算する judge、6 セル結果表の生成が実装されている
   (現行 supervisor は成功判定を計算しない)。
8. **prereg commit と measurement HEAD の記録**が実走成果物に焼かれ、祖先関係を機械検査できる。
9. **層3 材料レポートの生成と検査**が本系列の acceptance の必須経路に配線されている
   (現状は任意実行の CLI)。
10. **proposal / raw response / provider envelope / build 成果物 / bench 結果**と
    supervisor / campaign WAL の cross-binding があり、正式 proof chain の authority が
    決まっている (現状 `output/autonomous-trials/` は「正式 proof chain ではない」)。
11. **generation 予算に関するユーザー裁定** (§2 の限界) が済んでいる。
12. **計測環境**が単一 allocation / node / process で campaign を完遂できる
    (Pegasus の場合は環境専用 runbook に従う)。現行 trigger driver の env-tag は
    `linux-baremetal` 固定で、認識済みの Pegasus site を拒否する。

**現時点で 1〜12 はいずれも未充足である。** 本書は事前登録の**内容**を確定するものであり、
発効の手続き自体は下記のとおり未定である。実走の開始を意味しない。

### 発効の判定は誰が行うか (未解決)

**本書は「発効」を宣言する権限と形式をまだ定めていない。** 上の 12 条件と §5 の記入は
発効の**必要条件**であって、それだけで自動的に発効するわけではない。8b 設計 §8 は
holdout・予算・gate・判定基準の確定に**再凍結 + ユーザー承認**を要求しており、本系列の
発効もその系列に属すると考えられる。承認レコードの形式 (8b が採った approval record 方式を
使うか、別形式か)、発効を検証する機械 validator、発効 commit の認定手続きは**いずれも未定である**。
この設計択一はユーザー裁定へ返す。裁定と実装が済むまで、本書は発効しない。

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
  immutable registry でも hash anchor でもない。**入力が可変な 2 ファイルだけである以上、
  これは情報理論的に検出できない** — 外部の immutable な anchor (registry、commit、署名) が要る。
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
