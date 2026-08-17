## 変更

- [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:571)
  - `GuardMode` と exact 2 literal、既定値 `import-and-call` を追加。
  - held 関数の wrap 後にのみ call-only を判定。
  - pytest 由来 stack、および非委譲 `__main__` は従来どおり拒否。
  - `@wraps` と exact-token 解除契約は維持。

- [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:608)
  - loader path、`runpy`、nested subprocess、package self-import、`exec(open(...))` の静的 self-load 判定を追加。
  - full path 同一性、import alias、一意な代入、解決不能時の fail-closed を実装。
  - exact keyword 順序、runner 3 族、pre-guard alias 禁止を検査。
  - [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1122)で現行 held file 13 面と実 `test_check_docs.py` の foreign-loader 陰性を固定。
  - [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1396)以降に署名、未知 mode、import 成功後の呼出拒否、pytest/main 拒否の正負 controls を追加。

## 実走

pytest と nodeid は未実走です。したがって passed/failed 数、緑、closed は申告しません。

許可された静的確認のみ実施しました。

- 2 ファイルの `compile(..., "exec")` / AST parse: 成功
- 静的 import と契約解析: 成功
- registry: `count=59`、指定 key SHA 一致
- held file: 13、全既存 binding が `errors=0, self_load=False`
- 実 consumer 2 件は陽性、実 `test_check_docs.py` は陰性
- `git diff --check`: 成功

## 波及

- 現行 13 module の kwarg 無指定 caller は既定 mode により従来経路を通ります。
- `conftest.py` の enforcement session と collection skip は未変更です。
- `inspect.unwrap` を使う contract test と `test_real_repo_serialization.py` は、既存 `@wraps` 維持により影響を受けません。
- `hold_inventory.py`、59 rows、13 held files、登録済み test source は未変更です。
- 将来 call-only binding を追加する caller は、self-load の静的証明と pre-guard alias 不在を要求されます。

## 残件

- 親担当の pytest 実走、変異検査、docs fragment、commit は実施していません。
- `test_s8b_floor_campaign.py` と `test_dev_waves_integration.py` の実 registry 登録は段 4 の scope 外として未実装です。
- 既存の未追跡 `output/insights/2026-08-17_t1226-hold-guard-callonly/` は触れていません。
- dev-wave 段 5 の境界に従い、指定外ファイルと docs は編集していません。

## 総括

call-only の import 許可機構と狭い拒否条件を実装しました。  
held 関数の呼出防壁と exact-token 解除口は維持しています。  
self-load 選別、alias 禁止、foreign-loader 陰性を静的契約へ組み込みました。  
registry 59 件、digest、held file 13 面は不変です。  
実装済み・pytest 未実走です。