## 所見1 — 「実投入集合」は実際の emit や planner 利用へ束縛されず、D1429 の proof chain を満たさない

**主張:** プランが記録するのは `planner_context_payload()` の返値に組み立てた source 集合であり、emit 成功・proposal 生成・モデルへの投入のいずれにも束縛されない。

**根拠:** `plan.md:88-95` は payload 構築後、v2 受領証を発行してから context を emit する順序である。現行も出力先は任意の `--emit-planner-context PATH` であり (`p3_s4_loop.py:1941-1944`)、実書込みは `p3_s4_loop.py:2003-2009`、run 側の proposal 読込みとは hash/reference が無い (`p3_s4_loop.py:2077-2086`)。さらに現 checkout には certified-selection consumer 自体が無い (`layer3_report.py:834-838`)。

**放置時:** context 書込みが失敗した、または別入力で proposal が作られた場合でも、試行台帳と材料レポートは `injected_sources` を proof-complete と表示し、将来の certified 選択が実態のない参照を受理し得る。

**提案する最小の是正:** T-2183 内では欄を `planner_context_sources` など「構築した payload の source identities」と限定し、これだけで K2 certified 最終選択を開かない。実 emit bytes や proposal/model との束縛まで要求するなら T-2182 境界を越えるため、別タスクまたは裁定が必要である。

## 所見2 — 親 brief の「knowledge 0件だから材料レポートに記録経路がない」は誤った一般化である

**主張:** source code 上の `"knowledge"` が0件でも、材料レポートは既に WAL の `knowledge_provenance` と lock の knowledge keys を汎用欄経由で運ぶ。

**根拠:** 親の結論は `brief.md:27-34`。一方、`layer3_report.py:308-320` は全 WAL event を `variants[].events` へ payload ごと保存し、`layer3_report.py:788-806` は `workload=lock["search_config"]` として lock 全体を投影する。BUILD_START の `knowledge_provenance` は `wal.py:901-930` で lock digest と照合され、材料レポート入口の admission も `artifact_admission.py:1204-1206` で同 validator を通る。

**放置時:** 材料レポートに既に存在する値を別 top-level 欄へ重複投影し、schema・受理集合・テストだけを増やす。

**提案する最小の是正:** まず既存の `workload.knowledge_level` / `knowledge_manifest_sha256` と `variants[].events[].payload.knowledge_provenance.sources` を正式な相乗り経路として評価し、cross-field 検査と回帰テストだけを足す。consumer 利便性のため named projection が必要なら、その必要性を別に示す。

## 所見3 — 2段の正しい最小解は「knowledge level＝許可範囲、manifest/WAL sources＝投入 source」であり、2つの source 配列ではない

**主張:** 現実装には「許可された source 集合から一部を選ぶ」操作が無いため、manifest を `declared_sources`、payload を `injected_sources` とするプランは存在しない区別を作る。

**根拠:** D1429 は knowledge level を「宣言した外部取得と投入の範囲」と定義する (`d1429.md:5-16`)。現実装は全 manifest source を解決し (`knowledge_manifest.py:301-333`)、その全件を無条件に planner projection へ入れる (`knowledge_manifest.py:344-360`)。プラン自身も identity digest を同じ projection から先に作り、同じ payload から再確認するだけである (`plan.md:88-97`)。

**放置時:** 材料レポートには常に同値の `declared_sources` / `injected_sources` が二重記録される一方、将来両者が異なっても包含検査をしないため、「許可外 source が投入されたが proof-complete」という値まで表現できる。

**提案する最小の是正:** `allowed_scope = knowledge_level`、`injected_sources = 現行 manifest/WAL sources` と定義する。許可 corpus と retrieval 結果を別集合にするのは、実際に選択機構が必要になった T-2182 時点で行う。

## 所見4 — 受領証 v2 の新設は不要であり scope 超過である

**主張:** タスクは材料レポート・試行台帳・campaign identity の記録を要求しており、受領証世代の新設は本題に必要ない。

**根拠:** scope は `t2183-task.md:17-25`。既存 v1 受領証は既に level、manifest digest、canonical manifest、verified sources を保持する (`knowledge_manifest.py:400-417`)。プランはこれに並行して v2 API と schema を新設する (`plan.md:99-136`)。

**放置時:** 同じ receipt path に v1/v2 の二受理形が生まれ、WAL・replay・材料レポートが receipt version で分岐するが、記録される source identities は現在の v1 と同じである。

**提案する最小の是正:** v1 をそのまま使い、既存 `sources` を現在の投入 source 集合として試行台帳・材料レポートへ投影する。

## 所見5 — `require_receipt_v2()` は不要かつ実効性のない新規 gate である

**主張:** run 前に emit 経路の受領証を要求する条件は scope 外の新しい停止条件であり、実際の emit 成功も証明しない。

**根拠:** プランは receipt 欠落で run を停止する (`plan.md:95,108,170`)。タスクは仮想リスク向け gate の追加を明示的に除外する (`t2183-task.md:24-25`)。D1429 も初手の機械 gate 新設を却下する (`d1429.md:82-86`)。

**放置時:** 有効な manifest を持つ direct run が BUILD_START 前に新たに拒否される一方、先に残った receipt があれば context emit が失敗していても受理される。

**提案する最小の是正:** `require_receipt_v2()` を外し、run が既に解決している manifest/projection と既存 v1 receipt から従来どおり BUILD_START provenance を作る。

## 所見6 — legacy v1 campaign の材料レポート生成を一律 fail-closed にする必要はない

**主張:** D1429 が停止を要求するのは K2 certified 最終選択の主張であり、非認証の材料レポート生成そのものではない。

**根拠:** D1429 の境界は `d1429.md:39-42`。プランは v1 campaign の新レポート生成全体を拒否する (`plan.md:177,210-219`)。現行 `build_report()` は明示的に `certifying_input=false` を出す (`layer3_report.py:817-819`)。

**放置時:** 有効な既存 WAL から diagnostics 用材料レポートを作れる受理集合まで失われ、certified 選択とは無関係な成果物が生成不能になる。

**提案する最小の是正:** v1 campaign の非認証レポートは許可し、provenance の限界を明示する。拒否は `build_accepted_report()` または将来の最終選択 consumer に限定する。

## 所見7 — injected-source digest の `search_config` 追加は現在の identity に対して冗長である

**主張:** 現在は manifest source 全件がそのまま payload へ入るため、新 digest は既存 manifest digest と同じ集合を別形式で再ハッシュするだけである。

**根拠:** manifest digest は `{knowledge_level,sources}` 全体を覆う (`knowledge_manifest.py:73-81,253-260`)。それは既に `search_config` へ入り (`p3_s4_loop.py:1118-1125`)、campaign canonical preimage が全 `search_config` を覆う (`ident.py:196-223`)。プランの新 digest も同じ sources から導出される (`plan.md:61-71,88-97`)。

**放置時:** source 内容を変えず digest 欄を追加しただけで campaign ID と保存先が変わり、既存 v1 K2 campaign と新 campaign が分断される。

**提案する最小の是正:** 既存 `knowledge_manifest_sha256` を identity binding として維持する。実際に manifest と投入集合が異なる producer が導入された時点でのみ独立 digest を検討する。

## 所見8 — lock の3状態分岐と downgrade 拒否は不要な世代管理である

**主張:** unaware / legacy v1 / v2 の3状態は、不要な receipt v2 と injected digest を成立させるためだけの一般化である。

**根拠:** 現在の lock 判定は knowledge keys の両方有無だけを扱う (`wal.py:627-650`)。プランは新 digest の有無で3状態と部分集合拒否を追加する (`plan.md:140-160`)。

**放置時:** WAL replay と BUILD_START の受理形が lock 世代で分岐し、新 identity では従来の正しい3-key provenanceまで downgrade として拒否される。

**提案する最小の是正:** 現在の unaware / aware の2状態と3-key WAL provenance を維持し、材料レポート側で既存値を射影する。

## 所見9 — v3 据え置きで optional field を追加する案は mandatory provenance を schema で保証しない

**主張:** 同じ v3 literal の acceptance set を広げながら新欄を optional にすると、旧 validator は新 artifact を拒否し、新 validator は provenance 欠落 artifact を受理する。

**根拠:** プランは v3 据え置き・top-level optional を推奨する (`plan.md:5-6,191-208`)。現 schema は `additionalProperties:false` かつ v3 const である (`layer3_schema.json:5,22-27`)。

**放置時:** `knowledge_provenance` 欠落の v3 が schema-valid のまま残り、材料レポート単体では D1429 の必須 proof を判定できない。

**提案する最小の是正:** 既存 `workload` / raw WAL event を再利用するなら v3 schema を増やさない。新 top-level 欄を契約化するなら v4で required とし、v3を legacy readerとして残す。

## 所見10 — payload 本文の再hash検査は T-2182 境界を越える

**主張:** 新 extractor が `content_utf8` と SHA の一致を再検査する案は、source identity の記録ではなく「投入 bytes」の追加検証機構である。

**根拠:** プランは payload exact keys と `content_utf8` digest を検査する (`plan.md:101-105,243-246`)。タスクは実取得・投入 bytes・モデル側引用の分離を T-2182 まで先送りする (`t2183-task.md:12-13,21-22`)。

**放置時:** payload byte差による新しい拒否集合が生まれるが、emitやモデル利用への束縛は依然として無く、試行台帳の主張だけが過度に強くなる。

**提案する最小の是正:** T-2183 では既に producer が検証した source descriptor を記録するだけにし、payload bytes の再hash・delivery 証明を追加しない。

## 所見11 — 親実測のうち正しいのは個別事実であり、設計結論ではない

**主張:** `policy_hint` が scalar、knowledge keys が lock identity に入る、freeze pin が無い、という個別観測は正しいが、「相乗り不能」「実物が全く無い」まで一般化できない。

**根拠:** scalar は `layer3_schema.json:27`、lock への投入は `p3_s4_loop.py:1118-1125`、freeze manifest に材料レポート/WALが無いことは `test_frozen_artifacts.py:41-88`。一方 `workload` は実際には lock の `search_config` 全体 (`layer3_report.py:798-799`) であり、WAL event も丸ごと保存される。`brief.md:35-40` の実物確認は名前を挙げた1 campaign に限られ、指定された読み取り範囲ではその repo 外 directory を独立確認できない。

**放置時:** 既存の材料レポート・試行台帳経路を無いものとして扱い、成果物の値を変えないまま新 schema・gate・version ledger を増設する。

**提案する最小の是正:** 親 brief を「static literal は0件だが汎用投影あり」「named T-2182 campaign の runs/reports が空という観測」に限定して書き直し、その上で相乗り案を再評価する。

## 総括

1. 最も重い欠陥は、v2 receipt・WAL・材料レポートを追加しても「実際に投入した source」が emit/proposal/model に束縛されず、D1429 を満たしたように見えるだけである点。
2. 親 brief の `grep 0件 ⇒ 記録経路なし ⇒ 相乗り不能` は誤りで、既存 `workload` と raw WAL events を使う、はるかに小さい設計が成り立つ。
3. receipt v2、`require_receipt_v2()`、追加 identity digest、3状態 lock、v1 report 全拒否は一体として scope 超過であり、既存 v1 receipt・manifest digest・WAL provenanceを再利用すべきである。

pytest は実走しておらず、以上は指定資料と repo 内 consumer の静的読解による検査結果である。