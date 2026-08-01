# [T-288] 段 4 裁定 — プラン v2 と変異事前登録

親が段 3 の全所見を real/refuted・採用/不採用・scope 内/外に裁定した。

## 1. 所見裁定表

| ID | 判定 | 採否 | 理由 |
|---|---|---|---|
| A-01 | **real** | 採用 (scope 内) | `MAX_APPROVED_GENERATIONS=1` (`:91`) なので承認済み run で有限値を受けるのは critic だけ。プランは唯一 live な critic 配線を無試験のまま残していた。**ただし 2 世代テストは不要**と裁定する — 内部 key を ratio 名にすれば、世代 1 の payload key 集合の assert だけで「射影を迂回して内部 dict を直渡しする」変異を殺せる。generation 予算 gate (D114) を test で monkeypatch しない |
| A-02 | **real** | **不採用 (scope 外) → 裁定パッケージ** | `throughput[tps]` = commits/extime (`external/ccbench/common/result.cc:52-56`) を `throughput_ops_sec` と名付けている。YCSB 既定 `ycsb_max_ope=10` (`external/ccbench/include/ycsb.hh:22`) なので名目 10 倍。real だが **値は正しく名前だけが誤り**であり、是正には live role md 編集 = pin 閉包が要る。ユーザー裁定「追認 + 単位ずれ修正」の射程外 |
| A-03 | **real (親 brief の根拠が偽)** | 根拠を訂正、結論は維持 | role md は歴史資料ではなく 8c が実際に読む live prompt (`:101-108` → `claude_projected_provider.py:122`)。**P4/P5 の「歴史的例示だから触らない」は偽**。ただし触らない結論自体は維持する — 理由は「ユーザー裁定の射程外」であり「歴史的だから」ではない。説明 drift は裁定パッケージへ |
| A-04 | **real** | 採用 (文言のみ) | 提案 docstring の「評価済みのみ・機序なし」は checkpoint 値が無検証 (`p3_s4_loop.py:371,390`) なので恒真な保証になる。**docstring から発火しない保証を書かない**。checkpoint 値検証の実装は既存 [T-287] であり本 wave では実装しない |
| A-05 | **real** | 採用 (D116 本文へ) | 世代間記憶があれば連続する絶対 throughput から変化率を復元できる。coder も `baseline` で同じ値を受けるため、(b) 移行の前提条件は **planner だけでなく coder 面も含めて**書く |
| A-06 / B-09 | **real** | 採用 = **プランから削除** | `generation_record["metrics"]` 新設と `REPORT_SCHEMA_VERSION` v2 化は単位修正に不要な独立 schema 拡張。report は既に raw `harness` を持つ (`:951`)。**両方とも実装しない** |
| A-07 | **real** | 採用 = 範囲 guard を入れない | parser も screening も 0..1 上限を強制しない (`benchparse.py:71`, `screening_driver.py:113`)。role 側だけ範囲外を `None` にすると gate と説明が食い違う |
| A-08 | **real** | 採用 | 変異 M4 / M14 の kill 帰属が不成立。M14 は report metrics 削除で消滅、M4 は再照準する (`DW-M01`) |
| A-09 | real (nit) | 採用 (表現訂正) | 「既存テスト被覆ゼロ」は「本 defect を殺す assert がゼロ」に狭める。経路被覆は存在する |
| B-01 | **real** | 採用 (scope 内) | role payload の意味が変わるのに `SCHEMA_VERSION` (`:88`, `:606`, `:1030`) が v1 のままだと、同じ v1 が `0.079` と `7.9` の両方を意味する。**`SCHEMA_VERSION` を v2 へ上げる**。`REPORT_SCHEMA_VERSION` は report 形が変わらないので v1 のまま |
| B-02 | **real** | 結論維持、残余を明記 | pin 閉包の列挙は正確 (`review_ledger.py:22,25,62,65`、`spec.py:582`、`check_codex_agents.py:241`、`manifest.json:876`)。role md 編集は scope 外。D116 に「role md の記述は現行 recipient matrix の完全記述ではない」と残余を明記する |
| B-03 | **real** | **不採用 (scope 外) → 裁定パッケージ** | raw `outcome` の nan/inf は `generation_record["harness"]` に残り `allow_nan=False` (`:537`) で report 書込みが失敗、`run-finish` は先に journal へ入る (`:751,757`)。**既存欠陥であり本変更が導入するものではない**。docs で「nan を端から端まで処理した」と主張しない |
| B-04 | **real** | 採用 = 範囲 guard を入れない | 異常値を黙って「未観測」へ畳むのは不正。**既存 fitness guard (`:516-521`) と同じ bool + 非有限だけを `None` にする**。範囲外 ratio は ×100 して通し、異常を可視のまま残す |
| B-05 | **real** | 採用 (全項) | 世代 1 payload、critic payload、schema literal、恒真な version 比較を全て塞ぐ |
| B-06 | **real** | 採用 (docs、親所有) | 段 4b / 段 5 runbook (`docs/phase3-s4b-runbook.md:41,54`、`docs/phase3-s5-sort-runbook.md:40,56`) が `_pct` field を手作業射影させるのに ×100 規約がない。**同じ defect の手動経路なので単位ずれ修正の射程内**。各 runbook へ換算規約を追記する |
| B-07 | **real (親 brief が過大)** | 採用 = 訂正 | 承認済み 1 世代では planner/coder は全 `None` を読む。**今日変わるのは critic の帰属と役割台帳**であり、planner/coder 起因の受理集合変更は多世代開放後に限る |
| B-08 | real (nit) | 採用 (訂正済み) | live artifact は report + attempt journal の 2 件。`FROZEN_MANIFEST` は exact 23 path (`test_frozen_artifacts.py:141`) であって `output/` 全体ではない |
| B-10 | **real** | 不採用 (scope 外) → 裁定パッケージ | reject 世代が有効測定を全 `None` で無条件上書きする (`:953`) |
| B-11 | **real** | 不採用 (scope 外) → 裁定パッケージ | `ratio * 100.0` の表現契約が無い (`0.29*100 = 28.999999999999996`) |

**refuted はゼロ。** 段 3 の全所見が一次資料で裏付けられた。親 brief は 4 点 (P3 行参照、live artifact 0 件、role md が歴史資料、成果物影響の射程) で反証された。

## 2. プラン v2 (確定)

### 2.1 実装面 (Codex 実装子が所有)

**ファイル所有**: `orchestrator/campaign/p3_autonomous_workload_trial.py`、
`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_autonomous_workload_trial.py`。
単位は 1 つ (相互依存のため分割しない)。

1. **正規化 helper を 1 本だけ足す。** `_finite_metric_or_none(value)` —
   `None` / `bool` / 非数値 / `nan` / `±inf` を `None` に、有限な `int` / `float` を `float` に。
   既存 fitness guard (`:516-521`) と同じ判定を関数化したもので、**範囲検査は入れない**。
2. **`_metric_projection()` を内部 ratio schema にする。** key =
   `throughput_ops_sec` / `abort_rate` / `latency_ns` / `llc_miss_rate` / `ipc`。
   全値を `_finite_metric_or_none` に通す。現行 `abort_rate_pct` (`:523`) を `abort_rate` へ戻す。
3. **`_role_metric_payloads(current_metrics, *, contention_level)` を新設**し
   `(perf_payload, leading_payload)` を返す。**換算はここ 1 箇所だけ**。
   - `perf_payload` = `throughput_ops_sec` (絶対 ops/s のまま) / `abort_rate_pct` (=`abort_rate`×100) /
     `latency_ns` / `llc_miss_rate` (ratio、名前どおり) / `ipc`
   - `leading_payload` = `contention_level` / `cache_miss_rate_pct` (=`llc_miss_rate`×100) / `IPC_overall`
   - `None` は `None` のまま。未観測を `0` に補完しない。field 集合は現行と同一 (追認)
4. **配線**: `:796-802` の初期 dict を内部 key 名へ。`:816-825` の planner は
   `current_perf` ← `perf_payload`、`leading_indicators` ← `leading_payload`。
   `:858` の coder `baseline` ← 同じ `perf_payload` の copy。
   `:963` の critic `harness_result.metrics` ← 内部 ratio dict (`dict(current_metrics)`) のまま。
   `:851-852` の機序非転送境界は変更しない。
5. **`SCHEMA_VERSION` を `p3-autonomous-workload-trial/v2` へ上げる** (`:88`)。
   `REPORT_SCHEMA_VERSION` は v1 のまま。
6. **`p3_s4_loop.py` の docstring 是正** (`:273-277` と module docstring `:7`)。
   「whiteboard 射影経路に限った防壁であり planner 入力全体の性能値遮断ではない。絶対 throughput は
   `current_perf` で planner へ、`baseline` で coder へ別 field で渡る」と射程を書く。
   **発火しない保証を新たに書かない** (checkpoint 値の無検証は [T-287] の残余として言及に留める)。
   `_DELTA_PCT_LIVE=False`、`WhiteboardLeakError`、load 側拒否は変更しない。

### 2.2 実装しないもの (明示)

- `generation_record["metrics"]` の新設と `REPORT_SCHEMA_VERSION` の bump
- 0..1 範囲 guard / `_ratio_or_none`
- 2 世代テスト、generation 予算 gate の monkeypatch
- `.claude/agents/*.md`、`.codex/role-adapters/*.json`、`review_ledger.py`
- `output/` 配下の bytes

### 2.3 docs (親が所有)

`docs/decisions.md` D116、`docs/worklog.md`、`docs/phase3-s4b-runbook.md` /
`docs/phase3-s5-sort-runbook.md` の換算規約追記、insights。

## 3. 変異事前登録 (`DW-M01`)

各変異は「その位置より前に同じ入力を拒否する検査がないこと」を実装子が確認して登録する。
赤理由が一つに絞れないものは登録しない。

| # | 変異 | 期待 kill node |
|---:|---|---|
| M01 | `_role_metric_payloads`: `abort_rate * 100.0` → `abort_rate` | percent 換算 test |
| M02 | 同: `* 100.0` → `* 10.0` | percent 換算 test |
| M03 | 同: `llc_miss_rate * 100.0` → `llc_miss_rate` | percent 換算 test |
| M04 | `_finite_metric_or_none`: bool 排除条件を削除 | 無効値 test (`True` が `1.0` になる) |
| M05 | 同: `math.isfinite` 検査を削除 | 無効値 test (`nan`/`inf` が通る) |
| M06 | `_role_metric_payloads`: `None` → `0.0` に補完 | 未観測 None 保存 test + 世代 1 E2E |
| M07 | `_metric_projection`: report key を `abort_rate` → `abort_rate_pct` | 内部 ratio key test + critic payload E2E |
| M08 | `_metric_projection`: abort の source を `leading["llc_miss_rate"]` に変更 | 内部 ratio key test |
| M09 | planner `current_perf` ← `perf_payload` を `dict(current_metrics)` へ | 世代 1 E2E の planner key 集合 assert |
| M10 | coder `baseline` ← `perf_payload` を `dict(current_metrics)` へ | 世代 1 E2E の coder key 集合 assert |
| M11 | planner `leading_indicators` の `cache_miss_rate_pct` を内部 ratio 直渡し | percent 換算 test + 世代 1 E2E |
| M12 | critic `metrics` ← `dict(current_metrics)` を `dict(perf_payload)` へ | critic payload key 集合 E2E |
| M13 | `SCHEMA_VERSION` を v1 に戻す | schema literal test |
| M14 | 初期 `current_metrics` の `abort_rate` を `None` → `0.0` | 世代 1 E2E の全 None assert |
| M15 | `perf_payload` の `llc_miss_rate` を ×100 する (percent 名でない field を換算) | perf field 単位 test |

## 4. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **A-02**: `throughput_ops_sec` が実は tps。live role md の rename を伴う
2. **A-03 / B-02**: live role md の説明 drift 3 種 (planner の "leading-indicators only"、
   存在しない `last_delta_pct`、coder の "5 fields only") と pin 閉包の作業量
3. **B-03**: 非有限 raw metrics で terminal report が生成されず journal だけが残る破断
4. **B-10**: reject 世代が有効 baseline を全 `None` で上書きする
5. **B-11**: `ratio * 100.0` の float 表現契約 (丸め・桁) が無い
