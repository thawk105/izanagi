## 実装した内容

- [floor_pair_driver.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:22)、同:86、同:3117 — proof-limit を tree 同値、OID 非同値、実行 module bytes 非証明へ更新（must-fix 1, 6）。
- [floor_pair_driver.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:538) — `_git_show_head` を解決済み OID 指定へ変更。`_git_parents`、`_git_changed_paths` を追加し、raw stdout を厳密解析（must-fix 1, 2）。
- [floor_pair_driver.py:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1234) — `loaded_head` を冒頭で一度だけ解決し、spec・calibration・receipt の blob 比較を同 OIDへ束縛。唯一親と spec-only 差分を要求（must-fix 1, 2）。
- [floor_pair_driver.py:2272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:2272)、同:2740 — runtime/finalizer を `loaded_head` に統一し、status を `loaded_head_mismatch` へ変更（must-fix 1, 3）。
- [test_floor_pair_driver.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:306) — 模擬 Git を実 Git同形の raw stdout対応にし、`HEAD:path` と `<oid>:path` を分離可能にした（must-fix 2, 4）。
- [test_floor_pair_driver.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:492) — fresh worktree 正例、spec＋別 path 負例、merge HEAD 負例を実 Gitで追加。`out/.gitkeep` を親 commit に含めた（must-fix 4, 5）。
- [test_ccbench_spawn_sites.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_ccbench_spawn_sites.py:113) — 新 Git helper 2 site を exact inventory へ登録（must-fix 1）。

`SPEC_SCHEMA`、top-level/provenance exact key、既存 HMAC golden orderは変更していません。

## 現行挙動と変更後挙動

変更前は、通常の Git object 解決では「spec が HEAD blob と一致」かつ「`source_commit == HEAD`」を満たす正規 freeze commitを作成できませんでした。runtime も三者一致を要求していました。

変更後は、親 `C` に固定入力、唯一の子 `H` に spec pathだけを入れた形を受理します。`source_commit=C`、`loaded_head=runtime_head=H` です。merge、root HEAD、親不一致、spec以外の差分、blob不一致、runtime HEAD移動、Git raw出力不正は拒否します。

`--no-replace-objects`、freeze receipt、working-tree clean検査、T-2423は変更していません。

## 実走した検査

pytestは未実走です。`tools/run_tests.py`による以下の試行はいずれもテストプロセス開始前に `rc=16` となりました。

- 新規実Git 3 nodeid、blob OID、Git failure、mutation 03/19、runtime、finalizer、proof-limit、spawn inventoryの一括指定: `rc=16`
- `test_real_git_spec_only_child_loads_from_fresh_checkout`: `rc=16`
- 両変更テストファイルの `--collect-only`: `rc=16`

原因は Pegasus dispatch の `qstat -Q` が `EACCTAUTH Unknown user-id` で `rc=1` となったためです。

実行済みの静的検査:

- 3ファイルの `ast.parse`: `rc=0`
- `git diff --check`: `rc=0`
- HMAC golden orderの決定的再計算: `rc=0`、既存期待値と一致
- `ruff check`: `rc=127`（ruff未導入）

全 `test_floor_pair_driver.py`、spawn inventory meta-test、所有外consumer testは未実走です。

## 波及可能性

- 所有外caller: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- 同一ファイル内caller: driver CLIの `load_frozen_spec`
- 共有fixture consumer: `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
- meta-test: `test_reviewed_process_launch_inventory_is_recursive_and_exact`
- production file集合pin: `test_official_perf_closure.py`

## 未了・判断を仰ぐ点

- planの「status維持」と裁定の改名が競合したため、権威である裁定に従い `loaded_head_mismatch` を採用しました。
- 実装は完了していますが、Pegasus認証障害によりpytestは未実走です。
- 変更済みtracked fileは指定された3ファイルだけで、commit操作は行っていません。

## 総括

spec-only childによる作成可能なfreeze形へ修正しました。  
全blob、lineage、tree差分を一度解決した`loaded_head`へ束縛しています。  
実Git正負例とspawn inventoryも実装済みです。  
ただしpytestはdispatch障害のため未実走です。