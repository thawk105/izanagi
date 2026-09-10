## 変更した箇所 (file:line、旧値 → 新値)

- [test_s8b_oracle_manifest.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_s8b_oracle_manifest.py:64)  
  `053bbb...080e1` → `58190f...9f8e`
- [test_s8b_oracle_manifest.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_s8b_oracle_manifest.py:89)  
  materializer SHA-256: `e399e3...9b82` → `049642...316d`
- [test_ccbench_spawn_sites.py:2867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_ccbench_spawn_sites.py:2867)  
  build sink 行番号: `1215` → `1219`

## 再計算した sha256 (s1 全体、PIN_GATE_SPEC_RAW)

- s1 全体: `049642ca067d93b046df66b14ddfdda3782bb06c830f2803c71e0e60e42f316d`
- `PIN_GATE_SPEC_RAW`: `58190f7b402ea5a72d19e86e38d63ef2941e3281d1617a4a8ff986c2e4769f8e`
- `PIN_GATE_SPEC_SHA256` との一致を確認済み。
- schedule SHA-256 は `105bf4cb713f309fec174035814b7ab70ac892a70a51d62f028c31f6310c68d2` のままです。

## 実走した test と未実走

- 焦点 3 node を `tools/run_tests.py` で起動しましたが、Pegasus の `qstat -Q` preflight が失敗し `rc=16` となりました。
- `child_started=false` のため、pytest は 3 node とも未実走です。
- 実装済み・未実走です。
- `git diff --check` は成功しました。
- runner が作成した失敗 dispatch 一時成果物はすべて除去済みです。

## 総括

指定された 2 file の 3 literal だけを更新しました。段 5 差分や s1 本体、受理集合、その他の pin は変更していません。commit も行っていません。