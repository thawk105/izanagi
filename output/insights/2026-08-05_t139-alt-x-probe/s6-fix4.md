修正は指定 2 ファイルの同型バグ 2 件だけです。

修正箇所:

- [tools/pegasus/probes/t139_positive_control_probe.pbs:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:107) — `extract_blob` の `tmp` 代入を分離。
- [tools/pegasus/probes/t139_positive_control_probe.sh:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:329) — `limited_check` の `snapshot` 代入にも同型があったため分離。

`local` / `declare` / `readonly` / `export` を両ファイル全体で再走査し、修正後の同一文内依存は 0 件です。代入前参照・条件分岐後の未定義参照も静的に確認し、追加修正対象は 0 件でした。

最小再現:

```text
old rc=127 output=environment: line 3: destination: unbound variable
new rc=0 output=content=preregistration.md
repro cleanup: PASS (/tmp/t139-local-repro.RqTbQr removed)
```

検査結果:

- `bash -n` PBS: PASS
- `bash -n` driver: PASS
- driver self-check: rc=0
  - verdict: 正例 accepted / 負例 rejected
  - row structure: 正例 accepted / 負例 rejected
  - liveness: 正例 accepted / 負例 rejected
  - compile JSON: 正例 accepted
  - ycsb missing / duplicate: 負例 rejected
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: PASS

差分は宣言と派生値代入を分けた計 4 行だけです。検査、受理条件、state、cap、env 名、数値リテラルは変更していません。commit、qsub、qstat は実施していません。

最終 status は指定 2 ファイルのみ modified。request 892032 の既存未追跡成果物 3 件には触れていません。

## 総括

実走を止めた `set -u` バグと、driver 内に残っていた同型 1 件を最小差分で修正しました。既存の正負 self-check を維持したまま、必須検査はすべて成功しています。