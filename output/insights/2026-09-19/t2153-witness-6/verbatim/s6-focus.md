## 総括

**焦点再レビューは GO。新規 must-fix／regressed は検出しませんでした。** ただし、段6全体の完了判定は **partial** です。変異 matrix の確定結果、受入全走、commit 済み insight は提示された証拠では未完了です。

対象は `7cc76d98b`。対象6ファイルは HEAD と一致しています。本レビューでは pytest を実行していません。実走の判断はすべて親の [focus-logs-after-fix.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/focus-logs-after-fix.md) に基づきます。

### A／B 所見の対応表（DW-O16）

| 元所見 | 状態 | 根拠・残件 |
|---|---|---|
| A-1／B：REPORT fixture の空前処理 | **closed** | REPORT 限定の無条件宣言で既定側にも本文が残る。修正前の2失敗は親の374 passedで消失。**親の実走で閉じた**。 |
| A-2：companion 負例の誤帰属 | **closed** | docstring が meaning arm 単体の検査と明記。同じ入力を supply も拒否することを明示した。 |
| A-2：SORT undef 負例への疑義 | **closed（refuted 維持）** | 無条件値参照が undef より前に残り、supply の差分を維持する。 |
| A-3：rung1 が文字列検査だけ | **closed** | 実 helper／実 factory の宣言を evaluator 境界で捕捉。新規テストを含む親の374 passedで閉じた。 |
| B：rung1 成果物の値の回帰検査が薄い | **partial** | 宣言の配線は閉鎖。新テストは family を置換するため、最終 JSON の未確立一覧そのものを検査するものではない。 |
| A-3／B：S1 の枝・成果物到達への疑義 | **closed（refuted 維持）** | 実 evaluator を通す合成 fixture と保存経路は維持。実 TU の確認は下記 official 実走が補う。 |
| A-4／B：受理条件の緩和・scope 超過 | **closed（refuted 維持）** | production 差分は登録簿＋2、件数説明、rung1 配線1行。factory、`DEFINE_SPECS`、比較・拒否機構は不変。 |
| A-4：共有 root の一般化 | **partial／scope 外** | 任意の cache 履歴に対する集合包含は証明していない。既存 backlog 境界を維持。 |
| A-5：変異登録の訂正 | **partial** | 期待 node の訂正は反映。検出成績と完全性は**親の実走で閉じる**。帰属の区別は下表。 |
| A-6／B：official production 実走不足 | **closed** | 最終登録簿による login／計算ノードの SORT・REPORT 成功を親ログが報告。 |
| A-6／B：段6全体の完了証拠 | **partial** | matrix は開始報告まで。受入全走の完了報告はない。 |
| B：追加閉包の未走 | **closed** | 指摘された追加7ファイルを含む閉包走が350 passed／2 skipped。skip を通過扱いにはしない。 |
| A-6／B：5分契約 | **partial** | 今回の再走は6.68秒／80.49秒。以前の344.57秒の閉包全体や増分・受入全走の時間契約まで閉じる証拠ではない。 |
| B：provenance | **closed** | commit の author／reviewer／integrator trailer を確認。親ログは全史11,631件、新規違反なし。 |
| B：insight 未作成・記録漏れ | **partial** | commit 差分は実装・テスト6ファイルのみ。insight ディレクトリは未追跡であり、commit 済みの永続記録としては未閉鎖。 |
| B：target 構成・SORT 値差分への疑義、p3／S6 見送り | **closed** | 修正で前回の判定を覆す変更なし。p3／S6 は `declaration=None` を維持。 |
| B：重複 assert 等の削減候補 | **partial（任意 nit）** | 残存するが、正しさや成果物を阻害する修正要求ではない。 |

### 修正の実効性

[REPORT fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_condition_meaning_gate.py:255) の `int izanagi_owner_present = 1;` は両値で同じ本文を残し、`preprocess-output-empty` の原因だけを取り除きます。REPORT の条件枝は保持され、companion の `#define` も追加されません。他 macro はこの追加条件に入らず、production の空出力拒否も不変です。後半の BACKOFF_FIXED 同席検査まで含め、親の実走で閉じました。

[実 helper test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/tests/test_silo_ladder_rung1_driver.py:53) は **DW-O14 を満たします**。検査対象の `_require_condition_gates`、request 生成、factory、登録簿は実物で、capture／evaluator／family が外側の seam です。BACKOFF_FIXED・RUNG1 の宣言が `None`、REPORT が厳密に `ConditionalBranchMeaningDeclaration`、macro と `source_rel="cc/silo/ycsb_silo.cc"` が正しいことを検査しています。

### mutation-spec の照合

[mutation-spec.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-6/mutation-spec.json) の期待集合に、レビューAが指摘した **node の反映漏れ・過剰は静的には検出しませんでした**。全実行集合に対する完全性は親の matrix で確定してください。

| 変異 | 期待 node・帰属の確認 |
|---|---|
| m0 | 空集合／SURVIVED。コメント変更のみ。green baseline は親ログで確認済み。 |
| m1 | **7 node**。tuple pin、domain pin、registry SORT、SORT 正例2件・undef負例、S1正例を収録。fixture 経由4件は **KeyError**、S1は宣言型 assert。meaning の unestablished 検出に一括帰属しない。 |
| m2 | **7 node**。tuple pin、domain pin、registry REPORT、REPORT正例2件・companion負例、実 helper test を収録。fixture 経由4件は **KeyError**。文字列 test は含めていない。 |
| m3 | patch 束縛の **1 node**。独立した期待逐語との不一致による検出。通常正例を追加する必要はない。 |
| m4 | 文字列 pin と `test_condition_gates_pass_real_factory_declarations_to_evaluator` の **2 node**。後者は REPORT 宣言型の不一致を検出する。 |
| m5 | `test_compile_time_factory_rejects_nonpaired_values` の3 macroの **`0-0` のみ**。`0-1` は含まない。宣言可能集合の拡大への検出であり、family admit の証明ではない。 |
| m6 | SORT正例2件と `test_sort_undef_rejects_family_with_supply_still_green` の **3 node**。正例は一意性違反、undef負例は supply green 前提の崩壊。全件を一意性検出にまとめない。 |
| m7 | registry REPORT、REPORT正例2件、companion負例の **4 node**。registry node は meaning 単体、正例は supply／meaning 両方に影響、負例は期待理由コードの不一致。meaning 単独の family 拒否には帰属しない。 |

spec 自体には帰属説明欄がありません。**node 集合の訂正は反映済みですが、上記の帰属を親の変異結果台帳に残す必要があります。**

### official 完了条件と主張境界

裁定 plan v2 §6 の **official cell 条件は、親の実走で閉じました**。最終 production 登録簿・official 同形供給で、pegasus02 と bnode055（job `10879.nqsv`）の双方において SORT／REPORT が supply green、meaning `(1,1)/(0,1)`、admitted、未確立一覧 `[]`。digest・bytes・owner SHA・compiler の一致も報告されています。§6全体は matrix・受入全走待ちです。

- **合成 fixture と実 TU：** fixture は局所機構の検査、official cell は当該実 TU・入力の枝選択の証拠であり、本文の正しさや動的到達性までは示しません。
- **CLI 単独発行：** REPORT の CLI record は companion RUNG1=1 下の枝選択を示し、driver の同時要求や最終成果物への保存を単独では証明しません。
- **共有 build root：** 観測した入力での成功・一致を、任意の CMake cache 履歴での受理集合不変へ一般化しません。

DW-G05：新規の real must-fix／regressed はありません。未完了の検証・永続記録を完了済みと扱うと成果物台帳が過大主張になるため、既存の **partial** は親で閉じてください。