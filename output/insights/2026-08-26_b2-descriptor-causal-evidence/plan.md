## 総括

brief の前提のうち、次を覆した。

- §5 の未記入は「7 欄」ではなく、実測どおり **9 欄中 8 欄**。`measured-activation-report.txt:3-11` と `docs/phase3-8c-preregistration.md:185-197` が一致する。
- 判定パラメータの機械検証 consumer は、現時点では要件を満たさない。parser は violations を生成するが、発効判定がそれを消費しない。また result judge は production caller と §5 値への束縛経路を持たない。
- `G=2` は凍結済みだが、統計反復 `n` は未凍結。総ベンチ予算・master seed・schedule/manifest も未凍結である。
- generation/search が生成した variant を、selector 語彙の「予測構成」へ読み替える規則は未凍結。これは 8b §8 の再凍結＋ユーザー承認なしに author が補ってはならない。
- 既に別の oracle n-pilot と R=11 実測が存在する。新 pilot はこれを既知結果として登録し、前向きデータとして再利用してはならない。

したがって、現状のまま P2 を「因子・セル・反復・判定規則が確定した prereg」として author へ渡すのは **NO-GO**。まず generation 固有の出力規則を裁定し、その後に限り、非発効 living draft を作るのが実行可能な順序である。

### brief の実測 6 項目

1. **批准の閂: 確認。**  
   `capture_contract_loader_binding()` は HEAD blob と disk bytes を照合する [`contract_loader_binding.py:349`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg/orchestrator/campaign/contract_loader_binding.py:349)。closure digest が台帳に無ければ拒否する [`enforcement_source_ratification.py:619`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg/orchestrator/campaign/enforcement_source_ratification.py:619)。現 digest と台帳唯一行の不一致も [`README.md:31`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg/output/insights/2026-08-26_t1759-t1742-ratification-history/README.md:31) に記録済み。本段では再実走していない。

2. **B-2 prereg の存在: 一部確認、一部過大。**  
   generation/search 対応は `docs/phase3-8c-preregistration.md:57-70`、3 arm は `docs/phase3-8b-descriptor-design.md:156-170`、6 cell は `docs/phase3-8c-preregistration.md:139`、全 cell の `G=2` と固定停止は同 `:91-95,139-143` で凍結済み。  
   一方、統計反復 `n` / `delta_min` / `sd_max` は「値を凍結しない」と明記される `docs/phase3-8b-descriptor-design.md:464-484`。総ベンチ予算・seed・manifest も `docs/phase3-8c-preregistration.md:189-197` で未記入。

3. **§5 と C01〜C12: 件数を訂正したうえで確認。**  
   §5 は 8 UNFILLED + 1 FILLED [`measured-activation-report.txt:3-11`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b2-descriptor-prereg/measured-activation-report.txt:3)。条件理由は同 `:12-23` のとおり。ただし「未凍結はこれだけ」は、generation 出力の読み替え未定義があるため誤り。

4. **判定パラメータ consumer: 反証。**  
   `s8c_preregistration.py:818-820` は validator を呼び、`:874-945` が型・有限性・符号等を検査するが、結果は `MarkdownContract.section5_value_violations` に保存されるだけ (`:1042-1045`)。発効判定 `:1925-1956` はその値を参照しない。  
   `s8c_result_judge.py:217-238` にも validator はあるが、`judge()` は private `_ContrastParams` を直接要求する (`:1012-1019`)。production caller は存在せず、参照はテストと静的 evaluator に限られることも `docs/decisions.md:25943-25946` と grep が一致する。よって 8b §10.2 の解除条件は未充足。

5. **F369: 確認。**  
   二重 import による全条件 `evaluator-exception` 化と library 経路を正とする扱いは `docs/failures.md:10710-10725` に記録済み。本 wave の修理対象ではない。

6. **編集面の重複: 確認。**  
   base `e29084e0` に対する全 `worktree-*` branch の name-only 差分を再照合した。`s8b_*` / `phase3-8b*` に触るのは t1484 の `orchestrator/campaign/s8b_attempt_profile.py` と `docs/phase3-8b-restart-runbook.md` のみ。P2/P4 の予定 3 path との重複はない。B-4 worktree も clean。

### 攻撃点への回答

- **(a) P2 の時期:** 数値確定・発効は時期尚早。ただし、裁定後に「非発効 draft」として pilot scope、HARKing 境界、解除条件を先に commit する価値はある。C03/C05 完了まで文書設計自体を遅らせる必要はないが、読み替え裁定より先に因子・セルを author が決めてはならない。
- **(b) selector 語彙:** 未凍結。judge は `prediction` を構成 ID へ正規化し (`s8c_result_judge.py:538-672`)、on/off 差と swapped の exact follow を評価する (`:682-725`)。対して supervisor は generation ごとの proposal と `harness.variant` を記録するだけ (`p3_autonomous_workload_trial.py:3842-3845,4063-4129`) で、prediction map を生成しない。実装せず裁定へ送る。
- **(c) 置き場所:** 承認後の前向き・未発効 prereg は `docs/` が正しい。現時点で裁定資料だけを残す場合は `output/insights/` とし、P4 は行わない。
- **(d) 追加反証:** 既存 n-pilot は固定 6 configuration × 2 holdout の別 estimand [`preregistration.md:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg/output/insights/2026-08-16_t1142-n-pilot-prereg/preregistration.md:66) で、R=11 実測・n 未導出 [`measured_distributions.md:75`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-descriptor-prereg/output/insights/2026-08-16_t1142-n-pilot-prereg/measured_distributions.md:75)。また 8c 文書の「FORMAL_WORKLOADS 未実装」という現在地 `docs/phase3-8c-preregistration.md:201-203` は古く、実装は `p3_autonomous_workload_trial.py:242-249` に存在する。ただし formal preflight は意図的に拒否する `:922-935` ため、実走不能という結論は変わらない。

## プラン

### 0. author 開始前ゲート

1. 下記「裁定パッケージ候補」の generation 出力規則をユーザー裁定する。
2. 裁定が無い場合は repo 差分ゼロで停止し、新文書・P4 を作らない。
3. 裁定後も本 wave は文書 draft と living-doc 登録だけに限定し、8b/8c、judge、supervisor、campaign 起動経路を変更しない。

### 1. P2 新規文書

`docs/phase3-8b-pair-planning-pilot-preregistration.md:1` に新規作成する。節構成は B-4 の `§0`〜`§10` (`ref-phase3-b4-reflux-ablation-preregistration.md:32-321`) を踏襲する。

|節|凍結するもの|凍結しないもの|
|---|---|---|
|§0 状態と表記|`approval-waiting / NOT_EFFECTIVE`、正本の precedence、base `e29084e0` の activation snapshot、placeholder 規約|「現在有効」という宣言、§5 値|
|§1 効力と限界|全欄記入済み commit が pilot 観測より先であること、pilot commit/result commit の ancestry、変更手続き|B-2 正式系列の効力|
|§2 主張と scope|estimand は `n` / `delta_min` / `sd_max` の計画だけ。`b2_causal_evidence=false`、`formal_8c_cell=false`、`official_status_eligible=false` を規範化|descriptor 因果効果、headline、統計的有意、selector 成功|
|§3 因子・arm・cell|裁定済みの generation 出力単位、pilot の exact cell 集合、pair key、swapped を pilot に含めるか、同一予算・開始状態・乱数規則|8c の 6 cell 定義や判定規則の再定義。裁定前は全て placeholder|
|§4 正しさゲート|legacy + S2、trace-enabled verify と trace-disabled bench の分離、gate 不通過・欠測・非有限値は判定不能、unpaired fallback 禁止|gate の緩和、screen-reject の certified 化|
|§5 数値欄|pilot 反復 R、candidate `n` 集合、parameter 導出関数、schedule seed/generator hash、arm/holdout/総予算、env、model/prompt、責任者・開始時刻を値欄として列挙|初稿では全て未記入。8c §5 の値は書かない|
|§5.1 解除条件|裁定済み出力規則、完全 block schedule、manifest/registry、production consumer、独立データ、結果閲覧前の導出関数 commit を全て要求|既存 R=11 の値を見て選んだ境界|
|§6 前提条件|批准 closure、pilot 専用 namespace、全件 manifest、attempt registry、予算 consumer、correctness gate、parameter consumer、H1/H2 既観測 closure の申告|「mechanism が存在する」だけでの充足|
|§7 全件報告|全 attempt/reject/crash/missing、全 raw pair、導出失敗を含める。pilot trial ID を 8c manifest へ混入禁止。成功しても B-2 へ昇格禁止|成功例だけの要約、pilot から `official_status` を発行すること|
|§8 負の対照|duplicate/missing replicate、gate-red、非有限値、未承認 parameter、pilot artifact の formal 受入、未裁定 variant mapping を必須拒否例として登録|本 wave で負の対照実装済みという主張|
|§9 既知結果台帳|T-1142 prereg、R=11 実測、D466〜D468、現在の judge/parser、activation report を HARKing 境界として列挙|既存データを新しい前向き pilot と分類すること|
|§10 閉じないこと|generation 出力裁定の実装、§5 記入、8c C01〜C12、consumer wiring、formal run、B-2 結論|後続の完了を先取りすること|

「pilot を B-2 に数えない」は §1・§2・§7 の三か所で重ねて固定する。特に §7 には、pilot 結果が三条件を見かけ上満たしても、8c の `condition_ids`・6 cell manifest・三表へ入力してはならず、後から formal へ昇格できない、と逐語で置く。

### 2. P3 現在地

新文書 §0 には、可変な「現在値」ではなく `e29084e0` に限定した測定 snapshot として次を記録する。

- `NOT_EFFECTIVE freeze=valid`
- §5 = 8 UNFILLED / 1 FILLED
- C03 = manifest/registry 未定義
- C05 = schedule schema 不在
- C08 = prereg binding 未定義
- 残り 9 条件 = completion proof 非機械検査
- parameter violations は生成されるが発効判定に未結線
- judge は production caller なし

各 snapshot に source commit と `measured-activation-report.txt` の取得経路を添え、将来の現在値として再掲しない。

### 3. P4 の exact 編集点

裁定後に新文書を作る場合だけ行う。

- `tools/check_docs.py:145`、現 `phase3-8c-preregistration.md` 行の直前へ  
  `REPO / "docs" / "phase3-8b-pair-planning-pilot-preregistration.md"` を `LIVING_DOCS` として追加する。
- `docs/README.md:22-24` の 8c prereg 項目直後へ、pair-planning pilot の目的、非発効、B-2 証拠に数えないことを 1 項追記する。
- `orchestrator/tests/test_check_docs.py` は変更不要。`_enumerated_rels()` が `_ENUMERATED_DOCS` から動的導出する `:708-710`、合成 fixture が全列挙文書を自動生成する `:1230-1232` ため、新しい literal fixture は不要。

### 4. 焦点走対象

参照関係から引いた焦点 test は次。

- `orchestrator/tests/test_check_docs.py` — `check_docs` を直接 import (`:39-41`) し、列挙 living doc の合成 baseline (`:1393-1401`)、不在 positive control (`:10076-10111`)、実 repo lint (`:11945-11953`) を消費する。
- `orchestrator/tests/test_s8b_selector_output.py` — `check_docs` を直接 import (`:19-24`) するが、消費するのは別定数 `LITERAL_PLACEHOLDERS` (`:389`) のみ。import smoke としては関連するが、LIVING_DOCS の意味的 consumer ではない。
- production 相当の静的確認として `python3 tools/check_docs.py`。

本段では書込可能 tmp がないため、pytest・checker とも実走しておらず、緑とは報告しない。

### 5. 本 wave でやらないこと

- `docs/phase3-8b-descriptor-design.md` / `docs/phase3-8c-preregistration.md` の書換え
- 8c §5 の 8 未記入欄の記入
- generation 出力を prediction とみなす author 独自解釈
- `s8c_preregistration.py`、`s8c_result_judge.py`、supervisor、campaign launch の変更
- correctness gate、受理集合、screening 規則の緩和
- selector 実験、dry-run、YCSB A/B/C、既知 rr5/rr50/rr95、既存 T-1142 R=11 を B-2 成果へ算入
- pilot 成功後の遡及的 formal 昇格
- 二つ目の B-2 判定規則・事前登録の新設

## 裁定パッケージ候補

### 1. generation/search の出力単位

- **A: generation 固有の判定表へ再設計（推奨）**  
  G=2 の proposal sequence を generation/search の outcome として扱い、on/off 差・swapped 追従・性能対比を set/sequence 用に再凍結する。selector 語彙を流用しない。8b §8 再凍結と 8c 改訂が必要。
- **B: 最終 generation の canonical variant を arm 出力に固定**  
  実装は小さいが、generation 1 を捨て、独立生成間の swapped exact match が何を意味するかを追加裁定する必要がある。
- **C: 合成後に deterministic selector を置く**  
  現 judge を流用しやすいが、合成効果と選択効果が交絡し、8c が selector 実験と独立であるという scope を弱める。

A を推奨する。B/C を author の既定値として採ってはならない。

### 2. 本 wave の成果物

- **A: 上記裁定後、`docs/` に非発効 prereg draftを作る（推奨）**
- **B: 裁定前は repo 差分ゼロとし、ruling package だけを `output/insights/` に残す**
- **C: 裁定前でも未定義セルを含む living draft を作る**

C は「因子・セルを凍結した」という誤読を生むため非推奨。

### 3. 既存 n-pilot データの扱い

- **A: 既知結果台帳に載せ、新 pair pilot の parameter 導出から除外する（推奨）**
- **B: 既存 R=11 を exploratory prior として使うが、導出値は事前登録済みと呼ばない**
- **C: 既存値から `n` / `delta_min` / `sd_max` を確定する**

C は結果閲覧後登録になるため採らない。