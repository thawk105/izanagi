段5 author 実装を完了しました。production、docs、output、submodule は変更せず、commit も作成していません。

変更内容:

- [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1182) のみ変更
- `daemon_mod.select` binding だけを module-local proxy 化
- target thread、listener identity、readers/writers/errors、位置引数 timeout `0.25` を固定
- foreign call は保存した実 `select.select` へ委譲
- 順序付き観測、専用 timeout／shutdown-ignore sentinel、全出口 cleanup を実装
- outcome 観測後に thread を回収し、その後で patch を復元
- long-path node の固定 `join(120)` と wall-clock `is_alive()` assertion を除去
- daemon、real exchange、serve例外回収、capability probe、xdist marker、T-136 契約は維持

テスト結果:

- focused 3 node: `2 passed, 1 skipped`

  - `test_socket_roundtrip_works_beyond_108_byte_repository_path`: capability不足により正規 skip
  - `test_short_alias_bind_probe_separates_capability_loss_from_regression`: PASS
  - `test_every_node_that_touches_process_external_resources_stays_serialised`: PASS

- isolation meta-test 全体: `3 passed`
- proxy 単体 probe: target/foreign、`None`・巨大有限 timeout、park/release、shutdown-ignore sentinel の計6検査 PASS
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: PASS

赤の内訳:

- 裸の `pytest` は環境側の Python 3.9 を使用し、既存productionの `match` 文でcollection error。正規の `python3 -m pytest`（Python 3.10）で再走し、failure 0。
- 初回の一時 proxy probe は不正な空 readers を渡したため shape sentinel が発火。production同形へ修正した probe は PASS。scope外修正なし。

静的な波及可能性:

- 所有外 caller: node 実行中の `Supervisor.serve_forever()` のみ。foreign thread/call は実selectへ委譲。
- 共有fixture: 変更なし。
- consumer test: isolation meta-test が `daemon_mod`／thread 使用と既存xdist markerの対応を引き続き検査。
- 標準 `select.select` 属性、T-136の定数・state/reason/side-effect assertion、fixture/hash、揮発payload期待値は未変更。

## 総括

- 変更ファイル: integration test 1ファイルのみ
- 実装: plan v2 の test-owned deterministic shutdown harness
- 結果: focused `2 passed / 1 capability skip`、関連検査すべて成功
- 残リスク: sandbox制約によりreal long-path roundtripは未実走。capabilityのある親受入環境での再走とmutation matrixが必要です。