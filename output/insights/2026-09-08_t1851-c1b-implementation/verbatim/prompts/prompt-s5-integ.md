単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — **契約の正本。** 本作業の範囲は **5 節 (観測後の理由を別 field に載せる)、6 節 (封印の発行経路と信頼境界)、7 節 (crash 後の権威)、8 節 (採らないもの)、9 節 (射程の限界)**。1〜4 節は leaf が実装済みで、統合側はそれを**呼ぶ側**である。
2. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/plan-v2.md` — 実装手順。**4 節 (実装子 2 = 統合の plan) が本作業の範囲**である。3 節 (leaf) は実装済みなのでやり直さない。
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md` — 親の段 4 裁定。**4.2 の S1・S2 が本作業の変異照準**である。2 節の P1・P2 も読め。
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s1-brief.md` — 親 brief。5 節の不変条件。
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1113 / D1341 / D1522)。
6. `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ/orchestrator/campaign/s8b_terminal_evidence.py` — **leaf の実装 (既に commit 済み、変更禁止)。** 呼ぶ側として全文読め。

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ` (branch `impl-dev-wave-t1851-c1b-integ`、base `d03b26773`) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_profile.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `orchestrator/tests/test_attempt_registry_core_equivalence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

**`s8b_terminal_evidence.py` と `test_s8b_terminal_evidence.py` は所有外である (leaf が実装済み)。** `s8b_floor_campaign.py`、`s8b_floor_stats.py`、`s8b_holdout_admission.py`、`s8b_ratified_freeze.py`、`acceptance_duration_ledger.json`、docs も所有外である。**所有外に必要な変更が見つかったら実装せず完了報告に書け。** docs の編集と commit はしない。

## leaf が公開している surface (呼ぶ側の契約。変更禁止)

```python
class TerminalEvidenceError(ValueError)

@dataclass(frozen=True, slots=True)
class TerminalEvidenceProjection:
    terminal_status, failure_reason, measurement_retry_reason,
    campaign_excluded_reason, primary_value, raw_output_sha256,
    report_sha256, observation_sha256, finished_at

@dataclass(frozen=True, slots=True, init=False)
class SealedTerminalEvidenceDraft:   # _canonical_bytes のみ
    .canonical_bytes -> bytes        # 複製を返す
    .document -> Mapping             # 毎回 bytes から再生成 + 9 key 検査
    .projection -> TerminalEvidenceProjection

@dataclass(frozen=True, slots=True, init=False)
class ValidatedTerminalEvidence:     # _canonical_bytes, _issuer_token
    .canonical_bytes / .document (12 key 検査) / .projection / .sha256

def derive_terminal_projection(document) -> TerminalEvidenceProjection
def seal_terminal_evidence(reservation, opened, terminal) -> SealedTerminalEvidenceDraft
def require_sealed_terminal_evidence(value) -> ValidatedTerminalEvidence
```

draft の `attempt_binding` は exact 9 key (`admission_claim_digest` `attempt_id` `campaign_run_id` `freeze_sha256` `manifest_sha256` `protocol_sha256` `run_relpath` `schedule_row_sha256` `schedule_sha256`)。validated はこれに 3 digest (`classification_receipt_sha256` `classification_event_sha256` `observation_event_sha256`) を足した exact 12 key。**leaf は昇格関数を持たない。昇格は本作業が adapter へ置く。**

## 依頼 — C1b の統合層

plan v2 §4 の 4.1 (core) → 4.2 (profile) → 4.3 (launcher) → 4.4 (adapter) をこの順で実装する。

### 受理・拒否の現状 (scope 前) と、本作業で変わる点

- 現状: `DomainProfile` に `retryable_reason_field` は無く、`_assert_null_matrix` は `retryable-failure` / `terminal-failure` の両枝とも `failure_reason` を照合する。v2 の `S8B_V2_RETRYABLE_FAILURE_REASONS` は空。v2 terminal は adapter の無条件拒否 hook で落ちる。`launch_floor_attempt()` の production 呼び手は 0 件。
- 本作業後: (受理が増える) v2 terminal が封印証拠つきで記録できる。(拒否が増える) capability 無しの core 直呼びを canonical v2 profile が拒否する。証拠 file と行の全件不一致を拒否する。`observed` / `not-consumed` 枝で `measurement_retry_reason` 非 null を拒否する。v1 へ非 null の新 field を渡したら拒否する。
- **変えないもの: v1 の event key 集合 (現行 exact 24)、v1 の retryable reason 集合 (空)、v1 の `failure_reason` と classification の等値、v1 の observed / terminal-failure / rejection の既存行列、v1 adapter API と canonical lifecycle bytes、core 変更が s8c facade の bytes / signature へ波及しないこと。**

### 親の追加裁定 (段 1・段 5 leaf の実測に基づく。plan v2 より優先する)

1. **呼出し閉包の数は plan v2 から写すな。** plan v2 §4.4 の「4 / 7 / 3」は caller 数ではなく出現数である (親の実測: 実 caller は `_atomic_update_locked` 2 本、`_atomic_update` 6 本、`_atomic_update_with_consumption_marker` 2 本)。**自分で call site を数え直し、報告に実測値を書け。** 「callback 規約を変えるなら全 callable を同じ commit で直す」という要求は不変である。
2. **`record_attempt_terminal` の consumer は s8b 系の外にもある。** 親の実測では `p3_autonomous_workload_trial.py`、`trial_registry.py`、`s8c_preregistration_evidence.py` とその test も同 API を使う。**keyword-only + 既定値なら既存 caller は変更不要**という plan の見込みを**実際に確かめ**、変更が要ると判明したら (所有外なので) 実装せず報告しろ。
3. **例外名の綴りを launcher 側で正規化しろ。** leaf は契約 4.2 の 3 語 (`RuntimeError` / `subprocess.TimeoutExpired` / `OSError`) を exact member として検査する。一方 launcher の現行実装は `type(exc).__name__` を使うため `TimeoutExpired` を生成する (leaf 実装子が `s8b_floor_attempt_launcher.py:408` 付近で実測)。**契約が正本なので、launcher の v2 発行経路で `subprocess.TimeoutExpired` へ正規化しろ。** leaf 側の集合を変えてはならない (所有外でもある)。**v1 経路の既存の綴りは変えるな** — v1 の受理集合は 1 bit も変えない。
4. **reservation に durable identity を載せる。** leaf は `schedule_row_sha256` / `records` / `threads` / `workload` を要求するが現行 reservation には無い (leaf 実装子の実測)。plan v2 §4.3 のとおり、**契約 1.5 (a) の権威ある identity だけ**を通し、`event` / `kind` / `seq` / `round` / `trigger` / `retry` は reservation へ足さない。**`records` / `threads` / `workload` / `cell_id` / `attempt_id` は durable claim から再照合する** (`mode` だけではない)。

### 実装の要点

**4.1 core** — plan v2 §4.1 のとおり。`retryable_reason_field: str = field(default="failure_reason", kw_only=True)`。`_assert_null_matrix` は **`retryable-failure` 枝と `terminal-failure` 枝の両方**で照合先を切り替える (契約 5.1.1)。`observed` と `not-consumed` で profile が選んだ reason field も null を必須にする (契約 5.3)。`record_attempt_terminal()` へ `measurement_retry_reason` / `terminal_evidence_sha256` を keyword-only で追加し、`terminal_keys` に含まれるときだけ emit、**v1 へ非 null を渡したら拒否** (契約 5.4)。公開 API へ capability 引数を足さない (契約 8)。**`aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を書くな** (`test_reflux_formal_consumer.py` の AST 走査下)。

**4.2 profile** — `_S8B_EVENT_KEYS` は一切変更しない。`_S8B_V2_EVENT_KEYS` (`:490`) を event 別に組み立て、terminal だけへ 2 key を足す (v1 との差集合は exact 3 key)。`S8B_V2_RETRYABLE_FAILURE_REASONS` を E2 の exact 4 語に、`S8B_RETRYABLE_FAILURE_REASONS` は空のまま。canonical v2 profile の通常 `terminal_row_validator` は capability 無しの core 直呼びを拒否し、adapter が durable evidence を読んだ場合だけ private validating profile を使う。`_require_sealed_s8b_v2_terminal()` は `type(evidence) is ValidatedTerminalEvidence` を要求し、**契約 7 節の全件等値表 11 行 (`finished_at` を含む)** を projection と照合する。`make_s8b_v2_domain_profile()` は `retryable_reason_field="measurement_retry_reason"`。

**4.3 launcher** — plan v2 §4.3 の順序表どおり。`_checked_reservation_policy()` の v2 一律拒否を外すが、`(v2 schema) ⇔ (consumption_marker 非 null)`、protocol digest、mode、receipt/use_perf、reps の検査は genesis/reserve より前に行う。launcher が measurement 前後の時刻・binary digest・capture kwargs snapshot・opened `ScalePoint` surface・私有 rep sink を保持し、**`duration_s` と `finished_at` を terminal builder の選択値にしない。** production wrapper だけが固定 adapter の `record_sealed_attempt_terminal()` を呼び、launcher は `ValidatedTerminalEvidence` も core capability も受け取らない。`_launch_floor_attempt_for_test()` の fake registry が受け取れるのは **draft まで**。**`_CERTIFIED_MEASUREMENT_KEYWORDS`、`_owned_post_probe()` の argv / timeout / subprocess site は不変。`expected_use_perf` の導出は既存 gate (`:565-588`) 1 本のまま** (契約 9 / B-07)。

**4.4 adapter** — plan v2 §4.4 の private 境界 7 関数。昇格は draft の canonical bytes を復号して 3 key を足し **bytes を作り直す** (draft の bytes を流用しない)。evidence path は `floor-attempt-registry-receipts/terminal-evidence/<digest>.json`。root lock 下で registry bytes から terminal digest を抽出し、各 file を **no-follow regular file** として読み、filename / bytes digest / strict JSON / exact keys / canonical bytes / attempt binding を検査する。private issuer が exact `CapturedObservation` を `_require_handle()` へ通して validated capability を発行する。`_assert_exact_profile()` へ `retryable_reason_field` の exact 比較を足す。terminal を含みうる replay 8 箇所を**中央 evidence-aware loader へ束ねる**。旧 API の v2 拒否は残す。

### 変異の照準 (親裁定 4.2)

- **S1:** `terminal-failure` 枝だけ `failure_reason` 固定のまま残す変異は通常経路で生存する。**D1522 に従い `_assert_null_matrix` を v2 profile の `retryable_reason_field` つきで直接呼ぶ test** を置き、`terminal-failure` 行で照合先が切り替わることを単独で確かめろ。
- **S2:** old replay だけ evidence 再読を省く変異は candidate replay に吸収される。**evidence loader の呼出し回数を数える seam** を置き、old / candidate の 2 回が独立に発火することを確かめろ。
- **`not-consumed` 枝の正例も D1522 の下層直呼びで作れ。** E1 は `not-consumed` を出さないので、上流の sealed 経路を正例に使うと恒真な拒否になる。`_assert_null_matrix` へ「`measurement_retry_reason` が null の `not-consumed` 行」を直接渡して受理させ、非 null の同じ行が拒否されることを対で置け。
- plan v2 §5.1 の M1〜M12 も観測する node を置け。**各負例は「この入力を拒否する層が前後にも内側にも無い」ことを確かめ、確かめられない変異は完了報告にそう書け。冗長 gate による赤は kill に数えない。**

### 既存 test への影響 (plan v2 §7)

既存期待値を意味的に変えてよいのは **2 箇所だけ**である。

- `test_s8b_floor_attempt_launcher.py` の `test_v2_profile_is_rejected_before_any_registry_side_effect` (`:891` 付近) — 「v2 は全副作用前に拒否」から「v2 は draft まで進めるが fake registry は production capability を発行できない」へ
- `test_attempt_registry_core_s8b_profile.py` の `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` (`:2174` 付近) — v2 retryable 集合を空から E2 exact 4 語へ、terminal key 差集合を 1 key から 3 key へ

**それ以外の既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。赤になったら実装側が誤りである。期待値の側が誤りだと判断したら、実装を変えずに報告して止まれ。**
**「新 field が増えたから v1 golden も更新する」という変更は行わない。**

### 規模上限

production 750〜1,120 行、test 1,200〜1,800 行。**超えそうなら止めて報告する。** 途中分割はしない。

## 検査・報告 (DW-S05-C)

- 実走は自走 harness を使う。`cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-integ && PYTHONPATH=. python3 orchestrator/tests/<file>.py` の形で、所有 4 test file と `orchestrator/tests/test_s8b_terminal_evidence.py` を走らせろ。**`run_tests` は使うな。**
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して hold を解除するな。** その release token は明示的なユーザー指示のためのものであり、実装子が自分の判断で外してよいものではない。hold された test の結果が要ると判断したら、走らせずに報告しろ。
- **緑には実走 nodeid・範囲を併記する。** 実走不能なら `closed` と申告せず「実装済み・未実走」と書け。
- **変更した production file を参照する consumer test も自分で引いて走らせろ** (名前の推測でなく参照関係で引く。private symbol の変更は公開 API の consumer 表に出ないので symbol 名で production 全体を grep しろ)。
- **fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。** 機構の正例・負例は実体を名指しし、依存先を stub しない。
- **期待値へ揮発 payload (working tree hash、時刻、絶対 path 等) を焼き込まない。**
- 完了報告に、**所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。**
- **指示外の受理集合変更をしない。**
- **契約の条項が実体化できないと判断したら、回避策を自作せず止めて報告しろ。** 「どの条項が、どの consumer の何に阻まれるか」を現物の file:line で書け。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。

## 総括

最後に `## 総括` 節を置き、次を書く。

- 4.1〜4.4 の実装状況 (完了 / 部分 / 未実施)
- 実走した nodeid の範囲と結果 (緑 / 赤 / 未実走)。赤はその内訳と帰属
- 呼出し閉包の**実測値** (`_atomic_update_locked` / `_atomic_update` / `_atomic_update_with_consumption_marker` / transition callable / `record_attempt_terminal`)
- S1・S2・`not-consumed` 正例・M1〜M12 のうち単一理由で殺せると確かめられたものと、確かめられなかったもの
- 所有外への波及 (実際に変更が要ると判明したものは file:line つき)
- 契約のうち実体化できなかった条項 (あれば file:line つき)
- production / test の行数
