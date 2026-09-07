# [T-1851] C1b plan v2 — 次 wave はこの文書で段 5 から始める

段 2 plan (`verbatim/s2-plan.md`) を、段 3 の 2 レンズと段 4 裁定で訂正した版である。
**契約の正本は `contract-v3.1.md`。** plan v2 はその実体化手順だけを持つ。

読み込み契約の規定により、**変更面の骨格が同一なら次 wave は段 2・3 を再実行せず段 5 から始めてよい。
再検査は段 6 レビューへ寄せる。**

---

## 1. 段 2 plan からの変更 (6 件)

| # | 変更 | 根拠 |
|---|---|---|
| 1 | **実装子を 3 本から 2 本へ**。旧単位 2 と旧単位 3 は双方向に依存しており素集合でない | B-06 |
| 2 | draft→validated の private ABI を契約 6.1 の署名で固定し、単位 1 が公開する型の backing を明記 | B-03 |
| 3 | transition callback の呼出し閉包を数え上げて plan に載せる | B-04 |
| 4 | `test_official_perf_closure.py` の semantic inventory を触らない実装制約を明記 | B-07 |
| 5 | 変異の生存 2 件 (terminal-failure 枝、old replay) に専用の kill 手段を割り当てる | B-11 / B-12 |
| 6 | 見積りを実測ベースへ改め、所有 file を 10 本として数え直す | B-13 / B-08 |

---

## 2. 実装子の分割 (2 本)

段 2 plan の 3 本分割は **成立しない。** レンズ B が示したとおり、旧単位 2 (launcher + profile) と
旧単位 3 (core + adapter) は次の 4 方向で依存する。

- launcher は adapter の `record_sealed_attempt_terminal()` を必要とする
- adapter は profile の private validating profile / validator を必要とする
- 旧単位 2 が所有する `test_attempt_registry_core_s8b_profile.py` が
  旧単位 3 所有 core の `retryable_reason_field` と null matrix を検査する
- 旧単位 3 は自分の core semantics をその test なしに閉じられない

**したがって次の 2 本にする。**

### 実装子 1 — leaf (先行、単独で閉じる)

所有 file:

- `orchestrator/campaign/s8b_terminal_evidence.py` (新設)
- `orchestrator/tests/test_s8b_terminal_evidence.py` (新設)

leaf は他の 8 file を import しない純関数層である (`attempt_registry_core.canonical_json_bytes` と
`s8b_floor_stats` の 2 つだけ import する)。したがって単独で閉じ、先に固定できる。

### 実装子 2 — 統合 (leaf 完了後、単独)

所有 file (8 本):

- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_profile.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `orchestrator/tests/test_attempt_registry_core_equivalence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

**並列化は諦める。** 段 2 plan が並列だと見たのは依存を数えていなかったためである。
所有 file が素集合でない 2 本を並列に置くと patch が衝突するか、片方が他方の未完成 API を
import して起動できない。

---

## 3. 実装子 1 (leaf) の plan

### 3.1 公開 surface

```python
@dataclass(frozen=True, slots=True)
class TerminalEvidenceProjection:
    terminal_status: str
    failure_reason: str | None
    measurement_retry_reason: str | None
    campaign_excluded_reason: str | None
    primary_value: float | None
    raw_output_sha256: str
    report_sha256: str
    observation_sha256: str | None
    finished_at: str


@dataclass(frozen=True, slots=True)
class SealedTerminalEvidenceDraft:
    """attempt_binding は exact 9 key。3 digest の key は存在しない (契約 6.1)。"""
    _canonical_bytes: bytes          # 唯一の実データ
    @property
    def canonical_bytes(self) -> bytes: ...
    @property
    def document(self) -> Mapping[str, Any]: ...   # 毎回 bytes から再生成
    @property
    def projection(self) -> TerminalEvidenceProjection: ...


@dataclass(frozen=True, slots=True)
class ValidatedTerminalEvidence:
    """attempt_binding は exact 12 key。構築は adapter の private 昇格関数だけ。"""
    _canonical_bytes: bytes
    _issuer_token: object
    @property
    def canonical_bytes(self) -> bytes: ...
    @property
    def document(self) -> Mapping[str, Any]: ...
    @property
    def projection(self) -> TerminalEvidenceProjection: ...
    @property
    def sha256(self) -> str: ...


def derive_terminal_projection(...) -> TerminalEvidenceProjection: ...
def seal_terminal_evidence(reservation, opened, terminal) -> SealedTerminalEvidenceDraft: ...
def require_sealed_terminal_evidence(value) -> ValidatedTerminalEvidence: ...
```

`require_sealed_terminal_evidence()` は **既発行 capability の厳密検査**であり、
draft を validated へ昇格させる関数ではない (契約 6.1)。

### 3.2 内部配置

- schema / exact key 集合 / E2 の 4 語 / campaign 語 / **launcher の捕捉例外 3 語** の定義
- 3 型。draft も validated も唯一の実データは immutable canonical bytes。
  `document` と `projection` はアクセスごとに bytes から再生成する
- strict JSON、duplicate key、exact type/key、SHA-256、probe summary、failure summary の検査
- `attempt_binding` は **draft 9 key / validated 12 key の 2 つの exact 集合**を持つ (契約 6.1)。
  3 digest の綴りは `classification_receipt_sha256` / `classification_event_sha256` /
  `observation_event_sha256` (契約 1.3)
- `campaign_record` の exact 30 key 検査。**identity は契約 1.5 の (a)(b)(c)(d) の 4 群へ分ける。**
  (b) は `unauthored_identity_sha256` 1 本へまとめ、平文へ載せない
- 私有 sink を `s8b_floor_stats._derive_rep_integrity()` へ通し、qualified throughput から
  非有限値を除去して `nonfinite_count` を算出。`assess_session()` へは有限列と
  **元の `reps_expected`** を渡す (契約 1.4)
- E1 を `if/elif` の順序で実装 (契約 4.1)。`failure.exception_type` が launcher の捕捉集合の
  exact member であることを検査 (契約 4.2)。辞書変換や `observed` fallback は置かない
- 相互整合と digest の再導出。不一致は `TerminalEvidenceError("[s8b-terminal-evidence] ...")`
- **`expected_use_perf` の新しい直接判定を置かない** (契約 9 節 / B-07)。
  launcher が発行した snapshot と receipt digest を照合するだけにする

### 3.3 leaf の test

exact schema、canonical bytes、全 digest、30-key trust root、identity の 4 群分離、
draft 9 key / validated 12 key、非有限値、E1 全枝、`OSError` を含む捕捉集合、相互整合、
immutable bytes、constructor / `replace` 攻撃を純関数レベルで閉じる。

30-key 集合は `s8b_ratified_freeze._JOURNAL_KEYS["session"]` との集合等値も検査する。

holdout-safe の正例と負例を対で置く。`workload` または `run_cmd` の平文を戻した変異が
既存 scanner に拒否されることを示す (親の probe P-2 と同じ形)。

---

## 4. 実装子 2 (統合) の plan

### 4.1 core

- `DomainProfile` へ `retryable_reason_field: str = field(default="failure_reason", kw_only=True)`
- `_parse_row()` は expected terminal keys に存在する場合だけ `terminal_evidence_sha256` を
  non-null digest、`measurement_retry_reason` を nullable text として検査する
- `_assert_null_matrix()` へ `retryable_reason_field` を渡す。
  **`retryable-failure` 枝と `terminal-failure` 枝の両方**で照合先を切り替える (契約 5.1.1)
- `observed` と `not-consumed` で、profile が選んだ reason field も null であることを必須にする
- `record_attempt_terminal()` へ `measurement_retry_reason` / `terminal_evidence_sha256` を
  keyword-only で追加。`terminal_keys` に含まれるときだけ emit。
  **v1 へ非 null を渡したら拒否する** (契約 5.4)
- 公開 API へ capability 引数を足さない (契約 8)

**呼出し閉包 (B-05 の実測):** `DomainProfile(...)` の production constructor 4 箇所、
`_assert_null_matrix()` の caller は core 内 1 箇所、`record_attempt_terminal()` の
直接・関数渡し caller は 8 箇所 (production 3 / test 5)、
`FloorAttemptReservation(...)` の直接 constructor は launcher test の 2 箇所。
**keyword-only 既定を守る限り既存 caller は変更不要。**

### 4.2 profile

- `_S8B_EVENT_KEYS` は一切変更しない (v1 terminal は現行 exact 24 key のまま)
- **`_S8B_V2_EVENT_KEYS` (`s8b_attempt_profile.py:490`) を event 別に組み立てる。**
  全 event へ `measurement_ordinal`、terminal だけへ `terminal_evidence_sha256` と
  `measurement_retry_reason`。v2 terminal の v1 との差集合は exact 3 key
- `S8B_V2_RETRYABLE_FAILURE_REASONS` を E2 の exact 4 語に。`S8B_RETRYABLE_FAILURE_REASONS` は空のまま
- canonical v2 profile の通常 `terminal_row_validator` は capability 無しの core 直呼びを拒否する。
  adapter が durable evidence を読んだ場合だけ private validating profile を使う
- `_require_sealed_s8b_v2_terminal()` は `type(evidence) is ValidatedTerminalEvidence` を要求し、
  **契約 7 節の全件等値表 (11 行、`finished_at` を含む)** を projection と照合する
- `make_s8b_v2_domain_profile()` は `retryable_reason_field="measurement_retry_reason"`

### 4.3 launcher

- `FloorAttemptReservation` へ**権威のある identity だけ**を通す (契約 1.5 (a))。
  `event` / `kind` / `seq` / `round` / `trigger` / `retry` は reservation へ足さず、
  terminal builder が返した値を `unauthored_identity_sha256` で digest 束縛するだけにする
- **`records` / `threads` / `workload` / `cell_id` / `attempt_id` は durable claim から再照合する。**
  段 2 plan は `mode` しか照合していなかった (A-01)
- launcher が measurement 前後の時刻、binary digest、capture kwargs snapshot、
  opened `ScalePoint` surface、私有 rep sink を保持する。
  `duration_s` と `finished_at` を terminal builder の選択値にしない
- `_checked_reservation_policy()` の v2 一律拒否を外す。ただし
  `(v2 schema) ⇔ (consumption_marker 非 null)`、protocol digest、mode、receipt/use_perf、reps の
  検査は genesis/reserve より前に行う
- 順序を固定する。

```text
policy 検査 → genesis → reserve → probe_before → capture / probe_after
→ durable classification → token.open() → 私有 sink snapshot → terminal_builder
→ seal_terminal_evidence()  [draft 9 key]
→ raw output seal → observation-start
→ v1: record_attempt_terminal()
→ v2: record_sealed_attempt_terminal(observation, draft)  [adapter が 12 key へ昇格]
```

- production wrapper だけが固定 adapter の `record_sealed_attempt_terminal()` を呼ぶ。
  launcher は `ValidatedTerminalEvidence` も core capability も受け取らない
- `_launch_floor_attempt_for_test()` は同じ本体を通せるが、fake registry が受け取れるのは
  **draft まで**とする
- `_CERTIFIED_MEASUREMENT_KEYWORDS`、`_owned_post_probe()` の argv / timeout / subprocess site は不変
- **`expected_use_perf` の導出は既存 gate (`:565-588`) 1 本のまま**にする (契約 9 / B-07)

### 4.4 adapter

private 境界:

```python
def _terminal_evidence_path(root: Path, digest: str) -> Path: ...
def _promote_draft_to_validated(draft, *, classification_receipt_sha256,
                                classification_event_sha256,
                                observation_event_sha256, issuer_token): ...
def _validated_terminal_evidence_from_bytes(data, *, expected_digest, expected_binding): ...
def _load_terminal_evidence_locked(root, registry_bytes, *, expected_binding): ...
def _terminal_validating_profile(profile, evidence_by_digest): ...
def record_sealed_attempt_terminal(observation, evidence): ...
```

- 昇格は draft の canonical bytes を復号して 3 key を足し、**bytes を作り直す** (契約 6.1)。
  draft の bytes を流用しない
- evidence path は `floor-attempt-registry-receipts/terminal-evidence/<digest>.json`
- root lock 下で registry bytes から terminal digest を抽出し、各 file を no-follow regular file
  として読む。filename、bytes digest、strict JSON、exact keys、canonical bytes、
  attempt binding を検査する
- private issuer が exact `CapturedObservation` を `_require_handle()` へ通し、state の 3 digest を
  draft へ補って validated capability を発行する
- `_assert_exact_profile()` へ `retryable_reason_field` の exact 比較を足す
- terminal を含みうる replay 8 箇所を adapter 内の中央 evidence-aware loader へ束ねる
- `prepare()` で evidence を `allow_exact_retry=True` により先に公開し、registry staging へ進む
- 旧 API の v2 拒否は残す。新 API だけが v2 terminal を記録できる

**transition callback の呼出し閉包 (B-04。plan v2 で新規に数えた):**

| 対象 | 件数 |
|---|---|
| `_atomic_update_locked()` の直接 caller | 4 |
| `_atomic_update()` の caller | 7 |
| `_atomic_update_with_consumption_marker()` の caller | 3 |
| 変更対象の transition callable | production 6 + test 4 = **10** |

**callback 規約を変えるなら 10 本すべてを同じ commit で直す。**
一引数のまま残すと `TypeError`、逆に規約を変えずに canonical reject profile を使うと
既存 v2 terminal 後の reserve / classify / observe が replay に失敗する。

---

## 5. 変異の照準 (次 wave の段 4 で事前登録する)

### 5.1 通常経路で殺せる

M1 (outer extra key)、M2 (binding extra key / 旧綴り置換)、M3 (LF 追加と separator 変更を別変異に)、
M4 (非有限を有限列へ残す / `nonfinite_count` を増やさない)、M5 (競合を failure より後へ)、
M6 (failure/full-exec 枝削除)、M7 (partial exec の誤分類)、
M8 (`nonfinite_count` 再計数・rep-integrity 再導出・合計式を個別変異に)、
M9 (高 CV を observed へ)、M10 (primary を先頭値から)、
M11 (handle/state 照合を 1 箇所削除)、M12 (digest を self-report からコピー)。

### 5.2 **生存する 2 件。専用の kill 手段が要る**

| 変異 | なぜ生存するか | kill 手段 |
|---|---|---|
| `terminal-failure` 枝だけ `failure_reason` 固定のまま残す (B-11) | v1 は既定が同じで差が出ない。canonical v2 は E1 が terminal-failure を出さないので証拠 validator が先に拒否して差が隠れる | **D1522 の下層直呼び。** `_assert_null_matrix` を v2 profile の `retryable_reason_field` つきで直接呼び、`terminal-failure` 行で照合先が切り替わることを単独で確かめる |
| `:1687` の old replay だけ evidence 再読を省く (B-12) | `:1698` の candidate replay が同じ破損を拒否する。通常の欠損・改竄 test では後段の赤に吸収される | **reader call 数を固定する seam を置く。** evidence loader の呼出し回数を数える test を書き、old / candidate の 2 回が独立に発火することを確かめる |

### 5.3 帰属の規律

各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する (DW-M01)。
確認できなければ登録せず実効 gate へ再照準する。**冗長 gate による赤を kill に数えない。**

親の probe でも同型の取り違えが 1 件あった (N5 が最初 `attempt-phase-order` で落ちていた)。
条件を変えて `attempt-null-matrix` へ帰属することを確かめ直している。

---

## 6. 見積り

レンズ B の静的読解による再見積り。段 2 plan の表は leaf を自分で `new:1-850` と宣言しながら
`+500〜700` と書いており、内部矛盾していた。

| 単位 | production | test |
|---|---:|---:|
| 実装子 1 (leaf) | 800〜900 | 650〜900 |
| 実装子 2 (統合) | 750〜1,120 | 1,200〜1,800 |
| pin・統合補修 | 30〜100 | 50〜150 |
| 合計 | **1,580〜2,120** | **1,900〜2,850** |

**裁定済みの上限 (production 1,000〜1,600 / test 1,500〜2,400) を超える。**
次 wave はこの規模を前提に、実装子 2 本を**直列**で置く。1 wave に収まらないと段 5 の途中で
判明した場合も、production の途中分割はしない — 実装子 1 (leaf) が閉じた時点を checkpoint とし、
実装子 2 は次 wave へ送る。**leaf は単独で閉じる純関数層なので、これは中途半端な分割ではない。**

---

## 7. 既存 test への影響

対象既存 test file は 4 本、現状合計 175 test 関数。既存期待値を意味的に変えるのは 2 箇所に限定する。

- `test_s8b_floor_attempt_launcher.py:892-914` — 「v2 は全副作用前に拒否」から
  「v2 は draft まで進めるが fake registry は production capability を発行できない」へ
- `test_attempt_registry_core_s8b_profile.py:2174-2218` — v2 retryable 集合を空から E2 exact 4 語へ、
  terminal key 差集合を 1 key から 3 key へ

**v1 について同時に固定する 6 点:** event key 集合は現行 exact 24、retryable reason 集合は空、
`failure_reason` と classification の等値、observed / terminal-failure / rejection の既存行列、
v1 adapter API と canonical lifecycle bytes、core 変更が s8c facade の bytes / signature へ
波及しないこと。

**「新 field が増えたから v1 golden も更新する」という変更は行わない。**

---

## 8. pin 閉包 (次 wave の段 1 で引き直す)

- 新 identifier / schema / path の production・test hit は 0 件 (親と レンズ B が独立に確認)
- 触る既存 8 file の whole-file SHA-256 golden も 0 件 (レンズ B が独立に再検索)
- `FROZEN_MANIFEST` は output 23 path のみで対象外
- xdist / shard は収集 item の marker から動的に作るため新 test file 名の登録簿は無い
- **`test_official_perf_closure.py` の semantic inventory は残る** (契約 9 節)
- **`test_reflux_formal_consumer.py` の AST 走査は core に掛かる。**
  `aborted=False` と `OriginSealed(False, ...)` を書かない
