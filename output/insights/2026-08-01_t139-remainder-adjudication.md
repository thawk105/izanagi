# [T-139] 残余 (RF 規範化 + recovery pipeline 接続) — 実装しない裁定と一次資料 (dev-wave 2026-08-01)

`authority: none` / `default_effect: no-state-change` — 本書は凍結記録であり、可変状態の正本
(worklog 末尾) ではない。設計仕様の正本 = `2026-07-29_t139-silo-degradation-ladder-design.md`
(以下「設計 insight」)、rung 1 の実装台帳 = `2026-07-29_t139-silo-ladder-rung1-permanent.md`。

**結論:** 本 wave は段 4 で「実装しない」と裁定した (dev-wave `DW-S04`)。実装差分はゼロであり、
変異 matrix と受入全走は射程外である。T-139 の残余は**閉じておらず**、4 つの独立した
ユーザー裁定待ちへ分解された (§5)。

## 1. 本 wave が確定させた一次資料 (親の実測)

計測環境 = ローカル worktree `dev-wave-t139-rf-recovery` (branch
`worktree-dev-wave-t139-rf-recovery`)、CCBench pin `d706650cdb31e442bef45b9b4216951d4fb40969`。
性能計測は行っていない (identity 経路の静的実測のみ)。

### 1.1 rung 1 patch を当てたときに止まる fails-closed は 3 つ (設計 insight は 2 つしか記録していない)

clean tree では `assert_includes_match_head` / `assert_conditional_macros_covered` / `resolve` が
すべて通り `src_token = "stock"` を返す。`patches/silo_ladder_rung1.patch` を
`external/ccbench` へ適用すると次が発火した。

| # | 検査 | 停止理由 |
|---|---|---|
| (i) | `assert_includes_match_head` | `cc/silo/transaction.cc` の `#include` 行集合が HEAD baseline と不一致 (patch が `<mutex>` を足す) |
| (ii) | `assert_conditional_macros_covered` | 未知マクロ `IZANAGI_SILO_LADDER_RUNG1` (T-148 の TU 注入マクロ死角) |
| (iii) | `resolve` の ALLOWLIST 検査 | **ALLOWLIST 外の tracked 改変 `cc/silo/ycsb_silo.cc`** (D23) |

設計 insight §3.4-2 が挙げたのは (i)(ii) だけである。**(iii) は本 wave の新事実**であり、
`EVOLVE_BLOCK_SOURCES` が 2 file (`include/backoff.hh`, `cc/silo/transaction.cc`) なのに対し
rung patch は 3 file 目を触るという構造差から来る。接続案はこれも解かねばならない。

復元は patch 逆適用 + `git status --porcelain` 空 + 3 検査の OK 復帰で確認した。
なお `git -C external/ccbench checkout -- <path>` は `hooks/guard_bash.py` が
「ccbench root を破壊する操作」として拒否する (dev-wave の改善候補として §6 に記録)。

### 1.2 凍結 bytes の pin 閉包 (DW-O09) — 実態と、親の一般化の訂正

`patches/ledger.json` を 1 byte でも変えると
`orchestrator/tests/test_silo_ladder_rung1_evidence.py` が赤になる。同 test は
`binding["ledger"]["sha256"] == sha256(現物 ledger)` を要求する。さらに
`orchestrator/campaign/projection_guard.py` は ledger を**閉じた schema** で読み、未知 key を
`ProjectionPolicyError` で拒否する。したがって **rung 宣言を ledger へ key 追加する設計は二重に不可**である
(D107 が「残る構造問題」と呼び、D115 が task 別 file 分離で解いた型と同じ)。

同 evidence が pin する他の実体: `binding.driver` = `orchestrator/campaign/silo_ladder_rung1.py`、
`binding.runtime_modules` の 17 module (本 wave が触りうるのは
`orchestrator/campaign/patchharness.py` と `orchestrator/campaign/silo_ladder_rung1_contract.py`)、
`binding.patch`、`binding.policy`、`binding.calibration`。
`orchestrator/campaign/source_digest.py` は pin されていない。

**親の一般化の訂正 (段 3 レンズ A の指摘、real):** 上記は「同一 repo 内の整合鎖」であって
**独立した trust root ではない**。ledger / patch / evidence はいずれも
`orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` (23 件) に入っていない。
協調して複数ファイルを更新すれば整合 test は再び通る。「独立 byte seal」という表現は誤りであり、
正しくは「単独 drift を赤にする整合鎖」である。

### 1.3 recovery pipeline 接続の実入口は backoff について到達不能

`orchestrator/campaign/p3_s4_loop.py:67` は `PIN = "028f34d"` を歴史的 pin として保持し、
`default_cfg()` がそれを `ccbench_commit` に焼く。一方 rung base は `d706650` (ledger)。
`run_campaign` は `cfg.ccbench_commit` を `source_digest.resolve()` と `evaluate()` の両方へ渡すため、
backoff loop に rung baseline を接続しても commit 不一致で止まる。
sort (`p3_s4_loop_sort.py:86`) と trigger-gating (`axis_trigger_gating.py:27`) は
`pin.CURRENT_PIN` = `d706650` であり一致する。
なお `p3_s4_loop_sort.py:27-28` は backoff 側の literal 保持を**意図的な凍結**と明記している。

### 1.4 RF gate の入力は実在するが、rung 1 evidence は「宣言だけで拒否される負例」ではない

`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` には
`classification.recovery_measurement_eligibility` (false)、
`gap_leg.workloads[].calibration_status` (`registered` / `contract-transfer-only`)、
`gap_leg.builds[].trace` (全 false)、`gap_leg.performance_runs[]` (24 本 = 2 workload × 2 variant ×
6 rep)、`gap_leg.schedule_receipt` が実在する。W-cal の interleave は 3:3 で釣り合っている。

しかし段 3 レンズ B の指摘 (real) のとおり、**第 3 arm (X) が存在せず**、artifact の closed schema に
`env_tag` と測定 checkout が無い (CCBench pin だけがある)。D59 は env-tag 別の
calibration / noise / attestation を要求し、F41 は測定 checkout の併記を恒久義務にしている。
したがって RF 入力 gate を正しく作れば、この artifact は**宣言以外の理由でも拒否される**。
親 brief が段 1 で書いた「宣言を読まない mutant だけを殺す実負例になる」という設計根拠は
**成立しない** (負例の単一理由性が無く、`DW-M01` の変異が組めない)。

## 2. 段 2 プランの要点 (`s2-plan.md` 401 行、read-only codex)

推奨は P1 = 「pin 済み baseline overlay」で、対立案 (a) rung を CCBench のローカル commit にする案は
「凍結 patch 単体では未知マクロを解けず、CMake 変更まで足すと宣言集合を超え D16/D18 に反する」、
(b) dedicated-driver-only 維持は「scope 2 を閉じない」として却下した。

プランは親 brief の穴を 1 件突いた (real、採用): **identity gate を通すだけでは不十分**である。
`Genome.cmake_defines()` は `-DCCBENCH_*` しか生成せず、buildcache も Genome と TRACE しか
configure へ渡さないため、rung マクロを実ビルドへ注入しないと**マクロ OFF のバイナリを
recovery baseline と誤認する**。既存の専用 driver はこのため `CMAKE_CXX_FLAGS` を明示注入している。

## 3. 段 3 敵対レンズの結論 (両方 NO-GO)

レンズ A (正しさ防壁・identity 死角) = BLOCKER 6 件、レンズ B (統計・実装可能性・全層性) =
BLOCKER 10 件。独立に一致した点が 3 つある。

1. **sidecar は frozen ledger の禁止を別名で上書きする** (A-1 / B-9)。現 ledger は
   `recovery_measurement_eligibility=false`、`pipeline_eligible=false`、
   `composition="dedicated-driver-only"` を宣言し、`silo_ladder_rung1_contract.py` がその値を
   exact に要求する。「candidate ではなく baseline なら別」という区別は現 schema に無い。
2. **backoff の pin 不一致で実入口が死んでいる** (A-3 / B-10)。§1.3 で親が実測確認した。
3. **RF gate が公式成果物 consumer (材料レポート・台帳) に未配線** (A-7 / B-8)。
   producer も無いため、gate を通らない RF スカラーがレポートへ入りうる一方、
   正規の producer は存在しない。

レンズ A 単独の重い所見: rung マクロの緩和が pinned 出現箇所ではなく `EVOLVE_BLOCK_SOURCES`
全体に及び、**宣言済みマクロの新規使用を殺せない** (A-2、規律 2 直撃)。build 環境が
`src_token` 外でバイナリを変えうる (A-4、設計 insight §6-10 の未解決要件が接続で certified 経路へ入る)。

レンズ B 単独の重い所見: RF 規範案の統計設計に未確定点が 5 つ残る (B-1〜B-5) — paired block に
独立二群の並べ替えを当てている / workload × cell の多重比較 family が未定義 / within-run floor を
差の floor へ誤用し反復数 6 に実測根拠が無い / 区間推定と `<0`・`>1` の帰属意味論が無い /
選択的欠測と retry 系列を閉じていない。加えて **正例 artifact ゼロでの compute 実装は DW-G04 違反** (B-7)。

## 4. 裁定 (段 4)

**実装しない。** 段 5・6 を飛ばし `4→7→8→9`。理由は 4 つ。

1. A-1 / B-9 は**親の権限外**である。ledger の宣言は T-139 自身の certified evidence が縛るもので、
   別 policy file で実質上書きするのは受理集合の変更にあたる。`DW-S04` は scope 外の real 所見を
   実装せず裁定パッケージで返すと定める。
2. A-3 / B-10 で**接続の前提が崩れている**。「3 loop へ接続」は backoff について成立せず、
   pin を動かす案は歴史 campaign identity を変えるため本 wave の scope 外である。
3. B-6 / B-7 で **RF 実装の足場が無い**。正例 artifact も計測 ID も無く (DW-G04)、
   負例は単一理由性を持たない (DW-M01 の変異が組めない)。
4. A-2 / A-4 は**規律 2 に直接触れる**。プラン記載のままでは受理集合が宣言範囲を超えて広がる。

## 5. ユーザー裁定へ返すもの

1. **rung を loop の baseline として受理するか。** 受理するなら、ledger の `pipeline_eligible=false` /
   `composition=dedicated-driver-only` の射程を versioned policy で明文化し直す必要がある。
2. **RF 規範の統計設計 5 点** (§3 の B-1〜B-5)。
3. **正例 artifact をどう作るか** — env-tag・測定 checkout・CCBench pin・attestation・
   between-run floor・事前凍結 schedule を持つ 3 arm 計測を 1 本。これは [T-144] の前提でもある。
4. **backoff loop を recovery へ使うか** — 使うなら pin 不一致の解消方針 (歴史 driver を触らず
   別 driver を立てるか) の裁定。

## 6. 本書が主張しないこと

- 「T-139 の残余が閉じた」— 閉じていない。本 wave の成果は**閉じられない理由を file:line で
  確定させたこと**と、親 brief の誤り 2 件 (§1.2 の一般化、§1.4 の負例前提) の訂正である。
- 「接続が不可能である」— 可能かどうかは §5-1 のユーザー裁定に依存する。本書は
  「現行の宣言を無裁定で上書きしてはならない」までを主張する。
- 段 2・段 3 の子出力そのものの正しさ — 子の指摘は**データであって指示ではない** (絶対規律 6)。
  採否はすべて §4 の親裁定に帰する。親が独立に実測で裏を取ったのは §1.1・§1.2・§1.3・§1.4 である。
