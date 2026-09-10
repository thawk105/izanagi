## 所見

- **must-fix なし。**
- **D-01 / nit / [test_t316_sandbox_probe.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:185)** — 同じ root-location-only family を正例で1回、交叉負例で2回、計3回生成している。`tmp_path` ごとに再構築されるため cache hit はなく、同一意味の実 CMake configure/preprocess が重複する。機能・受理集合は壊さないため nit だが、推定で約1〜3秒は重複分。
- 新しい `comparison` により赤になる既存 assert はない。[test_t316_sandbox_probe.py:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1318) の exact equality は更新済み `_condition_gate_receipts()` 同士の比較なので通り、同ファイルの全 consumer も同じ helper 経由で更新される。
- 新 test は C++ compiler、CMake、fixture、書込み可能な `tmp_path`、実 preprocess を必要とする。欠ければ skip ではなく `assert`/例外で赤になるが、[test_t316_sandbox_probe.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:156) の既存 `_condition_gate_family` と同じ扱いで、新しい依存クラスではない。対して gate 側同型 test は [test_condition_meaning_gate.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py:47) で欠損時に skip する。無条件 skip はない。
- `tmp_path` は node ごとに固有で copy 先も固定名なので衝突しない。cache 対象の `_requested_default_condition_gate_family` は `tmp_path` や環境由来値を引数・保存 root に持たず、process/session 間の汚染はない。filesystem 順序や固定 digest への依存もない。
- 交叉負例の差替えは [test_t316_sandbox_probe.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1027) の pytest `monkeypatch.setattr` 経由で、各 parameter node の終了時に復元される。手書き `setattr` や復元漏れはない。
- 差分は production と t316 test の2ファイルだけ。gate 本体、policy、hooks、受入所要台帳、docs、`test_condition_meaning_gate.py` は変更されていない。

## 波及一覧

- Production:
  - `_condition_gate_receipt_summary` → [validator:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:376)、[build receipt生成:1923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:1923)。両方通る。
  - `condition_gates` → build で生成、[observe_s6:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2065) で伝播、[verdict_s6:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:399) で照合、最終 receipt に保存。新 field を含む同一 summary で通る。
  - `_INERT_CONDITION_GATE_PAIRS` → [_condition_gate_family_valid:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:381) のみ。正しい2組は通り、交叉・第3 reason は落ちる。
- Test fixtures:
  - `_condition_gate_receipts` → `_good_s6`、新規5 node、[receipt exact assert:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1318)。すべて更新後の field 集合で通る。
  - `_good_s6` → `_good_stages`、既存 S6 judge、missing/live-family/receipt-mismatch test、injected S6 test、新規5 node。負例は意図した `inconclusive`/`no-go`、それ以外は通る。
  - `_good_stages` → [1123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1123)、[1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1136)、[1164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1164)、[1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1178)、[1193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1193)、[1306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1306)、[1346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1346)、[1356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1356)、[1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1367)、[1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1395)。すべて `_good_s6` 経由で新 summary を受け取り、落ちない。
  - gate 側既存 assert [root-location-only:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py:674)、[identity:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py:878) は evaluator evidence の検査であり、receipt field 追加の影響を受けない。

## 新規 nodeid の完全列挙

- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[identity]`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_s6_rejects_requested_default_preprocess_difference`

## 所要の見積り

新規分は supply evaluator を4回起動する。内訳は root-location-only が3回、requested/default が1回。identity は既存 `_condition_gate_family` の `lru_cache` を再利用する。

同型 evaluator は1回につき requested/control の CMake configure 2回と preprocess 2回を行うため、増分は概ね **CMake configure 8回＋実 preprocess 8回**。root fixture の copy は3回。`declaration=None` の meaning arm は実 preprocess を増やさない。

投影資料には pytest の elapsed 秒や台帳値がないため静的推定だが、小型 fixture の既存同型 node 4個相当として **全体で約2〜6秒増**。このうち root family の2回分、約1〜3秒が重複相当で、D-01 の nit とした。

## 裁定パッケージ候補

新規なし。段4で既に scope 外とされた JSON scalar 型厳密化、receipt schema 版管理、t316 実経路の到達実測は再提起しない。

## 総括

**GO。must-fix はない。**  
受理集合は指定された2組に限定され、既存 consumer/assert の取り残しもない。  
実行環境依存と hard failure は既存 t316 fixture と同等で、skip 恒真化や monkeypatch 漏れもない。  
唯一の nit は実 preprocess の重複による推定1〜3秒の余分な所要。親は上記5 nodeidを受入台帳へ追加すればよい。