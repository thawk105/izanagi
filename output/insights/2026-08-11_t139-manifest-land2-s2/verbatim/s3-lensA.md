**NO-GO**

> read-only sandbox のため `$D/s3-lensA.md` は書き込めなかった（`test -w "$D"` は偽）。以下が同ファイルへ置く完成本文である。コード変更・テスト実行は行っていない。

## 1. GO / NO-GO 判定

**NO-GO。現行プランのまま実装・export・「§6 / §7.1 完了」の記録へ進めない。**

current blocker は 15 件。段 2 の B1〜B6 はすべて入力欠落として `real` だが、B3/B5 は producer・receipt-set consumer を持つ次 session で閉じる型であり、それ自体は本 session の blocker に数えない。B6 は本 session の完了 scope が誤っているため current blocker である。

## 2. blocker 一覧

### B1〜B6 の独立再判定

段 2 の引用行番号は全 6 件とも実文と一致した。ただし B4 は「数理契約まで存在しない」、B5 は「validator が現実の不在を証明すべき」という一般化が過大である。

#### B1 — `real` / (i) 承認済み文書の内部矛盾 / current blocker

- `record-items-v2.md:243-245` は「`CMakeCache.txt` 由来の値」を再読し、`record-items-v2.md:604-608` は configure argv / compile argv / CMakeCache の 3 者一致を要求する。
- schema の compile exact key は `receipt-schema-v1.json:97-107,137-147`、pointer は `compile_commands` だけである（同 `:128-131,168-171`）。`CMakeCache.txt` の `fileRecord` はない。
- `compile_commands.path` の sibling を推測する経路、`configure_argv` から build directory を推測する経路はいずれも承認済み grammar ではなく、具体的な再計算経路にならない。
- **成果物影響:** producer の `cmake_cache` 申告値を「実体」と誤認すれば trace/analysis build を performance build として受理できる。
- **要求:** CMakeCache raw pointer と path 関係を schema/record 契約として再発行するまで §7.1(12) を hard-stop にする。

#### B2 — `real` / (i) 承認済み文書の内部矛盾 / current blocker

- `record-items-v2.md:470-476` は create-only、上書き禁止、durable intent の全 attempt exact 被覆を要求し、同 `:581-582` は qsub 失敗 row も含む母集合との照合を要求する。
- schema が持つのは各 receipt row の `intent_ref` 一個だけである（`receipt-schema-v1.json:1095-1107,1121-1138`）。intent directory、母集合 index、O_EXCL provenance、履歴 pointer はない。
- receipt 内の「同 path・異 digest」を拒否しても、丸ごと省略された intent や、publish 前の上書きは検出できない。
- **成果物影響:** producer が不利な attempt を receipt と intent 集合の双方から省略しても exact coverage が緑になる。
- **要求:** producer 権限外または create-only namespace の authoritative intent index と履歴を契約へ追加するまで §7.1(16) を完了扱いしない。

#### B3 — `real` / (iii) 次 session の receipt-set consumer で閉じる / 本 session 単独の blocker ではない

- `record-items-v2.md:583-585` は別 stage receipt に同じ verification allocation を同じ bytes で記録させる。
- receipt schema は一 stage 一 receipt の exact top-level しか持たず（`receipt-schema-v1.json:1220-1240,1257-1300`）、peer receipt pointer はない。
- **具体的な将来経路:** persisted pilot/main receipt の両 path を受ける receipt-set consumer が、双方を独立 snapshot し、verification allocation の canonical bytes を再構成して比較する。
- **成果物影響:** receipt-local validator だけを合格させると stage 間で verification allocation を差し替えられる。
- **要求:** 本 session は local helper までに限定し、§6.1 全件完了を記録しない。peer consumer 結線を次 session の必須 acceptance にする。

#### B4 — `real` / (i) 承認済み文書の内部矛盾 / current blocker

- `record-items-v2.md:421-444` の telemetry は `receipt fileRecord` と `fixed_inputs` を持ち、validator が transcript を再計算するとする。同 `:679-684` は main の slot 数を `J` と一致させる。
- schema は transcript pointer と `{input_sha256,B_or_null,seed_or_null}` だけである（`receipt-schema-v1.json:941-955`）。transcript の byte grammar、pilot 母数との binding、権威ある `J` field はない。
- 追補 A は J の式・区間規則を与えるため「数理契約がない」は過大だが、どの raw bytes から式の入力を復元するかは依然未定義である。
- **成果物影響:** producer の `fixed_inputs.input_sha256` や `len(consumed_cluster_slots)` を J の根拠にすれば、producer が main の投入本数を選べる。
- **要求:** transcript canonical bytes、入力 receipt との参照、J の再導出規則を承認契約へ追加するまで §6.8 を hard-stop にする。

#### B5 — `real` / (iii) producer controller 側で閉じるもの / 本 session 単独の blocker ではない

- `record-items-v2.md:625-630` は観測終了から exec まで 5 秒以内かつ「他の作業・任意待機を挟まない」とする。
- schema の観測要素は stat raw、start/end、診断値等だけで（`receipt-schema-v1.json:1033-1089`）、全 event stream はない。
- §9 は producer が異なる bytes/schedule で走る偽造を検出できないと明記する（`record-items-v2.md:817-823`）。
- **具体的な将来経路:** producer controller の単一路で observation→decision→exec を直結し、validator は記録された時刻・raw の整合だけを検査する。producer 権限内の隠れた作業は承認済み残余として残る。
- **成果物影響:** validator が「他の作業がなかった」と証明したと記録すると、観測不能な実行順を certified fact に格上げする。
- **要求:** 本 session の validator verdict を「記録された窓・間隔の整合」に限定し、現実の無作業保証は次 session の controller acceptance と §9 残余へ分離する。

#### B6 — `real` / (ii) 本 session の scope 設定の誤り / current blocker

- `record-items-v2.md:654-667` は resolver・receipt validator・材料 report の 3 consumer が独立に全履歴を再走することを要求する。
- schema の exact top-level は receipt data のみで consumer/report を表現しない（`receipt-schema-v1.json:1220-1300`）。
- 親 brief は semantic validator が「§6 全件」を閉じる一方、材料 report/certified consumer を scope 外とする（`s1-brief.md:40-46`）。
- **成果物影響:** resolver/validator の 2 call だけで a13 を完了記録すると、report が現 tip の自己申告を信用する経路が残る。
- **要求:** report consumer を scope に戻す裁定、または本 session の完了主張を「§6.7(1)〜(7) helper + 2 consumers」に狭める裁定が必要。現 brief のまま実装完了とは書けない。

### BLK-01 — D291 の第 1 矢印が計画に存在しない

- **所見:** plan は D282/F_r だけを読み、`addendum_b=None` を pilot-ready、非 null を恒真 deny とする（`s2-plan.md:76-127,328-339`）。D291 が承認した `source_addendum_b` の正例を通せない。
- **根拠:** D291 は manifest 前に F_p payload の role 集合、三つ組、`document_relations` 全 field、値集合、閉包を exact 照合させる（`main:docs/decisions.md:13315-13320`）。approved role は exact 2 件（同 `:13441-13468`）。
- **成果物影響:** 正式な追補 B が解決不能な一方、D282-only binding が「pilot-ready」と表示される。
- **要求:** trusted code 内の固定 role→root 写像で D282/F_r と D291/F_p を別々に parse する replan が必要。caller/manifest に root 選択権を与えない。

### BLK-02 — 一つの flat manifest は二つの exact closure を表現できない

- **所見:** plan の manifest は D282 の triples/order/digest/boundary 一組だけである（`s2-plan.md:42-68`）。D291 の二 role allowlist、historical reject、`document_relations`、operational state の区画がない。
- **根拠:** receipt 自体も `approval_manifest` を一個しか持たない（`receipt-schema-v1.json:257-289`）。D282 は三つ組集合・erratum 順序等の exact 一致を要求する（`docs/decisions.md:12874-12879`）。D291 は approved role exact 2 件と relations 節全体の追加・削除禁止を要求する（`main:docs/decisions.md:13445-13468`）。
- **成果物影響:** flat union はどちらかの余剰 role を作り、projection を暗黙にすると caller が都合のよい closure を選べる。
- **要求:** role ごとの namespaced projection または二 manifest を正規契約として裁定する。既存 singular field を独断で umbrella manifest と解釈しない。

### BLK-03 — resolution と submission authorization が同じ object に混入する

- **所見:** plan の `pilot-ready` は identity 解決成功を投入可否へ読み替える。
- **根拠:** D291 fold 時点は `pilot_submission = forbidden` / `main_submission = forbidden` / `source_main_run_gate = not_implemented`（`main:docs/decisions.md:13470-13482`）。D292 は解除権限を canonical decision だけに限定し、manifest・wave 完了・handoff による解除を禁止する（同 `:13581-13588`）。
- **成果物影響:** 将来の submit consumer が `PreregBinding` の存在だけで投入を開始し、未完成 gate の certified 結果を作れる。
- **要求:** `PreregBinding` は identity-only とし、ready boolean/命名を持たせない。submit は別の `SubmissionAuthorization` を要求し、それは解除 decision の exact payload からのみ mint する。

### BLK-04 — B1 の申告値代用 seam

- **所見:** `_derive_compile_truth` の入力候補に、実体 pointer のない `cmake_cache` claim が残る。
- **根拠:** `s2-plan.md:257-271,357` 自身が B1 解消後と注記するが、plan 全体は semantic/writer positive を同 session で完成させる。
- **成果物影響:** `cmake_cache` claim を「CMakeCache 由来」と呼び替えた false-green が §7.1(12) の実装として記録される。
- **要求:** raw authority がなければ専用の unimplemented rejection に到達し、positive/vector/export を禁止する。

### BLK-05 — B2 の receipt-local consistency を provenance と誤認できる

- **所見:** 同じ receipt 内の同 path/異 digest 拒否は、create-only や母集合被覆を証明しない。
- **根拠:** plan も `s2-plan.md:361` で全 intent/provenance は検査不能と認める。
- **成果物影響:** 省略した attempt が一つも validator 入力へ現れず、exact coverage が恒真化する。
- **要求:** local check の reason 名・docstring・coverage ID に `create_only` / `exact_coverage` を使わず、B2 解消まで §7.1(16) coverage を missing のままにする。

### BLK-06 — B4 の `fixed_inputs` を authority にできる

- **所見:** transcript parser の grammar がないまま `input_sha256` や slot 数から J を導出できたことにする余地がある。
- **根拠:** §8 は `fixed_inputs` を producer claim と明記する（`record-items-v2.md:784-799`）。plan も authoritative source を「B4 解消後」とする（`s2-plan.md:258-269`）。
- **成果物影響:** main `consumed_cluster_slots` の許容数が producer の自己申告で動く。
- **要求:** B4 の承認済み grammar が得られるまで main-stage semantic positive を構成しない。

### BLK-07 — B3/B6 を残したまま「§6 全件」を完了できる

- **所見:** receipt-set comparison と材料 report を scope 外にしたまま、brief は semantic validator が §6 全件を担うと宣言する。
- **根拠:** `s1-brief.md:34-46`、`s2-plan.md:317-326,362,410`。
- **成果物影響:** stage 間 allocation と a13 第三 consumer が一度も検査されず、coverage index だけが完成する。
- **要求:** architecture conformance の実 consumer node まで acceptance に含める。未結線項目を data vector の対象外にして通してはならない。

### BLK-08 — 防壁の production 呼び出し元が scope にない

- **所見:** resolver、snapshot、semantic validator、writer の production sink が存在しない。現在の production 検索では T-139 の `PreregBinding` / resolver / validator 呼出しは 0 件で、各 preregistration module も「本 wave では実装しない」と記す（`orchestrator/preregistration/blobref.py:1-6` 等）。
- **根拠:** D162 は validator が persisted raw receipt path から再読し、consumer が同一呼出し内で validator を再実行することを要求する（`docs/decisions.md:8018-8029`）。plan の writer は publish 前の bytes 検査だけである（`s2-plan.md:186-210`）。
- **成果物影響:** test fixture は gate を通っても、official producer/report/certified path は旧 writerまたは未検査 pathを使い続ける。
- **要求:** 少なくとも official producer→writer と persisted path→validator→consumer の実 call edge を同じ acceptance node で固定するまで export・完了記録を禁止する。

各防壁の現状は次のとおり。

| 防壁 | 正例 | production consumer |
|---|---|---|
| D282 manifest | D282-only なら構成可 | resolver のみ。D291 後の総合正例ではない |
| D291 manifest | plan に正例なし | なし |
| Git hardening | 通常 local repo は構成可 | resolver のみ |
| resolver | `addendum_b=None` は post-D291 には誤った正例 | submit は scope 外 |
| snapshot | regular `fileRecord` は構成可 | semantic 内部だけ |
| schema | schema-only positive は構成可 | schema 適合は受理でない |
| semantic | B1/B2/B4 により完全 positive は構成不能 | writer 内部だけ |
| writer | semantic positive がないため構成不能 | official producer は scope 外 |
| a13 history | resolver/validator の 2 consumer | report が scope 外 |
| vector pin | 一根なら生成可能 | 二根 manifest が未定義 |

### BLK-09 — raw snapshot closure が pointer 全体を覆わない

- **所見:** `_load_raw_closure` は「全 `fileRecord`」だけを列挙する（`s2-plan.md:177-180`）。しかし `immutableArtifact`、`execWitness`、`performanceStartedMarker` は `fileRecord` ではない pointer shape である。
- **根拠:** `receipt-schema-v1.json:174-182,747-757,1013-1022`。`exec_witness` は actual run の必須 field（同 `:759-802`）。
- **成果物影響:** marker/exec/binary artifact を semantic code が別 path 読取または申告 digestだけで処理でき、snapshot APIを通らない。
- **要求:** schema の全 pointer-bearing shape を明示的に列挙し、全 bytes/metadata 読取を同一 SnapshotSet に閉じる。AST 禁止対象を semantic moduleだけでなく全 acceptance call graphに広げる。

TOCTOU tuple `(st_dev, st_ino, st_size, st_mtime_ns)` は `st_dev` を含むが、`st_ctime_ns`、`st_mode`、`st_nlink` を含まない（`s2-plan.md:167-173`）。全 directory fd を検査終了まで保持し、leaf の fd/path identity、mode、ctime を read 前後で照合する必要がある。

### BLK-10 — 16 MiB cap が未承認の受理集合を作る

- **所見:** plan は Git blob 用の既存 16 MiB literal を全 raw に流用する（`s2-plan.md:175`）。
- **根拠:** `fileRecord.size` は 0 以上だけで上限がない（`record-items-v2.md:119-130`、`receipt-schema-v1.json:17-25`）。
- **成果物影響:** 契約上適格な 16 MiB 超の run log/transcriptを恒真 denyし、実装都合で受理集合を狭める。
- **要求:** artifact kind 別の承認済み上限を得るか、streaming snapshot/hash/parser を設計する。既存 Git blob cap の名称共有は根拠にならない。

### BLK-11 — writer の支配点が AST heuristic と偽造可能な binding に依存する

- **所見:** caller-controlled `destination` と、T-139 literal を同じ関数で扱う場合だけ検出する AST inventory では canonical receipt namespaceを固定できない（`s2-plan.md:188-208`）。
- **根拠:** repo には既に generic writer が存在する（`tools/pegasus/dispatch_compute.py:1268-1283`、`orchestrator/qualification/atomic_publish.py:24-123`）。`PreregBinding` は Python の private seal/frozen dataclassだけでは provenanceにならない（`s2-plan.md:76-107`）。
- **成果物影響:** official producer が generic wrapper経由で別 destinationへ receipt を出せば、binding/semantic gateを一度も呼ばず publishできる。
- **要求:** canonical destination/series uniquenessを sink側で固定し、sinkが bindingのexact type、mint registry、repository/common-dir identityを再検証する。AST inventoryはliteral有無でなくofficial receipt namespaceへ到達する全writerを検査する。

同一権限の意図的な非協調 writer を完全に防げないこと自体は D282/D291 の境界内残余であり、ここでの blocker は **official call graph さえ固定されていないこと**である。

### BLK-12 — `reason_code` の正例を一意に構成できない

- **所見 1:** plan は route 3 で non-null `malformed_reason` を要求する（`s2-plan.md:247-254`）が、承認文書は「非 null **なら**一致」とするだけである（`record-items-v2.md:535-547`）。8列正常・busy範囲外は `malformed_reason=null` の正例である。
- **所見 2:** verification completed の「`actual_runs[]` は0件」（同 `:516-523`）が receipt全体か当該attemptか曖昧である。全体なら performance runを含む正常stageが通らない。
- **所見 3:** `scope=pre_run` は actual run参照必須（同 `:478-496`）だが、次 run の a03 失敗でexecしなかった場合は参照先 runが存在しない。
- **成果物影響:** valid route 3をfalse rejectする一方、失敗prefixの正規表現を実装者が独断で選ぶ。
- **要求:** route 3 条件5を逐語どおり条件付きに戻し、verification `actual_runs` の量化範囲とpre-run failure表現をcanonical erratum/裁定で確定する。

### BLK-13 — `argv_raw` から argv 配列への byte grammar がない

- **所見:** record は `argv_raw` bytes と `driver_argv[]` の exact 比較を要求する（`record-items-v2.md:618-621`）が、schema は `argv_raw=fileRecord` としか定めない（`receipt-schema-v1.json:759-802`）。
- **成果物影響:** NUL区切り、JSON、改行区切り等のparser選択で同じ raw の受理が実装ごとに動く。
- **要求:** encoding、separator、空要素、末尾、非UTF-8の扱いをfreezeするまで §7.1(13) の argv側を完了扱いしない。

### BLK-14 — vectors が複数制約を一つの負例へ束ねる

- **所見:** `wait-kind-seconds`、`window-or-exec-gap`、`busy-range-or-reobserve`、`phase-closure-or-nesting`、`phase-cap-or-signal-offset`、`pointer-size-or-hash`、`symlink-or-read-race` は一つのIDで複数制約を撃つ（`s2-plan.md:392-422`）。
- **根拠:** runner は single expected rejection を要求する（同 `:273-289`）。前段guardで落ちれば後段制約が一度も発火しない。
- **成果物影響:** coverage indexは§6全行を覆って見えるが、実際には後段guardが未実装でも緑になる。
- **要求:** leaf制約ごとに一変異・一理由のfixtureを置き、対象guardより前の全guardを通過したことをspy/assertする。architecture要件 §6.7(8) はdata vectorでなく実call nodeを固定する。

vector→index→manifest→source pin の順序自体は、一つの決定済みmanifestなら1 session内で閉じる。現在閉じない原因は循環ではなく、D291を含むmanifest表現が未裁定なことである。

### BLK-15 — canonical repository/common directory が機械的に固定されない

- **所見:** resolver の public署名はcaller supplied `repository_root` を受ける（`s2-plan.md:86-95`）。top-level repoであることだけでは「指定された一つの canonical local main」を同定しない。
- **根拠:** D282 boundary は独立clone・別 common directoryを保証外とする（`docs/decisions.md:12933-12938`）。D291も同じ限定を持つ（`main:docs/decisions.md:13503-13510`）。
- **成果物影響:**同じobjectsを持つ独立cloneでmintしたbindingがcanonical bindingと区別されず、writer/consumerが保証外receiptを承認済みとして扱う。
- **要求:** trusted canonical rootと`git-common-dir`のidentityをcaller外で固定し、bindingへ封じ、writer/consumerで再照合する。保証外cloneを単に「保証しない」と書くだけで成功bindingを返してはならない。

### §7.1 20項目の逐項監査

| # | 判定 | 所見 |
|---:|---|---|
| 1 | △ | outcome依存件数は実装可能だがBLK-12のverification outcome曖昧さに依存 |
| 2 | 可 | ordinal連番とSTART双方向はreceiptだけで再計算可能 |
| 3 | 可 | exact field集合から一意性を再計算可能 |
| 4 | 可 | a07/a08/a09は承認済み追補A bytesから逐語固定可能 |
| 5 | 可 | `36×slots` とschedule表の1:1は再導出可能 |
| 6 | 可 | role別phase閉包・capは記録値から算術可能 |
| 7 | × | `execWitness`等がsnapshot closure外（BLK-09） |
| 8 | × | route 3、verification、pre-run failureの契約が不一意（BLK-12） |
| 9 | 可 | attempt/allocation role関係はreceipt内で閉じる |
| 10 | 可 | raw grammarが固定されたproc/statについて再計算可能 |
| 11 | 可 | POSIX再正規化とGit tree再導出が可能 |
| 12 | × | CMakeCache raw pointerなし（B1） |
| 13 | × | `argv_raw` byte grammarなし（BLK-13） |
| 14 | × | pointer全体・snapshot metadata・capが未閉（BLK-09/10） |
| 15 | 可（限定） | 記録されたmonotonic順は検査可。現実の「他作業なし」は証明しない |
| 16 | × | intent母集合/create-only provenanceなし（B2） |
| 17 | △ | validator単体の履歴走査は可能、第三consumerが欠落（B6） |
| 18 | 可 | 時間予算算術と記録elapsedは再計算可能 |
| 19 | △ | D282 manifestのschema pinは検査可だがD291を含むbinding closureは未表現 |
| 20 | 可 | duplicate-key拒否付きparserで実装可能 |

§8 の `TripwireMapping` 案（`s2-plan.md:256-271`）はproseだけではないが、`_derive_authoritative_facts()` 単体ではなく最終acceptanceまでの全call graphをtripwireで包む必要がある。B1/B4未解消中に `cmake_cache` / `fixed_inputs` を読むpositiveは作れない。schema-validだけで成功を返さない旨はplanにあるが（同 `:212-234`）、実consumer不在のため防壁の発火はまだ証明されない。

### D291 追補の必答5問

1. **P6は方向として正しいが不十分。** role→rootはtrusted sourceの固定写像にし、caller/manifestに選ばせない。D291は三つ組だけでなく、2-role exact allowlist、historical reject、`document_relations`全節、approved values、operational stateまで検査する必要がある。

2. **manifest設計は変更必須。** D282 projectionとD291 projectionをnamespacedに分離しなければ、flat unionはどちらかのexact closureを壊す。`addendum_b`をmanifest外へ無断で逃がすのも第1矢印を失う。既存schemaのsingular `approval_manifest`をどう扱うかは裁定・契約再発行が必要。

3. **現RP-1のまま1 sessionへは入らない。** 既存D282 parserだけで587 production行あり、D291のnested exact parserは概算500〜800 production行＋負例を要する。ただし本質的blockerは行数でなくmanifest/schema表現の未裁定である。段4で表現を裁定し、まず二payload parserとidentity-only bindingまで、writer/export/完了宣言はconsumer結線後に切るべきである。

4. **解決成功と投入可否は別型にする。** `PreregBinding`にready状態を持たせず、submit APIはcanonical解除decisionからmintされた別authorizationを必須にする。manifest field、docstring、wave完了フラグはauthorization sourceにしない。

5. **追補の「未裁定1件」は現mainではD292により一部解消済み。** 解除権限はcanonical decisionだけに決まったが、解除条件と成立証拠は未決定である。RP-4の「公表core 3文書foldでpilot解禁」は失効しており、このsessionが実装できるのはidentity解決まで。pilot/main authorizationやsource main gateは実装してはならない。

## 3. 境界の内側と分類した残余

以下はRP-2(a)または承認済み§9の境界内であり、このsessionへの追加実装要求にはしない。

- `/usr/bin/git` の同一bytes別inode、bind mount、overlay、binary差替え、dynamic loader/shared library差替え。RP-2(a)が実行中のabsolute Gitを信頼するため残余。
- trusted Python/source、`approval_payload.py:17-21` 等のliteral、生成pin fileを協調して書き換えること。source自体のidentity束縛は明示的に境界内。
- canonical Git common directory内のrefs/object/configを同一権限actorが改変すること。resolverは毎回検査するが、common directory自体を信頼する境界である。
- generic publisherを同一権限の非協調codeが意図的に呼ぶこと。official call graphの未固定はBLK-11だが、境界外writerすべての封鎖までは要求しない。
- producerが経路3用rawを捏造すること（`record-items-v2.md:803-813`）。
- producerが実際とは異なるbytes/scheduleで走り、内部整合receiptを作ること（同 `:817-821`）。
- 台帳外投入、独立clone、別common directoryそのもの。ただしそれらにcanonicalと区別不能な成功bindingを返す部分はBLK-15であり残余扱いしない。

Git hardening項目について、PATH非継承、absolute起動、ambient `GIT_*`破棄、system/global config無効、replace/commit-graph/fsmonitor無効、alternates/promisor拒否、`--no-pager`はplanに列挙されている（`s2-plan.md:129-154`）。この集合で残る境界外の具体的accept注入は、callerがcanonical root/common-dirを選べるBLK-15である。local configの外部includeは完全には封じられていないが、現planの明示overrideを越えるfalse-accept keyは静的に特定できなかったためnitへ送る。

## 4. 親 brief・親の実測値・その一般化への所見

### `/usr/bin/git` 訂正

- 同一SHA-256は**同じbytes**を強く示すが、同じfile object、inode、mount、lower layerを示さない。byte-identical copy、bind mount、overlay上の別inodeは同じdigestを持てる。
- 本子sandboxでは `/usr/bin/git` は `uid/gid=65534/65534`、SHA-256は親記録と同じ `587ef218…` と観測した。`/proc/self/uid_map` はhost UID 31609だけをnamespace UID 0へ写しており、host rootがoverflow UID 65534に見える構成と整合する。これは**子sandbox内の観測**であり親環境のowner事実ではない。
- したがって親の `0/0` 訂正はUID namespace説明により妥当性が高いが、同一SHAだけを根拠に「同じfileを見ている」とする推論は成立しない。
- **成果物影響:** file identityまで同一と一般化するとmount差替え・loader差替えを検査済みと誤記する。

### RP-2(a) への一般化

- planの実装部分集合はownerを受理条件に使わない（`s2-plan.md:154`）ため、**選択した部分集合が変わらない**という結論は条件付きで妥当。
- root ownerであることは一般userによるbinary置換可能性を下げるが、bind/overlay、shared library、trusted-root侵害を閉じず、部分集合の十分性を独立には証明しない。
- 親briefが自ら認めるとおり、「owner検査を採ると本環境を拒否する」という旧却下理由だけは消える（`s1-brief.md:68-73`）。
- **成果物影響:** RP-2(a)を「ownerに依存せず十分」と記録すると、実際にはtrust assumptionで残した経路を実装済み防壁として数える。

### 他の実測前提

- `F_r` ancestry（`s1-premises.txt:6-7`）は特定worktree HEAD時点の事実である。子sandboxの現在HEADでもancestor rc=0だったが、resolverは各呼出しで再計算すべきで、mainや将来HEADへ一般化できない。
- record/schema pin一致（同 `:9-11`）はGit blob bytesの性質として再現可能だが、どのrepository/common-dirで読んだかは別途bindする必要がある。
- alpha台帳143 bytes（同 `:13-19`）はappend-only台帳の一点観測であり、将来も143 bytesという不変条件ではない。全履歴walkerを143-byte literalで代用してはならない。
- `jsonschema 3.2.0`（同 `:21-24`）は親interpreter環境の一点観測で、計算node・別venv・将来環境へ一般化できない。受理集合は明示的`Draft7Validator`とvectorsで固定すべきである。
- `s1-premises.txt` は「生出力」と称するが、実行command、cwd、hostname、interpreter path、timestamp、return codeを保持しないため独立再現性が不足する。
- D291追補の `local main=b13b7ea8` は既に時間切れで、現在mainにはD292も存在する。段4前にmain tip、D291/D292 ancestry、payload bytesを再読する必要がある。

### 親briefへの追加所見

- RP-4の「公表core 3文書のfoldがpilot解禁条件」（`s1-brief.md:27`）はD291/D292後は誤り。
- 「本sessionが§6全件・§7.1全20項目を閉じる」（同 `:40`）と、producer/report/certified consumerをscope外にする宣言（同 `:43-46`）は両立しない。
- 「純増検出力」とするwriter・20項目・symlink拒否（同 `:96-100`）はproduction call edgeと構成可能なpositiveがないため、現時点では検出力ではなく未発火設計である。
- 段2のB1〜B6引用行番号は正しかった。ただしB3/B5をcurrent validator実装の停止理由とする必要はなく、completion scopeと次session producer acceptanceへ分類し直すべきである。

## 5. nit / backlog

- Git local configの`include`/`includeIf`からcommon directory外のconfigを読む可能性がplanに明記されていない。現在の強制`-c`群を越えるfalse-accept keyは特定できなかったため、config origin inventoryの負例をbacklogとする。
- D291 parserの500〜800行見積りは既存587行parserとの規模比較にすぎず、安全性根拠には使えない。
- planに記された `new:L...` の予定行番号は実装後に必ずずれるため、acceptanceはsymbol/nodeidで固定すべきである。
- `s1-premises.txt` の実測provenance不足は今回の静的判定を逆転させないが、次回からcommand/環境/rcを保存すべきである。

## 総括

NO-GO。current blocker は15件。  
B1/B2/B4は承認済み入力不足、B6はscope誤り。B3/B5は次session側で閉じる。  
最大riskは、存在しないraw authorityをproducer申告値で代用し、未発火gateを「実装済み」と記録すること。  
D291/D292を取り込んだreplanと契約裁定が済むまで、実装・export・完了記録へ進めない。