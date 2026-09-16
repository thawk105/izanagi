## 全層の接続

略記は以下。行番号は適用後を指す。

- D：`orchestrator/campaign/paper_story_a1_paired.py`
- S：`orchestrator/campaign/paper_story_a1_source.py`
- J：`tools/pegasus/paper_story_a1_paired.sh`
- TJ／TP：`orchestrator/tests/test_paper_story_a1_{job_contract,paired}.py`
- R：射影された `s5-author.md`

**[refuted] sized 経路の接続切れは、確認した実装には見つからない。**

| 層 | 適用後の確認箇所 |
|---|---|
| submit | D:3411：study 別の契約 load、hydrate dir 実在確認。attempt 名照合は pilot のみ |
| intent | D:2636：sized 全 attempt に契約検算・hydrate 必須。D:2643 の3 workload に、D:2599 の hydrate 変数を渡す |
| job preflight | J:587：該当 workload の intent と hydrate 環境変数を照合 |
| staging | J:1380：両 policy が対象。`fetchcontent/{masstree,mimalloc,googletest}-src` へコピーし、J:1404 で CLI 引数を渡す |
| measure | D:7129：sized 契約 load、study 一致、pilot のみ attempt 照合。D:7134：hydrate 元と環境、staged root と dependency scratch を照合 |
| materialization | D:7142 → S:93 → S:99：`study_id` が契約 load と `SourceContext` まで届く |
| gate／campaign | D:7154 と D:7188：同じ `source_context.root`。D:7189 は context 自体も渡す |
| consumer | D:2243：sized 閉包追加。D:4849：閉包完全一致。D:4862：v2 binding 検算。D:5222：amended admission 発火 |
| configure | D:5006：追加4 token の長さ。D:5026：`-S` と admission root 一致。D:5039：FETCHCONTENT 4 token 完全一致 |

成果物影響：指定経路に、sized を pilot 固定条件で一律拒否する取り残しは認められない。

**[unverifiable] 「sized 本走が全層を実際に通る」は未確認。** TJ:3445、3480、3484 は receipt admission・materialization・campaign を stub する。pilot 実投入受領証の `submission.json:27` は hydrate **元**の記録を裏付けるが、sized の成功受領証ではない。

成果物影響：静的接続と経路 test の構造から、sized の本走成功・受領証発行済みとは記録できない。

## 閉包一致

**[refuted] 内容・順序の不一致は見つからない。** D:2243、J:58、451、986 の構成は次のとおり。

| 閉包 | 順序 |
|---|---|
| non-certifying：14 path | driver → 当該 policy → pipeline → job → campaign_lock → ident → wal → loop → trial_registry → runner → 契約 → module → patch → 追補 |
| terminal：9 path、2箇所 | driver → 当該 policy → pipeline → job → runner → 契約 → module → patch → 追補 |

pilot は v1 契約／9月11日追補、sized は v2 契約／9月17日追補。J:997 の埋込 Python は `IZANAGI_A1_TERMINAL_POLICY_RELATIVE` で二値選択し、同変数は J:952 で設定される。

成果物影響：閉包差による sized receipt の誤拒否は、静的には認められない。

**[refuted] `count == 3` の破綻はない。** 引用符込みの各 path を `grep -Fc` で確認した。

| path | 出現数 |
|---|---:|
| pilot v1 契約 | 3 |
| sized v2 契約 | 3 |
| 共通 module | 3 |
| 共通 patch | 3 |
| pilot 追補 | 3 |
| sized 追補 | 3 |

成果物影響：pilot／sized の各4 path とも、既存の出現数条件を維持する。

## test の実効性

**[refuted] test 1 は文字列 count だけではない。** TJ:3276 は driver の実関数と literal tuple を比較し、TJ:3278 は shell 区間を実評価、TJ:3285／3290 は埋込 Python の実区間を評価する構造になっている。

成果物影響：M5 の条件変異や順序変更を、count が変わらなくても検出できる構造である。

**[refuted] sized fixture の実 bytes 不足は解消されている。** TJ:3206 は v2/module/patch/追補、policy、preregistration、`sizing_inputs` 全値を `read_bytes`／`write_bytes` で配置する。sized policy の `sizing_inputs` は `sizing-pilot.json` と `sizing-certificate.json` の2 file。measure fixture は TJ:3420 で実 policy loader を復元する。

成果物影響：この既知の不足によって、source 経路より先に policy 検査が拒否する構造ではない。

**[refuted] test 6 の materializer stub は引数を捨てていない。** TJ:3470 が受けた `study_id` を記録し、TJ:3507 が sized を assert。TJ:3509〜3513 は staged root、gate root、campaign root、context 同一性を確認する。既存 AST test にも TJ:2244 の引渡し assert がある。

成果物影響：driver が既定 pilot の materializer を呼ぶ取り違えを見逃す恒真 test ではない。

**[unverifiable] materializer 内部までの動的接続は、この新規 test 群だけでは証明されない。** TJ:3480 は `materialized` 全体を置換し、TJ:3400 は `SourceContext` を直接生成する。S:99 の内部引渡しは静的には正しいが、両 test を連結した実観測ではない。

成果物影響：「実 materialization を経た sized context が trace/perf に届いた」と記録すると証拠を過大評価する。

**[refuted] test 7 の期待 error は実装と一致する。** TP:4911〜4914 は次の二分を実装済み。

| 負例 | 期待 error | 実装 |
|---|---|---|
| 非 canonical root／`tracked_clean=True`／pin 不一致 | `amended-source-admission-mismatch` | D:5226 |
| canonical だが configure `-S` と異なる root | `trace0-source-route-incomplete` | D:5026 |

TP:4899 は実 `_validate_arm` を呼び、正例は TP:4903 に分離されている。

成果物影響：root 不一致の誤った期待値に合わせて production 検査を変更する必要はない。

## 変異の帰属

**全変異の実測 KILLED／SURVIVED と、既存 test を含む失敗 node 完全集合は [unverifiable]。** 以下は適用後コードからの静的評価であり、変異実行結果ではない。

| ID | anchor・操作・期待 node の評価 |
|---|---|
| M0 | **候補：S:32** の一意な `CONTRACTS = {` を `CONTRACTS = {  # fixed pilot/sized contracts` にする。意味不変で SURVIVED 期待 |
| M1 | S:34 の sized 要素行は一意。削除すると TJ::`test_sized_source_closures_match_job_and_driver` の literal 期待値と D:2243 の結果が不一致になる。fixture の契約表参照による `KeyError` より、この node を主帰属にする |
| M2 | S:41〜42 の JSON 自体の SHA 検算を除去。TP::`test_sized_source_contract_pins_bytes_and_four_bindings` は TP:4831 で JSON に改行だけを追加するため、JSON parse／参照4 file に先取りされず、期待した例外が出なくなる |
| M3 | S:44 の一意な loop から `amendment` を除去。同じ TP node の追補 file 改変ケースが検出する。契約 JSON は保持され、前の各ケースも TP:4835 で復元されるため、JSON SHA 検査による先取りはない |
| M4 | **裸の条件行は非一意。** D:2243 と D:3411 が同文。D:2244 の `paths = ...` を含む2行を anchor とし、その条件だけ pilot 限定へ戻す。期待は TJ::`test_sized_source_closures_match_job_and_driver` |
| M5 | J:997〜999 の env 条件ブロックを anchor にして pilot 限定へ戻す。期待は同じ TJ node の TJ:3291。path 文字列は残るため count 検査に先取りされず、terminal tuple 不一致で検出する |
| M6 | **裸の OR 条件は非一意。** J:74 と J:1380 が同文。J:1379 の `THIRD_PARTY_ARGS=()` を含めて anchor 化し、staging 条件だけ pilot 限定へ戻す。期待は TJ::`test_sized_job_stages_hydrate_for_measurement` の TJ:3357 |
| M7 | D:5222 の一意な `any(...)` を v1 限定へ戻す。期待は TP::`test_sized_consumer_accepts_amended_configure`。amended root が設定されず D:5006 の argv 長で拒否されることが、この正例に対する意図した検出 |
| M8 | D:7132 の一意な条件を `if attempt.name != "attempt-0004":` にする。期待は TJ::`test_sized_measurement_routes_amended_source_and_hydrate` の `attempt-0002` 正例。pilot 条件だけを削除して `contract_source["attempt"]` を残す変更は、v2 の `KeyError` となり登録意図と不一致 |
| M9 | D:2636〜2638 の条件全体を pilot／attempt-0004 限定に戻す。期待は TJ::`test_sized_group_intent_requires_hydrate`。TJ:3329 は intent 作成前の直接呼出しなので、submit の hydrate 検査にも記録済み intent の復元にも先取りされない |
| M10 | D:4862〜4864 を旧 v1 限定照合へ戻す。期待は TP::`test_sized_amendment_binding_rejects_single_changed_input`。TP:4845 は閉包と digest の書式を保持して値だけ変えるため、D:4849 の閉包検査に先取りされず TP:4846 が検出する |

**[real] M4／M6 は、条件行単独では単一箇所変異にならない。** 上記の周辺行を含む再照準が必要。ただし、実際の `old` を保持する変異 spec は今回の射影にないため、既存 spec が誤っているとまでは断定しない。

成果物影響：裸条件の一括置換を使うと submit／閉包まで同時変更し、変異台帳の「単一箇所への帰属」が崩れる。

**[refuted] M2／M7／M8 の事前登録意図と test の明白な不整合はない。** M2 は意味不変の JSON 改変、M7 は独立正例、M8 は literal 比較を使えば、それぞれ狙った拒否・検出に対応する。

成果物影響：静的に成立する期待帰属はあるが、既存 test でも落ちないことまで確認した「新規検出力」としてはまだ計上できない。

## 受入時間

**[refuted] 新規 clone／build／実 materialization の増加は差分にない。** `_clone_canonical_ccbench` の呼出し箇所は変更前1箇所、変更後1箇所（TJ:484）。既存 materialization は TJ:491、新規 measure は TJ:3480 の stub、context の期待 materialization 生成も TJ:3398 で stub 化される。TP:4877 は command 構築であり build 実行ではない。

成果物影響：新規 sized test による clone／実 materialization の追加回数は0。

**[unverifiable] 受入時間内の完了は未確認。** TJ:3278／3351 の小規模 subprocess・fixture I/O は増えるが、所要時間は測定していない。

成果物影響：時間上限内という受入記録は確定できない。

## 報告と実体

**[real] R の停止理由・残作業・test 数が現在の差分と一致しない。**

| 報告 | 差分の実体 |
|---|---|
| R:97、107：test 8 の non-certifying validator が問題、訂正待ち | TP:4853 は既に terminal 用 `_validate_source_binding` |
| R:111：sized measurement fixture／test が残作業 | TJ:3416、3489 に存在 |
| R:112：pilot measure attempt 拒否 test が残作業 | TJ:3516 に存在 |
| R:80：TJ は95 test | 現物は97。差分の追加は TJ 9＋TP 5＝14 test |

成果物影響：この報告を現在の差分の受入証拠として使うと、変更版・実行済み node・未実走 node を誤対応させる。

**[unverifiable] DIRECT_CALL_PASS／FAIL は今回再確認していない。** R:57〜68 の結果、とくに呼出先が現物と異なる test 8 の FAIL を、現在版の結果として転記できない。R:74 の反実仮想「未実施」に対応して、こちらでも変異成功の証拠は得ていない。

成果物影響：現物に追加済みの measurement test や、訂正済み pilot test を緑・赤のどちらにも確定できない。

**[refuted] 所有外 file の変更・削除は提示差分にない。** 差分対象は指定6 path のみ。既存 test 関数の削除もなく、既定 pilot 引数の維持、AST assert 追加、既存 `_arm` 利用は R:83、91、92 と整合する。所有外 caller の網羅性は R:93 自身が未完了と明記している。

成果物影響：提示差分から、所有外成果物の書換えは認められない。ただし差分外の書込履歴までは証明しない。

## must-fix / nit の一覧

| 区分 | 判定 | 内容 |
|---|---|---|
| must-fix：受入証拠 | **real** | R:97〜112 と TP:4853／TJ:3489／3516 の不一致。現在の差分に対応する報告へ訂正し、過去の直接呼出し結果と未実走部分を区別する必要がある |
| 変異 anchor の確定事項 | **real** | M4 は D:2244、M6 は J:1379 を含めて単一箇所へ再照準。既存 spec の欠陥自体は未確認 |
| production の局所修正 | **refuted** | sized 接続切れを理由とする must-fix は見つからない |
| 証拠の限界 | **unverifiable** | 全層本走成功、全変異の実測帰属、回帰、受入時間。未確認を成功として扱わない |
| nit | — | 成果物影響を伴わない書式・命名指摘は挙げない |

## 総括

**sized の production 経路は静的に接続され、指定された fixture・test の主要な不足も解消されている。** 必須修正は、現在の差分と食い違う実装報告の整合。M4／M6 は周辺行込みの anchor が必要である。pytest・変異・本走を実行していないため、受入成功とは判定しない。

配列区間の評価コマンドは、自動承認レビュー（PreToolUse hook）が Pegasus の dispatch 必須スクリプト実行と判定して拒否したため未実行。閉包順序は静的確認、出現数は `grep -Fc` の実測である。