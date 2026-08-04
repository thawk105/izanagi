F1〜F4 の fix を実装しました。production 判定ロジック、既存テスト、fixture、docs は変更しておらず、commit もしていません。

## 変更内容

- [role_session_isolation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/role_session_isolation.py:2) — F1 / P5-3  
  process-local・provider 非認証・未予約 token 拒否が射程外という限界を残しつつ、未実装 P3 ledger が発行を所有するとの断定を削除しました。

- [test_role_session_isolation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:113) — F1 / P5-3  
  「別設計依存として未実装」という記述と、誤った owner 断定の不在を固定しました。

- [test_role_session_isolation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:242) — F3 / P5-2  
  永続化した重複 `child_id` artifact を独立 verifier が拒否する負例を追加しました。

- [test_role_session_isolation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:271) — F2 / P5-2  
  truthy 非文字列と、非空 provenance から `child_id` だけ欠落した場合の独立負例を追加しました。

- [test_role_session_isolation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:323) — F4 / P5-2  
  `claude-headless` の invalid role attempt を含む正当な partial run の受理を固定しました。

P5-1 の production／test には変更ありません。

## F1〜F4 の追加 nodeid

- F1 — `orchestrator/tests/test_role_session_isolation.py::test_leaf_docstring_keeps_unimplemented_dependency_without_owner_claim`: 未実装依存の明示を残し、存在しない ledger の owner 断定を防ぎます。
- F2 — `...::test_consumer_rejects_truthy_non_string_child_id` / `...::test_consumer_rejects_missing_child_id_from_nonempty_provenance`: truthiness への弱体化と欠落時既定値への回帰を検出します。
- F3 — `...::test_file_verifier_rejects_persisted_duplicate_child_id`: `verify_autonomous_trial_files()` の独立検証配線を固定します。
- F4 — `...::test_consumer_accepts_invalid_claude_attempt_in_partial_run`: 検査対象を `valid` 以外へ広げる過剰拒否を検出します。

## 受理集合

production の変更前後で受理集合の差はありません。新たに拒否または受理される runtime 入力はゼロです。増えたのは既存挙動を固定するテスト検出力だけです。

各一行を無効化した場合に赤くなる node は次のとおりです。

- docstring の未実装記述／owner 非断定 → F1 node
- `session_id` の exact string 検査 → F2 truthy 非文字列 node
- `child_id` 欠落を `None` に射影する検査 → F2 欠落 node
- verifier から completeness 検査への呼出し → F3 node
- `status == "valid"` filter → F4 node

## 検査結果

- `python3 -m py_compile`（変更2ファイル）: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 対象 test + `test_plain_runner_coverage.py`: rc=16、未実走  
  `tools/run_tests.py` が `qstat -Q preflight` で停止しました。`qstat -Q` / `qstat -B` は socket 作成不能でともに rc=1 でした。Pegasus ログインノード上の pytest は禁止されているため、ローカル代替実行はしておらず、緑は主張しません。
- 親 docs 未 land に起因する期待赤: なし
- mutation matrix: 親の段6責務であり未実施

## 所有外への波及

- production caller は `p3_autonomous_workload_trial.py` の tracker 生成・共有、`claude_projected_provider.py` の観測、`autonomous_trial_completeness.py` の write-time／file verifier／CLI consumer です。いずれも未変更です。
- 共有 fixture は `test_autonomous_trial_completeness.py` の `_complete_trial`、`_role_invalid_trial`、`_persist` を新規テストから利用するだけで、fixture 自体は未変更です。
- `test_claude_transport.py` の `_DeepCopyReceiptFixtureProvider` は `FixtureRoleProvider` 由来の role 固有 `child_id` を保持することを静的確認しました。親裁定どおり修正不要です。
- 直接 constructor caller は `test_claude_transport.py`、`test_p3_autonomous_workload_trial.py`、今回のテストファイルです。optional tracker を省略する既存 caller の契約は不変です。
- 既存 consumer test／fixture／assert／期待値は一切編集していません。

## 総括

F1 は、leaf が担えない限界を削って過大主張することなく、まだ存在しない P3 origin ledger を既存の発行所有者として扱う事実誤認だけを除去しました。F2 は空値と `None` だけでは生き残る `if not session_id` への弱体化、および欠落時に任意の既定値を補う回帰を、それぞれ独立した負例で拘束しました。F3 は合成 artifact の直接検査だけでなく、運用者が保存済み `attempts.jsonl` と `report.json` を検証する実ファイル経路まで重複 session 拒否を固定しています。F4 は invalid attempt に provenance が無い正当な partial run を受理させ、検査対象を valid 以外へ不用意に拡張する退行を防ぎます。production 判定ロジックと受理集合は変更していません。静的検査と必須 checker はすべて rc=0 ですが、pytest は計算ノード dispatch infrastructure の rc=16 により開始されていないため、親による sanctioned 環境での対象 node・meta-test・変異 matrix・受入再走が必要です。