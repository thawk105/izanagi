## 所見 1: 受理権威は最大 4 本で、IR admission と effect gate が二重化する

所見: プランどおり raw 候補を実 TU で conformance 確認するなら、P3 経路では 3 本、S1 `sort_best` 経路では最大 4 本の実効受理権威が立つ。

| 機構 | P3 | S1 | 判定 |
|---|---:|---:|---|
| IR admission | 有効 | 有効 | comparator-language authority |
| `_validate_single_sort_statement` | 恒真 | 恒真 | renderer 事後条件 |
| `coder_effect_gate.DENY_TABLE` | 有効 | 有効 | raw 候補を IR より先に拒否 |
| SWO oracle conformance | 有効 | 有効 | raw TU を使うなら候補拒否権を持つ |
| `sort_comparator_authority` | なし | 有効 | 15 組 exact binding |

根拠 (file:line または逐語): プランは IR を唯一の言語権威とする一方、DENY_TABLE を残す (`s2-plan.md:13-19`)。しかし現行配線は `L.quarantine()` が raw `implementation` を `scan_host_effects()` に渡して拒否した後 (`p3_s4_loop.py:326-358`)、sort oracle を呼ぶ (`p3_s4_loop_sort.py:190-220`)。T-396 の破棄理由は「同じ hole に受理権威が 2 つ並ぶ」こと (`2026-08-15_t396-hole-allowlist-refuted/README.md:24-28`)。したがって同型に当たる 2 者は、少なくとも **IR admission と `coder_effect_gate`** である。`sort_comparator_authority` は D1357 の別 domain なのでこの衝突には含めない。

成果物影響 1 行: 放置すると、同じ非 IR 候補の拒否理由と試行台帳参照が gate 順序で変わり、「IR admission 一本」という proof chain が成立しない。

推奨: 段 4 で、sort について IR admission を raw 候補の最初の意味 gate にし、effect scan は admitted 入力に対する恒真な事後確認へ移すか、sort では外すかを択一する。前段の effect gate を維持するなら「唯一の受理権威」という主張を撤回する。

## 所見 2: 旧 validator は正しく恒真化するが、SWO の一部も恒真化する

所見: `_validate_single_sort_statement` を renderer 出力だけに適用する案は正しく、候補 gate には数えられない。一方、79 IR は構造上すべて SWO なので、trusted 行列に対する公理検査も候補由来には発火しない。さらに実 TU が canonical renderer を compile するなら、行列不一致も oracle 実装故障であり `REJECT` ではなく `UNAVAILABLE` である。

根拠 (file:line または逐語): プランは renderer のみを旧 validator へ渡す (`s2-plan.md:54-56`)。また trusted 行列の SWO 違反を evaluator 故障として `UNAVAILABLE` にする (`s2-plan.md:91`)。ところが実 TU 不一致だけは `MUTATION` の `REJECT` とする (`s2-plan.md:84-89,159-160`)。現行実装は raw `statement` を候補 TU に入れる (`sort_swo_oracle.py:2786-2797`)。プランは raw 候補と renderer のどちらを compile するかを確定していない。

成果物影響 1 行: renderer を compile しながら不一致を `REJECT` にすると、oracle 自身の故障が候補 reject として試行台帳と critic に混入する。

推奨: 段 4 で compile 対象を明示する。raw admitted text を compile するなら conformance gate として役割を明記し、canonical renderer を compile するなら不一致を `UNAVAILABLE` にし、予定 node も `...is_unavailable_not_reject` に改める。

## 所見 3: 79 canonical render の実測だけでは包含の完全証明にならない

所見: 親 probe と予定 test は 79 個の canonical renderer 出力しか測っていない。プラン自身が whitespace 差を持つ raw 入力も admit するとしているため、「新受理文字列集合が現行 accepted 集合の部分集合」という一般化は未完である。

根拠 (file:line または逐語): probe は `render(ir)` の 79 値だけを旧 validator と effect gate へ渡す (`probe_narrowing.py:76-104`)。brief はそこから新受理集合全体の包含を主張する (`s1-brief.md:71-80`)。予定 test も全 renderer 値だけを見る (`s2-plan.md:147-152`) が、別 test では whitespace 差のある入力を admit する (`s2-plan.md:155-156`)。

成果物影響 1 行: 実際の受理集合が同じでも、certified 選択の「受理集合は狭まった」という proof 参照が 79 canonical bytes の測定だけでは支えられない。

推奨: 新 gate は足さず、production 文法の各 production が旧単一文条件と effect 非該当を含意することを静的に示す。raw 文法変種も build するなら、その包含命題を contract test に直接固定する。

## 所見 4: 変更が効く層の scope が不足している

所見: agent と receipt はプランに入っているが、共有 gate 順序、campaign identity の説明、critic の閉じた schema、oracle 環境 registry が不足している。

根拠 (file:line または逐語):

| 層 | 実際の波及 | 判定 |
|---|---|---|
| `.claude/agents/coder-v4-autonomous-sort.md` | raw comparator 合成から 79 IR 文法へ変わる | `s2-plan.md:56` で scope 内 |
| `p3_s4_loop.py` | effect gate が IR より先に発火する (`:326-358`) | scope 欠落 |
| `p3_s4_loop_sort.py` | oracle caller かつ `spec_content` が raw comparator 合成を名乗る (`:314-319`) | production 編集が必要 |
| `s1_direct_comparison.py` | 15 exact comparator が新 admission を通る (`:842-908`) | production 編集不要、境界実測は必要 |
| `critic/digest.py` | reason/kind が closed allowlist (`:313-338,366-409`) | scope 欠落 |
| `s8b_sort_swo_receipt.py` | current ID と保証境界を検査 (`:114-130,159-177`) | `s2-plan.md:115,141` で scope 内 |
| `s1_known_axes_freeze.py` | exact binding が IR より前に働く (`:826-858`) | D1357 により編集不要 |
| `tests/conftest.py` | 実 TU node は環境 consumer registry が必要 (`:576-606`) | scope 欠落 |

成果物影響 1 行: 放置すると campaign identity は旧 D39 実験を説明し続け、critic は新拒否を一般 anomaly に潰し、79 TU node は環境 prewarm を受けられない。

推奨: `p3_s4_loop.py`、`p3_s4_loop_sort.py`、`critic/digest.py`、`tests/conftest.py` を実装 scope に追加する。S1 と freeze はコード変更せず、15 組が同じ結果になる integration 対象に留める。

## 所見 5: critic digest は新しい admission と mismatch reason を受理できない

所見: `sort-ir.<stage>.v1` と `compiled-relation-differs-from-trusted-evaluator` は現行 critic schema に存在せず、そのままでは構造化理由が `sort-swo-oracle-finding-schema-invalid` に置換される。

根拠 (file:line または逐語): current finding の exact kind/key 集合には `mutation` が無い (`critic/digest.py:313-338`)。`structure` reason は旧 validator の 8 理由だけである (`critic/digest.py:390-399`)。未知 kind、key、reason は固定 anomaly へ落ちる (`critic/digest.py:558-590`)。プランは `test_critic.py` の ID golden には触れるが、この production schema 更新を列挙していない (`s2-plan.md:117-133`)。

成果物影響 1 行: admission reject の具体理由が材料レポートと次 iteration の critic 入力から消え、修正信号が一般 schema anomaly に化ける。

推奨: admission reason を `structure` の closed setへ追加する。TU mismatch を `REJECT` のまま採る裁定なら `mutation` keyset/reason も追加し、`UNAVAILABLE` に改めるなら critic rejection schemaへは追加しない。

## 所見 6: 変異 node は全件未実在で、1 件は変異定義が不足する

所見: プランが名指しした機構固有 node は現行 HEAD には全件存在しない。これは実装前としては自然だが、現時点では各変異の機構固有 node 数は 0 であり、KILLED と数えられない。

根拠 (file:line または逐語): 候補対応は `s2-plan.md:166-182`、F568 の規則は `F568.md:1-14`。repo 全文の exact symbol 検索では、列挙された 8 test 名はいずれも 0 hit。既存の identity churn node は独立 contract snapshot (`test_sort_swo_oracle.py:2034-2061`) と critic exact golden (`test_critic.py:98-103`) である。

| 変異 | identity churn 後の予定 node | 判定 |
|---|---|---|
| duplicate-field 拒否削除 | `test_public_oracle_rejects_non_ir_before_environment[duplicate-field]` | 実装後は固有になり得る |
| admission 呼出し迂回 | 同 `[generic-lambda]` | 「迂回後に IR をどう得るか」が未定義。単なる例外死では固有 kill にならない |
| renderer asc/desc 反転 | roundtrip node | 固有になり得る |
| signed storage | 全 79 TU node | 固有になり得るが高コスト |
| pointer rank 反転 | 全 79 TU node | 同上 |
| NUL key 切詰め | 全 79 TU node | 同上 |
| conformance 検査削除 | mismatch node | 分類裁定後に再命名が必要 |
| contract key 削除 | contract digest node | exact literal pinでなく、production key存在を独立確認すれば固有 |
| validator を raw gateへ戻す | postcondition-only node | spy が raw/canonical を区別すれば固有 |

成果物影響 1 行: このまま結果だけ集計すると、ORACLE ID が動いて落ちた node を 9 変異の検出力と誤記し、変異台帳が偽の KILLED を報告する。

推奨: 段 4 では予定名としてのみ凍結し、実装後に collected nodeid の実在を再確認する。admission bypass 変異は「generic lambda を強制的に特定 IR として扱う」など、例外死でない具体的変更へ定義し直す。

## 所見 7: D345 の contract ID 閉包は計画上閉じている

所見: D345 が要求する exact golden、ledger nodeid、`search_config` の 3 点について、未記載 consumer は見つからなかった。

根拠 (file:line または逐語): current ID の repo 内 exact literal は `test_critic.py:99-103` と `test_sort_swo_oracle.py:2055-2059` の 2 件だけで、プランは両方を更新する (`s2-plan.md:119-124`)。parametrize 展開で nodeid が変わることと ledger 更新も明記済み (`s2-plan.md:126-133`)。P3 と S1 は current 定数を `search_config` に入れる (`p3_s4_loop_sort.py:296-303`, `s1_direct_comparison.py:467-478`)。`search_config` は campaign identity preimage に含まれる (`ident.py:212-235`)。

成果物影響 1 行: 計画どおり実装すれば、旧 campaign、旧 ledger nodeid、旧 receipt を current 世代として参照する経路は残らない。

推奨: この部分は維持する。legacy v2/v3 ID は歴史 consumer なので更新せず、full JUnit 実測から ledger と exact suite set を更新する。

## 所見 8: D901 の三脚では cache 束縛だけが欠けるが、本 wave へ一般化すべき実害は未確認

所見: sort contract ID は identity と WAL 記録へ届くが、build cache identity には届かない。したがって D901 条項 2 を文字どおり sort に適用すれば未完である。ただし D901 は backoff 限定で、現時点の sort への一般化は `DW-G03` 上の新 policy になる。

根拠 (file:line または逐語): D901 は identity・WAL・cache の三脚を要求する (`decisions.md:32863-32882`)。sort は `search_config` と oracle attempt の `oracle_contract_id` に束縛される (`p3_s4_loop_sort.py:205-255,296-303`; `sort_swo_oracle.py:2939-2958`)。一方、legacy cache key は genome、commit、source token、toolchain、build admissionだけ (`buildcache.py:624-642`)、v2 も同じく contract IDを含まない (`buildcache.py:1295-1325`)。`DW-G03` は族一般化に独立 2 例を要求する (`docs/dev-wave/core.md:67-70`)。

成果物影響 1 行: 現行設計では新 oracle は build 前に再実行され、cache は同じ source bytes の binary を返すため、certified 値・受理集合・参照が変わる具体例は未確認である。

推奨: 本 waveには cache key追加を入れない。裁定パッケージには「D901 を backoff 限定のまま維持する」を推奨案として置き、全 hole grammar への一般化を選ぶ場合だけ別 task とする。

## 所見 9: D1451 の文言は満たすが、durable campaign identity の説明が旧実験のまま残る

所見: brief とプランは別実験であることを明記し、D344 を supersede したとは書いていない。この点は適合する。ただし `p3_s4_loop_sort.default_cfg().spec_content` の更新が scope に無く、実装後も raw comparator 独立合成を名乗る。

根拠 (file:line または逐語): D1451 は設計着手を許すが実験同一性論点を上書きしない (`D1451.md:3-13`)。brief は D39 の実証点が別実験へ移ると明記 (`s1-brief.md:16-19`)、プランも同じ (`s2-plan.md:7,27,56`)。一方、現行 `spec_content` は coder が comparator コードを合成すると記す (`p3_s4_loop_sort.py:314-319`)。この文字列は campaign identity preimage の一部である (`ident.py:212-218`)。

成果物影響 1 行: 放置すると新 campaign の proof chain と材料レポート参照が、実際は 79 IR 選択なのに D39 の raw C++ 独立合成実験を名乗る。

推奨: `spec_content`、CoderProposal の説明、agent 契約を同時に「閉じた 79 IR 文法を組み立てる別実験」へ更新する。D344 は元の raw 実験について有効なままと明記する。

## 所見 10: 79 TU node は focus・受入全走・3 変異走に載る

所見: プランの「受入全走から恒久除外」は現行コードと不一致である。新 node は通常の focus 走と受入全走の両方に入り、さらに evaluator 3 変異で各 79 compile が反復される。

根拠 (file:line または逐語): プランは focus と変異走を明記しつつ、受入全走では除外されるとする (`s2-plan.md:184-196`)。しかし current selection contract は `SANCTIONED_EXCLUSIONS=()` (`test_selection_contract.py:53-61`) で、runner の active table はその空集合を使う (`tools/run_tests.py:179-185`)。3 evaluator 変異はいずれも全 79 TU node を target にする (`s2-plan.md:175-177`)。さらに新 node は oracle environment registryにも未登録 (`tests/conftest.py:576-606`)。

成果物影響 1 行: 放置すると通常受入と 3 変異だけで少なくとも 316 回分の TU compile が追加され、開発所要と acceptance duration ledger が大きく変わる。

推奨: 検査範囲は維持し、79 comparator を単一 batch TUで compileして全 153,576 cellを照合する案を第一候補にする。この場合失うのは「79 値それぞれが独立の public compile/preflight/postflight を通る」保証であり、それは明記する。3 evaluator 変異は T-2113 と同じ discriminating IR 1 件ずつで killし、clean production の全 79 照合は 1 回残す。独立 compile 79 回を必須とするなら、full acceptance から外すには新しい selection policy 裁定が必要である。実測は未実行。

## 総括

(1) 実装を止めるべき所見: IR admission と effect gate の権威二重化、raw TUかrenderer TUかの未確定と誤った `REJECT` 帰属、包含完全証明の欠落、critic schemaとdurable campaign説明の取り残し。

(2) 段 4 で裁定すべき択一: effect gateをsortでは恒真化するか残して単一権威主張を撤回するか。TUはraw候補かrendererか。79検査はbatch化するか、独立79 compileを明示slow laneへ置くか。

(3) 新しい policy 選択が要る箇所: D901を全hole grammarへ一般化する場合と、79 compile nodeを受入全走から外す場合。どちらも採らなければ新policyは不要。