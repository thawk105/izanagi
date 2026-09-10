# 段 1 brief — [T-2107] 着手前実測 + [T-1851] 実装単位 B1

base = 着手時 local main `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3`。
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1`、
branch `worktree-dev-wave-t2107-t1851-b1`。起動 gate rc=0 (fresh)。

## scope — 2 つだけ

1. **[T-2107] の着手前実測**: D1380 が要求する分岐判定。「launcher の出力前分類方針を名乗る
   production 定数の**値**が、既存の固定純関数から機械導出できるか」を実測して結論を出す。
   人間所有の凍結 policy を変える値だと判明したら、その値の決定は止めてユーザーへ返す。
2. **[T-1851] 実装単位 B1** (claim/marker capability) の実装。

**scope 外**: 単位 A / B2 / D1 / C / D2、分類権限そのものの新設 (単位 C の面)、
被覆の全単射照合 (B2)、v1/v2 codec (単位 A)、仮想リスク向けの gate・検査・台帳・一般化。

## 確定済みユーザー裁定 (親は覆さない)

- **D1379**: proof の形 `{row_count=N, chain_head_at_N}` は変えず、schedule と admission claim から
  独立導出した集合と台帳生存行を全単射で照合する検査を足す。実装は D1341 の 1 commit 閉包内。
- **D1380**: 分類権限を production 定数として新設する。値の権威は上記 scope 1 の実測で決める。
  **判定を待たずに実装を始めない。**
- **D1193**: 予算の集約単位は凍結単位のまま、台帳の名前空間だけを protocol 世代ごとに分ける。
- **D1194**: proof chain 束縛は新規成果物へ前向きにだけ掛ける。既 certified の受理面は変えない。
- **D1341**: 台帳の配線と proof chain 束縛は同じ変更単位で land する。B1 は単独 land しない
  **unlanded checkpoint** である。本 wave は B1 を commit するが main へは land しない。
- 段 4 裁定 r2 の親裁定 6 (維持・明確化): 共有 admission root の既存 bytes は書換えないが**読む**。

## 不変条件

- 規律 2 を緩めない。marker 検証は**受理を狭める方向にだけ**変える。現在 adapter が
  legacy path で検証している状態を、admission 所有の正しい検証へ移す。
- 書き出す bytes を変えない。B1 は read 側 (射影 + 検証) だけを触る。
  `_MEASUREMENT_GENERATION_FLOOR_ATTEMPT_KEYS` と `_FLOOR_ATTEMPT_KEYS` の exact key 集合、
  marker document の値、claim document、台帳行の bytes はいずれも不変。
- legacy v1 marker validator は残す (既存 cut-6 test が使う)。受理形を減らさない。
- 共有 admission root の既存 bytes を書換えない・削除しない。
- B1 単独で main へ land しない (D1341)。

## 実アンカー表 (行番号は base `6ff06800d` 時点)

| path | anchor | 役割 |
|---|---|---|
| `orchestrator/campaign/s8b_holdout_admission.py` | 249-257 | `CellHoldoutAdmission` (5 field、frozen slots)。claim digest の射影先 |
| 同 | 389-403 | `_CellState.measurement_generation_claim_digest` — 射影する値の出所 |
| 同 | 1793-1819 | fresh 予約での token 構築 |
| 同 | 6227-6253 | inspector 再構築での token 構築 |
| 同 | 4435-4489 | `_MEASUREMENT_GENERATION_FLOOR_ATTEMPT_KEYS` と canonical document |
| 同 | 4519-4546 | `_floor_canonical_marker_path` — schema で v1 / measurement-generation を dispatch |
| 同 | 90, 126, 133 | `_MEASUREMENT_GENERATION_CONSUMED_DIR` / `_ATTEMPT_SCHEMA` / `_MEASUREMENT_GENERATION_ATTEMPT_SCHEMA` |
| `orchestrator/campaign/s8b_attempt_registry.py` | 1458-1509 | adapter の `_marker_path` と `_assert_consumed_marker` — **不一致の実体** |
| 同 | 55-68 | adapter 側で重複定義した `_FLOOR_CONSUMED_MARKER_KEYS` / `_FLOOR_CONSUMED_MARKER_SCHEMA` |
| `orchestrator/tests/test_s8b_holdout_admission.py` | — | admission 側の正例・負例 |
| `orchestrator/tests/test_s8b_attempt_registry.py` | — | adapter 側の正例・負例 |
| `orchestrator/tests/s8b_floor_evidence_fixture.py` | — | 共有 fixture |

## 親が実測した与件 (子は攻撃してよい)

- **不一致は実在する。** adapter の `_marker_path` (`s8b_attempt_registry.py:1458-1462`) は
  `root / "consumed" / f"{claim_digest}-{marker_digest}.json"` を**独自導出**し、legacy v1 path しか
  作らない。admission 側の `_floor_canonical_marker_path` は schema を見て
  `measurement-generation-consumed/` と `consumed/` を dispatch する。adapter は現行世代の
  marker を検証できない。
- **token は digest されていない。** `CellHoldoutAdmission` を渡す先で `asdict` / `astuple` /
  同一性 hash を導く経路は無い (唯一の field 参照は oracle 側の `token.protocol_sha256`、
  `s8b_holdout_admission.py:1727`)。よって field 追加は凍結 bytes を変えない。
- **`CellHoldoutAdmission` の名前を参照する code は `s8b_holdout_admission.py` 内だけ** (repo 全体で
  22 hit、全て同 file)。test も production も型名を書かず opaque に受けている。
- **DW-O09 の pin 閉包**: `_MEASUREMENT_GENERATION_ATTEMPT_SCHEMA` / `_ATTEMPT_SCHEMA` /
  `measurement-generation-consumed` を key に張る pin は上表の code hit と、
  `docs/decisions.md:39722`、`docs/archive/worklog-phase3-0901-1135-1136.md:508` の記述だけ。
  凍結 manifest・golden・review ledger からの byte pin は 0 件。
- **DW-O10 は不成立**: B1 は producer の出力 bytes を変えない (read 側のみ)。

## [T-2107] 実測の一次資料 (親の暫定読み — これを子に攻撃させる)

- 分類の**規則**は既に完全に機械化されている。`s8b_floor_campaign.py:6147-6162` の固定 if/elif
  ラダー — `probe_after["competing"]` → `measure_error is not None` → `exec_failures >= reps` →
  `exec_failures > 0 and derived_reason is None` → `rep_integrity_failures > 0 and
  derived_reason == PARTIAL` → else `derived_reason`。自由選択は無い。
- `derived_reason` は純関数 `s8b_floor_stats.assess_session()` (`:126-164`) が返す。
  理由名は module 定数 (`_REASON_COMPETING` / `_REASON_LAUNCH` / `_REASON_PARTIAL` /
  `_REASON_PERFORMANCE`、`s8b_floor_campaign.py:333-335`、`s8b_floor_stats.py:59-60`)。
- **唯一の非 code 入力**: `assess_session` は閾値 `session_cv_max` を**引数で受ける**
  (`s8b_floor_stats.py:126,145`)。値は凍結 protocol 側から来る。
- 既存の同型権威 `s8b_scheduler_accounting.authority_policy_document()` (`:65-102`) は、
  module 定数だけを組み立てた dict の canonical bytes から digest を導く形をとる。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-a)** 分類権限の policy 値は、既存の固定純関数と module 定数から**機械導出できる**。
  よって D1380 の分岐は「AI が閉じる」側に落ちる。
- **(P1-b)** ただし policy document に `session_cv_max` の**値そのもの**を埋めると、権威 digest が
  人間所有の凍結閾値に束縛され、凍結 protocol の版が変わるたび権威 digest が変わる。
  埋めずに「閾値は凍結 protocol から受ける引数である」という**構造**だけを名乗れば、
  機械導出のまま閉じる。どちらが D1032 / D1380 の要求を満たすかが本実測の核心である。
- **(P1-c)** B1 の編集面は `s8b_holdout_admission.py` + その test + fixture に閉じ、
  adapter (`s8b_attempt_registry.py`) の consumer 差し替えは単位 A ではなく B1 に含める。
  含めないと B1 単独では capability に呼び手が無く、恒真な API になる。

## 成果物の形

- **T-2107**: 実測レポート 1 本 (insight)。(P1-a)/(P1-b) の real/refuted と、D1380 の分岐の結論。
  「人間所有」側に落ちたら、値の決定をユーザーへ返す裁定パッケージを添える。
- **T-1851 B1**: `s8b_holdout_admission.py` に admission 所有の marker 検証 API と
  claim digest の read-only 射影。adapter がそれを受ける。更新テストは admission 側の
  正例・負例と adapter 側の consumer test。**unlanded checkpoint として commit するが land しない。**

## DW-G05 — 成果物影響

- 放置すると、adapter は現行世代の consumption marker を legacy path で探して**必ず失敗するか、
  legacy marker を誤って受理する**。台帳の consume 記録が現行 campaign の試行へ束縛されないまま
  certified 成果物の proof 参照に載る。これは D1194 が却下した「欠落を許したまま追跡を謳う状態」。

## 分割方針

- 実装面があるので軽量版にしない。正しさ防壁 (marker 受理面) に触り受理集合が変わるため、
  段 2 plan・段 3 敵対相談 2 本・段 6 敵対レビュー 2 本を省かない。
- 段 5 の Codex `role=author` 実装子は **1 本**。B1 は producer/consumer 契約 (admission の
  capability と adapter の受け手) が 1 単位を跨ぐので、分割すると契約が壊れる。
- 親は実装面を直接編集しない。docs・裁定・commit・受入・記録だけを担う。

## 受入・実測環境

- Pegasus login node 上の read-only 検査と pytest。build・benchmark・正式測定は行わない。
- 受入は `tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py`。
