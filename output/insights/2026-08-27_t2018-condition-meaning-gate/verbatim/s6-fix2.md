## 総括

T-2018 段6 fix round2を[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-condition-meaning-author/orchestrator/tests/test_condition_meaning_gate.py:348)のunstaged差分だけで実装しました。production、docs、driver、fixtureは変更していません。git add、commit、merge、rebaseも未実施です。

## Fix

- compile/run rc負例を`rc=4, stderr=b""`へ分離。
- compile/run stderr負例は`rc=0`専用nodeとして維持。
- process 6 nodeをすべてproductionの`assert_backoff_fixed_meaning`経路へ変更。
- compiler driftを安定名の2 nodeへ分割。
  - `test_compiler_identity_drift_after_version_is_rejected`
  - `test_compiler_identity_drift_after_compile_is_rejected`
- phase seamは対象phaseだけidentity不一致とし、他phaseはbaselineへ復帰。
- 実file raceやsleepは使用せず、version、compile、runを決定的なprocess seamで供給。

## 単一理由性

rc負例はstderr空、stderr負例はrc0です。compile seamは実行可能なbinary相当を生成し、run seamはBACKOFF_FIXED=5、start=1/2、bits=`4014000000000000`の有効出力を返します。

各identity nodeでは対象phaseの比較だけを外す確認走が`MeaningEvidence`まで到達し、非対象phaseの比較とprocess結果は正常なままです。

## 検査

- staged snapshot SHA-256: `9eb647bfe479af9b92efaebbdd7e42e4eb44770e053c179888fe2e342e5e1ac2`
- `s6-pre-fix2.patch`と完全一致。
- `git diff --check`: 異常なし。
- `git diff --cached --check`: 異常なし。
- unstaged変更はtestファイルだけです。

## 未実走・赤

8対象nodeのwrapper検査は`rc=16 / child_started=false`でした。原因は`qstat -Q preflight rc=1`です。

pytest childは一件も起動していないため、緑・赤・closedは申告しません。
