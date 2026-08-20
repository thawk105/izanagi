---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1420-c01-holdouts
seq: 1
title: '[T-1420] 8c事前登録条件C01の残ギャップ (holdouts未消費) を閉じた (コード+テスト、branch worktree-dev-wave-t1420-c01-holdouts、変異matrix = baseline 450 passed/1 known-red(C01 snapshot、統合commit後に反転予定)・4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 設計判断は {{D:c01-holdouts-dormant-check}} を参照。
- 段5 実装子の1回目試行は、実装自体はPlan v2と完全一致していたが完了報告に必須見出し
  `## 総括`が無く launcher validator (F43相当) に不採用となった。原因は親のprompt記述が
  「予算切れ時の代替」としか書かず常時必須と明記しなかったこと。親がgit diffで直接検収し
  実装のやり直しは不要と判断、報告フォーマットのみ修正して再投入し2回目で採用された
  (実装コードの再送信なし、model call・token を節約できた)。
- 段6 敵対レビュー2レンズ (正しさ境界・整合性実効性) が独立に同じ核心欠陥
  (candidate_id の集合比較では入れ替えを検出できない、`_deep_freeze`が非dict Mapping
  <UserDict等>を再帰変換しないため直接構築fixtureからmutable stateが漏れる) に収束した。
  fixで解消 (property内でcandidate_id exact一致検証+`dict(entry)`正規化)。
- `python3 tools/run_tests.py orchestrator/tests/test_s8b_ratified_freeze.py
  orchestrator/tests/test_p3_autonomous_workload_trial.py
  orchestrator/tests/test_s8c_preregistration_predicates.py -q` の初回実走で
  `test_noop_and_token_only_fixtures_never_satisfy`のC02/C07/C09パラメータ3件が
  非決定的に赤化したが、該当3 nodeidだけの単独再実行で3 passedに戻った。完全に独立した
  synthetic repo (`_init_repo(tmp_path)`) を使うテストで本waveの変更と無関係、xdist高並列下の
  既知フレーク (T-1362 waveのhandoffが記録した同型症状と一致) と判定し帰属しない。
  再走時 (fix後) は同3件とも緑だった。
- codex workspace-write sandbox内で`python3 tools/run_tests.py`を実行すると、内部の
  `systemd-run --user --scope`呼び出しが`guard_bash`hookに`qstat -Q preflight rc=1
  (Unknown user-id)`で拒否され実テストが0 nodeidになる制約を実測した (codexサブプロセスが
  Pegasus正規ユーザ資格情報を持たないためと推定)。親のセッションでは同じ制約を受けず
  正常に実走できることも実測済み。dev-wave改善候補としてhandoffに記録、reference節への
  統合は今回は見送り (予算満杯、既知)。
- dev-wave改善候補 (段8、ユーザー裁定へ返す。予算満杯のため即時のreference統合は行わない):
  1. 段5/6 author/fix promptで`## 総括`を「予算切れ時の代替」としか書かないと実装子の
     完了報告が launcher validatorに不採用になりうる。次に書く親への注意点として
     「常に最初の見出しにする」と独立に明記する運用を候補として記録。
  2. `tools/run_tests.py`のcodex workspace-write sandbox内`systemd-run`拒否は
     DW-S05-C「実走できない子は所見や要件をclosedと申告しない」の具体例として
     `docs/dev-wave/workers.md`へ一行追記する候補。
  3. contract JSON (`s8c_preregistration_evidence_contract.v1.json`condition_number=1)
     の`reachable_from`文言 (`"run_trial -> _run_workload -> load_ratified_freeze"`)が
     実装 (`run_trial`直下で直接呼ぶ) と字面上ズレている。evaluator自体はこの文字列を
     検査しないため機能上無害だが、契約文書の正確性としては別waveでの是正候補。

## 次の一手差分

### 完了

- [T-1420] P1・完了。C01がUNSATISFIED(ratified-generation-reference-absent)から
  EVIDENCE_UNDEFINED(completion-proof-not-machine-checkable)へ反転したことをlibrary経路
  (`s8c_preregistration_evidence.get_registry().evaluate_all()`直接呼び出し、CLI不使用)
  で確認済み。契約JSONのmachine_checkable反転・`_MACHINE_EVALUATORS`登録・
  `docs/phase3-8c-preregistration.md`は指示どおり対象外のまま。
  remaining: none
  base: 7a99425d9eff90556547f9c0bbf34807c2167d333d416f9908d3e0b5e5c723d7
