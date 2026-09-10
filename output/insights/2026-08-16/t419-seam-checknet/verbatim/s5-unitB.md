現行受理: 現行 contract `e576e9cd…` に一致する legacy protocol を受理し、ccbench pin の不一致は選択条件にしません。  
現行拒否: contract 一致が exact 1 件でない場合、record 型不正、再読 SHA 不一致、current validation 不成立を fail-closed で拒否します。

実装内容:

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/campaign/s8b_floor_campaign.py:877) に `root` だけを受け取る resolver を追加。`IndexedFloorProtocol` を返します。
- [certified_writer_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/campaign/certified_writer_admission.py:206) から literal path を除去。record の path を再読し、SHA-256 照合後に同じ bytes を検証します。
- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_s8b_protocol_builder.py:945) に resolver 正例、API、0 件拒否、6 ファイルの literal 一致 meta-testを追加。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/tests/test_campaign.py:4983) に resolver 差し替え正例と bytes 差し替え負例を追加。

テスト状況:

- 次の 7 nodeid を `tools/run_tests.py` へ投入しましたが、pytest 開始前に `rc=16` で停止したため、すべて実装済み・未実走です。

  - `test_current_floor_protocol_resolver_selects_exact_index_record`
  - `test_current_floor_protocol_resolver_has_only_root_selection_argument`
  - `test_current_floor_protocol_resolver_rejects_zero_current_matches`
  - `test_floor_protocol_path_literals_match_current_resolver`
  - `test_floor_admission_uses_authority_resolver_not_legacy_literal`
  - `test_floor_admission_rejects_disk_bytes_different_from_index_record`
  - `test_p2_actual_floor_and_t126_admission_accept_valid_evidence`

- 原因は sandbox から login admission ledger を更新できず、dispatch 側も `qstat -Q: EACCTAUTH Unknown user-id` で停止したためです。テスト赤は観測していません。
- 単位 A の既知 4 件は走行対象外で、今回の結果には含めていません。
- 静的確認は `AST OK 4`、`git diff --check` 成功。新規 test 名に追加の hold 登録はありません。
- 凍結成果物、shell、照合対象の5 moduleは差分なしです。

波及可能性は `certified_writer_preflight.py` の floor 経路、共有 `certified_writer_fixtures.py`、`env_contract.lookup`、既存 floor admission 正例です。5 moduleとshellは配線変更せず、literal一致検査だけを追加しました。

## 総括

- current floor protocol resolver を唯一の index authority 上に追加しました。
- caller が選べる引数は `root` のみに固定しました。
- ccbench pin は選択条件に含めていません。
- admission の literal path を resolver record へ置換しました。
- index走査後の disk bytes を SHA-256 で再束縛しました。
- exact 0 件と不正状態は fail-closed です。
- 単位 A、docs、shell、凍結成果物には触れていません。
- テストは環境基盤の `rc=16` により未実走で、緑は申告しません。