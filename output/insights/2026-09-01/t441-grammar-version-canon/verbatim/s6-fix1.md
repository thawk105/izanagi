## 直した所見

- D-1 — [p3_s4_loop.py:1116](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/campaign/p3_s4_loop.py:1116): duplicate reader で `validate_backoff_grammar_bindings()` と既存 `validate_commit_contract_bindings()` を併記し、完全 topology 検査への過剰接続を除去。
- D-2 — [p3_s4_loop.py:378](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/campaign/p3_s4_loop.py:378): 両 reject helper の既定を `Optional[int] = None` に変更。`None` は旧 pre-image、明示版だけが版 token を追加。
- D-3 — [p3_s4_loop.py:411](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/campaign/p3_s4_loop.py:411): variant ID 導出前に明示版と lock 版を exact 比較。省略・不一致を WAL 書込み前に拒否する負例を [test_p3_s4_loop.py:2349](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:2349) に追加。
- D-4 — [test_p3_s4_loop.py:2915](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:2915): unbound poison entry を配置し、legacy/v2 とも旧 entry を開かず fresh build へ進む実 lookup テストを追加。
- D-5 — [test_p3_s4_loop.py:2664](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:2664)・[test_p3_s4_loop.py:2732](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:2732): `run_campaign` の resolver/evaluate、および pipeline の resolver/build/build_v2 seam で同一版を exact に観測。
- D-6 — [test_p3_s4_loop.py:437](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:437): `run_one_iteration(do_build=True)` を通し、`value=20`、raw `0x14`、canonical source `20`、genome `BACKOFF_FIXED=20` を `run_campaign` 入口の同一呼出し内で固定。
- X-1 — [test_p3_s4_loop.py:230](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:230): 許可範囲どおり `20.0` を `20` にのみ更新。
- X-2 — [test_p3_s4_loop.py:3111](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:3111): `BUILD_START.payload` に `backoff_grammar_version` を1 keyだけ追加。

## 既定経路の不変性

[test_p3_s4_loop.py:2337](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix1/orchestrator/tests/test_p3_s4_loop.py:2337) で、旧式 `sha256(genome.canonical() + "|impl=" + implementation)[:12]` を独立に計算し、引数省略と明示 `None` の双方がその ID と exact 一致することを固定しました。所有外の sort／trigger／probe caller は版引数なしのままで、旧 identity 経路を維持します。

## 実走した検査

- `python3 -m py_compile orchestrator/campaign/p3_s4_loop.py orchestrator/tests/test_p3_s4_loop.py` — 成功。
- `git diff --check` — 成功。
- 新設3 nodeid、追加6 nodeidの collect-only、焦点 file 全体、および duration／real-repo 制約 meta-testを `tools/run_tests.py` から試行しましたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、`rc=16` で停止しました。
- pytest 本体へ到達した nodeid は0件です。したがって本成果は「実装済み・未実走」であり、緑・closed とは申告しません。

## 波及可能性

- 所有外 caller: `s6_sort_sweep.py:360`、`p3_s4_loop_sort.py:202,225,231`、`p3_s4_loop_trigger_gating.py:486`、`s8a_trigger_sweep.py:462`、`p3_b4_wiring_probe.py:1419`。いずれも `None` 経路へ戻ります。
- `_critic_view()` の既存20 call siteは明示 legacy lock のままです。
- consumer test は既知の duplicate 5 nodeid、versioned WAL writer/topology/duplicate reader、reflux payload exact 集合へ波及します。
- cache lookup テストは既存 `test_buildcache_v2` の `_contract`、`_install_toolchain`、`_fake_build_environment` を再利用しますが、共有 helper 自体は未変更です。
- docs、禁止固定値4群、両 import ブロックは無変更です。

## 赤の内訳

テスト由来の赤は未観測です。観測された失敗は全て Pegasus dispatch infrastructure の `rc=16` です。

また、`p3_s4_loop.py` は HEAD blob 束縛対象なので、親が統合 commit を作る前の焦点走では既知の `contract-loader-drift` 全赤が予想されます。親 commit 後に、従来の7赤、追加6 nodeid、制約 meta-testを再実走する必要があります。

## 総括

D-1〜D-6とX-1・X-2をコード／テスト2ファイルだけで実装しました。  
受理の含意: 指定された10表記は引き続き受理され、材料化後は `double now_backoff = 20;` に収束します。  
拒否の含意: 複文は `statement-count.v1`、`20.0f` は `initializer-literal.v1` で拒否され、複文の正準化は呼ばれません。  
commit・add・push・branch操作は行っていません。  
pytestはdispatch障害のため未実走です。