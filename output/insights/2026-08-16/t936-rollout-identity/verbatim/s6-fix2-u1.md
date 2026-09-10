## 総括

fix 2 巡目を実装し、GAP 2 形はいずれも `RC_SESSION`・候補数 2 の拒否へ閉じました。  
repo 外 probe は 6/6 `OK`、非空文字列の `session_id` fallback も維持しています。  
pytest は Pegasus の dispatch preflight 障害で起動できず、**実装済み・未実走**です。  
指定された 2 ファイル以外は編集せず、commit も行っていません。

## 所見対応表

| GAP | 状態 | 結果 |
|---|---|---|
| `[{}, PP, CP]` 対 `[PP]` | closed | `RC_SESSION`: `rollout count is 2, expected 1` |
| `[{"session_id":7}, PP, CP]` 対 `[PP]` | closed | `RC_SESSION`: `rollout count is 2, expected 1` |

partial / regressed はありません。

## 実装した変更

- [_rollout_matches_session](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:283)
  - `id` の有無に応じて候補値を選択。
  - 候補が非空 `str` の場合だけ own を確定。
  - 未確定行は全フラグと `saw_determinable` に寄与しないよう共通化。

- [回帰テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2479)
  - 空 payload 先頭行の回帰。
  - 数値 `session_id` 先頭行の回帰。
  - 既存テストの期待値は変更していません。

## 実走結果

repo 外 `check_gap.py`: rc=0、6/6 `OK`。

1 巡目で OK だった 4 形も同 probe で確認しました。

- null-id 先頭: 候補数 2 で拒否。
- 非 dict 先頭: 候補数 2 で拒否。
- fork 子 `[CP, PP]`: 親候補から除外され、親 rollout を一意選択。
- 逆順 fork 子 `[PP, CP]`: 候補数 2 で拒否。

追加確認:

- `session-id-only`: `OK`
- `reordered-keys`: `OK`
- 上記 fallback probe: rc=0
- 2 ファイルの AST parse: rc=0
- `git diff --check`: rc=0

pytest は次の nodeid 群を runner に渡しましたが、`qstat -Q` preflight 失敗により本体は未起動でした。

- 新規回帰 2 node
- `test_find_rollout_session_meta_encoding_and_payload_identity_semantics`
- 1 巡目の 4 形に対応する既存 node 群

実走 nodeid: なし。`tools/run_tests.py` の rc=16。したがって **実装済み・未実走**です。

## 波及の静的列挙

- `_rollout_matches_session` の直接 consumer は `_find_rollout` の eligible pin 候補確認と通常全走査です。
- 間接 consumer は `derive_independent_golden`、`render_prompt`、thread rollout の検証経路です。
- `_session_meta_rows`、`_find_rollout` の走査・件数検査、pin fast path、SHA 検査、消費側は未変更です。
- docs、`output/**`、その他 production、既存期待値には触れていません。

## 残る不確実性

pytest の新規・既存 node および全体回帰は、Pegasus の dispatch infrastructure 復旧後に親による再走が必要です。repo 外 probe は production の判定を直接確認していますが、pytest 受入の代替にはしていません。