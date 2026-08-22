結論として、変更対象は [tools/hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/tools/hold_inventory.py:110) と [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/test_hold_inventory.py:446) の2ファイル בלבדです。guard 実装や受理集合は変更しません。

### 1. `hold_inventory.py` の変更案

`known-resolved-bypass` を採用します。既知の迂回経路自体は inventory に残し、現在の実効結果だけを `effect` で示せます。`known-guarded-bypass` も考えられますが、未解決／解決済みの状態遷移が明確な前者を推奨します。

| entry・現行アンカー | classification | effect | reason |
|---|---|---|---|
| `plain-python-runner` (`:110`, `:112`, `:113`) | `known-resolved-bypass` | `rejected-by-hold-guard` | `import-time hold guard rejects manual plain-runner execution` |
| `pytest-noconftest` (`:118`, `:120`, `:121`) | `known-resolved-bypass` | `rejected-by-hold-guard` | `import-time hold guard rejects pytest without suite conftest` |
| `pytest-confcutdir-below-suite` (`:126`, `:130`, `:131`) | `known-resolved-bypass` | `rejected-by-hold-guard` | `import-time hold guard rejects pytest when confcutdir is below suite root` |
| `direct-test-function-call` (`:136`, `:138`, `:139`) | `known-resolved-bypass` | `rejected-by-hold-guard` | `import-time hold guard rejects direct import before the call-time wrapper runs` |

`id`、command/option/invocation、`tracking: "T-930"`、transport 2 entry は維持します。

### 2. golden copy の追随

`_expected_inventory()` の以下を上記4行に合わせます。

- `:446`, `:448`, `:449`
- `:456`, `:458`, `:459`
- `:464`, `:468`, `:469`
- `:476`, `:480`, `:481`

`test_inventory_projects_exact_registered_source_sets` の `bypass_by_id` assertion も同一値へ変更します。

- `:595`, `:597`, `:598`
- `:603`, `:605`, `:606`
- `:611`, `:613`, `:614`
- `:619`, `:621`, `:622`

`_expected_human()`、JSON schema、hold registry の件数・hash、release/status の期待値には追加変更は不要です。

### 3. 参照漏れ

静的検索で、現行の実行系 consumer は次の範囲に限定されます。

- `tools/hold_inventory.py`
- `orchestrator/tests/test_hold_inventory.py`
- `growth_test_hold_inventory()` は source inventory provider だが、今回の literal を持たない
- `test_growth_test_holds_contract.py` は guard 契約を検査するが、今回の metadata を参照しない

旧 `known-unresolved-bypass` は `docs/archive/` の過去 worklog にもありますが、当時の状態を記録する履歴であり更新しません。現行 docs に同じ literal の consumer はありません。

### 4. D347/D360 と decisions 追記

追記不要です。

- D347 は `bypass_surface` の構造と、未解決経路を未解決と明示する契約を定めており、literal 値を固定していません。今回の変更はその正確性を回復します。
- D360 は対象4経路を import-time／call-time の二層 guard で拒否する設計正本です。今回の変更は D360 の実装を反映するだけです。
- D503 の `call-only` 残余は今回の4 entryには該当しません。

### 5. guard 不変条件

変更不要です。[test_s8b_repo_scan_invariant.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/test_s8b_repo_scan_invariant.py:55) は既定の `import-and-call` guard を使用し、import 時拒否が発火します。`_wrap_held_function` の call-time 拒否は、import guard を免れた場合の防衛線として残ります。

pytest は実行していません。結論は指定資料・静的検索・コード経路の確認だけに基づきます。

## 総括

1. 4 entry を `known-resolved-bypass` / `rejected-by-hold-guard` へ更新する。
2. golden copy と `bypass_by_id` assertion の同一8箇所を追随させる。
3. guard、registry、受理集合、transport entry は変更しない。
4. 現行 consumer・D347/D360 は整合し、decisions/doc の追記は不要。