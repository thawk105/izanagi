# 段 4 裁定 (確定)

wave: dev-wave-c05-schedule-consumer / base main **64d37b1a** (ff-only 取り込み済み)
2026-08-18 18:49 JST 実測

## 所見の裁定

レンズ A 8 件 + レンズ B 8 件 = 16 件。重複を統合して裁定する。

| id | 深刻度 | 判定 | 採否 | scope |
|---|---|---|---|---|
| C05-IMPORT-004 / B-04 | blocker | real | 採用 | 内 |
| C05-BIND-003 / B-02 / B-03 | blocker | real | 採用 | 内 |
| C05-NC-002 / B-05 (後半) | major | real | 採用 (must-fix) | 内 |
| B-01 (`schedule_index` の二義化) | blocker | real | 採用 (改名不可のため明示で処理) | 内 + 一部外 |
| C05-STATE-006 | minor | real | 採用 | 内 |
| B-07 (自走 harness) | minor | real | 採用 | 内 |
| B-08 (brief の stale 記述) | nit | real | 採用 (訂正済み) | 内 |
| C05-GEN-007 | major | real | 部分採用 | 一部内 |
| C05-AST-001 / B-05 (前半) | major | real | 部分採用 | 一部内 |
| C05-LAUNCH-005 | blocker | real | 部分採用 | 一部内・大半外 |
| C05-CONSUME-008 / B-06 | major | real | 不採用 (明記のみ) | 外 |

### 統合裁定 1 — 依存性逆転 (blocker 3 件を 1 つの是正で解く)

**real。採用。** 実測 (親): レンズ B が名指しした権威 `WORKLOADS` (p3:208)、`ROLE_FILES` (p3:244)、
`ROLE_CONTRACTS` (p3:254)、`GATING_SPEC` (p3:305) は**すべて p3 の中にある**。
一方で契約 `reachable_from` は `run_trial -> verify_schedule` を要求する = p3 が新 module を
import する向き。よって新 module が p3 を import する設計は成立しない (循環)。
レンズ A の追加事実により function-local import への逃げ道も塞がれている
(evidence の resolver は module-level import しか束縛しない)。

→ **新 module は権威を引数で受け取る (dependency inversion)。**
`search_space_digest(authority)` / `initial_state_digest(authority)` は供給された authority の
純関数とし、authority の **key 集合を閉じて strict 検証**する。
key の欠落・余剰・型違反は `ScheduleError` (fail-closed)。

これで同時に解ける:
- 循環 import が消える (新 module は真の leaf)。
- 「実体が変わっても hash が変わらない」空洞が閉じる (authority の全 field が preimage に入る)。
- 「6 cell の hash が互いに等しいだけ」の恒真性が消える (外から供給された期待値との照合になる)。
- **部分的な authority では digest を計算できない**ため、抜けを黙って通す経路が無い。

brief の **(P4) は棄却**。段 2 プランの p3 import 案も棄却。

canonical JSON は**公開ヘルパ** `reflux_origin_artifacts.canonical_json_bytes` (:55、
標準ライブラリのみ import する leaf) を使う。段 2 プランが挙げた private
`s8b_prediction_runner._canonical_json_bytes` の跨ぎ参照は棄却 (B-04)。

### 統合裁定 2 — 負の対照を単一理由にする (must-fix)

**real。採用。** DW-M03 と F394 に直接抵触。
`verify_shared_search_space_and_initial_state` を**期待 hash を引数で受け取る形**にする。
負の対照は artifact bytes を無改変のまま、**期待 initial-state hash の 1 bit だけを反転**して
実関数へ渡す。exact bytes 検証は通り、shared hash 検証だけが赤になる = 単一理由。
判定関数を monkeypatch しないので F394 の禁止に触れない。

### 統合裁定 3 — `schedule_index` の二義化 (B-01)

**real。** ただし契約 JSON が `cells[*].schedule_index` を required field として固定しており、
本 wave は契約を 1 byte も変えない。**改名できない。**

採る是正:
- module docstring と field の docstring に、この添字が **cell ordinal (0..5)** であり、
  `s8b_oracle_manifest` の反復内 row 添字・`s8b_oracle_n_pilot` の observation `seq`・
  `s1_direct_comparison` の attempt 添字とは**別空間**であることを明記する。
- `Schedule` dataclass の field 名を module 内部では `cell_ordinal` とし、
  artifact の JSON key だけが契約どおり `schedule_index` になるようにして、
  コード上の取り違えを型で防ぐ。
- 観測 row との一対一対応付けは後続 wave → **裁定パッケージ**。

### 統合裁定 4 — 部分採用のもの

- **C05-GEN-007**: schema へ `generator_version` を入れる (内)。
  generator の source hash を artifact へ焼くのは F36「hash 自己参照は禁止」に触れるため採らない。
  事前 commit 済み artifact + §5 seed の固定は (P2) により外 → 裁定パッケージ。
- **C05-AST-001 / B-05**: `_evaluate_c05` は関数の存在と呼出し関係に加えて
  **必須 field literal の出現**も要求する (C02 の `binding_fields` と同じ手法)。完全な
  データフロー証明は AST 静的解析の枠外 → 裁定パッケージ。
  C02・C04・C05 で 3 例目のため DW-G03 の「独立 2 例」を満たし、族一般化を提案する。
- **C05-LAUNCH-005**: 契約の `reachable_from` は 2 本 —
  `run_trial -> load_schedule -> launch next cell` と
  `run_trial -> verify_schedule -> consume_schedule`。evaluator は**両方**を検査する (内)。
  値伝播と launch での実消費の証明は production 配線が前提で (P3) により外 → 裁定パッケージ。

### 不採用 (明記のみ)

- **C05-CONSUME-008 / B-06**: 一対一消費追跡・反復・attempt・receipt は
  trial registry (条件 3・4) と observation 層の責務。module に持ち込むと責務が二重化する。
  module docstring に「本 artifact は **cell 単位の seed schedule** であり、
  反復・attempt・observation の完全 block ではない。`consume_schedule` は使用履歴を追跡しない」
  と明記する → 裁定パッケージ。

## brief の訂正 (B-08、親が実測)

brief「並行 wave の危険」の「t1333 が `test_s8c_preregistration_predicates.py` を所有中」は
**stale**。実測: `git merge-base --is-ancestor worktree-dev-wave-t1333-t1310-workload-profile main`
が真 = t1333 の tip は main に取り込み済み。`git diff --name-only main...<branch>` も空。
本 wave は 18:49 JST に main を `38f173cb` → `64d37b1a` へ ff-only 取り込み済み。

残る間接衝突は `worktree-dev-wave-t1286-commit-receipt` が
`orchestrator/tests/test_p3_autonomous_workload_trial.py` を触る点だけで、
本 wave の編集面とは重ならない。

## プラン v2 (段 5 の確定仕様)

### 単位 A — `orchestrator/campaign/s8c_schedule.py` + `orchestrator/tests/test_s8c_schedule.py`

**import は標準ライブラリと `from . import reflux_origin_artifacts` だけ。**
`p3_autonomous_workload_trial` を import しない (文字列としても書かない)。
`trial_registry` も import しない。

top-level 関数だけで構成する (class にまとめない。AST ヘルパ `_functions` は module 直下しか見ない):

```
SCHEDULE_SCHEMA_VERSION = "s8c-schedule/v1"
GENERATOR_VERSION       = "s8c-schedule-generator/v1"
ARMS      = ("on", "off", "swapped")
HOLDOUTS  = ("H1", "H2")

class ScheduleError(ValueError)
@dataclass(frozen=True) class ScheduleCell:  cell_ordinal, holdout, arm,
                                             search_space_sha256, initial_state_sha256
@dataclass(frozen=True) class Schedule:      schema_version, generator_version,
                                             master_seed, cells

SEARCH_SPACE_AUTHORITY_KEYS  = frozenset({...})   # 閉じた key 集合
INITIAL_STATE_AUTHORITY_KEYS = frozenset({...})   # 閉じた key 集合

def validate_authority(authority) -> None
def search_space_digest(authority) -> str
def initial_state_digest(authority) -> str
def regenerate(master_seed, *, authority) -> bytes
def load_schedule(path) -> bytes
def verify_exact_schedule_bytes(artifact_bytes, *, master_seed, authority) -> None
def verify_shared_search_space_and_initial_state(
        schedule, *, expected_search_space_sha256, expected_initial_state_sha256) -> None
def verify_schedule(artifact_bytes, *, master_seed, authority) -> Schedule
def consume_schedule(artifact_bytes, *, master_seed, authority, schedule_index) -> ScheduleCell
```

- `verify_schedule` は `verify_exact_schedule_bytes` と
  `verify_shared_search_space_and_initial_state` の**両方**を live に呼ぶ。
- `consume_schedule` は `verify_schedule` を live に呼ぶ。
- authority の key 集合は閉じており、欠落・余剰・型違反はすべて `ScheduleError`。
  **部分 authority で digest を計算できてはならない。**
- artifact JSON: top-level は `schema_version` / `generator_version` / `master_seed` / `cells`。
  cell の key は `schedule_index` / `holdout` / `arm` /
  `search_space_sha256` / `initial_state_sha256` のみ (契約どおりの綴り)。
- 6 cell = 2 holdout x 3 arm、`schedule_index` は 0..5 の全単射。
  順序は `sha256(canonical_json({domain, master_seed, holdout, arm}))` の安定 sort。
- 真を返す既定路を作らない。不一致・欠落・余剰・型違反・重複はすべて raise。

テストは自走 harness 必須:
`if __name__ == "__main__": raise SystemExit(pytest.main([__file__, "-x"]))`

### 単位 B — `_evaluate_c05` + 負の対照

- `ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE = "schedule-consumer-unreachable"` を
  `SCHEDULE_CONSUMER_UNDEFINED` の直後へ追加。
- `_evaluate_c05` を `_evaluate_c09` の直前へ。**`_MACHINE_EVALUATORS` へ登録しない。**
  `SATISFIABLE_CONDITION_IDS` を変えない。SATISFIED を返す branch を作らない。
  終端は必ず `COMPLETION_PROOF_NOT_MACHINE_CHECKABLE`。
- 負の対照は `NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES` へ分離し、
  既存 `NEGATIVE_CONTROL_CASES` と 2 本のメタテストの期待集合を**変えない**。

## 変異事前登録 (DW-M01)

| id | 位置 | 変異 | 期待 |
|---|---|---|---|
| c05.m01 | `verify_shared_search_space_and_initial_state` | 先頭へ `return` を入れ常時許可 | KILLED (F394 必須) |
| c05.m02 | `verify_exact_schedule_bytes` | `!=` を `==` へ反転 | KILLED |
| c05.m03 | `verify_schedule` | shared 検証の呼出しを削除 | KILLED (統合裁定 2 の証拠) |
| c05.m04 | `regenerate` | 順序 hash の preimage から `master_seed` を落とす | KILLED |
| c05.m05 | `validate_authority` | 欠落 key の検査を削除 | KILLED (統合裁定 1 の証拠) |
| c05.m06 | `search_space_digest` | preimage から authority の 1 field を落とす | KILLED |
| c05.m07 | strict decoder | cell 数 6 の検査を削除 | KILLED |
| c05.m08 | strict decoder | `schedule_index` の一意性検査を削除 | KILLED |
| c05.m09 | `consume_schedule` | `verify_schedule` の呼出しを削除 | KILLED |
| c05.m10 | `_evaluate_c05` | consumer 不在の分岐を常時 skip | KILLED |

各変異は、同じ入力を拒否する層が前後に無いことを実装確認してから本登録する。
確認できないものは登録せず実効 gate へ再照準する (DW-M01)。

## 裁定パッケージ (ユーザーへ返す)

1. **activation wave (原子・最優先)**: 契約 `machine_checkable` 反転 + evaluator 登録 +
   `DECIDER_VERSION` bump + 凍結世代 g8 + §5 `master_seed` 記入 + schedule artifact の commit。
   F393/D520 に従い**同一 commit・最後の取り込み直後**。並行 wave が g8 を先取りしたら
   新 main の直上へ組み直す。
2. **production 配線**: `run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch`
   の値伝播。ここで authority の実体 (`WORKLOADS` / `ROLE_FILES` / `ROLE_CONTRACTS` /
   `GATING_SPEC` / descriptor binding) を供給する。
3. **`schedule_index` と観測 row の一対一対応**: 反復・attempt・observation・receipt との束縛
   (§6 前提条件 4・7)。同名添字の二義化を解く規約が要る。
4. **evaluator の検査力の族一般化**: C02・C04・C05 の 3 例で AST token-only の弱さが再現。
   DW-G03 の「独立 2 例」を満たす。
5. **generator の独立性**: 事前 commit 済み artifact + §5 seed + 発効単位での固定。
