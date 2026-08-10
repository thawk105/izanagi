静的監査結論は **NO-GO**。pytest は実行していない。

## 1. 測定・導出

算術自体は正しい。

- raw JSON の `during` 最大値は `0.5889730539638549` 秒。
- `0.588973 / 7044 = 8.3613429869e-5` で、記載値と一致。
- `15 / 7002 / 8.3613e-5 = 25.6208...`。25.6 は丸め値。
- `8.3613e-5 × 25.6 × 4 = 0.008562...`、`0.0086` は上向き丸め。

ただし、次の重大な測定欠陥がある。

### 所見 M-01 — Major

`probe_under_load.result.json` の `cat-file --batch-check` 最大値 `0.588973` は、`cycle_index=3`・`running_pytest_workers=0` のサンプルだった。pytest worker が存在するサンプルの最大値は `0.445290`。`during_samples_with_workers=445/450` で、全サンプルが負荷中ではない。

さらに `load_pytest_rc=1`、`load_result_is_acceptance=false` であり、受入全走の緑証拠ではない。

影響: `RATE=0.0086` は「pytest 全走負荷中の最大値」から導出された値ではなく、受理集合を根拠以上に広げる可能性がある。

### 所見 M-02 — Major

`25.6倍` は、15秒で打ち切られた単一観測から得た下界であり、尾部分布・p99・上側信頼限界ではない。したがって §5 の「25.6倍を全 kind に適用」は、代理シナリオとしては読めるが、全 kind の尾部遅延を保証しない。

特に pack 再配置、pack-index lock、特定 object の cold miss、filesystem metadata storm が `rev-list` / `log` だけを直撃する場合、`cat-file` の倍率から導いた「6.9倍余裕」は崩れる。

影響: `rev-list` や `log` が合法入力を固定15秒で `git-timeout` にし、赤が別の caller へ移る可能性が残る。

### 所見 M-03 — Major

byte 支配の `cat-file --batch` は、M2 では小さい4 blobだけを測っている。16 MiB / 32 MiB fixture は M1 の合成負荷であり、pytest 全走下ではない。実装の予算は要求数だけなので、4 request の合法な大 blob は約15.0344秒にしかならない。

影響: 大 blob の byte-specific な遅延が発生すると、既存の `blob-byte-limit` を満たす入力でも再び timeout しうる。

### 所見 M-04 — Minor

要求数の正本が不一致している。

- 段4・テスト: 7,005
- `MEASUREMENT.md`: 7,044
- raw JSON: candidate 2,348 commits × 3 paths = 7,044
- 現在の HEAD 直評価: 2,347 × 3 = 7,041

実装式は stdin を実際に数えるため本番計算自体は追随するが、テストの `real-invariant-r` は実 workload を検証していない。

影響: 実際の予算より最大 `39 × 0.0086 = 0.3354` 秒小さい測定・テスト証拠になる。

## 2. 本番 `_git` 予算

旧値は全て15秒。

| production caller | R | 新予算 | 分類 |
|---|---:|---:|---|
| `_assert_repository_safe`、`resolve_commit`、`rev-list`、`log`、`ls-tree`、`prepare_revision` | 0 | 15.0秒 | 据え置き |
| `read_blob_at` の `cat-file --batch-check` | 1 | 15.0086秒 | 増加 |
| `_batch_oids`（現HEAD） | 7,041 | 75.5526秒 | 増加 |
| invariant candidate / raw probe | 7,044 | 75.5784秒 | 増加 |
| `_batch_blob_bytes`（現測定の4 OID） | 4 | 15.0344秒 | 増加 |
| `_batch_oids` / blob batch | 33,140以上 | 300秒 | CAP |
| `MAX_BATCH_REQUESTS=50,000` | 50,000 | 300秒 | CAP |
| 50,001以上 | 超過 | `batch-request-limit` | Git実行前拒否 |

`R=MAX_BATCH_REQUESTS` 超過時の拒否順序は維持され、予算が旧15秒未満になる入力は見つからない。

## 3. 境界入力

- `stdin=None` → 15.0秒
- `stdin=b""` → 15.0秒
- 1行、末尾LFなし1 fragment → 15.0086秒
- `MAX_BATCH_REQUESTS` 行 → 300秒
- `MAX_BATCH_REQUESTS+1` 行 → helper単体では300秒、`_batch_oids` では事前に `batch-request-limit`
- `MAX_GIT_INPUT_BYTES=16 MiB` ちょうど → 許可、予算はCAP
- 16 MiB超過 → 旧来どおり `git-input-limit`、予算計算前に拒否

予算面の受理集合拡大は、明示された R1(a) / R2(b) の s8c `_git` 時間ゲート内には収まる。ただし `read_blob_at` の `path` はLFを拒否しないため、将来 caller が複数 batch 行を埋め込める残余はある。

## 4. 下流成果物

`CORE_MODULE_PATH` は [s8c_preregistration.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:41) 自身であり、現在の module bytes は変更されている。

再確認結果:

- 現在の module SHA: `29ee1b...`
- HEAD の module SHA: `f1359b...`
- `FROZEN_MANIFEST` に s8c module の pin はない。
- 現在の `condition-freeze.v1.g1.json` は契約値のみで module digest を持たない。
- 現 tree に有効な activation report / trial ledger / acceptance receipt の module digest はない。

したがって、現に repo にある凍結成果物の不整合は確認できない。ただし外部・一時保存された旧 activation report を再利用すれば `core-blob-mismatch` または activation digest 不一致になる。

## 5. 依頼達成度

段4の切り分けは妥当。`tools/ruleops.py` は固定20秒・stdinなしで別設計が必要であり、T-698も独立原因なので本 wave外にした判断は正しい。

ただし本 wave自身も、修正後の受入全走を示していない。M2 は実装前走行であり、`s8c` invariant が通ったことは修正効果の証拠ではない。`ruleops`、T-698、未測定の稀な tail により、producer / pilot の安定緑は未確認である。

## 総括

**NO-GO。**

M2 の最大値は実際には pytest 無負荷サンプルだった。  
25.6倍は尾部分布ではなく、全 kind への一般化は保証にならない。  
無 stdin caller は稀な command-specific timeout で赤が残りうる。  
byte-heavy batch も十分な負荷下測定がない。  
要求数は 7005 / 7041 / 7044 で資料が不一致。  
現凍結成果物の literal pin 不整合はない。  
ruleops と T-698 の別起票は妥当だが、受入全走の緑は未証明。