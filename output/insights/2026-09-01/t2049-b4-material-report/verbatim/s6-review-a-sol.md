## 総括

親の診断は正しいです。共有 fixture は generator の正常 assembly 経路を一度も通らず、全 report consumer が `evidence_binding` rejection を材料化しています。正常経路を通る test node は 0 件です。

さらに、R1 は安定した assembly rejection では 201 block / 402 arm を保持しますが、artifact 在否を二度観測するため、観測間の変化で report 全体が消えます。R2 の完全射影検査は同じ builder を正解側にも使う自己 oracle で、M03 は候補入力上で恒真です。R4 は rejection 時に読めない leaf の campaign root を黙って捨て、output guard が fail-open します。

したがって現状は受理不可です。実装値そのものが正しい R3/R5/R9 の面はありますが、それを正常経路で検査した証拠はありません。

## 所見

### F1. 正常 assembly → ledger → evaluator 経路を通る node が 0 件

- 深刻度: Critical
- 判定: **regressed**
- 根拠: `orchestrator/tests/test_p3_b4_material_report.py:45-84`, `orchestrator/tests/test_p3_b4_raw_record_producer.py:1523-1547`, `orchestrator/campaign/p3_b4_material_report.py:184-220`, `s6-focus-run1.log:151-155`
- 壊れ方の具体例: helper は一時的な `REPOSITORY_ROOT` / `ROLE_FILE` patch の内側で publication を作りますが、その patch が戻った後の `test_p3_b4_material_report.py:77-78` で再 assembly します。そこで `recorded judgments differ from source evidence rederivation` となり、`contract_binding=None`、`analysis_result=None` です。fixture 内の producer 成功は generator の正常経路ではありません。
- 正常経路を通らない node: 全 28 node。M03/M04/M05/M06/M14/M17/M18 の緑は `test_p3_b4_material_report.py:244-245` の stub が返す rejection inputs 上の緑です。M09 は意図どおり renderer-only です。issuer、symlink、early overwrite の node も正常分析を必要としません。
- 成果物影響: certified selection と ledger は直接変更されませんが、成功 report の source、ledger binding、`protocol_violation` 値、参照 hash の正しさが全て未検査です。
- 最小修正案: context 終了後かつ clean subprocess から再ロードしても `B4RawAnalysisAssembly` になる publication fixture に直し、fixture 構築時に `assembly`、`contract_binding`、`analysis_result` の非 None を明示 assertion すること。
- 区別: **実在欠陥**。親の実走で確認済みです。

### F2. R1 の安定ケースは閉じるが、artifact 在否の二重観測で report 全体が消える

- 深刻度: High
- 判定: **partial**
- 根拠: `orchestrator/campaign/p3_b4_material_report.py:261-283`, `:286-290`, `:424-480`, `:701-727`
- 閉じている面: manifest から assembly 前に frame を作り、rejection 時も `_rejected_row` を全 frame に生成します。親実走が `test_p3_b4_material_report.py:141` まで進んだことから、安定した rejection では 201 block / 402 arm と missing leaf が実際に残っています。raw 値も推測せず unavailable にしています。
- 壊れ方の具体例: `_project_rows()` が artifact 在否を観測した後、`_assert_complete_projection()` が `_rows_from_inputs()` を再実行して同じ path を再観測します。leaf がこの間に作成または削除されると `projection_value_mismatch` となり、JSON/Markdown は 1 file も出ません。
- 成果物影響: 走行済み 200 block と変化中の 1 block が report から丸ごと消え、file-drawer が再度開きます。ledger と certified selection 自体は不変です。
- 最小修正案: artifact 在否を `_B4PlannedArmFrame` 作成時に一度だけ凍結し、row と検査の双方がその凍結値を参照すること。
- 区別: **実在欠陥**。将来の仮想リスクではなく、現在の二重 filesystem read による受理集合の不安定化です。

### F3. R2 の完全射影検査は自己 oracle で、M03 は候補集合上で恒真

- 深刻度: High
- 判定: **partial**
- 根拠: `orchestrator/campaign/p3_b4_material_report.py:297-373`, `:461-494`; `orchestrator/tests/test_p3_b4_material_report.py:65-68`, `:160-198`, `:213-249`; `orchestrator/tests/test_p3_b4_raw_record_producer.py:1130-1135`
- 恒真な検査: production では `rows = _project_rows(inputs)` と `expected = _rows_from_inputs(inputs)` が同じ `_rows_from_inputs` を使います。安定した外部入力によって `observed != wanted` を発火させることはできません。赤になるのは monkeypatch による projection 後改変、または F2 の在否 race だけです。
- M03 の具体例: fixture は `terminal="commit"` なので source の `terminal_reason` は既に `None` です。登録変異「terminal_reason を null にする」は候補集合に含意され、検出不能です。既存の ABORT evidence は `terminal_reason="diff-quarantine"` を生成するため、これを使えば null 化が実際に赤になります。
- stub green: M03/M04 の負例は real source mapping を検査せず、cached rejection row の unavailable wrapper を書き換えています。`test_input_artifact_projection...` も disk input の 1 byte 改変ではなく、組立後 report を monkeypatch しています。
- 未固定の表示面: Markdown の producer/ledger field と JSON row の一致を検査する node はありません。正常正例も WAL、model/prompt/projection、driver、reference hash、performance presence の全 field を独立照合していません。
- 成果物影響: ABORT の停止理由や campaign id が null/別値になっても「完全射影検査済み」の report を受理でき、JSON と Markdown の値が producer とずれます。ledger と certified selection は直接変わりません。
- 最小修正案: builder と別実装の oracle で各 derived field を source/manifest/registry へ直接照合し、ABORT publication を M03 の候補にすること。負例は正常 assembly inputs を通し、renderer の必須列も照合すること。
- 区別: **実在欠陥**。現在値の誤写像を確認したという意味ではなく、裁定された正しさ防壁が実効でない欠陥です。

### F4. assembly rejection 時の output guard が campaign root 不明を黙って受理する

- 深刻度: High
- 判定: **partial**
- 根拠: `orchestrator/campaign/p3_b4_material_report.py:772-792`, `:803-815`, `:879-903`
- 壊れ方の具体例: ある planned leaf を削除し、その leaf だけが参照していた on campaign root を `output_root` に指定します。rejection 分岐は leaf の `OSError` を `continue` して campaign root 集合から落とすため、三方向比較は発火せず、その campaign 内へ `report.json` と `report.md` を書きます。malformed JSON でも同じです。
- 既存負例: M10〜M12 は成功 source を前提にした guard 試験で、現在は `_first_campaign_root()` が cached rejection row の WAL を読む時点で失敗しています。missing/malformed leaf と output intersection の組合せはありません。
- 成果物影響: campaign 配下へ未宣言 2 file が入り、campaign 完全性列挙と参照集合を変えます。report の配置受理集合が R4 より広くなります。
- 最小修正案: 全 campaign root を result leaf 消失前から復元できる publication-bound datum にする必要があります。現行 publication だけでは欠落 leaf の root を復元できないため、2 新規 file の範囲だけで R1 と R4 を同時に完全閉鎖したとは主張できません。親裁定へ scope を返すべきです。
- 区別: **実在欠陥**。具体的に構成可能な現在の fail-open です。

### F5. M13 と M16 は登録した機構へ照準していない

- 深刻度: Medium
- 判定: **partial**
- 根拠: `orchestrator/campaign/p3_b4_material_report.py:730-762`, `:803-815`, `:827-870`, `:887-903`; `orchestrator/tests/test_p3_b4_material_report.py:353-367`, `:419-480`
- M13: symlink test は `_resolve_output_root()` 内の symlink-component rejection で止まり、後段の resolved-path 三方向比較へ到達しません。比較を字面へ戻す M13 mutant はこの node では検出できません。
- M16: overwrite は早期検査 `:888`、publish 前検査 `:839`、hard-link create-only `:858` の三層です。一層だけ外しても別層が同じ入力を拒否します。clean subprocess node は「上書き禁止全体」は示しますが、登録変異を単一層、単一理由へ帰属できません。
- 成果物影響: 現行 runtime の resolved comparison と no-overwrite 値は正しいままですが、登録 mutant が生存しても緑となり、将来は alias 配置または上書き受理へ変わり得ます。
- 最小修正案: M13 は symlink を使わず、既存 directory と `..` で campaign と同じ実体になる lexical alias を使うこと。M16 は early rejection、publish 前 race、create-only publish を別 ID に分割すること。
- 区別: **実在する変異帰属欠陥**。現在の成果物破損そのものは未観測です。

### F6. Markdown は rejection 理由を失う

- 深刻度: Low / nit
- 判定: **partial**
- 根拠: `orchestrator/campaign/p3_b4_material_report.py:641-698`
- 壊れ方の具体例: `_display()` は unavailable object を理由ごと `"不在"` に縮約し、Markdown は `assembly.reason` を一度も表示しません。`incomplete_set` と `evidence_binding` の report.md は同じ見え方になります。
- 成果物影響: JSON と ledger は不変ですが、Markdown-only consumer は rejection の参照理由を失います。
- 最小修正案: assembly rejection の typed reason と unavailable reason を Markdown に決定論的表示し、JSON 値との一致を試験すること。
- 区別: **実在する表示損失**。canonical JSON が保持するため nit とします。

### F7. 禁止 file の変更、skip、xfail は確認されない

- 深刻度: Info
- 判定: **closed**
- 根拠: `git status --short` は指定された新規 2 file だけを `??` と表示し、`git diff --name-status 24014bdb2 --` は空でした。新規 2 file に `skip`、`xfail`、除外指定もありません。
- 成果物影響: 既存 producer、ledger、evaluator、既存 test の値・受理集合・参照は byte 変更されていません。
- 最小修正案: なし。
- 区別: **実測済みの closed 項目**です。

## 変異 M01〜M18 の帰属判定

親実走は baseline だけで、実際に M01〜M18 を投入したログや anchor 登録はありません。従って下表の node は静的な候補であり、現状を `KILLED` と認定はできません。

| ID | 赤になる node | 到達可能か | 単一理由か | 再照準の提案 |
|---|---|---|---|---|
| M01 | `test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf` | assembly rejection には到達するが baseline 自体が赤 | いいえ | 正常 fixture を直し、report 非生成だけを別 node で pin |
| M02 | M01 と同じ node | missing leaf は存在するが先に `evidence_binding` rejection | いいえ | baseline が `incomplete_set` になる専用 publication と行保持 node に分離 |
| M03 | `...[terminal-reason]` | target の成功 row に未到達。commit 候補では null が恒真 | いいえ | ABORT source の `"diff-quarantine"` を null 化して直接 source 比較 |
| M04 | `...[campaign-id]` と正常正例 `test_complete_projection...` | 現在は rejection wrapper のみ | 正常化後は複数 node | 正常 source の identity と row を一つの独立 node で比較 |
| M05 | `...[drop-one-arm]` | rejection report の projection validator へ到達し baseline 緑 | 局所注入では `projection_incomplete` 一理由 | 正常 fixture でも同じ count gate を通す |
| M06 | `...[duplicate-one-arm]` | 同上 | 局所注入では `projection_not_bijective` 一理由 | 正常 fixture で identity duplicate を pin |
| M07 | `...[rewrite-source-utf8]` | 不可。dict に文字列加算して validator 前に TypeError | いいえ | 正常 assembly の UTF-8 string を 1 byte 改変 |
| M08 | `test_m08_floor_absence_runs_existing_evaluator_as_protocol_violation` | 不可。evaluator 未到達で baseline 赤 | いいえ | 正常 fixture 後に `floor=None` の実 evaluator result だけを pin |
| M09 | `...[indeterminate]` | 到達可。renderer-only と明記済み | はい | 変更不要 |
| M10 | `...[equal]` | 現在は `_first_campaign_root` で baseline 赤 | いいえ | 正常 source root で guard 本体へ到達させる |
| M11 | `...[below]` | 同上 | いいえ | 同上 |
| M12 | `...[above]` | 同上 | いいえ | 同上 |
| M13 | `test_m13_output_symlink_component_is_rejected_before_any_report_write` | 不可。symlink guard が比較層より先に拒否 | いいえ | symlink 無しの `..` lexical alias で resolved comparison を試験 |
| M14 | `...[anomaly-class-alias]` | 現在は rejected-row branch だけ | branch 依存。成功 branch mutant は未検出 | 成功/rejection の両 branch を別 node で `anomaly_class=absent` と照合 |
| M15 | issuer node と ledger node | issuer は到達、ledger は assembly rejection に遮断 | 広い mutant では 2 node、ledger は baseline 赤 | M15a issuer、M15b 正常 assembly 後 ledger に分割 |
| M16 | early check は `test_existing_pair_is_rejected_before_publication_reload`; composite は clean subprocess node | early check は到達。後段は前後の同等 guard に遮断 | いいえ | early、pre-publish、hard-link collision を別 ID に分割 |
| M17 | `...[absent-to-zero]` | 現在は rejected-row branch だけ | 成功 branch mutantは生存 | 成功/rejection の両 branchで producer 不在を独立照合 |
| M18 | `...[remove-transcribed-binding]` | 現在は rejected-row branch だけ | mutant 適用時は test 自身の `pop` が KeyError となり、gate 理由に絞れない | `pop(..., None)` ではなく registry 値、binding、non-guarantee を独立 oracle で検査 |

到達不能: **M03、M04、M07、M08、M10、M11、M12、M13、ledger 側 M15**。  
検出不能または branch survivor: **M03、M13、M16、成功側 M14/M17/M18**。  
複数 node または理由非単一: **M04、M15、M16、M18**。  
現在 baseline が既に赤で帰属不能: **M01、M02、M07、M08、M10〜M13、ledger 側 M15**。

## 裁定 R1〜R9 の履行表

| R番号 | 判定 | 根拠 file:line |
|---|---|---|
| R1 | **partial** | stable rejection frame は `p3_b4_material_report.py:261-283,376-458`。二重在否観測による全 report 消失は `:286-290,467-480` |
| R2 | **regressed** | mapping 自体は `:297-373`、検査は自己 oracle `:461-494`。正常正例は `test_p3_b4_material_report.py:160-198` で baseline 赤 |
| R3 | **partial** | `floor=None` は `p3_b4_material_report.py:207-214`、4分類未実効宣言は `:552-559`、renderer-only 明記は test `:305-319`。実 evaluator node は baseline 赤 |
| R4 | **partial** | 三方向比較は `:803-815`。rejection 時の root skip は `:772-784`、M13 は比較層未到達 |
| R5 | **partial** | anomaly absent と precursor 分離は `:358-363,406-411` で正しい。成功 branch の変異防壁は未到達 |
| R6 | **partial** | issuer/ledger catch は `:175-205`。issuer node は通るが ledger node `test...:398-416` は assembly rejection に遮断 |
| R7 | **closed** | clean subprocess 条件と 2 回起動は `test_p3_b4_material_report.py:433-480`。`-B`、repo 外 cwd、環境除去を満たす |
| R8 | **regressed** | module fixture と invoke 2 回 assertion は `:45-84` にあるが、fixture publication が generator から再導出不能。early overwrite は `p3_b4_material_report.py:887-889` |
| R9 | **partial** | 値、`binding:"transcribed"`、non-guarantee は `:323-338,393-400` で正しい。正常 branch の node は未到達し、branch 別 mutation pin が無い |

## 検査できなかったこと

- sandbox 制約に従い、こちらでは pytest や mutation run を実走していません。緑とは報告しません。
- M01〜M18 を実際に source へ投入した probe、anchor、再走記録が提示されていないため、`KILLED` の実測認定はできません。
- clean subprocess、正常 report bytes、Markdown の実生成は再実走していません。親の baseline 実走 `9 failed / 19 passed / 39.21 秒` と静的経路だけを根拠にしています。