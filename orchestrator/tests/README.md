# orchestrator/tests — テスト方針

## 二重 runner

全テストファイルは pytest でも素の `python3 orchestrator/tests/test_*.py` でも走る
(pytest 非依存の `_run()` を各ファイル末尾に持つ)。pytest が無い環境でも検証を
止めないための意図的な設計。`_run()` は AssertionError (FAIL)・その他例外 (ERROR)・
`skiputil.Skip` (SKIP) を分けて数える。

## 依存物不在時の skip (可視化)

gnuplot / 実 Silo サンプル / submodule が無い環境では、該当テストは `skiputil.skip()`
で **skip として数える**。print + return の疑似スキップは PASS に数えられ、
「fresh clone で load-bearing テストが空虚に緑」というカバレッジ蒸発を隠すため
使わない (audit 2026-06-30 §3)。

- **実 Silo サンプル** (`output/runs/silo-sample`, 184k txn / 66MB):
  `test_verifier.test_real_silo_serializable` (規律2 の緑の地面) が使う。
  `.gitignore` の `output/runs/` 包括無視で git 追跡外のため fresh clone には無い。
  再生成: trace-enabled build (`build-trace`, `-DCCBENCH_TRACE=1`) で `ycsb_silo` を
  回し trace を `output/runs/silo-sample/` に置く (patches/README.md の trace 手順、
  worklog 2026-06-18 参照)。
- **submodule**: `git submodule update --init external/ccbench` 後に
  source_digest / EVOLVE-BLOCK 系テストが有効化される。
- **gnuplot**: `test_reports.test_make_plot_generates_valid_png` のみ。

テストの後半だけが依存物を要する場合 (前半で実検証が完了している場合) は
skip でなく return で打ち切る (その旨コメントを付ける)。

## fixtures

判定既知の手製極小トレースは `fixtures/README.md` 参照。
