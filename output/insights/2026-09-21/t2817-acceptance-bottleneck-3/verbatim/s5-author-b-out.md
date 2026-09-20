## 実装した内容

所有する次の 3 ファイルを作成しました。**実装済み・計算ノードでは未実走**です。

- [t2817_replica_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b/tools/t2817_replica_runner.py): hostname 防壁、環境初期化、clean 検査、smoke → A 1 走、session 記録・成果物コピー、2800 秒 alarm、process group 回収。
- [t2817_replica_plugin.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b/tools/t2817_replica_plugin.py): collection 後の遅延 wrapper、観測 key、成分・flock・consumer・test 区間の JSONL 記録。
- [t2817_replica_analyze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b/tools/t2817_replica_analyze.py): 排他的成分集計、JUnit/report 照合、全 worker の item timeline、L／最大占有 worker の成分 timeline、欠測出力。

KEYS・TIP 固定、L/P 条件、builder_slot、block 進行はありません。

## wrap 対象の対応表 (T-2786 前提 vs 現行)

行番号は現行 `orchestrator/tests/test_s8b_oracle_driver.py`。対象を import・実行せず静的に確認しました。

| T-2786 の対象・成分 | 現行の signature／呼出形・位置 | 対応 |
|---|---|---|
| `_T080SharedBases.get` | `get(self, key)` L940、helper から L1009 | 引数 key を記録。実 session と検査用 instance を区別 |
| builder | `_build_t080_stub_free_e2e_repo(tmp_path, *, r_trailer="AI-Agent: none", extra_r_path=False, issue_receipt=True, distinct_basis_blob=False, active_v2_base=False)` L1433。呼出 L955・1019 | 追加された `active_v2_base` を含め観測 |
| helper | `_t080_stub_free_e2e_repo`、builder と同じ引数形 L991 | helper 区間・key を記録 |
| copy | `_copy_git_visible_output(source_root, destination)` L843、呼出 L1454 | 同じ builder 直下区間 |
| copy | `_copy_t080_migration_basis_file(root, relative, basis)` L577、呼出 L1524 | 同上 |
| copy／runtime | `_copy_t080_basis_file(root, relative)` L570、呼出 L1458・1526・1559 | `t080-current-runtime` 配置を runtime に分離 |
| copy／base_copy | `shutil.copytree`、builder L1449、helper L1028 | 呼出元 code object で区別。再帰分を二重加算しない |
| git | `_run_git(root, *args)` L396、builder L1442–1446・1535–1544 | builder 直下だけ計測 |
| history | `migration.inspect_receipt_history(root=root, check_worktree=True)` L1545 | 同じ呼出位置 |
| issue | `subprocess.run([sys.executable, "-I", "-B", "-c", …], …)` L1708 | 発行子の起動から終了まで |
| verify | `migration.verify_receipt(root=root[, launch_validated=token])` L1740・1745 ほか | test 実行中の実呼出を記録。発行子内部 L1692 は issue に含む |
| key_wait | `fcntl.flock(lock, LOCK_EX)` L948 | 現行の非 v2＝4 要素 digest、v2＝5 要素 digest に対応 |

改名・消失した対象はありません。先例の固定 4 要素 key は撤去しました。legacy 4 要素の直接呼出は、その観測値を保持します。

## 実走した検査 (command と出力の逐語)

以下の範囲だけ成功を確認しました。pytest collection・xdist・`run_tests.py` 本走は起動していません。

**構文検査：rc 0、出力なし。** py_compile の生成物は `/tmp` に限定しました。

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/t2817b-compile-cache python3.10 -m py_compile tools/t2817_replica_runner.py tools/t2817_replica_plugin.py tools/t2817_replica_analyze.py
```

**plugin import：rc 0。**

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools python3.10 -c 'import t2817_replica_plugin; print("plugin import OK")'
plugin import OK
```

**runner ヘルプ：rc 0。**

```text
PYTHONDONTWRITEBYTECODE=1 python3.10 tools/t2817_replica_runner.py --help
usage: t2817_replica_runner.py [-h] --repo-root REPO_ROOT --probe-dir
                               PROBE_DIR --out-root OUT_ROOT --job-tag JOB_TAG
                               {run}

Compute-only smoke then one A replica; Python 3.10 standard library.

positional arguments:
  {run}

options:
  -h, --help            show this help message and exit
  --repo-root REPO_ROOT
  --probe-dir PROBE_DIR
  --out-root OUT_ROOT
  --job-tag JOB_TAG
```

**hostname 防壁：pegasus02 で期待どおり rc 3。**

```text
PYTHONDONTWRITEBYTECODE=1 python3.10 tools/t2817_replica_runner.py run --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b --probe-dir /tmp/t2817b-probe --out-root /tmp/t2817b-hostname-guard --job-tag hostname-guard
compute hostname prerequisite failed (requires bnode)
```

**解析器の合成正例・負例：検査 script 全体 rc 0。**

```text
PYTHONDONTWRITEBYTECODE=1 python3.10 /tmp/t2817b-synthetic-check.py tools/t2817_replica_analyze.py
COMMAND: python3.10 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b/tools/t2817_replica_analyze.py --run-dir /tmp/t2817b-synthetic/good/A --markdown /tmp/t2817b-synthetic/positive.md --json /tmp/t2817b-synthetic/positive.json
{"rc": 0, "key_count": 2, "missing": [], "fatal_error": null}
exit=0
POSITIVE: 2 keys; exclusive components, waiter, consumers, W/pre/O_max/L/P_L/F/post and timelines OK
COMMAND: python3.10 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2817-probe-b/tools/t2817_replica_analyze.py --run-dir /tmp/t2817b-synthetic/reversed/A --markdown /tmp/t2817b-synthetic/negative.md --json /tmp/t2817b-synthetic/negative.json
{"rc": 1, "key_count": null, "missing": null, "fatal_error": "reversed span: end < begin"}
exit=1
NEGATIVE: end < begin rejected OK
```

正例は発行あり／なしの 2 key、成分排他化、待ち手、verify・copytree、`W=30, pre=3, O_max=18, L=14, P_L=0, F=12, post=5` と rank 付き timeline を assert しています。

## 設計上の判断と限界

- `IZANAGI_ACCEPTANCE_SHARDS` は unset。`run_tests.py` L270 以降では外側分割の対象が login に限定され、compute の未指定値は 1 です。担当集合は指定された plugin spec の shard-0/3 で選択します。
- runner 自身は標準 library のみを import します。契約に明記された `acceptance_shards.create_session(repo, 3)` は別 Python 子から呼び、process group 管理下に置きました。
- smoke の fork 子でも PID ごとの span を保存します。rc 0・成功 build span ≥1・record-error なしを満たさなければ A を投入しません。
- wrapper は元の引数を一度だけ渡し、返り値をそのまま返し、元の例外を記録して再送出します。
- 「その他」は history＋runtime＋residual。JSON には各成分も残します。issue は子内部の verify を含みます。
- test 区間は logstart/logfinish 間です。外側 protocol の real-repo lock 待ちは含みません。占有は report の duration 和で、経過時間とは区別しています。
- 合成検査は集計処理の確認です。実機 wrapper 配線の妥当性は未確認で、job 内 smoke が次の確認点です。中央値・改善効果は主張しません。

## 所有外への波及

**所有外ファイルの変更は無し。** docs・既存 tools・conftest・共有 fixture・consumer test は編集していません。`git add`／`git commit` も実行していません。

実行時には共有 `shutil.copytree`・`subprocess.run`・`fcntl.flock`・migration 関数にも wrapper が掛かります。対象外呼出はそのまま委譲します。共有 fixture の smoke instance は別分類で記録します。

受理集合・deselect・skip・hold・verifier 判定・並び順を変更する処理はありません。

最終 `git status --porcelain`：

```text
?? tools/t2817_replica_analyze.py
?? tools/t2817_replica_plugin.py
?? tools/t2817_replica_runner.py
```

## 総括

3 ファイルの実装と許可された検査を完了しました。差分は worktree に残しています。**計算ノードの smoke／A は未実走**です。