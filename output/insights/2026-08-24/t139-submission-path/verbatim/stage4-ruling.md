# [T-139] 段4裁定 — plan v2 と変異事前登録

## 所見裁定

- Lens A F1（新canonical successor decisionの発効権限不足）: **realだが段2案に限定して採用**。新decision/foldは作らない。entry 874とユーザー直接指示はD574既決の機械可読projection実装を許すが、新しい設計判断の発効までは許さない。
- Lens A F2 / Lens B 9（spool fold後にP commitが確定する循環）: **real・採用**。canonical ledger payload案を撤回し、段9 foldをauthority生成に使わない。
- Lens A F3/F5（任意local history自動発見はcanonical authorityでない）: **real・採用**。history scan / generic chain walkを作らず、sourceが外部pinする固定payload BlobRefだけを読む。
- Lens A F4（D574二段rootは汎用chainを直ちに要求しない）: **real・採用**。D282 base + D574 projectionのexact 1段だけに限定し、将来successorはfail-closedとする。
- Lens A F6（receipt publishはD292投入禁止を直接迂回しない）: **refuted側を採用**。qsub/driver/export無しのtemp repo正例はscope内。実計算資源・live receiptは触らない。
- Lens A F7（raw CMake実装未照合）: **親が現行codeを再読して解消**。`_semantic_validator.py::_validate_compile_legs` はconfigure argv・compile commands・raw sibling cacheを正の3脚にし、その後に申告3値を不一致拒否だけへ使う。production predicateは変更しない。
- Lens A F9 / Lens B 8/12（投入経路完成の過大主張）: **real・採用**。成果物名をprivate receipt admission/publish gate integrationに限定し、producer/driver/collector/report/ledger到達や単位6完成を主張しない。
- Lens B 1/2/3（D509行予算）: **real・採用**。新resolver moduleを撤回し、`submission_gate/*.py`純増147行を絶対上限、134行を目標に既存`ApprovedManifest`へ統合する。超過なら正しさ要件を削らず停止する。
- Lens B 4/5/14（index世代）: **real・採用**。既存`index-v1.json`と旧42 vector JSONをbyte不変にし、新4 vector + `index-v2.json`を新世代として追加する。旧index commit/hashを独立literalで固定する。
- Lens B 6/7（fixture正例）: **採用**。fixed projection payloadを読むproduction resolverをtemp git repoで通し、writerの恒常拒否退化を殺す。qsubは呼ばない。
- Lens B 10（author所有）: **real・採用**。artifact/test/productionはCodex author、docs/spool/commitは親。循環pinを避けるため段5を3つの逐次author unitに分ける。
- Lens B 11（generic history契約未確定）: **realだが不適用化**。generic historyを実装しないことで閉じる。
- Lens B 13（B2未閉包）: **real・scope外**。series sealed set / receipt-set / consumerは実装せずinsight/handoffへ記録する。

## plan v2

### Authority構成

1. 既存D282 payloadをbaseとし、`base_approval_fold_commit=39d760985a5e37d20464c394760bf65596156566`を維持する。
2. 現在有効なcanonical判断はD574 fold `b261b293f40548d7fc44293df3806df69acb7bc9`とし、projection payloadの`approval_fold_commit`へ固定する。
3. projection payloadはD574の新判断ではなく機械可読射影で、structured predecessor（D282 exact ref）と`conformance_vector_index` BlobRefを持つ。generic successor discovery、cycle walk、caller指定refは持たない。候補がexact 1であることをsource pinで構造化する。
4. manifestは二段fold、D282 projection、index-v2宣言を持つ。manifest宣言は照合対象でありauthorityではない。
5. `approval_payload.py`の固定BlobRefがprojection payload bytesを外部pinし、payload内index BlobRefがvector authorityとなる。別の固定BlobRefがmanifestをpinする。resolverはD282 loaderをexact 1回使い、両artifactを固定commitから読む。
6. `_manifest.ApprovedManifest`を既存private tokenでsealした唯一のeffective authorityとし、`_PreregBinding`がそれをwriterへ運ぶ。新public dataclassや第4writer引数は作らない。

### 逐次author unit

- Unit I（author）: 旧42を参照し新4を足す`index-v2.json`、新vector 4本、世代境界/旧bytes不変のtestだけを書く。既存index-v1/vector/test_spool_fold/docsは変更しない。親が検査してcommit Iを作る。
- Unit A（author）: commit Iのindex-v2 BlobRefを宣言するtracked manifest JSONとprojection payload JSON、そのexact grammar fixture/testを追加する。両artifactは同commit Aに置ける（payloadはmanifest commitを自己申告せず、indexのみ外部pinする）。親が検査してcommit Aを作る。
- Unit C（author）: commit Aのpayload/manifest BlobRefを`approval_payload.py`で外部pinし、`_manifest.py` / `_binding.py` / `_writer.py`へ結線する。`_semantic_validator.py`は意味不変の説明是正だけ。既存unit1〜5 + private E2E正例/負例を更新する。親が検査してcommit Cを作る。

### Gate禁止と通る正例

- 禁止: manifest自身のindex宣言、caller引数、HEAD同名file、申告cmake値、sourceに直書きしたindex digestのいずれか単独を受理根拠にしてはならない。
- 通る正例: temp git repoのcanonical mainがD282 base、固定D574 projection payload、固定manifest、index-v2をsource-pinned commitで持ち、payloadとmanifestのindex BlobRefが一致し、sealed bindingと完全receiptのraw CMake三脚が一致するとき、private writerはcaller選択不能なtemp `output/receipts/t139/...json`へ入力bytesそのものをcreate-only publishする。qsub、D264 export、D292解除は発生しない。

## 変更アンカーと上限

- `orchestrator/preregistration/approval_payload.py`: fixed projection refs、exact parser、D282とのone-step合成。既存D282 parserを変えない。
- `orchestrator/submission_gate/_manifest.py`: sealed viewへmanifest ref・base/effective fold・vector indexを追加し、payload/manifest/index一致を検査。
- `orchestrator/submission_gate/_binding.py`:同じsealed viewを必須保持し、fixed blobsとroot identityを再検査。
- `orchestrator/submission_gate/_writer.py`: binding内authorityがindexを持ち、payload/manifest一致済みであることを検査。3 keyword-only引数とfixed namespace不変。
- `orchestrator/submission_gate/_semantic_validator.py`: raw三脚/reject-only説明を行数中立で是正、predicate無変更。
- tests/fixtures: index-v2、新4vectors、projection grammar、private E2E、旧42 pin。
- `submission_gate/*.py` baseline 6,053行、目標 <=6,187、絶対 <=6,200。`approval_payload.py`へ責務を逃がして上限を偽装しないため、production全体の純増も別途併記する。

## 変異事前登録（DW-M01）

1. M1 writer vector guardを恒真returnにする。legacy D282 bindingの`vector_authority_unavailable`負例だけが赤になる単一理由へ照準する。
2. M2 payload indexとmanifest indexの比較を削除する。manifest片側1 field差替え負例がpublish前に赤になることを要求する。
3. M3 fixed payload BlobRefをHEAD同名file読取へ退化させる。historical commit I/Aを保ったままHEAD側だけ差替える負例で赤にする。
4. M4 `ApprovedManifest` token検査を型検査だけへ弱化する。直接構築偽物を拒否する負例で赤にする。
5. M5 `_PreregBinding`からsealed authority保持/再検査を外す。別authorityを持つbinding負例で赤にする。
6. M6 writerのpublish対象を`raw_bytes`から再serialize bytesへ変える。正例のpublished bytes exact一致で赤にする。
7. M7 raw `CMakeCache.txt`再読を申告`cmake_cache`へ置換する。申告は正しいがraw siblingだけ誤る既存/追加負例で赤にする。
8. M8 index-v2から必須writer positiveまたはpayload mismatch vectorを除き、payload側index pinを同時更新しない。index digest不一致の単一理由で赤にする。

各mutationはauthor後に前後maskを実コードで再確認し、単一理由にならないものは登録から外して実効点へ再照準する。

## scope外

- D292解除、submit_pilot/main、PBS/qsub、driver/collector、live計算資源、解除decision、D264 4名前export。
- B2 sealed series/receipt-set、材料report/試行台帳consumer、generic future successor chain、AST alias hardening。
- `test_spool_fold.py`、worklog entry874本文/digest、既存index-v1と旧42vector bytes。
