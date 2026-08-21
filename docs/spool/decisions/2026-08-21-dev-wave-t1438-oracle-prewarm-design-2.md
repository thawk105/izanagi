---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1438-oracle-prewarm-design
seq: 2
---

## {{D:oracle-environment-controller-prewarm}}. sort SWO oracle の real-repo 直列鎖からの分離を controller-only prewarm barrier + 独立完全性検査で実装する

**決定:** T-1012 (D591) が `REAL_REPO_SERIAL_NODES` へ追加した 24 node (sort SWO oracle
fixture 消費者) を、`real_repo_receipt_memo.py` 型の controller-only prewarm barrier へ
置き換えて分離した。新設 sibling module (`sort_swo_oracle_receipt_memo.py`) が pytest
collection-finish 時に一度だけ `resolve_oracle_environment` を解決し、24 関数は fixture
受け取りから読み取り専用 getter 呼び出しへ移行した。fixture のままでは自動的に得られていた
機械的完全性検査 (closure gate、fixture の scope/baseid で機械判定) を失わないよう、同型の
独立 golden (`ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN`) + AST inventory + exact-match 検査 +
negative control を新設した。

**理由:**
- D591 が候補 C を見送った理由 (「controller の資源解決が worker 実行開始より必ず先行する」
  という hook 順序前提を file:line 粒度で実証できなかった) を、本 wave で pytest-xdist 3.8.0
  の実ソース (`dsession.py`/`remote.py`/`workermanage.py`/`scheduler/load.py`/
  `scheduler/loadgroup.py`) を読み証明した。controller 側の
  `pytest_xdist_node_collection_finished` (prewarm 発火点) の完了は、scheduler が
  `runtests` を送る前に必ず先行する。worker 再起動時の stale collection entry という
  段2 plan の副次説明の穴を段3 レンズA が指摘したが、schedule 対象の collection entry は
  必ず prewarm 発火点の後に登録されるため核心命題は破れない。
- fixture のまま prewarm 化しても既存 closure gate
  (`test_real_repo_serialization.py` の `_assert_fixture_closure_complete`、fixture の
  scope/baseid だけで機械判定) からは逃れられないため、fixture 解除への書き換えは必須である。
  一方、それだけでは機械的完全性検査を失い規律2 に抵触する。`RECEIPT_MEMO_CONSUMER_NODES`
  には実は AST inventory による同型の完全性検査が既にあった
  ({{F:receipt-memo-completeness-check-assumption}} 参照) ことを先例に、oracle 側にも
  同型の独立検査を新設した。
- `resolve_oracle_environment` は読み取り専用 (write/subprocess 皆無) であり、現行
  `REAL_REPO_SERIAL_NODES` の writer 群 (test_hooks.py、test_s8b_floor_campaign.py 等) は
  候補 path (`IZANAGI_SORT_SWO_CXX`/`CXX`/`g++` 解決先、`IZANAGI_SORT_SWO_MASSTREE_ROOT`、
  `ccbench/build/_deps/masstree-src`、ancestor-cache) を作らないことを、writer 実装を
  実際に実行して検証する回帰テストで担保した。

**却下した選択肢:**
- 24 node の fixture 解除 + prewarm 配線だけ (段2 plan の当初案) — closure gate の機械的
  完全性検査を失うため規律2 に抵触し不採用。独立完全性検査の新設を必須要件とした
  (段4 裁定、scope 拡大)。
- D591 の 66/90 件という過去実測値 (79.02s/119.34s) をそのまま新旧比較の基準に使う —
  本 wave では計算ノードで現行 66-node 鎖を再測定し (76.46 秒、D591 の 66-node 基準値と
  3% 以内で一致)、過去値は文脈情報としてのみ扱った。90-node 状態の同日再測定は
  `IZANAGI_RUN_GROWTH_HELD_TESTS` (2026-08-12 裁定で `explicit-user-command-only` 指定)
  を要する既定 skip 57 件を含むため、本 wave では実行せず、公式性能主張はユーザー明示時に
  別途行う。
