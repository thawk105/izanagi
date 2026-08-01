結論として P1〜P6 の方向は採用可能です。ただし P3 の行参照には事実誤認があります。現行の `:963` は `generation_record["metrics"]` ではなく、critic 入力の `critic_payload["harness_result"]["metrics"]` です（[p3_autonomous_workload_trial.py:957](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:957)）。report へ残すには明示的な field 追加が必要です。

以下の行番号は編集前の現 checkout を指します。

## 1. 換算の実装

### 1.1 内部値の正規化

[p3_autonomous_workload_trial.py:505](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:505) の直前へ、次の純粋関数を追加します。

```python
def _finite_float_or_none(value: Any) -> float | None: ...
def _ratio_or_none(value: Any) -> float | None: ...
def _ratio_to_percent(value: Any) -> float | None: ...

def _role_metric_payloads(
    current_metrics: Mapping[str, Any],
    *,
    contention_level: str,
) -> tuple[dict[str, Any], dict[str, Any]]: ...
```

契約は次のとおりです。

- `_finite_float_or_none`
  - `None`、`bool`、非数値、`nan`、`inf`、`-inf`、float 化で overflow する値を `None` にする。
  - 有限な `int` / `float` だけを `float` として返す。
  - `False` / `True` を `0.0` / `1.0` として受理しない。
- `_ratio_or_none`
  - 上記に加え、率の契約外である `<0` / `>1` を `None` にする。
  - 境界の `0.0` / `1.0` は有効値として保存する。
- `_ratio_to_percent`
  - 有効な ratio だけ `ratio * 100.0`。
  - `None` は `None` のまま。未観測を `0` に補完しない。

率が 0..1 である根拠は `llc_miss_rate` の契約（[model.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/calibrator/model.py:38)）と `abort_rate` の算出式（[benchparse.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/calibrator/benchparse.py:66)）です。

### 1.2 `_metric_projection()` を report/internal 専用にする

[p3_autonomous_workload_trial.py:505-527](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:505) を置き換え、role 名を含まない次の内部 schema を返します。

| internal key | 値・単位 | 正規化 |
|---|---|---|
| `throughput_ops_sec` | 絶対 throughput、ops/s | finite number |
| `abort_rate` | ratio、0..1 | finite ratio |
| `latency_ns` | ns | finite number |
| `llc_miss_rate` | ratio、0..1 | finite ratio |
| `ipc` | instructions/cycle | finite number |

重要なのは現行 `abort_rate_pct`（[p3_autonomous_workload_trial.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:523)）を内部では `abort_rate` に戻すことです。`leading.get(...)` の生値を無検査で通す処理もすべて正規化関数経由にします。

### 1.3 role-facing payload を一箇所で作る

`_role_metric_payloads()` は `(perf_payload, leading_payload)` を返します。

`perf_payload` は planner の `current_perf` と coder の `baseline` の双方に使い、field と単位を完全一致させます。

| `current_perf` / `baseline` field | 単位 |
|---|---|
| `throughput_ops_sec` | 絶対 ops/s |
| `abort_rate_pct` | percent、0..100 |
| `latency_ns` | ns |
| `llc_miss_rate` | ratio、0..1。既存 field 名・単位を維持 |
| `ipc` | instructions/cycle |

`leading_payload` は次です。

| `leading_indicators` field | 単位 |
|---|---|
| `cache_miss_rate_pct` | percent、0..100 |
| `contention_level` | descriptor 由来の categorical label |
| `IPC_overall` | instructions/cycle |

`llc_miss_rate` が `current_perf` / `baseline` では ratio のままなのは、現行 `dict(current_metrics)` の field 面を変えないためです。percent を名乗る `cache_miss_rate_pct` と `abort_rate_pct` だけを ×100 し、recipient matrix 自体は変更しません。

### 1.4 `_run_workload()` の配線

- [p3_autonomous_workload_trial.py:796-802](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:796)
  - 初期 `current_metrics` の `abort_rate_pct` を `abort_rate` へ変更。
  - 初期値は全て `None` のままにする。
- [p3_autonomous_workload_trial.py:815-825](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:815)
  - generation 冒頭で `_role_metric_payloads(current_metrics, contention_level=...)` を一度呼ぶ。
  - planner の `current_perf` に `dict(perf_payload)`、`leading_indicators` に `dict(leading_payload)` を渡す。
- [p3_autonomous_workload_trial.py:843-860](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:843)
  - coder の `baseline` は同じ `perf_payload` の copy にする。
  - planner の `justification`・機序テキストを転送しない [851-852] の境界は変更しない。
- `last_delta_pct` は新設しない。現行 8c はその値を計算・送信しておらず、`delta_pct` の live 化にも踏み込まない。

## 2. report との分離

[p3_autonomous_workload_trial.py:951-954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:951) で `_metric_projection(outcome)` の直後に次を追加します。

```python
current_metrics = _metric_projection(outcome)
generation_record["metrics"] = dict(current_metrics)
```

critic 入力の [p3_autonomous_workload_trial.py:963](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:963) もこの report-side 辞書を copy して使います。report と critic が別々に再投影して drift する経路を作りません。

`generation_record["metrics"]` の schema は次です。

```json
{
  "throughput_ops_sec": 88124.1,
  "abort_rate": 0.079,
  "latency_ns": 1234.0,
  "llc_miss_rate": 0.124,
  "ipc": 2.1
}
```

率は ratio のままで、`abort_rate_pct` / `cache_miss_rate_pct` は report に書きません。`generation_record["harness"]`（[p3_autonomous_workload_trial.py:951](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:951)）の生 outcome も変更しません。

互換性については、[REPORT_SCHEMA_VERSION:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:89) を `p3-autonomous-workload-trial-report/v2` へ上げるべきです。

- 現行 v1 に `generation_record["metrics"]` は存在しません。
- 凍結済みの実 report も v1 かつ generation は `generation/outcome/roles` のみです（[control report:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-report.json:32)、[schema:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-report.json:211)）。
- 過去 v1 は書き換え・backfill しない。新 consumer は v1/v2 を version 分岐する必要がある。
- exact-key の外部 consumer に対しては互換ではない。repo 内にはこの field を読む既存 consumer は見つからない。
- `output/` の既存 bytes は一切変更しない。

## 3. docstring / コメント是正

[p3_s4_loop.py:273-277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:273) は次の文面へ置き換えます。

```python
"""planner-v4 / coder-v4 入力の whiteboard フィールド
(評価済みのみ・機序なし)。段 4 はこの whiteboard 射影経路に限って
delta_pct≡None を fail-closed 強制し、iteration ごとの相対性能を
whiteboard から渡さない (規律2/6)。これは planner 入力全体の性能値遮断ではない。
絶対 throughput は別 field として planner へ current_perf で、
coder へ baseline で渡り、planner には leading_indicators も渡る。
load 側 state_from_dict と二重で塞ぎ、in-memory 経路
(project_whiteboard が誤って非 None を書く) も射影の関所で止める
(監査 2026-07-08)。"""
```

同じ誤読を招く箇所は次です。

- [p3_s4_loop.py:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:7): planner 入力を `leading-indicators` だけのように要約している。  
  `current_perf (絶対 throughput を含む) + leading-indicators + abstract whiteboard → 方向提案 (出力は値なし)` へ是正する。
- [planner-v4.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:3)、[planner-v4.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:11)、特に [planner-v4.md:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:68): 「leading-indicators だけ」と記す一方、入力例は `current_perf` に絶対 throughput を含む（[32-35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:32)）。
- [planner-v4.md:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:35): `last_delta_pct=-1.2` は現行 8c の実 payload には存在しない。
- [coder-v4-autonomous-trigger-gating.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:20): 「leading-indicators」と要約するが、実際の 8c recipient は `baseline`（入力例は [50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/coder-v4-autonomous-trigger-gating.md:50)）。

ただし後三者は P5 に従い今回編集しません。D116 で「role md の “only” 記述は現行 8c recipient matrix の完全記述ではない」と残余を明記します。全説明面の矛盾解消を完了条件にするなら P5 は成立せず、pin 閉包込みの別変更が必要です。

[p3_s4_loop.py:343-353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:343) は checkpoint / `delta_pct` に射程が局所化されており、`WhiteboardLeakError` と併せて触りません。

## 4. 追加テスト

純粋関数テストは [test_p3_autonomous_workload_trial.py:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:92) の後、two-generation 配線テストは既存 fixture E2E の [164-215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_p3_autonomous_workload_trial.py:164) の後へ追加します。

| 追加 nodeid | 固定する意味・殺す変異 |
|---|---|
| `test_metric_projection_uses_ratio_keys_and_units` | `0.079/0.124` が report/internal ではそのまま、key が `abort_rate` / `llc_miss_rate`。report 側で ×100、旧 `abort_rate_pct` key、abort/LLC の取り違えを殺す。 |
| `test_metric_projection_preserves_none_and_rejects_invalid_numbers` | 欠損、bool、nan、±inf、範囲外 ratio が `None`、実測 0.0 は保持。bool guard、finite guard、range guard、None→0 補完の変異を殺す。 |
| `test_role_metric_payloads_convert_only_percent_fields` | 入力 `abort_rate=.079`, `llc_miss_rate=.124` に対し `abort_rate_pct=7.9`, `cache_miss_rate_pct=12.4` を literal/`pytest.approx` で確認。`current_perf.llc_miss_rate=.124` も固定する。×1/×10/×1000、別 field 換算を殺す。 |
| `test_role_metric_payloads_preserve_unobserved_none` | first generation の全数値が `None`、`contention_level` だけ descriptor 値。未観測を 0 にする変異を殺す。 |
| `test_second_generation_payloads_share_units_and_report_keeps_ratios` | `MAX_APPROVED_GENERATIONS` をテスト内だけ 2 にし、測定値を返す fake drive を使う。第2世代の planner `current_perf` と coder `baseline` が同じ snapshot かつ双方 `abort_rate_pct=7.9`、planner LI が `cache_miss_rate_pct=12.4`、第1世代 report `metrics` は ratio、disk report は v2、と個別に断言する。片方だけ内部辞書を直渡しする変異や report への role payload 混入を殺す。 |

two-generation test は `planner_payload == coder_payload` だけで済ませません。両方が誤って ratio のままでも緑になるため、双方の percent literal、report の ratio literal、key の存在・不在を別々に assert します。hash の差や恒真 assert は判定に使いません。

## 5. 触らない面と P1/P5/P6 判定

- `_DELTA_PCT_LIVE = False`（[p3_s4_loop.py:353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_s4_loop.py:353)）、`WhiteboardLeakError`、load/射影の二重拒否は変更しない。
- planner への絶対 throughput は [current_perf:818](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:818) に残す。今回 (b) へ移行しない。
- coder の `baseline`（[858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:858)）も残す。
- `output/` は変更しない。`FROZEN_MANIFEST` が output bytes を pin している（[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/tests/test_frozen_artifacts.py:38)）。
- P1 は成立する。role md は既に `abort_rate_pct=7.9` / `cache_miss_rate_pct=12.4`（[planner-v4.md:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:34)、[38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.claude/agents/planner-v4.md:38)）を示しており、実装を percent に合わせれば key 改名不要。
- P5 は「コード修正に role md 編集は不要」という意味では成立する。ただし前節の説明矛盾は残るため条件付き成立。
- role md を触る場合は review ledger の source hash（[review_ledger.py:15-25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/codex_roles/review_ledger.py:15)）と adapter の source pins（[planner adapter:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.codex/role-adapters/planner-v4.json:124)、[coder adapter:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/.codex/role-adapters/coder-v4-autonomous-trigger-gating.json:165)）を同時更新する必要があるため、今回は避ける。
- P6 は成立する。親所有で [docs/decisions.md:5460](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/decisions.md:5460) の後へ D116 を追加し、recipient matrix、whiteboard 防壁の局所射程、ratio/report と percent/role の分離、(b) を multi-generation 開放条件とすることを一体で記録する。

## 6. 変異事前登録候補

| # | 変異箇所・書換え | 落ちるべきテスト |
|---:|---|---|
| 1 | 新 `_ratio_to_percent`: `value * 100.0` → `value` | `test_role_metric_payloads_convert_only_percent_fields`, two-generation |
| 2 | 同: `* 100.0` → `* 10.0` | 同上 |
| 3 | 新 `_finite_float_or_none`: bool 排除条件を削除 | `test_metric_projection_preserves_none_and_rejects_invalid_numbers` |
| 4 | 同: `math.isfinite` 検査を削除 | invalid-numbers、disk report E2E |
| 5 | 新 `_ratio_or_none`: 0..1 範囲検査を削除 | invalid-numbers |
| 6 | 新 `_ratio_to_percent`: `None` → `0.0` | `test_role_metric_payloads_preserve_unobserved_none` |
| 7 | [旧 :523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:523): report key `abort_rate` → `abort_rate_pct` | ratio-key test、two-generation report assert |
| 8 | `_metric_projection`: abort の source を `leading["llc_miss_rate"]` に変更 | ratio-key test |
| 9 | role projection: `abort_rate_pct` に内部 ratio を直入れ | role conversion、two-generation |
| 10 | role projection: `cache_miss_rate_pct` に内部 ratio を直入れ | role conversion、two-generation |
| 11 | [planner :818](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:818): `perf_payload` → `current_metrics` | two-generation の planner literal/key assert |
| 12 | [coder :858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/orchestrator/campaign/p3_autonomous_workload_trial.py:858): `perf_payload` → `current_metrics` | two-generation の coder literal/key assert |
| 13 | planner LI の `cache_miss_rate_pct` を `current_metrics["llc_miss_rate"]` から直渡し | two-generation の 12.4 assert |
| 14 | `generation_record["metrics"]` に `perf_payload` を保存 | ratio-key test、two-generation report assert |
| 15 | `generation_record["metrics"]` の代入を削除 | two-generation の report field assert |

pytest は実走していません。したがって上記テストを「緑」とは報告しません。

## 総括

- 実装単位は 8c の internal ratio 正規化、role percent 射影、report ratio 保存の三点。
- 所有ファイルは `p3_autonomous_workload_trial.py`、`p3_s4_loop.py`、対応テストの三本。
- `current_perf` と `baseline` の recipient matrix、planner の絶対 throughput は維持する。
- `delta_pct≡None` と `WhiteboardLeakError`、凍結 `output/`、role md は変更しない。
- 主リスクは report v2 互換、role 文書に残る “leading-indicators only” の説明矛盾、片側だけ射影を迂回する wiring drift。
- テストは未実走であり、結果の緑は主張しない。