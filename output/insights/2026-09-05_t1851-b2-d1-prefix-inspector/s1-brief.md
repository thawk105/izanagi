# [T-1851] 段 1 brief — 実装単位 B2 (inspector) と D1 (契約・proof 型) の非 terminal 部分

日付: 2026-09-05。branch `worktree-dev-wave-t1851-unit-a`。継承 tip `fd814b2f0`。
main 取り込み後 tip `50dbf9158` (local main `61bc6ac69`、両親が共に触った file 0、integrator)。

## scope

台帳配線 3 task 閉包の 6 段分割 `B1 → A → B2 → D1 → C → D2` のうち、**B2 と D1 の terminal 証拠に
依存しない部分**を unlanded checkpoint として積む (A2β README 8 節)。terminal 証拠の契約は単位 C の
brief が先に固定するので、terminal に依存する部分 (coverage の全単射、sealed terminal 集合との照合、
`finished_at` の terminal field、attempts projection の `attempt_id`) は本 wave では実装せず境界だけ固定する。

- **B2-a (admission 層、read-only prefix inspector):** current protocol generation の全 bytes を
  `_locked_readonly(root)` 内で読み、世代 genesis から profile を構築して全行 replay する read-only inspector を
  **既存 recovery reader と別 API** として新設する (s4-adjudication-r2 B2-7)。入口は 2 つ。
  producer capture = full replay 後の `N=len(rows)` と `rows[N-1]["event_sha256"]` を返す。
  verifier inspection = live 全行を replay した後だけ `len(rows) >= N` と `rows[N-1]["event_sha256"] == reported head`
  を比較する (D1337 prefix 証明)。N 以後も parse / replay 対象なので壊れた tail は拒否し、正当な append は許す。
- **D1-a (契約):** result schema を legacy v4 / v5 / readable 集合へ分け、schema 別 exact key 集合を持つ
  (v5 = v4 keys + `attempt_registry`)。`result_keys_for_mode` は schema を受ける。
- **D1-b (proof 型):** v5 の `attempt_registry` は exact 7 field object
  (`schema` literal / `registry_schema` / `freeze_sha256` / `protocol_sha256` / `schedule_sha256` / `row_count` / `chain_head_sha256`)。
  row_count は正整数、digest は lowercase hex64、`chain_head_sha256` は `rows[N-1].event_sha256` の意味に限定する。
  validator は core (`attempt_registry_core`) に置く。
- **D1-c (pure verifier):** `verify_floor_artifact()` は v4 なら `attempt_registry` field を禁止して既存受理を維持し、
  v5 なら proof shape・binding (freeze / protocol / schedule)・正の N・nonzero head を検査し、live wrapper から渡された
  独立 proof と `reported == independently_replayed_live_prefix` の向きで比較する。
- **D1-d (live wrapper):** `verify_floor_artifact_with_live_admission()` は v4 で registry を一切読まず、v5 だけ B2-a の
  verifier inspection を呼ぶ。v4 の受理面を増減させない。
- **本 wave が実装しないもの (境界だけ固定):** coverage (result attempt identity ↔ prefix 内 sealed terminal の全単射)、
  producer の `assemble_result(attempt_registry=proof)` と pending の再読 (単位 C)、candidate v5-only 入口・ratified
  reverify・earlier result の v5 検査 (単位 D2)、E1 / E2 (単位 C、A2β 7 節)。

## 確定済みユーザー裁定 (不変)

- D1194 (前向き束縛のみ)、D1337 (prefix 証明 `{N, head_at_N}`、末尾一致は禁止)、D1340 (予算は世代横断 replay)、
  D1341 (6 段を揃えて 1 変更単位で land。**本 wave も land しない**)、D1342 (発行層は台帳生存を再確認しない)、
  D1336 / D1114 (書き手が production から呼ばれるまで land しない。本 wave の gate は production で発火しない)。
- D1522 (上流が拒否しても下層の実体を名指しする直接検査を置く)、D1533 (非束縛の集合を明記する)。
- A2β 7 節の 3 決定: E1 / E2 は単位 C、証拠の意味規則は固定済み、分類 claim / 回復行は今は囲まない。
- D95: 実装面は Codex author。規律 2 (正しさゲートを緩めない) と規律 3 (構造化した拒否理由) は不変。

## 不変条件

- v1 台帳 (1 段 path、schema v1) の reader・writer・filename digest は 1 byte も変えない。v2 terminal は A2α の S5 / S6 の
  二層拒否のまま (E1 は単位 C)。
- 現行 producer の出力 bytes は変えない (下の (P1))。凍結成果物・trust root・`FROZEN_MANIFEST` に触れない。
- 既存 v4 artifact の受理集合は不変。v4 で `attempt_registry` が現れれば拒否 (exact key)。
- 新 gate はすべて exact / fail-closed。「reported が無ければ skip」の形を作らない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 現行 producer は v4 のまま。** `RESULT_SCHEMA` の値 `s8b-floor-result/v4` は本 wave で変えず、v5 は別名の定数として
  足す。plan v2 の「RESULT_SCHEMA=v5」は 6 段が揃った終端状態であり、単位 C が producer を v5 へ切り替える。理由: 本 wave で
  値を変えると proof の無い producer が自分の contract で止まり、受入全走が緑にならない (D1341 の checkpoint 条件)。
- **(P2) inspector の置き場所。** plan v2 は `s8b_holdout_admission` を指すが、世代 path の解決・genesis peek・profile 構築は
  `s8b_attempt_registry` が持ち、同 module は admission を import する。循環を避けるため **公開 read-only API は
  `s8b_attempt_registry` に置き、admission / stats はそれを呼ぶ**形を暫定とする。plan が現物で判定する。
- **(P3) 検査入力の到達可能性 (DW-O13)。** v2 世代は現在 genesis + reservation (start / classification) 行までしか持てない
  (terminal は S5 / S6 で拒否)。よって prefix inspector の正例は `N >= 1` の genesis / start 行の世代で組み、
  v5 artifact は test が組み立てる (producer は無い)。D1114 の条件どおり production の呼び手は 0 件であり、本 wave は
  「効いている」と書かない。
- **(P4) `result_keys_for_mode(mode, *, schema=<legacy v4>, perf_preflight)` の default で D2 の file を触らない。**
  22 呼出し (production 4 file / test 3 file) のうち holdout_freeze / ratified_freeze は単位 D2 の所有であり、本 wave では
  変更しない。schema 必須化は D2 が行う。
- **(P5) 1 wave に収まる。** 実装子 1 本 + fix 3 巡以内、production +500〜900 行 / test node +40〜70 と見込む。
  plan が A1' と同じ手順で規模を実測し、収まらなければ B2-a + D1-b (inspector + proof 型) を先に、D1-a / c / d を次 wave に割る。
- **(P6) 所有分割。** 実装子 1 本 (B2-a → D1-b → D1-a → D1-c / d の順)。plan が 2 本へ割るなら file 所有で割り、
  stats (D1-c / d) は inspector API の signature を先に固定してから着手する。

## 実アンカー表 (tip `50dbf9158`)

| file | symbol / 現行行 | 本 wave の扱い |
|---|---|---|
| `orchestrator/campaign/s8b_attempt_registry.py` | `_entry_paths` :520、`_peek_registry_genesis` :637、`_registry_generation_paths_locked` :649、`_profile_and_binding_for_generation` :727、`_registry_bytes` :824、`_load_other_generation_budget_counts_locked` :1392、`read_attempt_registry` :1631 (write lock で replay する既存 reader) | B2-a の新 read-only API の土台。既存 symbol は変えない |
| `orchestrator/campaign/s8b_holdout_admission.py` | `_locked_readonly` :730、`_measurement_generation_*` :900-1136、`validate_floor_attempt_consumption_marker` :5082、`inspect_floor_holdout_admission_evidence` :6090 | B2-a の lock と、D1-d が呼ぶ既存 inspector。既存 recovery reader は保存 |
| `orchestrator/campaign/attempt_registry_core.py` | `event_sha256` :240、`chained_event_row` :246、`previous_event_sha256` :260、`_assert_chain` :449、`load_attempt_registry` :1454、`load_attempt_registry_with_budget_counts` :1465 | D1-b の proof validator を置く。chain の意味論は変えない |
| `orchestrator/campaign/s8b_attempt_profile.py` | `S8BAttemptBinding` :48 (freeze / protocol / schedule の 3 digest) | proof の binding 3 field の出所。変更なし |
| `orchestrator/campaign/s8b_floor_contract.py` | `RESULT_SCHEMA` :34、`_RESULT_KEYS` :81-87、`result_keys_for_mode` :157 | D1-a |
| `orchestrator/campaign/s8b_floor_stats.py` | `verify_floor_artifact` :682、`verify_floor_artifact_with_live_admission` :1036 | D1-c / D1-d |
| test | `test_s8b_attempt_registry.py`、`test_s8b_holdout_admission.py`、`test_attempt_registry_core_s8b_profile.py`、`test_s8b_floor_contract.py` (:180 の v4 pin は不変)、`test_s8b_floor_stats.py` (:596 / :1323-1325 の v4 pin は不変) | 既存 file へ足す。新規 test file は自走 harness と列挙 meta-test を要するので作らない |

## DW-O09 / O10 / O13

- pin 閉包: `s8b-floor-result/v4` の literal は contract :34、`test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:596,1325`。
  `RESULT_SCHEMA` の word は production 6 file (campaign / holdout_freeze / ratified_freeze / stats / paper_story_a1_paired /
  oracle_n_pilot) と test 5 file。tracked な v4 result bytes は `output/` に 0 件。(P1) により producer 出力は不変なので
  DW-O10 (producer write-path 棚卸し) は発火しない。
- DW-O13: proof の入力 field は `S8BAttemptBinding` の 3 digest と `chained_event_row` の `event_sha256` に実在する。
  v5 artifact の `attempt_registry` field は実成果物に 0 件 (到達不能)。これは D1114 / D1341 が予定する状態であり、
  本 wave の gate は production で発火しない。到達可能な値域は (P3) のとおり。

## 成果物の形と DW-G05

放置時: v5 proof を検証する側が無いままでは単位 C の書き手を D1341 の同時 land に載せられず、certified 選択は台帳束縛の
無いまま (D1194 の「謳うだけで発火しない」状態) が続く。既存 certified の値・受理集合・参照は本 wave で変わらない。

成果物: 実装 commit (Codex author)、変異 matrix (事前登録は段 4)、焦点走 + 受入全走 child-green、insight README、
worklog / decisions fragment。D1341 により land しない。

## 実測環境

focus 走は login node、受入全走は `tools/dev_wave_wait.py acceptance` (必要なら D612 上書き 3600/600)。新規 Pegasus
実行体を要する実測は無い。変異は `tools/mutation_worktree.py` でなく harness 直接 + repo 外退避 (並行 wave 環境)。
