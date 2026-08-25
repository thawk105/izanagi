---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 3
---

## 再発

### F62

- **再発: 2026-08-26** — 受入全走 attempt 2 (claimed_main
  `f4c2c5ded29d72d8f06bca66992a5ef5694fcb51`) で `test_s8b_floor_campaign.py` の
  official / pilot 系 **11 件**が同じ `assert repo_before == _real_output_snapshot()` で落ちた。
  **書き手は親ではなく、同じ全走の中の並行テストである。** 差分本文は
  `At index 13837 diff: ('dir','s1-budget') != ('dir','runs/pytest-launcher-failures/0-948253.nqsv--bnode042')` で、
  侵入 entry は `orchestrator/tests/test_codex_worker_launch.py:55` の `_FAILURE_ARTIFACT_ROOT`
  (`output/runs/pytest-launcher-failures`) を `_failure_run_directory()` (87-92 行) が
  **失敗時にだけ**掘ったものである。親は attempt 1 / 2 の実行中に `output/` を一切書いていない。
  同 wave の attempt 1 は launcher 9 件 + floor 0 件、attempt 2 は launcher 2 件 + floor 11 件で、
  件数でなく書き込みと snapshot 窓の重なりで決まる。
  単独走はいずれも緑 (`--force-dispatch`) — `test_codex_worker_launch.py` = 202 passed / 8.83s、
  `test_s8b_floor_campaign.py` = 455 passed / 2 skipped / 34.21s。`DW-O18` に従い実装差分へ帰属させず、
  land せずに停止した。
- **再発: 2026-08-26 (別 wave・別 helper。同日 2 例目)** — branch
  `worktree-dev-wave-t1219-carry-same-id` (tip `b190116c`) の受入 attempt 2 で
  `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`
  が落ちた。junit
  `/work/1/SFC/tanab/.izanagi-acceptance-shards/fcb3b5638d9f8a70135f34950072047a/junit.xml`
  を直接読んで確認した (全走 13 failed)。**検査は `_real_output_snapshot()` ではなく、
  `orchestrator/tests/test_s8b_oracle_driver.py:554` の `_t080_output_snapshot()` という
  別 file の独立した 2 つ目の helper である** (呼出しは 1138 / 1150 行)。
  こちらは各 entry の `st_mode` / `st_size` / `st_mtime_ns` / `st_ctime_ns` を記録するため、
  内容が変わらなくても**一時 file の作成削除による directory timestamp の変化だけで落ちる**。
  侵入 entry は `runs` と `task-runs/reports` の 2 つで、`runs` の mtime は同じ snapshot 内の
  `s1-budget` より **12,261 秒後** (1787680919 対 1787668658) であり走行中に掘られたことと整合する。
  一方 `task-runs/reports` の mtime は `s1-budget` の 1 秒後 (1787668659) で走行中の生成では
  説明できず、entry として現れた機序は未解明である。
  **同じ 2 entry が別 wave・別 branch・別 junit で観測されており、書き手は wave 固有ではない。**
- **再発: 2026-08-26 (書き手の棚卸し)** — 本件を機に `output/` 配下の窓内書き手を数えたところ、
  親の編集 (F62 の元事例) 以外に少なくとも次が在り、**列挙は完了していない。**
  (i) `output/runs/pytest-launcher-failures/<PBS_JOBID>--<host>/` — launcher テストの失敗時診断。
  `.gitignore:18` 済みで git 系検査には現れない。
  (ii) `output/pegasus-dispatch/<hash>/receipt.json` — dispatch ごとの receipt。`.gitignore:26` 済み。
  **失敗時でなく毎回書く** — 本 wave 単独で 17 件生成された。並行 wave が変異走行や
  dispatch を回していれば全走中に増える。
  (iii) `output/task-runs/reports/` — tracked (ignore されない) 点で (i)(ii) と異なる。
  窓内の書き手は未特定である (`tools/run_tests.py:1068` は root を既定するが、
  `record_test_run` の呼出しは `duration_s` / `exit_status` を取る走行後の位置 1211-1220 行にあり、
  外側の走行自体は窓内で書かない)。
  並行 session の独立実測では **launcher の赤が 0 件**でも floor_campaign の 11 件が落ちており、
  **launcher の失敗は十分条件であって必要条件ではない。**

## supersede 追記

- F62 **supersede: 2026-08-26** — 恒久対応の「受入全走の実行中は `output/` 配下を一切編集しない」は親向けの行動規律であり、同じ全走の中にいる並行テストや dispatch receipt の書き込みには効かない。機構側の対応が要る。選択肢は (a) `output/` の揮発 subtree を除外する、(b) 書き手側の artifact root を repo 外へ移す、(c) `orchestrator/tests/conftest.py:338` の `REAL_REPO_SERIAL_NODES` へ落ちた node を登録して `xdist_group("real-repo")` で直列化する (1326-1330 行、`test_s8b_floor_campaign.py` は 394/395/421 行の 3 node が登録済みで本件の 11 件は未登録) の 3 つ。(b)(c) はいずれも書き手を列挙し切ることを前提にするが本追記のとおり列挙は未完了であり、(a) だけが列挙に依存しない。ただし (a) は 1 箇所では閉じない — 走査 helper は `test_s8b_floor_campaign.py:1451` の `_real_output_snapshot()` と `test_s8b_oracle_driver.py:554` の `_t080_output_snapshot()` の 2 つが独立に在り、後者は mtime/ctime まで見るため除外規則を共通化して両方へ適用し、揮発 entry の親 directory も対象に含める必要がある。どれを採るかは受理集合の射程を変えるため裁定へ返した。
