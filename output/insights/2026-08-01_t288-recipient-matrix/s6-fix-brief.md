# [T-288] 段 6 fix brief — 所見裁定と修正指示

親が段 6 の全所見を裁定した。`s4-adjudication.md` の裁定は引き続き有効で、本書はその差分である。

## 1. 所見裁定

| ID | 判定 | 採否 | 対応 |
|---|---|---|---|
| RA-01 | **real** | 採用 (must-fix) | 新 docstring の「iteration ごとの相対性能を whiteboard から渡さない」は `state_from_dict` が `direction`/`magnitude`/`result` の**値**を無検証で通す (`p3_s4_loop.py:390-404`) ため機械保証されない。**`delta_pct` field に限定した記述へ狭め**、値無検証の残余を [T-287] として 1 行で明記する |
| RA-02 | **real** | 採用 (must-fix) | module docstring の「出力は値なし」も `justification`/`uncertainty` が自由文字列 (`:218-254`) なので保証でない。**「proposal スキーマに値 field を持たない」という構造の記述へ狭める**。自由文は journal/report に残るという事実も 1 行で書く |
| RA-03 | real (nit) | 採用 (docs のみ) | 換算値は payload SHA と provider payload file の bytes に影響する。コード変更は不要。D116 に 1 行残す |
| RA-04 | **real** | 採用 (must-fix、1 行) | `sys.float_info.max` は有限で通るが ×100 で `inf` になり canonical JSON (`allow_nan=False`) を壊す。**×100 の結果にも有限判定を適用**する。テストで `sys.float_info.max` を覆う |
| RB-01 | **real** | 採用 (blocker) | 世代 1 で唯一有限値を受ける critic の**値と単位**が未試験。`_fake_drive` が metrics を返さないため、critic の `llc_miss_rate` を ×100 する変異が生存する |
| RB-02 | **real** | 採用 (blocker) | `contention_level` の配線**値**が未固定。`contention_level="wrong"` が生存する |
| RB-03 | **real** | 採用 (must-fix) | 境界 `1.0` が未被覆で `metric != 1.0` 変異が生存する。**`Decimal` / numpy scalar は不採用** — metric source は bench 出力の parse 結果で `int`/`float` しか来ない (`benchparse.py`)。存在しない入力型の oracle を作らない |
| RB-04 | **real** | 採用 (blocker) | 「report に `metrics` が無い」が dry-pass 世代でしか固定されておらず、live outcome にだけ `metrics` を復活させる変異が生存する |
| RB-05 | **real** | 採用 (親が対応) | M03/M11 の注入位置が競合、M06 の `None` が複数、M15 が二重理由。**`DW-M01` 違反**。親が下記 §3 で変異表を一意 anchor へ再登録した |
| RB-06 | **real** | 採用 (must-fix) | module docstring が coder を「勝ち筋値を見ずに合成」と断言する一方、`baseline` は絶対 throughput を渡す。**coder が受ける絶対値と、受けないもの (過去候補の勝ち筋値) を区別して書く** |

**refuted はゼロ。** RA/RB とも全所見が一次資料で裏付けられた。

## 2. fix 指示 (実装子)

### 2.1 コード

1. `_role_metric_payloads` の ×100 は**結果にも有限判定を適用**する (RA-04)。
   `None` は `None` のまま。非有限になったら `None`。
2. それ以外の production コードの挙動は変えない。

### 2.2 docstring (`p3_s4_loop.py`)

3. `whiteboard_for_planner` の docstring から**機械保証されない主張を除く** (RA-01)。
   `delta_pct≡None` の fail-closed は `delta_pct` field についてのみ真である。
   `direction`/`magnitude`/`result` の値は checkpoint から無検証で入る ([T-287] の残余) と 1 行書く。
4. module docstring の planner 行を「proposal スキーマに値 field を持たない」という**構造の記述**へ狭め、
   `justification`/`uncertainty` の自由文は journal/report に残ると 1 行書く (RA-02)。
5. module docstring の coder 行を、**coder が受ける絶対値 (`baseline`) と受けないもの
   (過去候補の勝ち筋値・critic の機序帰属) を区別**した記述にする (RB-06)。

### 2.3 テスト

6. **有限 metrics を返す drive fixture を足す** (RB-01/RB-02/RB-04 の共通土台)。
   既存 `_fake_drive` は変更せず、別 fixture として足すこと。
   `leading_indicators` に `abort_rate=0.079` / `llc_miss_rate=0.124` / `latency_ns` / `ipc` を、
   `fitness_tps` に有限値を持つ outcome を返す。
7. その fixture を使う E2E で次を**個別に**断言する。
   - critic の `harness_result.metrics` が `abort_rate == 0.079` / `llc_miss_rate == 0.124` を
     **ratio のまま**持ち、`abort_rate_pct` / `cache_miss_rate_pct` を**持たない** (RB-01)
   - planner の `leading_indicators["contention_level"]` が descriptor の label と**同じ値** (RB-02)
   - その世代の `generation_record` に `metrics` key が**無い** (RB-04)
8. `_finite_metric_or_none` のテストに `1.0` と `sys.float_info.max` を足す (RB-03/RA-04)。
   `1.0` は受理、`sys.float_info.max` は `_finite_metric_or_none` では受理されるが
   ×100 後は `None` になることを `_role_metric_payloads` 側で断言する。
9. **`Decimal` / numpy scalar のテストは書かない** (RB-03 の該当部分は不採用)。

### 2.4 変えてはならないもの

`s4-adjudication.md` 「2.2 実装しないもの」は全て有効。加えて既存 `_fake_drive` の内容と
既存テストの期待値を変えない。2 世代テストと `MAX_APPROVED_GENERATIONS` の monkeypatch は禁止。

## 3. 変異表の再登録 (`DW-M01` — 一意 anchor・単一理由)

RB-05 を受け、各変異を**一意な old 逐語 anchor**で再登録した。anchor が repo 内で一意でない、
または赤理由が 2 つ以上になるものは登録から外した。

| # | file | anchor (old 逐語、一意) | new | 単一理由 |
|---:|---|---|---|---|
| N01 | trial | `abort_rate * 100.0` | `abort_rate * 1.0` | `abort_rate_pct` だけが変わる |
| N02 | trial | `llc_miss_rate * 100.0` | `llc_miss_rate * 1.0` | `cache_miss_rate_pct` だけが変わる |
| N03 | trial | `if isinstance(value, bool) or not isinstance(value, (int, float)):` | `if not isinstance(value, (int, float)):` | bool だけが通る |
| N04 | trial | `return metric if math.isfinite(metric) else None` | `return metric` | 非有限だけが通る |
| N05 | trial | `"abort_rate": _finite_metric_or_none(leading.get("abort_rate")),` | `"abort_rate_pct": _finite_metric_or_none(leading.get("abort_rate")),` | 内部 key だけが変わる |
| N06 | trial | `"abort_rate": _finite_metric_or_none(leading.get("abort_rate")),` | `"abort_rate": _finite_metric_or_none(leading.get("llc_miss_rate")),` | abort の source だけが変わる |
| N07 | trial | `"current_perf": dict(perf_payload),` | `"current_perf": dict(current_metrics),` | planner の key 集合だけが変わる |
| N08 | trial | `"baseline": dict(perf_payload),` | `"baseline": dict(current_metrics),` | coder の key 集合だけが変わる |
| N09 | trial | `"metrics": dict(current_metrics),` | `"metrics": dict(perf_payload),` | critic の key 集合だけが変わる |
| N10 | trial | `SCHEMA_VERSION = "p3-autonomous-workload-trial/v2"` | `...trial/v1"` | schema literal だけが変わる |
| N11 | trial | `contention_level=descriptor["contention"]["label"],` | `contention_level="wrong",` | leading の label だけが変わる |
| N12 | trial | 初期 dict の `"abort_rate": None,` | `"abort_rate": 0.0,` | 未観測世代の値だけが変わる |
| N13 | trial | `"llc_miss_rate": llc_miss_rate,` (perf_payload 内) | `"llc_miss_rate": llc_miss_rate * 100.0,` | percent 名でない field だけが変わる |
| N14 | trial | ×100 結果の有限判定 (RA-04 の新規行) | 判定を外す | `sys.float_info.max` 経路だけが変わる |
| N15 | trial | `current_metrics = _metric_projection(outcome)` | 同行の直後に `generation_record["metrics"] = dict(current_metrics)` を追加 | report の key 集合だけが変わる |

**注**: N01/N02 は別の逐語なので競合しない (旧 M03/M11 の衝突を解消)。
旧 M06 (複数 `None`) は N12 (初期 dict の 1 箇所) と N14 に分割した。
旧 M15 の二重理由は N13 (guarded な perf_payload 内) に一本化した。
anchor の一意性は実装子が `grep -c` で確認し、複数ヒットしたら登録を止めて報告すること。
