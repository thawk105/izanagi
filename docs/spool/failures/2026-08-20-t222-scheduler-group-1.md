---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: t222-scheduler-group
seq: 1
---

## 新規

### {{F:pytest-xdist-teardown-hang-under-mass-failure}}. 大量失敗を伴う変異走行で pytest-xdist の集約・終了処理が host 混雑下で無応答になる [infra不調] [測定汚染]

- 事象: `tools/pegasus/dispatch_compute.py` の `_accounting_present` へ「常に False を返す」
  「比較演算子を反転する」型の変異を適用し、`orchestrator/tests/test_pegasus_dispatch_compute.py`
  全体 (188 test, `pytest -n 32 --dist loadgroup`) を `tools/run_tests.py` で実走したところ、
  4回中4回、90〜300秒 CPU時間ほぼ0のまま無応答になった (`-n 4` へ削減しても再現)。
  host load average 5〜10 (18ユーザー、多数の並行 dev-wave wave が同時に main へ land していた)、
  `free -h` は 199GiB available で単純なメモリ枯渇ではなかった。SIGTERM で終了させると
  `pytest_sessionfinish` の hookwrapper teardown で `OSError: cannot send (already closed?)`
  (`PluggyTeardownRaisedWarning`) が発生し、それまでの進捗 (76%超) がまとめて flush された。
- 根本原因: 未特定。大量の同時失敗 (~50件超) を32 worker から集約する際の pytest-xdist の
  worker 終了ハンドシェイクが、host 混雑下でのプロセススケジューリング遅延と組み合わさって
  極端に遅延する、または稀に完全に停止する事象と推定される。変異が生む失敗の性質
  (`_accounting_present` に依存する無関係な多数の integration test を波及的に失敗させる) が
  トリガーになっている可能性が高いが、pytest-xdist / execnet 側の再現条件までは切り分けていない。
- 恒久対応: 未実装。回避策のみ確立 — 変異の検証に本当に必要な test 関数だけへ pytest node
  選択 (`file.py::test_name` の裸列挙、`-k` ではなく明示 nodeid) で絞り込むと、同じ変異でも
  2秒未満で完走し再発しなかった。変異事前登録の時点で「この変異は無関係な多数のテストへ
  波及するか」を検討し、波及する変異は最初から絞り込んだ node 集合で登録するとよい。
- 再発検知: 同種の「ほぼ全ての呼び出しで False/True を返す」型の変異を伴う手動変異検証で、
  full-file 実走が baseline (数秒〜十数秒) の5倍以上を要して停止していなければ、この節を疑う。
