# [T-1034] usage dominance fixture の過剰決定 — 変異台帳と検出力の純増

## 何が起きていたか

`tools/claude_session_ledger.py` の相 2a は、cross-file replica を結合してよいかを次の短絡連鎖で
決める。

```
structurally_valid = bool(
    _is_canonical_message_id(value)
    and all(request["message_ids"] == {value} for request in requests)
    and len(request_id_sets) == 1
    and common_structure_is_valid(group)   # ← usage dominance はこの中の最後
)
```

`orchestrator/tests/test_claude_session_ledger.py` の 2 テストは、fixture の `message.id` に
`msg-incomparable` / `msg-shared-but-requests-differ` を使っていた。本番が要求する canonical 形は
`msg_[A-Za-z0-9]+` (`_CANONICAL_MESSAGE_ID`) であり、どちらも合致しない。したがって**連鎖の
先頭で False が確定し、テストが主張していた理由 (usage dominance の不成立 / requestId 集合の相違) は
一度も評価されていなかった**。

両テストは緑だったが、緑の理由は主張と違っていた。D376 が定めた usage dominance が壊れても
気づけない状態である。

## 実測 (2026-08-13、Pegasus 計算ノード)

tracked file を一時変異して即時復元する経路 (DW-O19) で挟み込んだ。

| # | 変異 | 対象 | 結果 |
|---|---|---|---|
| 1 | `_dominates` → `return True` | incomparable 4 param | 4 passed = 生存 |
| 2 | #1 + `_is_canonical_message_id` → `return True` | incomparable 4 param | 4 failed = kill |
| 3 | `_is_canonical_message_id` → `return True` のみ | incomparable 4 param | 4 passed |
| 4 | `len(request_id_sets) == 1` → `True` | different_request_ids | 1 passed = 生存 |

\#2 と #3 の差が「正規形検査を外すと dominance だけが唯一の理由として残る」ことを示す。
\#3 が通ることは、fixture を canonical にしても本番の判定が依然 fatal であること
(= 期待値の緩和にならないこと) を示す。

## 是正

fixture の `message.id` を canonical 形へ差し替えた。期待値 (`rc == 2`、`message_id_collision`、
`model_calls == 0`) と production は変更していない。併せて、拒否 detail が
`fatal: message_id_collision: <id>: ...` (相 2a) であることを検査する assertion を足し、
component 段の `replica component: ...` と区別できるようにした。

## 検出力の純増 (DW-M08 の新旧両走)

runner 範囲は `orchestrator/tests/test_claude_session_ledger.py` 全体。

| 変異 | wave 前 `734c03a1` | wave 後 `7ad74525` |
|---|---|---|
| MUT-A (`_dominates` → `True`) | KILLED / 失敗 node 1 件 (`test_cross_bucket_replica_is_attributed_to_root_once`) | KILLED / 失敗 node 5 件 |
| MUT-B (`len(request_id_sets) == 1` → `True`) | **SURVIVED** / 失敗 node 0 件 | KILLED / 失敗 node 1 件 |

純増した検出 node は 5 件。

- `test_incomparable_usage_replicas_remain_fatal[cache_creation_input_tokens]`
- `test_incomparable_usage_replicas_remain_fatal[cache_read_input_tokens]`
- `test_incomparable_usage_replicas_remain_fatal[input_tokens]`
- `test_incomparable_usage_replicas_remain_fatal[output_tokens]`
- `test_same_message_and_usage_with_different_request_ids_remains_fatal`

両走とも `tools/mutation_harness.py` (旧版は `tools/mutation_worktree.py --commit` 経由) の
`--runner-mode dispatch` で回し、期待 node の完全一致で `KILLED` を判定している。
台帳は `mutation-ledger-new.json` / `mutation-ledger-old.json`、spec は
`mutation-spec-new.json` / `mutation-spec-old.json`。

## 一般化できること

「fixture が本番の形式検査を通らない合成 ID を使うと、意図した gate へ到達する前に落ちる」
という型である。テストは緑のまま、意図した不変条件を 1 度も検査しない。本 wave では同一ファイル内で
独立 2 件が再現した。producer が 1 つなので族一般化 (DW-G03) の条件は満たさず、機械検査の新設は
していない。同型を疑うべき場所は、合成 ID や合成 path を fixture に置き、本番側にその形式検査が
あるテスト全般である。
