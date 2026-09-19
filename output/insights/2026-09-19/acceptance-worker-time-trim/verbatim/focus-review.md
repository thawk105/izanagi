## 判定

**NO-GO（所見の全閉鎖として）。** 実装修正は確認でき、focus3 に赤はなく、V の性能回帰も解消しています。
ただし B2 の「保守的」断定と B5 の script コメントが未訂正です。A/B 全走 rc の確認も提示資料では未成立です。

## 所見別の対応表

F＝`orchestrator/tests/test_s8b_ratified_freeze.py`、R＝`orchestrator/tests/test_run_tests_preflight.py`。行番号は修正後の現物。

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1/B1 | **closed** | F:1387 に `@in_sealed_fixture_process`。新正例は focus3 で成功、**19.312秒**。 |
| A2 | **closed** | F:62、1005–1021。深さ制限を撤去し、session 成分を `PYTEST_XDIST_TESTRUNUID or process token` に変更。標準配置・下位 dir・私設 session を採用し、外側 custom basetemp でも異なる session key は別 digest に分離される。 |
| A3 | **closed（裁定上）** | F:1099 の入力再読取りは残る。[fix2 報告:31](/home/SFC/tanab/.claude/jobs/28fa456a/fix2-u1-out.md:31) に未登録 tracked 入力読取りを明記。裁定の処置を満たすが、走行中不変の前提は残る。 |
| A4/B4 | **closed** | R:1405 の fixture 引数が4 parameter 全体に適用。4 node 合計は **42.678→0.211秒**。dispatch node 単体は微増、下表参照。 |
| B2 | **partial** | 数値は一致するが、[focus1-summary.md:68](/home/SFC/tanab/.claude/jobs/28fa456a/tmp/focus1-summary.md:68) に「差は保守的」「過小評価側」が残る。異条件の観測差として訂正が必要。 |
| B3 | **closed** | F:1426、1427、1431、1436 の builder 呼出しは4回（fresh／seed／hit／marker 破壊後の再構築）。prefix 実構築は3回。snapshot に blob 取得なし、F:1421 で g1/topology を直接比較。focus3 成功、19.312秒。 |
| B5 | **partial** | [ab_compute.sh:3](/home/SFC/tanab/.claude/jobs/28fa456a/tmp/ab_compute.sh:3) に `--basetemp` が残り、実 argv（:26–28）にはない。rc 記録はあるが、全走 rc の確認結果は本資料では未確認。 |
| B6 | **closed** | F:1059–1065 の metadata から `copied_files`／`copied_bytes` が削除済み。 |

A2 の依頼文にある「外側 custom basetemp を迂回」は、fix2 では置き換えられています。現物は `run-a`／`run-b` とも外側の同じ memo 親を採用し、**key で別 session の hit を防ぎます**。通常の xdist では走ごとに異なる UID、非 xdist の別 interpreter では異なる import 時 token を使う構造です。同じ UID を別走へ意図的に再使用する場合までの分離保証ではありません。

現物から抽出した2関数のメモリ内検査でも、標準 xdist／非 xdist、`mutation`／`baseline`、私設 session の採用、通常の `/tmp` tempfile の迂回、異なる token／UID の digest 分離を確認しました。配置検査の `is_dir` は模擬しており、実 filesystem での再実走ではありません。

## 派生値の検算表

指定された JUnit を `Decimal` で再集計しました。単位は **testcase 時間合計秒**で、wall time ではありません。全 file の合計・件数・fail/error/skip は親要約と丸め後一致します。

| file（`test_` 省略） | 段1 | focus1 | focus2 | focus3 |
|---|---:|---:|---:|---:|
| run_tests_preflight | 206.659 | 72.934 | 17.191 | 20.825 |
| s8b_holdout_freeze | — | 402.737 | 405.462 | 406.669 |
| s8b_oracle_driver | — | 2972.629 | 2439.312 | 未実走 |
| s8b_oracle_manifest | — | 3.107 | 2.524 | 2.747 |
| s8b_oracle_report | — | 43.836 | 40.355 | 40.543 |
| s8b_ratified_freeze | — | 134.856 | 165.211 | 157.120 |
| s8b_ratified_verify | 825.316 | 223.888 | 416.313 | 223.473 |
| s8b_verdict | — | 20.175 | 21.310 | 21.425 |
| t080_freeze_migration | — | 69.138 | 69.700 | 69.339 |

| 観測差（段1−各 focus） | focus1 | focus2 | focus3 | 親要約との照合 |
|---|---:|---:|---:|---|
| R | 133.725 | 189.468 | 185.834 | すべて一致 |
| V | 601.428 | 409.003 | 601.843 | すべて一致 |

段1のその他4 file も再集計：floor_campaign **1319.539秒**（class 内9 node を含む）、p3_b4 **398.389秒**、t1259 **12.061秒**、codex_reasoning_ab **345.735秒**。レビュー B の値と一致します。

| 四象限 parameter | focus1 | focus3 | 差（focus1−focus3） |
|---|---:|---:|---:|
| True-True-local | 13.600 | 0.068 | +13.532 |
| True-False-local | 14.438 | 0.065 | +14.373 |
| False-False-local | 14.638 | 0.066 | +14.572 |
| False-True-dispatch | 0.002 | 0.012 | −0.010 |
| **合計** | **42.678** | **0.211** | **+42.467** |

## 回帰

- **focus3 は1161 node、1159成功・2 skip・failure/error なし。** oracle_driver は対象外なので、同 file の fix2 後の成功までは主張できません。
- V は **223.888→416.313→223.473秒**。focus2 比 **192.840秒減**、focus1 比 **0.415秒減（約0.19%）**で、focus1 並みに戻っています。
- focus2 では深さ制限が `tmp_path/"mutation"` や `"baseline"` を memo 迂回にしました。fix2 の制限撤去と回復は整合します。例えば `test_frozen_at_head_not_generation_parent_rejected` は **1.050→14.103→1.112秒**です。
- F の focus1→3 は **22.264秒増**ですが、新正例が早期失敗 **0.212秒**から正常完走 **19.312秒**へ変わった分を含みます。R の focus2→3 は **3.634秒増**で、四象限の短縮は維持されています。
- focus1/2 は9 file、focus3 は8 file、段1は file 単独です。上記は観測差であり、因果的な削減秒・保守的下限とは扱えません。
- focus2/3 要約の「上位 node (focus1)」という見出しは古いままです。記載数値はそれぞれの走の値です。

## 総括

コード側の対象所見は裁定に沿って閉鎖でき、V の回帰も解消しています。
残件は B2/B5 の報告訂正と A/B 全走 rc の確認です。
A3 の未登録 tracked 入力読取りと走行中不変の前提は残ります。
本レビューではファイル変更・pytest 実行を行っていません。