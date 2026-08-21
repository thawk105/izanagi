---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: worktree-dev-wave-t1433-collection-cost
seq: 1
---

## {{D:t1433-collection-manifest-no-low-risk}}. xdist collection 固定費への controller-only / manifest 共有はいずれも低リスク案なしと結論する

**決定:** 受入全走の xdist collection 固定費 (D532 (c)、48 worker が各自全テストを collection
する費用) を、worker 数変更以外の技法 (controller-only collection、collection manifest 共有)
で削減する案を、xdist 3.8.0 の実ソースで検証し、**いずれも採用しない (実装しない)。**
worker 数変更・`IZANAGI_TEST_NPROC` 変更・D585 (per-test snapshot copytree の hardlink化) は
再提案しない。

**理由:**
- controller 側の `pytest_collection` hook は `# prohibit collection of test items in
  controller process` と明記して controller 自身の collection を構造的に禁止しており
  (`xdist/dsession.py:103-105`)、controller-only collection の実現にはこの guard を外すこと
  に加え、controller から worker へ**実行可能な worker-local Item 相当の object** を渡す
  新しい IPC 経路が要る。現行 wire protocol (`xdist/remote.py:257-261`) は nodeid 文字列しか
  運ばない。
- worker の実行は `self.session.items[index]` を直接参照して `pytest_runtest_protocol` へ渡す
  (`xdist/remote.py:211-227`)。scheduler が保持・比較するのは nodeid 文字列一覧であり
  (`xdist/scheduler/load.py:62-65`, `xdist/scheduler/loadscope.py:93-99`)、id 一覧が一致しても
  worker 側の実行用 Item construction を代替しない。したがって「manifest (id 一覧) を 1 回だけ
  計算して worker 間で共有し、各 worker の再 collection を省く」案も、worker 側の Item
  construction を省けない点で controller-only と同じ壁に当たる。
- `--dist loadgroup` (本 repo の既定、`tools/run_tests.py:406-410`) が使う
  `LoadGroupScheduling` は `LoadScopeScheduling` を継承し (`xdist/scheduler/loadgroup.py:10`)、
  初回 collection 完了時に全 worker の collected id 一覧が完全一致することを要求する
  (`xdist/scheduler/load.py:257-264,309-335`、`xdist/scheduler/loadscope.py:357-382,409-438`。
  後発 worker の再照合は `load.py:127-145`、`loadscope.py:207-231`)。不一致は
  `report_collection_diff` で abort する。id 一覧の配布だけでは、各 worker が独立に本物の
  Item を構築して報告するという不変条件を満たせない。
- `--dist` の既存値 (`each`/`load`/`loadscope`/`loadfile`/`loadgroup`/`worksteal`,
  `xdist/dsession.py:108-126`)、`pytest_xdist_node_collection_finished` (collection 完了後の
  通知 hook、代替入口ではない、`dsession.py:274-306`)、gateway 起動方式 (`popen` / 非 `popen`
  いずれも `remote_exec` で worker-local pytest session を起動する、
  `xdist/workermanage.py:325-349`) のいずれにも、worker 側の Item construction を省く既存の
  抜け道は無い。
- 段2 codex plan (read-only) と段3 敵対相談 2 レンズ (正しさ境界、整合性・実効性・scope) が
  独立に上記を検証し、BLOCKER 0 で結論を支持した。

**却下した選択肢:**
- controller-only collection (controller が collection を担い、結果を worker へ配布する) —
  `dsession.py:103-105` の既存 guard と正面から矛盾し、worker-local Item を渡す新しい IPC を
  要求する。xdist protocol の変更に当たり低リスクではない。
- collection manifest 共有 (collected node id 一覧を 1 回だけ計算し worker 間で共有する) —
  id 一覧は scheduler の必要条件に過ぎず、worker 側の実行用 Item construction を代替できない。
  結局 worker bootstrap 契約の変更を要し、controller-only と同じ理由で低リスクではない。
- worker 数変更・`IZANAGI_TEST_NPROC` の調整 — D532 が既に却下済み (worker 数増は gen_S の
  per-job CPU 上限 48 で頭打ち、減は模型で悪化)。本決定の scope 外。
- D585 型の per-test hardlink 化の再提案 — D585 は別トピック (real-repo 鎖の per-test snapshot
  copytree) であり、実測で効果が高々 1 秒と確認済み。本件 (xdist collection) には適用対象がなく
  再提案しない。

固定費削減 (D532 (c)) の他の実現手段は本決定の対象外とし、閉じない。P2 (現在の collection
コスト実態の再測定要否) は本決定と独立の backlog として worklog へ別記する。
