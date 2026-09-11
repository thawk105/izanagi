## 総括

所有ファイル `orchestrator/manual_probes/test_t2397_a1_source.py` のみ、8行追加しました。

- `PBS_JOBID` 不在時、既存 `require_local_attempt_marker` に dispatcher の両 helper を渡して検証し、実 ID を probe・依存 staging に共有します。
- 通常 dispatch は従来どおり。marker 欠落・不正は拒否し、既存の検査・期待値・bench 禁止は不変です。
- 所有外への波及は、依存 staging が検証済み ID を継承する点です。共有 fixture・dispatcher・他テストは未変更です。

差分の空白検査は通過。**実装済み・未実走**で、正例・負例の実動作確認は親に委ねます。文書・過去出力の変更、add・commit・submit は行っていません。