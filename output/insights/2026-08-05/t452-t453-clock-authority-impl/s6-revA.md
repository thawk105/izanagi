| 是正 | 判定 | 静的検査結果 |
|---|---|---|
| A-2 | **partial** | Silo raw は `2% fail / 3% pass` を実経路で検査する。一方 self/issuer/receipt consumer の負例は policy を `3.0` にしたまま tolerance `2.0` を渡しており、帯幅ではなく policy 不一致で落ちる。literal `5.0` 幅が生存する。Silo live test 自体も到達不能。 |
| A-3 | **closed** | `nextafter(2.0, ±inf) / 2.5 / 2.9` が loader・issuer・consumer・self の全層にある。 |
| A-4 | **partial** | v1/v2 × top/profile/effective_clock の schema-valid duplicate 負例はある。production 3 consumer も共通 parser を使うが、live/raw の配線テストは空 profile で過剰決定され、certification shell の fixture は v2 移行に追随していない。 |
| A-7 | **partial** | payload の探索集合＝golden、22 組の意味的一致、success 全件の二述語検査はある。ただし success path 自体は固定せず件数だけで、docs 集合には存在確認なしの手書き path が混じる。 |

## 層別変異照合

| 層 | production | 変異検出 |
|---|---|---|
| policy 定数 | [effective_clock_policy.py:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/effective_clock_policy.py:6) | `2.0→他値` は literal/AST test が検出。 |
| producer 注入 | [cli.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py:546) | 削除・hard-code `2.0` は policy `3.0` producer test が検出。 |
| expected schema | [schema_v2.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/schema_v2.py:235) | `100.0`、nextafter、`1e300` 負例と直下正例で検出。 |
| loader | [env_attestation.py:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:844) | equality 削除・丸め・`isclose` は schema-valid 負例が検出。 |
| issuer | [env_attestation.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:721) | **literal `5.0` 幅が生存**。既存 test は逆に +2.5% を pass と期待する。 |
| canonical consumer | [execution_guard.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py:159) | public predicate の幅変異は Silo raw が検出するが、receipt consumer 内だけを `5.0` 化する変異は生存。 |
| 取得時 self gate | [cli.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py:380)、[cli.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py:605) | **literal `5.0` が生存**。現 integration 負例は約46%外れ値。 |
| registry 不変条件 | [test_env_contract.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:439) | `passes=True` と空 loop は検出するが、constant-false/equality bypass は生存。backlog。 |
| receipt exact key | [execution_guard.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py:294) | observed injection、expected missing/extra が各検査の削除を検出。 |
| Silo live/raw | [silo_ladder_rung1.py:1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:1972)、[silo_ladder_rung1.py:3425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:3425) | raw は検出。live test は fixture 構築時と 2% reject 時の二箇所で赤になる。 |

## 所見

### A2-R1 — self/issuer/receipt consumer の差分 vector が帯幅を検査していない

- **ID:** A2-R1
- **主張:** [test_calibrator_certify.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:664) で authority を `3.0` にした後、[同:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:714) の tolerance `2.0` 負例でも authority を戻していない。したがって拒否理由は「2%帯外」ではなく「current policy 3.0 と不一致」である。
- **file:line:** self 呼出しは [test_calibrator_certify.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:708)、issuer は [env_attestation.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:737)、receipt consumer は [execution_guard.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py:175)。
- **失敗シナリオ:** exact policy equality は残し、self/issuer/receipt consumer の帯幅だけ literal `5.0` にする。authority `3.0` の +3% は期待どおり pass、tolerance `2.0` は policy 不一致で fail、約46%外れ値も fail するため現行テストを通る。
- **成果物影響:** policy `2.0` なのに +3% 外れ値を持つ calibration candidate が publish され、または forged pass receipt が consumer に受理され、certified 根拠と試行台帳の受理集合が広がる。
- **強度:** **must-fix**
- **最小の是正案:** 同じ +3% vector を、authority と expected tolerance を共に `2.0` にした負例、共に `3.0` にした正例として別々に実行する。self は `_invoke()` の publish/reject まで、issuer は `compare_profiles()`、consumer は `receipt_matches_contract()` まで通す。

さらに、[test_env_attestation.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:172) は expected を `2.0` に縮小したのに、[同:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:264) は median `2400` に対する `[2450,2460,2440]`（上限 `2448`）を pass と期待する。正しい現実装では静的に fail となる一方、literal `5.0` mutant なら緑になる。

### A2-R2 — Silo live metamorphic test は production verdict へ到達しない

- **ID:** A2-R2
- **主張:** synthetic `VerifiedCalibration` が stale profile SHA を保持し、さらに 2% case は production が `False` を返さず `InfraFailure` を送出する。
- **file:line:** stale SHA の構築は [test_silo_ladder_rung1_driver.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:789)。SHA 自己整合検査は [env_attestation.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:98)。test の無条件 return 期待は [test_silo_ladder_rung1_driver.py:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:836)、production reject は [silo_ladder_rung1.py:2004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:2004)。
- **失敗シナリオ:** `dataclasses.replace(verified, calibration=...)` の `__post_init__` が最初に `AttestationError`。これを直しても authority `2.0` では `_attest_environment()` が `InfraFailure` を投げ、`result["effective_clock_match"]` へ到達しない。
- **成果物影響:** Silo live の `effective_clock_match/all_pass` が literal `5.0` や median-only に退行しても、検出力を示す受入 test が成立しない。
- **強度:** **must-fix**
- **最小の是正案:** synthetic profile SHA を再計算し、2% case は `InfraFailure(reason_code="attestation")`、3% case は `all_pass=True` を期待する二分岐にする。spy の exact key assertion は維持する。

### A4-R1 — raw consumer の duplicate-parser 配線変異が生存する

- **ID:** A4-R1
- **主張:** 共通 parser 自体の schema-valid duplicate test は有効だが、live/raw consumer test の duplicate payload は `profile={}` である。last-wins parser に戻しても profile schema で同じ failure class へ落ちる。
- **file:line:** 有効な三階層負例は [test_env_attestation.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:316)。過剰決定された live/raw fixture は [test_silo_ladder_rung1_driver.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:746)、[同:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:1803)。3 consumer は [certify_calibration.sh:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/certify_calibration.sh:571)、[silo_ladder_rung1.py:1956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:1956)、[同:3405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:3405)。
- **失敗シナリオ:** consumer 1 箇所だけを plain `json.loads` へ戻す。重複消失後も空 profile が拒否されるため live/raw test は同じ理由で通る。certification shell には schema-valid duplicate attack test がない。
- **成果物影響:** last-wins で選ばれた観測 profile が calibration acquisition receipt または Silo `all_pass` に束縛され、試行台帳の観測参照が非一意になる。
- **強度:** **must-fix**
- **最小の是正案:** duplicate を除けば全 gate を通る完全 v2 profile を各 consumer に投入する。raw は manifest を再封印し、live は all-pass profile、shell は acquisition embedded Python を直接実行して parser 固有の拒否を確認する。

Shell の既存 executable fixture も古いままである。[certify_calibration.sh:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/certify_calibration.sh:560) は 13 引数と完全 v2 profile を要求するが、[test_pegasus_tools.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_tools.py:649) は旧 `{ok,profile.cpu/cores}`、[同:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_tools.py:668) は `repo_root` を欠く12引数であり、静的に赤である。

### A7-R1 — success identity と docs 探索が exact でない

- **ID:** A7-R1
- **主張:** payload path 集合は探索結果と golden を比較するが、success/failure は path ごとの golden ではなく総数だけである。また Silo README は存在確認なしで `discovered_docs` へ挿入される。
- **file:line:** path 探索は [test_env_attestation.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:388)、手動 docs 挿入は [同:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:397)、status は [同:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:415) の counters のみ。
- **失敗シナリオ:** 元 success 1件を failure、元 failure 1件を帯条件を満たす success に替えると `(19,3)` のまま通る。`silo_ladder_rung1/README.md` を削除しても、手動 `Path` は集合に残り 47 件 assertion が通る。
- **成果物影響:** legacy replay の success/failure と材料文書の exact reference 集合が履歴試行台帳からずれても、corpus 完全性が緑になる。
- **強度:** **must-fix**
- **最小の是正案:** success 19 path と failure 3 path を独立 golden にし、各 `parsed.ok` を path ごとに照合する。docs は実在ファイル探索または少なくとも `is_file()` を通した集合と golden を比較する。

### RI-B1 — registry equality 負例は自己不整合 outlier に食われる

- **ID:** RI-B1
- **主張:** [test_env_contract.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:490) は全 tolerance で現登録較正の約46% outlierを保持する。policy equality を外しても帯域判定で false のままである。[同:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:464) の production 定数比較も loader の直後なので実質その postcondition である。
- **失敗シナリオ:** `_registry_clock_self_passes()` を private arbitrary-width math へ変更する、または constant-false にする。既知 entry、synthetic outlier、全 equality edge がすべて false のまま通る。
- **成果物影響:** 単独ではなし。loader と canonical consumer が別 test で同じ非 policy artifact を拒否するため、現在の certified 受理集合は変わらない。
- **強度:** **backlog**
- **最小の是正案:** samples `[100.0]` の policy `2.0` 正例と、同じ clean samples の4 equality負例を helper に与える。

## 裁定・凍結・弱体化監査

- **R-1 は遵守:** loader は [env_attestation.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:830) で schema/cross-field/policy だけを検査し、self-pass は追加していない。`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は [test_env_contract.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:60) の exact 1 件。裁定済みの clean-live pass 穴は残るが NO-GO 理由にはしていない。
- **R-2 は遵守:** `t126_driver.py` は実装 commit で無変更。[t126_driver.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:443) は引き続き `CalibrationV2` を expected に渡す。`output/` の `t126-qualification-attestation` は静的検索 0 件で、受理集合は空。
- **凍結境界は遵守:** wave commit は `output/`、`env_contract.py`、`test_frozen_artifacts.py` を変更していない。登録較正 SHA は `753f…e5a49`、floor protocol SHA は `261c…74aac` のまま。[contract SHA golden:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:722) も `e576…2c01` のまま。
- **弱体化:** skip/xfail の追加はない。CLI 任意 tolerance test の置換、required fixture の `2.0` 化、歴史 Silo binding の current 不一致化は裁定済み U-2/U-3/U-5/P1 の範囲。旧任意幅数学は [test_execution_guard.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_execution_guard.py:424) の18 vectorsで独立に残る。
- 新しい歴史 SHA は current driver への追随ではなく、[test_silo_ladder_rung1_evidence.py:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1234) で current SHA と不一致を要求しており、fixture hash 差し込みによる緑化ではない。
- 新設 test に空 loop で成功するもの、揮発する epoch/hash を期待値へ焼き込むものは見つからなかった。

## 総括

- **(a) NO-GO。**
- **(b-1)** A-2 の self/issuer/receipt consumer は真の `2% fail / 3% pass` になっておらず、literal `5.0` 幅が生存する。
- **(b-2)** Silo live test と certification embedded-Python test は静的に赤で、A-4 の consumer 配線負例も過剰決定されている。
- **(b-3)** A-7 は success path identity と docs 実在を固定せず、履歴 corpus の入替え・欠落を許す。
- **(c)** 親全走では最初に `test_compare_profiles_normalizes_raw_name_and_applies_expected_clock_tolerance`、`test_silo_live_clock_wiring_moves_with_policy_and_uses_exact_keys`、`test_known_values_cpu_check_rejects_nearby_sku` を確認すべきである。
- pytest は実行しておらず、緑は申告しない。以上は commit 済み snapshot の静的検査結果である。