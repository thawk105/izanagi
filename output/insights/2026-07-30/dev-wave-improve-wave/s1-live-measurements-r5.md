# 親の実走実測 (R5 closure wave, 2026-07-31)

前 wave は「pytest、build、qsub、qstat、qdel、mutation は未実走」で停止していた。本 wave の親が
初めて実走した結果を、主張の強さを込みで記録する。**すべて親の主張であり段 3 の攻撃対象とする。**

## L1 — sanctioned runner はログインノードで一度も dispatch できない (PYTHONPATH)

- 実測: worktree root で `python3 tools/run_tests.py` → rc 125、
  `Pegasus test dispatch failed: login dispatch refuses unbound pytest/plugin environment: PYTHONPATH`
- 環境事実: pegasus02 の login shell は `PYTHONPATH=/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/advisor/2022.3.1/pythonapi`
  を site-wide に設定している (ユーザーの dotfiles ではない)
- 該当コード: `tools/pegasus/test_dispatch.py:733-741 encode_pytest_argv` の `_PLUGIN_ENV` 非空拒否
- 親の主張 (攻撃対象): これは安全側の**過剰拒否**である。runner 環境 allowlist (`:302-309`) は
  そもそも `PYTHONPATH` を子へ渡さないので、拒否ではなく除去で足りる。現状では
  `hooks/guard_bash.py` が直接 pytest を拒否し runner も拒否するため、**既定 shell では
  重い処理を走らせる正規手段が存在しない**
- 親の主張の限界: 「除去で足りる」は静的読みであり、除去版を実装して測ってはいない

## L2 — sanctioned runner は nested submodule 未初期化でも dispatch できない

- 実測: `env -u PYTHONPATH python3 tools/run_tests.py` → rc 125、
  `Pegasus test dispatch failed: submodule size inventory requires initialization`
- 環境事実: `git submodule status` は ` d706650 external/ccbench` (初期化済み) だが、
  `git submodule status --recursive` は `-fb14e659... external/ccbench/third_party/shirakami` を返す
- 該当コード: `tools/pegasus/test_dispatch.py:1618-1628` が `submodule status --recursive` の
  `-` 接頭辞を一律拒否
- 親の主張 (攻撃対象): repo の運用契約 (`DW-O08`) と既存 wave の受入は
  `git submodule update --init` (非 recursive) までしか要求していない。よって再帰要求は
  契約と食い違う過剰拒否である
- 親の主張の限界: shirakami を初期化した場合に通るかは測っていない (初期化していない)

## L3 — 継承した staged tree は 15 赤である

- 実測 A (wave tree, staged 差分あり): 計算ノード bnode040 / affinity 48 / Python 3.10.12 /
  `python3.10 -m pytest -n 48 -q -rf` → **15 failed, 4069 passed, 19 skipped in 101.55s**
- 内訳: `test_s8b_oracle_driver.py` 10、`test_pegasus_test_dispatch.py` 3、
  `test_pegasus_tools.py` 1、`test_run_tests_task_run.py` 1
- 実測 B (base `72e3800` の clean detached worktree、submodule 初期化済み、`-n 16`):
  同 3 file (`test_s8b_oracle_driver.py` / `test_pegasus_tools.py` / `test_run_tests_task_run.py`)
  → **178 passed, 1 skipped, 0 failed**
- 実測 C (s8b の根本原因、失敗本文より逐語):
  `FileNotFoundError: [Errno 2] No such file or directory:
  '<fixture repo>/tools/pegasus_policy.py'` が
  `orchestrator/campaign/buildcache.py:52 _read_trusted_policy_source` で発生し、
  `s1_known_axes_freeze.py:25` の import 連鎖を落としている
- 親の主張 (攻撃対象): 15 赤はすべて wave の staged 差分に帰属し、うち 10 件は単一原因
  = wave が `buildcache.py` に新しい trusted policy source (`tools/pegasus_policy.py`) を足した際に
  T-080 E2E fixture の必須 file 閉包を更新しなかった **consumer 取り残し**である
- 親の主張の限界: 実測 B は 3 file だけ・`-n 16`・別 path の clean checkout であり、
  実測 A と worker 数も tree 状態も揃っていない。s8b は git 履歴と作業ツリー状態に敏感なので、
  「staged 差分に帰属」と「未 commit 状態に帰属」を実測で分離していない

## L4 — 受入の実行手段

- 本 wave の受入計測は、親側の使い捨て qsub job script (job tmp、repo へ commit しない) で
  計算ノードへ投入している。理由は L1/L2 により製品側 runner が使えないため
- 親の主張 (攻撃対象): これは「製品の dispatcher を通した受入」ではないので、
  dispatcher 自身の end-to-end 正しさは本 wave では受入できていない
