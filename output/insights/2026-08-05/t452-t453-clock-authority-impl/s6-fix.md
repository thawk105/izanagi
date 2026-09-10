| 所見／赤グループ | 状態 | 対応 |
|---|---|---|
| L6-B-1 | partial | exact 射影を実装済み。pytest 未実走 |
| A2-R1 | partial | self／issuer／receipt／publish の真の 2% fail・3% pass を実装済み |
| A2-R2 | partial | SHA 自己整合と production の例外／成功 verdict を修正済み |
| A4-R1 | partial | live／raw／shell を単一理由の完全 v2 duplicate fixture 化 |
| A7-R1 | partial | success 19・failure 3 の exact path と docs 実在を固定 |
| RI-B1 | partial | clean `[100.0]` 正例と同一標本の equality 4 負例へ変更 |
| calibrator 赤 10 件 | partial | L6-B-1 と test 内 full-map 誤用を修正済み |
| env attestation 赤 3 件 | partial | observed-side CPU 不一致を比較まで運ぶよう修正、2%内 fixture 化 |
| Pegasus tools 赤 2 件 | partial | shell fixture を完全 v2・13引数へ移行 |
| silo driver 赤 5 件 | partial | module identity 二重化と live metamorphic fixture を修正済み |

すべての `partial` は「実装済みだが scheduler 障害で pytest 未実走」という意味です。静的監査で残る既知の実装欠落や `regressed` はありません。

主な修正は次のとおりです。

- [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py:380) で self-gate の expected を `{samples_mhz,tolerance_pct}`、observed を `{samples_mhz}` に明示射影しました。public predicate は緩めていません。
- production caller を全走査し、receipt consumer と silo live/raw は既に exact 射影済みで、full map 直結はこの self-gate だけだったと確認しました。
- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:519) は observed の raw/normalized CPU 名を独立値として保持し、不一致を parser で落とさず `compare_profiles()` の verdict へ運ぶようにしました。
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py:34) は兄弟 module を canonical な `campaign.*` 名で統一しました。repo root も保持し、遅延 `orchestrator.verifier` import は壊していません。
- [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_calibrator_certify.py:663) で +3.0% vector を使い、policy と artifact tolerance が双方 3% の pass、双方 2% の self／issuer／receipt／publish reject を分離しました。loader equality の旧負例も独立に残しています。
- [test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:746) と [test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_tools.py:710) は、duplicate を除けば全 gate を通る完全 v2 profile を使用します。
- [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:386) と [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_contract.py:490) で A7-R1／RI-B1 を閉じる検出力を追加しました。

テスト・検査結果:

- 対象 nodeid（ファイル単位）:
  `test_calibrator_certify.py`、`test_env_attestation.py`、`test_env_contract.py`、`test_pegasus_tools.py`、`test_silo_ladder_rung1_driver.py`
  - `tools/run_tests.py ... -rf`: **rc=16**
  - `qstat -Q preflight`: `Unknown user-id (uid: 31609)`
  - pytest は起動されず、実行 node は 0 件です。
- 同 5 ファイル `--collect-only`: **rc=0、357 tests collected**
- 所有外 8 ファイルの `--collect-only`: **rc=0**
  - `test_execution_guard.py`
  - `test_campaign.py`
  - `test_s8b_floor_campaign.py`
  - `test_s8b_oracle_driver.py`
  - `test_s8b_oracle_report.py`
  - `test_s8b_ratified_verify.py`
  - `test_silo_ladder_rung1_evidence.py`
  - `test_t126_qualification_driver.py`
- 変更 Python の `py_compile`: **rc=0**
- `git diff --check`: **rc=0**
- `tools/check_codex_agents.py`: **rc=0**
- `tools/check_docs.py`: **rc=0**

波及可能性として、observed normalizer の caller は calibrator、execution receipt issuer、floor/oracle fixture、T126 回帰です。silo import 統一は `tools/pegasus/{silo_ladder_rung1,submit_silo_ladder_rung1}.sh`、third-party fetcher、歴史 evidence test に届きます。共有 loader caller の campaign loop、oracle report、ratified freeze／verify はコード未変更ですが、親の全走対象です。

境界確認:

- R-1: loader self-pass は追加していません。
- R-2: `t126_driver.py` は未変更です。
- R-3 後半: T126 envelope は上げていません。
- `output/`、docs、`external/ccbench`、registry、`FROZEN_MANIFEST` は無変更です。
- 登録較正 SHA は `753f535a…e5a49`、`contract_sha256` golden は `e576e9cd…2c01` のままです。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は exact 1 件です。
- `git add`／`git commit` は実行していません。

## 総括

- L6-B-1 の full-map 誤配線を exact 射影へ修正した。
- 受入赤 20 件の四つの根因すべてへコードまたは fixture 修正を入れた。
- A2-R1/R2、A4-R1、A7-R1、RI-B1 の検出力を強化した。
- 既存 assertion の緩和、skip、xfail、削除は行っていない。
- 凍結境界、R-1/R-2/R-3 後半、submodule 境界を維持した。
- 静的検査と 357 node の collection は rc=0。
- scheduler のユーザー認証失敗により pytest 実走は rc=16・0 node のまま。
- 親の全走では最初に calibrator publish 成功経路、次に silo 2% reject／3% pass、shell duplicate 負例を見るべきです。