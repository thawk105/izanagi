## 所見 1 — 親の実測だけでは全受理集合の包含を証明していない

**所見:** 79 個の正準 render が旧 validator と effect gate を通ること、および 15 件が render 集合に含まれることだけから、`新受理集合 ⊆ 現受理集合` とは結論できない。15 件の包含は certified 互換性の証拠であって、autonomous oracle の包含証明ではない。ただし段 2 プランどおり、実候補の compile/run、全行列一致、既存の diff/auditor/effect gateをすべて残すなら、設計上の包含は成立する。

**根拠:** 親 driver が直接呼ぶのは `_validate_single_sort_statement` と `scan_host_effects` だけである (`probe_narrowing.py:76-104`)。測っていない層は、diff 検疫と materialization (`p3_s4_loop.py:313-358`)、auditor veto (`p3_s4_loop_sort.py:190-200`)、依存検証・trusted preflight/postflight・候補 compile (`sort_swo_oracle.py:2702-2881`)、broker/run・例外・呼出し回数・非決定性 (`sort_swo_oracle.py:2122-2332,2442-2483`)、production build/correctness、S1/floor consumer、receipt、試行台帳である。T-2113 の全 79 実 TU 比較も dependency manifest 検証を迂回した意味実測であり、production producer の証明ではない (`insight-t2113-liveness.md:83-92`)。段 2 自身もまだ pytest/compileを実行していない (`s2-plan.md:184-196`)。

**成果物影響 1 行:** 親 probe を全経路証明として引用すると、certified 値が不変でも、材料レポートと試行台帳が未測定の consumer 経路を「包含確認済み」と誤参照する。

**推奨:** 親実測の主張を「二つの旧 gate に対する canonical 79 個の包含」に限定する。最終包含は、プラン既定の実 TU 全件一致と public P3/S1 境界の結果が出るまで未確定とする。

## 所見 2 — evaluator 食い違いの具体条件と、拡大経路の有無

**所見:** 値取り出しには具体的な食い違い条件がある。ただし段 2 プランは実行行列との 1 cell の差も `REJECT` にするため、親 brief の「食い違えば現行 REJECT が新 PASS になる唯一の経路」は段 2 設計には当てはまらない。食い違い検査が省略または誤配線された場合にだけ拡大経路になる。

**根拠:** `storage_` は `Storage` 型で (`external/ccbench/include/op_element.hh:19`)、underlying type は `std::uint32_t` (`external/ccbench/include/workload.hh:5`)。TU も `std::uint32_t` から cast する (`sort_swo_oracle.py:718-720,1194-1202`)。したがって signed 化、幅変更、型定義 drift が食い違い条件になる。`key_` は `std::string` (`op_element.hh:20`) で、明示長つき `string_view` から構築されるため NUL も値の一部である (`sort_swo_oracle.py:1199-1202`)。NUL 終端化、Unicode 化、signed-char 順、prefix/length の誤処理が食い違い条件になる。`rcdptr_` は実 `Tuple*` (`op_element.hh:21`) で、aliases 配列の後に separate 6 個を monotonic arena から割り当てる (`sort_swo_oracle.py:817-827,1177-1198`)。null 順、aliases 内順位、separate 内順位、割当間への別 allocation 挿入、別 compiler における無関係 object pointer の `<` が具体的な条件である。特に無関係 object や null を含む built-in pointer `<` は portable C++ の全順序定理ではない。

負例 3 件は signed storage、aliases/separate のクラス逆転、NUL truncation だけを壊している (`t2113-driver-source.md:308-336`)。null 順、各 pointer クラス内の逆転、key の signed-byte/Unicode/prefix 誤読、storage 幅、production dependency 経路は検出対象外である。また三変異はいずれも別の全順序を作るので SWO のままであり、`check_relation_matrix` ではなく実 TU との一致だけが検出している。段 2 は不一致を明示的に `REJECT` とする (`s2-plan.md:78-91`)。

**成果物影響 1 行:** 一致検査が生きていれば値は certified に入らず、材料レポートと台帳には不一致が残るため、受理集合は広がらない。

**推奨:** 実行行列と trusted 行列の byte exact 一致を load-bearing 条件として扱い、負例 3 件を evaluator 一般の正しさ証明や SWO 検査の証拠とは書かない。

## 所見 3 — 行列不一致を candidate `REJECT` に帰属する択一は未解決

**所見:** 段 2 は compiled/trusted 不一致を `OracleRejectKind.MUTATION` の candidate `REJECT` にするが、不一致は candidate だけでなく evaluator、pointer mapping、compiler/TU の意味 drift でも発生する。候補帰属は D344 から自動的には導けず、段 4 で `REJECT` と `UNAVAILABLE` の択一が必要である。

**根拠:** 段 2 は不一致を `MUTATION` とする一方 (`s2-plan.md:84-91`)、trusted 行列自身の公理違反は evaluator 故障として `UNAVAILABLE` とする (`s2-plan.md:91`)。D344 は環境故障を candidate reject や fitness に混ぜず `UNAVAILABLE` に分ける (`D344.md:18-20,35-38`)。現在の S1 consumer は `oracle-reject` を即時終端にする (`s1_direct_comparison.py:738-756,1285-1293`) が、`UNAVAILABLE` は retryable とする (`s1_direct_comparison.py:958-968,1258-1269`)。したがって分類は単なる表示差ではない。

**成果物影響 1 行:** `REJECT` を放置すると certified 値は増えないが、材料レポートは trusted 側の故障を候補欠陥と記し、試行台帳は即時 `oracle-reject` で終了して candidate fitness を汚す。

**推奨:** 原因を candidate に一意帰属できない compiled/trusted 不一致は `UNAVAILABLE` とするのを推奨する。少なくとも author 開始前に段 4 で分類を確定する。

## 所見 4 — `while (true) { break; }` 反証は一般証明ではないが、具体的な拡大例もない

**所見:** nit。親の一例だけでは「挙動集合全体が不変または縮小」は証明できないが、段 2 の閉じた文法を文字どおり実装する限り、呼出し回数、例外、副作用、compile 可否による具体的な拡大例は見つからない。

**根拠:** 親の例と結論は `s1-brief.md:69-80`。新文法は `return false`、field `<`、副作用のない最大 3 field の conditional だけを受け、field 重複も拒否する (`s2-plan.md:32-54`)。関数呼出し、loop、throw、追加 statement は文法外である。さらに実 TU compile/run は残り (`s2-plan.md:78-89`)、現在の harness は comparator の二度目の全 pair 呼出し、例外、呼出し回数、abort、sandbox fault を検出する (`sort_swo_oracle.py:934-959,2273-2332`)。`while (true) { break; }` の余分な時間挙動そのものは IR に取り込まれない。

**成果物影響 1 行:** nit のため、プランどおり raw admitted statement を実 TU で実行する限り、certified 値・材料レポート・試行台帳の受理集合は変わらない。

**推奨:** 「renderer と外延同値だから安全」ではなく、「admitted raw statement 自体を compile/run し、trusted 行列と一致させるから安全」と記述する。renderer を candidate TU の代用品にしてはならない。

## 所見 5 — 79 値から certified `sort_best` 15 組への漏出は見つからない

**所見:** P1-d の分離は現在の authority と consumer 配線では保たれる。79 値 admission は oracle の comparator language であり、`sort_best` の exact name/comparator authority を置換していない。

**根拠:** authority index は `s6_sort_sweep.CANDIDATES` だけから構成され (`sort_comparator_authority.py:54-65`)、CANDIDATES は固定 15 件である (`s6_sort_sweep.py:140-160`)。known-axes freeze は生成時と検証時の両方で exact binding を要求する (`s1_known_axes_freeze.py:494-540,826-858`)。S1 measurement freeze は known-axes 文書を検証してから値をそのまま射影する (`s1_measurement_freeze.py:160-190,244-275`)。S8B holdout はその entry をコピーし、再構成値との一致を要求する (`s8b_holdout_freeze.py:774-799,1062-1126`)。floor は freeze binding を materialize し、`sort_best` に SWO PASS receipt を必須化する (`s8b_floor_campaign.py:4159-4174,4404-4451`)。段 2 も authority module と 15 件を触らないとしている (`s2-plan.md:9-19,143-164`)。

**成果物影響 1 行:** 放置しても 79 値は autonomous admission に留まり、certified `sort_best`、材料レポートの選択値、試行台帳の freeze entry は 15 組から広がらない。

**推奨:** `sort_comparator_authority` と `s6_sort_sweep.CANDIDATES` を IR domain から生成する refactor は行わず、段 2 の分離を維持する。

## 所見 6 — 79 値は trusted IR 上では全件 SWO、ただし証明の種類が変わる

**所見:** 79 値は trusted rank semantics 上ではすべて SWO である。したがって `check_relation_matrix(trusted_matrix)` は候補 gate ではなく evaluator invariant の監視となる。新 oracle は単純な強化ではなく、「候補実行行列への動的公理検査」から「構成的 SWO と実行 conformance」への別種の証明へ変わる。

**根拠:** `const_false` は空の厳密関係なので SWO。単一 field は値を厳密全順序へ写した relation の pullback であり、同値類は同一 field 値になるため SWO。相異なる field の辞書式合成も、最初に異なる field の厳密順序で決まるため、irreflexive、asymmetric、transitive、incomparability transitive を保存する。asc/desc は順序反転にすぎない。pointer も trusted evaluator 内では整数 rank なので同じ証明が成り立つ。ただし rendered C++ の無関係 object pointer `<` を corpus 外まで保証する証明ではない。

現在の `check_relation_matrix` は四公理を実行行列に適用する (`sort_swo_oracle.py:588-626,2442-2483`)。段 2 後は trusted 行列だけに適用し、破れを `UNAVAILABLE` にする (`s2-plan.md:84-91`)。現行 runbook は依然として「候補に対する有限 corpus の反例探索 gate」と主張している (`docs/phase3-s5-sort-runbook.md:190-205`)。この主張は段 2 後には load-bearing な説明ではなくなる。

**成果物影響 1 行:** certified 値は conformance により維持できるが、材料レポートの proof chain と台帳の PASS は「候補行列を公理検査した」から「構成的 SWO の trusted 行列に実行が一致した」へ参照内容が変わる。

**推奨:** `check_relation_matrix` を candidate gate に数えず、proof chain を「IR membershipによる構成的 SWO + versioned corpus 上の実 TU conformance」と記す。これは provenance 面では強くなるが、任意 C++ の動的反例探索能力は失う、という両面を明示する。

## 所見 7 — 新しい rejection を既存 critic が受理できない

**所見:** must-fix。段 2 プランは新しい `sort-ir.<stage>.v1` の structure reason と current 世代の `MUTATION/compiled-relation-differs-from-trusted-evaluator` を生成するが、既存 critic consumer の exact schema に変更が計画されていない。

**根拠:** 新 reason は `s2-plan.md:44-54,89`。一方、current critic の exact finding keysetには `mutation` 自体がなく (`orchestrator/critic/digest.py:313-338`)、current structure reason allowlist に `sort-ir.*` はない (`orchestrator/critic/digest.py:366-409`)。mutation renderer は legacy corpus snapshot 専用説明のままである (`orchestrator/critic/digest.py:1522-1524`)。段 2 が挙げる critic 変更は contract ID golden と nodeid 更新だけである (`s2-plan.md:117-133`)。

**成果物影響 1 行:** candidate は拒否されるため certified 集合は広がらないが、試行台帳の正当な finding を材料レポートが `sort-swo-oracle-finding-schema-invalid` に変え、理由と参照を失う。

**推奨:** 既存 consumer の current-generation exact keyset、reason allowlist、固定 renderer を新 producer 契約へ追随させることを段 2 の実装範囲へ入れる。新しい gate の追加ではなく、既存 producer/consumer 契約の修正である。

## 所見 8 — compiler 不在などの `UNAVAILABLE` が黙って PASS になる経路はない

**所見:** 段 2 プランをそのまま実装すれば、trusted evaluator の導入で従来の環境故障が PASS へ変わる経路はない。compiler、dependency、trusted control、broker が必要な実 TU conformance を残しているためである。

**根拠:** 現行 result 型は PASS に receipt を必須とし、UNAVAILABLE に infrastructure attribution を必須とする (`sort_swo_oracle.py:410-456`)。環境解決、required header、dependency verification、trusted preflight は candidate 実行前に fail-closed である (`sort_swo_oracle.py:2702-2784`)。段 2 は compile/run を残す (`s2-plan.md:78-89`)。P3 は UNAVAILABLE を WAL に attempt-infra として残して停止し (`p3_s4_loop_sort.py:225-234`)、S1 も PASS として扱わず retryable に分離する (`s1_direct_comparison.py:897-908,958-968`)。

**成果物影響 1 行:** compiler 不在時は certified 値も材料レポートの PASS receipt も生成されず、試行台帳には attempt-infra または retry 上限後の未完了だけが残る。

**推奨:** trusted 行列の SWO 成功だけで早期 PASS する分岐を作らず、receipt 発行を実 TU conformance 完了後に限定する。新しい policy 選択は不要である。

## 総括

(1) 実装を止めるべき所見: author 開始前に、compiled/trusted 不一致の帰属を裁定し、critic の producer/consumer 取り残しを段 2 へ戻すべきである。受理拡大そのものは、計画どおり実 TU conformance を残す限り見つからない。

(2) 段 4 で裁定すべき択一: compiled/trusted 不一致を candidate `REJECT` にするか oracle `UNAVAILABLE` にするか。原因を一意帰属できないため `UNAVAILABLE` を推奨する。

(3) 新しい policy 選択が要る箇所: 上記の不一致帰属だけ。79/15 分離、SWO-by-construction、compiler 不在の fail-closed は既存裁定から導ける。静的レビューのみで、pytest・compile・実 TU 実行は行っていない。