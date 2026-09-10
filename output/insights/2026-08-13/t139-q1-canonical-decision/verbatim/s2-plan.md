### 1. 読んだ資料と、読めなかった資料

指定された必読資料はすべて読めた。読めなかった資料はない。

基点: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-q1-canonical-decision/`

- `s1-brief.md`
- `s1-brief-appendix-pins.md`
- `src-Q1-Q2-package.md`
- `src-worklog-516-t139.md`
- `src-rulings7.md`
- `src-D234.md`
- `src-D282.md`
- `src-D291.md`
- `src-D292.md`
- `src-D320.md`
- `src-land2q4-package.md`
- `src-spool-readme.md`

加えて、実成果物の `receipt-schema-v1.json`、`record-items-v2.md`、D282/D291 の固定 parser、canonical `docs/decisions.md` の D291 後半を必要範囲だけ確認した。Web 取得、ファイル編集、テスト実行はいずれも行っていない。

### 2. decision の題 (1 行) と slug 案

題: **T-139 の受理述語欠落 4 件を閉じ、二重承認 manifest の namespaced closure を固定する**

slug: `t139-acceptance-predicate-envelope`

fragment 見出し案: `## {{D:t139-acceptance-predicate-envelope}}. T-139 の受理述語欠落 4 件を閉じ、二重承認 manifest の namespaced closure を固定する`

slug と遅延採番は `src-spool-readme.md:51-63`、decision 見出し形式は `docs/spool/decisions/README.md:5-16` に適合する。

### 3. 「決定」節の骨格

本文冒頭で、次の D234 外部署名を変更しないと宣言する。

```text
resolve_effective_preregistration(
    repository_root, *,
    core_ref   = (commit, path, sha256),
    addendum_a = (commit, path, sha256),
    addendum_b = (commit, path, sha256) | None,
) -> PreregBinding

submit_pilot(*, binding: PreregBinding) -> submission_id
submit_main(*, binding: PreregBinding) -> submission_id
verify_receipt(*, binding: PreregBinding, receipt) -> None
```

併せて、D234 の条件を逐語相当で全件保持する。

1. `core_ref.path` は canonical core path と一致する。
2. `core_ref.commit` の tree に blob が実在し、申告 SHA-256 と承認済み core の digest の両方に一致する。
3. `core_ref.commit` は承認 decision の fold commit の子孫である。
4. `addendum_a` は同型に解決し、従属先の `(path, commit, sha256)` が `core_ref` と一致する。
5. `addendum_a` は core の閉集合を exact-key で満たし、欠落・余剰をともに拒否する。
6. core と追補の commit は、caller でなく実 checkout から導出した `measurement_head` の祖先である。
7. core の `pilot_admission` が要求する追補がすべて解決済みである。`submit_main` はさらに `addendum_b` を同型に要求する。

根拠は `src-D234.md:64-94`。manifest の自己申告をこの七条件の代替にしてはならない。

**決定 (1): B1 — CMakeCache raw pointer は新しい記録要件版と schema 版で追加する。**

- 既存の `record-items-v2.md` と `receipt-schema-v1.json` は変更しない。新規 `record-items-v3.md` と `receipt-schema-v2.json` を別 blob として発行し、`schema_version = "t139-receipt/v2"` とする。
- v2 schema は `performanceCompileStock`、`performanceCompileMode`、`correctnessCompile` の各 `required` と `properties` に `cmake_cache_raw: fileRecord` を追加する。v3 記録要件では性能 compile を exact 10 key、correctness compile を exact 7 key とし、従来の全制約も維持する。
- 新しい canonical approval payload が D282 の `record_items` と `receipt_schema` role を新三つ組へ明示的に forward-supersede し、残る 4 approved blob role、target core、erratum 順序、合成 digest、保証境界を明示的に preserve する。D282 の既存 6 blob の bytes を書き換える経路は禁止する。
- validator は `cmake_cache_raw` の実 bytes を snapshot として検査し、そこから再導出した二値を `configure_argv`、`compile_commands` 実体と照合する。`cmake_cache`、`trace_enabled`、`analysis_enabled` は引き続き申告値であり、単独では受理入力にしない。

実成果物では性能 compile の `cmake_cache` は二値 object、`compile_commands` だけが `fileRecord` である (`receipt-schema-v1.json:54-61,94-132,134-171`)。correctness 側も同じ欠落を持つ (`receipt-schema-v1.json:805-826`)。記録要件も現在は性能 compile exact 9 key、correctness compile に raw pointer を持たない (`record-items-v2.md:222-245,377-401`)。現 blob の承認三つ組は `src-D282.md:41-47` に固定されている。

通る正例は、全 3 arm と全 correctness build の `cmake_cache_raw` が実在し、size/digest、CMakeCache の再解析値、argv macro、compile command が一致する v2 受領証である。**現時点では到達不能**であり、v3 要件、v2 schema、新 approval payload、writer、validator、正例 vector が land した後に到達可能になる。

**決定 (2): B2 — intent の母集合は producer の外にある sealed authority からだけ発見する。**

契約署名を次で固定する。

```text
issue_submission_intent(
    repository_root, *,
    study_id, series_id, study_stage, attempt
) -> fileRecord

issue_performance_started_marker(
    repository_root, *,
    study_id, series_id, study_stage, attempt_id
) -> fileRecord

seal_submission_intent_set(
    repository_root, *,
    study_id, series_id, study_stage
) -> fileRecord

discover_submission_intent_set(
    repository_root, *,
    study_id, series_id, study_stage
) -> SealedIntentSet
```

- canonical namespace は `output/registry/t139-submission-intents/<study_id>/<series_id>/<study_stage>/` とし、caller は root/path を渡せない。
- intent と marker のファイル名は `sha256(UTF-8(attempt_id))` の lowercase hex から一意に導出する。
- `intent-set.json` の exact key は `schema_version`、`study_id`、`series_id`、`study_stage`、`entries`。各 entry は exact `attempt_id`、`intent_ref`、`performance_started_marker_ref_or_null` を持つ。
- intent、marker、seal は create-only とし、既存 path、symlink、非 regular file を拒否する。書き込みの契約は `O_EXCL`、全 byte 書込み、file `fsync`、directory `fsync` までとする。既存の durable writer にこの実在可能な型がある (`orchestrator/qualification/submission.py:143-164`)。
- sealed set と `attempts[]` は attempt ID と `intent_ref` の三つ組で完全双射にする。qsub 失敗も省略せず、余剰 intent、欠落 row、digest 差、seal 後の intent を拒否する。
- authority は trusted submission controller であり、receipt producer の申告や `intent_ref` の自己整合ではない。

現 schema には attempt ごとの `intent_ref: fileRecord` はあるが (`receipt-schema-v1.json:1092-1123`)、母集合、namespace、seal はない。承認済み要件は qsub 前の create-only と全 attempt の exact 被覆を要求する (`record-items-v2.md:450-476,575-585`)。

通る正例は、trusted controller が intent を durable 化してから qsub し、失敗 attempt を含む sealed set の全 entry が受領証の `attempts[]` と完全双射になる stage である。**現時点では到達不能**であり、authority writer、seal/discovery、receipt writer、validator が land した後に到達可能になる。

**決定 (3): B3 — receipt-set は caller の配列でなく固定 namespace の terminal index から発見する。**

```text
discover_receipt_set(
    repository_root, *,
    study_id, series_id
) -> ReceiptSet
```

- namespace は `output/receipts/t139/<study_id>/<series_id>/`。許可名は `pilot.json`、`main_run.json`、`receipt-set.json` だけとし、caller が peer path や receipt 配列を渡す API は作らない。
- `receipt-set.json` の exact key は `schema_version`、`study_id`、`series_id`、`terminal_state`、`receipts`。
- `terminal_state == "main_complete"` では `receipts` は exact `{pilot, main_run}` で、各値は `fileRecord`。pilot 後に main を行わず終端した状態では exact `{pilot}` を許すが、main の適格 verdict は生成しない。
- 各 receipt の `study_id`、`series_id`、`study_stage` を index と照合する。`main_complete` では verification allocation が双方にちょうど 1 件あり、`allocation_id` と `accounting_trace`、`exclusivity.raw` の size/digest が一致しなければ拒否する。
- pilot 単体の stage-local 検査結果は `pending_peer` 相当であり、paired study の最終適格性に昇格させない。

現 schema は 1 object が `study_stage` を 1 つ持つ形で (`receipt-schema-v1.json:1220-1249`)、top-level exact closure に peer receipt や receipt-set field はない (`receipt-schema-v1.json:1222-1240,1293-1300`)。一方、承認要件は受領証 1 枚を 1 stage とし、pilot/main が同じ verification allocation を記録するよう要求する (`record-items-v2.md:29-53,575-585`)。

通る正例は、同一 `study_id` / `series_id` の `pilot.json` と `main_run.json` が index に exact に列挙され、verification allocation の ID と raw fileRecord が一致する集合である。**現時点では到達不能**であり、二つの receipt writer、terminal index、discovery consumer が land した後に到達可能になる。

**決定 (4): B4 — derivation transcript の canonical bytes、authority、数値契約を同時に固定する。**

- `j_derivation` と `q_derivation` は共通の `t139-derivation-transcript/v1` envelope を使う。top-level exact key は `schema_version`、`kind`、`authority`、`input`、`certificates`、`result`。
- `authority` は exact `approval_manifest`、`addendum_a`、`derivation_map`、`pilot_receipt`、`j_transcript_or_null`。最初の 3 件は承認済み `blobRef`、receipt/transcript は B3 の発見結果と一致する `fileRecord` とする。caller や `fixed_inputs` から authority を選ばせない。
- `kind == "j_derivation"` の `input` は exact `component_order`、`n_p`、`pilot_vectors`、`candidate_js`。順序は `(N_W1,H_W1,G_W1,N_W2,H_W2,G_W2)`、`n_p = 8`、候補は exact `[4,5,6,7,8,9,10,11,12,13]`。
- 非整数入力は既約な `{numerator, denominator}`、認証区間端点は正規化した `{numerator, exponent2}` で表し、JSON number の浮動小数は禁じる。
- canonical bytes は UTF-8、duplicate key 禁止、object key の UTF-8 byte 昇順、`,` / `:` 以外の空白なし、最終 LF ちょうど 1 個とし、fileRecord の size/digest は LF を含む全 bytes に対して計算する。
- 数値結果は承認済み a10/a11 の数学的定義に従い、各実数を `2^-80` 格子へ外向きに丸めた一意な dyadic 区間とする。quantile は `inf {x | CDF(x) >= p}`、`q` は上端、各 `p_k` は個別に外向き丸めしてから合計する。`L_j < 0.80 <= U_j` の候補があれば fail-closed で `design_not_feasible`、それ以外は `L_j >= 0.80` を満たす最小 `j` を `J` とする。
- validator は B3 で発見した pilot receipt/raw から入力、区間、`J` を独立再計算する。`admission_telemetry[].fixed_inputs.input_sha256` は再計算値との照合対象に限り、authority にはしない。
- main receipt の `consumed_cluster_slots` の要素数は再導出した `J` と一致しなければならない。

raw pointer 自体は `admission_telemetry[].receipt` に存在するが grammar はない (`receipt-schema-v1.json:941-955`)。producer の `fixed_inputs` を受理入力にしてはならない (`record-items-v2.md:784-799`)。再計算義務と main の `J` 一致は `record-items-v2.md:421-444,677-684`、承認済み選択式と区間条件は `addendum-a-reissue.md:607-746` にある。

通る正例は、発見済み pilot receipt 8 cluster から再計算した全 interval が transcript と一致し、曖昧な閾値跨ぎがなく、最小の適格 `J` と main slot 数が一致する組である。**現時点では到達不能**であり、pilot receipt、grammar、独立 interval validator、具体的な正例 vector が land した後に到達可能になる。

**決定 (5): Q2 — approval manifest は固定 envelope と三つの namespaced projection にする。**

- root は exact `schema_version`、`d282_record_approval`、`d291_publication_approval`、`conformance_vectors`。
- D282 と D291 の role を共有 `approved_blobs` へ union しない。
- fold root は trusted resolver 内の role-to-root 定数から選び、caller にも manifest にも選択権を与えない。manifest 内の fold commit は照合されるコピーであり、root 選択入力ではない。
- 現 receipt には `preregistration.approval_manifest: blobRef` が実在する (`receipt-schema-v1.json:257-288`)。一方、三 namespace はまだ code/canonical payload に存在しない (`s1-brief-appendix-pins.md:32-39`)。
- 通る正例は、両 projection がそれぞれの固定 fold payload と exact 一致し、vector index digest も一致する manifest である。**現時点では到達不能**であり、B1 の新 approval fold、manifest bytes、vector index、resolver が land した後に到達可能になる。

最後に、本文へ次を明記する。

> 完全な正例が public acceptance 経路を通る前に、本契約を「semantic validator 実装済み」「投入 gate 配線済み」と記録してはならない。受理集合が空のまま全入力を拒否する実装は本決定の実装ではない。

### 4. envelope の具体形 (Q2)

`F_r` は D282 の既存 fold、`F_r*` は B1 の新しい exact-byte approval payload の fold、`F_p` は D291 の fold とする。実 manifest に記号値は許さず、`F_r*` が literal に確定するまで `approval_manifest/v2` は発行できない。

```text
schema_version = "approval_manifest/v2"

d282_record_approval:
  base_approval_fold_commit
  approval_fold_commit
  decision_kind
  forward_supersedes
  preserved
  target_core
  approved_blobs
  erratum_application_order
  composed_sha256
  not_approved_as_record_items_root
  operational_boundary

d291_publication_approval:
  approval_fold_commit
  decision_kind
  prior_exact_byte_authority
  procedural_history
  source_core
  source_study_inputs
  document_relations
  approved_blobs
  approved_values_for_future_addendum_p
  historical_candidates_rejected_for_role
  exact_closure
  operational_state_on_fold
  authority_field_note
  role_coupling
  operational_boundary

conformance_vectors:
  index_path
  index_sha256
```

- `d282_record_approval.approved_blobs` は role 集合 exact 6 件を維持し、B1 後は `record_items` と `receipt_schema` だけが新三つ組になる。D282 の既存 role 集合は `src-D282.md:27-51` と `approval_payload.py:23-32`。
- `d291_publication_approval.approved_blobs` は exact `{publication_core, source_addendum_b}`。`document_relations` 全節、historical rejects、exact closure、禁止状態、role coupling も落とさない (`docs/decisions.md:13426-13510`; parser の exact top-level は `approval_d291.py:33-48`)。
- `conformance_vectors` の index 自体は exact `schema_version`、`positive`, `negative` とし、少なくとも完全正例 1 件、B1〜B4 の distinguishing negative、D234 (i)〜(vii) の各欠落、namespace swap、余剰 role、`alpha_reservation` 混入を含める。各 vector entry は `{path, sha256}`。index は `preregistration.approval_manifest.commit` の tree から読む。
- root mapping は次の固定写像とする。

```text
target_core                                      -> d282_record_approval.target_core, F_r*
addendum_a                                       -> d282_record_approval.approved_blobs.addendum_a, F_r*
derivation_map                                   -> d282_record_approval.approved_blobs.derivation_map, F_r*
erratum_t139_core_s15_exactkey_v1                -> d282_record_approval.approved_blobs..., F_r*
record_items                                     -> d282_record_approval.approved_blobs.record_items, F_r*
receipt_schema                                   -> d282_record_approval.approved_blobs.receipt_schema, F_r*
erratum_t139_core_s7_stresscheck_v1              -> d282_record_approval.approved_blobs..., F_r*
publication_core                                 -> d291_publication_approval.approved_blobs.publication_core, F_p
addendum_b alias / source_addendum_b              -> d291_publication_approval.approved_blobs.source_addendum_b, F_p
```

未知 role、別 namespace への fallback、caller 指定 root は拒否する。D291 の二 role 一括解決という既存 seam と整合する (`approval_d291.py:542-596`)。

`alpha_reservation` は root にも三 namespace にも置かず、存在すれば余剰 key として拒否する。resolver は固定 `F_r` の D282 payload から直接読む (`approval_payload.py:166-171`)。対象は実際には 9 field である (`src-D282.md:70-86`; `approval_payload.py:54-65`)。したがって「manifest は D282 payload 全体と exact 一致する」とは書かず、「`alpha_reservation` を除いた、ここで定義した D282 manifest projection と exact 一致する」と書く。

### 5. 「理由」節に入れるべき論点

- B1〜B4 は欠落の型こそ異なるが、同じ receipt acceptance と effective record approval に合流するため、1 decision で共通の非退行条件を固定する。
- v1/v2 の承認済み bytes を変更せず、新版と明示的 supersession を使うことで、既存 authority の捏造と silent rewrite を避ける。
- D282 の 6 role と D291 の 2 role は別々の exact closure であり、flat union はどちらかを必ず壊す (`src-Q1-Q2-package.md:82-97`)。
- role-to-root を内部固定することで、偽 manifest が自分で選んだ fold commit に対して自己整合する経路を閉じる。D282/D291 自身も manifest を trust root にしないよう要求する (`src-D282.md:3-8`; `src-D291.md:3-11`)。
- `alpha_reservation` は approval manifest の role closure ではなく、D282 base payload 直読の operational input である。非再掲は無視ではなく経路分離である。
- 正例 vector を完了条件に含め、恒真 deny と本物の validator を観測可能に区別する。
- 保証は trusted namespace、記録された bytes、数学的再計算の整合までに限る。台帳外 qsub、実際と異なる schedule を書く同権限 producer、観測窓外の現実を証明しない (`record-items-v2.md:801-827`)。
- B4 が保証するのは承認済み planning model と記録入力に対する再計算であり、planning model 自体の真実性や `L_J` が真の検出力に近いことではない。

### 6. 「却下した選択肢」節に入れるべきもの

- **Q1 (b): B1〜B4 を 4 decision に分ける。** effective record approval、manifest、vectors の連鎖を四重化し、途中状態で別々の受理述語が見えるため却下。
- **Q1 (c): 実装可能な部分だけを semantic validator と呼び、4 件を常時 hard-stop する。** 一時的 scaffold としては許せるが、完全実装・投入可能と記録する最終形としては却下。受理集合が空なら status は `contract-only` / `incomplete` のままにする。
- **Q2 (b): manifest を 2 枚に分ける。** root 選択が caller 側へ漏れ、D291 の parse/trust failure が二 role を同時に落とす coupling を保ちにくいため却下。
- **Q2 (c): `addendum_b` を manifest 外に置き、D291 payload からだけ直読する。** ledger から manifest への対応を `source_addendum_b` role だけ失うため却下。
- D282/D291 の role を単一 `approved_blobs` に flat union する案。
- `receipt-schema-v1.json` または `record-items-v2.md` を in-place 編集する案。
- `alpha_reservation` を manifest の別 namespace に再掲する案。
- `cmake_cache`、`fixed_inputs`、`len(consumed_cluster_slots)` の producer 申告を authority とする案。
- manifest の `approval_fold_commit` や caller 引数で trust root を選ぶ案。
- 完全正例なしの恒真 deny を「実装済み」と記録する案。
- 本 decision の fold を D292 の解除と読む案。

### 7. 「実装境界」節

**実装境界:** 本決定は文書上の契約だけを定める。新しい record-items/schema/approval payload の発行、manifest、intent authority、receipt-set index、transcript writer、resolver、semantic validator、consumer、conformance vectors、投入 script の実装は後続 wave の責務であり、本変更ではコードもテストも追加しない。

本決定をもって「semantic validator を実装した」「approval manifest を発行した」「投入 gate を機械配線した」「pilot または本走を解禁した」と記録してはならない。完全正例が実成果物を使って public acceptance 経路を通り、対応する負例が同じ経路で拒否されるまでは、受理集合が空のままでも完成扱いにしない。D264 の期待値も実 binding の正例が通るまで変更しない (`src-land2q4-package.md:192-194`)。

D292 の `pilot_submission = forbidden` / `main_submission = forbidden` は不変であり、解除は別の canonical decision と投入経路の実体を必要とする (`src-D292.md:1-8`)。

### 8. 親 brief への反論 (あれば)

- **P1:** 条件付きで賛成。1 decision にまとめてよいが、B1〜B4 の failure reason と入力 authority は混同せず独立節にする。
- **P2:** 「D320 が本 decision にかからない」という説明には反対する。D320 は凍結 pin、commit 束縛、bytes 同一性機構の新設・維持を既定で見送っており (`src-D320.md:3-10`)、B1 の新 exact approval payload、Q2 の fold-root projection、vector digest pin はその列挙に実質的に該当する。正しい整理は「D320 の射程外」ではなく、**後発かつ T-139 を名指しした第 7 束 Q1/Q2 (a) が、この範囲だけ既定を上書きする個別裁定**である (`src-rulings7.md:16-20`; `src-worklog-516-t139.md:8-15`)。D320 全体を supersede したとは書かない。
- **P3:** 賛成。D234 と同型の実装境界を必須とする。
- **P4:** 型分解には賛成。ただし B1 は schema だけでなく、exact 9/6 key を定める `record-items-v2.md` とも衝突するため、新 `record-items` 版も必要である。また B1 の supersession 後に Q2 の D282 root を旧 `F_r` だけへ固定すると、新 schema の authority が無い。`F_r` を base、実効 approval の fold を版ごとに内部固定する必要がある。
- **P5:** 賛成。ただし元パッケージの「6 field」は誤記で、列挙も実 payload も 9 field である。decision では件数を誤写しない (`src-Q1-Q2-package.md:120-129`; `src-D282.md:70-86`)。

### 9. この decision を land しても閉じない穴

- `record-items-v3.md`、`receipt-schema-v2.json`、それらの exact bytes を承認する新 payload と fold commit `F_r*` はまだ存在しない。したがって有効な `approval_manifest/v2` もまだ発行できない。
- `F_r*` を literal に持つ manifest は approval payload の fold 後にしか作れない。Q4 の「1 session」は維持できても、単一 land で approval fold とその literal を持つ manifest を同時成立させる方法は別途整理が要る。
- intent authority、receipt-set discovery、transcript grammar、数値 validator、full-path consumer、conformance vectors は未実装である。
- 実 receipt と完全正例がないため、受理集合の非空性はまだ実証されない。これを理由に条件を緩めてはならない。
- D292 の投入禁止、D264 の非 export・期待値維持は残る。pilot/main は依然投入不可である。
- trusted controller を迂回した台帳外 qsub、canonical namespace 外の receipt、同権限 actor による偽 raw は観測できない。記録された bytes の整合を、現実世界の不在証明へ拡張してはならない。
- B5 の上限も残る。validator が保証できるのは記録された観測窓・間隔・時刻の相互整合までで、実際に他作業が無かったことではない (`src-Q1-Q2-package.md:41-50`)。

## 総括

- Q1 は B1〜B4 を別型の契約として固定し、共通の effective approval と完全正例で束ねる。  
- B1 は既存 bytes の改変でなく、新 record-items/schema 版と新 approval payload を要する。  
- Q2 は exact 4-key root、D282/D291/vector の三 namespace、内部固定 role-to-root 写像とする。  
- `alpha_reservation` は manifest 閉包外とし、固定 `F_r` の D282 payload からのみ直読する。  
- D320 は射程外ではなく、後発の個別裁定による T-139 限定例外として明記すべきである。  
- この decision 自体は実装でも D292 の解除でもなく、完全正例が通るまで実装済みと記録してはならない。