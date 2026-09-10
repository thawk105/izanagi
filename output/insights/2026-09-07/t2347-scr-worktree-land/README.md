# [T-2347] 計算ノード job の scratch worktree が land を塞ぐ問題を直す (F851)

- wave branch: `worktree-dev-wave-t2347-scr-worktree-land`
- 実装 commit: `28cd7bf931c3cf3639dfcccfd1a4f14bbbd39f56`
- 変異本走の `repo_head`: `28cd7bf931c3cf3639dfcccfd1a4f14bbbd39f56`
- 対象: `tools/dev_wave_land.py` の `_registered_worktree_paths`、`orchestrator/tests/test_dev_wave_land.py`

## 何が起きていたか

計算ノード job (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) は
`git -C "$REPO_BASE" worktree add --detach "$TMPDIR/job-repo"` で、node-local scratch を**共有 repo の
worktree 登録簿へ**登録する。この path は login node から見えない。

`tools/dev_wave_land.py` の `_registered_worktree_paths` は、fold gate の隔離 dir が登録 worktree と
重ならないことを確かめるために全登録を `Path.resolve(strict=True)` していた。login node では
`/scr` が存在しないので `FileNotFoundError` になり、それが一律 `_FoldGateFailure` へ落ちて
`rc=31 status=fold-gate-failed`、`retryable_same_request=false` になる。job は最大 2 時間走るので、
その間**この repo の全 wave の land が塞がれ、緑の受入が 1 本ずつ捨てられる** (F851)。

## 直し方 (段 4 裁定。正本は `verbatim/s4-ruling.md`)

`resolve(strict=True)` が **`FileNotFoundError`** を上げた登録だけ、**捨てずに**解決しない絶対 path
として返り値へ残す。それ以外の `OSError` と `UnicodeError` は従来どおり `_FoldGateFailure`。
行走査・空判定・重なり判定・`_execute_fold_gate` は変えず、`git worktree prune` も足さない。

```python
        try:
            path = Path(os.fsdecode(record.removeprefix(b"worktree ")))
            try:
                path = path.resolve(strict=True)
            except FileNotFoundError:
                path = path.absolute()
            paths.append(path)
        except (OSError, UnicodeError) as exc:
            raise _FoldGateFailure(
                f"registered worktree path cannot be resolved: {exc}"
            ) from exc
```

**登録を 1 件も捨てない**ことが要点である。捨てる設計は、その登録を fold gate の非接触検査から
外してしまい、受理集合を意図より広げる。

## 段 2 プランを却下した根拠 — 親の実測 3 点

段 2 のプラン (`verbatim/s2-plan.md`) は `git worktree list --porcelain` の `prunable` 行を読んで
record を除外する形だった。段 3 の敵対相談 (`verbatim/s3-consult-lensA.md` / `lensB.md`) が穴を挙げ、
親が使い捨て repo で実測して却下した。逐語は `git-worktree-porcelain-probe.txt`。

1. **`git worktree list --porcelain -z` はこの機体の git 2.34.1 に無い** (`rc=129`,
   `error: unknown switch 'z'`)。record 境界を NUL で一意にする逃げ道が無い。
2. **`prunable` は「path 不在」を意味しない。** worktree の directory は実在し `.git` file だけ消した
   登録も `prunable gitdir file points to non-existent location` と報告された。marker で除外すると、
   実在する worktree を非接触検査から外す。
3. **path に改行を含む実在 worktree は marker を偽装できる。** path
   `<D>/live\nprunable fake-marker` の実在 worktree は、porcelain 上で
   `worktree <D>/live` / `prunable fake-marker` / `HEAD <sha>` / `detached` という record になる。
   行単位でも record 単位でも、実在登録と prunable 登録を区別できない。

`FileNotFoundError` で分岐する形にすると、この 3 点に加えて次も同時に閉じる。

- **TOCTOU** (段 3 レンズ A 所見 3): 登録一覧の取得は隔離 dir の作成より前なので、
  「観測時に不在なら後で作る隔離 dir と重ならない」は成り立たない。不在 path も比較対象に残すため、
  隔離 dir が不在登録の path と一致すれば従来どおり拒否する。
- **locked かつ path 不在** (同レンズ A 所見 4): git は locked な登録を prunable と報告しないことが
  ある。marker 方式はここを取り逃すが、`FileNotFoundError` 方式は同じ経路で通る。

## テスト (T1〜T10、すべて `orchestrator/tests/test_dev_wave_land.py`)

実 repo を fixture 内に作り、本物の `git worktree add` と本物の porcelain を通す。

| ID | nodeid | 固定するもの |
|---|---|---|
| T1 | `test_fold_gate_rejects_overlap_with_third_live_registered_worktree` | 第三の**実在** linked worktree との重なりは従来どおり拒否 |
| T2 | `test_registered_worktree_paths_keep_absent_registration` | path 不在の登録で赤にならず、かつ**返り値に残る** |
| T3 | `test_registered_worktree_paths_keep_live_directory_with_missing_dotgit` | git が prunable と呼ぶが directory は実在する登録は解決済みで返る |
| T4 | `test_registered_worktree_paths_keep_live_newline_marker_registration` | 改行 path の実在登録が marker 偽装で落ちない |
| T5 | `test_registered_worktree_paths_fail_closed_for_other_resolution_errors[permission\|unicode]` | `FileNotFoundError` 以外は fail-closed のまま |
| T6 | `test_registered_worktree_paths_reject_list_without_worktree_lines[empty\|marker-only]` | `worktree ` 行ゼロは `registered worktree list is empty` |
| T7 | `test_registered_worktree_paths_do_not_prune_absent_registration` | land は registry を prune しない (事後状態で確認) |
| T8 | `test_fold_gate_rejects_recreated_absent_registered_isolation_path` | 不在登録の path が隔離 dir と一致すれば拒否 |
| T9 | `test_land_succeeds_with_absent_registered_worktree` | end-to-end `land()` が `(RC_OK, "landed")` |
| T10 | `test_land_with_absent_registration_still_rejects_live_wave_dirt` | 実在 worktree の dirt は今までどおり `(RC_DIRT, "rejected")` |

## 実測

| 走行 | 結果 |
|---|---|
| 焦点走 1 (`test_dev_wave_land.py` 全体) | 311 passed / 1 skipped、`child_rc=0`、bnode005、980096.nqsv |
| 焦点走 2 (consumer 9 file) | 1390 passed / 3 skipped、980098.nqsv |
| 全史 provenance 監査 | rc=0、8367 件、新規違反なし |
| 変異 probe 走 | baseline PASSED、8/8 が node を出す (SURVIVED 登録に対し MISMATCH) |
| **変異本走** | **baseline PASSED、8/8 KILLED、期待 node 完全一致 (`matching=8`)、SURVIVED 0** |

consumer 9 file は変更した production module 名で `orchestrator/tests/` を引いた結果である
(`test_dev_wave_wait` / `test_run_tests_shards` / `test_flaky_test_holds_contract` / `test_check_docs` /
`test_t793_approval_d291` / `test_t139_approval_payload` / `test_acceptance_schedule_order` /
`test_pytest_collection_config` / `test_fold_gate_nodes_contract`)。

## 変異 matrix (事前登録 → 本走)

spec は `mutation-spec-final.json`、台帳は `mutation-ledger-final.json`。spec の生成器は job 側の probe として
走らせ (repo へは入れない)、各変異の `old` の出現がちょうど 1 件であることを生成時に検査した。

| ID | 変異 | 結果 | 殺したテスト |
|---|---|---|---|
| M1 | `except FileNotFoundError` を `except OSError` へ広げる | KILLED | T5 permission |
| M2 | 不在登録を `continue` で捨てる | KILLED | T2, T4, T7, T8 |
| M3 | `resolve(strict=False)` にする | KILLED | T5 permission |
| M4 | fail-closed から `UnicodeError` を外す | KILLED | T5 unicode |
| M5 | 段 2 プランの `prunable` marker 除外へ戻す | KILLED | T2, T3, T4, T7, T8 |
| M6 | 空一覧の関門を削除する | KILLED | T6 empty, T6 marker-only |
| M7 | 隔離 dir の重なり拒否を無効化する | KILLED | T1, T8 |
| M8 | 一覧取得の前に `worktree prune --expire now` を足す | KILLED | T2, T3, T7, T8, **T9** |

8 本とも、殺したのは本 wave の新規テストだけである (段 3・段 6 の両レビューが、
先に赤を出す既存テストが無いことを別々に確認した)。M8 は end-to-end の T9 でも殺される。

## 敵対レビューの所見と裁定

段 6 のレビュー 2 本 (`verbatim/s6-review-A.md` / `s6-review-B.md`) は**どちらも must-fix ゼロ**。
nit は次の 3 件で、いずれも「放置しても land 判定の値は変わらない」と自認しているため
`DW-G05` により backlog とした。

- T5 は `NotADirectoryError` / `OSError(ELOOP)` / `RuntimeError` を直接固定していない
  (いずれも現行は `OSError` 捕捉または `_run_fold_gate` の包括捕捉で rc=31 のまま)。
- T9 は不在登録を 1 本しか作らず、F851 逐語の「同時に 2 本」を再現していない。
- 追加テストは parametrization 展開で 12 case、`git worktree add` を延べ 20 回行う。

## scope 外として実装しなかったもの

- **案 (b) (job 専用 clone)**: F851 は「(a) または (b)」を許しており (a) を採った。共有 registry 依存
  そのものを切る価値は残る。clone のコストは本 wave で実測しておらず、採否の理由に使っていない。
- **a5 の異常終了残骸**: 同 script の cleanup は CCBench 側しか `worktree prune` せず、superproject 側の
  残骸は job が SIGKILL された場合などに残りうる (段 3 レンズ B 所見 5)。
- **他 tool の同型箇所**: `tools/mutation_worktree.py` / `tools/mutation_fanout.py` /
  `tools/check_acceptance_reds.py` も worktree 一覧を引くが、`/scr` 登録で同型に壊れるかは
  **本 wave では検査していない**。緑とも赤とも報告しない。
- **bind mount / inode alias**: `_paths_overlap_absolute` は resolved path の等号と親子関係しか見ず、
  同じ tree を指す別 mount path を重なりと判定しない。これは本差分が作った問題ではなく既存の限界である。
