# レンズ C 敵対レビュー

静的レビューでは、正規の `ExecutionEnvironmentContract` を通る現行経路の受理・拒否・例外順序・戻り値は同値です。ただし、profile hash の正本が二重化され、将来の片側変更を防げなくなった must-fix が 1 件あります。

## must-fix

### C1. profile hash の canonicalization が二重実装されている

公開側は [env_attestation.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:840)–850、leaf 側は [calibration_verify.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:29)–38 に別実装されています。今日はいずれも `dataclasses.asdict` → `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)` → SHA-256 で同値です。

しかし `VerifiedCalibration` の生成と自己検査は leaf 側だけを使います（[calibration_verify.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:56)、[calibration_verify.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:141)）。既存テストは一つの fixture について両者を比較するだけで（[test_env_attestation.py:1111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1111)–1117）、非 ASCII、将来追加される field、値依存の canonicalization 変更などの片側 drift を構造的には防ぎません。

leaf に公開 `profile_sha256` を一つだけ置き、`env_attestation.profile_sha256` を同じ関数への alias/delegationにするべきです。少なくとも関数同一性を固定するテストも必要です。

**成果物影響:** 片側だけ変わると、execution receipt が記録する leaf hash（[execution_guard.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/execution_guard.py:488)）と T-126 の公開側 hash 経路（[t126_driver.py:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/t126_driver.py:453)–454）が異なる正本を参照し、比較 verdict が同じでも proof hash が分岐します。silo の `runtime_modules_sha256` は両 module の bytes を pin するだけで、両 hash 値の意味論的一致は証明しません。

## should-fix

なし。

## nit

### N1. 公開 class の defining module は変わる

`AttestationError` と `VerifiedCalibration` は leaf で定義され（[calibration_verify.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:25)、[calibration_verify.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:41)）、[env_attestation.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:53) と [env_attestation.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:107) で同一 object が再公開されています。このため `except` / `isinstance` は保たれますが、`type(x).__module__` と新規 pickle の qualified path は変わります。

**成果物影響:** 列挙した caller に introspection/pickle 利用はなく、certified 選択結果・レポート・試行台帳の現行値には影響しません。

## 挙動同値性の突合

旧実装は [s5-impl.patch:245](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5-impl.patch:245)–320、現実装は wrapper と leaf に分かれています。正規 contract に対する検査順は次のとおり一致します。

1. contract 型検査  
   wrapper の最初の処理として維持されています（[env_attestation.py:1029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1029)–1034）。

2. `repo_root` 型 → strict resolve → relative path → strict artifact resolve → `relative_to(root)`  
   [calibration_verify.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:91)–104。catch 対象と例外文言も旧実装と同じです。

3. artifact read → bytes SHA 照合  
   [calibration_verify.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:105)–114。SHA より前に schema や mode を判定する経路はありません。

4. `attestation_mode="required"`  
   schema → `env_tag` → `clocks_per_us` → effective-clock policy の順です（[calibration_verify.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:116)–142）。同じ validator・policy 定数を使い、`quality.status=accepted` の新規検査も足されていません。

5. `attestation_mode="none"`  
   grandfathered bytes SHA → duplicate-aware JSON parse → top-level `dict` の順です（[calibration_verify.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:144)–158）。定数値も同じです。

6. 未対応 mode  
   全 filesystem/SHA 検査後に同じ `AttestationError` 文言で拒否します（[calibration_verify.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:159)）。

したがって、正規 contract/artifact の複合不正でも「先に出るエラー」は旧実装と同じです。

## 一回読みと TOCTOU

artifact bytes を読む箇所は [calibration_verify.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:106) の一箇所だけです。同じ `raw` が SHA、v2 validator、v1 JSON parser に渡されます。wrapper は filesystem を読みません。

既存の swap-after-read テストも変更されておらず、二度読みまたは parse 時の再読を検出する構造です（[test_env_attestation.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1181)–1197）。

## 公開 alias と全 caller

本番の直接 caller は次の 7 箇所で、検索上の漏れはありません。

- [loop.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/loop.py:86)
- [t126_driver.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/t126_driver.py:441)
- [s8b_floor_campaign.py:2762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2762)
- [s8b_oracle_driver.py:789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_driver.py:789)
- [s8b_oracle_report.py:1230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1230)
- [s8b_ratified_freeze.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1820)
- [silo_ladder_rung1.py:1940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:1940)

各 `except env_attestation.AttestationError` は再公開された同一 class を捕捉します。戻り値側も `execution_guard` の `isinstance`（[execution_guard.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/execution_guard.py:125)、[execution_guard.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/execution_guard.py:456)）を通ります。field、frozen dataclass、property の挙動は旧定義と同じです。

## `env_contract` import 閉包

leaf のローカル import は `effective_clock_policy` と `schema_v2` だけです（[calibration_verify.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:13)–14）。

間接閉包も以下で閉じています。

- `campaign/__init__.py`: executable import なし。
- `calibrator/__init__.py`: executable import なし。
- [effective_clock_policy.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/effective_clock_policy.py:3): `typing` のみ。
- [schema_v2.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/schema_v2.py:10)–17: stdlib のみ。

直接・間接とも `campaign.env_contract` への辺はありません。fresh-process 検査も追加されています（[test_env_attestation.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1093)）。

## 事前登録 6 変異の kill 対応

| 変異 | 落とす nodeid | 静的な落ち方 |
|---|---|---|
| M1 SHA 恒真化 | `orchestrator/tests/test_env_attestation.py::test_leaf_rejects_sha_mismatch` | 例外が出ず失敗 |
| M2 path 封じ込め除去 | `...::test_leaf_rejects_repo_escape` | 通過または後段の別エラーとなり、要求した `repo_root 外` に一致せず失敗 |
| M3 env_tag 照合除去 | `...::test_leaf_rejects_contract_cross_field[env_tag-other-env]` | 例外が出ず失敗 |
| M4 clock 照合除去 | `...::test_leaf_rejects_contract_cross_field[clocks_per_us-1801]` | 例外が出ず失敗 |
| M4 policy 照合除去 | `...::test_leaf_rejects_effective_clock_policy_mismatch` | 例外が出ず失敗 |
| M5 wrapper 委譲除去 | `...::test_load_verified_calibration_delegates_raw_values_to_leaf` | spy が呼ばれず sentinel/引数表が不一致 |
| M6 runtime 閉包から除外 | `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_runtime_binding_covers_all_execution_semantics_modules` | exact path set が不一致 |

従って、静的には落とせない事前登録変異はありません。g1/94a4 の過剰拒否は `test_leaf_accepts_both_registered_pegasus_calibrations` が担当します。

## テストの緩和有無

テスト差分は `test_env_attestation.py` が `+129/-0`、`test_env_contract.py` が `+7/-0`、silo test が `+1/-0` です。既存 assertion の反転・削除、skip/xfail の追加はありません。

既存期待値の変更は runtime module exact-set への leaf 追加（[test_silo_ladder_rung1_driver.py:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_driver.py:926)–948）のみで、実装側の閉包追加（[silo_ladder_rung1.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:254)–272）と対応しています。`V2_ENV_NEUTRAL_MODULES` も検査対象を増やしており、緩和ではありません。

pytest・変異実験は read-only sandbox のため一切実走しておらず、緑は主張しません。

## 総括

1. **挙動同値性は保たれている。** 正規 contract/artifact に対する受理集合・拒否集合・検査順・例外・戻り値・一回読みは同値。ただし profile hash の単一正本性は破れており、C1 は land 前の must-fix。

2. 事前登録した 6 変異のうち、静的に落とせないものはない。M1〜M6 の全てに対応 nodeid があるが、実際の kill は未実測。

3. 親は C1 を単一 hash 実装へ直した後、`tools/run_tests.py` 経由で上記 nodeid、`test_env_attestation.py` 全体、全 7 caller の consumer tests、g1/94a4/v1 正例を実走し、その後 M1〜M6 を実際に適用して kill を確認すべきである。