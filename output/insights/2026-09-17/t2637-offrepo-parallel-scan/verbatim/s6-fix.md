## 変更一覧

変更は指定の2ファイルのみ。docs 編集、git add、commit は行っていません。

実装: [tools/audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/tools/audit_dangling_commits.py)

| 行 | 関数・変更 |
|---|---|
| 868 | `_WalkKey` / `_OffrepoKeys` 新設。代表の DFS 訪問順を保持 |
| 910 | `_process_offrepo_iteration`：共有照合規則を維持し、worker 内で最小 key の代表を選択 |
| 977 | `_scan_offrepo_subtree` を `_scan_offrepo_directory` へ置換。1 yield だけ処理して walk を閉じ、非 symlink の子 task を返す |
| 1007 | `_run_offrepo_queue` 新設。固定 N thread、queue、未完了数、計数公開、主 thread の heartbeat、例外保存と全 thread の join |
| 1094 | `_merge_offrepo_candidates`：worker 間でも最小 key の代表を選択 |
| 1117 | `_enumerate_offrepo_candidates`：root ごとに走査を完結し、OID・identity の挿入順を復元 |

テスト: [orchestrator/tests/test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/orchestrator/tests/test_audit_dangling_commits.py)

- 1316、1394、1519、1541、1572、1600：段5新設テスト6件を新設計へ更新。
- 1440：`_canonical_offrepo_candidates` 新設。挿入順を含む比較用。
- 1448：`test_parallel_offrepo_scan_handles_deep_and_wide_trees` 新設。深さ10、巨大部分木300 directory、小部分木20個で等価性・重複0・欠落0を検査。
- 1483：`test_parallel_offrepo_scan_symlink_directory_is_listed_not_entered` 新設。root 直下・部分木内部の symlink directory を検査。

## 実走結果

指定コマンドを実行しました。

```text
PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py
155 passed in 9.14s
```

**155 passed、0 failed、0 skipped、rc=0。** `git diff --check` も rc=0。

変異実走、実根での等価性・性能測定、親の統合検査は未実走です。

## 期待値と等価性

既存テストの期待値は変更していません。HEAD との AST 比較で、残存する既存テスト関数がすべて不変と確認しました。旧並列禁止テストの置換は段5適用済みのものです。

段5新設テストの内部変更は、`uses_multiple_threads`、`preserves_first_seen`、`propagates_worker_exception`、`heartbeat_runs_on_caller`、`worker_configuration`、`empty_offrepo_candidates_touch_neither_filesystem_nor_pool` の6件です。他の4件は変更していません。

1. 各 directory は1 task が最初の yield だけ処理し、再帰は queue が担当します。workers=1 は従来の全体 walk を維持します。
2. scandir 失敗は `os.walk` の `onerror` が1回計数し、yield がなければ候補処理しません。
3. symlink directory は `dirnames` に残し、再帰条件と同じ `islink` 判定で投入を除外します。directory 計数は逐次版と一致します。
4. file `(0, name)`・子 directory `(1, name)` の key 最小を代表とし、OID・identity も key 順に復元します。
5. root は sorted 順に完結させ、先の root の代表を保持します。入れ子 root の alias 2個・失敗2回も維持します。

## 変異 matrix の対象行と予想 killer

以下の **A = `tools/audit_dangling_commits.py`**。old は現在の実装の逐語引用です。**結果は予想であり、変異実走ではありません。**

| ID | 対象 file:line・old | 変異と予想 killer |
|---|---|---|
| M0 | A:1123 `"""blob を読まず basename・size・mode が一致する外部実体を列挙する。"""` | 意味不変の言い換え。SURVIVED 予想 |
| M1 | A:1091 `counts.failures += failures` | 合算を除去。`test_parallel_offrepo_scan_preserves_failure_counts` |
| M2 | A:1000 `for name in iteration[1]` | `iteration[1][:-1]` とし sorted 末尾を投入しない。`test_parallel_offrepo_scan_preserves_enumeration` |
| M3 | A:996 `root, iteration, by_basename, possible, counts, notify, keys, key_prefix` | root の filenames を空にして照合を省略。`test_parallel_offrepo_scan_preserves_enumeration` |
| M4 | A:990 `directory, topdown=True, onerror=counts.record_error, followlinks=False` | **`True` への変更だけでは等価変異となり SURVIVED 予想**。1 yield で閉じるため。追跡を起こす変異は A:1001 `if not os.path.islink(os.path.join(directory, name))` の除去で、`test_parallel_offrepo_scan_symlink_directory_is_listed_not_entered` が killer |
| M5 | A:967、1105 `if group_key not in keys or key < keys[group_key]:` | `<` を `>` にし最大 key を代表にする。`test_parallel_offrepo_scan_preserves_first_seen` |
| M6 | A:1055–1057 `except BaseException as error:` / `with lock:` / `if not errors:` | worker 例外を保存せず握りつぶして続行。`test_parallel_offrepo_scan_propagates_worker_exception` |
| M7 | A:1043–1045 `children = _scan_offrepo_directory(` / `*task, root, by_basename, found, found_keys, local, publish` / `)` | worker 内で `heartbeat.pulse(...)` を追加。`test_parallel_offrepo_scan_heartbeat_runs_on_caller` |
| M8 | A:30 `OFFREPO_SCAN_WORKERS = 16` | 16→0。`test_offrepo_scan_worker_configuration` |
| M9 | A:1124–1125 `if not candidates:` / `return {}, 0, False` | 早期 return 前に queue／thread を生成。`test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool` |

M4 は新設計で再帰を queue へ移したことによる変異定義の差です。元の変異を KILLED とは報告しません。

## 総括

directory 単位の動的 queue への修正を完了し、対象モジュール **155件 passed** を確認しました。実根の性能改善と受理条件は未判定であり、wave の closed は主張しません。
