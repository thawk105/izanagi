結論として、wrapper 本体は実装可能です。ただし段 4 では、次の 2 点を brief へ補正すべきです。

- dispatch 走行の receipt/stdout は使い捨て木内に作られ、単純削除すると `--resume` の再検証が壊れるため、scratch root への退避・同一絶対 path への再実体化を wrapper の必須処理にする。
- SIGKILL 残骸の自動削除は、発火済み artifact が現存しないため `DW-G04` に従い今 wave では実装せず、既存 path を拒否して手動処理へ返す。

pytest は read-only sandbox のため未実走です。以下は静的検査に基づく段 2 プランです。

## 既存 seam と設計根拠

- harness CLI は `tools/mutation_harness.py:1857-1878`、引数正規化と runtime artifact 検査は `:1881-1918`。
- `--plan-only` は preflight・見積り後に rc=0 で戻る `:1957-1966`。実走だけ `--detached` が必須 `:1895-1896`。
- harness の最終 rc は期待一致なら 0、不一致なら 1 `:2086-2088`、`HarnessError` は 2、SIGINT/SIGTERM は 130/143 `:2093-2104`。
- `--resume` は tool/runner の絶対 path まで exact 比較する `:1657-1705`。したがって使い捨て木の絶対 path は invocation 間で固定する必要がある。
- dispatch evidence は `<repo>/output/pegasus-dispatch` に束縛され、resume 時に実 file を再読する `:859-908`。木を削除する前の退避が必要。
- harness 自身が runner を `cwd=<使い捨て木>`、stdout/stderr 結合、独立 session で起動する `:1116-1174`。wrapper は harness の stdout/stderr を加工せず親へ継承する。
- `run_tests.py` の `_REPO` は実行された script の checkout から決まる `tools/run_tests.py:46-49`。使い捨て木内の script を起動すれば dispatch の repo root も使い捨て木になる `:808-818`。

## 実装ファイルの予定構成

新規ファイルなので、以下は実装時に固定する予定行です。

### `tools/mutation_worktree.py`

- `L1-L36`: module docstring、import、保証範囲。「共有木の bytes を mutation 対象にしないだけで、物理永続性は保証しない」と明記。
- `L38-L91`: 定数、`MutationWorktreeError`、`SignalAbort`、`Preflight`／`SharedSnapshot` dataclass。固定 path は以下。
  - container: `<scratch-root>/.izanagi-mutation-worktree`
  - checkout: `<container>/repo`
  - dispatch evidence: `<scratch-root>/.izanagi-mutation-dispatch`
- `L93-L151`: Git 環境の濾過、command allowlist、`_run_git()`。allowlist に `worktree remove` と `submodule deinit` を置かない。
- `L153-L231`: source repo・commit・scratch・artifact の `_preflight()`。
- `L233-L279`: registered worktree の解析、共有 main/source の `status`／`submodule status` snapshot。
- `L281-L326`: container の原子的所有、worktree add、submodule 実体化、post-provision 検査。
- `L328-L368`: dispatch evidence の `_rehydrate_dispatch_evidence()`／`_stash_dispatch_evidence()`。
- `L370-L416`: harness argv 構築、環境、cwd、stdout/stderr 継承、rc 取得。
- `L418-L474`: SIGINT/SIGTERM 転送、active child 停止、`finally` teardown。
- `L476-L535`: argparse、`main()`、exit-code mapping、診断。

### `orchestrator/tests/test_mutation_worktree.py`

- `L1-L30`: wrapper を importlib でロード。
- `L32-L72`: `_git()`、commit、status snapshot helper。
- `L74-L170`: real Git fixture。main repo、linked source worktree、ローカル submodule origin、`external/ccbench`、固定 commit、repo 外 spec/out/scratch を作る。
- `L172-L215`: wrapper argv と小さい mutation spec の helper。
- `L217-L520`: 下記テスト群。

## CLI 契約

実行形は次とします。

```text
python3 tools/mutation_worktree.py
  [--source-repo PATH]
  [--commit REV]
  --scratch-root PATH
  --spec PATH
  --expected-spec-sha256 HEX64
  --out PATH
  --runner-mode {local,dispatch}
  [--resume]
  [--detached]
  [--plan-only]
  -- RUNNER_ARGV...
```

契約は次のとおりです。

- `--source-repo`: 既定は current directory。git worktree root そのものを要求する。
- `--commit`: 既定は `HEAD`。`REV^{commit}` を一度だけ full SHA へ解決し、以後は symbolic REV を使わない。
- `--scratch-root`: 必須。既存・非 symlink・書込／検索可能な directory。
- `--repo`: wrapper CLI では受け付けない。常に `<scratch-root>/.izanagi-mutation-worktree/repo` を生成して harness へ渡す。
- `--spec`、`--expected-spec-sha256`、`--out`、`--runner-mode`、`--resume`: harness へ意味を変えず渡す。
- `--` 後の argv: 最初の delimiter だけ wrapper が除き、harness argv では delimiter を再挿入する。各 runner token の追加・削除・並べ替え・shell 展開はしない。
- `--plan-only`: worktree provision、submodule 実体化、harness preflight、teardown までは行う。mutation／ledger write は行わず、`--detached` は不要。
- `--detached`: wrapper 自身を detach する option ではなく、既存 harness と同じ外側上限外起動の表明。非 plan-only では wrapper も provision 前に必須検査し、そのまま harness へ渡す。
- `--resume`:同一 `--scratch-root`、commit、spec、runner argv、runner mode を再利用する。固定 checkout path により harness の absolute identity 比較を維持する。
- stdout/stderr: harness の両 stream を捕捉・結合・tail 化せず、それぞれ親 process へ直接継承する。wrapper 自身の見積りは stdout、診断は stderr。

exit code は以下です。

- `0`、`1`、`2` およびその他の child rc: teardown と postcondition が成功した場合は harness rc をそのまま返す。
- `125`: wrapper の preflight、provision、起動、evidence 退避、teardown、共有木の事後比較の失敗。child rc が既にあれば stderr に併記する。
- `130`／`143`: wrapper が SIGINT／SIGTERM を受け、転送と teardown が成功した。
- signal 中でも teardown が失敗した場合は、安全失敗を優先して `125`。
- argparse の構文エラーは通常どおり `2`。

## preflight の fail-closed 署名

`S=source repo`、`C=解決済み commit`、`R=scratch root`、`D=固定 checkout`、`W=同一 common Git dir の全 registered worktree root` とします。

```text
preflight(...) → READY iff

  git(S, rev-parse --is-inside-work-tree) == "true"
  ∧ resolve(git(S, rev-parse --show-toplevel)) == resolve(S)
  ∧ git(S, rev-parse --verify --end-of-options REV^{commit}) == C
  ∧ C は full lowercase commit SHA
  ∧ lstat(R) は directory かつ symlink でない
  ∧ R は W のいずれの配下でもない
  ∧ R は write/search 可能
  ∧ lstat(<R>/.izanagi-mutation-worktree) == ENOENT
  ∧ container の mkdir(exist_ok=False) が成功
  ∧ spec/out は D および W のいずれの配下でもない
  ∧ shared main/source の porcelain と submodule status を取得できる
```

どの Git・`lstat`・resolve・列挙・mkdir が失敗しても「不明だから許可」へ丸めず `125` で停止します。

未 commit 差分については、source cleanliness を入場条件にはしません。`REV` を full commit SHA に固定し、その SHA から新 worktree を作るため、source の dirty bytes は構造的にコピーされません。さらに provision 後に HEAD と porcelain を再検査します。

通る正例は、段 1 probe が成立させた次の組です。

```text
source:
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree
commit:
  5a322447b8b90751a991ab8243e7f7570ee5c672
scratch:
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t503-disposable-worktree
spec/out:
  上記 scratch または別の repo 外 job directory 配下
```

この source は linked worktree root、scratch は registered worktree 外であり、probe は同 scratch 配下に worktree を実作成できています。

## provisioning と所要見積り

`tools/mutation_worktree.py:L281-L326` は次の順序に固定します。

1. container を `mkdir(mode=0o700, exist_ok=False)` で原子的に所有する。
2. source repo から次を shell 無しで実行する。

   ```text
   git worktree add --detach <container>/repo <full-commit-sha>
   ```

3. local modules cache だけを使って次を実行する。

   ```text
   git -C <repo> -c protocol.file.allow=always \
     submodule update --init --no-fetch -- external/ccbench
   ```

4. `git -C <repo> rev-parse --verify HEAD == C` を要求する。
5. `git -C <repo> status --porcelain=v1 --untracked-files=all --ignore-submodules=none` が byte 空であることを要求する。
6. `git -C <repo> submodule status -- external/ccbench` が初期化済み・gitlink pin 一致であることを要求する。
7. いずれかが失敗したら harness は起動せず teardown へ進む。

段 1 実測をそのまま点見積りに使います。

- worktree add: 10.10 s
- submodule: 1.45 s
- provision 合計: 約 11.55 s
- recursive delete: 4.90 s
- wrapper 固定 overhead: 約 16.45 s + prune／postcheck
- 追加 disk: 約 134 MB

したがって全体は `harness の既存 estimate + 約16.45秒`。`--plan-only` もこの provision／teardown 費用を払います。これは実測点であって上限保証ではありません。

## harness 起動と dispatch evidence

`tools/mutation_worktree.py:L370-L416` から、次の child を起動します。

```text
<current sys.executable>
<generated-repo>/tools/mutation_harness.py
--repo <generated-repo>
--spec <absolute external spec>
--expected-spec-sha256 ...
--out <absolute external out>
--runner-mode ...
[--resume] [--detached] [--plan-only]
-- <runner argv unchanged>
```

- cwd は生成した worktree root。
- `GIT_DIR`、`GIT_WORK_TREE` など repository 選択用 `GIT_*` は継承せず、既存 harness と同じ allowlist にする。
- `GIT_TERMINAL_PROMPT=0`、`PYTHONDONTWRITEBYTECODE=1` を設定する。
- stdin は `/dev/null`、stdout/stderr は親から継承する。
- spec/out は絶対 path へ正規化し、source/main/generated worktree の外であることを wrapper が先に検査する。

dispatch では追加処理が必要です。現行 harness は receipt と job stdout の実 file を `<generated-repo>/output/pegasus-dispatch` から再検証するため、単純削除すると `--resume` が必ず赤になります。

そこで `L328-L368` に次を置きます。

- 新規 dispatch run: external evidence directory が既存なら上書きせず停止。
- teardown 前: `<D>/output/pegasus-dispatch` を同じ filesystem 上の
  `<R>/.izanagi-mutation-dispatch` へ rename 退避。
- dispatch resume: provision/post-clean 検査後、退避 directory を元の同一絶対 path へ rename してから harness を起動。
- harness 終了後は再び scratch 側へ戻してから worktree を削除。
- symlink、既存 destination、rename 失敗はすべて `125`。
- rename 順序を検査するだけであり、fsync 後の物理永続性は主張しない。

この evidence shuttle を入れない案は、`mutation_harness.py:887-908` と `:1706-1727` により `--resume` 契約を壊すため不採用です。

## teardown と共有 checkout の事後検査

`tools/mutation_worktree.py:L418-L474` は所有済み container を囲む一つの `try/finally` にします。

- signal handler は container 所有前に設置し、SIGINT/SIGTERM を active child process group へ転送する。
- harness には既存の runner cleanup に必要な最大 10 秒に余裕を足した 12 秒を与える。
- 12 秒で harness が終わらなければ harness group を SIGKILL し、使い捨て木の破棄へ進む。独立 session の runner が残る可能性は後述の残余リスク。
- signal handler は二度目以降を ignore へ変え、teardown を中断させない。
- teardown は evidence 退避後、所有済みの固定 container に限って、shell/glob 無しで次を行う。

  ```text
  rm -rf -- <exact-owned-container>
  git -C <source-repo> worktree prune
  ```

- recursive delete が失敗しても prune を試し、複数の失敗を集約する。
- `git worktree remove` と `git submodule deinit` は command allowlist に存在させない。
- prune 後に generated path が `git worktree list --porcelain` から消えたことを確認する。

共有 checkout と source worktree については、provision 前と prune 後に以下の stdout bytes を比較します。

```text
git status --porcelain=v1 --untracked-files=all --ignore-submodules=none
git submodule status --recursive
```

primary/main worktree と source worktree が同一なら一度だけ取得します。差があれば並行 session 由来か wrapper 由来かを推測せず、「共有木非接触を証明できない」として `125`。テストではさらに fixture の sentinel file bytes を比較します。

## stale 掃除の裁定案

現時点では自動 stale 掃除を実装しません。

段 1 の具体 path だった以下は、probe 自身が既に削除・prune 済みです。

```text
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t503-disposable-worktree/probe-wt-1
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t503-disposable-worktree/probe-wt-2
```

現在の job directory に両 path はなく、`git worktree list --porcelain` にも登録がありません。したがって「SIGKILL で残った本 wrapper 所有 artifact」という `DW-G04` の既存 artifact path を示せません。

今 wave の動作は以下に限定します。

- 固定 container が既存なら、それを stale と推測せず拒否する。
- 既存 container をこの invocation の `finally` で削除しない。
- stderr に exact path、`git worktree list` 確認、`rm -rf`、`git worktree prune` の手動手順を出す。
- 別 scratch root を使う fresh run は妨げない。

後続の設計メモには、次を残します。

1. container 作成時に exact schema の owner record と `flock` file を repo 外へ作る。
2. record は common Git dir identity、固定 worktree path、commit、host、boot ID、PID、process starttime を束縛する。
3. 次回起動は同じ scratch root の固定 record だけを見る。root 全体を prefix scan しない。
4. lock を取得できなければ live session として非接触。
5. lock を取得できても record 欠落・未知 schema・symlink・Git identity 不一致なら自動削除せず停止。
6. exact owner record と Git registration が一致した場合だけ directory delete → prune。
7. この機能を有効化するには、実際の SIGKILL 残骸 path または計測 ID を次 wave brief に載せる。

## テスト一覧

`orchestrator/tests/test_mutation_worktree.py` に以下を置きます。各説明は、そのテストが kill する欠陥です。

1. `test_real_plan_only_accepts_linked_worktree_commit_and_external_scratch` — 正常入力まで過剰拒否する preflight を kill。
2. `test_source_must_be_the_exact_worktree_root` — nested directory を source root と誤認する変更を kill。
3. `test_uncommitted_source_bytes_are_not_copied_to_disposable_commit` — source の dirty bytes を checkout へコピーする変更を kill。
4. `test_unknown_or_noncommit_revision_fails_before_container_claim` — commit 解決失敗後も provision する変更を kill。
5. `test_scratch_inside_any_registered_worktree_is_rejected` — main または linked worktree 内への nested checkout を許す変更を kill。
6. `test_scratch_symlink_is_rejected_even_when_target_is_writable` — symlink を resolve 後に許す変更を kill。
7. `test_unwritable_scratch_fails_before_git_worktree_add` — writeability の UNKNOWN を許可へ丸める変更を kill。
8. `test_existing_container_is_preserved_and_never_claimed` — 他 session の同名 directory を wrapper 所有として消す変更を kill。
9. `test_spec_and_out_are_rejected_inside_registered_or_generated_repo` — runtime artifact を共有木へ書く変更を kill。
10. `test_provision_uses_detached_full_sha_and_materializes_ccbench_without_fetch` — symbolic HEAD 使用または submodule 初期化省略を kill。
11. `test_post_provision_rejects_head_different_from_requested_commit` — checkout 後の SHA 再確認を外す変更を kill。
12. `test_post_provision_rejects_nonempty_porcelain_before_harness` — dirty disposable tree で harness を起動する変更を kill。
13. `test_harness_argv_injects_only_generated_repo_and_preserves_runner_remainder` — `--repo` 誤注入または runner token の欠落・並べ替えを kill。
14. `test_plan_only_needs_no_detached_flag_and_still_tears_down` — plan-only を実走扱いする変更、または plan-only 後の残骸を kill。
15. `test_real_run_without_detached_stops_before_provision` — detached 自己申告を遅延・省略する変更を kill。
16. `test_recreated_fixed_path_preserves_resume_tool_and_runner_identity` — invocation ごとに random worktree path を使う変更を kill。
17. `test_harness_uses_disposable_cwd_sanitized_env_and_inherited_streams` — source cwd、repository 選択 env、stdout/stderr 捕捉を kill。
18. `test_dispatch_evidence_is_moved_out_before_recursive_delete` — receipt/stdout を worktree と一緒に消す変更を kill。
19. `test_dispatch_resume_rehydrates_exact_absolute_evidence_paths` — resume 前の evidence 再実体化を外す変更を kill。
20. `test_child_return_code_is_propagated_after_successful_postconditions` — child rc を常に 0/125 へ丸める変更を kill。
21. `test_exception_after_provision_still_deletes_and_prunes` —例外経路の `finally` を外す変更を kill。
22. `test_sigint_and_sigterm_are_forwarded_before_teardown` — wrapper だけ終了して harness を残す変更を kill。
23. `test_teardown_syscall_order_is_recursive_delete_then_prune_not_physical_durability` — prune と delete の逆転を kill。docstring は「検査するのは syscall 順序であって物理永続性ではない。」
24. `test_disposable_run_claims_only_shared_tree_bytes_unchanged_at_observation_points` — main/source の sentinel を触る変更を kill。docstring は「共有木の bytes 不変だけを主張する。L-B の物理永続性は主張しない。」
25. `test_shared_tree_snapshot_drift_fails_closed` — post-run の共有木比較を省く変更を kill。
26. `test_teardown_failure_overrides_child_rc_with_wrapper_rc_125` — cleanup 赤を child 成功として返す変更を kill。
27. `test_git_command_surface_excludes_worktree_remove_and_submodule_deinit` — F26 の禁止 command を追加する変更を kill。

real Git fixture は `tmp_path` 内だけで、次の順に作ります。

1. 小さい submodule origin を `git init`、`CMakeLists.txt` を commit。
2. main repo に実 `tools/mutation_harness.py`、mutation target、pytest target を配置。
3. `git -c protocol.file.allow=always submodule add` で `external/ccbench` を追加して commit。
4. `git worktree add --detach <source> HEAD` で linked source を作る。
5. main/source の `external/ccbench` を local cache から初期化。
6. spec/out/scratch は両 repo の sibling に置く。

共有実 checkout は使わないため `real-repo` xdist group は不要です。

## 変異事前登録候補

実装後に old 逐語の一意性を再確認しますが、事前登録候補は次の 14 件です。

| ID | 無効化する述語 | 確実に赤になるテスト | 単一理由性 |
|---|---|---|---|
| MW-01 | `show-toplevel == source` | `test_source_must_be_the_exact_worktree_root` | harness は生成後の `--repo` だけを検査し、source path を知らない |
| MW-02 | scratch が全 registered root 外 | `test_scratch_inside_any_registered_worktree_is_rejected` | Git は nested worktree を作成でき、teardown 後の endpoint snapshot も元へ戻る |
| MW-03 | scratch leaf の非 symlink | `test_scratch_symlink_is_rejected_even_when_target_is_writable` | resolve 先が正常なら Git/harness は拒否しない |
| MW-04 | container 所有 flag は mkdir 成功後だけ立てる | `test_existing_container_is_preserved_and_never_claimed` | Git の後段拒否とは別に、既存 sentinel の誤削除を直接検出する |
| MW-05 | checkout path を scratch ごとに固定 | `test_recreated_fixed_path_preserves_resume_tool_and_runner_identity` | harness は絶対 tool/runner path を exact 比較するため path 変更だけで赤 |
| MW-06 | post-provision `HEAD == requested SHA` | `test_post_provision_rejects_head_different_from_requested_commit` | harness は実際の HEAD に自己束縛するだけで、要求 commit を知らない |
| MW-07 | `submodule update --init` を必須化 | `test_provision_uses_detached_full_sha_and_materializes_ccbench_without_fetch` | plan-only harness は submodule marker を検査しない |
| MW-08 | spec が source/main 外 | `test_spec_and_out_are_rejected_inside_registered_or_generated_repo` の spec case | harness は generated repo 外であれば source 内 spec を受理する |
| MW-09 | runner remainder の無変更 | `test_harness_argv_injects_only_generated_repo_and_preserves_runner_remainder` | `-q` 等の非必須 token を落としても harness preflight は通る |
| MW-10 | child rc の直接返却 | `test_child_return_code_is_propagated_after_successful_postconditions` | rc の後段 consumer は wrapper だけ |
| MW-11 | recursive delete → prune の順序 | `test_teardown_syscall_order_is_recursive_delete_then_prune_not_physical_durability` | prune を先にすると live path の admin record は残り、二度目の prune は無い |
| MW-12 | post-run shared snapshot exact 比較 | `test_shared_tree_snapshot_drift_fails_closed` | harness は source/main に注入された別変更を検査しない |
| MW-13 | dispatch evidence を delete 前に退避 | `test_dispatch_evidence_is_moved_out_before_recursive_delete` | worktree 削除後に同 evidence を回収する層は無い |
| MW-14 | wrapper signal を active child へ転送 | `test_sigint_and_sigterm_are_forwarded_before_teardown` | wrapper PID だけへの signal は child session へ自然伝播しない |

次は前後層に mask されるため事前登録しません。

- commit 解決省略: `git worktree add` 自身も不正 object を拒否する。
- writable 検査省略: container mkdir が同じ入力を拒否する。
- porcelain postcheck 省略: harness `_assert_clean_tracked` が後段で拒否する。
- `--detached` wrapper 検査省略: harness が後段で拒否する。

## docs 差分案

### `docs/dev-wave/mutation.md` の `DW-M05` 追記案

```markdown
変異本走は、固定 commit から `tools/mutation_worktree.py` が repo 外の scratch root に作る
使い捨て専有 worktree を `--repo` として行い、共有 checkout を直接 `--repo` にしてはならない。
wrapper は detached worktree と `external/ccbench` を実体化した後に HEAD 一致と空 porcelain を
再検査し、正常・例外・SIGINT・SIGTERM の全経路で専有 directory の再帰削除後に
`git worktree prune` を行う。`git worktree remove` と `git submodule deinit` は使わない。
dispatch の receipt/stdout は削除前に同じ scratch root へ退避し、`--resume` では同一の
絶対 worktree path へ再実体化して既存の evidence 検査を通す。これは共有 checkout の
観測前後 bytes 不変だけを主張し、物理ノード死後の永続性を主張しない。

wrapper 自身を変異対象にする wave の matrix に限り、段 4 の明示裁定により従来経路を外側の
harness として使える。その場合も同一 spec を wrapper 経由で対照走行し、変異 ID ごとの
KILLED / SURVIVED / MISMATCH / TIMEOUT が一致しなければ受理しない。
```

### `docs/mutation-restore-durability-design.md` §9.2 追記案

```markdown
**2026-08-06 裁定 V-1 (b) の第一 slice:** `mutation_harness` 自体は変更せず、固定 commit から
repo 外へ使い捨て専有 worktree を provision する wrapper を実装する。変異・runner・submodule・
ignored dispatch artifact はその木へ閉じ、終了時は木を directory ごと破棄する。これにより
canonical state root、incarnation nonce、consumer lease、in-place repair の発行者問題は
「共有木を修復する」のではなく「専有木を捨てる」ことで回避する。

この slice は write-ahead journal、原子的 target 置換、`clean` capability、metadata admission、
quiescence 証明を実装しない。したがって §9.1 の 1 / 4 / 5 / 6、V-3 / V-4 / V-5 は
in-place 復元経路を作る後続 slice まで未発火であり、放棄ではない。テストが固定するのは
teardown の syscall 順序と共有木の観測前後 bytes 不変だけで、L-B は引き続き `UNKNOWN` である。

SIGKILL 残骸の自動回収は、`DW-G04` の発火条件を満たす既存 wrapper artifact path が無いため
本 slice では実装しない。既存の固定 container は fail-closed に拒否し、owner record と
exclusive lock による自動回収案は実残骸が観測された wave の設計メモへ留める。
```

なお、§9.2 を更新する際は文書冒頭 `docs/mutation-restore-durability-design.md:3-4` の
「択一待ち」「production 実装ゼロ」も同時に現状へ直さないと本文と矛盾します。

## 総括

骨子:

- 固定 commit・固定 scratch 相対 pathから detached worktree を一度 provisionし、その中の既存 harness をそのまま使う。
- spec/out と dispatch evidence は repo 外へ置き、dispatch evidence だけ resume 前後に同一絶対 path へ往復させる。
- 全終了経路を一つの `finally` に集約し、`rm -rf` → `git worktree prune` → shared snapshot 比較で閉じる。
- stale 自動削除は `DW-G04` により延期し、今 wave は既存 path を非接触で拒否する。

最大の技術的リスク:

1. dispatch receipt/stdout の退避・再実体化を誤ると、台帳は残っても `--resume` の evidence 再検証が壊れる。
2. harness の runner は別 session なので、wrapper SIGTERM 後も異常 child が残り、削除中の使い捨て木と競合する可能性がある。共有木は守れるが child 終了までは保証しない。
3. SIGKILL stale 自動回収を延期するため、同じ scratch root の resume は人手整理まで止まる。別 scratch の fresh run は可能。

親裁定への見解:

- **P1: 賛成・補強。** scratch 必須に加え、固定 child path、全 registered worktree 外、spec/out 外部、原子的 container 所有を要求する。
- **P2: 一部反対。** `finally` と signal teardown は採用するが、stale 自動掃除は既存 artifact 不在のため今 wave では実装しない。
- **P3: 賛成。** `DW-M05` は wrapper 経由を必須化し、推奨表現にはしない。
- **P4: 賛成。** wrapper 自身の mutant 注入には従来外側 harness が必要であり、同一 spec の wrapper 対照走行を変異 ID ごとに照合する。