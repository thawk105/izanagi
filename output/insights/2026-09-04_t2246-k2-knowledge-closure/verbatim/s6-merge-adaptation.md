## 削除した行

```python
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
```

削除前の前後 3 行:

```python
    else:
        cfg = default_cfg(reflux=(a.reflux == "on"))
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    cfg, _knowledge_layout, knowledge_input = _prepare_knowledge_campaign(
        cfg,
        resolved_knowledge,
```

## 自己検査の結果

1. 残存箇所は次の 3 箇所です。

   - 1091 行目: `default_cfg`
   - 1418 行目: `run_one_iteration`
   - 1875 行目: `drive_iteration`

   `main()` 内の指定箇所だけが削除されています。

2. `main()` の `knowledge_input` を確認しました。205? Wait no. assignments at 2062 and 2105. Need exact line actual 2062 and 2105. It is assigned by `_prepare_knowledge_campaign` before each use, and the name remains unchanged. No undefined reference occurs.

3. `python3 -m py_compile orchestrator/campaign/p3_s4_loop.py` は終了コード 0 で通過しました。

4. 編集は指定行 1 行の削除だけです。行数は 2260 行から 2259 行になり、追加、置換、他ファイルの編集はしていません。git command も実行していません。

## 総括

`main()` 内の重複した環境契約束縛を 1 行削除しました。  
他の関数にある環境契約束縛は維持しています。  
`knowledge_input` の K2 配線と構文は保持されています。