静的レビューのみを実施し、テストは走らせていない。結論は **NO-GO** である。

## 裁定 §1 の13項目トレーサビリティ

|#|実装箇所|判定|
|---|---|---|
|1 `effective_at(C)`|`orchestrator/campaign/s8c_preregistration.py:742-775,1237-1300`|△ 文書・artifact は C の blob だが、公開 `registry=` と live core が迂回路|
|2 保護範囲拡張|同 `:151-159,650-696,946-959`|△ 対象は入るが、意味を潰す正規化あり|
|3 canonical policy block|`docs/phase3-8c-preregistration.md:132-159`、core `:665-686`|○ §6 本文として hash 対象。ただし所見7の迂回あり|
|4 gN ruling 実在検査|core `:968-995,1121-1129`|× 台帳中の字面検索に留まり、実在する人間裁定を検証しない|
|5 C11 compliance|evidence `:509-552`|× no-op と文字列だけで SATISFIED にできる|
|6 pre-run evidence 原則|core `:103-108,1273-1279`、evidence `:599-640`|△ false status は閉じるが、6述語は永久 undefined、残りは構文 token 検査|
|7 evaluator hash/meta-test|core `:188-197,1246-1248,1280-1289`、predicate test `:366-396`|△ field はあるが、実際に使った injected registry と無関係な hash を載せられる|
|8 commit blob 評価|evidence `:373-389`、core `:1187-1234`|△ default module は照合するが `registry=` と dirty core は無照合|
|9 merge 遷移|core `:962-965,1083-1111`|○ コードは存在。negative control は遷移箇所を単独検査していない|
|10 `LIVING_DOCS`|`tools/check_docs.py:33-68`、invariant test `:150-178`|○|
|11 capability probing|evidence `:599-640`|△ 不在は undefined だが、機構が現れても同じく undefined|
|12 compact contract + 実 artifact scan|predicate test `:169-175`、invariant test `:109-127`|△ scan は実装、brief の理由は旧文面のまま|
|13 DW-O09 key/role 検索|`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:46-49`|× path 検索と FROZEN_MANIFEST しか記録されていない|

## 所見

### 1. `effective_at(C)` は C の blob だけで決まらない

**主張:** 公開 API の `registry=` に任意評価器を渡せるうえ、conjunction・正規化・freeze 判定を行う core module 自身も C の bytes と照合されない。

**根拠:** `orchestrator/campaign/s8c_preregistration.py:1237-1272,1293-1300`。module hash は `:1246-1248,1288` で常に C の evidence module を記録するが、injected registry が実際の評価器でもその hash との関係を検査しない。テスト用 `_Registry` は全件任意 status・証拠空である (`orchestrator/tests/test_s8c_preregistration_core.py:164-173`)。評価器 blob のない repository でも、この registry で effective object を得るテストがある (`:524-532`)。

**具体的な攻撃手順:** 有効な g1 と canonical JSON で埋めた §5 を持つ C を作り、12件の `PredicateResult(..., SATISFIED, ..., [])` を返す registry を `effective_at(repo, C, registry=...)` へ渡す。未実装の全機構を迂回して capability が返る。別経路では core の `all` を dirty worktree で `any` に変える。evidence module は clean のままなので blob 照合を通る。

**重大度:** blocker

**成果物影響:** 未充足 C を指す trial が正式受理集合へ入り、certified 選択・材料レポート・試行台帳が「発効済み事前登録」を偽って参照する。

**提案修正:** production API から registry 注入を除去する。core と predicate evaluator の双方を immutable な実行 bundle に束縛し、report には実際に実行した両 module の hash を載せる。テスト注入は production entrypoint と別関数に隔離する。

### 2. machine-checkable 6述語は対象機構なしで SATISFIED になる

**主張:** 評価は import/data-flow/control-flow/consumer semantics ではなく、関数名・文字列・整数の AST 出現検査である。証拠契約の `field_paths`、`reachable_from`、`consumer_requirement` は parse 後に使われない (`s8c_preregistration_evidence.py:191-263,643-700`)。

**根拠と反例:**

|述語|根拠|SATISFIED にできる反例|
|---|---|---|
|C01|evidence `:409-432`、fixture `test_s8c_preregistration_predicates.py:178-197`|未 import の `load_ratified_freeze` と定数を置くだけ。fixture は実行時 NameError でも green|
|C04|evidence `:435-445`、fixture `:199-211`|local no-op の停止関数を呼び、別 module に未接続 no-op を置く|
|C09|evidence `:448-460`、fixture `:213-227`|no-op 呼出しと `"no-build"` / `"certifying"` 文字列だけ|
|C10|evidence `:481-495`、fixture `:229-246`|field 名 tuple と no-op verifier だけ|
|C11|evidence `:509-552`、fixture `:248-263`|検証・critic を no-op にし、hash field 名を文字列として置く。実 generation loop は不要|
|C12|evidence `:555-583`、fixture `:265-284`|本物の env/guard/reservation を import せず、同名 local 関数と属性を置く|

さらに `read_blob_at()` は object type `blob` しか見ず tree mode を検査しない (`s8c_preregistration.py:751-765`)。mode 120000 の symlink blobに短い decoy Python を格納しても AST 証拠になり得る。

**具体的な攻撃手順:** 各 “GREEN” fixture と同形の no-op module を commit し、残る6述語だけを将来実装する。上記6件は実機構なしで SATISFIED となり、全 conjunction が成立する。

**重大度:** blocker

**成果物影響:** crash 全体停止、Layer 3、cross-binding、critic 還流、環境隔離を実施しない trial が受理され、試行台帳の受理集合と certified variant が変わる。

**提案修正:** production import の exact symbol binding、実 sink までのデータ束縛、拒否分岐を検査する。静的に証明できない述語は SATISFIED にせず、production entrypoint を対象とする end-to-end control が揃うまで undefined のままにする。

### 3. freeze namespace が契約自身の必須 artifact を拒否する

**主張:** `output/s8c-preregistration/` 配下は generation record 以外を一律拒否する一方、証拠契約は同じ directory に manifest・schedule・sample plan・cap-lift を要求する。

**根拠:** namespace 拒否は `s8c_preregistration.py:883-894`。競合する必須 path は evidence contract `:79,158,398,410`。

**具体的な反例:** `output/s8c-preregistration/trial-manifest.v1.json` を正しく commit するだけで `_history_namespace_paths()` が `freeze-namespace-unknown` を返す。schedule、sample-plan、cap-lift も同じである。

**重大度:** blocker

**成果物影響:** C03/C05/C11 を完成させるほど freeze が false となり、正式6セルの受理集合が永久に空になる。

**提案修正:** generation ledger を専用 subdirectory に分離し、その namespace だけを閉じる。運用 artifact の exact allowlist と freeze record の immutable 履歴検査を混同しない。

### 4. gN の「人間 ruling」は任意文字列で偽造できる

**主張:** 実装は ruling record を parse せず、任意の `docs/archive/*`・decisions・worklog 中に ID の字面があれば受理する。

**根拠:** `_RULING_RE` は任意の `T-N` / `DN` を許す (`s8c_preregistration.py:49`)。検査は境界付き substring search のみ (`:968-995`)。テスト自身も revision と同じ commit で `T-999 permits...` を追記して正例にしている (`test_s8c_preregistration_core.py:138-161,309-315`)。

**具体的な攻撃手順:** 条件を弱める g2 と同じ commit で `docs/archive/x.md` に `T-999 denied` と書き、record の `ruling_reference` を `T-999` にする。肯定・否定、record 型、人間裁定かを見ないため通る。

**重大度:** blocker

**成果物影響:** 無権限の条件緩和で Layer 3 や停止規則を外した trial が受理集合へ入り、材料レポートの proof chain が偽になる。

**提案修正:** canonical ledger の閉じた record schema、裁定 status、対象契約、許可された authority/provenance を構造検査する。任意 archive path と自由文検索を authority にしない。

### 5. `EffectivePreregistration` は sealed capability ではない

**主張:** factory と report が公開 Python object であり、seal は容易に迂回できる。

**根拠:** `ActivationReport` は公開 dataclass (`s8c_preregistration.py:187-197`)、factory `_construct_effective` も module global (`:200-238`)。`__new__` は `report.effective` しか整合検査しない (`:208-213`)。テストは capability 自身への `dataclasses.replace` と通常代入しか試さない (`test_s8c_preregistration_core.py:544-555`)。

**具体的な攻撃手順:**

```python
forged = dataclasses.replace(report, effective=True)
cap = M._construct_effective(forged)
```

または `object.__new__(M.EffectivePreregistration)` と `object.__setattr__` で `_report` を設定できる。global `ActivationReport` の差し替えも `isinstance` の基準を変える。copy/pickle の素の挙動に依存せず偽造可能である。さらに `PredicateResult.evidence` は mutable list (`s8c_preregistration.py:117-123`) で、封印後の証拠も改変できる。

**重大度:** blocker

**成果物影響:** arbitrary commit を持つ偽 capability が launch/acceptance に渡り、trial registry と材料レポートの事前登録参照を捏造できる。

**提案修正:** Python 型を信頼境界にしない。consumer が C と report digest を毎回再検証し、factory object 単独を authority として受け取らない。証拠集合も tuple 化する。

### 6. §5 は `null` や JSON 化した「未記入」を FILLED と判定する

**主張:** 欄ごとの型・非空・意味・artifact binding は検査せず、canonical JSON ならすべて FILLED である。

**根拠:** `_classify_section5_value()` は canonical JSON 一致だけで FILLED を返す (`s8c_preregistration.py:585-604`)。発効式は全 finding が FILLED かしか見ない (`:1273-1279`)。テストは plain placeholder と arbitrary text のみ (`test_s8c_preregistration_core.py:297-306`)。

**具体的な攻撃手順:** 9欄すべてを code span の `` `null` ``、`` `""` ``、または `` `"未記入"` `` で埋める。budget、floor、manifest、責任者が存在しなくても all_filled になる。

**重大度:** blocker

**成果物影響:** floor・予算・6セル集合が未定の C を発効扱いでき、judge の値、試行台帳の母集団、certified 選択が結果適合的に変わる。

**提案修正:** 9欄の versioned typed schema、非空制約、範囲制約、manifest/floor/schedule bytes hash との一致を検査する。placeholder 相当の JSON string/null/empty container を拒否する。

### 7. 正規化が規範上の意味差を消す

**主張:** H2 見出しの文言と code fence 対 prose の差が protected hash に入らない。

**根拠:** section slice は H2 自身の次行から始まる (`s8c_preregistration.py:460-494`)。正規化は fence delimiter を捨て、全 whitespace を一空白へ潰す (`:421-452`)。テストは見出し改名を明示的に許す (`test_s8c_preregistration_core.py:192-202`)。

**具体的な攻撃手順:** `## 4. 8c 固有の事項` を `## 4. 参考資料（非規範）` に変更する。または発効ポリシーや§7の規則本文を空 info-string の fenced code block で囲み、「規範」から「コード例」に変える。本文 token は同じなので hash は不変で gN が不要になる。

**重大度:** blocker

**成果物影響:** 停止規則・全件報告・発効ポリシーの規範性を同一 generation のまま変え、試行台帳の包含集合と材料レポートの主張を変更できる。

**提案修正:** Markdown AST の node kind、H2/H3 title、list/paragraph/code の区別を canonical form に保持する。layout-only control と semantic-node-kind control を分離する。

### 8. C02/C03/C05/C06/C07/C08 は機構完成後も green にならない

**主張:** 6述語は artifact を読むだけで、無条件に `EVIDENCE_UNDEFINED` を返す。

**根拠:** `s8c_preregistration_evidence.py:599-640`。契約も該当6件を `machine_checkable:false` としている (`evidence_contract...json:71,114,191,228,264,300`)。

**具体的な反例:** 完全な trial registry、manifest、schedule consumer、budget consumer、floor judge、prereg binding を commit しても、C02等は reason codeが変わるだけで status は常に undefined である。

**重大度:** must-fix

**成果物影響:** 正式機構が完成しても発効集合が空のままで、certified 選択・材料レポート・試行台帳に正式8c trialを一件も載せられない。

**提案修正:** 本 land を「activation scaffolding」に明確に降格するか、6件の completion-sensitive evaluator と各 negative control を揃えてから発効判定層を名乗る。

### 9. 事前登録した mutation m01 と m14 をテストが kill しない

**主張:** `all`→`any` の最重要変異に混合 status fixture がなく、merge control も別の早期拒否理由で赤になる。

**根拠:** m01 の期待テストは裁定 `s4-ruling.md:73`。実テストは12件すべて同一の非SAT statusだけ (`test_s8c_preregistration_core.py:486-501`)。全SAT正例は `:524-532`。したがって `all` を `any` にしても両方の assert は変わらない。merge 負例は異なる g2 bytes を作り、`generation-mutated` も成功理由として許す (`:408-429`)。この拒否は merge 遷移より前の core `:1017-1019` で起きる。

**具体的な攻撃手順:** core `:1276` の `all(...)` を `any(...)` に変える。全非SAT fixture は false、全SAT fixture は true のままである。merge 条件を緩めても、現 fixture は早期 `generation-mutated` で赤のままである。

**重大度:** must-fix

**成果物影響:** 一述語だけ満たす trial が正式受理集合へ入り得る。merge 側では相反する generation state を選ぶ実装変更の専用防壁がない。

**提案修正:** 11 SAT + 1 非SATを C01〜C12 全件で回す。merge は state-transition helper を切り出し、先行 guard に触れない fixture と exact reason で検査する。

### 10. negative control が無効な「green」を正解として固定している

**主張:** parameterized test は production mechanism の正例ではなく、所見2の no-op/token fixture が SATISFIED になることを要求する。

**根拠:** `test_s8c_preregistration_predicates.py:178-284,287-396`。特に `:389-392` が no-op fixture を green と断定し、負例は token 一個を置換して `not SATISFIED` だけを見る。

**具体的な反例:** C09 の正例は no-op `assert_campaign_layer3_chain()` と二文字列だけ、C10 は field 名 tuple と no-op readだけである。実 Layer 3 reportや参照 bytesを一件も検査しないのにテスト上の正解になる。

**重大度:** must-fix

**成果物影響:** 対象 consumer を実装しない token-check evaluator が検査を通り、未検証 trial が certified 選択と材料レポートへ流入する。

**提案修正:** production-shaped入口と実 sink を使い、正例でも拒否対象の改変が実際に consumer へ届くことを検査する。負例は exact reason と evidence path/hash も固定する。

### 11. 裁定項目12・13の記録要件が未反映

**主張:** 実 artifact scan は追加されたが、P3 の理由と DW-O09 key/role 検索記録は裁定どおりでない。

**根拠:** brief `:34-36` は依然「本文複製が scan を汚染しうる」を理由にする。DW-O09 は `:46-49` の path hit と FROZEN_MANIFEST だけで、query・key/role側結果・分類がない。

**具体的な反例:** role 名を key にした pin は対象 path の文字列を含まなくても成立するため、記録された検索だけでは「pinゼロ」を再現できない。

**重大度:** should

**提案修正:** compact canonical contract を理由として記載し、実行した path/key/role query、hit、real/refuted 分類を brief に残す。

### 12. 巨大履歴・timeout は構造化拒否にならない

**主張:** false acceptance ではないが、巨大入力や停止した Git に対して fail-closed reportを返さず、無期限待機またはメモリ枯渇になり得る。Rule 3 の診断も粗く潰れる。

**根拠:** Git subprocess に timeout がない (`s8c_preregistration.py:704-719`)。全履歴を保持し (`:870-880`)、commit×path の全積を一括生成する (`:897-924`)。generation 数に上限がなく `range(1,max_generation+1)` を作る (`:1006-1013`)。predicate 例外は generic `BLOB_READ_ERROR` / `evaluator-exception` へ畳まれる (`s8c_preregistration_evidence.py:686-698`、core `:1228-1234`)。

**具体的な攻撃手順:** `condition-freeze.v1.g999999999.json` を含む履歴、または巨大 commit graphを渡す。判定は受理しないが、明示的な拒否結果へ到達できない。

**重大度:** should

**提案修正:** generation・commit数・blob bytes の上限と Git timeoutを設け、超過を閉じた reason codeで返す。条件単位の原因を保持する。

shallow repository・replace refs・grafts は `s8c_preregistration.py:729-739` で拒否され、非UTF-8は `:274-304`、missing/submodule gitlink は `:751-765` で拒否側に倒れる。detached HEAD は branch を要求しないため、commit snapshotとして扱われる。F36についても freeze record 自身への self hash はなく (`:63-79`)、この点単独は裁定に適合する。

## 総括

- **判定: NO-GO**
- **blocker: 7件**
- `effective_at()` の公開 registry 注入と偽造可能な capability により、静的 readiness 層自身が correctness boundary になっていない。
- machine-checkable 6述語の green fixture は、対象機構ではなく no-op と token の存在を証明している。
- 残る6述語は永久 undefined、さらに必須 artifact を置くと freeze namespace が拒否するため、正しい実装でも発効不能である。
- 親が最初に直すべき点は、`registry=` を production API から除去し、C に束縛された評価 bundle以外から `effective` を生成できなくすること。
- その直後に、no-op green controls を廃棄し、production consumer を実際に証明する12述語へ置き換える必要がある。