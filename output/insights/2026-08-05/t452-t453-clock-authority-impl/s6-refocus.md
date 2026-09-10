| ID | 判定 | 静的根拠 |
|---|---|---|
| L6-B-1 | **closed** | self gate は expected を exact `{samples_mhz,tolerance_pct}`、observed を `{samples_mhz}` に射影する（[cli.py:380–397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py:380)）。public predicate の exact-key/policy gate は未変更（[execution_guard.py:183–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py:183)）。production caller 全件を再検索し、receipt consumer と Silo live/raw も明示射影済み（[execution_guard.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py:176)、[silo_ladder_rung1.py:1967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:1967)、[同:3414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:3414)）。full map 直結は残っていない。 |
| A2-R1 | **closed** | policy/artifact が共に 3% の publish・issuer・self・receipt 正例（[test_calibrator_certify.py:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:666)）と、共に 2% の同一 +3% vector 負例（[同:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:739)）が分離された。publish は理由を clock self failure 一件に固定し、issuer/public/receipt も policy 不一致でなく帯域計算まで到達する。各層の literal `5.0` 幅変異は負例を pass にして assertion を殺す。 |
| A2-R2 | **closed** | synthetic profile SHA を再計算（[test_silo_ladder_rung1_driver.py:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:825)）。2% は production の `InfraFailure("attestation")`、3% は `effective_clock_match/all_pass=True` まで到達し、exact-key spy も一回発火する（[同:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:863)）。 |
| A4-R1 | **closed** | live duplicate は duplicate を除けば all-pass の完全 v2 profile（[test_silo_ladder_rung1_driver.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:746)）。raw は元 bundle が failure 0 の fixtureを再封印して duplicate だけを加える（[同:1767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:1767)、[同:1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:1855)）。shell も完全 v2・13引数で、duplicate を外せば candidate が生成される正例形（[test_pegasus_tools.py:632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_tools.py:632)、[同:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_tools.py:710)）。 |
| A7-R1 | **closed** | success 19／failure 3 の path を独立 golden 化（[test_env_attestation.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:386)）。探索集合、docs 実在、全 pair の意味的一致、path ごとの `parsed.ok` を固定する（[同:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:415)）。 |
| RI-B1 | **closed** | clean `[100.0]`・policy 2.0 の正例を先に要求し、同じ標本で `nextafter(±inf)/2.5/2.9` だけを変える（[test_env_contract.py:490–515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:490)）。帯域判定による mask はない。 |

pytest は未実行。上表は fix 後 snapshot の静的判定であり、緑の申告ではない。

## 所見

### NREG-CPU-1

- **ID:** NREG-CPU-1
- **主張:** observed parser の key-set exactnessと duplicate 拒否は維持されているが、CPU の `model_name_raw` と `model_name_normalized` の導出整合性を意図的に外しており、指示外に parser の受理集合が広がった。
- **file:line:** validation copy だけ normalized 値を raw から再生成し（[env_attestation.py:537–557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:537)）、返却値には未照合の元ペアを使う（[同:559–565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:559)）。Silo live/raw は normalized 値だけを authority とする（[silo_ladder_rung1.py:1980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:1980)、[同:3421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:3421)）。
- **失敗シナリオ:** 完全 valid な v2 profile の raw 名だけを `Intel Xeon Platinum 8468H`、normalized 名を期待値 `Intel Xeon Platinum 8468` のままにする。parser は通り、他の profile 値と clock を帯内に置けば Silo は `cpu_model_match=True`、最終的に `all_pass=True` を記録する。raw replay も同じ normalized-only 再導出で通る。
- **成果物影響:** 近接 SKU の観測を期待 CPU として Silo 材料レポート／raw 試行台帳が `all_pass` 扱いし、環境同一性の値を誤る。
- **強度:** **must-fix**
- **最小の是正案:** raw parser では `model_name_normalized == normalize_cpu_model_name(model_name_raw)` を再び必須化する。比較器の raw/normalized 独立 mismatch test は parser を経由せず `ObservedAttestationProfile` fixture を直接構築し、期待 verdict は維持する。v1/v2 の forged pair 負例も追加する。

### IMP-R1

- **ID:** IMP-R1
- **主張:** `campaign.*` 統一自体と遅延 `orchestrator.verifier` import、path-based runtime binding に破損は見つからない。ただし追加された orchestrator root が import 後も `sys.path` に残る。
- **file:line:** driver が repo root と orchestrator root を恒久挿入する（[silo_ladder_rung1.py:34–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:34)）一方、fetcher は一時追加した repo root しか除去しない（[fetch_third_party.py:51–68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/fetch_third_party.py:51)）。既存契約は import 前後の完全一致を要求する（[test_pegasus_thirdparty_fetch.py:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_thirdparty_fetch.py:836)）。
- **失敗シナリオ:** fresh process で `_driver_module()` を呼ぶと、finally 後も `<repo>/orchestrator` が残る。module cache や全走の収集順によって既存 test がこの状態を隠す可能性もある。
- **成果物影響:** 現行 standalone fetch 経路でレポート／台帳値を誤る後続 import は確認できず、直接の成果物影響は未立証。
- **強度:** **backlog**
- **最小の是正案:** fetcher が repo root と orchestrator root の双方を一時挿入・正確に復元し、fresh subprocess で既存契約を検査する。

## 裁定・凍結境界

- R-1 は維持。loader は schema/env/clocks/policy 一致までで self-pass を要求しない（[env_attestation.py:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:852)）。
- R-2 は維持。`t126_driver.py` は wave baseline から無変更で、誤型呼出しが残る（[t126_driver.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:439)）。
- R-3 後半も維持。T126 envelope は `t126-qualification-attestation/v1` のまま（[t126_driver.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/qualification/t126_driver.py:451)）。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は exact 1 件（[test_env_contract.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:60)）。registry path/SHA と `contract_sha256` golden も不変（[env_contract.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_contract.py:185)、[test_env_contract.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:730)）。
- fix commit `0f68838` はコード／テスト 8 ファイルだけで、`output/`、`env_contract.py`、`t126_driver.py`、`test_frozen_artifacts.py` の diff は空。wave baseline から現 HEAD まで対象の calibration/Silo/freeze bytes にも差分なし。
- skip/xfail、恒真・恒偽 assert は追加されていない。削除された件数 assert と `is want` は、それぞれ exact path 集合と成功／例外の分岐 assertion に強化されている。

## 総括

- (a) **NO-GO**。pytest は未実行であり、静的判定である。
- (b-1) observed CPU の raw/normalized 整合 gate が外れ、Silo 材料・raw 台帳が近接 SKU を `all_pass` にできる。
- 旧所見 L6-B-1 / A2-R1 / A2-R2 / A4-R1 / A7-R1 / RI-B1 自体はすべて closed。
- import 後の `sys.path` 汚染は real だが、現行成果物影響未立証のため backlog。
- (c) 修正後は forged CPU pair の v1/v2・Silo live/raw 負例を最初に確認すること。
- 続いて元の metamorphic node、duplicate consumer 群、`test_driver_import_removes_only_its_temporary_sys_path_entry` を単独確認してから全走すること。
- [T-476] の既知 flake は本判定理由に含めていない。