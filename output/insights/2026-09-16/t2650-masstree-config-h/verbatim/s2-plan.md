## 現状の配線 (file:line)

以下の `campaign/` は `orchestrator/campaign/`、`tests/` は `orchestrator/tests/` を指す。行番号は現在の worktree 基準。

| 区間 | 現在の値と経路 |
|---|---|
| campaign → prebuild | `campaign/s8b_floor_campaign.py:4281–4295` で staging または明示指定から `fetchcontent_base` を取得し、`_prepare_floor_oracle_dependency` へ渡す。 |
| prebuild の入力 | 同 `3395–3426` の `effective_base` と `staged_sources` から、base と masstree・mimalloc・googletest の3 source dir を `prepare_kwargs` に入れる。 |
| CMake define の生成 | `campaign/buildcache.py:2051–2072` が prefix、base、3 source dir を configure argv にする。`dependency_prefix` は床値側から渡しておらず、同 `2034` の既定 `""`。したがって現行床値の対象 token は **4本**。 |
| prebuild の実行 | 同 `2090–2096` で configure と既存の `masstree_build` を実行。返却値の `configure_argv` は同 `2101–2105` にあるが、床値側 `3426` は返却値を保持しない。 |
| binding の返却 | `campaign/s8b_floor_campaign.py:3456–3482` が `_FloorOracleDependencyBinding` を返す。同 `2129–2147` の dataclass は masstree の `source_root` 等を持つが、gate configure 引数や他2依存の source dir を持たない。 |
| oracle 用コピー | 同 `3477` → `3261–3327` は `oracle_root` 等を追加する。`source_root` は保持される。gate に渡すべき staged source と oracle 用コピーは区別する。 |
| cell の prepare | 同 `4290` の `dependency_binding` → `4344–4356` の closure → `4359–4362` の `_prepared_binding` → `campaign/s8b_materialization.py:128–136` → `prepare_cell`。 |
| prepare → gate | `campaign/s1_direct_comparison.py:836,966–971` → 同 `298–309` の `capture_define_inputs` → `campaign/condition_meaning_gate.py:1697–1707` の実 configure argv。受け口は既にある。 |

## 欠陥が生じている正確な地点 (file:line)

情報が落ちる地点は2つある。

1. `campaign/s8b_floor_campaign.py:3421–3426` で使った3 source dir を、同 `3469–3482` の返却 binding に保持していない。
2. 同 `4349–4356` の `prepare_fn` 呼び出しが `condition_configure_args` を渡していない。その結果、`campaign/s1_direct_comparison.py:836` の `()` が gate まで届く。

`external/ccbench/cmake/ThirdParty.cmake:57–78` は `config.h` を build 時生成物として宣言し、同 `85` がその source dir を include path にする。gate 側は `campaign/condition_meaning_gate.py:1703–1715` で configure するため、prebuild 済み source dir の明示指定が必要である。

## prebuild の適用範囲 — 全 cell か sort_best 限定か (行番号で確定)

**`sort_best` を含む本番 campaign で、cell ループ前に1回実行される。各 cell ごとの実行ではない。**

- 本番判定は `campaign/s8b_floor_campaign.py:4215` の `prepare_fn is prepare_cell`。
- prebuild に入る条件は同 `4259–4260` の `production_floor_path and any(... == "sort_best")`。
- prebuild 呼び出しは同 `4290–4296`、cell ループ開始は同 `4328`。
- binding がある場合の `floor_prepare` 適用は同 `4332`。**ここには sort 限定条件がない。**
- 同 `4334` の sort 限定条件は oracle marker 用。cell build の FetchContent 注入は別途、同 `4434–4473` で sort 限定。

したがって、`sort_best` と同じ campaign にある `backoff_fixed_best` には、共有 prebuild の base と3 source dir を gate 引数として渡せる。

一方、**非 sort cell だけの呼び出しでは現状 prebuild も binding も作られない**。今回の案ではこの適用範囲を広げず、その経路の引数は従来どおり空とする。既存 prebuild の配線修正と、非 sort 単独実行への prebuild 新設を混同しない。

## 実装プラン (file:line 粒度、変更順)

変更対象は `campaign/s8b_floor_campaign.py` と `tests/test_s8b_floor_campaign.py` の2ファイル。

1. **binding に gate 引数を保持する。**  
   `campaign/s8b_floor_campaign.py:2147` の dataclass 末尾へ、内部搬送用の `condition_configure_args: tuple[str, ...] = ()` を追加する。同 `2149–2193` の `cache_receipt()`／`private_dict()` には追加しない。

2. **既存 prebuild と同じ入力から引数を生成する。**  
   同 `3426` の prebuild 成功後に、`p3_s4_loop._condition_gate_offline_configure_args` を関数内の相対 import で再利用する。渡す値は以下に固定する。

   ```python
   dependency_prefix=prepare_kwargs.get("dependency_prefix", "")
   fetchcontent_base_dir=prepare_kwargs["fetchcontent_base_dir"]
   masstree_source_dir=prepare_kwargs["masstree_source_dir"]
   mimalloc_source_dir=prepare_kwargs["mimalloc_source_dir"]
   googletest_source_dir=prepare_kwargs["googletest_source_dir"]
   ```

   `oracle_root` からの逆算や環境変数からの補完は行わない。同 `3469–3476` の既存 `replace` で生成した tuple を binding に保持する。同 `3322–3327` の canonical materialization は `replace` なので、このフィールドも引き継がれる。

3. **全 cell の既存 closure から渡す。**  
   同 `4349–4356` に次の keyword を追加する。

   ```python
   condition_configure_args=_dependency.condition_configure_args
   ```

   同 `4332` の条件を維持し、sort 判定の内側へ移さない。同 `4434–4473` の build 引数生成は変更しない。

4. **既存 fixture を新しい引数に対応させ、回帰 test を追加する。**  
   `tests/test_s8b_floor_campaign.py:3565–3574` の `production_prepare` に明示的な `condition_configure_args` 引数を追加し、受け取った値を記録する。同 `3642–3685` の既存 assert はすべて維持する。追加 test の内容は次節。

## 足す test (関数名と assert の中身)

**1. `test_floor_prebuild_offline_tokens_reach_real_condition_gate_configure_argv`**

追加位置は `tests/test_s8b_floor_campaign.py:3804` の既存 prebuild test の後。

- 同 `3704–3787` の pinned checkout、staged sources、payload policy、materialization の fixture 構成を使う。
- `_prepare_floor_oracle_dependency` と `buildcache.prepare_masstree_fetchcontent` は実関数を通し、`buildcache._run` を記録用 stub にして prebuild configure argv を捕捉する。
- 同 `3532–3543` の campaign fixture を使い、`backoff_fixed_best` を先頭、`sort_best` を同じ `cells` に含める。
- fixture の backoff entry は、`campaign/s1_direct_comparison.py:902–908` を満たすように `BACKOFF_FIXED == backoff_us` とする。
- `prepare_cell`、`_condition_records_for_genome`、gate の configure argv 生成は実関数を通す。checkout／patch 適用を fixture に向け、`condition_meaning_gate._run_process` で最初の configure argv を捕捉して専用例外で停止する。先例は `tests/test_p3_s4_loop.py:8247–8284`。

対象 token は `CMAKE_PREFIX_PATH`、`FETCHCONTENT_BASE_DIR`、3本の `FETCHCONTENT_SOURCE_DIR_*` の5種類に限定する。実 prebuild の入力を使って `buildcache._v2_commands` でも比較用 configure argv を生成する。

```python
assert prebuild_call_count == 1
assert observed_configuration == "backoff_fixed_best"
assert len(observed_gate_argv) == 1
assert offline(gate_argv) == offline(prebuild_argv)
assert offline(gate_argv) == offline(campaign_argv)
assert len(offline(gate_argv)) == 4
assert offline_names(gate_argv) == {
    "FETCHCONTENT_BASE_DIR",
    "FETCHCONTENT_SOURCE_DIR_MASSTREE",
    "FETCHCONTENT_SOURCE_DIR_MIMALLOC",
    "FETCHCONTENT_SOURCE_DIR_GOOGLETEST",
}
```

`offline` は順序を保持した tuple として抽出し、集合一致に加えて重複も検出する。床値には明示 prefix がないため、先例の5本を機械的に要求せず、同 `8335–8369` の prefix なし先例に合わせる。

比較対象の `campaign_argv` は**同じ依存入力を渡した build argv 生成器の出力**であり、非 sort の実 build にその入力を新規注入するものではない。

**2. `test_floor_condition_configure_args_reach_all_cells_without_expanding_build_binding`**

追加位置は `tests/test_s8b_floor_campaign.py:3701` の後。同 `3530–3701` の `_freeze_document`、`_fixture_dependency_binding`、`_fake_prepare`、`_make_fake_build` を使う。

```python
assert events.count("prebuild") == 1
assert captured_prepare_args == {
    cell["cell_id"]: dependency.condition_configure_args
    for cell in cells
}
assert captured_prepare_args[backoff_cell_id] == expected_offline_args
assert sort_only_keys <= set(build_kwargs[sort_cell_id])
for cell_id in non_sort_ids:
    assert sort_only_keys.isdisjoint(build_kwargs[cell_id])
```

さらに既存 `test_floor_dependency_prebuild_uses_pinned_checkout_and_exact_helper_once` の `3788–3804` に、返却 binding の tuple が prebuild に渡した base／3 source dir と一致する assert を追加する。これで producer 側と全 cell への搬送を両方固定する。

## 先例との差分と、再利用か複製かの判断

先例は `campaign/p3_s4_loop.py:1914–1925` で receipt の有無に応じて生成器を呼び、同 `1935–1944` では同じ依存入力を campaign build に渡す。床値は binding が campaign 単位で存在する一方、実 build の FetchContent 注入は sort 限定なので、**gate の搬送範囲と build の注入範囲が異なる**。

import 方向について、`campaign/s8b_floor_campaign.py:138` → `s1_direct_comparison.py:842` → `p3_s4_loop` という既存経路がある。確認した `tests/test_campaign_import_invariant.py:31–37` は名前空間・相対 import 等の制約で、今回の module 間方向を禁止する規則は見つからなかった。

**判断は再利用を勧める。** `p3_s4_loop.py:346–376` の既存生成器を相対の関数内 import で使えば、新しい共通層や複製を作らず、既存の正規化・token 構成を床値にも適用できる。

## 触らない境界と、その根拠

- **gate の受理集合・reason code：** `campaign/s1_direct_comparison.py:331–350` の判定と理由生成、`campaign/condition_meaning_gate.py` の evaluator は変更しない。入力する依存パスだけを補う。
- **gate に build を追加しない：** 既存の build 起動は `campaign/buildcache.py:2073–2096` のまま。新しい `cmake --build` 起動点は不要。追加する案に変えるなら、`campaign/materializer_admission.py:52` の登録簿と `tests/test_s8b_floor_campaign.py:7793` の網羅 test に及ぶが、本案では変更しない。
- **非 sort の build binding：** `campaign/s8b_floor_campaign.py:4434–4473` と `tests/test_s8b_floor_campaign.py:3668–3685` を維持する。cache receipt・永続記録へのフィールド追加もしない。
- **既存期待値：** fixture の引数対応と assert の追加のみ。既存 assert の削除・緩和はしない。
- **`tools/pegasus/*.sh`：** 編集対象外。必要な値と受け口は Python 側に既にあり、shell 変更は不要。
- docs、commit、push、実装は今回実施しない。

## 未確認のまま残した点

- pytest、実 CMake、実前処理は未実行。上記は静的確認に基づくプランであり、`preprocess-failed` 解消の実測結果ではない。
- import 制約は既存経路と関連 checker の静的確認までで、変更後の import 実行は親の検証事項。
- 非 sort だけの campaign には prebuild がない。その経路の修復は本案に含めない。
- gflags／glog 等、実機 configure に必要な依存の充足は今回検証していない。

## 総括

共有 prebuild の入力から既存生成器で作った configure 引数を binding に保持し、全 cell の既存 `floor_prepare` へ渡す2ファイルの変更を提案する。これにより、sort を含む official campaign の非 sort gate にも prebuild 済み masstree を供給しつつ、sort 限定の build binding と gate の判定規則を維持できる。