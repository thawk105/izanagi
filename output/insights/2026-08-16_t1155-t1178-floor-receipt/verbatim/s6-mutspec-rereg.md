1. [mutation-spec-2.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/mutation-spec-2.json) を書き出した。

   - `swo.identity-external-binding-drop`: `expected_nodes` 6 件
   - `admission.campaign-filter-drop`: `expected_nodes` 4 件

   root・mutation・replacement の exact-key 契約を `jq` で検証した。`expected_nodes` 以外の mutation fields と root scalar は元 spec と同値で、JSON は valid UTF-8 である。

2. 新 spec から全 10 nodeid を `jq -r '.mutations[].expected_nodes[]'` で抽出し、各行を `grep -Fqx` で `nodes.txt` と完全一致照合した。欠落は 0 件だった。

3. `configuration_id-stock_common` は、テストが receipt の値を `stock_common` に変更する一方、validator が外部期待値との比較前に `_validate_identity()` を呼ぶため発火しない。[s8b_sort_swo_receipt.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:225) から始まる receipt 内部 identity 検証が、`configuration_id != "sort_best"` を [s8b_sort_swo_receipt.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:103) で先に拒否する。変異対象の外部期待値比較はその後の [s8b_sort_swo_receipt.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:231) にあるため、この parametrization は当該変異に対して単一理由ではない。

## 総括

書き出し済み。訂正後の件数は 6 件と 4 件で、全 nodeid の実在を確認した。

発火しなかった理由は、外部束縛より先に portable receipt 内部の `sort_best` 固定 identity 層が拒否するためである。