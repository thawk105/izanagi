## 所見一覧 (番号・must-fix/nit・real/plausible/refuted・file:line)

指定された7ファイルをすべて読み、差分・展開済み実装・現物3 campaign を確認した。静的レビューのみで、CLI・pytest は実行していない。以下、`caller` は `orchestrator/campaign/p3_b4_prerun_caller.py`、`test` は `orchestrator/tests/test_p3_b4_prerun_caller.py` を指す。

1. **must-fix / real — 使用しない3 field の必須検査が拒否条件を増やしている。**
   `caller:74` は `direction`・`magnitude`・`delta_pct` の欠落でも campaign 全体を拒否する。しかし、この呼び手は3 field を使用しない。例えば `{"iteration":1,"result":"rejected"}` から候補と不足の所在を読めても、12 field の不足報告へ進めない。確定裁定の入力解釈不能を超える検査であり、DW-G05 の観点で削減対象。
   **最小是正:** 行が dict であることと、呼び手が実際に読む `result`・`iteration` の存在確認に絞る。既存 test の期待値変更は不要。

2. **nit / plausible — 静的な欠落理由が、探索済みの不存在証明に読める。**
   `caller:27` の “No artifact assigns …”、`:37` の “No per-attempt record establishes …” に対し、実際に開くのは `:62`・`:63` の checkpoint と lock だけ。`artifact_path` も常に checkpoint を指す（`:97`）。保存形式の制限としては妥当だが、WAL・別保存 proposal・事前登録を探索した結果ではない。
   **最小是正:** collect の docstring に「12項目は現行保存形式の既知の制限に基づく静的な不足分類であり、artifact_path は候補の観測位置を示す」と明記する。resolver や追加探索は不要。

3. **nit / real — 内部関数の戻り値は裁定の表記と異なる。**
   `caller:49` は `(batch, missing, campaigns)`、`:120` は `(payload, rc)` を返す。裁定の `(batch, missing)`、`issue(batch) -> dict` とは逐語的に異なる。件数報告と終了コードの受け渡しに閉じた差分であり、外部 JSON 契約の破壊や一般化ではない。author 報告も差分を明記しているため、変更必須とはしない。

4. **must-fix 指摘候補 / refuted — 常に空 batch を返すこと自体が裁定違反。**
   `caller:90`・`:104`。確定仕様では全候補に12項目の出所がなく、非空入力は必ず不足停止する。利用されない不完全行を作らないことは、今回の観測可能な契約と等価。非空組立て能力がない点も `caller:3` に明記されている。

5. **must-fix 指摘候補 / refuted — 例外型と追加 test が要求外の機構。**
   `caller:41`、`test:199`・`:229`。例外型は要求された typed stop の伝達手段。追加 test は解釈不能時の発行禁止と全候補集計を確認する。削除対象ではない。

6. **nit 指摘候補 / refuted — bootstrap 文言、英語 message、相対 path が不適切。**
   `caller:32`・`:84`・`:143`。bootstrap 文言は必要な所属証拠を述べており、集合や固定時点を決定していない。英語は既存 B-4 module と整合する。相対 path の出力も契約違反ではない。

## 裁定との差分

CLI が出す JSON を key 単位で照合した。

| 分岐・対象 | 実装の key | 判定 |
|---|---|---|
| 不足停止 | `reason`, `missing`, `candidate_count`, `campaigns` | 一致 |
| 発行器拒否 | `reason`, `detail`, `candidate_count`, `campaigns` | 一致 |
| 成功 | `issued`, `candidate_count`, `campaigns` | 今回のレビュー指示の契約に一致 |
| `issued` 内 | `receipt_path`, `receipt_sha256`, `issuer_commitment_sha256`, `manifest_row_count` | 4 field exact |
| 入力解釈不能 | `reason`, `detail`, `campaign_root` | 一致 |
| `campaigns[]` | `campaign_root`, `driver`, `whiteboard_rows`, `rejected_rows` | 4 field exact |

根拠は `caller:83`、`:129`、`:134`、`:149`、`:157`、`:161`。この契約に対する余分な key・欠落 key はない。tuple は `json.dumps` で JSON array になる。

ただし、**段4文書の成功例そのものは `{"issued": ...}` だけを記載している**。これを閉じた外形と解釈すれば、実装の成功 CLI には `candidate_count`・`campaigns` が追加されている。今回のレビュー指示はその2 key を明示的に要求しているため、不具合とは判定しない。T5 は `issue()` を直接呼ぶので、同関数の戻り値が `issued` のみであることを検査している（`test:175`）。

`missing[]` は `campaign_root`・`whiteboard_index`・`iteration`・`field`・`artifact_path`・`artifact_key`・`explanation`。裁定の所在情報要求を満たす。内部関数の戻り値変更は所見3のとおり。

## 静的な欠落表の是非

**今回の確定仕様に限れば、行を作らず静的な12項目を返す方式は等価と判断する。**

構成可能な5 field のうち、driver は campaign 情報として保持され、候補順は argv 順×配列順、whiteboard result は選別で確定する。schema version と reason は定数として与えられる。しかし残り12項目が未成立なので、完全な `B4ScheduledAttemptInput` は作れない。使われない部分行を新設する是正は最小性に反する。

ただし、実測されるのは campaign の読取り・候補位置・件数であり、12種類の外部証拠を個別探索した結果ではない。追加 field が将来保存されても、この実装は取り込まず同じ不足を返す。これは将来の発行経路ではないという裁定の限界と一致する。

`artifact_path` を WAL や事前登録へ変更すると、未読資料を検査したように見える可能性もある。今回は checkpoint を**候補の観測位置**として維持し、静的分類との区別を説明する所見2の文言修正が最小である。

## explanation と docstring の文言

12項目の内容は、次の限定の下で妥当。

| field | 評価 |
|---|---|
| `attempt_id`, `block_id` | B-4 attempt／block への対応が未同定という説明は妥当。“No artifact” は探索範囲を限定すると正確。 |
| `digest_red_classes` | checkpoint に WAL digest への結合 key がないという限定された記述で妥当。 |
| `workload`, `calibrated_workload_member` | precursor と校正 workload の対応・所属証拠が不足するという説明で妥当。lock の設定値だけでは埋まらない。 |
| `initial_proposal_sha256` | D39 決定3と D1846 に整合。whiteboard／genome／src_token を proposal document exact value の代用にしていない。 |
| `bootstrap_member` | “fixed in advance” は所属述語の必要条件。集合の定義・固定時点を裁定済みとは述べていない。 |
| `reference_tps`, `reference_snapshot_hash`, `reference_receipt_hash`, `reference_is_unique` | 一意な祖先参照点とその対応証拠が未成立という説明で妥当。repo 全域の不存在証明とは扱わない。 |
| `arm_digest_received` | attempt 単位の受領根拠が不足するという説明で妥当。lock の `reflux="on"` を真偽値へ転用していない。 |

D39 は `docs/decisions.md:1100` 付近、D1846 は同 `:55897` 以降を確認した。別保存された元 proposal の利用まで禁止する裁定ではなく、今回の実装もその禁止を追加していない。

module docstring は非空 batch 構成不能、成果の限定、全件性を証明しないこと、`rejected` 選別の依頼上の理由、SUCCESS に関する訂正を含む（`caller:3`）。

test 冒頭の docstring は、201行 fixture が issue／serialize の検査であり、現物の非空組立てや production publication の証拠ではないと明記する（`test:1`）。T5 単独の docstring と合わせて十分。

既存 issuer・ledger・floor issuer の docstring も英語である。日本語を含む argparse description は通常の Unicode 文字列であり、静的に文字化けを示す根拠はない。標準 formatter による改行の畳込みはあり得るが、`-h` は未実行。

## 入力解釈不能の集合と DW-G05

現物の3 checkpoint は、全7行とも5 key を持っている。そのため、所見1は今回の現物実行を妨げない。

検査の線引きは次のとおり。

- checkpoint／lock の不存在・読取り不能・JSON 不正、object でない最上位、whiteboard 非 list、未知 trial：要求された解釈不能の処理。
- whiteboard 行が dict でない、使用する key がない：候補判定・所在報告に必要な最小検査。
- 未使用の `direction`・`magnitude`・`delta_pct` の必須化：呼び手の責務に不要な検査。

`test_unreadable_campaign_never_calls_issuer` の6 parameter は保持してよい。`row` ケースは `[null]` であり、未使用3 key の必須化を正当化する test ではない（`test:219`）。

`test_all_candidates_have_all_missing_fields` も保持してよい。T2 の1候補だけでは確認できない、複数 campaign・複数候補への全件集計を検査している。新しい gate・台帳・carrier・ID 規約は追加されていない。

## 現物での実行の予測

現物を読み、次を確認した。

| campaign | lock の trial | whiteboard 行数 | rejected |
|---|---|---:|---:|
| base | `p3-s4-loop` | 4 | 0 |
| sort | `p3-s5-sort-loop` | 1 | 0 |
| trigger | `p3-s8a-trigger-loop` | 2 | 0 |

全7行が `success`。sort は最上位 `iteration=2` だが、配列の行数は1であり、実装は正しく `len(whiteboard)` を報告する。

入力・実行環境が変わらず、先行する発行器検査と乱数取得が成功する場合、予測する stdout は次の1行、rc は **2**。

```json
{"campaigns": [{"campaign_root": "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387", "driver": "base", "rejected_rows": 0, "whiteboard_rows": 4}, {"campaign_root": "output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d", "driver": "sort", "rejected_rows": 0, "whiteboard_rows": 1}, {"campaign_root": "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5", "driver": "trigger", "rejected_rows": 0, "whiteboard_rows": 2}], "candidate_count": 0, "detail": "fewer than 201 eligible scheduled attempts", "reason": "design_not_feasible"}
```

根拠は、候補選別 `caller:78`、空 tuple の返却 `:104`、発行器呼出し `:160`、接頭辞除去 `:132`、件数付加 `:161`、1行出力 `:165`。

相対 path は `.resolve()` されず、今回の表記のまま出る。絶対化は必須ではない。親の記録に実行 cwd を添えれば所在を再現できる。

publication root は読取り時点で不在、親 `output/` は存在した。発行器の `_ensure_new_publication_root` は存在検査のみ（`p3_b4_prerun_issuer.py:259`）。空 batch は manifest 生成後の `:840` で拒否され、`:882` の `_publish_bundle` に届かない。root を作る `os.mkdir` は同 `:648` にあるため、**この実行は root を作らない**。実行後の不在は、親による実測確認が必要。

## 段 3 レンズ B 所見の反映

| 段3所見 | 反映 |
|---|---|
| 1：非空 batch を組めない | `caller:3` に明記。成果の過大認定なし。 |
| 2／N5：SUCCESS と適格性の混同 | `caller:7` で明示訂正。ledger の `SUCCESS` 定義とも整合。 |
| 3：registry 全件性を証明しない | `caller:5` に明記。 |
| 5：条件9の過大表現禁止 | code／author 報告に条件9を充足したとの主張なし。親 insight でも充足数を増やさないこと。 |
| 7：成功試験の認定範囲 | T5 は実発行器と201行 fixture を使用。test docstring と author 報告が issue／serialize に限定。 |
| 10：候補0では欠落経路を通らない | そのとおり。T2 と全候補 test が合成入力で欠落経路を検査する。現物での12項目欠落の実測とは区別が必要。 |

author 報告は、完了したとする試験、中断した合同焦点走、未実施の現物 CLI・変異試験・受入全走を区別している。今回のレビューでは実行ログを検証しておらず、author 記載の成功件数を独立に認定していない。

## 総括

**must-fix は、未使用3 field を必須にする検査の削減1件。** 静的欠落表の根拠と観測位置の意味を明記する文言改善を nit とする。

JSON 契約、N5訂正、成果範囲の限定、実発行器による T5 の位置付けは適合している。現物3 campaign からは候補0、空 batch で発行器へ1回到達し、`design_not_feasible`・rc=2・publication root 未作成を予測する。非空発行経路の完成、条件9の追加充足、T-2632達成の証拠にはならない。