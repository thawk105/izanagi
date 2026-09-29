## 所見

- **A1 — must-fix。** README §0（11行）「coder → … → critic の 1 iteration を 1 呼び出しで進める」。出所 `orchestrator/campaign/p3_s4_loop_policy.py:434-439,462-484` では `drive_iteration` は生成済みの `proposal` と `auditor` を受け、評価後に critic 用 digest を書く。`output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md:115-116` は役割を呼ぶ round tool を後続実装としている。**現行の一呼び出しが coder と critic まで実行する、という記述は誤り。** 評価 driver と外部の役割呼出しを分けて書く。

- **A2 — must-fix。** README §0（12行）「記録された 6 つの理由」、§3.2（78行）の R6。出所 `docs/related-work/shinka-deepdive.md:14-18` の反面教師は inspiration 注入、交叉、prompt evolution、並列評価群、fuzzy patch 適用で、R6 の reward hack は `docs/decisions.md:99-103` の **D9** にある。**D9 を Shinka 深掘りに記録された理由として数えている。** R6 は「関連する別判断」に移し、要約の件数と内訳を数え直す。

- **A3 — must-fix。** README §0（16行）・§6.1（220、228行）「検査時間は trace の取引数に比例する」「候補 約540万件／本」。出所の `…-c4efe427/runs/wal.jsonl:3-4` は性能検査の取引数が **5,424,323 件**、区間が約 **85.9 秒**。`…-4e8009c5/runs/wal.jsonl:3-4` は **7,990,485 件**、約 **74.4 秒**。**もう一方の候補は取引数が多いのに区間が短く、比例という実測結論に反する。** 540万件は該当候補に限定し、比例の断定を撤回する。

- **A4 — must-fix。** README §5.4（202行）「1 段目で certified の子」。出所 `docs/decisions.md:72080` は偵察の「診断 build は NON_ADMISSIBLE で certified 候補とは称さない」と明記する。同じ README の202行後半もそれを認めており、**一段目の資格を誤記している。** 「一段目の検査を通過した子」などに改め、certified は本評価後に限定する。

- **A5 — should。** README §4.2（137行）「草稿 §6 と同じく endpoint として 5 session 測り直す」。出所 `docs/silo-policy-generator-contrast-preregistration.md:257-266` は**各系列の自系列候補**から endpoint を選び、5 session 測り直す規則。README の「母集団の中の最良」は選択単位が異なる。5 session の再測定だけを流用したと明記する。

## 照合して一致した事項

主な一致を **約15件**確認した。例として、`make_policy_coder_input` の履歴7 key と診断6 field、停止値10回・3,600秒、方策設定に同時検査 key が無いこと、pair job の Elapse **741・793秒**、WAL の候補区間 **434・491秒**、D2240 の上位3点と1%以内の一致、D2263 の4 arm・未発効、runbook §7.5 の独立 job 並行投入がある。費用の算術も、規模 M の `48 × 0.206 + 0.325 ≈ 10.2`、規模 L の `720 × 0.206 + 30 × 0.325 ≈ 158` と一致した。

## 照合できなかった事項

Shinka の **62技法の個別記録**は、指定された worklog によれば session 内・非コミットで、照合できない。`orchestrator/`・`tools/` 全体で関連実装が「0件」という網羅的な不在主張、wave 開始時の gate 記録、週上限そのものの値も今回の照合では確証を得ていない。指定どおりテストは実行していない。

## 総括

must-fix **4件**、should **1件**。  
現状は一次資料として **NO-GO**。