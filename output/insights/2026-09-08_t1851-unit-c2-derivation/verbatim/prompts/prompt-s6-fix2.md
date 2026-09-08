単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1`
- **親の段 4 裁定**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 段 6 レビュー B (この所見の出所): `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s6-reviewB.md`
- 段 6 レビュー A: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s6-reviewA.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/CLAUDE.md`

# 段 6 fix 2 — floor_pair_driver の consumer 取り残しを閉じる

## 所有する file (これ 1 つだけ。他の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/test_floor_pair_driver.py
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**production file を 1 行も変更しない。** 新しい file も作らない。

## 所見 (親が現物で裏取り済み)

`orchestrator/campaign/floor_pair_driver.py` は
`measure_point(..., rep_observations=observations)` の **production consumer** である
(`:1596-1618`)。そして `:2020-2034` で `rep_observations` を**そのまま**
`floor-pair-window/v3` の record へ保存し、その bytes が `finalize_floor()` の
`artifact_sha256` に入る。

本 wave で runner が 7 key を出すようになったので、**実行時にはこの成果物の bytes と
digest が変わる。**

ところが所有 file の fake は**まだ 3 key しか作っていない**。

- `test_floor_pair_driver.py:1457-1461`
- `test_floor_pair_driver.py:1670-1673` 付近
- `test_floor_pair_driver.py:2331-2335` 付近

```python
{"rep_index": 0, "returncode": 0, "throughput": 101.0},
```

このため、**同じ `floor-pair-window/v3` schema が旧 3 key と新 7 key の両方を受理し、
実 producer の形を 1 度も通していない。** 依存先の stub が実体と食い違っている状態である
(F649 の型)。

## やること

1. **所有 file の fake observation を、実 runner が実際に出す 7 key の形にする。**
   key は `rep_index` / `returncode` / `counter_status` / `missing_perf_events` /
   `perf_raw` / `throughput` / `execution_failure`。
   **実 runner の生成箇所 (`orchestrator/calibrator/runner.py` の
   `capture_measure_point()` と `measure_point()`) を自分で開き、
   正常 rep のときに何が入るかを読み取って合わせること。** 推測で書かない。
   `execution_failure` は exact `bool`。正常 rep なので `False`。
2. **保存される window record が 7 key の observation を持つことを test で固定する。**
   `floor-pair-window/v3` の record に入った `rep_observations` の key 集合を
   exact に検査する node を足す。**`artifact_sha256` の値そのものを焼き込まない**
   (揮発 payload になる)。固定するのは **key 集合と型**である。
3. **fake を実体へ寄せた結果、既存 node が赤くなったら、それは実体との食い違いが
   露出したということである。** その場合は**期待値を緩めずに**報告すること。
   production を直す必要があると判断したら、**直さずに報告して止まること**
   (production は所有外)。

## 禁止

- `git` を実行しない。commit しない。
- `orchestrator/tests/test_floor_pair_driver.py` 以外の追跡下 file を 1 つも変更しない。
- production の挙動を変えない。
- **テストを甘くして緑にしない** (F27)。期待値の反転・緩和・skip・削除をしない。
  赤なら実装側が誤りとし、期待値が誤りなら実装を変えず報告して止まる。
- 期待値へ揮発 payload (hash・時刻・絶対 path) を焼き込まない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1
PYTHONPATH=. python3 orchestrator/tests/test_floor_pair_driver.py
```

**`run_tests` は使わない (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
**成長 hold が出たら迂回せず、走らせずに報告すること。**
**緑には実走 nodeid・範囲を必ず併記する。** 実走できなかったものは
「実装済み・未実走」と書き、理由を書くこと。

## 出力形式 (この見出しをこの順で使う)

## 実 runner が正常 rep で出す 7 key の実測
## 直した fake の位置 (file:line)
## 追加した window record の固定
## 実走した nodeid と結果
## 期待値を緩めずに報告した赤 (無ければ「無し」)
## 総括
