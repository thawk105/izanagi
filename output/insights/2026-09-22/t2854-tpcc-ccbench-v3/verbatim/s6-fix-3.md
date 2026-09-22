`sources()` だけを修正しました。同関数の外側は変更前と byte 一致を確認済みです。

- [run_probe.py:222](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-ccb-b/output/runs/t2854-ccbench-v3/probe/run_probe.py:222)：scratch の `objects.git/info/attributes` に指定の2行を設定。
- 同 file:245：tree の regular file・gitlink・symlink を分類。symlink は記録して拒否。
- 同 file:282：file 集合と全 blob ID を照合。件数・除外 gitlink・不一致を `source_evidence` に記録。blob 不一致時は attributes と診断を保存して停止し、修復しません。

自己確認はすべて rc=0 でした。

- `python3 -B output/runs/t2854-ccbench-v3/probe/v3check.py --selftest`：**193/193 passed; failures=0**。試験・期待値の変更なし。
- `run_probe.py --help`、構文確認：合格。
- pegasus02 で指定 bundle を使い、`sources()` を build なしで実走：

| source | 集合・blob 照合 | 除外 gitlink | symlink |
|---|---:|---|---:|
| pin | 404/404 一致 | `third_party/shirakami` | 0 |
| C2 | 404/404 一致 | `third_party/shirakami` | 0 |

両 source の `cc/oze/CMakeLists.txt` を確認しました。独立した `git hash-object --no-filters` による全件照合も一致。指定の `tmp-source-check/` は削除済みです。

## 総括

- archive の欠落 blocker を修正し、全808 file の内容一致を実測しました。
- tracked file・index・HEAD・他関数・spec は変更していません。
- build・計算 job 投入・C0〜C6 全走、および新しい拒否経路への異常注入試験は未実走です。