修正対象は [mutation_harness.py](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/mutation_harness.py:613) のみです。

### parser 修正

- ANSI 除去後、各行先頭の dispatch wrapper `| ` を除去。
- `FAILED` と `ERROR` の両方を解析。
- ` - ` があれば手前、なければ末尾空白を除いた行末までを node として記録。
- 期待 node と観測 node は従来どおり `_normalize_node()` で同形式に正規化。
- failure record に `outcome`、`node`、`assertion` を保存。

### `PARSE_FAILED`

[整合検査](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/mutation_harness.py:641)を追加しました。

- `rc != 0` かつ node が空
- `rc == 0` かつ node が存在
- timeout でないのに rc が取得不能

これらは `PARSE_FAILED` とし、全 raw 出力を台帳へ保存して現行変異列を停止します。HEAD baseline でも同様に M6 を実行せず停止し、M6 HEAD 自身の不整合も `PARSE_FAILED` になります。

### M6 HEAD 対照

既存 raw 台帳では、実際には以下が確認できました。

- `head_rc=1`
- `head_injection_verified=true`
- `t249-mutation-head/tools/pegasus/policy.json` に `7200→7199`
- dispatch receipt も `t249-mutation-head` 配下
- 期待された T-139／T-126 の2 node が実際に赤

したがって変異先・cwd・復元時期は正しく、`SURVIVED: green/none` の直接原因は parser でした。

加えて HEAD baseline は未初期化 submodule による別赤があったため、[HEAD worktree 準備](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/mutation_harness.py:871)で `--no-fetch` の cache-only 初期化と marker 検査を追加しました。M6 HEAD kill には2 nodeだけでなく、両方の sha256 assertion marker も要求します。

### 静的検査

- `python3 -m py_compile mutation_harness.py`: 成功
- harness／pytest 本走: 未実施
- repo HEAD: `4abe245`
- repo tree: clean
- commit・docs・repo ファイル変更: なし

## 総括

parser と HEAD 対照の修正は完了しました。
既存 raw 出力上、M6 HEAD の2 node は正しく赤でした。
ただし修正版 harness の本走は親担当のため、M6 結果はまだ採用可能とは報告しません。