---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1440-batch-oids-narrow
seq: 2
---

## {{D:batch-oids-narrow-verification}}. `_batch_oids` の narrow 漏れ疑いを実測で棄却し、経路別の回帰テストで確定する

**決定:**

1. D551 が narrow した `validate_condition_freeze_at` 経路 (`_commit_graph` 経由) に加え、
   `_batch_oids` のもう一つの呼び出し経路 (`_assert_rulings_exist`) も、世代数
   (`MAX_GENERATIONS=1024` 上限) にのみ比例し生の履歴 commit 数には非依存であることを
   実測で確認した。production コードへの追加 narrowing は行わない。
2. `test_batch_request_count_ignores_no_touch_history_length`
   (`orchestrator/tests/test_s8c_preregistration_core.py`) を拡張し、
   `_assert_rulings_exist` 経路の request 数が no-touch commit 数に依存しないことを
   generation2 fixture で固定した。新規テスト関数は追加しない。

**理由:**

- 発端になった受入失敗の実測 (50072 requests) の真因は、branch が D551 land
  (2026-08-19 12:51:11) より前の main (11:08:54) から分岐していたことだった。
  D551 の親コミット時点のコードと当該 branch の失敗 tip を使った独立の再現実験で
  50061 requests を再現し (元の実測値とほぼ一致)、「`_batch_oids` を通る他経路が
  履歴比例のまま残っている」という疑いは実測で否定された。
- `_batch_oids` の呼び出しは repo 全体で2箇所のみ (独立 grep で確認)。片方は D551 で
  絞り込み済み、もう片方は元から世代数ベースの設計で安全だった。
- 既存の2つの回帰テストはいずれも `_assert_rulings_exist` 経路を除外または実質未発火に
  しており、この経路が将来履歴比例へ戻る退行を検出できなかった。変異 matrix
  (新HEAD版 KILLED・旧HEAD版 SURVIVED) で純増検出力を実測確認した。

**却下した選択肢:**

- production コード (`_batch_oids`/`_assert_rulings_exist`) へ追加の narrowing を実装する
  — 前提 (narrow 漏れ経路の存在) が実測で否定されたため、対象が無い。
- 新規テスト関数を追加する — 既存テストの fixture 拡張で同じ検出力を得られ、規律5
  「盛らない」に照らし既存関数の拡張を採用した (敵対相談レンズの推奨)。
