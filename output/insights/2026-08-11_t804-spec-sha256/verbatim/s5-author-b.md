## 総括

実装子 B の変更を完了しました。docs・所有外ファイルは編集せず、commit も作成していません。

変更内容:

- driver
  - standalone/run flow に approved spec を伝播。
  - run flow は spec load と manifest verify を各1回に限定。
  - `gate_check` の `verified_manifest` 注入を exact type・実 manifest hash・spec hashで再束縛。
  - spec 不一致時は実走前に拒否し、prepare/evaluate・campaign・budget・markerを生成しないテストを追加。
- report
  - official 経路で spec load後に実 verifierを呼び出す。
  - official observations のみ `spec_sha256` を掲載。
  - legacy observations からは同 fieldを完全に除外。
  - spec一致／別spec拒否のmetamorphic CLIテストを追加。
- judge
  - CLIへ `--manifest` / `--repo-root` を追加し、freeze再検証→spec load→manifest実再検証を実装。
  - `judge_oracle` の2 hash引数をrequired keyword、defaultなしに変更。
  - manifest/spec hashおよびofficial manifest kind不一致を判定不能へ倒す。
  - legacyからverdict artifactへ到達しない統合テストを追加。
- artifacts
  - production差分なし。manifest/observations schemaは`v1`のまま、loaderもclassifier契約を維持。

変更ファイルは [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py)、[report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_report.py)、[judge](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py) と対応する3テストです。

検査状況は「実装済み・pytest未実走」です。`tools/run_tests.py`で以下を試しましたが、いずれも`qstat -Q preflight rc=1`でdispatch前に停止しました。

- 新設metamorphicテスト6 nodeid
- 指定されたconsumer pin 2 nodeid
- B所有テスト5ファイル＋manifest contract＋`test_pytest_collection_config.py`

成功した静的検査:

- 全変更ファイルの`py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- production consumer集合:
  - manifest loader = judge/report
  - observations loader = judge
  - verifier = driver/judge/report
- judgeのrequired keyword 2件にdefaultがないことを確認

赤の内訳:

- pin golden待ちで意図的に赤となる見込み:
  - `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`
  - `test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
  - 静的確認ではreport/judge hashのみstale、artifacts hashは一致。
- 回帰: pytest未実走のため未確定。観測済みのテスト赤はありません。
- 当初のconsumer pin 2件は静的集合上は解消済みですが、実走緑は主張しません。

所有外への波及:

- A所有のpin goldenは親段で最終source bytesに更新が必要です。
- A所有のconsumer contract testはjudge追加後の集合と静的に一致します。
- 共有fixtureは再利用のみで未編集です。
- `s8b_verdict.judge_combined`のverdict封印は裁定どおりscope外です。
- artifacts系テストとbinding driftguardはproduction契約の間接consumerですが、今回直接編集は不要でした。