### RA1 — must-fix：TPC-C executor 試験の正例が認定されない

根拠: [test_campaign.py:7519](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7519)、[test_campaign.py:7557](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7557)。正例・存在違反例・witness 欠落例の key `district` は小文字・偶数桁の 16 進 key ではなく、`malformed_keys` により integrity が汚れます。正例の `certified` assertion は失敗し、witness 対照の「notes は不一致だけ」という assertion も失敗します。全ケースで key を有効な 16 進表現に直してください。

成果物への影響: 実装が正しくても試験は赤になり、TPC-C v3 が certified に届くという結合証拠を得られません。

### RA2 — must-fix：M8 は現状、受理集合の変化で kill されない

根拠: [test_campaign.py:7523](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7523)、[test_campaign.py:7560](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7560)、[pipeline.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:639)。v2 入力にも無効な `district` key があるため、M8 で v3 要求を除いても verifier が `indeterminate` として拒否します。現試験が検出するのは拒否理由の変更だけです。v2 入力を有効な key、witness、X/P 証拠を持つ認定可能な trace に直し、M8 適用時には `abort is None` に変わることを対照で確認してください。

成果物への影響: v2 TPC-C を誤って受け入れる変異が、事前登録された fail-closed の照準で検証されません。

## 総括

静的検査では、v3 要求は verifier の直後、certified 判定の前にあります。判定の `binary` は `_run_trace` に渡すものと同じで、`payload_binary` は使っていません。
v2 の射影は `result_to_dict_v3` 内で旧 `result_to_dict` のままです。変更した import に循環も見当たりません。
M1〜M7・M9・M10 の名指し試験は、それぞれ構造化出力・digest・受理集合の変更を検出する形です。M8 は RA2 のとおりです。M11 の試験にも、親が既に確定した欠陥があります。
allowlist 試験は実 `_run_trace` を通ります。executor 試験は `trace_runner` seam を使うため、両機構を一つの run で結ぶ証拠ではありません。
書き込みとテスト実測は行っていません。