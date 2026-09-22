## 所見

1. **must-fix — 新 build sink が既存の gate 到達検査と整合していない。**
   根拠: `orchestrator/campaign/silo_policy_coverage.py:334–348`、`orchestrator/tests/test_ccbench_spawn_sites.py:1988–2010,2919`。gate は `for macro in gate_macros` 内だけで呼ばれる一方、既存解析はループ0回の経路を残し、ループ内の証拠を build sink に持ち越さない。C2 が報告した赤見込みは現 HEAD に残っている。これは実行時の gate 不在を断定する所見ではなく、静的な受入条件との不整合である。
   **影響:** 新 sink の条件証拠を既存検査が認めず、受入全走の合格を妨げる。
   **修正案:** driver 内の gate 呼出し・集約を、既存解析が扱える支配関係に局所整理する。検査の緩和や deferred entry の追加で通さない。

2. **must-fix — prefix unlock 変異の方策が段4裁定と違う。**
   根拠: `orchestrator/campaign/silo_policy_coverage.py:67`、`patches/broken-silo-policy-no-prefix-unlock.patch:12,31–46`。段4 §3 はこの変異に `maxwait` を指定しているが、実装は `abort0`。変異 patch は上限出口と hook abort 出口の両方から unlock を除去するのに、即 abort 方策では待機・retry を経た上限出口を狙う実験にならない。
   **影響:** `all_pass=true` でも、裁定で指定した prefix unlock 実験を実施したことにならない。
   **修正案:** 当該変異と正常対照を `maxwait` に合わせる。case を追加する必要はない。

3. **should — hook 変異の合格条件と「単一理由」の裁定を整合させる必要がある。**
   根拠: `orchestrator/campaign/silo_policy_coverage.py:219–226`、`orchestrator/tests/test_silo_policy_coverage.py:58–63`。現実装は no-abort-hook で abort・lock・commit、no-lock-hook で abort・lock の複数照合が赤になることを要求する。これは段4 §4 の「この照合だけが赤」と一致しない。C2 の完全一致判定自体は C1 より厳しく、既存検査を弱めた変更ではない。
   **影響:** 現結果を単一照合の検出力証明として報告すると、観測が支える範囲を超える。
   **修正案:** 符号の連動による赤集合を正本に明記し、単一照合という主張を訂正するか、焦点方策を局所修正する。単なる期待値変更を仕様達成と扱わない。

4. **should — 正常対照を少なくとも5走削減でき、計算見積りも更新が必要。**
   根拠: `orchestrator/campaign/silo_policy_coverage.py:63–71,507–520`。3 hook＋wrong-reason の正常対照4本は、すべて同じ focus 方策・probe・legacy workload で、`focus/focus` と重複する。no-reload の正常対照も `focus/retry` と重複する。毎回新規 build しており、反復測定としての集計もない。
   **影響:** 検査範囲を増やさず、承認済み2.4 node時間の予算を消費する。
   **修正案:** 同一観測を各対照判定から参照する局所的な対応表で共有する。現状は報告どおり coverage 26 build・25 trace、smoke 10 build・10 trace＋5 bench。coverage の旧単価での換算は約0.23〜0.39時間となり、段4の約0.19〜0.32時間から増えている。依存 build・gate configure・既消費分も含めて残予算を再計算する。上限超過の実測はまだない。

5. **should — smoke 接続試験に timeout 経路が欠ける。**
   根拠: `orchestrator/tests/test_silo_policy_smoke_entry.py:82–139`、`orchestrator/campaign/silo_policy_coverage.py:282–284`。grammar 拒否・正常・compiler 不在・例外の4件はあるが、timeout から候補 build に到達しない接続試験はない。compile 単体の timeout 試験は存在する。
   **影響:** timeout 時に smoke が build を止めるという接続上の自己確認は未証明。
   **修正案:** 既存の timeout 用 fixture を再利用して接続試験を1件追加する。実装上は `timed_out` を拒否しており、現在の通過不具合を認めたわけではない。

## 削れる項目と足りない項目

- **削れる:** 所見4の重複対照5走。汎用キャッシュや新 framework は不要。
- **足りない:** 所見1・2の局所修正、timeout 接続確認、親担当の `patches/README.md` における適用順・診断用途の説明。
- 専用 lexer は段4で再利用不可の理由が明示されている。型付き parser、compile module 内の UBSan harness、85 fixture は今回の契約を扱っており、行数だけを理由に削除すべきではない。
- 既存 quarantine・effect gate・source digest・patchharness・計算用 helper は再利用されている。新 reject 理由、新台帳、E段 role、pipeline／p3_s4_loop への実装接続、候補ごとの sanitizer は追加されていない。
- 既存3軸の grammar・driver・既存負例 patch は変更されていない。既存 test の変更も、登録追加・件数追随・新 sink の確認が中心で、既存期待値の弱化や skip／xfail 追加は見当たらない。
- docs の第3列、planner 例外、trigger 注記、§7.3 の修正は設計 §8・D2214 決定8と整合する。設計採用と実測済みを区別する留保も適切。

## 報告と実体の食い違い

- **C2 の「指定された赤・緑集合」:** 実装は複数照合の赤集合に厳密一致するが、提示された正本の段4 §4にはその集合がなく、単一照合を要求している。所見3の仕様差が残る。
- **C1 の `_run:451`:** 現 HEAD の直接 subprocess 呼出しは457行。C2 による先行行の追加後の参照としては古い。
- A の10 file、C1 の14 file、C2 の10 file、coverage 30 case・53 check、smoke 5 case・30 check は整合する。manifest は85件で、grammar 受理21／拒否64、compile 受理64／拒否21というBの件数とも一致した。
- A・B・C1の「既存 tracked file を変更していない」は各単位の差分と整合する。C2も既存 entry の削除や行番号 pin の変更で検査を逃がしていない。
- 各子の未実走という留保は適切。過去の compiler 成功や UBSan 成功は今回再実行しておらず、報告の実測結果を独立確認したとは扱わない。

## 総括

**NO-GO（現差分の land 判定）。**

must-fix は次の2件。

1. 新 build sink と既存 gate 到達検査の不整合を局所修正する。
2. prefix unlock 変異・対照の方策を、裁定どおり `maxwait` にする。

scope 外の一般化や既存3軸の受理集合の変更は見当たらない。
hook 変異の主張を整理し、重複対照を削減して残計算予算を更新する。
本レビューは静的検査のみ。統合焦点走・coverage／smoke・変異自己試験の未取得結果を合格とは扱っていない。