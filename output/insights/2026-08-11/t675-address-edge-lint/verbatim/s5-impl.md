実装は完了し、変更は指定された2ファイルだけです。commit／git add／docs変更は行っていません。

### 実装内容

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076)
  - cleanup command 限定の1分岐を frontmatter 解析前へ追加。
  - `_visible_dispatch_inventory_text(...).splitlines()`、ASCII lookaround の `F26`、backtick 込み exact path を使用。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6717)
  - 負例4本、正例2本を追加。
  - 負例は合成 checker の digest のみ再束縛し、違反1件かつ digest finding 不在を検査。
  - [meta-test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:2876) に6テスト名を登録。

現行は interface 契約と whole-file SHA pin（[check_docs.py:4511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4511)）だけだったため、digest 再束縛後の4偽edgeを受理していました。今回の拒否集合追加は指定された cleanup command の address edge だけです。

### 検査結果

緑:

- `python3 tools/check_docs.py` — 違反なし
- `python3 tools/check_codex_agents.py` — OK
- AST parse、`git diff --check`
- 実 command SHA-256 は `a92d960c…22e3` のまま

pytest は以下7 nodeidを `tools/run_tests.py` 経由で2回投入しましたが、いずれも実行前に rc=16 で停止しました。実走範囲は0件です。

```text
test_cleanup_address_edge_rejects_split_lines
test_cleanup_address_edge_rejects_substring_decoys
test_cleanup_address_edge_rejects_raw_html_block
test_cleanup_address_edge_rejects_link_definition
test_cleanup_address_edge_accepts_rewording
test_cleanup_address_edge_accepts_baseline
test_dev_wave_new_gate_case_registration_is_complete
```

原因は login headroom が約1.73 GBで予約2 GiB未満、かつ sandbox 内の `qstat -Q` が `NQSconnect errno 1` となり dispatch 不能だったためです。したがって、揮発する digest を実際に変更する p1 を含め、状態は「実装済み・未実走」です。pytest assertion の赤は観測されておらず、残る赤は infrastructure rc=16だけです。

### 波及可能性

- production caller: `check_docs.main()`、`tools/task_run_check.py` の `docs-check`、`tools/dev_wave_land.py`、`tools/dev_waves/{cli,checker,daemon}.py`。
- 共有 fixture: `_build_min_repo()` は同テストファイル内で224箌所から利用されます。baseline edgeを保持しているため静的には既存consumerへの追加findingなしです。
- consumer test: `test_dev_wave_land.py`、`test_dev_waves_checker.py`、`test_dev_waves_integration.py`、`test_s8b_selector_output.py` が checker 経路へ到達し得ます。
- 親の未導入docs変更に起因する期待findingはありません。現状の `tools/check_docs.py` が緑で確認済みです。

## 総括

指定§2のみを2ファイルへ実装し、docs・pin・実command bytesは非接触です。  
静的checkerと構文・差分検査は緑です。  
指定7 nodeidは環境rc=16により未実走で、親の全走が必要です。  
commit／git addは行わず、作業ツリーに差分を残しました。