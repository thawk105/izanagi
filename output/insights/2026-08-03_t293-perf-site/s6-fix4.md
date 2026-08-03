修正を完了しました。変更は `.pbs` 1 ファイルだけです。

## 総括

- 変更箇所: [t293_perf_site_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:63)
  - `python3 python3.10 python3.11 python3.12` の順に探索
  - `command -v` で解決
  - `-I -S -B -c` で Python 3.10 以上を実測
  - `realpath -e` で絶対パスを確定
  - 選択不能時は probe を起動せず `exit 2`
  - 選択結果を `noclobber` により `interpreter` へ create-only で記録
  - [probe 起動箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:84) は `"$PY" -I -B` に置換

- SHA-256:
  - `.pbs`: `7143052852f69833ea6b6a839b59fe897676eed242372fd1c759137c3a3e9b4d`
  - `.py`: `9a992293abe1497b6159e67e67bf9ed7a6f43e638bd8d65b6ee67671ac90b030`
  - `.py` は指定値から不変です。

- `git status --short`:

```text
 M tools/pegasus/probes/t293_perf_site_probe.pbs
?? output/env/pegasus/t293-perf-site/
?? t293_perf_site_probe.pbs.e881946
?? t293_perf_site_probe.pbs.o881946
```

未追跡物は作業開始前から存在しており、変更していません。

- 検査:
  - `bash -n tools/pegasus/probes/t293_perf_site_probe.pbs`: 成功（rc=0）
  - `git diff --check -- tools/pegasus/probes/t293_perf_site_probe.pbs`: 成功（rc=0）
  - ログインノード上で probe は実行していません。