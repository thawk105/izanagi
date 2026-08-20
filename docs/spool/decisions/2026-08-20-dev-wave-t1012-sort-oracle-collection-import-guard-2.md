---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1012-sort-oracle-collection-import-guard
seq: 2
---

## {{D:t1012-collection-import-guard}}. sort SWO oracle の pytest collection時 import 保護は pytest fixture 化 + REAL_REPO_SERIAL_NODES 拡張とし、鎖を伸ばさない controller-prewarm 方式は見送る

**決定:** `orchestrator/tests/test_sort_swo_oracle.py` の module 直下
`_ENVIRONMENT = O.resolve_oracle_environment(_CCBENCH)` (pytest collection 時に全 xdist worker
で実行され、`REAL_REPO_SERIAL_NODES` の実行時直列化では保護できない) を、
`@pytest.fixture(scope="module")` の `oracle_environment` へ遅延化する。直接 consumer 16 関数 +
`compiled_oracle_artifacts` 経由の間接 consumer 8 関数、計 24 canonical node (27 collected item)
を `REAL_REPO_SERIAL_NODES` / 独立 golden (`test_real_repo_serialization.py`) の両方へ追加する
(66→90件)。同ファイルの `_assert_fixture_closure_complete` が fixture 消費者の登録漏れを機械検査
する。collection 中に resolver が呼ばれないことを検査する回帰テストを追加する。

**理由:**
- 親プロセス内で `resolve_oracle_environment` を monkeypatch し `--collect-only`
  (テスト実行ゼロ) を走らせると実呼び出しが1回発火することを実測した。`REAL_REPO_SERIAL_NODES` の
  `xdist_group("real-repo")` marker 付与 (`pytest_collection_modifyitems`) は collection
  **完了後**の hook のため、import 時アクセスを構造的に保護できない。
- 既存の `real_repo_ratified_memo.py` (`new_outcome_cache`) / `real_repo_receipt_memo.py`
  (prewarm barrier) と同種の「lazy 化して collection 時アクセスを避ける」設計を再利用する。
- pytest fixture 化 (候補B) は、既存の `_assert_fixture_closure_complete` が fixture 消費者の
  `REAL_REPO_SERIAL_NODES` 登録漏れを (少なくとも 1 件が既に登録されている限り) 自動検出する
  — 手書き `functools.lru_cache` 方式 (候補A) にはこの安全網が無い。

**却下した選択肢:**
- 候補A (`functools.lru_cache` 包みの module-level lazy singleton) — 機械的差分は小さいが、
  `REAL_REPO_SERIAL_NODES` 登録漏れを検出する既存機構の恩恵を受けない。
- 候補C (`real_repo_receipt_memo.py` 型の controller-only prewarm barrier + cross-worker
  cache、`REAL_REPO_SERIAL_NODES` を一切伸ばさない) — 実装複雑度が高く、安全性が依存する
  「controller の資源解決が worker 実行開始より必ず先行する」という hook 順序前提を本 wave では
  file:line 粒度で実証できなかった。D531 (「配布順の変更で wall が下がるという主張は、実装した
  上で同一 branch 上の A/B 対測定で示す」) の方法論に従い、まず候補B を実装して実測し、増分が
  許容できない場合に候補C へ投資する順序を選んだ。
- `REAL_REPO_SERIAL_NODES` への追加を24件未満に絞る — module scope の `oracle_environment`
  fixture を消費する全 canonical node が、xdist の worker 割当て次第でいずれも fixture 要求時の
  未保護トリガになりうるため、部分集合での保護は原理的に成立しない。

**実測 (real-repo 直列鎖への影響):** 同一commit上で 66 canonical (追加前相当) / 90 canonical
(現行) を明示的に node 列挙して直列実行し比較: 79.02s → 119.34s (+40.32秒、+51%)。追加27件
(skip 0件) は事前の lens 予測 (直接16+間接7+4-parametrize展開4) と一致した。この増分は D531/D532
(鎖はwallの74〜78%を占める) に照らし軽微とは言えないが、既知トレードオフとして受容し、
{{T:sort-oracle-collection-guard-chain-cost}} で候補Cの再検討余地を記録する。
