---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1858-chain-shared-setup
seq: 2
---

## 新規

### {{F:flaky-hold-remediation-blocked-by-ownership}}. 非帰属 flake の規定の是正経路が並行 wave の所有で塞がり、hold 登録という誤った側へ倒れかけた [手順漏れ] [資源競合]

- 事象: 本 wave の受入全走が 2 走続けて `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`
  1 件だけで赤になった (17392 passed / 1 failed / 64 skipped、2 走とも同一 node・同一 assertion)。
  assertion 本文は `child.pid was not registered before deadline; stderr=''` で、
  子 process が 2 秒の期限内に pid file を書けなかったという時間依存の主張である。
  同 node の単独走は 1 passed / 7.15 秒で再現しない。本 wave の差分は s8c 事前登録の
  test 2 file だけで、この経路へ到達しない。**非帰属である。**
- `DW-O18` は再赤に対して「main 既存の F を証拠に Codex `role=author` が
  `orchestrator/tests/flaky_test_holds.py` へ登録」を規定する。証拠は F57 が満たしており、
  検証器の要求 (evidence section が test 関数名と failure signature を逐語で含むこと) も
  実測で確認した。**それでも登録できなかった。**
- 根本原因: 是正経路 2 本がどちらも並行 wave の所有下にあった。
  (a) `orchestrator/tests/flaky_test_holds.py` は 3 wave が触っており、うち 1 つは
  登録済み hold を全撤去する wave だった。(b) 期限そのものを直す
  `orchestrator/tests/test_codex_worker_launch.py` も 2 wave の所有下だった。
- **書き込む前に所有者へ相談したことで、より重い誤りを避けられた。** 相談の結果、
  同じ node を別 wave (`worktree-dev-wave-t1848-env-coincidence`) が
  **hold ではなく修理で既に閉じている**ことが分かった。修理は 2 秒の絶対期限を除去して
  判定を launcher 終了後へ移すもので (`child.pid` は終了後も残る)、外側の 10 秒 watchdog は
  元のまま、上限は 1 つも広げていない。期限を復活させない回帰検出テストも同時に足されている。
  **もし所有を押し切って hold を登録していたら、着地の瞬間に「修理済みのテストが台帳に残る」
  状態を作っていた。**
- **同じ node で 3 つの wave が独立に詰まり、うち 2 つが hold へ倒れかけた** (1 つは登録後に
  撤回した)。同型の陳腐化そのものは別 wave が `stale-flaky-hold-outlives-its-fix` として
  記録しているので、本項では重複させない。
- **hold の射程を過小評価してはならない。** `conftest.py` の `pytest_collection_modifyitems` は
  登録 node へ無条件に `pytest.mark.skip(..., append=False)` を付けるため、受入だけでなく
  焦点走でも常に skip される。登録は「受入から一時的に外す」ではなく
  「検査集合から落とす」である。
- 恒久対応: **非帰属赤で hold 登録へ進む前に、(1) 同じ node を別 wave が修理していないか、
  (2) 是正経路の file を別 wave が所有していないかを、この順で確認する。**
  どちらかに当たったら書き込まず所有者へ相談する。所有の塞がりが常態化する場合の構造的対処は
  裁定事項として次の 2 案を残す — (a) hold registry を wave ごとの fragment + fold 方式にして
  行の奪い合いをなくす、(b) 是正経路の file を編集面重複検査の例外にする。
  (b) は fail-open の方向に既定値を作るため D445 が同型の allowlist 案を却下した前例がある。
  本件の実地の解は (a) でも (b) でもなく**別 wave による修理**だった。
- 再発検知: 受入が非帰属赤で 2 走連続して落ち、かつ是正経路の file が別 wave の所有下にある状態。
