## 総括

`_run_contained_serve_child()` は、fresh subprocess から 2,728 行のテストモジュールを再 import しており、D463(b) 型の成長比例コストになっている。  
child 実行経路を `orchestrator/tests/_dev_waves_serve_child.py` へ分離し、親側は固定された helper entrypoint だけを起動する。  
既存の socket runtime node は marker・本体・受理集合を変更せず、別の ungrouped static assertion を D452 用 gate とする。  
`growth_test_holds.py`、docs、commit は実装子の編集対象外とする。

## 修正方針

1. 新設する [`_dev_waves_serve_child.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/_dev_waves_serve_child.py:1) に、child 専用の次の依存閉包を移す。

   - `_sandbox_permits_short_alias_bind()`（現 [`test_dev_waves_integration.py:1140`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1140)）
   - `_ServeObservation`、`_ServeHarnessFailure`、`_ServePoll*`、`_ServeSelectProxy`（現 `:1308-1510`）
   - `_run_long_path_serve_harness()`（現 [`:1687`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1687)）
   - `_serve_child_payload()`（現 [`:1819`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1819)）
   - `_serve_child_main()`（現 [`:2021`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2021)）
   - result prefix など child/親で共有する protocol 定数。

2. helper は `test_dev_waves_integration` を import しない。`tools.dev_waves.*` と標準ライブラリだけを import し、child 用の supervisor/request/wait 構築を helper 内に bounded に持つ。

3. 現在 `_run_long_path_serve_harness()` 内で作っている temporary repository は、親側の [`_run_contained_serve_child()` 現 `:2052-2061`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2052) で、既存の `_isolated_process_environment()`・`_temporary_repo()`（現 `:120-240`）を使って作る。child には `repo.main`、fake executable、digest、runtime path を argv で渡す。

   これにより、既存の fake receipt・Git repository・108-byte 超の path 条件を再利用しつつ、fresh subprocess が import するのは helper だけになる。

4. [`test_dev_waves_integration.py:2052-2164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2052) の process lifecycle、timeout、process-group cleanup、structured result parser 呼び出しは維持する。  
   [`:1830-2018`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1830) の parser と JSON schema も変更しない。

5. launcher の script を module-level constant 化する。

   ```python
   _SERVE_CHILD_SCRIPT = (
       "from orchestrator.tests import _dev_waves_serve_child as target;"
       "raise SystemExit(target._serve_child_main())"
   )
   ```

   `Popen` はこの constant を使う。旧 `test_dev_waves_integration as target` は残さない。

6. [`test_socket_roundtrip_works_beyond_108_byte_repository_path()` 現 `:2167-2169`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2167) は marker、本体、assertion を変更しない。

## 新設/改修テスト

### D452 用 static assertion

[`test_dev_waves_integration.py` の parser test 直後、現 `:2010` 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2010) に、次の性質だけを確認する unmarked node を新設する。

- `_SERVE_CHILD_SCRIPT` が `_dev_waves_serve_child` を指す。
- `test_dev_waves_integration` を import target に含まない。
- subprocess、socket、temporary repository、実 runtime は起動しない。

想定 node id:

```text
test_dev_waves_integration.py::test_contained_serve_child_uses_dedicated_helper_entrypoint
```

D452 の判定は次のとおり。

- (a) 既定 skip されない: `test_dev_waves_integration.py` は `GROWTH_TEST_HOLDS` に登録されておらず、新 node に `pytest.skip()` 経路もない。
- (b) mutation 時に failure になる: helper 名を旧 test module 名へ置換する mutation は、static assertion の `AssertionError` として `FAILED` に記録される。child 起動や import error には到達しない。
- (c) `xdist_group` 非所属: 新 node には marker を付けない。既存の `:2167` runtime node は mutation expected node に使わない。

段4で、上記 script literal の helper module 名を旧 test module 名へ置換する mutation を DW-M01/M04/M08 に従って事前登録する。期待赤集合は上記 static node 1件に限定する。D452 の代替である「親の直接実測へ回す」は不要だが、親は別途 child import 経路の実測を行う。

### 既存 contract test

[`test_growth_test_holds_contract.py:1470-1500`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_growth_test_holds_contract.py:1470) は、旧 launcher の self-load 文字列を埋め込んでいる。

- `test_dev_waves_integration.py` 用の fixture は helper import へ更新し、期待値を self-load なしへ変更する。
- self-load detector の陽性ケースは別の synthetic source として残す。
- これは registry 変更ではなく、launcher 形状を検査する test fixture の更新である。

## 影響範囲

- 内部 consumer:
  - `_serve_child_main()` → `_run_long_path_serve_harness()` / `_serve_child_payload()`（現 `:2021-2037`）
  - `_run_contained_serve_child()` → `_serve_child_main()`（現 `:2052-2055`）
  - socket runtime test → `_run_contained_serve_child()`（現 `:2168-2169`）
  - result parser test → `_parse_serve_child_result()`（現 `:2010-2018`）
- 他ファイル:
  - `test_growth_test_holds_contract.py:1488-1496`: 上記の synthetic launcher fixture のみ改修。
  - `test_dev_waves_cli.py:24-30`: `_isolated_process_environment` 等の共有 test helper だけを importしており、影響なし。
  - `test_dev_waves_isolation_contract.py:30,151`: 対象ファイルと marker を AST 検査するが、新 static node は resource-free・ungrouped のため既存契約内。
  - grep 上、`_serve_child_main` 等の live consumer は上記以外にない。

### growth hold 影響ゼロ

[`growth_test_holds.py:115-564`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/growth_test_holds.py:115) の `_HOLD_ROWS` / `GROWTH_TEST_HOLDS` に `test_dev_waves_integration.py` の登録はない。

実装では次を一切変更しない。

- `_wrap_held_function()` [`:602-609`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/growth_test_holds.py:602)
- `enforce_held_functions()` [`:631-689`](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/growth_test_holds.py:631)
- registry、hold count、digest
- 恒久保留の新規登録

## 未解決の懸念

- temporary repository の生成を親へ移すことで、「fixture 生成も child 境界内であること」を socket test の暗黙契約と解釈するかは、段3で攻撃対象にする。必要なら fixture builder も helper 側へ移すが、その場合も integration module への逆 importは禁止する。
- helper の import 閉包に `test_dev_waves_integration` が間接的に入らないことを static に確認する必要がある。
- helper 側での argv parsing 失敗や `pytest.skip.Exception` が、現行と同じ structured `PASS/SKIP/FAIL` envelope になるかを実装後に確認する。
- D499 の item2 保留解除を今回の command が明示した、という段1解釈自体は段3・段4で再裁定する。
- 段5の実装子はコード・テストのみを編集し、docs編集と commit を行わない。