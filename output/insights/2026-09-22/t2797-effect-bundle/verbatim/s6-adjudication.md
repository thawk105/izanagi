# [T-2797] 段 6 裁定 — 敵対レビュー 2 本 (A: 正しさ・整合、B: 過剰・削除) の採否

入力: `codex/s6-review-A.md` (NO-GO、must-fix 2 / should 2 / nit 1)、`codex/s6-review-B.md` (NO-GO、must-fix 4 / should 2 / nit 1)。対象 = wave 木 `d327dd30c` (実装) + `00364a1fe` (insight)。

| # | 出所 | 所見 | 判定 | 処置 | 担い手 |
|---|---|---|---|---|---|
| R1 | B-1 | `record-models` の `matches_expected` に client の版の形式検査が混じる (version が null の行 1 つで系列停止へつながる) | real (`tools/b5_llm_round.py` の `record_models`、`reasons` に version 異常を積む) | 版の異常は別欄に記録し、一致判定は「assistant 行 ≥ 1 ∧ model 集合 = {予定 ID} ∧ agentType = role ∧ transcript / meta が読める」に限る | Codex fix B2 |
| R2 | A-1 / B-2 | 最後の評価の後の critic で不一致を検出しても、driver は次の handshake を待たずに score へ進むので「系列が欠測になる」とは限らない | real (driver は B = 10 / A = 30 到達で探索を抜ける) | critic は「次の原提案の request が公開され、その next_evaluation が直前より増えたときだけ、生成入力へ還流する分として走らせる」に改める (試走も 10 評価に対し critic は 9 本)。走らせた critic はすべて次の planner / coder へ入るので、その不一致は proposal 非公開 → 欠測で閉じる。最後の評価の後は critic を走らせない。driver に待機 gate は足さない | 親 (template・README・JSON・D-4 の文言) |
| R3 | A-2 | 親 template に A だけを消費する拒否 (planner / coder の出力不合格、proposal の検査落ち、子側の前処理・Tier0 不通過) から次の原提案へ進む手順がない | real | template に分岐を書く: 親側の不合格は候補を直さず `reject` (A 消費)、子側の拒否は slot が出ず同じ評価番号の次の request が来る。どちらも critic は走らせず次の a へ進む | 親 |
| R4 | B-3 | 「列挙 hash が同じなら後の main も可」は承認対象を広げる (親指示・settings は hash 列挙の外) | real | 承認対象を「本 wave の land commit と、承認に基づく発効 commit の固定 checkout」に限定する。束の data file (親指示・settings・schedule 等、draft JSON 自身を除く) の sha256 も列挙する | 親 |
| R5 | B-4 | launcher 用に新設した process 起動目録 test (`test_ccbench_spawn_sites.py` の +24 行) は新しい検査面の追加 | real (既存目録の走査対象外だった launcher に新しい構文閉集合検査を足した) | 新設 test を戻す (同 file を base と同じ内容にする)。registered の env / argv・dry-run の無副作用・投入失敗の機能 test は残す | Codex fix A1 |
| R6 | B-7 | schedule の順序均衡検査を 2 node で重複して実行 | real (nit) | `test_registered_schedule_llm_four_per_stage` は LLM 数だけ、`test_registered_schedule_six_orders_twice` は 6 順序 × 2 と先後均衡を 1 回ずつに整理する。変異 MA6 (回転を外す) は LLM 数では検出できないので、kill 先を `six_orders_twice` へ再照準する (erratum) | Codex fix A1 |
| R7 | B-5 | 費用の「親待ち最大」「k を上げても実消費は増えない」は模型より強い | real | 「780 s / 機会を仮定した A = 30 の試算」「同じ処理が旧 walltime 内に完走する場合、予約を増やしても実 Elapse は増えない」に直す | 親 |
| R8 | B-6 | draft JSON の N1 要約が初回 attempt と retry を区別しない | real | README と同じ限定 (初回 attempt で B が 1 少なく記録、retry は保持) を写す | 親 |
| R9 | A-3 | toolchain の「固定」と「試走観測・本走時記録」が区別されていない | real | 本走で要求する版 = 試走の観測値 (gcc / g++ 11.4.0-1ubuntu1~22.04.3、cmake 3.22.1、python3.10 sha256 d6bca2b8…) と定め、job の prebuild receipt の値が異なる job は発効束への不適合として、その系列 (または block-stock) を欠測扱いにし救済しない (事前登録、機械 gate ではなく結果集計時の手順) | 親 |
| R10 | A-4 | prompt 変更の一覧が D-3 (5) の CV だけでなく、critic の他の欠測表示 (fitness・anomalies・median・反復数・rounds・settled・abort・IPC) にも及ぶことを書いていない | real (実装子 B は報告済み) | 変更一覧に明記する。方向は欠測を正しく示すもので撤回しない | 親 |
| R11 | A-5 | 費用表の中間値の丸め (検査秒の切り上げ) が書かれていない | real (nit) | 丸め規則 (検査秒を整数秒へ切り上げ) を表に書く | 親 |

**攻撃が成立しなかった主な項目 (2 本の合意):** registered header の report 受理と pilot 不変、purpose の受け渡し、schedule (D-2)、walltime の Decimal 切り上げ、job ごとの tree と全件事前検査、
LLM tool の a / k 分離・継承・公開順・知識解決、規律 2・6、`ANTHROPIC_DEFAULT_OPUS_MODEL` が課金経路の切替でないこと、Tier0・lock・親運用・walltime 式の作り直しが無いこと、
束の hash 31 件・事前登録・schedule・random / sweep・rep 1・N1 の数値の一致。

**裁定パッケージ候補にしない:** 最終 critic を待つ driver の待機、model 記録を読む report、台帳の不一致 field (相談 A が分離を勧めた案) は、R2 の手順で必要がなくなる。

## 変異の再登録 (DW-M01、fix 前)

- MA6 (除く組の回転 `+ b − 1` を外す) の kill 先を `test_b5_contrast_launch.py::test_registered_schedule_six_orders_twice` へ再照準する (回転を外しても各 stage の LLM は 4 本のまま、実測は親の算術)。
- 新規 MB9: `record_models` で client の版の異常を一致判定の理由に入れる → `test_b5_llm_round.py::test_model_record_version_is_recorded_only` で落ちるべき。
