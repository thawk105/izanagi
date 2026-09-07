### 旧 root `kind` 負例が手前の別判定だけで FC07 になる

種別: refuted

根拠: [test_reflux_formal_consumer.py:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:304) の `_rewrite_wal()` は root の attempt、source bytes、projection hash、result digest を同期する。[reflux_result_evidence.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_result_evidence.py:594) は root attempt を受け、同 file:653-662 は object、attempt、source bytes の一致しか検査しない。[reflux_formal_consumer.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:727) の FC05C exact gate は trigger record だけに適用される。したがって [test_reflux_formal_consumer.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:843) の legacy terminal は前段を越え、[reflux_formal_consumer.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:868) の `stage == STAGE_ABORT` で初めて落ちる。この比較を除けば後続の root witness 条件も満たし、FC07 ではなく P6Unavailable に到達する。

影響: 負例は stage reader の回帰を実際に検出し、誤った FC07 report と null proof-chain 参照を見逃さない。

分類: nit

### `P6Unavailable` は commit 枝を通過した証拠にならない

種別: refuted

根拠: 正例は [test_reflux_formal_consumer.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:858) で physical result と ledger member を accepted に同期し、production 外枠の commit terminal を置く。accepted record は [reflux_formal_consumer.py:861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:861) の commit stage と verifier-order の両判定を必ず通る。[reflux_formal_consumer.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:1040) より前後の失敗は `FormalContractRejected` となり、`P6Unavailable` の生成は同 file:1072 の一箇所だけである。

影響: 正例は今回の修理による report reason の FC07 から P6_UNAVAILABLE への変化と receipt/proof-chain 参照の発行を固定する。

分類: nit

### witness mutation の payload 移動で既存テストが緩んだ

種別: refuted

根拠: fixture terminal は [reflux_origin_fixture_builder.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:376) で outer `{variant, stage, env_tag, ts, payload}` を持ち、witness は payload 内だけに存在する。更新後の [test_reflux_formal_consumer.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:922) と同 file:943 は、その実際に消費される payload 値を変更している。[reflux_formal_consumer.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:822) は root 優先だが、現 fixture の root に同名 field はないため、空 witness は同 file:874-879 で FC07、二番目の class は FC07 を通過後に同 file:902-919 で FC09 になる。

影響: 元の単一 witness 欠落と kmax 超過を捕捉する能力は維持され、report、台帳の期待 reason も変わらない。

分類: nit

### fixture が root fallback に隠れて payload 経路を検査していない

種別: refuted

根拠: [reflux_origin_fixture_builder.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:376) の terminal root には attempt、attribution、truncated、witness がなく、すべて payload にだけある。同 file:391-405 はこの record を変更せず projection へ入れる。[test_reflux_formal_consumer.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:423) の fixture 全体の正例が P6Unavailable へ到達するため、現物では `_wal_field()` の payload 経路が実際に通っている。

影響: fixture の経路変更で FC07 検査対象が失われた状態ではなく、report と receipt の基準入力は production-shaped terminal に同期している。

分類: nit

### terminal outer-shape gate がないため flat `stage` terminal も受理される

種別: real

根拠: [reflux_result_evidence.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_result_evidence.py:601) は canonical list を `wal.parse_line()` に通さず、同 file:653-658 も dict と attempt しか要求しない。[reflux_formal_consumer.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:822) は root field を優先し、同 file:858-879 は terminal の exact outer keys を閉じない。このため `{stage:"abort", build_attempt_id:..., candidate_attributable:true, truncated:false, witness_class_sha256s:[...]}` のような非 production flat record も通る。

影響: certified 選択値自体は変えないが、不正形状でも report reason が P6_UNAVAILABLE、receipt/evidence-root が実 digest となり、[reflux_origin_client.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_origin_client.py:249) から aborted terminal を台帳へ commit できる。

分類: scope 外・裁定パッケージ候補

### 親裁定 1〜5への逸脱または pin の誤計算がある

種別: refuted

根拠: 定数は [reflux_formal_consumer.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:35) から import され、変更は同 file:862/868 の二比較だけで、`_wal_field()` は同 file:822-826 のままである。abort producerも追加されず、production abort payload [pipeline.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/pipeline.py:1071) および同 file:1206-1215 には依然 witness fields がない。read-only の再計算結果は projection `975 / 271323...`、result `1848 / 631a5...`、outer `5aaf...`、wrong-domain `515e...` で、[reflux_origin_fixture_baseline.json:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_baseline.json:15) と [test_reflux_result_evidence.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_result_evidence.py:24) に全値一致する。

影響: accepted 側だけが FC07 を越え、rejected 側は裁定どおり FC07 に残る。fixture、report、台帳 digest の参照ずれもない。

分類: nit

## 総括

must-fix:

- 0件。

scope 内の実装、負例、正例、既存テスト、pin 同期に不整合は見つからなかった。親の焦点走も `687 passed`、新規二例も `2 passed` で静的結論と一致している。実在する所見は terminal exact outer-shape が未検査な点だけだが、親裁定 4 により明示的に scope 外である。