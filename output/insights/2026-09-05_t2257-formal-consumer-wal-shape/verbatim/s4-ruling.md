# 段 4 裁定 — [T-2257] plan v2 と変異事前登録 (親、2026-09-05 13:20 JST)

裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox`) と local main の進行 (f4c247b0d、裁定 fragment のみ) を再走査した。
T-2257 に触れる新裁定は無い。D1555 の前提 (consumer 側の修理は provisioning と独立に必要) は不変。

## 所見の裁定

| 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | payload の key 集合を `{build_attempt_id, trigger_gate_binding}` に閉じていない | real | 採用 (FC05C)。production の `validate_trigger_bindings` も exact key 集合 (`wal.py:84-86`) を要求しており整合 |
| A-2 | root に `build_attempt_id` を足した record は `_projection_attempt_id` の root 優先で payload 不一致が隠れ、`_wal_trigger` が受理する | real | 採用。trigger record の outer key 集合を production の `{variant, stage, env_tag, ts, payload}` に exact で閉じる (`wal._record_to_line` が書く key と同一)。payload の attempt 一致検査は consumer に**足さない** — outer 閉包があれば root shadow は FC05C、root 無しの payload 不一致は既存 FC05B (resolve 段) が拒否するので、同じ入力を拒否する層を二重にしない (DW-M01 単一理由性) |
| A-3 / B-1 | 正例が mask 7・nonce `"a"*64`・source=None の 1 点だけで、「その nonce だけ許す」「source 付きを拒否する」変異が生き残る。ledger commitment を同じ binding から導く正例単独では commitment 比較脱落を殺せない | real | 採用。producer 実走正例を `(mask=18, nonce="b"*64, source=SourceBinding(src_token="fixture-src", source_bytes_sha256="c"*64))` でも通す。独立 pin として、逐語 literal test は producer が書いた `build_start` 行の `trigger_gate_binding_commitment` (`3971d4e14424e4d13bd63fc709a993ee12d8dfe13e072ce9960c9e51fa0b7029`) と `_wal_trigger()` の射影値の一致を assert する (consumer とは別経路で producer が計算した値) |
| A-nit | 正例の projection が trigger 直後に legacy abort で、production の trigger→build_start 系列ではない | real (nit) | 採用 (安い)。逐語 literal test は LINE 1 (trigger) と LINE 2 (build_start) の 2 行を逐語で持ち、attempt id だけ fixture に移植した上で fixture terminal を続ける。名称・docstring に「逐語から attempt だけ移植」と書く (B-nit) |
| A-nit | binding 2 本の拒否は production 履歴を失わない (別 attempt は projection 混在で拒否済み) | real | 記録のみ。(P1) の「ちょうど 1」を維持 |
| B-2 | brief が FC06 test (`test_reflux_formal_consumer.py:540-552`) の旧形状依存を列挙していない | real | 採用。plan の donor raw binding コピーで追随 |
| B-3 | `_rewrite_wal()` が root に `build_attempt_id` を足すと production 形状でなくなる | real | 採用。既存の格納位置 (root にあれば root、なければ payload) だけを書き換える |
| B-4 | `test_reflux_*.py` は pytest-only allowlist。`python3 file.py` は 0 件 exit 0 | real | 採用。親の焦点走は `python3 tools/run_tests.py <files>` 経由。brief の「自走 harness」記述を訂正 |
| B-5 | fixture builder test の自己整合検査は余分な root key でも通る | real | 採用。`test_reflux_origin_fixture_builder.py` に trigger record の outer / payload / raw の exact key 集合 assertion を足す |
| B-nit | duration ledger は nodeid 単位。新 node は実測後に登録 | real | 親が段 7 前に `tools/update_acceptance_duration_ledger.py` の手順で登録する (受入全走の結果から) |
| B-nit | producer の将来 drift 時の扱い | real | insight に記す: 裁定済みなら consumer と literal を更新、未裁定なら producer 側の回帰。旧 literal の互換受理は足さない |
| (P3) | terminal `kind` は据え置き | 両レンズ支持 | 段 7 で新規 carry。production terminal は `stage` が `commit`/`abort` (`model.py:24-36`) で outer に `kind` は無いので、修理後も本番 projection は FC07 で止まる。この wave の成果は「FC05C を production 形状で通す」であり end-to-end ではないと明記する |

(P1)(P2)(P4)(P5) は上記の補強付きで確定。`wal.py` は不変 (両レンズとも producer 変更不要を確認)。

## plan v2 (実装子への確定指示)

1. `orchestrator/campaign/reflux_formal_consumer.py`
   - import: `from . import trigger_gate_binding`、`from .reflux_ir import TriggerGateIR, encode_wire`、
     `from .wal import TRIGGER_BINDING_COMMITMENT_KEY, TRIGGER_BINDING_PAYLOAD_KEY`。
   - `_wal_trigger(records)`: (a) `record.get("stage") == trigger_gate_binding.WAL_RECORD_STAGE` の record を数え、
     1 件でなければ None。(b) その record の key 集合が exact `{"variant","stage","env_tag","ts","payload"}` でなければ None。
     (c) `payload` が exact dict で key 集合が exact `{"build_attempt_id", TRIGGER_BINDING_PAYLOAD_KEY}` でなければ None。
     (d) `trigger_gate_binding.validate_record(payload[TRIGGER_BINDING_PAYLOAD_KEY], require_source=False)`、
     `TriggerGateBindingError` は None。(e) `{"mask": binding.mask, "candidate_wire": encode_wire(TriggerGateIR(binding.mask)),
     TRIGGER_BINDING_COMMITMENT_KEY: trigger_gate_binding.commitment(binding)}` を返す。
   - `_validate_bijection()` の比較式は不変 (exact dict 比較)。
   - 他の関数 (`_validate_wal_outcomes` の `terminal.get("kind")` を含む) は触らない。
2. `orchestrator/tests/reflux_origin_fixture_builder.py`: plan のとおり `_fixture_trigger_gate_binding(mask)` (nonce `"a"*64`、
   source None)、`_trigger_binding(mask)` の commitment は `trigger_gate_binding.commitment(binding)`、`candidate_wire` は独立
   `_wire()` を維持、`_wal_records()` の trigger record を production 形状 (`variant:"fixture-v"`, `stage`, `env_tag:"fixture-env"`,
   `ts: 0` (int), `payload:{build_attempt_id, trigger_gate_binding: to_record(binding)}`)。terminal は不変。module docstring の説明を更新。
3. `orchestrator/tests/reflux_origin_fixture_baseline.json`: 独立再計算で `build_execution_provenance`、`build_ordered_wal_projection`、
   `build_result_evidence_record` の 3 entry だけ更新。他 entry は不変。
4. `orchestrator/tests/test_reflux_origin_fixture_builder.py`: trigger record の outer / payload / raw の exact key 集合と
   `stage` 値の assertion を追加 (`test_fixture_repository_writes_33_consistent_create_only_records` 付近か新 test)。
5. `orchestrator/tests/test_reflux_formal_consumer.py`:
   - `_rewrite_wal()` は既存の格納位置だけを書き換える。
   - 既存 3 test の追随: `test_fc05c_rejects_wal_trigger_binding_mismatch` (raw nonce を別の valid 64 hex に)、FC06 test (donor の
     production raw binding をコピー)、FC07 verify-config test (現在の projection の trigger を保存し terminal だけ commit に)。
   - 正例 (全て `_evaluate(case)` が P6Unavailable まで到達):
     P-1 producer 実走 (mask 7、nonce "a"*64、source None): `CampaignLayout(tmp_path/...).ensure()` → `wal.log_trigger_binding()` →
     `runs/wal.jsonl` の 1 行を `json.loads` → fixture terminal と共に `_rewrite_wal`。戻り commitment == ledger commitment を assert。
     P-2 producer 実走 (mask 18、nonce "b"*64、source=SourceBinding("fixture-src", "c"*64)): ledger と execution provenance の
     `trigger_binding` を同じ binding から (`mask`, `_wire`-相当の wire, `commitment`) に揃えて通す。
     P-3 逐語 literal: refs/producer-verbatim-record.txt の LINE 1 と LINE 2 を文字列 literal で保持し、`json.loads` 後に
     attempt id だけ fixture の attempt へ移植、fixture terminal を続ける。`_wal_trigger()` の射影値の commitment が literal の
     build_start の `trigger_gate_binding_commitment` と一致することを assert (独立 pin)。
   - 負例 (全て FC05C):
     N-1 旧形状 (`{"kind":"TriggerGateBinding","build_attempt_id":..,"trigger_binding": ledger と同値}`)。
     N-2 stage 不一致 (valid payload、stage を `"build_start"` に)。
     N-3 duplicate (valid production trigger 2 本、同値)。
     N-4 duplicate の 2 本目が payload 不正 (stage 個数で数えることの検査)。
     N-5 raw binding に余分な key。
     N-6 payload に余分な key (`"extra": 1`)。
     N-7 root shadow (production record に root `build_attempt_id` = physical attempt を足し、payload の attempt を別値に)。
     N-8 mask-only mismatch (ledger と provenance の mask だけ 31、wire と commitment は据え置き)。
     N-9 commitment-only mismatch (ledger と provenance の commitment だけ別の valid sha256)。
     N-10 source-only mismatch (P-2 の binding で、WAL 側 raw の source を None に差し替え、ledger commitment は source 付きのまま)。
     N-11 source 付き raw を消す変異の検出は P-2 が担う (負例ではなく正例)。

## 変異事前登録 (DW-M01、実装前に凍結。位置は consumer のみ)

| # | 変異 (consumer 内) | 殺すテスト (期待) | 単一理由 |
|---|---|---|---|
| M1 | root `kind`/`trigger_binding` 形状も読む fallback を足す | N-1 | 旧形状を同値で置くので M1 だけが P6Unavailable へ抜ける |
| M2 | selector を「payload に key があるか」だけにし stage を見ない | N-2 | raw と ledger は一致、stage 判定だけが差 |
| M3 | 射影の `mask` を ledger の値で埋める (比較脱落) | N-8 | wire/commitment/provenance は一致、mask 差だけ |
| M4 | 射影の commitment を ledger の値で埋める (比較脱落) | 更新済み FC05C test (nonce 差) と N-9 | mask/wire は同じ、commitment だけ差 |
| M5 | stage record が複数なら先頭を返す | N-3 | 2 本とも valid・同値 |
| M6 | `encode_wire` の代わりに MSB-first で wire を作る | 既存 `test_exact_fixture_contract_reaches_only_p6_unavailable` + P-1〜P-3 | mask 7 = "11100" は非対称 |
| M7 | `validate_record` を呼ばず既知 field を直接読む | N-5 | exact raw key 集合だけが差 |
| M8 | stage record のうち payload が valid な最初の 1 件を返す | N-4 | 個数を先に数える実装だけが FC05C |
| M9 | outer key 集合の閉包を落とす | N-7 | root shadow は FC05B を通り、M9 だけが受理 |
| M10 | payload key 集合の閉包を落とす | N-6 | payload 余分 key だけが差 |
| M11 | `binding.source is not None` を None (拒否) にする | P-2 | source 付き正例だけが差 |

受理集合を縮小する wave なので、過剰拒否の正例は P-1〜P-3 (と既存の 33 record fixture 正例) が担う。
実装後に各変異の赤理由が一つに絞れることを親が確認し、絞れない変異は登録から外して再照準する (F820/F28)。

## 実装子の path allowlist (ちょうど 5 本)

- `orchestrator/campaign/reflux_formal_consumer.py`
- `orchestrator/tests/reflux_origin_fixture_builder.py`
- `orchestrator/tests/reflux_origin_fixture_baseline.json`
- `orchestrator/tests/test_reflux_origin_fixture_builder.py`
- `orchestrator/tests/test_reflux_formal_consumer.py`
