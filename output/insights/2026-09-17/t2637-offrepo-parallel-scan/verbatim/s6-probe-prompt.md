単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/tools/audit_dangling_commits.py` — 現行の監査 tool (並列化済み、未 commit の作業ツリー = commit 78f8af060 と同一 bytes)。`_OffrepoCounts` (872〜880 付近)、`_process_offrepo_iteration` (910〜975)、`_scan_offrepo_directory` (977〜1005)、`_run_offrepo_queue` (1007〜1092)、`audit_with_offrepo` (1530〜) を読む。`grep -n "^def \|^class "` で位置を出す
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s6-probe-brief.md` — 親の依頼の背景 (実根で並列走だけに「確認不能」が出る件数の帰属)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl` とする。**大きい file を全文 `cat` しないこと。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。**repo 内に probe の手本は無い。**

## この段の仕事

使い捨ての診断 probe `tools/t2637_onerror_probe.py` (100〜150 行、stdlib のみ) を 1 file だけ書く。親が実行後に repo 外へ退避し、repo には残さない (commit しない)。目的: 監査の repo 外走査で `failures` に数えられた OSError の **path と errno と発生箇所** を記録し、探索根の churn (他 wave の worktree 生成・削除) に帰属できるかを判定する材料を得る。

仕様:

1. `importlib` で `tools/audit_dangling_commits.py` を module として読み込む (test file と同じ `importlib.util.spec_from_file_location` 方式。`sys.path` に頼らない)。
2. 監査の本番経路 `audit_with_offrepo(repo, offrepo_roots=(root,), progress=...)` を **そのまま** 呼ぶ (走査規則を複製しない)。引数: `--repo <fixture repo の絶対 path>`、`--offrepo-root <探索根の絶対 path>`、`--out <記録 JSON の絶対 path>`、`--workers <正整数>` (env `IZANAGI_AUDIT_SCAN_WORKERS` を probe 内で `os.environ` に設定する)。
3. 呼ぶ前に module の 3 箇所へ **記録だけを足す wrapper** を monkeypatch する (挙動・計数・戻り値は変えない):
   - `_OffrepoCounts.record_error(self, error)`: 元の method を呼んだ後に `{"site": "walk-onerror", "path": getattr(error, "filename", None), "errno": error.errno, "strerror": error.strerror, "thread": threading.get_ident(), "t": time.monotonic()}` を lock 付き list へ append。
   - `_process_offrepo_iteration` 内の候補 `lstat` 失敗 (`except OSError: counts.failures += 1`) は関数内部なので直接 wrap できない。代わりに `pathlib.Path.lstat` を wrap し、OSError が出た呼び出しだけ `{"site": "candidate-lstat", "path": str(self), "errno": ..., "strerror": ...}` を記録して例外はそのまま再送出する (成功時は何も記録しない)。
   - root の `lstat` / permission 検査の失敗は `walk-onerror` と `candidate-lstat` の外なので、走査前に root を `os.lstat` して記録に `root_stat_ok` を書く。
4. 走査後、記録を JSON で `--out` へ書く: `{"repo": ..., "root": ..., "workers": N, "started": ISO 時刻, "elapsed_seconds": ..., "scan_failures_reported": report.scan_failures, "recorded_errors": [...], "recorded_count": len(...), "errno_histogram": {"ENOENT": n, ...}, "paths_still_exist_after": {path: bool} (記録した各 path について走査完了後に `os.path.lexists` を取る), "report": {"findings": len(report.findings), "suppressions": len(report.suppressions), "unreferenced_copies": len(report.unreferenced_copies), "external_files": ...}}`。`recorded_count` と `scan_failures_reported` が一致しなければ `"mismatch": true` を書く (数えられた失敗のうち記録できなかったものがあれば、それも分かるように)。
5. `--selftest` を付けると、`tempfile.mkdtemp()` に小さな tree (読めない dir 1 個 `chmod 0`、走査中に消える dir は不要) を作り、workers=4 で probe を通し、`recorded_count == scan_failures_reported == 1` かつ errno が EACCES であることを assert して rc=0、違えば rc=1。root 実行なら selftest を skip して rc=0 と出力する。
6. 進捗行は stderr へ (監査の `progress` callback を stderr に流す)。stdout には最後に 1 行 `PROBE ok recorded=<n> reported=<m>` を出す。
7. 実根 `/work/1/SFC/tanab/dev-wave-jobs` を probe 作成中に走査しない。`--selftest` は走らせてよい (tmp のみ)。

**禁止:** 監査 tool の編集、他の file の作成・編集、`git add` / `git commit`、docs 編集。

## 完了報告に必ず含める

- probe の path と行数、`--selftest` の実走結果 (rc と出力行)。
- wrapper が挙動を変えないことの根拠 (元 method を呼ぶ、例外を再送出、計数を触らない)。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。

節の順:

## probe の仕様と実走
## 挙動不変の根拠
## 総括
