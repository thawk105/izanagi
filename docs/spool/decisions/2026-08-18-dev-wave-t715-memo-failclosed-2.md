---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t715-memo-failclosed
seq: 2
---

## {{D:receipt-memo-prewarm-barrier}}. receipt memo の prewarm barrier は worker 起動前でなく test 実行前に置く

**決定:** 実 repo の T-080 receipt 解決を畳む test 支援 memo の prewarm barrier は、
**test body が 1 本も走る前**に置く。実装は `pytest_xdist_node_collection_finished`
(xdist controller) と `pytest_collection_finish` (非 xdist) で、worker 側は二重 guard で除外する。
UID の確定だけは `pytest_configure` で行う。`tools/run_tests.py` の argv は変更しない。
xdist の `--testrunuid` は charset を制限しないため、UID を検査で弾かず内容 hash から cache 名を作る。

**理由:**
- 承認済み裁定の字面は「worker 起動前に runner が 1 回解決して cache を作る」だが、
  xdist 3.8.0 でこれをコードで満たす経路は存在しない。`DSession.pytest_sessionstart` が
  `NodeManager` 生成と `setup_nodes()` (worker 起動) を同じ関数で行い、
  `DSession.pytest_collection` は controller の item collection を短絡する。
  「collect 結果で prewarm を条件分岐する」と「worker process 生成前」は両立しない。
- 裁定の目的である「session 中に production 経路が実 repo を再解決しない」は、
  test 実行前 barrier で達成される。縮小が成立する前提 (collection 時に consumer が
  resolver へ到達しないこと) は meta-test で機械固定する。
- memo が返す値は本番 resolver の戻り object そのままで受理集合は不変。変わるのは
  snapshot の時点 (最初の consumer 時点 → collection barrier 時点) と、miss が赤になること。
  固定 snapshot に対して全 consumer が同じ解決結果を観測する。

**却下した選択肢:**
- 無条件 prewarm — consumer を含まない焦点走に解決 1 回分が丸乗りし、テスト時間規則を自ら破る。
- controller 側で consumer file だけを自前 collect する — 二重 collection のコストを新設する。
- UID の charset 検査を残す — xdist が受理する正当な UID を新たに拒否してしまう。
