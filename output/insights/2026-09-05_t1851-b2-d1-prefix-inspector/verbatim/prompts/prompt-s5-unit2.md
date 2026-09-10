単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定。**plan v2 節・変異事前登録・不変 pin 表が本作業の契約**であり、段 2 plan と食い違う点はこちらが正しい
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md` — 段 2 plan。4〜5 節 (D1-a / D1-c / D1-d)、7〜8 節 (赤・pin・テスト計画) が unit 2 の土台
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s3-lens-a.md` と `s3-lens-b.md` — 段 3 の敵対所見。裁定で「採用」とされた所見の (d) 修正案を実装に反映する
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md` — 親 brief (件数は裁定末尾の訂正が優先)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1337 / D1522 / D1533)

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit2` (branch `impl-dev-wave-t1851-b2-d1-unit2`、base `50dbf9158`) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_floor_contract.py`
- `orchestrator/campaign/s8b_floor_stats.py`
- `orchestrator/tests/test_s8b_floor_contract.py`
- `orchestrator/tests/test_s8b_floor_stats.py`

`attempt_registry_core.py`、`s8b_attempt_registry.py`、`s8b_holdout_freeze.py`、`s8b_ratified_freeze.py`、`s8b_floor_campaign.py`、fixture、docs、他の test file は所有外である。
所有外に必要な変更が見つかったら実装せず完了報告に書け。docs の編集と commit はしない。

## 前提 — unit 1 が並行して実装する API (本 worktree には無い)

unit 1 が `attempt_registry_core.py` と `s8b_attempt_registry.py` へ次を足す。**本 worktree にはまだ存在しない**ので、unit 2 の実装は
局所 import と monkeypatch で結合し、統合後に親が実走する。

```python
# attempt_registry_core
ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA = "s8b-floor-attempt-registry-proof/v1"
ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS = frozenset({"schema", "registry_schema", "freeze_sha256", "protocol_sha256", "schedule_sha256", "row_count", "chain_head_sha256"})
def validate_attempt_registry_prefix_proof(value: object) -> dict[str, object]: ...   # exact 7 key、literal、hex64、正整数、nonzero head

# s8b_attempt_registry
def inspect_attempt_registry_prefix(repo_root: Path, *, expected_binding: S8BAttemptBinding, row_count: int, chain_head_sha256: str) -> dict[str, object]: ...
```

`validate_attempt_registry_prefix_proof` は unit 1 の所有なので、unit 2 の verifier は局所 import で呼ぶ。統合前に本 worktree で走らせるときは
`monkeypatch.setattr(core_module, "validate_attempt_registry_prefix_proof", fake, raising=False)` の形で差し込んでよいが、**production code 側に fallback を書いてはならない**
(import できなければ例外のまま)。registry schema literal は `s8b_attempt_profile.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION` (現物名を確認せよ) を使う。

## 依頼 — unit 2: D1-a (契約) → D1-c (pure verifier) → D1-d (live wrapper)

裁定の plan v2 節 5〜7 と、段 2 plan 4〜5 節を実装する。

### D1-a (`s8b_floor_contract.py`)

- `LEGACY_RESULT_SCHEMA = "s8b-floor-result/v4"`、`RESULT_SCHEMA = LEGACY_RESULT_SCHEMA` (**値は変えない**)、`RESULT_SCHEMA_V5 = "s8b-floor-result/v5"`、
  `READABLE_RESULT_SCHEMAS = frozenset({LEGACY, V5})`、`_RESULT_V4_KEYS` (既存集合)、`_RESULT_KEYS = _RESULT_V4_KEYS` (alias 保存)、
  `_RESULT_V5_KEYS = _RESULT_V4_KEYS | {"attempt_registry"}`、`_RESULT_KEYS_BY_SCHEMA`。
- `result_keys_for_mode(mode, *, schema: object = LEGACY_RESULT_SCHEMA, perf_preflight=None)`。未知 schema は `FloorContractError` で拒否。既存 12 呼出しは無変更で互換。

### D1-c (`s8b_floor_stats.py` `verify_floor_artifact`)

- signature に kw-only `expected_attempt_registry: Mapping[str, object] | None = None` を足す (既存の必須 kw は不変)。
- schema dispatch: v4 は従来の key 集合 (top-level `attempt_registry` は既存 exact key 経路で拒否)。v4 で `expected_attempt_registry` が非 None なら caller 契約違反として拒否。
  v3 等の非 readable schema は既存 error 文字列 `"artifact.schema が 's8b-floor-result/v4' でない"` を保存する (`test_s8b_floor_stats.py:1323-1325` は不変 pin)。
- v5: top-level exact key で `attempt_registry` を必須化 → 局所 import した `validate_attempt_registry_prefix_proof` で shape 検査 →
  **`proof["freeze_sha256"] == artifact["freeze_sha256"]`、`proof["protocol_sha256"] == artifact["protocol_sha256"]`** を検査 (レンズ A-1 / B-3) →
  `expected_attempt_registry` は非 None 必須で同 validator を通し、`reported == expected` の 7 field 等値を検査。比較の向きは reported を expected へ流用しない。
  拒否は既存の error list 形式に揃え、理由文字列は 1 検査 1 文字列で固定する。

### D1-d (`s8b_floor_stats.py` `verify_floor_artifact_with_live_admission`)

- 既存 signature は不変。artifact の schema が v5 のときだけ、関数内で `from . import s8b_attempt_registry as _attempt_registry` を局所 import し
  `_attempt_registry.inspect_attempt_registry_prefix(repo_root, expected_binding=..., row_count=..., chain_head_sha256=...)` を呼ぶ。v4 / v3 / 欠損 schema では registry を一切読まない。
- expected binding は**外部引数だけ**から作る: `freeze_sha256` = 引数、`protocol_sha256` = `_floor_contract.canonical_protocol_sha256(protocol)`、
  `schedule_sha256` = `hashlib.sha256(core.canonical_json_bytes(list(schedule))).hexdigest()` (`attempt_registry_core.canonical_json_bytes`)。
  binding の型は `s8b_attempt_profile.S8BAttemptBinding` (局所 import)。reported proof の binding を path 選択にも expected にも使わない。
- reported proof は shape 検査して `row_count` / `chain_head_sha256` だけを inspector へ渡し、返った独立 proof を pure verifier の `expected_attempt_registry` へ渡す。

### テスト (裁定の変異事前登録 M11〜M16 を観測する node を必ず置く)

`test_s8b_floor_contract.py`: 既存 2 node を拡張 (旧 assertion はすべて残す) — v4 current / v5 別名 / readable 集合、v5 = v4 ∪ {attempt_registry} (M11)、
schema default が v4、未知 schema 拒否。**pilot / official × perf の各 v4 key set を直接取得し `"attempt_registry" not in keys` を literal で固定する** (M15、D1522)。

`test_s8b_floor_stats.py` (honest v4 artifact を schema / key / proof だけ v5 へ変換する helper を置き、各 v5 test は perf / admission / session / binary の各 gate が同じ入力を拒否しないことを先に assert する):

- `test_pure_verifier_accepts_v5_with_independent_prefix_proof` (正例)
- `test_pure_verifier_rejects_v4_attempt_registry_as_extra_key`、v4 で `expected_attempt_registry` 非 None を拒否、v5 で `expected_attempt_registry=None` を拒否
- `test_v5_rejects_missing_attempt_registry_proof`
- `test_v5_rejects_reported_prefix_head_tamper` (pure verifier 直接。M12)
- `test_v5_rejects_artifact_header_freeze_tamper` / `..._protocol_tamper` (artifact の header だけを変える。M16)
- `test_v5_rejects_proof_binding_mismatch[freeze|protocol|schedule]` (reported proof の binding だけを変え、expected は正しい)
- `test_live_v4_does_not_call_attempt_registry_inspector` (inspector を tripwire にして v4 を通す。M13)
- `test_live_v5_calls_inspector_and_compares_reported_to_independent_proof` (fake inspector を monkeypatch (`raising=False`) し、
  受け取った `expected_binding` が外部引数から導出した値と一致すること、1 回呼ばれたこと、返した proof が pure verifier の expected に使われたことを assert。
  M14 の段 5 版。正例対照を同じ test に置く)
- D1522: 上流 (exact key) が拒否する形でも、下層 (`result_keys_for_mode` の各集合、pure verifier の等値比較) を直接名指しする検査を置く。

## 検査・報告 (DW-S05-C)

- 実走できる範囲で `python3 -m pytest orchestrator/tests/test_s8b_floor_contract.py orchestrator/tests/test_s8b_floor_stats.py -q` を走らせ、緑には実走 nodeid・範囲を併記する。
  unit 1 の API が無いために走らない node は「実装済み・未実走 (unit 1 待ち)」と明記する。
- テスト新設の単位は、親の名指しを網羅と見なさず制約 meta-test (`test_official_perf_closure.py` の surface inventory、file 列挙 meta-test、`test_check_docs` 系) を自ら洗い出して走らせる。
  `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact` が `result_keys_for_mode` の signature を pin していないか現物で確かめ、赤になるなら所有外として報告せよ (直さない)。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。production code に fallback / 互換 shim を書かない。
- 完了報告に、所有外 caller (`s8b_holdout_freeze.py:1429,1620`、`s8b_ratified_freeze.py:2360,3281`、`s8b_floor_campaign.py:6684`) と共有 fixture
  (`s8b_v2_freeze_fixture.py:340`、`test_s8b_ratified_verify.py:460`、`test_s8b_floor_campaign.py:6552`) への波及可能性を静的列挙する。
- 指示外の受理集合変更をしない。scope 前の受理・拒否挙動 (v4 artifact の受理集合不変、v3 拒否文字列不変) を報告に明記する。不変 pin 表の node は 1 行も変えない。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、変更 file と行数、新設 test node 数、実走結果 (nodeid 範囲と passed / failed 件数、unit 1 待ちの件数)、所有外への波及、未実装項目を 10 行以内で書け。
