## 所見ごとの対応

- **R2: closed。** `printf` の引数を 5 個に修正しました。一時ディレクトリで表示行だけを実行し、1 行に `rc=7`、`seconds=42`、正しい report・stderr のパスが出ることを確認しました。script の終了 rc の扱いは変更していません。
- **R3: closed（実装確認）。** `--fix-parent-oid` を固定 OID と照合します。照合はログインノード拒否より前の 79–80 行にあり、不一致は既存の `except Exception` により結果 JSON の `errors` に記録され、rc=1 になります。本走は未実走です。

## 変更内容

[run_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/scripts/run_judge_v3.sh)
SHA-256: `2a7c9087cd8efc71074eab7d568ed8dcaef6c8d79a89bac757ecdb63a9f9a23e`

```diff
--- /tmp/silo-run-judge-v3-before.sh	2026-09-30 12:36:42.834221854 +0900
+++ output/runs/silo-line/scripts/run_judge_v3.sh	2026-09-30 12:36:49.000000000 +0900
@@ -60,6 +60,6 @@
   > "$out_dir/b-gcc$version.report.json" 2> "$out_dir/b-gcc$version.stderr" || rc=$?
 printf '%s\n' "$rc" > "$out_dir/b-gcc$version.rc"
 printf '%s\n' "$(( $(date +%s) - started ))" > "$out_dir/b-gcc$version.seconds"
-printf 'b-gcc%s rc=%s seconds=%s report=%s stderr=%s\n' "$version" "$rc" \
+printf 'b-gcc%s rc=%s seconds=%s report=%s stderr=%s\n' "$version" \
   "$(cat "$out_dir/b-gcc$version.rc")" "$(cat "$out_dir/b-gcc$version.seconds")" \
   "$out_dir/b-gcc$version.report.json" "$out_dir/b-gcc$version.stderr"
```

[launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/scripts/launch_gate_liveness_v3.py)
SHA-256: `ceec71a417bd7ef3c3490072faccd703f4ee0e1127c0119859902f7160b015b2`

```diff
--- /tmp/silo-launch-gate-liveness-v3-before.py	2026-09-30 12:36:42.842221229 +0900
+++ output/runs/silo-line/scripts/launch_gate_liveness_v3.py	2026-09-30 12:36:49.000000000 +0900
@@ -16,6 +16,7 @@
 import launch_gate_liveness as u

 F = "25898d00b9a6bbf09329ff8e8318c77d4f08b46e"
+FIX_PARENT = "7e5fa528037805dfc0459c742e4a21d6114c9799"


 def git(root, *args):
@@ -75,6 +76,8 @@
     try:
         if sys.version_info < (3, 10):
             raise RuntimeError("Python >=3.10 required")
+        if a.fix_parent_oid != FIX_PARENT:
+            raise RuntimeError("fix parent OID mismatch")
         if re.fullmatch(r"pegasus0\d+(?:\..*)?", result["host"]):
             raise RuntimeError("login node refused")
         if not a.bundle.is_file() or not a.checker.is_file() or not a.third_party_cache.is_dir():
```

## 実走した command と rc

| command | rc・結果 |
|---|---|
| `bash -n output/runs/silo-line/scripts/run_judge_v3.sh` | 0 |
| `PYTHONPYCACHEPREFIX=/tmp/silo-fix-pycache python3 -m py_compile output/runs/silo-line/scripts/launch_gate_liveness_v3.py` | 0 |
| `tail -n 3` で表示行を抽出し、一時 `.rc=7`・`.seconds=42` を使って `source`、期待する 1 行と比較 | 0。一致 |
| 両ファイルの変更前後の `diff -u` | 各 1。上記の差分あり |
| 両ファイルの `sha256sum` | 0 |

最初の再現コマンドは一時領域の削除指定が自動審査で拒否され、実行されませんでした。削除指定を外して再実行した結果が上記です。

## 未実走・残る懸念

R3 の起動器と計算ノードでの本走は未実走です。固定 OID の照合位置とエラー経路は静的に確認しました。所有外の repo ファイルは編集せず、commit もしていません。自己確認用ファイルは `/tmp` にあります。

## 総括

R2・R3 を指定の 2 ファイル内で修正し、指定された構文検査と R2 の再現を通しました。R1 の裁定どおり、検査器実行後の script 終了 rc は変更していません。