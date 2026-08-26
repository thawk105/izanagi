# 親が独立に実測・読解した事実 (段 4 裁定で子の主張と突き合わせる)

基準: worktree `.claude/worktrees/dev-wave-flaky-holds-20260826`、main `e29084e0` 取り込み済み。

## M1. hold は焦点走でも常に skip される (opt-in の抜け道が無い)

3 node を `tools/run_tests.py` で名指しした焦点走 → `3 skipped`、
`IZANAGI_FLAKY_HOLD_SUMMARY_V1 {"registered_node_count":3,"matched_node_count":3,"skipped_node_count":3,...}`。

`conftest.py` の `pytest_collection_modifyitems` は `flaky_node_id` が付いた item へ
無条件に `pytest.mark.skip` を付ける。growth hold と違い `opted_in` の分岐が無い。
**登録された node はどこでも走らない。**

## M2. hold を外すと 3 node とも緑

DW-O19 の一時変異 (`FLAKY_TEST_HOLDS = _validate_flaky_test_hold_rows(())` の 1 行、
`git diff --stat` = 1 file / 1 insertion / 1 deletion) で焦点走 → `3 passed in 13.66s`。
`git checkout --` で復元し `git status --porcelain` 空を確認済み。

単独走が緑なのは hold 登録時点でも同じだった (登録行の `green_observation` がそう書いている)。
**この実測は「修理された」ことの証拠ではなく、「受入相当の並列下でしか出ない」ことの再確認である。**
hold#1 / hold#3 が本当に直ったかは、本 wave の受入全走でしか確かめられない。

## M3. T-1856 の決定的な赤を 3 file で同時再現

焦点走 rc=1。3 件とも `assert 'runs' in ('pegasus-dispatch',)`。

- `test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
- `test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
- `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes`

fresh worktree に `output/runs` は不在。`output/task-runs` は在る。

## M4. snapshot helper は 3 つあるが、同型は 2 つだけ

- `test_s8b_oracle_driver.py:558` の `_t080_output_snapshot` と
  `test_real_repo_serialization.py:541` の同名 helper は**逐語で同一**
  (`diff` は後続関数の有無だけ)。両者が (D-b) を持つ。
- `test_s8b_floor_campaign.py:1484` の `_real_output_snapshot` は**構造が違う**。
  root entry を含めず、`st_mtime_ns` / `st_ctime_ns` を一切記録しない。
  `(kind, rel, digest)` の内容 hash を取る。**(D-b) を構造的に持たない。**
  同 file には独立 oracle の `_real_output_snapshot_reference` (`rglob` 実装) があり、
  両者の一致を `test_real_output_snapshot_matches_reference_and_is_deterministic` が固定している。

含意 2 つ。

1. (D-b) の修理対象は 2 file であって 3 file ではない。
2. **`test_s8b_floor_campaign.py` が (D-b) を持たない形の存在証明になっている。**
   「timestamp を記録しなくても snapshot 検査は成立する」ことを、同じ repo の中の
   別実装が示している。(D-b) の修理案「mtime / ctime を記録しない」は、
   新奇な設計ではなく既存の姉妹実装へ寄せる変更である。
3. ただし F136 が `test_s8b_floor_campaign.py` で記録した赤
   (`first extra item: ('dir', 'task-runs/reports')`) は (D-b) ではない。
   **git-visible な directory が並行 shard によって実際に作られている。**
   これは除外集合の直し方では消えない別問題であり、本 wave の scope 外。

## M5. 空 registry は既に想定済み

- `conftest.py` は `not FLAKY_TEST_HOLDS` の分岐を明示的に持ち、空でも
  `IZANAGI_FLAKY_HOLD_SUMMARY_V1` を出す (M2 の実走で確認)。
- `test_flaky_test_holds_contract.py:316` に `_EMPTY_REGISTRY_SHA256` の定数がある。
- registry digest は全経路が動的計算で、literal pin は上記 1 つだけ。

live registry が非空であることに依存する箇所は 2 つ。

- `test_flaky_test_holds_contract.py:292-311`
  `test_live_registry_excludes_reintroduced_node_and_preserves_main_hold`
  (`REG.FLAKY_TEST_HOLDS[_NEW_HELD_NODE]` が KeyError になる。
  `reintroduction_task_id == "{{T:flaky-thread-join-upper-bound}}"` を逐語 pin している)
- 同 file `913` の `_NEW_HELD_NODE: REG.FLAKY_TEST_HOLDS[_NEW_HELD_NODE]`

`1011` / `1015` は `len()` 経由なので空でも通る。

## M6. hold#1 の再導入タスクに T 番号が無い

`{{T:flaky-thread-join-upper-bound}}` は `docs/spool/FOLDED.md` の allocation に現れない。
他の 2 件は割り当て済み (`t080-output-snapshot-shard-race` → [T-1773]、
`flaky-xdist-hook-order` → [T-1803])。撤去すれば消えるので本 wave では追わない。

## M7. `git check-ignore` は末尾スラッシュが無いと、それ自体が状態依存になる

段 2 プランの (D-a) 案は「候補を `git check-ignore --no-index --stdin -z` に渡す」だが、
親が temp repo で実測すると**候補の綴り方しだいで案が成立しない**。

probe: `/home/SFC/tanab/.claude/jobs/0384fcef/tmp/probe_checkignore2.py`
(git 2.34.1、`.gitignore` = `output/runs/` と `output/logs`)

| 入力 | directory の実在 | rc | stdout |
|---|---|---|---|
| `output/runs` (スラッシュ無し) | 不在 | 1 | 空 |
| `output/runs` (スラッシュ無し) | 実在 | 0 | `output/runs` |
| `output/runs/` (スラッシュ有り) | 不在 | 0 | `output/runs/` |
| `output/logs` (directory 規則でない) | 不在 | 0 | `output/logs` |

**含意**: `output/runs/` のような directory 規則に対して末尾スラッシュ無しで問い合わせると、
`check-ignore` は「今そこに directory があるか」で答えを変える。
`ls-files` を `check-ignore` へ置き換えるだけでは状態依存は消えない。
**directory 規則由来の候補には末尾スラッシュを付けて問い合わせ、prefix を作るときに外す**必要がある。

これは黙って恒真化する経路である。スラッシュを付け忘れると `check-ignore` は常に
「一致なし」を返し、除外集合は今までどおり `ls-files` の結果だけになる。
テストは緑のまま、fresh worktree の赤も直らない。

## M8. batch の rc は「1 件でも一致すれば 0」で、per-path の結果は stdout でしか読めない

同 probe。

| 入力 | rc | stdout |
|---|---|---|
| 一致 1 + 非一致 1 | 0 | 一致した path だけ |
| 一致 2 | 0 | 一致した 2 path |
| 非一致 2 | 1 | 空 |

**含意**: rc で per-path の可否を判定してはならない。stdout に返ってきた path 集合だけが答えである。
エラー (repository 外の path) は rc=128 と stderr で区別できる。
`git check-ignore` の 3 状態 (一致あり / 一致なし / エラー) は
rc = 0 / 1 / 128 で区別でき、これは段 3 luna レンズの検査項目 1 への回答になる。

## M9. 空の ignored directory も `ls-files -o -i --directory` は返す

`output/runs/` が空でも `output/runs/` が返る。**「中身が無いと見えない」わけではない。**
見えないのは directory 自体が存在しないときだけである。

## M10. `output/` に tracked file が 1 つも無いと `ls-files` は `output/` 自身を返す

probe 1 で観測。現行 `output_snapshot_ignores.py:31-34` はこれを
「output/ 全体が Git ignore 対象」と読んで AssertionError を投げる。
実 repo の `output/` には tracked file が 12784 個あるので発火しないが、
fixture の temp repo で `output/` を空にすると誤検出しうる。
段 5 で temp repo の contract test を書くときの落とし穴。

## M11. 偽 clock 注入後、hold#1 のテストは 13.5 秒から 0.01 秒になった

段 6 fix B の適用後、親が計算ノードで実測 (`--durations=5`)。

```
0.01s call  test_control_lock_allows_peer_after_pending_hold_is_durably_released
2 passed in 3.71s
```

- 注入前: 単独走で 13.49〜13.94 秒 (F480 の記録)、うち join 区間が 10.015 秒 (M7 の probe)
- 注入後: **0.01 秒**

`_THREAD_COORDINATION_WATCHDOG_S = 30.0` に対する余裕は約 3000 倍。
決定的な床が消えたので、この bound は latency 予算ではなく hang 回収の watchdog として機能する。
DW-O13 の「時間予算は実測分布の max への倍率で決め、母集合と観測 regime を併記する」に対して、
母集合 = 計算ノードでの当該 2 node 単独走、regime = 受入全走と同一ではない、と併記する。
ただし注入後の実所要が 0.01 秒である以上、regime の差が 30 秒を食い潰す経路は現実的でない。

契約テストを含めた焦点走は `39 passed in 34.18s` (`focus5.log`)。
