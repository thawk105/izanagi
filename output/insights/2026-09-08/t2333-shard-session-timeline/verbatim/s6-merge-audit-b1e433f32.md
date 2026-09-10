## 総括

merge は実行せず、競合解決案と merge message を作成しました。

- [resolved-acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/resolved-acceptance_duration_ledger.json)
- [merge-message-t2333.txt](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/merge-message-t2333.txt)

commit・ref 更新・テスト実行はしていません。

## 自分で数えた merge 後の map の長さと導出

- base: 19541
- HEAD: 19557、base からの追加 16
- main: 19592、base からの追加 51
- 両側の追加 key の重複: 0
- merge 後: `19541 + 16 + 51 - 0 = 19608`

親の実測値 19608 と一致しました。両側とも削除および既存値の変更はありません。

解決 JSON の `nodeid_count` も 19608 です。`schema_version: 1` と `unit: "seconds"` は維持し、HEAD の整形規則を再現しています。

## 両側が同じ key を違う値で足していないかの確認

該当なしです。

- 重複追加 key: 0
- 異なる値を持つ重複追加 key: 0
- base 既存 key の値競合: 0

## 合成監査で見たものと結論

`240ee6360..b1e433f32` の変更 147 path を調べました。

main は次を変更していません。

- `tools/acceptance_shards.py`
- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_run_tests_shards.py`
- `session_timeline`
- `_REPORT_FIELDS`
- `pytest_collection_finish`
- shard report の schema・集約処理
- real-repo lock protocol
- 当 wave の追加テストが使う helper・fixture

`test_real_repo_serialization.py` の main 側変更は、S8C predicate snapshot の golden node 1件追加のみです。当 wave の helper、fixture、呼出し元との食い違いはありません。

実質的な交差は `acceptance_duration_ledger.json` のみで、上記の和集合として解決しました。

## merge message file の内容

```text
merge(main): 固定 SHA b1e433f32 を [T-2333] wave へ取り込む

local main b1e433f323706a74223929ad079a662ffb002819 の campaign、test、文書、insight 更新を取り込む。

acceptance_duration_ledger.json の競合は、base 19541 件に HEAD の追加 16 件と main の追加 51 件を和集合で残して解決する。重複追加、削除、既存値変更はなく、nodeid_count は map の実長 19608 に合わせる。schema_version と unit は維持する。

合成監査では、main が tools/acceptance_shards.py、orchestrator/tests/conftest.py、orchestrator/tests/test_run_tests_shards.py、および session_timeline、_REPORT_FIELDS、pytest_collection_finish、real-repo lock protocol の実装面に触れていないことを確認した。test_real_repo_serialization.py の差分は S8C predicate snapshot の golden node 1 件だけで、当 wave の helper、fixture、呼出し元との食い違いはない。

AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author; scope=merge
AI-Agent: product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator; scope=merge
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```