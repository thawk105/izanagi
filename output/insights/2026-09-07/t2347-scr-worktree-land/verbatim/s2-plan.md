## 総括

案 (a) を採用し、[`_registered_worktree_paths`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449) だけを record 単位の解析へ変更する。

- `prunable` 行を同一 record に持つ登録だけを重なり検査から除外する。
- 実在する登録、非 prunable の解決失敗、登録 record がゼロの場合は従来どおり fail-closed。
- consumer の [`_execute_fold_gate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3804) は変更しない。
- job script、`/scr` allowlist、prune、他 tool、docs は変更しない。
- pytest は未実走。指定された5ファイルの静的確認のみ実施した。

## 実装プラン (file:line)

[`tools/dev_wave_land.py:3449-3471`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449) を次の形へ置き換える。

```python
def _registered_worktree_paths(repository: _Repository) -> tuple[Path, ...]:
    raw = _require_git(
        _git(repository.wave, "worktree", "list", "--porcelain"),
        "fold gate registered worktree list",
        RC_FOLD_GATE,
    )
    paths: list[Path] = []
    saw_worktree_record = False
    for raw_record in raw.split(b"\n\n"):
        lines = raw_record.splitlines()
        is_prunable = any(
            line == b"prunable" or line.startswith(b"prunable ")
            for line in lines
        )
        for line in lines:
            if not line.startswith(b"worktree "):
                continue
            saw_worktree_record = True
            if is_prunable:
                continue
            try:
                paths.append(
                    Path(os.fsdecode(line.removeprefix(b"worktree "))).resolve(
                        strict=True
                    )
                )
            except (OSError, UnicodeError) as exc:
                raise _FoldGateFailure(
                    f"registered worktree path cannot be resolved: {exc}"
                ) from exc
    if not saw_worktree_record:
        raise _FoldGateFailure("registered worktree list is empty")
    return tuple(paths)
```

変更点の境界は以下のとおり。

- 現行 [`:3456`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3456) の行走査を、空行 `b"\n\n"` 区切りの record 走査＋record 内の行走査へ組み替える。
- `prunable` は独立した field 行として、`b"prunable"` または `b"prunable "` で始まる行だけを認識する。branch 名や path 中の文字列 `"prunable"` は判定材料にしない。
- record 内に複数の `worktree ` 行がある異常入力でも、現行同様すべて走査する。`worktree ` 以外の行は、`prunable` marker の認識を除き引き続き無視する。
- [`:3461`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3461) の `os.fsdecode` は残し、非 prunable の `worktree ` path bytes にだけ適用する。
- [`:3465`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3465) の `(OSError, UnicodeError)` 捕捉と `_FoldGateFailure` 化は変えない。prunable record は意図的に decode/resolve 前に除外するが、非 prunable の decode 不能は従来どおり赤。
- [`:3469`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3469) の空判定対象だけを `paths` から `saw_worktree_record` へ変える。全登録が prunable の場合は `()` を返し、`worktree ` 行が本当にゼロの場合だけ失敗させる。
- [`:3474-3475`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3474) の重なり定義、および [`:3811-3820`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3811) の唯一の consumer は変更しない。

発生源の [`a5_second_boot_backoff_sweep.sh:459-469`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:459) と終了時 cleanup [`:123-186`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:123) は参照のみとする。

## テスト設計 (不変条件ごと)

追加先はすべて [`orchestrator/tests/test_dev_wave_land.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:1)。新規 test file は作らない。

既存の使い捨て repo 基盤を再利用する。

- `_git`: [`:89-102`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:89)
- `_Repo`: [`:148-231`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:148)
- `_repo` context fixture: [`:383-389`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:383)

[`test_dev_wave_land.py:391`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:391) の `_fake_gate_receipt` 前へ、次の補助 helper を置く。

```python
def _make_prunable_worktree(
    repo: _Repo,
    name: str = "job-repo",
) -> tuple[Path, Path, bytes]:
    path = repo.root / "scratch" / name
    path.parent.mkdir()
    _git(repo.main, "worktree", "add", "--detach", str(path), repo.base)
    admin = Path(
        (path / ".git").read_text(encoding="utf-8")
        .removeprefix("gitdir: ")
        .strip()
    )
    shutil.rmtree(path)

    result = LAND._git(repo.main, "worktree", "list", "--porcelain")
    assert result.returncode == 0
    record = next(
        record
        for record in result.stdout.split(b"\n\n")
        if b"worktree " + os.fsencode(path) in record.splitlines()
    )
    assert any(
        line.startswith(b"prunable ")
        for line in record.splitlines()
    )
    return path, admin, record + b"\n\n"
```

これにより、合成文字列だけで済ませず、本物の `git worktree add`、path 削除、本物の `git worktree list --porcelain` を通す。

テスト本体は、fold-gate テスト群の直前である現行 [`:9212`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9212) へまとめて追加する。

1. **不変条件1 — 実在登録との重なり拒否**

   `test_registered_worktree_paths_preserves_existing_overlap_rejection`

   - `_repo()` の本物の main/wave 登録を `_registered_worktree_paths` が両方返すことを確認。
   - wave 配下に隔離 dir 候補を作り、`LAND.tempfile.TemporaryDirectory` だけを、その path を返す context manager に差し替える。
   - `_execute_fold_gate` を呼び、`fold gate isolation directory overlaps a registered worktree` の `_FoldGateFailure` を期待する。
   - 単に例外型だけでなくメッセージも固定し、後段の別エラーによる偽陽性を防ぐ。

2. **不変条件2 — 非 prunable の解決失敗は fail-closed**

   `test_registered_worktree_paths_fail_closed_for_nonprunable_decode_and_resolution_errors`

   - `failure_kind=("resolve", "decode")` の parameterize 1関数とする。
   - 実在する main 登録を含む本物の porcelain 出力を使う。
   - `resolve` case は対象 path かつ `strict=True` の場合だけ `PermissionError` を発生させる。
   - `decode` case は対象 bytes に対する `os.fsdecode` だけ `UnicodeError` を発生させる。
   - 両 case とも `registered worktree path cannot be resolved` の `_FoldGateFailure` を要求する。

3. **不変条件3 — 本当に登録ゼロなら赤**

   `test_registered_worktree_paths_distinguishes_all_prunable_from_no_records`

   - helper が本物の Git から採取した prunable record だけを `_git` の stdout として返す場合、結果が `()` になることを確認する。
   - 次に `worktree ` 行を1本も含まない stdout を与え、`registered worktree list is empty` を要求する。
   - これにより、最終判定を `if not paths:` のままにする実装は前半で必ず赤になる。全登録 prunable と登録 record ゼロを同じ空リストとして扱えない。

4. **不変条件4 — 受理拡大は prunable marker のある record だけ**

   `test_registered_worktree_paths_exempts_only_prunable_record`

   - 本物の full porcelain 出力では、削除済み scratch path が返り値から除外され、同じ一覧の実在 main/wave は従来どおり返ることを確認する。
   - 採取した同一 record から真の `prunable ...` 行だけを除き、代わりに `branch refs/heads/prunable-not-a-marker` と未知 field を加える。
   - この入力では missing path の resolve が `_FoldGateFailure` になることを要求する。
   - main/wave の HEAD・status bytes の前後一致も確認する。
   - tracked/index/submodule dirt、incoming untracked、ff-only、provenance の既存期待値は変更せず、下記の焦点走に含める。

5. **不変条件5 — land は prune しない**

   `test_registered_worktree_paths_does_not_prune_registry`

   - helper が返した `.git/worktrees/<id>` admin path が呼出し前に存在することを確認。
   - `LAND._git` を実呼出しへ委譲する spy にし、`_registered_worktree_paths` を実行。
   - 呼出しが `("worktree", "list", "--porcelain")` の1回だけであること、admin path が呼出し後も存在すること、再取得した実 porcelain に同じ prunable record が残ることを要求する。
   - `prune` の追加、暗黙 cleanup、登録 admin の削除のいずれでも赤になる。

## 既存テストへの波及

丸ごと monkeypatch している2箇所は返値 contract が `tuple[Path, ...]` のままなので、静的には変更不要。

- [`test_fold_gate_missing_junit_reports_bounded_escaped_child_output:9307`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9307)  
  [`:9329`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9329) の `lambda _repo: (ROOT,)` はそのまま使える。
- [`test_fold_gate_real_argv_environment_create_junit_in_gitless_tree:9354`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9354)  
  [`:9380`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9380) も同様に変更不要。
- [`test_fold_gate_exports_full_tree_applies_raw_bytes_and_runs_one_pytest:9213`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9213) は monkeypatch せず本物の main/wave 登録を読む。どちらも実在・非 prunable なので、期待値は変わらない。

既存テストの期待値を変える理由はない。変更が必要になった場合は scope 逸脱または返値 contract の破壊を示すため、その時点で止める。

## 焦点走 nodeid

実装後、親が次を実走する。

```text
orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_preserves_existing_overlap_rejection
orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_fail_closed_for_nonprunable_decode_and_resolution_errors
orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_distinguishes_all_prunable_from_no_records
orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_exempts_only_prunable_record
orchestrator/tests/test_dev_wave_land.py::test_registered_worktree_paths_does_not_prune_registry
orchestrator/tests/test_dev_wave_land.py::test_fold_gate_exports_full_tree_applies_raw_bytes_and_runs_one_pytest
orchestrator/tests/test_dev_wave_land.py::test_fold_gate_missing_junit_reports_bounded_escaped_child_output
orchestrator/tests/test_dev_wave_land.py::test_fold_gate_real_argv_environment_create_junit_in_gitless_tree
orchestrator/tests/test_dev_wave_land.py::test_fold_gate_tmp_isolation_preserves_main_and_wave_status_bytes
orchestrator/tests/test_dev_wave_land.py::test_colliding_untracked_rejected_without_main_or_foreign_artifact_change
orchestrator/tests/test_dev_wave_land.py::test_tracked_and_staged_main_dirt_are_rejected
orchestrator/tests/test_dev_wave_land.py::test_git_operation_surface_is_read_only_except_sha_ff_merge
orchestrator/tests/test_dev_wave_land.py::test_provenance_gate_rejects_tip_nonzero_before_ff
orchestrator/tests/test_dev_wave_land.py::test_conflicting_forward_merge_is_rejected_by_replay_rc_gate
```

parameterized test は関数 nodeid を指定して全 case を走らせる。

## 変異事前登録の候補

行番号は現行 [`tools/dev_wave_land.py:3449-3471`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449) をアンカーとする。

1. record 分割を行分割へ退行させる。

   ```python
   for raw_record in raw.splitlines():
   ```

   実 Git の `worktree` 行と `prunable` 行が再び分離され、条件3・4のテストが KILL。

2. prunable 認識を無効化する。

   ```python
   is_prunable = False
   ```

   本物の削除済み worktree を resolve して失敗し、条件3・4が KILL。

3. prunable record を登録数に数えない。

   ```python
   saw_worktree_record = not is_prunable
   ```

   全登録 prunable を「登録ゼロ」と誤認し、条件3が KILL。

4. 最終空判定を解決済み path 数へ戻す。

   ```python
   if not paths:
   ```

   全登録 prunable の期待 `()` と衝突し、条件3が KILL。

5. `UnicodeError` の fail-closed を外す。

   ```python
   except OSError as exc:
   ```

   decode case が `_FoldGateFailure` にならず、条件2が KILL。

6. strict resolve を弱める。

   ```python
   .resolve(strict=False)
   ```

   非 prunable missing path が通り、条件2の resolve caseおよび条件4の marker 除去 caseが KILL。

7. 現行 [`:3817`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3817) の重なり拒否を無効化する。

   ```python
   if False and any(
       _paths_overlap_absolute(tree, path) for path in registered
   ):
   ```

   条件1の exact-message テストが KILL。

8. 一覧取得前に prune を追加する。

   ```python
   _require_git(
       _git(repository.wave, "worktree", "prune", "--expire", "now"),
       "fold gate registered worktree prune",
       RC_FOLD_GATE,
   )
   ```

   Git 呼出し列と admin path 永続性の双方で条件5が KILL。

## 裁定パッケージ候補 (scope 外の所見)

主目的の実装に追加裁定は不要。

将来別 wave で裁定候補になり得るのは、`locked` かつ path 不在で Git が `prunable` を出さない登録を除外対象へ広げるかどうかだけである。今回それを path 不在一般へ拡張すると不変条件2を破るため、現状は fail-closed のままとする。

job 専用 clone、`/scr` allowlist、land 側 prune、他 tool の同型箇所、docs 新節はすべて本プランから除外する。