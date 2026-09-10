判定は **NO-GO**。F1〜F6 と段6所見11件中10件は閉じていますが、R1-6 の新 D が未着手です。fix 前 snapshot と現物を再構成比較した範囲では、F80 型の正例被覆退行はありません。

私は pytest・変異注入を実走していません。無変異 current の実測は、提示された親計測「48 passed / 0 failed」を根拠にしています。変異表は静的判定です。

略号: L=[reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py)、T=[test_reflux_origin_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py)、P=[liveness_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py)、W=[probe wrapper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_t244_p3_liveness_probe.py)、A=[s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s4-adjudication.md)、F=[promptFix.txt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s6/promptFix.txt)、D=[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/decisions.md)。

## 1. 所見対応表

### 段6レビュー所見

| 所見 | 判定 | 根拠と再発検出 |
|---|---|---|
| R1-1 | `closed` | V18 は12セル・合法3セルを維持し、raw member列から3 countを再計算する（T:2924-2969）。stale countを戻すと合法 tombstone セルの decode equality が失敗する（T:2970-2978）。decoderの再計算照合も不変（L:1057-1079）。 |
| R1-2 | `closed` | 親裁定どおり新語彙へ期待を更新した（F:31-39）。parserの label（L:320-324）と狭い anchor（T:1379-1380）が一致し、再び不一致なら `Raises` が失敗する。 |
| R1-3 | `closed` | policy 2 key（P:42-45）と snapshot field（P:175-182）を追随。wrapperは subprocess成功と6件すべてのPASSを維持する（W:17-39）。旧APIへ戻せば wrapper が失敗する。 |
| R1-4 | `closed` | budget旧形（T:2057-2063）、reserve/commit旧-only形（T:2107-2121）、sealed旧形（T:2158-2168）を個別に拒否。旧 alias を受理すると各 `Raises("keys")` が失敗する。 |
| R1-5 | `closed` | gateは実行候補数が正のbatchだけ（L:1624-1629）。既定1、明示2の正例・負例を固定した（T:4114-4185）。fix前へ戻すM14なら正例が失敗する。 |
| R1-6 | `未着手` | 新 D の参照規則は必須（A:52-56）、probe追随記録も要求される（A:191-193）。fix報告自身がdocs未編集と明記し、現 decisions の最終見出しはD193のまま（D:9398）。 |
| R2-1 | `closed` | R1-4と同じ。指摘された4種の実際の旧形がすべて存在する（T:2057-2168）。 |
| R2-2 | `closed` | R1-3と同じ。probeの6検査本体は変更せずAPI追随のみ（P:42-45, 175-188、W:34-39）。 |
| R2-3 | `closed` | R1-1と同じ。合法性やdecoderを緩めず、fixture側だけを独立再計算した（T:2948-2988）。 |
| R2-4 | `closed` | 親裁定された唯一の期待値更新。無条件 `Raises()` 化ではなく、新拒否理由を一意に束縛する（T:1379-1380）。 |
| R2-5 | `closed` | 混在例でsnapshot `2`（T:4224）とsemantic `(3,2,1)`（T:4225-4229）を固定。非tombstone unionへの変更や相互取り違えなら assertion が失敗する。 |

### 親の fix 項目

| Fix | 判定 | 根拠 |
|---|---|---|
| F1 | `closed` | raw列から3 countを再計算し、合法3セル・不合法9セルの期待は維持（T:2924-2988）。 |
| F2 | `closed` | 許可された1件だけを `batch member row minimum` へ更新（T:1379）。 |
| F3 | `closed` | 新policy key・snapshot fieldへ追随し、wrapperは未変更（P:42-45, 175-182、W:17-39）。 |
| F4 | `closed` | reserve、commit、sealed、budgetの旧形を全て拒否（T:2057-2168）。M10を静的に殺す。 |
| F5 | `closed` | production gateと既定1・明示2の三境界が対応（L:1624-1629、T:4114-4185）。 |
| F6 | `closed` | snapshotとsemanticの異なる3値を同一混在fixtureで直接固定（T:4211-4229）。 |

## 2. fixによる退行検査

snapshot.patchをHEADへメモリ上で適用し、現物との差分を比較しました。

| 検査 | 結果 |
|---|---|
| 既存 `assert` の削除 | 0件 |
| assertion・`Raises` の弱体化、無条件化 | 0件 |
| skip / xfail追加 | 0件 |
| 既存正例入力の単純化 | 0件。V18の12セルとcandidate/outcomeは不変で、stale derived countだけを訂正（T:2924-2969）。 |
| 期待値変更 | F2の拒否理由1件のみ（T:1379）。親の明示許可範囲内。 |
| その他の入力差替え | F4で「新sealed形＋余分な`cardinality`」を、実際の旧sealed形へ差替え（T:2158-2168）。これは正例削減ではなく、誤照準だった負例の代表性強化。 |
| probeの意味変更 | なし。C-a〜C-eの判定は維持され、API名だけ追随（P:184以降、W:34-39）。 |

したがって、fix起因の正例被覆退行・無許可の期待値変更は認めません。

### F5の抜け道構成

全tombstone batchだけを2件並べる経路を追うと、次のどちらでもcertifiable sealへ到達できません。

| 構成 | 到達結果 |
|---|---|
| 正しいcounterで `OriginSealed(... sealed_queries=0, tombstoned_queries=4)` | 全tombstone memberは `sealed_queries` に加算されず（L:1565-1591）、query floorが先に拒否する（L:1619-1623）。既存V14がこの形を直接固定（T:2013-2034）。 |
| `sealed_queries=4` と偽装 | floorより前のstate counter照合で拒否（L:1601-1609）。 |
| floorを満たす非tombstone batchを追加 | そのbatchは必ず `sealed_distinct_candidate_count > 0` となり、候補数gateの対象に戻る（L:1554-1558, 1624-1629）。明示2のpass/fail対が固定済み（T:4160-4185）。 |

またauthority parserはfloorを非空とし、各 required query を最低2以上に制限する（L:309-311, 320-339）。したがって全tombstone batchだけでgateを回避する経路は構成不能です。

## 3. 変異の再判定

「あり」は、変異注入時に失敗する検査が静的に存在するという意味で、変異実走結果ではありません。

| 変異 | 赤くなる検査 | 静的根拠 |
|---|---|---|
| M01 | あり（KILL） | `len(normalized)`ならT1のbatch/semantic `(3,2,1)` assertionが失敗（T:4219-4229）。 |
| M02 | あり（KILL） | `(2,1,2)` に `all` は偽となり、中央batch拒否の `Raises` が失敗（T:4297-4307）。 |
| M03 | あり（KILL） | first batchは適格2なので、first-only検査では拒否されずT3が失敗（T:4264-4307）。 |
| M04 | あり（KILL） | T1の全member distinctは2、実行distinctは1。前者へgateを替えると拒否期待が失敗（T:4197-4237）。 |
| M05 | あり（KILL） | 明示2・distinct1でもaborted sealは受理される正例（T:4097-4111）。 |
| M06 | あり（KILL） | 明示2・distinct2の正例が存在し、`<=`なら過剰拒否（T:4039-4057）。 |
| M07 | あり（KILL） | 3 countを1項ずつ改竄し、それぞれ固有理由で拒否（T:2136-2157）。 |
| M08 | あり（KILL） | candidate countが異なるstateでもpreseal SHA同値を固定（T:3146-3157）。countを残すと不一致。 |
| M09 | あり（KILL） | `candidate_min=3 / member_min=2` の負例（T:4310-4317）。 |
| M10 | **あり（KILL）** | reserve/commitの旧-only `cardinality`（T:2107-2121）、旧budget（T:2057-2063）、旧sealed（T:2158-2168）。R1時点のSURVIVEは解消。 |
| M11 | あり（KILL） | 同じ候補を2batchで反復してsnapshot union `1`を固定（T:2700-2719）。総和なら2になり失敗。 |
| M12 | あり（KILL） | 11 bytes/batchを独立literalとmax/max+1で固定（T:3301-3337）。旧6 bytesへ戻すと不一致。 |
| M13 | あり（KILL） | 既定1・distinct1のcertifiable正例（T:3997-4009）。 |
| M14 | あり（KILL） | 全tombstone batchを含む既定1・明示2正例（T:4114-4171）。fix前gateへ戻すとcount 0で過剰拒否。 |

## 残る所見

### RF-1 — must-fix — T2/T6の新Dが未記録

根拠: T2の参照規則は新Dへの記録が必須（A:52-56）、T6追随も同Dへの記録を要求（A:191-193）。D96は新設計判断と境界テストの同一変更単位を要求する（D:4269-4279）が、fixはdocs未編集で、現 decisions はD193まで（D:9398）。

成果物影響: `sealed_queries`・member行数を候補数と再解釈するconsumerを統治上禁止できず、受理集合変更のdecision/proof-chain参照が欠落する。

nitは0件です。

## 総括

1. **NO-GO**
2. 残る must-fix: **1件**（RF-1 / R1-6）
3. fixによる退行: **なし**。F80型の正例被覆後退、無許可の期待値変更、F5のcertifiable抜け道はいずれも認めない。