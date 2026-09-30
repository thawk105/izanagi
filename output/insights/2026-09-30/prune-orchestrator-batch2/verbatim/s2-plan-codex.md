## 候補別判定

依頼に列挙された削除単位は **9 群**です。`submission_gate/` の 11 Python file と、単体の 8 module を合わせると **19 file** になります。「12 module」という件数とは一致しないため、以下は列挙された全候補を対象にしました。

| 候補 | 判定 | 拘束（D1989 の分類と根拠） | D2179 で崩れた項 | 消えたら失われる検査性質 |
|---|---|---|---|---|
| `submission_gate/` と T-338・T-139 test／fixtures | 残す | **現役の拘束的 consumer**。D574 の受理述語は [decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/decisions.md:23167)、実装完了と pilot 禁止の継続は同ファイル `:29216`。承認 manifest が fixture index を要求する [t139-approval-manifest-v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/orchestrator/preregistration/t139-approval-manifest-v1.json:20)。 | 現行機構の実装でない、が不成立。test も単純な専用対ではない。 | Git 履歴・束縛 `test_t338_submission_gate_unit1.py:218,531`、安全な IO と schema `unit2.py:249,426`、受領証の意味検証 `unit3.py:746,1024`、全履歴の一意性 `unit4.py:363`、vector index と公開 call site `unit5.py:356,490`、固定 authority `test_t139_submission_path.py:100,210` の検査が失われる。 |
| `backoff_counterfactual_analysis.py` | 残す | **現役の拘束的 consumer**。凍結事前登録が解析器の独立 pin と cohort 専用の受理集合を要求する [backoff-counterfactual-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/backoff-counterfactual-preregistration.md:345)。 | 現行機構の実装でない、が不成立。 | v2 事前登録 SHA と解析入力の束縛 `test_backoff_counterfactual_analysis.py:584,618`、推定と等価性境界 `:270,546` の検査が失われる。 |
| `backoff_counterfactual_cohort2_analysis.py` | 残す | **現役の拘束的 consumer**。live probe test が module の seed 定数を照合先にする [test_t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/orchestrator/tests/test_t2187_adaptive_const_probe.py:1974)。 | 現行機構の実装でない、が不成立。 | probe の認証 seed 表の照合に加え、LCG・terminal 処理・事前登録 SHA `test_backoff_counterfactual_cohort2_analysis.py:259,340,643` の検査が失われる。 |
| `backoff_nonmonotonicity_analysis.py` | 残す | **現役の拘束的 consumer**。後続 probe が同じ解析器を再利用した記録と現行 SHA は [T-2583 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/output/insights/2026-09-15/t2583-backoff-high-band-sign/README.md:380)、[T-2635 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/output/insights/2026-09-16/t2635-high-band-control-feasibility/README.md:202)。 | 一回限り、が不成立。 | 保存値からの方向性再計算、J0〜J4 の判定 `test_backoff_nonmonotonicity_analysis.py:392,495,538,628,663,685` の検査が失われる。 |
| `backoff_policy_performance_analysis.py` | 残す | **現役の拘束的 consumer**。事前登録が公開解析関数を指定する [backoff-policy-performance-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/backoff-policy-performance-preregistration.md:330)。 | 現行機構の実装でない、が不成立。 | 登録済み仮説の三値判定、入力 identity、事前登録 bytes の pin `test_backoff_policy_performance_analysis.py:519,901,996` の検査が失われる。 |
| `backoff_sweep_report.py` | 残す | **現役の拘束的 consumer**。D12 材料レポートの規約 [orchestrator-design.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/orchestrator-design.md:117) に対応し、共有 test が certified view を読む経路を検査する `test_backoff_consumers.py:108`。 | 現行機構の実装でない、が不成立。共有 test は専用対として丸ごと削除できない。 | certified view の読み分け、noise 境界、IPC 欠測表示 `test_backoff_consumers.py:108,186,231,330` の検査が失われる。 |
| `s8b_floor_evacuation.py` | 残す | **現役の拘束的 consumer**。現行手順が `python3 -m` を指定する [phase3-8b-restart-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/phase3-8b-restart-runbook.md:279)。別 test も import する `test_s8b_holdout_freeze.py:3324`。 | 一回限り・現行機構でない、が確認できない。 | 退避失敗時の byte 保持、namespace 全体の復元、clean scan との関係 `test_s8b_floor_evacuation.py:121,253,380` の検査が失われる。 |
| `s8b_oracle_exploration.py` | 残す | **現役の拘束的 consumer**。探索 schema の現用名として [decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/decisions.md:21801) が記す。共有 test が CLI を実行する `test_s8b_oracle_artifacts.py:341`。 | 現行機構でない、が確認できず、test の専用性も不成立。 | 探索出力を official 出力から分離する CLI 検査 `test_s8b_oracle_artifacts.py:61,341` が失われる。同じ test の現行 official loader 検査 `:120,208,225` も丸ごと削除では失われる。 |
| `s8b_verdict.py` | 残す | **現役の拘束的 consumer**。現行判定の変更を D555 が指定する [decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-orchestrator-batch2/docs/decisions.md:22607)。閉包 test の固定表にも入る `test_official_perf_closure.py:187,439`。 | 現行機構の実装でない、が不成立。 | 条件 1・2、oracle の診断限定、freeze identity、測定 claim gate `test_s8b_verdict.py:149,193,238,1488,1744` の検査が失われる。 |

## 親 brief への反証

| 裁定 | 検査結果 |
|---|---|
| P1 | **支持。ただし根拠を限定。** manifest `t139-approval-manifest-v1.json:20` が直接 pin するのは *fixture index* であり、11 個の実装 file 自体ではない。実装の保持根拠は D574 `decisions.md:23167`、D749 `:29216` と live test。D2257 `:72627` の持ち越し取り下げは D を取消さない。 |
| P2 | **支持。** counterfactual の事前登録契約 `backoff-counterfactual-preregistration.md:345`、cohort2 の live seed 照合 `test_t2187_adaptive_const_probe.py:1974`、非単調性解析器の後続再利用 `t2583…/README.md:380`、sweep の共有 test `test_backoff_consumers.py:108` を確認した。09-20 の README だけに依存する判定ではない。 |
| P3 | **支持。** 事前登録 `backoff-policy-performance-preregistration.md:330` と解析契約の test `test_backoff_policy_performance_analysis.py:353,996` が残る。 |
| P4 | **支持。** runbook `phase3-8b-restart-runbook.md:279` の実行手順に加え、非専用 test `test_s8b_holdout_freeze.py:3324` がある。 |
| P5 | **支持。ただし D の名前記載だけでは足りない。** `decisions.md:21801` に加え、CLI を実行する `test_s8b_oracle_artifacts.py:341` を確認した。同 test は official loader も検査する `:120,208`。 |
| P6 | **支持。** 凍結設計文書の列挙だけでなく、D555 `decisions.md:22607`、閉包の固定表 `test_official_perf_closure.py:187`、判定の実 test `test_s8b_verdict.py:1744` がある。 |

候補 file の**現行 SHA-256 と git blob ID の両方**を計算し、tracked 全体を値で検索した。値による hit は counterfactual の過去の SHA 言及、非単調性解析器の再利用記録、verdict の到達性台帳に限られた。これらを新たな live pin と誤認せず、上表の現行契約と区別した。

## 削除計画

なし。

## 総括

- 静的検査では、列挙されたどの削除単位も D1989・D2179 の必要条件をすべて満たさない。
- 親の「削除 0」は支持するが、manifest の fixture pin や歴史的 SHA 言及だけを実装 file の直接 pin とは数えなかった。
- test の関数単位確認により、共有 test を対ごと消すと現行 code の検査も失う候補を確認した。
- test の実走は指定どおり行っていない。