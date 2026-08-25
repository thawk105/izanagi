### [B-1] 公開経路は 1 本だが、集計 helper の直呼出しは検査を迂回する

**確信度**: high

**根拠**: 事実として、`aggregate_manifest` は `verify_manifest` の単なる別名であり、両 CLI は同じ replay 経路へ収束する (`tools/codex_reasoning_ab.py:10215-10227`, `tools/codex_reasoning_ab.py:10237-10247`, `tools/codex_reasoning_ab.py:11018-11025`)。一方、`_aggregate_verified` は呼出側が渡した `verdicts` と空の `reasons` だけで `valid=true` を返せる (`tools/codex_reasoning_ab.py:9172-9180`, `tools/codex_reasoning_ab.py:9557-9561`)。既存テストもこの直呼出しを行い、`valid is True` を確認している (`orchestrator/tests/test_codex_reasoning_ab.py:10047-10056`)。repo 内の非テスト Python caller は確認できなかったが、段 2 はこの helper 自体へ認証宣言を付けるため、将来または外部の import caller にも宣言付き bypass report を作れる。

**scope 内 / scope 外**: 公開 `verify` / `aggregate` の保護は scope 内。private helper の直接利用まで certified とみなすかは親 brief の境界外なので、裁定パッケージ候補。「certified report は公開 2 API の返値だけ」と限定するか、helper の返値には宣言を付けない必要がある。

**成果物影響**: 現プランのままでは、snapshot evidence を一度も通さず `certification_scope` 付き `valid=true` report を構築できる。

### [B-2] packet 由来値を外へ出す中間経路は複数あり、1 箇所の検査では守られない

**確信度**: high

**根拠**: `make-packets` は final output bytes を packet file へコピーし、public `packet-state.json` と private custodian mapping を書く (`tools/codex_reasoning_ab.py:10331-10375`)。`append-verdicts` は packet digest を verdict log へ入れ (`tools/codex_reasoning_ab.py:10468-10518`)、`freeze-verdicts` は packet digest を凍結し (`tools/codex_reasoning_ab.py:10528-10570`)、`reveal-mapping` は packet-to-run mapping を外へ書く (`tools/codex_reasoning_ab.py:10657-10712`)。これらは全て CLI subcommand かつ import 可能な関数である (`tools/codex_reasoning_ab.py:10863-10886`, `tools/codex_reasoning_ab.py:11026-11051`)。さらに `score-run` は任意の path の bytes を直接採点でき、packet file を指定しても snapshot join は通らない (`tools/codex_reasoning_ab.py:8384-8399`, `tools/codex_reasoning_ab.py:11016-11017`)。

**scope 内 / scope 外**: 中間層への再検証追加は brief が明示的に scope 外としている (`s1-brief.md:8-10`)。したがって、これらを保護済みと装わず、「直接消費は uncertified で引用不可」とする裁定パッケージ候補。

**成果物影響**: 1 箇所の検査が守るのは公開 `verify` / `aggregate` の `valid` だけで、packet file、verdict、freeze、mapping、単独 score の値は守られない。

### [B-3] invalid report にも packet 由来の axis ledger が残る

**確信度**: high

**根拠**: aggregate 値は joined verdict から生成される (`tools/codex_reasoning_ab.py:9213-9273`)。`reasons` があれば旧 projection の `primary_judgment_ledger`、`decision`、`reader_agreement` などは `None` になる (`tools/codex_reasoning_ab.py:9507-9518`)。しかし `primary_judgment_axis_ledger`、`new_finding_axis_ledger`、`post_treatment_reliability_axis_ledger`、`reader_agreement_axis_ledger` は無条件で report に残る (`tools/codex_reasoning_ab.py:9563-9578`)。既存テストも invalid 時に旧 6 field だけを `None` と確認し、axis ledger は対象外である (`orchestrator/tests/test_codex_reasoning_ab.py:10245-10269`)。

**scope 内 / scope 外**: 宣言の意味を決める部分は scope 内。「違反を `valid=false` にする」だけなら整合するが、「未検証 snapshot 由来の値を材料 report に載せない」という意味なら現プランは不足し、後者は追加裁定が必要。

**成果物影響**: 未検証 run があれば `valid` は赤くなるが、その packet の verdict に由来する axis 集計値は report から読み取れてしまう。

### [B-4] 宣言 field は JSON namespace と既存の certified 用語を混在させている

**確信度**: high

**根拠**: 計画値の `"aggregate.valid"` は実在する JSON path ではなく、実際の key は top-level `"valid"` である (`s2-plan-out.md:48-65`, `tools/codex_reasoning_ab.py:9557-9562`)。しかも `verify` と `aggregate` は同一 object を返し、report 内に command kind は無い (`tools/codex_reasoning_ab.py:10237-10247`)。対して `"packet_state"`、`"verdict_log"`、`"revealed_map"` は manifest descriptor 名であり (`tools/codex_reasoning_ab.py:8697-8708`)、`"packet"` は artifact kind である。1 個の配列が異なる namespace を混在させている。また repo の既存 glossary は certified を「variant が workload/config の正しさゲートを通った状態」と定義しており (`docs/glossary.md:175`)、report の boolean field を certified と呼ぶ用法と衝突する。

**scope 内 / scope 外**: field shape は明確に scope 内。少なくとも report field、entrypoint、artifact kind を別 key に分け、closed-world かどうかを明記すべきである。repo 全体の certified 用語変更は scope 外の裁定パッケージ候補。

**成果物影響**: 下流 machine は `"aggregate.valid"` を JSON path として解決できず、人間は report 全体や実験 variant が certified だと誤読しうる。

### [B-5] 既存の凍結材料 report は宣言なしのまま引用され続ける

**確信度**: high

**根拠**: 現在の凍結 `aggregate.json.gz` と `verify.json.gz` は展開後 bytes が同一で、`schema_version=2`、`valid=true` だが `certification_scope` を持たない (`output/insights/2026-08-09_t181-certified-rerun/aggregate.json.gz:1`, `output/insights/2026-08-09_t181-certified-rerun/verify.json.gz:1`)。それらは今も「認証済み集計」として人間向け文書から参照される (`output/insights/2026-08-09_t181-certified-rerun/README.md:148-162`, `docs/phase3.md:1167-1176`)。erratum も `valid=true` を認証成立の根拠としている (`output/insights/2026-08-09_t181-certified-rerun/erratum-f176.md:9-14`)。

**scope 内 / scope 外**: 凍結 JSON bytes の変更は scope 外。既存 report を prospective なコード変更で救済したことにはできないため、隣接 README/sidecar で認証水準を明記するか、「新規生成 report のみ対象」と裁定するパッケージ候補。

**成果物影響**: 最も実際に引用されている材料 report は新 field の恩恵を受けず、従来どおり report 全体が certified と読める状態が残る。

### [B-6] 凍結 packet bytes と既存 canonical artifact 比較は、計画どおりなら壊れない

**確信度**: high

**根拠**: `SCHEMA_VERSION` は legacy serializer 用の 2 に固定されている (`tools/codex_reasoning_ab.py:48-54`)。packet state と private mapping はその定数と `_write_frozen_json` だけで生成される (`tools/codex_reasoning_ab.py:10358-10375`, `tools/codex_reasoning_ab.py:3319-3324`)。段 2 はこの範囲へ触れないと明記する (`s2-plan-out.md:119-120`)。snapshot oracle、receipt、score の既存 artifact 比較は canonical bytes の完全一致であり (`tools/codex_reasoning_ab.py:10023-10047`)、report-only field を追加しても比較対象 serializer へは入らない。stage2 schema が legacy `SCHEMA_VERSION` へ混入しないテストもある (`orchestrator/tests/test_codex_reasoning_ab.py:8071-8083`)。

**scope 内 / scope 外**: bytes 不変は scope 内で成立する。ただし report の shape だけを同じ `schema_version=2` のまま増やす additive-schema 方針は明文化されていない。既知の repo consumer は閉じた key set を要求していないが、report 専用 schema の要否は scope 外の裁定パッケージ候補。

**成果物影響**: packet-state、custodian mapping、snapshot/receipt/score の既存 bytes と replay 比較は変わらない。変わるのは将来の aggregate/verify report bytes だけである。

### [B-7] 既存 failure reason 契約への既知の破壊はない

**確信度**: high

**根拠**: 計画は既存 mismatch reason を削除・改名せず、membership reason を追加するだけとしている (`s2-plan-out.md:107-117`)。既存の exact `failure_reasons` assert は主に model/receipt 系であり、新検査経路とは独立している (`orchestrator/tests/test_codex_reasoning_ab.py:1323`, `orchestrator/tests/test_codex_reasoning_ab.py:1344-1346`, `orchestrator/tests/test_codex_reasoning_ab.py:1384-1386`, `orchestrator/tests/test_codex_reasoning_ab.py:1398-1400`)。必須引数化で壊れる `_load_adjudication` 直呼出しは 4 箇所あり (`orchestrator/tests/test_codex_reasoning_ab.py:11246-11248`, `orchestrator/tests/test_codex_reasoning_ab.py:11282-11284`, `orchestrator/tests/test_codex_reasoning_ab.py:11311-11313`, `orchestrator/tests/test_codex_reasoning_ab.py:11416-11418`)、段 2 は全て更新対象としている (`s2-plan-out.md:142-145`)。

**scope 内 / scope 外**: scope 内。実装時に既存理由を局所判定へ移す際、文字列だけでなく append 条件も温存する必要がある。

**成果物影響**: 計画どおりなら既存理由は残り、新理由が追加される invalid report だけ `failure_reasons` 集合が広がる。

### [B-8] `valid` の受理集合は狭まるだけで、広げる設計要素は見当たらない

**確信度**: high

**根拠**: `valid` は一貫して `not reasons` で決まる (`tools/codex_reasoning_ab.py:9557-9561`)。新 membership 条件は reason の追加だけである (`s2-plan-out.md:104-108`)。cache key を path 単独から path・descriptor SHA・case へ細分化すると cache hit は減るだけであり、成功時だけ cache へ入れる変更も失敗を隠さない (`s2-plan-out.md:75-91`)。pre/post 比較を cache miss 内から全 run へ移す変更も検査回数を増やす方向である (`s2-plan-out.md:83-87`)。宣言 field 自体は `reasons` を変更しない (`s2-plan-out.md:95-99`)。

**scope 内 / scope 外**: scope 内。静的な計画比較では monotone narrowing である。実装後は親が差分を確認すべきだが、本 consult では実走していない。

**成果物影響**: 従来赤かった manifest が緑になる経路は見つからず、同じままか、新 membership/pre-post 検査で追加的に赤くなる。

### [B-9] 事前登録の順序・判定式とは整合するが、宣言文言は実保証より強い

**確信度**: high

**根拠**: 事前登録は snapshot before/after、packet 化、freeze、mapping reveal、最後の aggregate/verify replay という順序を要求する (`docs/phase3-t189-model-routing-preregistration.md:139-153`)。計画も snapshot replay 後に `_load_adjudication` の join を行うため、この順序を変えない (`tools/codex_reasoning_ab.py:10023-10029`, `tools/codex_reasoning_ab.py:10156-10168`)。provenance 破綻を experiment evidence から外す判定とも整合する (`docs/phase3-t189-model-routing-preregistration.md:129-135`, `docs/phase3-t189-model-routing-preregistration.md:758-765`)。統計式や quality/resource gate は変更されない (`docs/phase3-t189-model-routing-preregistration.md:623-645`)。

一方、実コードが行うのは report 時点の `Path(oracle["snapshot"])` の再検証と、凍結 pre/post oracle bytes の一致確認である (`tools/codex_reasoning_ab.py:10023-10029`)。段 2 自身も「過去の run 時点を再構成せず、同じ bytes へ戻す攻撃を扱わない」と認める (`s2-plan-out.md:169-173`)。したがって `"source_run_snapshot_verified"` は、run 時点そのものが認証されたとの読みでは実保証より強い。`"mapped_final_run_snapshot_replay_verified"` 相当の限定が実態に近い。

**scope 内 / scope 外**: プロトコル整合は scope 内で問題なし。machine identifier の強さも scope 内で修正すべき。過去状態の完全証明や TOCTOU 排除は scope 外の裁定パッケージ候補。

**成果物影響**: 値や受理集合は変わらないが、現 field 名のままでは材料 report が持つ証拠能力を人間・下流 tool が過大評価する。

## 総括

- 公開 `verify` / `aggregate` は 1 本へ収束するが、宣言を `_aggregate_verified` に置くと直呼出し bypass まで certified 表示になるため、認証対象 entrypoint を裁定する必要がある。
- 中間 CLI/API、単独 score、既存凍結 report は 1 箇所の検査では守られない。再検証追加ではなく「uncertified・引用不可」の境界を裁定パッケージ化すべきである。
- invalid report に packet 由来 axis ledger を残すか、`valid=false` だけを防壁とするかを明示的に決める必要がある。
- `aggregate.valid`、artifact kind、既存 glossary の certified が衝突しているため、field namespace と closed-world semantics を確定すべきである。
- 受理集合は静的には狭まるだけで、凍結 packet bytes、既存 canonical 比較、既存 failure reason の破壊は見つからない。
- 「aggregate の valid だけが certified」は公開経路に限定すれば妥当だが、現 plan 全体では helper bypass と `"source_run_snapshot_verified"` により実装より強い表示になる。