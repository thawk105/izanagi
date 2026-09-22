## 所見ごとの閉じ方

対象 HEAD は `0a4b38abe0a1d95be0683fad5158d76d78c3b92a` と一致。静的レビューのみ実施しました。f8 の764 passed／0 failed／2 skipped は親の報告として扱い、coverage-5 の合格は認定していません。

以下、`C`＝`orchestrator/campaign`、`Q`＝`orchestrator/tests`、`P`＝`patches`、`J`＝`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2857-silo-policy-stage-c`。表の closed は、明記した実装修正の範囲です。

| 項目 | 判定 | 根拠・残事項 |
|---|---|---|
| 新所見1：出口の独立性 | **closed（実装）** | `P/broken-silo-policy-no-prefix-unlock.patch:8` は action-abort 側だけ、`P/broken-silo-policy-no-prefix-unlock-limit.patch:8` は上限側だけを条件分岐化。BREAK=1 と0の差は、それぞれ対象の unlock 1行だけで、他方の出口を保存する。`C/silo_policy_coverage.py:74` が別 patch を選択。`Q/test_silo_policy_coverage.py:344` は対象1行を除いたソースとの完全一致を検査する。分離後の timeout 実測は未確認。 |
| 新所見2：prefix 保持下の到達証拠 | **closed（実装）** | `P/instr-silo-function-policy-probe.patch:209`、`:238` は各出口で **`itr != write_set_.begin()` の場合だけ**新計数を加算。`C/silo_policy_coverage.py:648` は limit→`focus/retry`、conflict→`focus/abort0` を対応させ、同方策・同一の非空 workload・対応計数の正値を要求する。`:666` は timeout 判定との AND なので、到達0なら偽。`:636` は別走の証拠である限界を結果 JSON に明記。 |
| A2 | **partial** | 出口分離と到達条件は修正済み。coverage-4 は旧来の両出口を壊す patch の実測であり、分離後の独立検出を閉じる証拠にはならない。 |
| B4 | **partial** | `C/silo_policy_coverage.py:612` の対照5走の共有は維持。`Q/test_silo_policy_coverage.py:207` の現在の式は case 用24 build（依存物準備を除く）。指定資料には累積消費を反映した残予算の再計算がなく、coverage-4 の合格でもこの留保は解消しない。 |
| I2 | **partial** | prefix の出口対応は実装上解消。ただし、新しい probe と出口別変異を組み合わせた最終実測は未取得。下記の `wrong-reason` の計数追随漏れもある。 |
| J1 | **partial** | `C/silo_policy_coverage.py:659` で方策・workload・prefix 到達を要求し、`:665` で従来の `limit_aborts > 0` も維持。coverage-4 の `focus/retry` は `limit_aborts=123638`、上限変異は trace-timeout。ただし新しい prefix 計数は存在せず、その正値を実測で確認したことにはならない。 |

coverage-4 は `all_pass=true`、55 check 全件真でした。ただし両 prefix case は同じ旧 patch を使っており、`focus/abort0` もありません。最終構成は **33 case・61 check** で、旧結果をそのまま合格証拠として移用できません。

## 新たな所見

1. **should — `wrong-reason` の複製ループが新しい到達計数に追随していない。**

   **根拠：** `P/broken-silo-policy-wrong-reason.patch:12`、`:42` の BREAK=1 側には、更新 probe の `prefix_held_limit_aborts`／`prefix_held_action_aborts` の加算がありません。対応する通常側には `P/instr-silo-function-policy-probe.patch:209`、`:238` で追加されています。

   **影響：** この変異では、理由の変更に加えて新計数も欠落します。prefix 保持下で対象出口に到達しても、新計数は0のままで、出力の観測意味が通常側と一致しません。現在の `wrong-reason` 判定（`C/silo_policy_coverage.py:237`）は新計数を使わないため、これによる既存判定の偽合格は確認していません。

   **修正案：** 複製ループの両出口に同じ条件付き加算を追加する。理由代入だけを正常値に戻した BREAK=1 ソースが probe ソースと一致する検査を追加すれば、この追随漏れも検出できます。

その他の確認結果：

- **恒真化・必須集合の不整合は見つかりません。** `C/silo_policy_coverage.py:99`、`:111`、`:118` に新 case と6検査が登録され、`:260` の集合完全一致、bool 型検査、`:270` の判定再導出を維持しています。
- **`focus/abort0` の到達判定は抜けていません。** certified・commit・abort・lock・保存則・prefix action 到達を必須とし、変異側からも到達を再要求します。focus 方策用の状態符号照合を全て要求しないことは、今回の到達証拠の用途では欠陥と判断しません。
- **他の機構 patch に適用文脈の破損は静的には見つかりません。** 新計数の挿入は既存ハンクの文脈を分断していません。ただし上記の複製ループには意味上の追随漏れがあります。今回、実際の patch 適用は再実行していません。
- **fix-6b は対象検査を弱めていません。** build 数の式は現在24となり、余分な build を検出します。共有対照5件の固定集合・観測共有の検査を維持し、出口別 patch の名前と相違も検査しています（`Q/test_silo_policy_coverage.py:207`、`:210`、`:219`）。到達0・欠落・方策／workload 不一致・異なる timeout 理由を拒否する検査もあります（同`:282`）。

## 総括

**GO（静的な焦点再レビューの範囲）。must-fix：なし。**

- 前回の新所見1・2は実装上 closed。分離後の実測合格は未認定。
- 新たな should は1件：`wrong-reason` の複製ループへの新計数の追随漏れ。
- A2・I2・J1 は最終構成の coverage-5 待ちで partial。
- B4 は累積残予算の確認がなく partial。
- coverage-4 の55検査合格を、最終 HEAD の61検査合格として扱わない。