## 総括

- 変更箇所: `tools/pegasus/probes/t293_perf_site_probe.py:835`
  - 候補列: `[str(Path(sys.executable).resolve())]`（838 行目）
  - 理由の日本語 `note` を 839 行目に追加
- probe.py SHA-256: `9a992293abe1497b6159e67e67bf9ed7a6f43e638bd8d65b6ee67671ac90b030`
- `git status --short`:

```text
?? tools/pegasus/probes/t293_perf_site_probe.pbs
?? tools/pegasus/probes/t293_perf_site_probe.py
```

既存の上記 2 ファイルのうち、編集したのは `probe.py` のみです。`.pbs` の SHA-256 は作業前後とも `afa4526aa7c7df0e87c21b1bc7a8bb0b8381e03c71a2a5eee71c1b7205bb4021` でした。

- 検査: `python3 -m py_compile tools/pegasus/probes/t293_perf_site_probe.py` → rc `0`
- probe 本体はログインノードで実行していません。
- 負 control、binding、必須 field 検査、per-candidate 測定、`.pbs` は変更していません。