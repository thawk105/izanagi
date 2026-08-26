# 段 4 裁定 — [T-1380] 事前登録 artifact 3 件の発行

**裁定: 実装しない。D1077 を新事実付きでユーザー再裁定へ戻す。段 5・6 を飛ばし 4→7→8→9 とする。**

段 2 (プラン)、段 3 レンズ A、段 3 レンズ B、および親の独立実測が、互いに独立に同じ結論へ到達した。

## 1. 所見の real / refuted と採否

### R1 (real・採用) schedule authority 18 field のうち 3 件が実運用の値と型・意味で矛盾する

親が独立に実測した。

- `s8c_generation_projection.LEAKPROOF_CONTEXT` は文字列。
  `s8c_schedule._MAPPING_AUTHORITY_KEYS` は `leakproof_context` を JSON object と定める。
- `p3_autonomous_workload_trial._whiteboard()` は正式初期状態で空配列を返す。
  `s8c_schedule._validate_non_degenerate_value` は空配列を拒否する。
- `descriptor_binding` は runtime では cell ごとに異なるが、schedule は全 cell 共通の
  単一 mapping を要求する。

さらに `p3_autonomous_workload_trial._load_s8c_schedule_authority()` は無条件に例外を送出し、
production の authority は 1 つも存在しない。

**成果物影響:** この 3 件を projection で埋める規則を本 wave が決めると、6 cell 全部の
`search_space_sha256` / `initial_state_sha256` が著者選択の値で固定される。
certified 選択は空のままでも、以後の台帳がその digest を正として参照する。

### R2 (real・採用) D992 と D959 の着手順序規定に抵触する

- **D959** (2026-08-26) は 8c の閉塞を依存の層として記録し、
  「(d) 6 cell manifest・二段束縛 record・trial registry の不在」「(e) schedule authority の
  無条件 raise」を **(a) 発効判定に充足を返す終端の不在**に従属する下流症状と位置づけ、
  **順序を入れ替えて先に解除してはならない**と定めている。本 wave が発行しようとする
  3 artifact は、まさに (d) と (e) である。
- **D992** (2026-08-26) は「判定用 schedule の権威を凍結 spec に置く実装は、
  共有 8b ratified freeze が active になるまで着手しない」と定める。
- 親が実測: `s8b_ratified_freeze.load_ratified_freeze()` は
  `RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)` を送出する。
  **D992 の前提条件は満たされていない。**

### R3 (real・採用) D549 が本 wave のやろうとしたことを既に明示却下している

**D549** (2026-08-19) の本文:

- `output/s8c-preregistration/schedule.v1.json` の commit は、
  `run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch` の配線と
  権威の実体供給が完了する**別 wave (T-1380) まで scope 外として保留**する。
- 却下した選択肢: 「暫定 authority (test helper 相当の 18-key mapping) を provisional と
  marking した上で実装する — 機械的に暫定性を拒否できる仕組みが無く、正式 artifact として
  repo に残ってしまう。**段 3 の敵対相談 2 本が独立に不採用を推奨した。**」

**これは重い。** 本 wave の段 3 敵対相談 2 本も、独立に同じ不採用を推奨した。
2026-08-19 と 2026-08-27 で、別の子が同じ結論に到達している。

さらに **D549 は T-1380 を「配線と権威の実体供給を行う wave」と定義している。**
本 wave の引数は C05 配線 ([T-1379]) を scope 外にしたため、**D549 が定めた T-1380 の
内容と、本 wave に与えられた scope が食い違っている。**

### R4 (real・採用) 3 つの値が設計文書から一意に決まらない

- `campaign_id`: production は実 site から `ident.campaign_id()` で再計算して exact 一致を
  要求する。正式 site が未確定のため導出できない。発明した値は launch 時に拒否されるか、
  特定 site を暗黙に選んだ manifest になる。
- `freeze_id`: 8b §10.5 は「freeze identity」を要求するが、condition-freeze tip digest /
  manifest digest / ratified generation のどれを使うかを定めた規則が無い。
- genesis の slot 集合: 8b §10.5 は全 (holdout, 構成, 反復, attempt) slot を最初の観測前に
  閉じた集合として割り当てることを要求する。反復数 `n` は §5 未記入で、8b §10.2 は
  「`n` / `delta_min` / `sd_max` の値は凍結しない」と明記する。retry 理由の exact 列挙も
  事前登録の凍結範囲に無い。genesis は create-only かつ freeze ごとに唯一なので、
  濃度を発明して発行すると freeze が誤った割当へ恒久的に束縛される。

### R5 (real・scope 外・裁定パッケージへ) binding は任意 bytes の genesis で技術的には通る

レンズ A が発見した。`validate_preregistration_binding()` は genesis blob の hash 一致だけを
見て、`load_attempt_registry()` へ通さない。したがって P の canonical path に任意 bytes を置き、
その SHA-256 を binding に書けば binding は受理される。

**これは使ってはならない** (絶対規律 2)。ただし**実装側の穴として実在する**ので、
裁定パッケージへ載せる。

### R6 (real・scope 外) 証拠契約と実装の field 名不一致

証拠契約 C03 / C08 の `field_paths` は `cells[*].trial_id` だが、実装の manifest schema
`p3-8c-trial-manifest/v2` は `trials[*]` である。[T-1806] / D967 の担当で本 wave の scope 外。

### R7 (real・scope 外) manifest schema が 8b の要求を満たしていない

8b §10.2 は「manifest は cell ごとに `n` を持つ」と要求するが、
`_TRIAL_KEYS` は `trial_id / arm / holdout / campaign_id / generations` だけで `n` を持たない。

### R8 (real・scope 外) `C` の singleton diff を production が強制していない

`assert_effective_commit_exact_parent` は `C` の親集合だけを検査し、
`C` が binding path だけを導入したことは検査しない。設計 §1・§7 の要求と実装の間に隙がある。

### R9 (real・採用・**親の当初主張の訂正**) C05 の reason 遷移は artifact の正当性を証明しない

親は段 2 進行中に「schedule.v1.json を足すと C05 が
`EVIDENCE_UNDEFINED / schedule-schema-absent` → `UNSATISFIED / schedule-consumer-unreachable`
へ進み、SATISFIED は 0 のまま」と実測し、これを本 wave の値打ちとして挙げた。

レンズ A 所見 7 がこれを正しく攻撃した。**`_evaluate_c05` は artifact を decode しない。
1 byte の blob でも同じ遷移が起きる。** したがってこの遷移は「正当な schedule を発行した」
ことの証拠にはならず、gap ledger が「schema は成立した」と誤読される危険すらある。

**親の当初の value 主張は取り下げる。** 「発行すれば閂が 1 つ進む」は、
「blob を置けば表示が変わる」でしかない。

## 2. provisional 裁定 (P1)〜(P5) の確定

|#|親の provisional|段 2|レンズ A|レンズ B|**確定**|
|---|---|---|---|---|---|
|P1|master_seed を condition-freeze tip digest から導出|条件付き賛成|反対|条件付き反対|**不採用。** 循環はしないが、その seed 導出式を定めた規則が設計に無い。批准前は偽の権威|
|P2|trial_id / campaign_id を導出|反対|反対|反対|**不採用。** campaign_id は site 未確定で導出不能|
|P3|A→P→C の二段束縛 commit 構造|賛成|賛成|条件付き賛成|**採用。ただし実装しないので保留。** 次 wave が使えるよう記録する|
|P4|authority 18 field を既存凍結物から組む|反対|反対|反対|**不採用。** 3 件が型・意味で矛盾する|
|P5|genesis を本 wave で発行|必要性は賛成・実行は反対|同左|同左|**必要性のみ採用、発行は不採用**|

## 3. 変異事前登録

実装面の差分がゼロなので変異 matrix は免除する (`DW-S04`)。**受入全走は免除しない。**

## 4. 成果物影響 (DW-G05)

- **実装しない場合:** certified 選択・レポート・台帳の値は 1 つも変わらない。受理集合も不変。
  正式系列は起動できないままだが、それは本 wave の前から D959 が記録している状態である。
- **形式だけ発行した場合:** binding validator と formal non-certifying 経路の受理集合が
  不当に広がり、著者選択の authority digest が 6 cell 全部の初期状態参照として恒久固定される。
  genesis は create-only なので後戻りできない。

## 5. ユーザーへ返す裁定パッケージ

D1077 は 2026-08-27 の裁定であり、D992 / D959 (2026-08-26) と D549 (2026-08-19) より新しい。
**しかし D1077 の本文にも、それを記録した worklog 1011 の 1 行にも、これら 3 件への言及が無い。**
したがって「順序規定を意図的に上書きした」のか「3 件が視野に入っていなかった」のかが
判別できない。ここだけはユーザーにしか決められない。

**核心の 1 問:** D1077 は D549 / D959 / D992 の着手順序規定を上書きする意図だったか。

択一:

|択|内容|犠牲になるもの|機械で照合できるか|
|---|---|---|---|
|**B (親の推奨)**|D992 / D959 の順序どおり、共有 8b ratified freeze の発効を先に片付け、本件は保留する|T-1380 と D1077 の完了が延期される。受理集合と凍結意味は不変|`load_ratified_freeze()` の成功が解除条件として機械照合できる|
|A|導出規則を一括で裁定する (正式 site / env、trial id 規則、master seed 規則、freeze id 規則、18 field の canonical projection、`n`、attempt 数、retry 理由の exact 集合、D992 との関係)。必要な `DECIDER_VERSION` bump と次世代 condition-freeze record を発行する|ユーザー手番と変更規模が増える|裁定後は各値が導出式として照合できる|
|C|schedule v2 / manifest v3 / binding v2 を設計し、site 別 identity、`n`、genesis の実 parse を schema へ持たせる|既存 consumer との互換、移行実装、再凍結が要る。最も大きい|schema 側で強制できるので最も強い|
|D (不採用)|暫定 projection・任意 freeze id・6 個の `r0/a0` genesis で形式だけ発行する|D1077 の趣旨と絶対規律 2 を失う|できない|

**親が B を推す理由:** D549 が 2026-08-19 に同じ択を検討し、段 3 敵対相談 2 本の独立推奨で
D (形式発行) を却下している。本 wave の段 3 敵対相談 2 本も独立に同じ結論に達した。
**同じ問いに対して、別々の日に、別々の子が、4 本とも同じ答えを出している。**
加えて D992 の解除条件 (ratified freeze の active 化) は機械で照合でき、
別線として独立に進められると D959 自身が明記している。

**ただし A も同時に用意する価値がある。** B は「待つ」だけなので、待っている間に
A の裁定を取れば、ratified freeze が active になった瞬間に着手できる。
A と B は排他ではない。

## 6. 併せて返す scope 外の real 所見

- R5: binding validator が genesis を parse しない穴 (悪用すれば規律 2 を破れる)
- R6: 証拠契約 C03/C08 の `field_paths` が `cells[*]`、実装は `trials[*]` ([T-1806]/D967)
- R7: manifest schema が 8b §10.2 の「cell ごとの `n`」を持たない
- R8: `C` の singleton diff を production が強制していない
- R9: 論文 §8 B-3 の「どちらの経路も 3 artifact の不在に阻まれている」は正しいが、
  **D959 の層の記述と併記しないと「3 件を作れば進む」と誤読される。**
  実際には (d)(e) は (a) に従属する下流症状である。paper-story の次版で併記を要する。
