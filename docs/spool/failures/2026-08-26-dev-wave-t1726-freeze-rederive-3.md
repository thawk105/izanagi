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
- **再発: 2026-08-26 (書き手の棚卸し)** — 本件を機に `output/` 配下の窓内書き手を数えたところ、
  親の編集 (F62 の元事例) 以外に少なくとも次が在り、**列挙は完了していない。**
  (i) `output/runs/pytest-launcher-failures/<PBS_JOBID>--<host>/` — launcher テストの失敗時診断。
  `.gitignore:18` 済みで git 系検査には現れない。
  (ii) `output/pegasus-dispatch/<hash>/receipt.json` — dispatch ごとの receipt。`.gitignore:26` 済み。
  **失敗時でなく毎回書く** — 本 wave 単独で 17 件生成された。並行 wave が変異走行や
  dispatch を回していれば全走中に増える。
  (iii) `output/task-runs/reports/` — 並行 session が窓内で観測した実体。
  こちらは tracked (ignore されない) 点で (i)(ii) と異なる。窓内の書き手は未特定である
  (`tools/run_tests.py:1068` は root を既定するが、`record_test_run` の呼出しは
  `duration_s` / `exit_status` を取る走行後の位置 1211-1220 行にあり、外側の走行自体は窓内で書かない)。
  並行 session の独立実測では **launcher の赤が 0 件**でも同じ 11 件が落ち、侵入 entry は
  `runs` と `task-runs/reports` だった。**launcher の失敗は十分条件であって必要条件ではない。**

## supersede 追記

- F62 **supersede: 2026-08-26** — 恒久対応の「受入全走の実行中は `output/` 配下を一切編集しない」は親向けの行動規律であり、同じ全走の中にいる並行テストや dispatch receipt の書き込みには効かない。機構側の対応が要る。選択肢は (a) `_real_output_snapshot()` から `output/` の揮発 subtree を除外する、(b) 書き手側の artifact root を repo 外へ移す、(c) `orchestrator/tests/conftest.py:338` の `REAL_REPO_SERIAL_NODES` へ落ちた node を登録して `xdist_group("real-repo")` で直列化する (1326-1330 行、`test_s8b_floor_campaign.py` は 394/395/421 行の 3 node が登録済みで本件の 11 件は未登録) の 3 つで、(b)(c) はいずれも書き手を列挙し切ることを前提にするが本追記のとおり列挙は未完了であり、(a) だけが列挙に依存しない。どれを採るかは受理集合の射程を変えるため裁定へ返した。
