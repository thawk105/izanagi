# [T-1851] 段 1 brief — 単位 C1b やり直し: 封印 terminal 証拠の縦 1 単位

継承 tip `89605bb39` + local main `645d0d663` 取り込み `8193eefdb`。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**
継承元の正本は `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/` の
README 7 節と `rulings-resolved.md` 全 6 節。**契約は本 wave の `contract-v3.md` が正本**で、
各条項は `parent-probes.md` の probe 番号を持つ。

## scope (成果物影響、DW-G05)

v2 台帳の terminal は `_reject_unsealed_s8b_v2_terminal` (`s8b_attempt_profile.py:556-563`) が
無条件で拒否し、`S8B_V2_RETRYABLE_FAILURE_REASONS` は空。放置すると v2 台帳に terminal 行が
1 行も出ず、B2 の prefix proof が参照する行数が観測開始で止まり、result v5 の
`attempt_registry` proof を作れない。C1b はこの拒否 hook を封印証拠 API へ置き換える。

## 確定済み裁定・不変条件

- D1341 land しない。D1113 呼び手は証拠の値を選べない。D1522 上流が拒否する形でも下層の実体を
  直接呼ぶ test を置く。
- 契約 v3 の 5 節 (観測後の理由を別 field に載せる)、3 節 (`exec_failures` は等値束縛だけ)、
  6.4 (信頼境界)、4 節 (単位を分割しない) は codex 2 本に諮って決着済み。**再設計しない。**
- 規律 2: `observed` へ落とす逃がし道を 1 本も作らない。相互整合が 1 つでも破れたら拒否する。
- v1 の event key 集合と受理集合は 1 bit も変えない。
- `_CERTIFIED_MEASUREMENT_KEYWORDS`、`_owned_post_probe` の argv / timeout / 関数名
  (spawn-site pin) は不変。
- `attempt_registry_core.py` へ `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を
  書かない (`test_reflux_formal_consumer.py` の AST 走査下、probe P-7)。

## 変更面のアンカー (実測)

| path | 現物 | C1b が触る点 |
|---|---|---|
| `orchestrator/campaign/s8b_terminal_evidence.py` | **不在** | 新設。契約 v3 の dataclass、`seal_terminal_evidence` (draft 返し)、`require_sealed_terminal_evidence`、E1 再導出の純関数 |
| `s8b_attempt_profile.py` (684 行) | `_reject_unsealed_s8b_v2_terminal :556`、空の `S8B_V2_RETRYABLE_FAILURE_REASONS :533`、`_S8B_V2_EVENT_KEYS :495` の一律内包表記 | 拒否 hook を validator へ、E2 の 4 語を active 化、terminal だけに 2 key を足す event 別分岐 |
| `attempt_registry_core.py` (2,131 行) | `DomainProfile :198`、`_assert_null_matrix :1050`、等値検査 :1419、validator 呼出し :1434、`record_attempt_terminal :2000` | `retryable_reason_field` 追加、null matrix の照合先を profile 選択に、`observed`/`not-consumed` の新 field null 要求、terminal 行への 2 key 条件付き emit |
| `s8b_attempt_registry.py` (3,122 行) | `_AttemptState :165`、handle 機構 `_new_handle :258` / `_require_handle :279`、guarded writer `_write_staging :1173` | `record_sealed_attempt_terminal` 新設、draft → validated の発行、証拠文書の公開 |
| `s8b_floor_attempt_launcher.py` (909 行) | terminal call :844、`launch_floor_attempt :855`、test seam `:879` | 封印 draft の発行と新 adapter API への差し替え |
| test 3 file | launcher / registry / core profile | 各所有者が持つ |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 実装子 3 本、依存 1 段。** (1) leaf + その test を先に閉じ、完了後に
  (2) launcher + profile + その test と (3) core + adapter + その test を並列に置く。
  所有 file は素集合。見積り production +1,000〜1,600 行 / test +1,500〜2,400 行。
- **(P2) 縦 1 単位を割らない。** production 効果のある分割は無いとレンズ B が実測済み。
  段 2 が「収まらない」と判定したら、中途半端に割らず**契約 v3 の文書だけで切る**。
- **(P3) production 到達性は 0 のまま。** `launch_floor_attempt()` の production 呼び手は
  再実測でも 0 件。gate 入力は fake 由来の値域しか実測できない (契約 v3 の 9 節)。
- **(P4) 凍結 bytes は増えない。** 新識別子・新 path の pin 閉包は 0 件、変更予定 7 file の
  whole-file hash pin も 0 件 (probe P-7)。新しい成果物名を足すので段 2 で引き直す。
- **(P5) 変異候補は再照準が要る。** 前 wave の M4/M5/M6/M7/M9/M12 は軽い具体化で成立するが、
  M1/M2/M3/M8/M10/M11 は設計が A 案から B 案へ変わったので照準し直す。M13〜M18 は範囲外。

## 成果物の形

leaf module 1 本 + その test、既存 4 file への差分、insight
`output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/`、worklog / decisions fragment。
受入は login からの `tools/dev_wave_wait.py acceptance --lease-optional`。
