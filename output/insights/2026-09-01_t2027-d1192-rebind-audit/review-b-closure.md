## 所見

### 1. must-fix: oracle の descriptor 経路へ current masstree root が届かない

- 要約: `s8b_oracle_driver` が descriptor だけを注入し、`current_compiler_input_masstree_root` を供給しないため、FetchContent 入力を持つ v2 cache hit は必ず失敗する。
- 失敗シナリオ: fresh build は origin root を current root の代用にして v2 entry を発行できる。しかし次に同じ entry を選ぶと current root が `None` のまま `_validate_v2_entry` へ入り、`fetchcontent-masstree` entry が `current FetchContent masstree root is required` で拒否される。
- 根拠:
  - oracle wrapper は descriptor だけを追加する: [s8b_oracle_driver.py:1186](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_oracle_driver.py:1186)、[s8b_oracle_driver.py:1221](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_oracle_driver.py:1221)
  - pipeline の `common` に current root はない: [pipeline.py:1055](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/pipeline.py:1055)
  - descriptor は external policy を必ず有効にする: [buildcache.py:2952](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:2952)
  - fresh のみ origin fallback がある: [buildcache.py:2613](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:2613)
  - hit は caller の current root をそのまま渡す: [buildcache.py:2467](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:2467)
  - validator は current root 不在を拒否する: [s8b_compiler_input.py:916](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:916)
- 全件確認方法: `rg` で `expected_materialization_descriptor` の production 全参照を抽出し、AST で `build_v2` の直接 call と `**kwargs` wrapper を照合した。descriptor production consumer は floor とこの oracle wrapper の2系統だけだった。
- 成果物影響: cached oracle build が abort し、該当 cell の certified oracle observation とその proof 参照を生成できない。
- scope: `s4-adjudication.md` が限定した8ファイルの外だが、D1192 の「run 間の cache 再利用」を反証するため must-fix。

### 2. must-fix: floor の current root 供給が `sort_best` の同居に依存する

- 要約: production `build_cells` に non-sort cell だけを渡す経路では dependency root が作られず、fresh build 後の receipt 発行すら失敗する。
- 失敗シナリオ: dependency の準備条件は `cells` 中に `sort_best` があること。non-sort-only 呼出しでは descriptor build が origin fallback で v2 manifest を作れるが、receipt issuer へは `None` が渡り、FetchContent entry が拒否される。
- 根拠:
  - dependency 作成条件: [s8b_floor_campaign.py:4050](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_floor_campaign.py:4050)
  - current root は dependency がある場合だけ build へ渡る: [s8b_floor_campaign.py:4216](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_floor_campaign.py:4216)
  - 全 cell は descriptor build: [s8b_floor_campaign.py:4275](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_floor_campaign.py:4275)
  - receipt も dependency がなければ `None`: [s8b_floor_campaign.py:4374](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_floor_campaign.py:4374)
- 成果物影響: non-sort-only production materialization は binary admission receipt を発行できず、certified 選択は0件になる。
- scope: 裁定対象の `s8b_floor_campaign.py` 内。official full-floor は常に `sort_best` を含むため今回の31件主経路には発火しないが、公開されている production 経路の閉包は閉じていない。

### 3. nit: 7件クラスの境界を固定する v2 regression test がない

- 要約: 現行コードは7件を正しく救わないが、`/scr/0_<jobid>.nqsv/{gflags,glog}-install/...` を直接モデル化した test がない。
- 失敗シナリオ: 将来 `filesystem` 分類や current-root canonicality が変更されても、この scope 境界を専用 node が捕捉しない。
- 根拠: collector は snapshot・masstree のどちらにも属さない絶対 path を `filesystem` と `/` 相対 path にする: [s8b_compiler_input.py:1028](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:1028)。validator は `/` から同じ job-id path を再 hash する: [s8b_compiler_input.py:925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:925)。`test_s8b_compiler_input.py` 全文を `gflags-install|glog-install|0_.*nqsv` で検索したが該当0件。
- 成果物影響: 現時点の成果物値への影響はないため nit。
- scope: 専用 test の追加は裁定の「7件を実装しない」と両立する。

## 呼び出し閉包

`rg` の3引数全参照と、`collect_compiler_input_manifest`、`validate_compiler_input_manifest`、`build_v2`、`_build_v2_impl`、`_validate_v2_entry`、`issue_binary_admission_receipt` の AST call/definition を `orchestrator/**/*.py` 全件で照合した結果:

- `origin_fetchcontent_masstree_root`: build 後の CMake metadata resolverから collector まで閉じている。
- `current_fetchcontent_masstree_root`: collector 自己検証、fresh再検証、cache-hit再検証、receipt issuer内部まで閉じている。
- `current_compiler_input_masstree_root`: `build_v2 -> common -> _build_v2_impl -> hit/fresh validator` と、official full-floorの build/receipt は閉じている。
- 未閉包は上記2経路: oracle descriptor consumer、sortを含まない production floor。
- fake/fixture は、変更対象の `_fake_build_environment`、`_make_fake_build`、collector fake、issuer spy が新引数または `**kwargs` を受ける。v1 fixture の省略は optional 引数とv1 read-only互換で妥当。

## 31件クラス

official full-floor では救われると判定する。

1. full cell 集合に `sort_best` があるため共有 dependency root が作られる。
2. その root は全 cell の build kwargs に入る。
3. descriptor により external policy が有効になる。
4. build 後の `CMakeCache.txt` と `DependInfo.cmake` から origin masstree rootを解決する。
5. origin 配下の入力を `fetchcontent-masstree` と根相対 pathへ分類する。
6. fresh、cache hit、receipt の全境界で共有 current rootへ再束縛する。

CMake predicate は、現行コードが測定済みと記す CMake 3.22.1/3.25.0・現行 pin・Unix Makefiles の値域と一致している: [buildcache.py:1041](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:1041)。実走はしていない。

## 7件クラス

救われない。`filesystem` entry の path は先頭 `/` を除いた `scr/0_<jobid>.nqsv/...` として残り、旧 job directory 消失後の live hash で構造化拒否される。current masstree rootへの誤った再束縛は起きない。これは裁定どおり。

## Cache identity

`compiler_input_manifest_schema` は `source_snapshot_sha256` を持つ全 v2 identity に追加される: [buildcache.py:1317](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:1317)。

- invalidation 範囲: 全 snapshot-bound entry。floor の全 cellと、descriptorを注入する oracle の trace/perf entry。snapshotを持たない通常の `build_v2` entryは不変。
- 旧 entry は削除されず、新 digest から到達不能になる。
- schemaが一定で current/originの絶対 rootはpreimageに入らないため、正常にcurrent rootを供給する経路では再buildはschema移行時の1回だけ。
- ただし所見1の oracle 経路はidentityではなくlive validationでhitを拒否するため、実効的には「run間の再利用を失わない」を満たさない。

## Consumer test

`s8b-compiler-input/v1` を含む test file 8本を全件確認した。いずれも legacy completion分離またはportable receipt互換のfixtureであり、v1維持で妥当だった。更新漏れは、所見1を捕捉すべき `test_s8b_oracle_driver.py` の descriptor付きcache-hit testと、所見2のnon-sort-only floor testである。既存のreal-build oracle canaryは descriptor wrapperを通さず、fresh buildを1回だけ見るため取り残しを検出しない: [test_s8b_oracle_driver.py:5970](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_s8b_oracle_driver.py:5970)。

## 総括

- must-fix:
  - oracle descriptor consumerへcurrent rootを供給する。
  - non-sort-only production floorでもcurrent rootを確立するか、その経路を明示的に禁止する。
- nit / backlog:
  - 7件クラスのjob-id path消失を固定するv2 regression test。
- 31件: official full-floorでは救われる。
- 7件: scopeどおり残り、黙って受理されない。
- 親への反証: 「official full-floorの31件を救う」は支持する。一方、D1192全体の呼び出し閉包とrun間cache再利用が完成したという解釈は、oracle経路により反証される。
- pytestは実行していない。所見は静的検査のみ。