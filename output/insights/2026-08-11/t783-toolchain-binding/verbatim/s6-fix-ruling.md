# 段 6 fix 裁定 — レビュー所見の real/refuted と分割

統合 snapshot = `snapshot-integration.patch` (退避済み、`DW-S06-B`)。
統合 commit = `0e11e68d` (単位 A) + `5256b96b` (単位 B)。

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| R1-1 | `expected_toolchain_manifest` が `version_first_line` だけを持つため、gate 後の**下位行 drift** を `build_v2` の再観測が受理する | **real / must-fix** | **採用** |
| R1-2 | wrapper (`_bind_current_toolchain`) の**投影配線**を弱める変異が殺せない (helper へ誤った値を渡す 1 行変異が生存) | **real / should → 採用** | **採用** (変異 matrix の射程に直結する) |
| R2-1 | `toolchain_binding.py` が `_runtime_module_paths()` の閉包に無く、silo evidence の `runtime_modules_sha256` が helper の bytes を束縛しない。exact closure test が漏れを固定して緑にしている | **real / must-fix** | **採用** |
| 既知赤 1 | `test_s8b_materialization.py::test_floor_manifest_golden_stable` が `build_cells` の新引数を渡していない | real | **採用** (親が所有を追加) |
| 既知赤 2 | `test_s8b_floor_campaign.py::test_deterministic_artifacts_across_roots_and_subprocess_environments` の subprocess 経路に fake が届かない | real | **採用** |

**refuted / 確認できた健全性** (レビューが積極的に確認した点、記録として残す):

- bool 述語の例外処理は **fail-closed** 方向 (`floor_toolchain_matches` は例外時 `False` → caller が raise)
- `_assert_official_permitted` の無条件拒否は維持。`run_campaign` の公開引数と injection 拒否列挙は基準 commit から**不変**
- `expected_toolchain_manifest=None` は短絡のみで **narrowing-only**
- gate 全削除は**恒真な緑ではない** (`build_cells` の binding 呼出しテストが赤になる)
- 静的には**恒真な赤でもない** (helper と wrapper の双方に正例がある)
- silo の受理集合は**不変** (first-wins と旧 5 条件が述語レベルで完全一致)
- `FROZEN_MANIFEST` 23 artifact の blob は基準 commit と HEAD で全一致。`floor_protocol.json` も不変
- manifest / result の top-level key 追加なし。既存テストの期待値反転・skip・削除・exact SHA 書換えなし

## R1-1 の修正方針 (親が指定する。実装子に選ばせない)

`_tool_version` / `_toolchain_manifest` の**戻り値を変えてはならない** — その値は
`_v2_identity` の preimage に入り、build digest と cache key を決めるため、
変えると**全 producer の identity が動く** (本 wave の scope 外)。

したがって次の形にする。

- `_bind_current_toolchain` は `build_v2` へ、`version_first_line` に加えて
  **version 全文を持つ別 key の期待値**を渡す。
- `build_v2` は `expected_toolchain_manifest` が渡されたときだけ、
  **identity 用とは別に全文を再観測**して全文一致を要求する。
- **`_v2_identity` の preimage には 1 bit も足さない。** 既定 `None` の挙動も不変のまま。

## 分割 (所有が素集合。並列投入可)

- **fix-A**: R2-1
  - `orchestrator/campaign/silo_ladder_rung1.py`
  - `orchestrator/tests/test_silo_ladder_rung1_driver.py`
- **fix-B**: R1-1 / R1-2 / 既知赤 1 / 既知赤 2
  - `orchestrator/campaign/buildcache.py`
  - `orchestrator/campaign/s8b_floor_campaign.py`
  - `orchestrator/tests/test_buildcache_v2.py`
  - `orchestrator/tests/test_s8b_floor_campaign.py`
  - `orchestrator/tests/test_s8b_materialization.py` (**親が段 6 で所有へ追加**。
    `build_cells` の署名が変わった以上 caller の追随は不可避で、
    段 4 の no-touch 裁定はこの追随を想定していなかった)

`toolchain_binding.py` は **fix-A も fix-B も編集しない** (単位 A で確定済み。
R1-1 / R1-2 は wrapper 側の問題であり helper の述語は正しい)。

## 変異事前登録の更新 (`DW-M01` / `DW-M02`)

R1-2 が「wrapper の投影配線が変異射程外」と指摘したため、変異表へ 3 件追加する。
また、**既存 campaign テストの autouse fixture (`test_s8b_floor_campaign.py:135`) が
実 gate を置換している**ため、helper だけを狙う変異は mask されうる (`DW-M02`)。
wrapper を通る変異を必ず含める。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M13 | `_bind_current_toolchain` の `live_cc_realpath=` 実引数 | `observed["cc"].realpath` → `receipt.toolchain.compiler_path` | KILLED |
| M14 | `_bind_current_toolchain` の `live_cxx_version=` 実引数 | `observed["cxx"].version` → `observed["cc"].version` | KILLED |
| M15 | `build_v2` の全文再観測比較 | 比較を削除 (R1-1 の修正箇所) | KILLED |
