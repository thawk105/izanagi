実装は完了しました。**実装済み・未実走**です。pytest、commit、docs 更新は行っていません。

変更ファイル:

- [t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_coordinator.py:201)
  - `_assert_declared_file_identity()`
  - `_assert_staged_file_identities()`
  - `prepare_group()`
  - `_subprocess_scheduler()`
- [t810_pbs_wrapper.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/tools/pegasus/t810_pbs_wrapper.py:341)
  - `publish_wrapper_request()`
- [test_t810_coordinator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_coordinator.py:104)
  - `_config()` fixture 実体化
  - S-A′、S-B′、S-D′、M1〜M6、P1/P2 のテスト
- [test_t810_pbs_wrapper.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t922-measure-happypath/orchestrator/tests/test_t810_pbs_wrapper.py:106)
  - wrapper/binary fixture 実体化
  - publication 前の宣言 hash 不一致負例

追加した述語は逐語で次のとおりです。

- `sha256(実 bytes of slot["wrapper_path"]) == slot["wrapper_sha256"]`
- `sha256(実 bytes of slot["wrapper_path"]) == sha256(実 bytes of 同梱 t810_pbs_wrapper.py)`
- `sha256(実 bytes of slot["binary_source_path"]) == slot["binary_sha256"]`
- `roots = repository_roots_from_git_identity(resolve_git_identity(coordinator repo root)) ∪ caller repository_roots`

同梱 wrapper anchor は coordinator 自身の `__file__` から導出しています。`pbs_wrapper.__file__` は使用していません。binary の anchor 比較、依存閉包、node 読取時点の束縛、guard/budget は実装していません。

挙動差:

- prepare 後に wrapper または binary が改変された入力を、qsub 前に新たに拒否します。
- 宣言 hash と実 bytes が違う staged file を publication 前に拒否します。
- 宣言値とは自己整合するが、同梱 wrapper と異なる wrapper を拒否します。
- caller が live repository root を roots から除外して repo 内へ `work_root` を置く迂回を拒否します。
- 正当な repo 外 `work_root` と、同梱 wrapper と byte 同一の staged wrapper は引き続き受理します。
- 空の caller roots は従来どおり拒否するため、受理集合は広げていません。

変異対応:

- M1: `test_scheduler_adapter_rejects_wrapper_changed_after_prepare` を追加。`_scheduler_effect()` を通さず最内 adapter を直接検査するため、前段の先取りなし。
- M2: `test_staged_wrapper_must_match_shipped_module_bytes` を追加。実 bytes と宣言 hash は一致させており、宣言一致検査には先取りされません。
- M3: `test_prepare_group_rejects_forged_git_identity_before_any_mkdir` を追加。`prepare_group()` 直呼びかつ `mkdir` 到達を fail に固定しました。
- M4: 同負例に加え、`test_prepare_group_accepts_external_root_with_anchor_union` で live anchor と caller roots の双方が保持されることを検査します。
- M5: `test_generated_script_executes_staged_wrapper_cli` に照準変更。旧テストの slot-00 exact assertion をこの統合テストへ移し、「slot-00 が別 slot の request を指す」変異が旧テストに先取りされない形にしました。他の12 slotの期待は維持しています。
- M6: `test_declared_identity_rejects_file_swapped_during_read` を追加。読取 bytes は宣言値と一致したまま、同 inode の mtime だけ確実に変えるため、前後 fingerprint 検査だけが拒否理由です。
- P1: repo 外の正当な work root と追加 caller root の受理を実装。
- P2: staged wrapper と同梱 module の byte 同一、および prepare 成功を実装。

S-D′ は script 最終行を `shlex.split()` し、そこから得た staged wrapper argv をそのまま subprocess 起動します。`PBS_JOBID` は subprocess env で付与し、`os.uname()` と `os.sched_getaffinity(0)` は実値のままです。load 待ちだけを子プロセス用 `sitecustomize` で固定し、exit code `2`、stdout `pre_release_invalid`、node receipt の PBS ID／hostname を固定しています。evil wrapper の負例は、宣言 hash まで自己整合させたうえで qsub effect 前に anchor 検査が拒否します。

所有外への静的波及可能性:

- `prepare_group()` の全 caller は、coordinator repo の live git identity 解決と roots 追加を受けます。
- placeholder `wrapper_sha256` や実在しない staged wrapper/binary を使う共有 fixture は拒否されます。
- prepare 後に staged file を置換する caller は `_subprocess_scheduler()` で拒否されます。
- `test_mutation_fanout_contract.py` の別 schema の `wrapper_sha256` は対象外です。
- custom injected scheduler adapter、staged dependency closure、node-side TOCTOU は未解決のままです。

静的確認は AST parse と `git diff --check` が成功しました。制約 meta-test を検索し、新規 nodeid の登録を要求する対象は見つかりませんでした。dev-wave 段5契約に従い、docs・handoff・commit・親の全走には触れていません。

## 総括

S-A′、S-B′、S-D′と fixture 実体化を所有内4ファイルへ実装しました。変更は拒否側の純増です。テスト実測は親へ委ねるため、最終状態は **実装済み・未実走** です。