## 所見

### F-A1

- 対象 file:line: `s2-plan.md:37-53`、`orchestrator/campaign/build_admission.py:9-20,533-558,647-709`、`orchestrator/campaign/s8b_materialization.py:73-95`
- 主張: 提案する root 非依存 descendant receipt は、元の `BuildAdmission` 本体、元 receipt の SHA、nested review receipt、issuer revision のいずれも保持しない。下流が検査できるのは自己申告 field と再計算可能な外側 SHA だけであり、「build gateway が発行した」という系譜は証明できない。既存コード自身も persistent receipt は真正な issuer を認証しないと明記している。
- 再現手順または素通り入力:

  1. 対象 cell の正しい `binding` と freeze entry を取得する。
  2. 同じ materialized source を `buildcache.build_v2` 外で直接ビルドし、binary `B` と SHA `H` を得る。
  3. current policy SHA、`review_id="s8b-floor"`、`input_sha256=binding.entry_sha256`、対象 cell、`H`、`trace=false` を持つ descendant receipt を手書きする。
  4. 外側 `receipt_sha256` を canonical JSON から再計算し、record の `binary_sha256`、`bin_hash_short`、store bytes、manifest、result、journal の `binary_sha256_at_measure` を `H` に揃える。
  5. この一式を generation `G` に載せる。全照合値は一致するため提案 validator は通る。oracle 再ビルドも同じ source から `H` を得るので `expected_perf_sha256` も通り得る。

- 成果物影響: gateway を一度も通っていない floor 測定 binary が、自己発行 receipt により manifest、result、ratified freeze、oracle の期待 hash、最終 report の参照集合へ入る。受理集合が「gateway 発行済み」ではなく「整合した JSON を作れる」に広がる。
- 重大度: blocker

### F-A2

- 対象 file:line: `orchestrator/campaign/s8b_oracle_driver.py:832-949`、`orchestrator/campaign/pipeline.py:917-932`、`orchestrator/campaign/s8b_oracle_report.py:1759-1773`、`orchestrator/campaign/s8b_oracle_judge.py:370-386`
- 主張: store bytes の検査結果は `_V2Plan` に hash 値だけ残され、実走完了後の report／judge 層では store を再読しない。pipeline の第二防壁が検査するのは再ビルドした `pf.bin_sha256` であり、store bytes ではない。限定検索では `_store_sha256(` は campaign 全体で2件、定義と oracle pre-run の呼出しだけだった。
- 再現手順または素通り入力:

  1. 正当な store bytes `B` を置き、oracle pre-run を通して `run_block` を完了させる。
  2. `run_block` 完了後、report 生成前に `out_root/rec["store_path"]` を別 bytes `X` へ差し替える。
  3. report CLI と judge CLI を実行する。
  4. 両者の `reverify_published_freeze()` は tracked floor artifact と record の hash field を再検証するが、`out_root` の store bytes は読まないため report／verdict が生成される。

- 成果物影響: report が参照する `store_path` の実 bytes は `X`、記録値と oracle 実走値は `H` という切断状態になる。型 (d) は実走直前には拒否されても、最終証拠 consumer では拒否されない。
- 重大度: blocker

### F-A3

- 対象 file:line: `s2-plan.md:45-47`、`orchestrator/campaign/buildcache.py:620-637,959-1002,1246-1248`、`orchestrator/campaign/s8b_floor_campaign.py:1366-1416,3115-3135,3172-3179`
- 主張: `BuildResult` は admission receipt や completion manifest hash を返さない。提案 issuer が sealed admission、source、実 binary hash、contract を検査しても、その binary がその admission を使った `build_v2` の出力であることは検査不能である。
- 再現手順または素通り入力:

  1. source `S` について正当な sealed `BuildAdmission` を作る。
  2. 任意 binary `X` を指し、`bin_sha256=sha256(X)`、期待 contract、正しい argv を持つ exact `BuildResult` を直接構築する。
  3. pilot または直接 `build_cells(..., build_fn=fake)` へ返す。
  4. 提案 issuer の列挙済み検査は全て通り、`X` に正規 receipt が発行される。

- 成果物影響: pilot の floor 値と manifest には、偽造 receipt ですらなく正規 issuer が発行した未 admission binary が入る。official wrapper の `build_fn` 固定は現在この入力を軽減するが、issuer 自身の契約は成立していない。
- 重大度: must-fix

### F-A4

- 対象 file:line: `s2-plan.md:37,113,131`、`orchestrator/campaign/s8b_floor_campaign.py:1485-1494`
- 主張: 型 (a) の変異は到達不能である。`"admission_receipt"` を exact key 集合へ追加した後に key を削除すると、`admission_receipt is None` 分岐より先に exact-key 検査が拒否する。
- 再現手順または素通り入力:

  1. 正当 record から `"admission_receipt"` key を削除する。
  2. `validate_portable_binary_record()` の `admission_receipt is None` を受理側へ反転する。
  3. `_validate_portable_built()` の exact-key 拒否が残るため、対象テストは依然拒否を観測し、狙った分岐を検査しない。

- 成果物影響: 型 (a) 自体は別防壁で拒否されるが、変異 matrix が新 validator の missing gate を実証したことにはならない。key 欠落と、key 存在かつ値 `None` を分離する必要がある。
- 重大度: must-fix

### F-A5

- 対象 file:line: `s2-plan.md:42,47,117,133`、`orchestrator/tests/test_s8b_ratified_verify.py:266-283`、`orchestrator/tests/s8b_v2_freeze_fixture.py:197-206`
- 主張: 型 (c) の receipt swap は、cell／binding tuple gate を削除しても独立な `subject.binary_sha256 == record.binary_sha256` や source 対応が先に拒否し得る。現行 fixture は cell ごとに異なる binary SHA を作るため、そのまま receipt を交換すると特にこの問題が出る。
- 再現手順または素通り入力:

  1. binary SHA が異なる2 cell の receipt だけを交換する。
  2. `(cell_id, holdout_id, configuration_id, entry_sha256, binding_sha256)` gate を削除する。
  3. foreign receipt の `subject.binary_sha256` が record と不一致になり、binary gate が拒否する。
  4. exact cause の差でテストを赤くしても、受理集合は依然拒否なので tuple gate の必要性には帰属しない。

- 成果物影響: cell／binding gate が消えても matrix が KILLED と見える、またはテストが拒否のまま SURVIVE する。隔離入力は、同じ configuration を持つ別 holdout など、binary、source、entry、binding を同一にし、cell／holdout だけが異なる2 receipt にする必要がある。
- 重大度: must-fix

### F-A6

- 対象 file:line: `s2-plan.md:59-65,75,80-83`、`orchestrator/campaign/s8b_floor_campaign.py:1341,3505-3519`、`orchestrator/campaign/s8b_oracle_driver.py:1175,1273-1285`、`orchestrator/campaign/artifact_admission.py:361-364`
- 主張: 「同じ current policy を全 consumer へ渡す」という値の出所がない。floor の context は `build_cells()` 内部で生成され返却されず、resume は `build_cells()` を通らない。oracle は `launch_validate()` の後で context を作るため、ratified 検査時点には policy がない。
- 再現手順または素通り入力:

  1. receipt の `policy_sha256` を任意値 `P*` に変え、外側 SHA を再計算する。
  2. consumer が artifact 内の policy を expected として再利用すれば、`P* == P*` の恒真検査になる。
  3. plan のままではこれを避ける独立 authority が指定されていない。

- 成果物影響: foreign／旧 policy receipt が resume、ratified 検査、oracle pre-run で current と誤認される可能性がある。`build_admission.py` に公開の安定 policy resolver を置き、artifact を読まずに全 consumer が再構築する設計が必要である。
- 重大度: must-fix

### F-A7

- 対象 file:line: `s2-plan.md:71-73`、`orchestrator/campaign/s8b_floor_stats.py:412-414,591-637,880-929`
- 主張: `verify_floor_artifact()` に渡る独立入力は7 scalar と cell ID 集合で、ccbench pin、contract、freeze entry、binding identity を含まない。`expected_admission_policy` だけを足しても、receipt と record の相互一致は自己申告同士の照合になる。
- 再現手順または素通り入力:

  1. valid result の1 cellについて、別の `genome_canonical`、`src_token`、`entry_sha256` を持つ internally coherent binding `B*` を作る。
  2. receipt の source と subject を `B*` に合わせ、外側 SHA を再計算する。binary SHA と journal receipt は変えない。
  3. `expected_protocol` は同じ cell ID 集合のまま渡す。
  4. verifier には正しい freeze entry がないため、`B*` が対象 freeze 由来でないことを判定できない。

- 成果物影響: standalone floor verifier は foreign binding を受理する。後段の holdout／ratified verifier が拒否しても、この層を独立 gate と呼ぶ保証は恒真になる。外部の per-cell entry／binding authority を渡すか、保証範囲を明示的に狭める必要がある。
- 重大度: must-fix

## プランの前提で誤っているもの

- `build_admission.py` を変更せず root 非依存 receipt の「元 admission 完全検証」を下流でも維持できる、は誤りである。既存 validator は full exact body と `source_root` を要求し、提案 body はその validator へ再投入できない。
- descendant receipt が「capability transfer」になる、はコード上の事実ではない。親 receipt の body も SHA もないため、単なる再記述である。
- current policy が既に全 consumer で利用可能、は誤りである。fresh build の局所変数しかなく、resume／launch validation／report reverify には届かない。
- 型 (d) の第二防壁が store を再検査する、は誤りである。pipeline が照合するのは再ビルドした perf binary である。
- `verify_floor_artifact()` が ccbench pin／freeze binding を独立検査できる、は現行引数形と食い違う。
- `"admission_receipt"` の限定検索は `orchestrator/campaign` と `orchestrator/tests` の Python 全件で0件だった。これは現行 schema に field がない証拠だが、repo 外 run directory や計算ノード store が0件である証拠ではない。
- tracked freeze に binaries がないことから schema 移行不要とは結論できない。プラン自身が repo 外の過去 run／resume artifact 件数を未確認としている。

## 変異帰属の検査

| 変異 | 判定 | 理由 |
|---|---|---|
| (a) `admission_receipt is None` を受理へ反転 | 不成立 | key 削除入力は exact-key 検査が先に拒否し、変異分岐へ到達しない。 |
| (b) subject と record の `binary_sha256` equality を削除 | 成立 | receipt は変更せず、record SHA、short hash、store path、store bytes だけを別 `H` に揃えれば、この equality が唯一の semantic 差になる。 |
| (c) cell／binding tuple equality を削除 | 不成立 | 通常の2 cell swap は binary SHA または source 差で拒否され続ける。同一 binary／source／binding で cell だけ違う入力が必要。 |
| (d) oracle の store hash mismatch 分岐を無効化 | 分岐帰属は成立、新 gate 帰属は不成立 | store を読む既存箇所はここだけなのでテストは当該既存分岐を検出する。ただし本 wave の receipt gate の検出力は何も証明しない。 |

追加で、policy や `input_sha256` を receipt 内で変更する負例は、必ず外側 `receipt_sha256` を再計算する必要がある。再計算しなければ outer SHA 検査への帰属になる。

また、自己発行した完全整合 receipt を拒否できるかという最重要変異が事前登録されていない。現設計ではその変異は拒否不能である。

## scope の抜け

- 親 admission と binary の結合層が scope 外である。`BuildResult` に validated completion manifest、親 receipt、binary record の結合証跡を運ぶ変更が必要で、`buildcache.py` を「回帰だけ」とする分割では閉じない。
- report／judge の最終 store 再検証が scope 外である。report は `output_root` を持つため再 hash 可能だが、judge は持たない。最終 store seal、report receipt、judge API のいずれを採るか裁定が必要である。
- issuer 真正性の trust root が scope 外である。署名を導入する案は `docs/phase3.md:612` の既裁定と衝突するため、必要なら再裁定パッケージにする。署名を採らないなら保証名を「自己整合 provenance」に狭める必要がある。
- current policy の公開 resolver と、その policy が新 validator／issuer revision をどう識別するかが scope 外である。
- outer manifest／result schema を据え置いたまま required nested key を追加するため、同じ schema 名に receipt 有無の非互換な2形が生じる。旧 durable artifact の拒否でよいか、schema 世代を上げるかは裁定対象である。
- `verify_floor_artifact()` を独立 gate とするなら、per-cell freeze entry、binding、ccbench pin、contract の外部 authority 追加が scope に必要である。

## 総括

- 提案の中心である descendant receipt は gateway 発行を証明せず、自己整合 JSON に留まる。
- 手書き receipt と gateway 外 build を組み合わせ、floor 値から completed oracle report まで運べる。
- store は oracle pre-run 後に差し替えると report／judge で再検査されない。
- 型 (a) は exact-key 防壁で拒否されるが、提案変異の分岐には到達しない。
- 型 (b) の binary equality 変異だけは現入力で帰属が成立する。
- 型 (c) は別の binary／source 検査が先に発火し、tuple gate の帰属が成立しない。
- 型 (d) の変異は既存 hash 防壁の回帰であり、新 receipt gate の証拠ではない。
- buildcache 結合、独立 current policy、report／judge、schema 世代が追加 scope または裁定対象である。
- F-A1 と F-A2 を閉じないまま段4で実装採用すると、規律2の新 gate を実装したという主張は成立しない。
- pytest、build、mutation は実走しておらず、以上は限定 path の静的検査結果である。