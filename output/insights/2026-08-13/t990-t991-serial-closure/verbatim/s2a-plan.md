## 依頼 1 — 閉包の残件

結論は **(b)**。独立した第 4 系統はない。レンズ A の「実 git object を書く node」は、系統 2 の linked worktree 管理領域変更を広く言い換えたものと判断する。

根拠は次のとおり。

- `patchharness.applied()` は `git apply` を `--index` なしで実行し、source working tree だけを変更する（`orchestrator/campaign/patchharness.py:193-199`）。終了時の `git checkout -- .` は working tree を index へ戻し、必要な index lock は取り得るが、blob/tree/commit を `.git/objects` へ生成しない（`:202-238`）。
- `patchharness.checkout()` の `git worktree add --detach` は既存 commit を checkout するだけで、新しい Git object は作らない（`:291`）。一方、実共有 common-dir 配下には linked worktree の管理ディレクトリ `worktrees/<id>/`、`HEAD`、`index`、`gitdir`、`commondir`、関連する per-worktree log/ref を登録し、linked tree 側には `.git` gitfile と checkout 済みファイルを作る。
- `git worktree remove --force` は linked tree と `worktrees/<id>/` の登録を削除する（`:302`）。失敗時の `git worktree prune` は stale な同登録を削除する（`:304`）。いずれも object database への書込みではないが、共有 common-dir の明確な変更である。
- これは親が確定した次の 2 node の競合面そのものである。

  - `test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`（`:3455`）
  - `test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration`（`:3498`）

  両者は `s1_direct_comparison.py:527` から実 `external/ccbench` を `base_dir` にして `checkout()` を呼ぶ。
- `test_hooks.py::test_real_submodule_payload_edit`（`:773-790`）は実 `backoff.hh` を読み、`GW.decide("Edit", …)` に編集候補文字列を渡して許否を検査するだけである。Edit 実行、ファイル更新、index 更新、object 生成はない。この node は「実 source reader」として既に正本に入っている。

したがって、`git worktree add/remove/prune` の管理領域変更が系統 2、「実 Git object writer」は該当なしであり、追加の node は不要である。

### 系統 1 の差集合

`test_s1_measurement_freeze.py` で `freeze_env` または `real_known_axes_doc` を直接引数に取る test は 11 件だった。

- `:111` `test_generate_builds_registered_cells_comparisons_and_schedule`
- `:146` `test_generate_refuses_existing_freeze`
- `:153` `test_verify_rejects_one_byte_freeze_tamper`
- `:168` `test_verify_rejects_one_byte_workload_flag_tamper`
- `:181` `test_verify_rejects_stats_implementation_tamper`
- `:190` `test_verify_rejects_known_axes_material_tamper`
- `:199` `test_schedule_is_balanced_and_reproducible`
- `:216` `test_recorded_ccbench_pin_hold_and_release_positive_control`
- `:232` `test_s1b_pairing_rejects_mismatched_flags`
- `:243` `test_build_document_rejects_tampered_known_axes_semantics`
- `:262` `test_receipt_exists_but_measurement_verify_stays_legacy_strict`

`conftest.py:196-205` の正本との差集合は次のとおり。

- fixture 集合 − 正本:
  `test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control`
- 正本内の同ファイル 10 node − fixture 集合: 空集合

### 系統 3 の件数

`benchmark_snapshots` を直接引数に取る top-level test 関数は静的 AST 検査で **17 件**。関数名集合は `parent-findings.md` の列挙と完全一致し、過不足はない。

以上より、限定された点検範囲では親の閉包漏れは正確に **1 + 2 + 17 = 20 node** である。

実装時の再発検査は `test_real_repo_serialization.py` に置き、次の AST 由来集合が正本の部分集合であることを検査する。

- `freeze_env` / `real_known_axes_doc` 消費 test
- `benchmark_snapshots` 消費 test
- 実 `ROOT/external/ccbench` と `prepare_cell` を同じ test 経路で使用する canary

正本集合を引数に取る assertion helper を分離し、導出済み node を 1 件除いた集合を渡す positive control で必ず赤になることも検査する。履歴や commit 数には依存させない。

## 依頼 2 — optional lock

### 確定表

| 候補 | 現状 | 受入全走で候補行を実行 | 裁定 |
|---|---|---:|---|
| `orchestrator/tests/repo_tree_util.py:20-27` | `env` 未指定 | はい。`test_s8b_protocol_builder.py:431-444`、`test_ruleops.py:3276` から実 repo に対して実行 | 是正 |
| `orchestrator/campaign/source_digest.py:761-770` | `env` 未指定 | はい。`test_campaign.py:9217-9261` 等の `resolve()` 経路が実行 | 是正 |
| `orchestrator/campaign/silo_ladder_rung1.py:963` | `_run()` の scrub 済み env | いいえ。受入中の直接呼出しは absent-root 異常系だけで、status より前に停止 | 今回は除外 |
| `orchestrator/campaign/silo_ladder_rung1.py:2084` | 同上 | いいえ。実 build/correctness command 用で、受入 test から到達しない | 今回は除外 |

`_ENV_ALLOW_EXACT`（`silo_ladder_rung1.py:117-124`）に `GIT_OPTIONAL_LOCKS` は含まれない。さらに `_ENV_FORBIDDEN_PREFIXES` に `GIT_` があるため、allowlist へ名前だけ追加しても `scrub_environment()`（`:306-320`）で落ちる。

一方、`_run()` の `env = scrub_environment()` の直後に `env["GIT_OPTIONAL_LOCKS"] = "0"` を設定すれば、その辞書は後段の `subprocess.run(..., env=env)` へ再 scrub なしで渡るため有効である。ただし今回、その方法が必要な 2 本の status は受入全走から到達しないので、`silo_ladder_rung1.py` は最終是正リストから外す。将来 production 経路も同じ規律へ揃える場合は、allowlist を広げず `_run()` の scrub 後に固定値を注入する。

### 規律 2 への影響

`GIT_OPTIONAL_LOCKS=0` によって新たに「dirty なのに clean」となる条件はない。

抑止されるのは、`git status` が検査中に更新した stat cache を on-disk index へ書き戻す副作用である。working tree と index の比較および status 出力を作るための in-memory refresh は行われる。書込みコマンドに必要な mandatory lock も抑止されない。

`assume-unchanged`、不正な fsmonitor、同一 stat tuple を意図的に再現した変更など、Git 一般の別要因による見逃し可能性はあるが、optional lock の有無とは独立である。

重要な fails-closed 消費箇所は次のとおり。

- `repo_tree_util.py:78-91`: action 前後の porcelain bytes を比較し、status 自体の失敗は `RepoTreeSnapshotError` にする。
- `source_digest.py:770-776`: status の非 0 終了を拒否。
- `source_digest.py:833`: tracked path を allowlist 検査へ渡す。
- `source_digest.py:852-861`: status の clean/dirty と full tracked diff hash の整合も検査する。

したがって、今回の変更は正しさゲートを緩めず、検査コマンド自身の index-lock churn だけを除去する。

### `test_t810_validator.py:401`

このテストは外部環境から `GIT_DIR`、`GIT_INDEX_FILE`、`GIT_OPTIONAL_LOCKS=1` を注入し、それでも repository snapshot が別 repo へ誘導されず安定することを検査している。その後、実 `.git/objects/info/alternates` の追加は snapshot 差として検出されることも確認する。

SUT の `_git()` は危険な Git 環境変数を除去したうえで `GIT_OPTIONAL_LOCKS=0` を明示的に上書きしている（`orchestrator/campaign/t810_validator.py:334-354`）。今回の 2 ファイルの変更とは独立しており、期待値変更は不要。むしろ同じ「親環境の `"1"` を信頼せず `"0"` へ固定する」形に揃う。

### 是正の最終リスト

1. `orchestrator/tests/repo_tree_util.py:20-27`

Before:

```python
return subprocess.run([...], cwd=str(root), ..., check=True).stdout
```

After（この `env` を `subprocess.run(..., env=env)` に渡す）:

```python
env = os.environ.copy()
# Git status の optional index refresh lock を抑止し、実 repo writer と競合させない。
env["GIT_OPTIONAL_LOCKS"] = "0"
```

`import os` も追加する。

2. `orchestrator/campaign/source_digest.py:761-770`

Before:

```python
r = subprocess.run(["git", "-C", sub, "status", "--porcelain"], ...)
```

After（同じ `env` を呼出しへ渡す）:

```python
env = os.environ.copy()
# Git status の optional index refresh lock を抑止し、共有 source writer と競合させない。
env["GIT_OPTIONAL_LOCKS"] = "0"
```

対応する回帰テストでは親環境を `"1"` にして runner の `env["GIT_OPTIONAL_LOCKS"] == "0"` を確認する。既存の status 内容・fails-closed assertion は変更しない。

## 実装順序

段 5 の author 1 本は次の順序で編集する。

1. `orchestrator/tests/conftest.py`
   - 20 node を追加。
   -既存 node は削除しない。
   - 誤った writer コメントを実装上の reader/実資源依存へ修正。
   - slow canary の除外註記から「共有管理領域を変えない」という誤った含意を除く。
2. `orchestrator/tests/test_real_repo_serialization.py`
   - 独立 golden に同じ 20 node を追加。
   - fixture/call/path から導出する閉包検査と、1 node 欠落の positive control を追加。
   - `test_codex_reasoning_ab.py` 自体は編集しない。
3. `orchestrator/tests/repo_tree_util.py`
   - `os.environ.copy()`、理由コメント、`GIT_OPTIONAL_LOCKS=0`、`env=env` を追加。
4. `orchestrator/tests/test_s8b_protocol_builder.py`
   - 親の `"1"` が `"0"` へ上書きされる runner-capture 回帰テストを追加。
5. `orchestrator/campaign/source_digest.py`
   - `_tracked_status_paths()` に同形の env 設定を追加。
6. `orchestrator/tests/test_campaign.py`
   - status runner の env、出力解析、既存 fails-closed 挙動を同時に確認する回帰テストを追加。

`orchestrator/campaign/silo_ladder_rung1.py`、`orchestrator/tests/test_codex_reasoning_ab.py`、`tools/codex_reasoning_ab.py` は本案では編集しない。

## 未確認のまま残した点

40-call 上限による打切り項目はない。sandbox が read-only という指定に従い、pytest・受入全走・変異テストは実行していないため、緑は主張しない。

## 総括

独立した第 4 系統はなく、親の 20 node は過不足なし。optional lock の今回の是正対象は、受入全走で実際に到達する `repo_tree_util.py` と `source_digest.py` の 2 箇所に限定する。`GIT_OPTIONAL_LOCKS=0` は status の意味を変えず、optional な index 書戻しだけを抑止するため、規律 2 を緩めない。