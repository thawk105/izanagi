# [T-1851] 単位 C3a — 段 4 裁定と変異事前登録 (2026-09-09)

branch `worktree-dev-wave-t1851-unit-c2`、base `21dfbe0f3` (local main `cbcdb6c91` 取り込み済み)。
**land しない (D1341)。** 全単位が揃うまで unlanded checkpoint に留める。

## 0. 段 3 所見の real / refuted と採否

| 所見 | 判定 | 採否 | 根拠 |
|---|---|---|---|
| A-1 blocker 1 の発火 (pre-probe competing ∧ marker で inspector が拒否) | **real** | 採用 | 親が `s8b_holdout_admission.py:6733-6741` と launcher `:985-997` の順序を現物で確認 |
| A-2 既存 seam では解けない | **real** | 採用 | production 入口は reservation/marker supplier を受けない (`:1189-1215`) |
| A-3 ordinal の 5 軸の意味 (campaign retry = `slot_id[3]`、recovery = `slot_id[4]`) | **real** | 採用 | `s8b_attempt_profile.py:159-168,238-256`、`s8b_floor_contract.py:248-270` |
| A-4 adapter/replay も誤束縛を独立に要求 | **real** | 採用 | `s8b_attempt_registry.py:1394-1429`、fixture 3 箇所 |
| A-5 `PRODUCTION_RESULT_SCHEMA` 新設は不要 | **refuted** (plan の案が不要) | 採用 | v5 は既設 (`s8b_floor_contract.py:35-40,88-100,170-187`) |
| B-1 案 (a) は受理集合を広げ D1660 に逆行 | **real** | 採用 → 案 (a) 却下 | `s8b_holdout_admission.py:6577-6582,6733-6741` |
| B-2 案 (b) は artifact 受理集合を保存 | **refuted** (欠陥なし) | 採用 → 案 (b) 採択 | 同上 + production 呼び手 0 件 |
| B-3 competing marker の負例が実体を名指ししていない | **real** | 採用 | 実 `inspect_floor_holdout_admission_evidence()` を通す負例を必須化 |
| B-4 planned `None` を拒否し続ける変異が生存する | **real** | 採用 | planned 専用の正例・負例を別 node として必須化 |
| B-5 値域 receipt の fake 混入変異に production locus が無い | **real** | 採用 | 変異登録から外し、非 pytest evidence として扱う (C3b) |
| B-6 C3a checkpoint は死んだ gate ではないが単独 land 不可 | **refuted / real の複合** | 採用 | D1114/D1194/D1341。本 wave は land しない |
| B-7 producer v5 と v4 consumer の不整合は fail-closed な到達不能 | **real** | 採用 | `s8b_holdout_freeze.py:1431-1442`、`s8b_ratified_freeze.py:2393-2409` |
| B-8 `s8b_holdout_admission.py` は result consumer ではない | **refuted** | 採用 (表記を訂正) | `:6755-6774` は attempt-ledger consumer |
| B-9 pin 閉包に 5 件の抜け | **real** | 採用 | 下記 §4 に収録 |
| B-10 whole-file sha256 pin 0 件 | **refuted** (親 plan の主張は正しい) | 採用 | 子が 11 file の hash を検索して 0 件 |
| B-11 1 campaign の min/max を母集合へ一般化できない | **real** | 採用 | 限界文言を C3b の成果物へ必須化 |

## 1. 択一の裁定 (親の provisional。ユーザー追認は §6)

- **択一 1 (marker と pre-probe) = (a) launcher-owned 二段。ただし plan と両レンズの案より小さく実装する。**
  既存 production 入口 `launch_floor_attempt()` の**署名と挙動は変えない** (親が実測: 既存 test が
  `post_probe=` で 6 箇所呼び、`test_s8b_floor_attempt_launcher.py:2222-2230` が署名と source を pin し、
  `:1999` が competing 正例を production 入口で通している)。
  新設するのは次の 2 つだけである。
  1. `probe_floor_attempt_preconditions(*, post_probe: FloorPostProbeCapability) -> FloorAttemptPreProbe`
     — launcher 私有の固定 probe を 1 回だけ実行し、**封印した一回限りの** pre-probe を返す。
  2. `launch_probed_floor_attempt(reservation, registry_genesis, measurement, *, pre_probe,
     classified_at, terminal_builder) -> FloorAttemptLaunchResult`
     — 封印 pre-probe を `probe_before` として使い、内部で probe をやり直さない。
     それ以外の順序・precedence・封印 terminal 発行は `_launch_floor_attempt` を共有する。
  **blocker は「誰がいつ marker を消費するか」で閉じる。** campaign は phase 1 の結果が competing なら
  marker を消費せず launcher を呼ばない (既存の unconsumed 枝を保つ)。clean のときだけ
  `consume_attempt_ticket()` を通し phase 2 を呼ぶ。**inspector は 1 bit も緩めない。**
  - 成果物影響: これが無いと production 経路は competing 枝で必ず
    `attempt-ledger-coverage-mismatch` を出し、result の self-check と certified 到達が止まる。
- **択一 2 (campaign retry ordinal) = (a) erratum で `slot_id[3]` に束縛する。**
  `retry_ordinal is None ⟺ measurement_ordinal == 0`、それ以外は `retry_ordinal == measurement_ordinal`。
  現行 `retry_ordinal == slot_id[4]` は production で `slot_id[4]` が常に 0 に固定されるため
  (`s8b_attempt_registry.py:2534-2538`)、campaign の `1..N` を**構造的に表現できない**。
  **これは受理集合の緩和ではない** — 束縛は総体として保たれ、retry 側は今まで恒真に 0 を強いていた
  検査が実軸へ再照準される。planned の `None` は契約 `s8b_floor_contract.py:248-270` が定める形である。
  - 成果物影響: これが無いと planned も retry も production sealed terminal を作れず、
    registry terminal と result v5 proof が完成しない。
- **択一 3 (production result schema) = (a) campaign が既設 `RESULT_SCHEMA_V5` を直接選ぶ。**
  `s8b_floor_contract.py` と `test_s8b_floor_contract.py` は**変更対象から外す**。
  - 成果物影響: v4 の global alias と既存 frozen bytes を不変に保ったまま、新規 result だけ v5 になる。
- **択一 4 (単位分割) = (a) C3a と C3b に分ける。**
  本 wave の確定成果物は **C3a (配線・v5 producer・ordinal erratum)**。
  **C3b (fresh production campaign と値域 receipt) は、C3a の受入全走が緑になった後に同 wave 内で
  投入を試みる条件付き目標**とし、完了しなければ次の一手として起票する。
  F660 は不発火 (main 側登録簿に 2 path 実在) だが、これは静的確認であって qsub 成功の実測ではない。

## 2. 既存テスト期待値の変更を許す範囲 (親の名指し)

原則は不変 (`DW-S05-B`)。**例外は択一 2 の erratum が権威となる次の 3 箇所だけ**とし、
子はこれ以外の既存期待値を 1 行も変えない。変える必要が生じたら**実装せず報告して止まる**。

1. `orchestrator/tests/test_s8b_terminal_evidence.py:124-142,159-169` の fixture
   (`retry_ordinal=slot_id[4]` を `slot_id[3]` 系へ)
2. `orchestrator/tests/test_s8b_attempt_registry.py:367-388` の fixture
   (`kind="planned"` なのに `retry_ordinal=slot.attempt_ordinal`)
3. 同 `:4300-4372` の transplant 負例 (誤軸を pin している部分)
4. **(2026-09-09 09:25 追記)** `orchestrator/tests/test_s8b_floor_attempt_launcher.py:1490` の
   planned fixture (`retry_ordinal=reservation.slot_id[4]` = 0 を生成している。訂正後は `None`)。
   子 A2 が所有外として手を付けず報告した箇所で、実測された統合赤 2 node
   (`test_test_seam_forwarding_registry_lacks_launcher_origin_capability`、
   `test_certified_pre_probe_competing_branch_publishes_sealed_terminal`、いずれも
   `campaign_record.retry_ordinal differs from durable identity`) の原因である。
   **所有は launcher file を持つ子 (A1 系) 側とし、同じ強度要求 (i)(ii) を課す。**

**強度を落とさないこと。** 訂正後も次の 2 つの負例が発火しなければならない。
(i) planned なのに `retry_ordinal` が非 null なら拒否、
(ii) retry の `retry_ordinal` を `attempt_ordinal` (recovery 軸) へ差し替えたら拒否。

## 3. plan v2 — 実装面 (9 file) と所有分割

| 子 | 所有 path | 主な作業 |
|---|---|---|
| A1 | `orchestrator/campaign/s8b_floor_attempt_launcher.py`, `orchestrator/tests/test_s8b_floor_attempt_launcher.py` | phase 1 の封印 pre-probe と `launch_probed_floor_attempt`。既存入口は不変 |
| A2 | `orchestrator/campaign/s8b_terminal_evidence.py`, `orchestrator/campaign/s8b_attempt_registry.py`, `orchestrator/tests/test_s8b_terminal_evidence.py`, `orchestrator/tests/test_s8b_attempt_registry.py` | ordinal erratum の実装 (leaf + adapter/replay + fixture 3 箇所) |
| B | `orchestrator/campaign/s8b_floor_campaign.py`, `orchestrator/tests/test_s8b_floor_campaign.py` | 配線 (phase 1 → 分岐 → ticket 消費 → phase 2)、v5 result、prefix capture |
| 親 | `orchestrator/tests/acceptance_duration_ledger.json` | 統合後に add-only で 1 回だけ |

`s8b_floor_contract.py` と `test_s8b_floor_contract.py` は択一 3(a) により変更しない。
契約の追記訂正 `contract-v3.1-erratum-2.md` は親が docs として書く。

**境界の固定 (子は勝手に変えない。変える必要があれば止めて報告する)**

```python
# s8b_floor_attempt_launcher.py が公開する 2 つの新 symbol
def probe_floor_attempt_preconditions(
    *, post_probe: FloorPostProbeCapability,
) -> FloorAttemptPreProbe: ...

def launch_probed_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    pre_probe: FloorAttemptPreProbe,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
) -> FloorAttemptLaunchResult: ...
```

`FloorAttemptPreProbe` は launcher 私有型で、`competing: bool` だけを読み取り公開する。
caller が構成した object・再利用した object・別 capability 由来の object は
`FloorAttemptLauncherError` で拒否する (一回限り)。

## 4. pin 閉包 (段 2 の列挙 + B-9 の 5 件)

凍結 23 件はすべて byte 不変。`FORMULA_ID` は据え置き (裁定 1 未裁定)。
段 2 が列挙した pin に次を追加する。

- `orchestrator/tests/test_s8b_floor_stats.py:1603-1629` — live verifier の AST 比較数と caller exact 3 file
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py:2221-2230` — certified API の署名と固定 recorder
- `orchestrator/tests/test_s8b_holdout_admission.py:3727-3742` — inspector の公開署名 12 引数
- `orchestrator/tests/test_s8b_ratified_freeze.py:1468-1472` — schema 省略時の v4 result key set
- `orchestrator/tests/test_s8b_floor_contract.py:164-180` — campaign の schema alias re-export identity
- `orchestrator/tests/test_ccbench_spawn_sites.py:895-910,2642-2720` — campaign の行番号 4707 / 8636。
  **新 helper は 8636 より後ろへ置き、前方の物理行数を保存する。**

## 5. 変異事前登録 (12 件、単一理由)

段 2 の 14 候補から、レンズ A が帰属不成立とした #4 / #5 / #12 / #13 / #14 を外し、
#8 を向きを直して再登録し、blocker 修正に対応する 4 件を足した。

| # | 変異の位置と内容 | 期待 kill node (単一理由) |
|---|---|---|
| M1 | campaign の default 経路を `launch_probed_floor_attempt` から旧 `measure_fn` へ戻す | `test_default_production_attempt_uses_certified_launcher_once` (launcher 呼び出し回数を直接 spy) |
| M2 | registry plan helper の genesis から retry slot 1 個を除く | `test_registry_plan_declares_exact_planned_and_retry_slot_closure` (helper の exact slot 集合を直接比較) |
| M3 | slot の `repetition` を 0 始まりでなく `round` のままにする | `test_registry_plan_maps_round_to_zero_based_repetition` (helper 直接。integration は marker identity で過剰決定) |
| M6 | campaign が未発行 marker object を `consume_attempt_ticket()` の戻り値の代わりに渡す | `test_certified_campaign_rejects_unissued_consumption_marker` (exact issuer 拒否理由を pin) |
| M7 | launcher が返した terminal の copy を journal emit 前に書き換える | `test_journal_emits_launcher_terminal_record_byte_identically` |
| M9 | production result の schema を v4 へ戻す | `test_default_production_result_is_v5` |
| M10 | result の prefix head を別の有効 64hex へ差し替える | `test_production_v5_self_check_rejects_prefix_head_mismatch` (exact reason `attempt-registry-prefix-head-mismatch`) |
| M11 | erratum 後の retry 束縛を `attempt_ordinal` (recovery 軸) へ戻す | `test_campaign_retry_binds_measurement_ordinal_not_recovery_ordinal` |
| M15 | campaign が phase 1 の competing 判定を無視して marker を消費し phase 2 を呼ぶ | `test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row` (**実** `inspect_floor_holdout_admission_evidence()` を通す) |
| M16 | terminal leaf の `retry_ordinal` 型検査を「非負整数のみ」へ戻す (planned の `None` を拒否) | `test_planned_terminal_binds_none_retry_ordinal` |
| M17 | adapter/replay の比較を `slot.attempt_ordinal` へ戻す | `test_durable_replay_binds_measurement_ordinal` |
| M18 | v5 prefix の被覆を「消費された非 competing session」から「emit した全 session」へ広げる | `test_v5_prefix_covers_every_consumed_non_competing_session` (competing 正例が赤になる向き) |

**過剰拒否の正例 (受理集合を狭めていないことの対照)**
- `test_competing_pre_probe_session_remains_valid_without_attempt_row`
  — pre-probe competing の session が従来どおり有効なまま受理されること。
- `test_planned_session_with_measurement_ordinal_zero_is_accepted`
  — planned が拒否されないこと。

変異は実装後に単一理由性を実測で確認する (`DW-M01`、F820)。
確認できない候補は登録から外し、実効 gate へ再照準する。

## 6. ユーザーへ返す裁定パッケージ候補 (段 7 で `ruling-package.md` に収録)

1. 裁定 2 の (a) 採用と 7 単位化の追認 (親の provisional で進めた)。
2. 択一 1 の二段化と、択一 2 の ordinal erratum の追認。**受理集合の向き**について、
   planned `None` を表現可能にする変更を D1660 の単調縮小方針とどう整合させるか。
3. 前 wave の裁定 1 (`FORMULA_ID` 改版要否) は未裁定のまま持ち越し。
4. C3b の実測 (fresh production campaign と値域 receipt)。1 run の min/max を母集合へ
   一般化できない (B-11) ため、成果物へ載せる限界文言を含めて返す。
5. D2 (consumers/fixtures) — v5 result が holdout / ratified freeze へ到達するのは D2 以降。

## 7. 停止条件

- 子が既存期待値の変更を §2 の 3 箇所以外で必要と判断したら、実装せず報告して止まる。
- pin 閉包 §4 のどれかに触れると判明したら止まる。
- `FORMULA_ID`、凍結 23 件、`attempt_registry_core.py` に触れる必要が出たら止まる。
- 変異の単一理由性が確認できない候補は登録から外す (緑と数えない)。

---

# 段 6 の裁定 (2026-09-09 14:20 追記)

敵対レビュー 2 本 (`out-s6-ra.md` / `out-s6-rb.md`) の所見を裁定した。

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| RA-1 cut-6 M+A- replay に blocker 1 が残る | **real** | 採用 (must-fix) | fix 3 で exact reason `cut6_replay_pre_probe_competing_existing_marker` の fail-closed 停止へ。inspector は不変 |
| RA-2 / RB-1 competing 分岐が実測していない probe 値を記録 | **real (重大、2 レンズが独立検出)** | 採用 (must-fix) | fix 3 で `read_floor_attempt_pre_probe()` を足し実 raw を記録。合成 tuple 除去 |
| RA-3 v5 prefix 被覆 test が result producer を通らない | **real** | 採用 (must-fix) | fix 3 で通常 finalize 経路へ再照準。stale prefix 変異が赤になることを実測 (result 6 / live 11) |
| RB-2 campaign が module attribute 経由で adapter 境界を迂回 | **real** | 採用 (must-fix) | fix 3 で launcher の狭い surface 10 個へ置換。間接参照 0 件を AST test で固定 |
| RA-4 fix 2 は operational な受理集合を広げている | **real** | 採用 (記述訂正) | 「受理集合を広げていない」は誤り。§6 の追認対象へ第 3 の受理変更として明示 |
| RA-6 ordinal 訂正は無限定には「緩和でない」と言えない | **real** | 採用 (記述訂正) | erratum を「受理集合の**置換**」へ書き直す。下記参照 |
| RB-4 親が名指ししていない fixture 変更 1 箇所 (`:1034` の局所 planned builder) | **real** | 採用 (追認) | §2 の 5 箇所目として追認。向きは erratum と同じで強度低下なし |
| RB-3 fix 2 の報告が review の必読に無い | **refuted (親の投げ文の不備)** | — | `out-fix2.md` を作成前に投げ文を書いたため。実体は commit と報告に存在する。段 8 の改善候補へ |
| RA-5 「旧束縛は retry 側で 0 を強いた」 | **refuted (主張は正しい)** | 採用 | 射程を「production reserve を通過した v2 slot では」と明示する |
| RA-7 inspector を緩めていない | **refuted (主張は正しい)** | 採用 | base/HEAD blob が同一 (`fab28e9d3...`) |
| RA-8 pre-probe 偽装拒否は type だけでない | **refuted (主張は正しい)** | 採用 | issuer state・owner・origin seal・one-shot まで検査 |
| RA-9 ordinal 負例の両軸は分離済み | **refuted (主張は正しい)** | 採用 | terminal / replay の双方で異なる値 |
| RB-5〜RB-9 行番号 pin・perf inventory・凍結 bytes・揮発値・v4 consumer | **すべて refuted** | 採用 | pin 4707 / 8636 不変、凍結 23 件の sha256 一致、v5 は v4 consumer で fail-closed |

## erratum の記述訂正 (RA-6 を採用)

「訂正は受理の緩和ではない」は無限定には誤りである。正しい表現は次のとおり。

> これは単調な gate 弱体化ではない。旧誤軸の受理形 (planned の `0`、retry の recovery 軸 `0`) を
> **新たに拒否**し、campaign 契約が要求する planned の `None` と retry の measurement ordinal を
> **新たに受理**する、**受理集合の置換**である。意図した軸への束縛強度は上がる。

同様に fix 2 についても「受理集合を広げていない」ではなく、
「無条件拒否だった sealed terminal 後の遷移を、**検証済み terminal 履歴に限って**受理する
限定解除である」と記述する。どちらも段 7 の記録と裁定パッケージで明示する。

## 既存テスト期待値の変更を許す範囲 (5 箇所目を追加)

5. `orchestrator/tests/test_s8b_floor_attempt_launcher.py:1034` の局所 planned builder
   (`"retry_ordinal": 0` → `None`)。RB-4 が名指しした。erratum と同じ向きで強度低下はない。
