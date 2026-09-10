# 段 1 brief — [T-2333] 受入 shard report.json の session timeline 観測 field

## scope

受入 shard の `report.json` に session timeline の観測 field を足す (D1647)。足す観測は 3 種。

- (a) collection 終了時刻
- (b) 各 worker の最初と最後の test 時刻
- (c) `pytest_runtest_protocol` wrapper の real-repo lock 取得時刻 / 解放時刻

## 確定済みユーザー裁定 (D1647、逐語は verbatim-rulings.md)

- 観測 field として足す。**gate・判定・受理集合には触れない。**
- D1620 が固定した測定面 (canonical 起動の receipt が記録する最遅 shard の wall) は変えない。
- timeline に基づく判定や gate を同時に足すことは、D1647 が明示的に却下している。

## 不変条件

- `merge_reports` の 6 gate と `validate_report_evidence` の既存判定を 1 つも緩めない。
- receipt の field と `dev_wave_wait.py` の受入経路は変えない。
- 観測の追加コストは受入 wall を実測できる程度に小さく保つ (per-item の I/O を足さない)。

## 起動時に親が実測した事実

- `session_timeline` は main に 1 件も無い (`git grep` rc=1)。
- `tools/acceptance_shards.py` (blob 5f162cdceb071ec27656584ab772181ac7fa5833) と
  `orchestrator/tests/conftest.py` (blob f01aa7a41284a78e999bfa80148b326360b1e489) を
  値で検索した結果 pin 0 件。凍結成果物の bytes 束縛は無い。
- pytest は 9.1.1。`_pytest.runner` は `TestReport` を `start=` / `stop=` 付きで作る。
- `merge_reports` は `set(report) != _REPORT_FIELDS` で **top-level key 集合の厳密一致**を要求する。
  `validate_report_evidence` は個別 key 参照なので追加 field 自体では赤にならない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1-a)** 新 field は `_REPORT_FIELDS` へ必須として足す。任意 field を許す緩和 (部分集合判定への
  書き換え) はしない。
- **(P1-b)** (b) は controller 側の `pytest_runtest_logreport` が見る `report.start` / `report.stop` で
  足り、worker からの運搬は要らない。(c) だけが worker 側で発生するので `_worker_payload` を拡張する。
- **(P1-c)** 時刻は epoch 秒 (float)。shard は別 host になりうるので monotonic では跨げない。
- **(P1-d)** `orchestrator/tests/conftest.py` から `tools/acceptance_shards.py` の記録関数を呼ぶ
  依存方向にする。plugin が未装着 (通常の run_tests) のときは無害な no-op にする。

## 変更面アンカー (行番号は base commit c5754d1f4 時点)

| file:line | 対象 |
|---|---|
| `tools/acceptance_shards.py:61` | `_REPORT_FIELDS` |
| `tools/acceptance_shards.py:798` | plugin の module 状態 (`_PLUGIN_CONFIG` ほか) |
| `tools/acceptance_shards.py:806` | `pytest_configure` (状態初期化) |
| `tools/acceptance_shards.py:826` | `pytest_collection_modifyitems` — **末尾だけ**触る |
| `tools/acceptance_shards.py:862` | `pytest_runtest_logreport` |
| `tools/acceptance_shards.py:913` | `_worker_payload` |
| `tools/acceptance_shards.py:928` | `_controller_state` |
| `tools/acceptance_shards.py:956` | `pytest_sessionfinish` の report payload |
| `tools/acceptance_shards.py:518` | `validate_report_evidence` (形の検査を足すかは裁定対象) |
| `orchestrator/tests/conftest.py:2081` | `pytest_runtest_protocol` の lock 取得 / 解放 |
| `orchestrator/tests/test_run_tests_shards.py` | テスト |

## 並行 wave との編集面重複 (実測)

`/work/1/SFC/tanab/izanagi/.codex/worktrees/accwall-unit-b` が `tools/acceptance_shards.py` を
未 commit で編集中。触っているのは `records_from_items` (768 付近) と
`pytest_collection_modifyitems` の 837〜850 行。**この範囲の既存行を書き換えない。**
collection 終了時刻の記録は同関数の**末尾** (`setattr(config, "_izanagi_acceptance_shard_state", …)`
の直後または同 dict の中) へ寄せる。

## 成果物

コード + テスト + 変異 matrix + 受入全走 + worklog / decisions fragment。

## 分割方針

単一 file 中心なので Codex author 1 本。受理集合 (merge_reports が受理する report の形) が
変わるため、段 2・3 と段 6 レビューは省かない。
