## Q1

`_add_task_manifest_option` の呼び出しは全件検索で **10 件**。定義 `tools/codex_reasoning_ab.py:11849-11850` 自体は件数に含めない。

| CLI verb | 呼び出し |
|---|---:|
| `build-snapshot` | `tools/codex_reasoning_ab.py:11862` |
| `render-prompt` | `tools/codex_reasoning_ab.py:11874` |
| `collect-run` | `tools/codex_reasoning_ab.py:11909` |
| `supervise-pair` | `tools/codex_reasoning_ab.py:11923` |
| `aggregate` | `tools/codex_reasoning_ab.py:11987` |
| `verify` | `tools/codex_reasoning_ab.py:11992` |
| `make-packets` | `tools/codex_reasoning_ab.py:11998` |
| `append-verdicts` | `tools/codex_reasoning_ab.py:12007` |
| `freeze-verdicts` | `tools/codex_reasoning_ab.py:12013` |
| `reveal-mapping` | `tools/codex_reasoning_ab.py:12021` |

`main` は指定された manifest を一度ロードし (`tools/codex_reasoning_ab.py:12028-12031`)、各 verb へ渡す。したがって A1 の「CLI に task-manifest 入力が無い」は実態より低い。

一方、`verify-snapshot` は `--task-manifest` を持たず、selector も POS/NEG 固定である (`tools/codex_reasoning_ab.py:11864-11867`)。`main` からも manifest を渡していない (`tools/codex_reasoning_ab.py:12054-12058`)。

## Q2

前案の「`render-prompt` は既定 manifest の provenance のみを読み、task 入力処理の CLI 閉包は未完成」という主張は、**前半が偽**。

実行経路は次のとおり。

1. CLI が外部 manifest をロードする (`tools/codex_reasoning_ab.py:12028-12031`)。
2. その manifest を使って `benchmark_task_id` を解決する (`tools/codex_reasoning_ab.py:12034-12044`)。
3. 同じ manifest を `render_prompt` へ渡す (`tools/codex_reasoning_ab.py:12060-12072`)。
4. `render_prompt` は manifest から task を選び (`tools/codex_reasoning_ab.py:3461-3465`)、task 固有の session、rollout、prompt-source pin を入力決定に使う (`tools/codex_reasoning_ab.py:3483-3505`)。
5. task の `snapshot.artifact_names` から、prompt が要求する untracked path 集合も検査する (`tools/codex_reasoning_ab.py:3522-3535`)。
6. 外部 manifest の場合は、その digest を持つ snapshot oracle も要求する (`tools/codex_reasoning_ab.py:3466-3478`)。

したがって `render-prompt` は provenance を記録するだけではなく、**task 入力そのものを manifest から決定する**。前案は採らない。

ただし Q1 のとおり standalone `verify-snapshot` が未接続なので、「task 入力処理層全体の CLI 閉包が完全」とまでは書けない。

## Q3

費用計算は次の範囲まで実装済み。

- 発火条件は、全 slot が凍結 price version を持ち、material に schedule descriptor が存在する場合 (`tools/codex_reasoning_ab.py:10105-10136`)。
- snapshot の path、bytes digest、schema、version を再検査する (`tools/codex_reasoning_ab.py:9556-9587`)。
- `coverage_status` は常に `"partial"`、`certification_status` は常に `"not-certified"` (`tools/codex_reasoning_ab.py:9696-9707`)。
- run/attempt ごとの値は `_normalized_cost_for_attempt` が Decimal で計算する (`tools/codex_reasoning_ab.py:9711-9793`)。
- `cache_write` の mapping は receipt field 空、operation `None` (`tools/t189_price_snapshot.py:81-98`)。計算器は operation `None` を明示的に skip する (`tools/codex_reasoning_ab.py:9754-9764`)。
- per-run 値は各 `resource_ledger` 行の `resource["normalized_cost"]` に入る (`tools/codex_reasoning_ab.py:10383-10425`)。
- 軸別集計は `_AXIS_FIELDS` と arm ごとに作られ (`tools/codex_reasoning_ab.py:9796-9866`)、結果直下の `normalized_cost_axis_ledger` に入る (`tools/codex_reasoning_ab.py:10530-10531`)。
- `unavailable` と `not-incurred` は金額・`attempt_count` に加えず、`scheduled_attempt_count`、`unavailable_count`、`not_incurred_count` に残す (`tools/codex_reasoning_ab.py:9867-9881`)。
- `_certification_scope` の `certified_report_fields` は `["valid"]` だけで、費用 field は入っていない (`tools/codex_reasoning_ab.py:11208-11227`)。
- `normalized_cost` の全出現は計算・出力構築側であり、resource gate や overall 判定の reader は現行ファイル内に無い。

よって「費用の正規化計算は未実装」は実態より低い。ただし、完全費用・certified field・判定 gate と呼ぶこともできない。

## Q4

前案の主張は **真**。

`make_packets` は manifest を読んだ直後、schedule descriptor の有無を調べる前に、packet-source manifest の `task_manifest_sha256` を要求する (`tools/codex_reasoning_ab.py:11292-11307`)。digest が無い場合、`_require_task_manifest_sha256` は「artifact predates task-manifest digest binding and must be regenerated」と fail-closed に拒否する (`tools/codex_reasoning_ab.py:2731-2749`)。

schedule descriptor 無しの経路自体は残る (`tools/codex_reasoning_ab.py:11355-11357`)。しかし、digest を持たない既存 legacy manifest bytes はそこへ到達できない。したがって、

- legacy shape の経路は残る
- 既存 artifact との byte-level 後方互換は無い
- 利用には digest 付き manifest の再生成が必要

という三点を併記すべき。

## Q5

結論は **部分的に真**。前案の「両 field が schedule、verdict、aggregate へ伝播する」を、そのまま採ると広すぎる。

- `oracle_kind` は task manifest の必須 field (`tools/codex_reasoning_ab.py:2609-2618`)。`_slot_dimensions` が task manifest から読み (`tools/codex_reasoning_ab.py:9069-9087`)、validated schedule row へ書き戻す (`tools/codex_reasoning_ab.py:9134-9147`)。aggregate では positive/negative 軸と false-finding 集計に使う (`tools/codex_reasoning_ab.py:10151-10218`)。
- `known_finding_ids` も task manifest の必須 field で、集合を task 単位または manifest 全体から取得できる (`tools/codex_reasoning_ab.py:3017-3042`)。
- blind verdict 時点では task が非公開なので、`known_finding_ids` の **manifest-wide union** で `equivalent_to` を検査する (`tools/codex_reasoning_ab.py:11480-11516`, `tools/codex_reasoning_ab.py:11528-11539`)。
- reveal 後の aggregate では、各 slot の `benchmark_task_id` に対応する **task-specific 集合**でも再検査する (`tools/codex_reasoning_ab.py:10175-10184`)。
- `known_finding_ids` 自体を schedule row や verdict row へ複製してはいない。task manifest digest で同一 manifest に間接束縛している。

未登録面の全件検索結果は次のとおり。

- `oracle_manifest` / `oracle-manifest` / `oracle manifest`: 0 件。
- `oracle_ledger` / `oracle-ledger` / `oracle ledger`: 0 件。
- `oracle_manifest_sha256`: 0 件。
- task manifest task から `acceptance` を読む `task.get(...)` / `task[...]`: 0 件。
- `snapshot_oracle_sha256` は `tools/codex_reasoning_ab.py:3775` にあるが、これは snapshot oracle の hash であり、独立 oracle manifest の hash 契約ではない。
- task acceptance は stage2 で exact に `unbound`、fix/routing eligibility は false (`tools/codex_reasoning_ab.py:4651-4657`)。stage5 も同じ (`tools/codex_reasoning_ab.py:6241-6249`)。

したがって未登録なのは、独立 oracle ledger、task 固有 acceptance、独立 oracle manifest、oracle manifest 自身の hash 契約。現行 task manifest の digest が `oracle_kind` と `known_finding_ids` を間接的に束縛することと、独立 oracle manifest が存在することは区別すべき。

## 変更面 A1〜A12

### A1

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:178`

> **CLI 未接続**。schema v3 の task manifest 層は存在するが、既定値は T-181 の POS/NEG 固定のままで、CLI に task-manifest 入力が無い

- 実装側: task manifest の validation/load/digest は `tools/codex_reasoning_ab.py:2591-2750`。schedule cardinality と finding 集合は manifest から導出する (`tools/codex_reasoning_ab.py:2962-3042`)。CLI call site は Q1 の10件。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> **実装済み**。schema v3 の外部 task manifest は10 verb の `--task-manifest` から読み込まれ、task/arm cardinality と task 別 known finding 集合を manifest 由来で検査する。canonical digest は snapshot、prompt、schedule/run、material、packet、verdict 系へ伝播する。

### A2

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:183`

> **内部 API のみ**。外部 task manifest を受け取らず既定値で検査する

- 実装側: `supervise-pair` に option があり (`tools/codex_reasoning_ab.py:11911-11923`)、`main` も manifest を渡す (`tools/codex_reasoning_ab.py:12113-12127`)。schedule digest を exact 検査し (`tools/codex_reasoning_ab.py:7420-7431`)、予約・完了 ledger と返却値へ同じ digest を記録する (`tools/codex_reasoning_ab.py:7498-7510`, `tools/codex_reasoning_ab.py:7668-7675`)。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> **実装済み**。`supervise-pair` は `--task-manifest` を受け、schedule の canonical digest を exact 検査し、attempt ledger、launch/completion、返却 receipt を同じ digest に束縛する。

### A3

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:186`

> **CLI 未接続**。上の task manifest 行と同じ理由

- 実装側: `render-prompt` は外部 manifest を task 入力決定に使う (`tools/codex_reasoning_ab.py:3461-3535`, `tools/codex_reasoning_ab.py:12060-12072`)。一方、standalone `verify-snapshot` は option が無く、manifest も渡さない (`tools/codex_reasoning_ab.py:11864-11867`, `tools/codex_reasoning_ab.py:12054-12058`)。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。「prompt producer 未接続」という前案は採らない。

文案:

> **部分実装**。build、prompt、run、supervisor、aggregate/verify、packet/verdict 系の現行 consumer は外部 task manifest の CLI に接続され、`render-prompt` も task provenance と snapshot 入力を manifest から決定する。ただし standalone `verify-snapshot` は `--task-manifest` を持たず、task 入力処理層の CLI 閉包は未完成である。

### A4

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:189`

> **実装済み**。price version も集計軸に入る。ただし**費用の正規化計算は未実装**であり、version の束縛と cost 計算は別物である

- 実装側: cost calculator は `tools/codex_reasoning_ab.py:9659-9882`、aggregate 接続は `tools/codex_reasoning_ab.py:10105-10136`。per-run と軸別の出力先は `tools/codex_reasoning_ab.py:10383-10425`, `tools/codex_reasoning_ab.py:10530-10531`。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> **部分実装**。凍結 price version、bound schedule descriptor、観測可能な token 数を用いる部分正規化 cost を run/attempt ごとと軸別に生成する。cache write は未計上で、`coverage_status=partial`、`certification_status=not-certified` であり、費用 field は certified field、resource gate、overall のいずれにも接続していない。

### A5

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:190`

> **実装済み**。非 null price が実在する schedule では、凍結 version の文字列が本文にあれば packet 公開前に fail-closed で止める。なお **schedule descriptor を持たない legacy 互換経路が残っており、この経路は price 束縛も一様性検査も通らない (uncertified)**

- 実装側: packet-source manifest の digest 要求は `tools/codex_reasoning_ab.py:11292-11299`。欠落 artifact の明示的拒否は `tools/codex_reasoning_ab.py:2738-2749`。scheduleless 分岐はその後にある (`tools/codex_reasoning_ab.py:11307-11357`)。
- 判定: 主機構は一致するが、「legacy 互換」は既存 bytes まで互換と読めるため、全体として **(c) 実態より高い**。
- 差し替え: 要。「追記」より、`legacy 互換` という語自体を限定する。

文案:

> **実装済み**。非 null price が実在する schedule では、凍結 version の文字列が本文にあれば packet 公開前に fail-closed で止める。schedule descriptor を持たない経路は残るが、この経路も packet-source manifest の task manifest digest を必須とするため、digest 無しの既存 legacy artifact との byte-level 後方互換はなく、利用には再生成が必要である。scheduleless 経路は price 束縛も一様性検査も通らず uncertified のままである。

### A6

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:194-195`

> **表の到達度は price component の wiring を除いて 2026-08-25 時点のものであり、  
> 「全機能が完了した」という主張ではない。**

- 実装側: manifest CLI、費用計算、packet digest の現行実装は Q1、Q3、Q4 の各アンカーで確認できる。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> **表の到達度は 2026-08-27 の静的実測へ更新した。部分実装および未束縛と明記した面を含み、「全機能が完了した」という主張ではない。**

### A7

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:232-236`

> **task-specific oracle manifest**: T-181 装置は `KNOWN_FINDINGS` を固定集合として前提にしており  
> (`:167-170`)、verdict validator もその集合以外の `equivalent_to` を拒否する (`:5753-5790`、  
> 段3所見 B7)。task ごとの oracle finding ID、positive/negative control、reader agreement、  
> task-stage-model 別 numerator/denominator を schema 化し、`_validate_schedule`、  
> `_load_adjudication`、`_aggregate_verified` 全体で hash と件数を束縛する。

- 実装側: `oracle_kind` は schedule と aggregate 軸へ伝播する (`tools/codex_reasoning_ab.py:9069-9087`, `tools/codex_reasoning_ab.py:10151-10218`)。finding ID は blind verdict では全 manifest union、aggregate では task-specific 集合を使う (`tools/codex_reasoning_ab.py:11506-11516`, `tools/codex_reasoning_ab.py:10179-10184`)。
- 判定: **(a) 実態より低い**。ただし独立 oracle manifest が着地したわけではない。
- 差し替え: 要。§5.3 既存語彙で限定する。

文案:

> **task-specific oracle manifest**: 現行 task manifest 内の oracle contract については **機構は着地**している。`oracle_kind` は normalized schedule、run/attempt、aggregate 軸へ伝播し、`known_finding_ids` は blind verdict 時には manifest-wide union、mapping reveal 後の aggregate では task-specific 集合として検査され、task manifest digest に束縛される。一方、独立 oracle ledger、task 固有 acceptance、独立 oracle manifest とその hash 契約は **task 固有契約は未登録**であり、acceptance は **acceptance 未束縛**のままである。機構全体を実装済みとは呼ばない。

### A8

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:238`

> - task ごとの snapshot、prompt、oracle manifest の hash 固定

- 実装側: snapshot oracle は task manifest digest を持つ (`tools/codex_reasoning_ab.py:3376-3398`)。外部 manifest prompt は同 digest の snapshot oracle を要求し、prompt receipt に digest を残す (`tools/codex_reasoning_ab.py:3465-3478`, `tools/codex_reasoning_ab.py:3539-3555`)。独立 oracle manifest hash は全件検索 0 件。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> - task ごとの snapshot と prompt の hash 固定、および task manifest provenance pin は **機構は着地**。独立 oracle manifest とその固有 hash 契約は **task 固有契約は未登録**。

### A9

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:241`

> - price snapshot の保存

- 実装側: parser は保存済み bytes から artifact を生成・検査する (`tools/t189_price_snapshot.py:462-562`, `tools/t189_price_snapshot.py:650-762`)。装置は固定 path/digest/version と実 bytes を読む (`tools/codex_reasoning_ab.py:96-105`, `tools/codex_reasoning_ab.py:8890-8940`)。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> - price snapshot の保存、parser、schedule/aggregate への接続は **機構は着地**。登録世代 lock と完全費用に必要な cache-write 数量 receipt は未完了。

### A10

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:644-646`

> - **費用の正規化計算は未実装である。** version を束縛したことと、SKU 単価を使って  
>   cost を計算することは別である。集計は price version を軸として持つが、  
>   正規化 cost の値は生成しない。

- 実装側: Q3 のとおり `_normalized_cost_for_attempt` と軸別集計が接続済み (`tools/codex_reasoning_ab.py:9711-9882`, `tools/codex_reasoning_ab.py:10118-10136`)。
- 判定: **(a) 実態より低い**。
- 差し替え: 要。

文案:

> - **price binding に加え、部分正規化 cost の計算器を接続した。** bound schedule descriptor があり、凍結 price version と token 数を検査できる run について、Decimal を用いて run/attempt ごとと軸別の値を生成する。cache write は未計上で、`coverage_status=partial`、`certification_status=not-certified` とする。費用 field は certified field、resource gate、overall に接続していない。

### A11

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:657`

> 1. 比較可能性のため、全 run の正規化 cost は開始時に凍結した price version で計算する。

- 実装側: token 観測不能時は `unavailable`、prelaunch 等は `not-incurred` (`tools/codex_reasoning_ab.py:9613-9656`)。両者は金額に入れず、状態別件数と scheduled count を残す (`tools/codex_reasoning_ab.py:9867-9881`)。
- 判定: **(c) 実態より高い**。「全 run に金額が存在する」とは保証していない。
- 差し替え: 要。D932 の射影された裁定文を超えない。

文案:

> 1. 比較可能性のため、token が観測可能な run の部分正規化 cost は開始時に凍結した price version で計算する。`unavailable` と `not-incurred` は金額および観測可能 run の `attempt_count` に入れず、`scheduled_attempt_count`、`unavailable_count`、`not_incurred_count` を機械可読で残す。

### A12

- 文書側: `docs/phase3-t189-model-routing-preregistration.md:612-613`

> - **価格が不明な token category は「キャッシュ書込」である。**  
>   receipt にこれへ対応する記録項目が存在しないため、`unknown_token_categories` に載せてある。

- 実装側: cache-write の単価自体は price schema に存在するが、receipt mapping は field 空、operation `None` (`tools/t189_price_snapshot.py:50-51`, `tools/t189_price_snapshot.py:81-98`)。正規 receipt が保存するのは input/cached/output/reasoning の4 fieldだけ (`tools/codex_reasoning_ab.py:8462-8472`) で、計算器は cache-write を skip する (`tools/codex_reasoning_ab.py:9754-9764`)。
- 判定: **(a) 実態より低い**。不明なのは単価ではなく数量。
- 差し替え: 要。

文案:

> - **数量が不明な token category は「キャッシュ書込」である。** 単価は snapshot に存在するが、正規 receipt が `cache_write_input_tokens` を保存しないため、その金額を計算できない。したがって `unknown_token_categories` に載せ、部分正規化 cost では未計上とする。

## 親の裁定への反対意見

### P1

**賛成。** A3 と A4 は「内部 API のみ」「CLI 未接続」「実装済み」のいずれか一語では正確に表せない。

`docs/phase3-t189-model-routing-preregistration.md:168-173` に次を追加するのが安全。

> - **部分実装** — 同じ表行が表す変更閉包の一部は着地したが、未接続面または未登録契約が残り、行全体を **実装済み** と呼ぶ条件を満たさない。

A1/A2 は実装済み、A3/A4 は部分実装と分ければ、到達度を上げすぎない。

### P2

**限定付きで賛成だが、「oracle manifest が部分着地」という主語には反対。**

コード上、独立 oracle manifest は存在しない。着地したのは **task manifest 内の `oracle_kind` / `known_finding_ids` とその consumer** である。したがって §5.3 の既存語彙を使い、

- task manifest 内の伝播は「機構は着地」
- 独立 oracle manifest/ledger/hash は「task 固有契約は未登録」
- acceptance は「acceptance 未束縛」

と分解すべき。「task-specific oracle manifest: 部分着地」だけでは独立 artifact 自体が存在するように読める。

### P3

**賛成。** 射影された brief にある D932 は、部分被覆費用を記述統計に限定し、certified field/gate にせず、観測不能試行を黙って落とさず内訳を機械可読に出す、としている。

A11 文案は、

- 観測可能 run だけ金額計算
- 凍結 version を使用
- `unavailable` / `not-incurred` を件数として残す
- gate/certification へ昇格しない

という範囲なので、その線引きを守れる。

ただし `docs/decisions.md` 自体は本 dispatch の射影対象外だったため、親は執筆前に D932 正本と逐語照合すること。§10 のそれ以外の意味規則は触らない。

## scope 外の所見

別 wave または既裁定待ちとして残すもの:

- `_load_adjudication` の task-specific oracle 対応。現状は blind verdict で manifest-wide union を使い、task-specific 再検査は aggregate 側で行う。
- standalone `verify-snapshot` の外部 task manifest CLI 接続。
- 独立 oracle ledger、独立 oracle manifest、その固有 hash 契約。
- task 固有 acceptance。stage2/stage5 は現行 `unbound` 固定。
- cache-write 数量を保存する receipt field。
- 費用を certified field、resource gate、overall reader に接続すること。
- receipt schema の新世代、`SCHEMA_VERSION` の世代区別と移行契約。
- §11.2 / §12 / §13 の改訂。

本 wave ではいずれもコード変更として提案せず、文書に未登録・未接続として正直に残す。

## 総括

静的検査の結論は次のとおり。

- `--task-manifest` は10 verbに接続済み。
- `render-prompt` は task 入力決定にも外部 manifest を使う。前案の provenance-only 説は誤り。
- 部分正規化 cost は per-run/attempt と軸別の双方で実装済みだが、cache write 未計上、partial、not-certified、gate 未接続。
- scheduleless packet 経路は残るが、digest 無し legacy artifact の byte-level 後方互換は失われた。
- oracle fields の consumer は部分着地しているが、独立 oracle manifest/ledger/hash と task acceptance は未登録。

安全な判定は A1/A2/A3/A4/A6/A7/A8/A9/A10/A12 が「実態より低い」、A5/A11 が「実態より高い」。pytest や runtime 実走は行っておらず、結論は指定ファイルの静的な全件検索と実行経路読解による。