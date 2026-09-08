実装を完了し、指定された 3 file だけを変更しました。commit、add、stash は行っていません。

## 変更内容

- [s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-author/orchestrator/campaign/s1_direct_comparison.py:162): `+17/-3`、変更 20 行
  - `PreparedCell` 末尾へ contract field を追加。
  - oracle PASS 後の `contract_id` を保持。
  - sort_best のみ `resolve_evidence(..., sort_oracle_contract_id=...).src_token` を使用。
  - contract が非 None の場合だけ `evaluate` kwargs へ転送。
- [test_s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-author/orchestrator/tests/test_s1_direct_comparison.py:703): `+164/-3`、変更 167 行
  - M1からM6、非 sort 経路、REJECT 後の非呼出を固定。
  - `_capture_prepare_quarantine` に記録型 `resolve_evidence` double を追加。
- [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-author/orchestrator/tests/test_s8b_oracle_manifest.py:89): `+1/-1`、変更 2 行
  - materializer sha256 literal だけを更新。

## 受理・拒否挙動

受理する入力は変わりません。sort_best comparator が oracle PASS なら prepare は成功し、PASS 済み contract ID で token が束縛されます。  
拒否する入力も変わりません。oracle REJECT、contract ID 不一致、未知 status、allowlist 逸脱は従来の DriverError または RuntimeError のままです。

scope 前は全 cell が `source_digest.resolve()` を使い、evaluate に sort contract は渡されませんでした。scope 後は非 stock の sort_best token だけが sort contract の domain-bound hash へ変わり、variant_id、WAL、build cache が同じ ID に束縛されます。stock/inert sort_best は binder 規約により `STOCK` のままです。backoff_fixed_best、stock_common および他 configuration の token と evaluate kwargs は変わりません。

freeze の正常な sort_best cell では、`PreparedCell.sort_oracle_contract_id == ORACLE_CONTRACT_ID`、token は契約付き `resolve_evidence` の戻り値となり、run_role も同じ ID を evaluate へ渡します。

## 検査結果

- `python3 -m py_compile` 対象 3 file: rc=0
- `git diff --check -- <3 files>`: rc=0
- `sha256sum orchestrator/campaign/s1_direct_comparison.py`:  
  `79086a6c09da7ba548e24d1106c51ad89d305b180932b10d5429f9885fb5967e`
- `git diff --name-only`: 指定された 3 file のみ
- `rg` と AST による caller 検査: 全 `PreparedCell` 構築で位置引数は最大 4 個。末尾 field 追加による対応ずれなし。
- pytest: sandbox 制約により実装済み・未実走。`tools/run_tests.py` は既知の rc=16、直接の pytest は guard 対象のため実行していません。

materializer sha256:

- 旧: `049642ca067d93b046df66b14ddfdda3782bb06c830f2803c71e0e60e42f316d`
- 新: `79086a6c09da7ba548e24d1106c51ad89d305b180932b10d5429f9885fb5967e`

## 静的波及調査

`PreparedCell` の全構築箇所を列挙しました。

- production: `s1_direct_comparison.py:937`、`s8b_oracle_driver.py:1731`
- 当該 test: `test_s1_direct_comparison.py:239,545,584,619,640,718,1846,1960`
- consumer tests:
  - `test_s8b_predicate_build_proof.py:46`
  - `test_s8b_floor_campaign.py:428,2351,6732`
  - `test_s8b_materialization.py:64,541`
  - `test_s8b_freeze_io.py:378`
  - `test_s8b_expected_materialization.py:384,446,480,518,573,611`
  - `test_s8b_oracle_driver.py:2201,4608`
  - `test_s8b_ratified_freeze.py:456`
  - `test_s8b_oracle_n_pilot.py:631`
  - generated-source sentinel: `test_ccbench_spawn_sites.py:2883`

共有 fixture は新 field を省略すると従来どおり None になります。`resolve()` と `resolve_evidence()` の public signature は変更しておらず、既存 33 caller file の呼出形への影響はありません。

所有外の残余として、[test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2327-author/orchestrator/tests/test_sort_swo_oracle.py:2689) は旧 `resolve` だけを double にし、旧呼出順序を期待しています。新しい sort_best 経路では `resolve_evidence` double への追随が必要になる可能性が高く、親の実走対象へ含めるべき consumer test として記録します。

## 総括

- sort_best の token、variant identity、WAL、build cache を同一 contract ID へ束縛しました。
- 非 sort configuration と既存の受理・拒否集合は維持しています。
- 指定 3 file の構文、差分、sha256 pin は検査済みです。
- pytest は実装済み・未実走で、所有外 consumer test 1 件に静的な追随候補があります。