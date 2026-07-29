実装完了しました。変更は指定された2ファイルだけで、commit はしていません。

- [codex_worker_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-b/tools/codex_worker_ledger.py:188)
  - R4: `cached_input_tokens > input_tokens` を `usage_cached_exceeds_input` として無効化。
  - 凍結 manifest schema の独立 strict parser を実装。未知 field、duplicate key、bool-as-int、件数・一意性・canonical UUID 等を検査。
  - R10: manifest 欠損・構造違反・空 sessions・rollout 欠損を `--strict` なしでも rc=2。
  - filename、raw `session_meta.session_id`、manifest の完全一致で選択。
  - R11: `--manifest` と `--cwd-contains` の併用を argparse rc=2。
  - R16: `job_id` / `attempt_index` を公開し、worklog は distinct `job_id` で集計。manifest 経路では prompt hash を計算せず `null` とし、retry lineage は job/attempt から設定。
- [test_codex_worker_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-b/orchestrator/tests/test_codex_worker_ledger.py:485)
  - M12〜M15 の指定 nodeid、P2、schema 負例、三者一致、複数 meta exact 選択を追加。
  - P2 は合成10 sessionで `10 / 434 / 2,757,982`、stage別値、JSON列、table header、issue順を golden 固定。

受理集合の変更：

- R4: 変更前は strict でも `input=100, cached=200, output=1` を受理し `cli_reported=-99`。変更後は usage を集計せず、issue を出して strict rc=2。非 strict は従来どおり診断出力モードのため rc=0だが、issue は必ず公開します。
- R10: 従来の cwd selector は非 strict で部分・空選択を rc=0にできました。新しい manifest selector は構造不正、manifest file欠損、空 sessions、三者一致する rollout 欠損を常に rc=2にします。manifest 未指定経路は P2 で不変を固定しました。

静的波及：

- Python caller／consumer は対象2ファイル外に見つかりませんでした。
- 単位A launcher は、凍結 schemaとcanonical filename/meta IDを正確に発行する必要があります。
- 将来の T-183 consumer は manifest 経路の `retry_group=job_id`、`retry_index=attempt_index`、`prompt_hash=null` を考慮する必要があります。
- 共有 fixture は変更せず、既存 `_materialize()` に任意の `meta_id` seamだけ追加しました。
- docs更新、A統合、R17実データ受入、変異matrix、repo全走、commitは親の担当として未実施です。

## 総括

- 実装: R4 / R10 / R11 / R16、凍結 manifest strict parser。
- 指定nodeid M12〜M15・P2直接実走: 5 passed。
- `orchestrator/tests/test_codex_worker_ledger.py` 全範囲: 103 passed。
- `check_codex_agents.py`: OK、`check_docs.py`: 違反なし、`git diff --check`: rc=0。
- 未了: 親担当のA統合・R17・変異・repo全走・docs・commit。
- 受理集合縮小: R4不整合usage、R10不完全manifest。manifest未指定経路は不変。