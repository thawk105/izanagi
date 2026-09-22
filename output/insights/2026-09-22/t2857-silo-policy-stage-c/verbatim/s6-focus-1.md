## 所見ごとの閉じ方

対象 HEAD は `c7fc4846c81ea9204d94bfb98125d839e443ea2d` と一致。静的検査と既存結果の読み取りのみを行い、build・pytest は実行していません。coverage-4 は未取得として扱います。

以下、`C`＝`orchestrator/campaign`、`Q`＝`orchestrator/tests`、`P`＝`patches`、`J`＝`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2857-silo-policy-stage-c`。

| 項目 | 判定 | 根拠 file:line・閉じ方 |
|---|---|---|
| A1 | closed | `C/silo_policy_coverage.py:371`：gate 集合取得と成功確認が configure/build を支配。解析側の緩和なし。 |
| A2 | partial | 同`:67`、`:635`：上限側を retry に分離し到達条件を追加。ただし両出口の独立検証には新所見1・2が残る。最終実測も未取得。 |
| A3 | closed（裁定上） | `J/s6-ruling-1.md:20`、`:29`：M-CHK-EMPTY を単一理由変異から削除。`C/silo_policy_coverage.py:257` の冗長な拒否は維持。KILLED の証拠としては扱えない。 |
| A4 | closed | `P/instr-silo-function-policy-probe.patch:136`、`C/silo_policy_coverage.py:213`：同一 worker の commit 後比較を別計数し、一致正・不一致0を要求。 |
| B1 | closed | `C/silo_policy_coverage.py:371`、`Q/test_ccbench_spawn_sites.py:2935`：成功確認と sink の pin が整合。 |
| B2 | closed（方策指定の訂正） | `J/s6-ruling-5.md:8`、`C/silo_policy_coverage.py:68`：maxwait 指定を明示的に retry へ訂正。検出期待は維持。検証成立全体は A2 の留保付き。 |
| B3 | closed | `J/s6-ruling-1.md:19`、`C/silo_policy_coverage.py:234`：単一照合という主張を撤回し、宣言した赤集合への完全一致を維持。 |
| B4 | partial | `C/silo_policy_coverage.py:80`、`:609`：重複対照5走の共有は完了。累積消費を含む残予算の再計算は指定記録だけでは確認できない。 |
| B5 | closed | `Q/test_silo_policy_smoke_entry.py:142`：実 timeout fixture で候補 build 未到達を確認する試験を追加。 |
| F1 | closed | `C/silo_policy_coverage.py:334`、`:371`：空集合・不成功を拒否してから build。 |
| F2 | closed | `Q/condition_gate_test_support.py:26`、`:39`：cache 変数と universal definition を追加。 |
| F3 | closed | `C/silo_policy_coverage.py:283`、`:558`：既存 `quarantine(write=False)` を経由し、全検査後に書き込む。入口閉集合の拡張なし。 |
| F4 | closed | `C/screening_driver.py:71`、`:98`：3 macro の既定値0を追加。要求生成は引き続き genome の macro に限定。 |
| G2 | closed | `C/condition_meaning_gate.py:85`、`C/silo_policy_coverage.py:369`：重複 companion を除去し、軸値は cache 経路から供給。 |
| G3 | closed | `Q/test_ccbench_spawn_sites.py:2935`、`C/silo_policy_coverage.py:379`：本 wave の pin のみ追随。 |
| G4 | closed | `C/silo_policy_coverage.py:435`、`:620`：`arguments`／`command` 両形式を処理。 |
| G1 | closed（原因断定は訂正済み） | `C/silo_policy_coverage.py:304`、`:352`：1 gate＝1 macro。旧失敗原因の断定は `J/s6-ruling-3.md:10` の H2 が訂正。 |
| G5 | closed | `C/silo_policy_coverage.py:318`、`:743`：両 arm の状態・理由と canonical 記録を保存。 |
| H1 | closed | `C/silo_policy_coverage.py:703`、`:738`：両 mode とも準備 stock build が最初の gate より先。拒否記録も保持。 |
| I1 | closed | `C/silo_policy_coverage.py:387`：owner TU と YCSB target 出力で1行へ絞り、0行・複数行を拒否。 |
| I2 | partial | `J/codex/s6-fix-4.md:7` の外部交点の修正は概ね一致。ただし prefix timeout と出口の対応には新所見1・2が残る。 |
| J1 | partial | `C/silo_policy_coverage.py:645`：指定された方策・workload 一致と上限 abort 正を実装。期待緩和なし。ただし証拠の射程と最終実測が未完。 |

`regressed` と断定する項目はありません。

## 新たな所見

1. **must-fix — `abort0` による action-abort 出口の独立性が成立していない。**

   根拠：`J/s6-ruling-1.md:15` は「action-abort 出口だけに到達」としますが、`P/silo-function-policy-variant.patch:158` と`:164` は、hook 呼出しの有無によらず各周回を計数します。CAS 失敗後もループは続きます（`external/ccbench/cc/silo/transaction.cc:172`）。他 worker の更新により、ロック解除済みの異なる値を返す CAS 失敗が32回続けば、`abort0` でも上限出口へ到達できます。

   一方、`P/broken-silo-policy-no-prefix-unlock.patch:12` と`:41` は両出口の unlock を同時に削除し、`C/silo_policy_coverage.py:226` は timeout だけを受理します。したがって action-abort 側の unlock を正常に戻しても、上限側の漏れによる timeout を当該 case の成功として受理できる構造です。現在の timeout が実際にこの経路だったという断定ではありません。

   **影響：** action-abort 出口を検証していない結果まで、出口別検証済みとして受理・報告できます。

   修正案：出口ごとの変異へ分け、各変異が他方の unlock を保存することを確認する。方策名と `target_exit` の照合だけでは独立性の証拠になりません。

2. **should — J1 の到達条件は「prefix を保持した上限出口」の証拠ではない。**

   根拠：`P/instr-silo-function-policy-probe.patch:205` の `limit_aborts` は、`itr == write_set_.begin()` の場合も加算します。`C/silo_policy_coverage.py:645` は別実行の probe 有効な `focus/retry` の合計だけを要求し、変異実行は probe 無効です（同`:68`）。

   この条件は同方策・同 workload で上限到達が観測されたことを示しますが、prefix 保持下の到達や変異実行自身の到達は示しません。

   **影響：** 「同構成の別走で上限到達」という証拠を、「対象 unlock の実行機会を確認済み」へ拡大解釈できます。

   修正案：既存 probe に prefix 保持下の上限到達を別計数し、その正値を要求する。別走を証拠に使う場合は、結果にもその限界を明記する。

3. **should — 実測件数と原因説明の記録を訂正する必要がある。**

   根拠：`J/s6-ruling-5.md:4` の30 case は結果 JSON と不一致。同`:8` の maxwait 未到達は、probe 無効の対象2走からは直接確認できません。

   **影響：** 実行件数が誤記され、未検出の原因仮説が実測済み事実として残ります。

   修正案：下節の件数へ訂正し、maxwait の原因説明を推定として記す。

fix 差分に、判定式の恒真化、既存 gate 判定の緩和、不要な除外登録は見つかりませんでした。既存 test の変更は本 wave の pin・companion 期待と、新しい到達条件に伴う fixture の追随です。必須集合一致、bool 型確認、判定の再導出、norw の exit 1、hook の赤集合は維持されています。

## 記録の派生値・量化の照合

| 記録・主張 | 照合結果 |
|---|---|
| coverage-3「全30 case」 | **不一致。32 case**。負例6＋焦点3＋対照9＋変異9＋flag4＋TRACE=0の1。共有対照5件を含むため「32回の独立実走」でもない。 |
| 「55 check 中54真、偽は上限 prefix の1件」 | 一致。`coverage-3.json:224870` が唯一の偽。`all_pass=false`。 |
| coverage の実行量 | case 用23 build＋準備1＝24 build。独立 trace 起動22回。coverage-3 は timeout 2回なので verifier 呼出し20回。 |
| fix-4「通常19 verifier」 | **期待 timeout 3回を仮定した見積りとして正しい**。coverage-3 の実績値ではない。 |
| 裁定1の build「26→約21」、prefix「1走増」 | 共有化で−5だが、新しい出口には変異と対照の計2 build が必要。fix 後は23、依存物準備追加後は24。 |
| norw cycles 40,756／15,786、exit 1 | JSON・要約と一致。 |
| lockskip X 2種、early-unlock は保持欠落のみ | JSON・要約と一致。 |
| focus の一致56,777～62,431、不一致0 | 3 hook 照合について一致。成功後比較は別値で、一致 **56,775**・不一致0（`coverage-3.json:63547`）。 |
| hook 変異の赤集合 | abort解除 `{abort,lock,commit}`、lock解除 `{abort,lock}`、commit解除 `{commit}`、要因誤記録 `{reason}` と一致。 |
| retry 上限125,445、再取得19,856、no-reload再取得0 | 一致。 |
| maxwait「上限に到達していなかった」 | **直接の実測根拠なし**。対象変異・対照とも probe 無効。certified と commit/abort 数は確認できるが、未到達の原因断定はできない。 |
| 50µs×32＝1.6ms | 算術は正しい。ただし CAS 失敗周回は待機しないため、上限到達時に必ず1.6ms待つという意味にはならない。 |
| f2の赤8件がf3で全件消失 | 失敗 node の集合は入れ替わっており一致。f3には別の赤8件が残る。 |
| f4／f5／f6／f7 | ログの4785／100／107／27 passed と一致。skip はそれぞれ8／2／2／0。 |
| smoke | 5 case・30 checkすべて真・`all_pass=true` を確認。準備込み11 build、verify10回、bench5回と整合。 |
| 裁定1の使用済み292秒 | 27＋27＋10＋228＝292秒、約0.08時間は算術上整合。ただし最終の累積残予算ではない。 |

fix-4 の照合表は、target／成果物、依存物準備、workload、CLI、probe の取得順、verifier の入出力、前処理、TRACE=0、smoke identity について実装と整合しています。timeout の理由名と部分出力保存も整合します。ただし、**timeout と特定の unlock 出口との因果対応までは、その表では証明されていません**。

maxwait→retry は、変異の期待を certified へ変更せず、timeout を維持し、到達条件を追加しています。したがって**結果を見て期待を緩めた変更ではなく、未検出を受けた実験構成の訂正として妥当**です。ただし事後変更であることを残し、新しい実測で確認する必要があります。現条件は「focus/retry 自体も上限未到達」という空振りを拒否しますが、新所見2の射程までは保証しません。

## 総括

**NO-GO。must-fix は1件。**

- `abort0` でも CAS 失敗経由で上限出口へ到達できるため、両出口を同時に壊す変異では action-abort 出口の独立検証を保証できない。
- 出口別変異などで独立性を成立させ、対応する実測を確認する必要がある。
- J1 の期待緩和は認めない。方策変更は妥当だが、到達証拠の限界を残す。
- coverage-3 は32 case・55 check中54真。30 caseという記録を訂正する。
- coverage-4 は未取得。最終 HEAD の動的合格は認定していない。