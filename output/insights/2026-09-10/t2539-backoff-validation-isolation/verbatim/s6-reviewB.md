## 親の実測への判定

`early-unlock` の rc=0 は、段 4 が定めた V に対しては正しいです。patch は `writePhase()` を編集しており、`validationPhase()` からの下向き呼び先閉包には入りません（`patches/broken-silo-early-unlock-validation.patch:5-16`）。ファイル名の `validation` は判定材料ではありません。

一方、この結果は「rc=0 は正しさ検査を省略できる」という読みを明確に破壊する positive control です。`claim_boundary` は write/writeback と serializability を非保証として挙げているため、全文を読む人には境界を説明できています（`tools/check_silo_validation_isolation.py:34,42-52`）。しかし、その境界を検査する実運用 consumer はなく、test も early-unlock を固定していません。したがって現状では誤用を機械的には防げず、worklog には「既知の正しさ破壊 patch も同じ rc=0 になる」と明記すべきです。

## real 所見

### 1. anomaly 即 reject は宣言だけで、発火する実装ではない

- 何が壊れるか: `runtime_anomaly_policy` は「無条件に即 reject」と断言しますが、checker は runtime anomaly を入力として受け取らず、rc=0 を通常の成功として返します。規律 2 の実効的な防壁として扱うと弱体化になります。
- 根拠: policy は定数文字列だけです（`tools/check_silo_validation_isolation.py:38-40`）。`analyze()` の入力は repo と patch だけで（`:1135-1139`）、最終 verdict は intersection の有無だけで決まり（`:1228-1230`）、rc=0 もそこから直接返ります（`:1242-1247`）。test は文字列一致しか確認しません（`orchestrator/tests/test_silo_validation_isolation.py:272-274`）。
- 具体的な反例: 親の実測では early-unlock が rc=0 です。別の実走がこの variant の anomaly を検出済みでも、この checker 単独の出力と終了コードは変わりません。
- 直し方: この wave 内では policy を構造化し、少なくとも `enforced_by_this_checker: false` と外部 anomaly evidence が必須であることを明示します。runtime evidence と合成して reject する consumer の新設は scope 外なので裁定パッケージへ送ります。将来の consumer には「anomaly=true なら静的 verdict に関係なく reject」の負例 test が必要です。

### 2. claim boundary は未消費で、test 名に反して完全には固定されていない

- 何が壊れるか: production consumer が存在せず、重要な非保証が改変されても現 test が通ります。機械可読であるだけで、利用者が rc しか見なければ early-unlock の意味を失います。
- 根拠: exact schema/verdict の repository 内参照は checker 自身とこの test だけです。CLI consumer はありません。さらに `test_claim_boundary_records_every_required_non_guarantee`（`orchestrator/tests/test_silo_validation_isolation.py:261-277`）は、実装にある `pure_timing_or_side_effect_freedom_proven`（`tools/check_silo_validation_isolation.py:35`）も、`does_not_prove` 全体（`:42-52`）も検査していません。
- 具体的な反例: `pure_timing_or_side_effect_freedom_proven` を `True` にする、または `serializability_or_dynamic_anomaly_absence` を削除しても、この boundary test は失敗しません。early-unlock 自体も test 入力にないため、最重要の境界例が固定されていません。
- 直し方: hardcode した完全な dict の equality と exact key set を test に置きます。さらに early-unlock を実 patch の境界 test として追加し、rc=0、write/writeback 非保証、serializability 非保証を同時に固定します。自動 consumer の新設は裁定パッケージ候補ですが、少なくとも worklog consumer はこの反例を明記して境界を実際に消費する必要があります。

### 3. patch 内のコメントや marker が macro 判定を動かせる

- 何が壊れるか: 外部由来の patch 本文を単なるデータとして扱い切れていません。コメント内の `#if` 文字列が conditional macro として解釈され、意味のないコメント編集だけで verdict を変えられます。また、conditional marker と同じ edit span にある別の file-scope 内容まで `macro-inspection` として消費されます。
- 根拠: `_conditional_macros()` はコメントを除去せず raw 行を走査します（`tools/check_silo_validation_isolation.py:1015-1023`）。function region に入らない span は、macro が一つ見つかるだけで span 全体が分類済みになります（`:1083-1105`）。その macro は closure 内の実 token と照合され、intersection を生成します（`:1115-1132,1215-1223`）。
- 具体的な反例: `cc/silo/include/transaction.hh:100-104` の doc comment 内へ、行頭が `#if TRACE` の一行を追加すると、C++ 上はコメントのままです。しかし checker は `TRACE` の macro edit と解釈し、validation closure にある実際の `#if TRACE`（`external/ccbench/cc/silo/transaction.cc:390,410`）へ交差させられます。
- 直し方: span 単体の raw text ではなく、pre/post image 全体を lexical state つきで解析し、コメントと literal 内の directive-like text を除外します。`macro-inspection` に分類する場合も、span の非コメント token が対応する conditional directive だけであることを確認し、それ以外を含めば `UNCONSUMED_EDITS` にします。これは副作用検査の新設ではなく、既存分類器の信頼境界修正です。

## refuted 所見

- verdict 名そのものが正しさ認証を表す、という疑いは否定します。`PASS`、`accept`、`safe`、`certify`、`license` は verdict、test 名、docstring に存在せず、`NO_STATIC_VALIDATION_CLOSURE_INTERSECTION` は十分限定的です（`tools/check_silo_validation_isolation.py:2-7,22-23`）。`POSITIVE_PATCH` は test 内部の対照名にすぎません。
- early-unlock が parser の false negative だという疑いも否定します。V は下向き閉包であり、`writePhase()` を意図的に除外しています。非保証項目の過不足についても、親の probe で観測した early-unlock、abort instrumentation、他 protocol、ERROR の各類型は、それぞれ write/writeback、abort/retry lifecycle、other protocols、error policy に記載されています。問題は記載不足より実効消費の欠如です。
- Silo 以外の patch が誤って「交差なし」になるという実測上の疑いは否定します。提示された mocc、cicada、ss2pl patch はすべて rc=2 `ERROR` で、`other_protocols_covered: false` もあります。ERROR code が protocol 専用でない点は説明性の弱さに留まり、受理にはなっていません。
- 既存 test の期待値や既存 gate の受理集合を変えた形跡はありません。`git status --short` では新規 2 file だけで、既存 consumer への接続もありません。tmpdir patch は現物 source から都度生成され、揮発した実走 payload を期待値として焼き込んではいません。
- テスト実走は本レビューでは行っていないため、緑とは判定していません。

## 依頼への回答としての射程

本 checker が示せるのは、`silo-backoff-fixed.patch` の全 6 edit span が分類され、その function edit と変更 macro が `cc/silo/transaction.cc` の `TxExecutor::validationPhase()` を根とする raw-config union の下向き呼び先閉包に静的には交差しない、という限定事実です。これは validation 実装そのものへの直接編集がないことを示す補助根拠にはなりますが、backoff 変更後も abort/retry の待ち時間を介して interleaving と validation 判定系列は変わり得ます。また commit consumer、write/writeback、他 protocol、動的 anomaly absence は覆いません。したがって既存 1 group の認証を policy 2 の未実行 12 seed や policy 0 の未実行条件へ拡張する根拠にはならず、実走で anomaly が一つでも検出された variant はこの静的結果に関係なく reject すべきです。

## 総括

V に対する静的判定は正しいが、正しさ検査省略の根拠にはならない。  
必須修正は claim の非強制性と early-unlock 境界例の固定、コメント由来 macro 判定の除去。  
runtime evidence との強制合成は scope 外の裁定パッケージ候補。