# 段 1 brief — [T-1851] 台帳配線 3 task 閉包 / 実装単位 A (core/profile/adapter)

2026-09-02。branch `worktree-dev-wave-t1851-unit-a`、base `ef88208f8` (B1 tip) + local main
`08c17d674` 取り込み済み。

## scope

台帳配線 3 task 閉包 (T-1851 前半 / T-2107 / T-1946) の 6 段分割
`B1 → A → B2 → D1 → C → D2` のうち **A だけ**を実装する。B1 は着地済みでなく本 branch 上の
checkpoint である。

段 2 plan v2 (`output/insights/2026-09-01_t1946-t2107-registry-wiring-design/verbatim/s2-plan-v2.md`
「単位 A: 台帳層」) が渡した項目は次の 6 群である。

- A1 registry schema を `s8b-floor-attempt-registry/v2` へ上げ、path を
  `floor-attempt-registries/{freeze}/{protocol}/registry.jsonl` の 2 段にする。v1 / v2 は
  別 `DomainProfile`・別 slot codec・別 layout とし、genesis schema の peek で dispatch する。
- A2 adapter に `_registry_generation_paths_locked(root, freeze_sha256)` を置き、freeze 直下の
  lowercase 64 hex real directory だけを世代とする。core に
  `load_attempt_registry_with_budget_counts(...)` を足し、`_atomic_update` が共有 root lock 下で
  他世代を replay して予算を累積する。
- A3 v2 slot を 5 軸 `(freeze_holdout_key, configuration_id, repetition, measurement_ordinal,
  attempt_ordinal)` にし、series / budget key を対応させる。
- A4 台帳専用理由語彙 4 値を固定し、`derive_s8b_terminal_projection(sealed_session_record)` を
  profile 層へ置く。呼び手の自己申告 reason / status を受け取らない。
- A5 v2 terminal 行へ exact `sealed_session_record` を足し、`serialize_session_line(record)` を
  単一源にして `raw_output_sha256` と一致させる。
- A6 adapter の `_assert_consumed_marker()` が raw path を独自導出せず、B1 の
  `validate_floor_attempt_consumption_marker()` が返す capability だけを受ける。
  classification claim を v3 へ上げ、full binding 3 値と 5 軸を含める。

## 確定済みユーザー裁定 (覆さない)

- **D1341** — 配線と束縛は同じ変更単位で land する。**本 wave は land しない。** 段 9 は
  B1 と同じく unlanded checkpoint で終える。
- **D1193** — 名前空間は複合形。予算を凍結単位に残し、台帳だけ世代ごとに分ける。
- **D1194** — proof chain 束縛は新規成果物への前向き適用。
- **D1340 / D1337 / D1342** — 前 wave の設計裁定。
- 前 wave 段 4 の採用済み具体化 (A2-2 / A2-4 / A2-6 / B2-1〜B2-9)。plan v2 はこれを反映済み。
- **親裁定 6** — 共有 admission root の既存 bytes を書き換えない。読むのは可。

## 不変条件

- 規律 2 — 受理集合を緩める変異を採らない。A4 の理由語彙固定と A6 の claim v3 は受理集合を
  **狭める**方向であり、広げる側は plan v2 が名指しした項目に限る。
- 規律 3 — 拒否は署名で書き、通る正例を 1 つ添える (`DW-S04`)。
- `marker.use()` が開けた journal TOCTOU 窓は本 wave でも閉じない。閉じたと書かない。
- 旧世代 (legacy v1 inspector token) の受理経路と cut-6 回復経路を壊さない。
- 段 5 実装子は実装面だけを編集し、docs 編集・commit をしない。

## 成果物の形

- 実装 commit 1 本 (production + test)。docs / insight は段 7 の記録 commit へ分ける。
- 変異 matrix は事前登録 (`DW-M01`) して本走まで実測する。
- 受入は焦点走 + consumer 焦点走 (`DW-O26`)。land しないので最終受入全走は最終単位が担う。

## 親の provisional 裁定 — 攻撃対象

- **(P1-a) 単位 A を 1 wave に載せる。** 前 wave は閉包全体を 2,650-4,000 行 / 220 node 超と
  見積もったが、単位 A 単体の規模は未測定である。段 2 は A1〜A6 の行数と test node 数を
  file 単位で見積もり、段 3 はそれを攻撃せよ。**1 wave に収まらないと実測されたら、段 4 で
  A を A1'/A2' へ再分割し、本 wave は前半だけを積む。** 境界の symbol・引数・戻り型を plan へ
  固定できることを分割の条件とする。
- **(P1-b) 内部更新 seam は `_atomic_update` の 2 分割で作る。**
  `_atomic_update_locked(lock, ...)` を新設し、既存 `_atomic_update` は `admission._locked(root)`
  を取って前者へ委譲する。B1 capability を消費する経路は
  `marker.use(lock=..., action=lambda lock: _atomic_update_locked(lock, ...))` とし、同じ
  admission root lock を二度取らない。**攻撃点:** `admission._locked` の非再入性を実測したか、
  `_PRELOCK_SNAPSHOT_HOOK` の rendezvous read が lock 内経路で意味を失わないか、
  既存 6 呼出し (`:1183, :1439, :1556, :1666, :1716, :1756`) の戻り型が変わらないか。
- **(P1-c) 正規 1 段 v1 path を v1 profile として読む。** 現行 canonical は 1 段
  `<freeze>/registry.jsonl`、live 共有 root の残骸は 2 段 `<freeze>/<protocol>/registry.jsonl`
  である。両方を読める受理表を plan へ書く。
- **(P1-d) `consumption-catalog.jsonl` は freeze 直下の既知 sibling として無視する。**
  世代列挙は 64 hex real directory だけを拾い、通常 sibling file で fail-closed にしない。
- **(P1-e) 受入・実測環境は login node の焦点走とする。** 本 wave は実装面のみで計測系を触らない。

## 変更面アンカー表 (実測、base = 本 branch HEAD)

| 面 | file:line | 現状 |
|---|---|---|
| schema 版 | `orchestrator/campaign/s8b_attempt_profile.py:22` | `S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION = "s8b-floor-attempt-registry/v1"` |
| slot 4 軸 | `orchestrator/campaign/s8b_attempt_profile.py:27-40` | `S8BSlotIdentity = tuple[str, str, int, int]`、`measurement_ordinal` 不在 |
| layout | `orchestrator/campaign/s8b_attempt_profile.py:378-386` | `floor-attempt-registries/{freeze_sha256}/registry.jsonl` (世代次元なし) |
| 理由語彙 | `orchestrator/campaign/s8b_attempt_profile.py:388-399` | `S8B_RETRYABLE_FAILURE_REASONS = frozenset()` (空) |
| path API | `orchestrator/campaign/s8b_attempt_registry.py:451-506` | `_relative_registry_path` / `_entry_paths` / `registry_path` |
| 更新経路 | `orchestrator/campaign/s8b_attempt_registry.py:984-1048` | `_atomic_update` が `admission._locked(root)` を自分で取る |
| marker 検査 | `orchestrator/campaign/s8b_attempt_registry.py:1458-1509` | `_marker_path` を自前導出、schema `s8b-holdout-attempt-consumption/v1` |
| marker 呼出 | `orchestrator/campaign/s8b_attempt_registry.py:1539, :2042` | いずれも `_atomic_update` の transition 内 = lock 保持中 |
| claim | `orchestrator/campaign/s8b_attempt_registry.py:811-901` | classification claim の address / payload |
| core replay | `orchestrator/campaign/attempt_registry_core.py:986-1020, 1120-1129, 1363-1399` | `load_attempt_registry` / `assert_registry_rows` の local accumulator |
| core profile 構築 | `orchestrator/campaign/attempt_registry_core.py:654-725` | 単一 current profile |
| B1 capability | `orchestrator/campaign/s8b_holdout_admission.py:303-370, 5082-5127` | `FloorAttemptConsumptionMarker.use(lock=..., action=...)`、`validate_floor_attempt_consumption_marker()` |

test 面: `test_s8b_attempt_registry.py` (35 node)、`test_attempt_registry_core_s8b_profile.py`
(50 node)、`test_attempt_registry_core_equivalence.py` (9 node)。consumer は
`test_s8b_floor_attempt_launcher.py` / `test_s8b_floor_campaign.py` /
`test_s8b_holdout_admission.py` / `test_s8b_scheduler_accounting.py` /
`test_reflux_formal_consumer.py`。production consumer は `p3_b4_analysis_ledgers.py` /
`p3_b4_prerun_issuer.py` / `p3_b4_raw_record_producer.py` / `trial_registry.py` /
`s8b_floor_attempt_launcher.py` / `s8b_holdout_admission.py` / `s8b_scheduler_accounting.py`。

## 実測した前提 (brief 前の裏取り)

- **DW-O09 pin 閉包:** `floor-attempt-registries` は `orchestrator/tests/test_frozen_artifacts.py`
  の `FROZEN_MANIFEST` に無い。repo 内 tracked な `registry.jsonl` は 0 件。pin は path 側にも
  key 側にも見つからない。
- **DW-O10 producer 書き込み面:** 対象 producer が書くのは共有 admission root 配下の
  `registry.jsonl`、`floor-attempt-registry-receipts/`、claim file、consumption marker、
  staging file。凍結成果物 (`output/` の durable manifest) は書かない。
- **live 共有 root の実在 (2026-09-02 再測):**
  `.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575…/d388477f…/registry.jsonl`
  と、同じ freeze 直下の `consumption-catalog.jsonl` が実在する。freeze は `db07b575` の 1 本だけ。
  前 wave の B2-12 裁定どおり本番 freeze とは別で、test は一時 Git repository を作る。
- **編集面の重なり:** 未着地 branch `worktree-dev-wave-t524-slot-experiment-unit` が
  `orchestrator/campaign/attempt_registry_core.py` を +29 行変更している。稼働 codex / claude
  process は 0 件。統合時に基準 hunk がずれうる。
- **submodule:** top-level `external/ccbench` と `third_party/shirakami` は初期化済み。最深の
  `shirakami/third_party/googletest` は revision 不在で `--init --recursive` が rc=1。
  main worktree はそもそも shirakami を展開していない。開始 gate は rc=0。
- **B1 の spool fragment** (worklog 1 / decisions 1) は本 branch 上に健在。main の worklog
  ローテーションで base digest が stale になりうるので段 7 で確認する。

## dev-wave 改善候補

(段 8 で裁定する。現時点の記録は handoff 側)
