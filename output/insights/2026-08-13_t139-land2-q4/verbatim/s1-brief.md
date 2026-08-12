# 段 1 brief — [T-139] land 2 / Q4 組み替え scope (投入の実務経路 + 解除 decision + 束縛検査)

wave = `dev-wave-t139-land2-q4`、worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4`
(branch `worktree-dev-wave-t139-land2-q4`、base = local main `adf7997f`)。

## 1. scope (すべてユーザー裁定で確定済み。親の裁量ではない)

**同一 land で組むもの (6 件):**

1. `submit_pilot` — pilot 投入の admission gate (純関数 + 薄い副作用境界)
2. PBS driver — pilot job の投入 script / job script (`a09` の**意味的** schedule generator を消費)
3. collector — qsub 結果と job 側 preflight reject の回収 (`qsub_result.raw` / `failure_evidence.pointer`)
4. **D292 を上書きする pilot 解除 decision** (docs/spool/decisions fragment。親が書く。**pilot のみ**)
5. **束縛検査** (テスト。正例 1 本を必ず含む)
6. **D264 の前向き更新** — 現行 D264 は `submit_pilot` の export を機械検査で禁止しており、
   本 wave の実装と正面から衝突する。解除 decision に「D264 の当該禁止を前向きに解く」を含める

**実装しないもの (裁定で確定済み。scope 外を実装したふりにしない):**

- Q1 (受理述語の入力欠落 4 件 B1〜B4) / Q2 (approval manifest の新表現) = **機構を新設しない** (D320)
- `a09` の canonical serialization (§10 閉包 4) と canonical `schedule_sha256` = **名乗らない** (R2 (a))。
  serialization は `operational-only` と明記する
- D308 の機械執行 = T-508 の機械化移管枠 (R4 (a))
- `orchestrator/qualification/submission.py:150` の単発 `os.write` = 別タスク (R5 (a))
- `main_submission` の解除 (D292 が「pilot と本走は別に裁定」と定める)
- **pilot の実走投入** (ユーザー引数が scope 外と明記。経路の実装と land まで)
- 固定 semantic validator (§7.1 の 20 項目) — 本 wave は投入経路であって受領証 validator ではない

## 2. 不変条件 (緩めない)

- **規律 2**: `submit_pilot` は fail-closed。受理集合を広げる変異を採らない
- **R3 (a)**: 受理集合が空の gate は land しない。**通る正例を必ず 1 本添える** (`DW-S04`)
- **D292**: 解除は canonical 台帳へ fold された decision だけ。wave の自己申告・manifest の宣言・
  完了報告・handoff では解除しない。**gate は canonical `docs/decisions.md` を読む。
  spool fragment を権威として読んではならない** (読んだ瞬間に D292 違反)
- **D308**: 解除 decision と束縛検査は同一 land。片方だけ land しない
- **D282 / D291 の承認 bytes を 1 bit も変えない**
- 追補 A `a12`: pilot 1 本目の投入**より前**に完走が必須。未完了なら `design_not_feasible`
- 絶対規律 1: 投入経路は性能計測 build に trace を混ぜない

## 3. 段 1 で実測した前提 (裁定時点から動いたもの・動いていないもの)

| # | 前提 | 実測結果 |
|---|---|---|
| M1 | エントリ 470 の閂 (i) `a12` が実装・実走 0 件 | **解消**。`orchestrator/preregistration/stress_check_simulation.py` (1186 行) が main にあり、pass artifact `output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json` は **tracked** |
| M2 | エントリ 470 の閂 (ii) `a09` serialization が §10 未承認閉包 4 | **不変**。§10 の表に閉包 4 として現存。R2 (a) の「名乗らない」で回避する |
| M3 | `a13` の alpha 予約 | **発行済み 1 行**。`output/registry/t139-alpha-reservations.jsonl` に `ordinal:1` (tracked)。`t139-publication-reservations.jsonl` は 0 byte のまま |
| M4 | D292 の投入禁止 | canonical に現存 (`docs/decisions.md` D292)。D291 `operational_state_on_fold` が `pilot_submission = forbidden` / `main_submission = forbidden` |
| M5 | D264 の export 禁止 | canonical に現存。`orchestrator/tests/test_t139_preregistration_binding.py::test_module_exports_no_admission_api` と `orchestrator/tests/test_t139_stress_check_simulation.py` の `FORBIDDEN_D264_NAMES` が機械検査 |
| M6 | 凍結 bytes の pin 閉包 (`DW-O09`) | 承認済み 3 文書 path を `--include=*.py` で全検索。hit は `test_t139_approval_payload.py` と `test_t139_preregistration_binding.py` の 2 file のみ。本 wave はこれらの bytes を変えない |
| M7 | 投入基盤の実在 (`DW-S01` の別 program 棚卸し) | `tools/pegasus/dispatch_compute.py` (1970 行、qsub 経路)、`tools/pegasus/collect_receipt.py` (239 行)、`tools/pegasus/t139_a12_stress_check.pbs` (30 行、直近の PBS job script 実例)、`orchestrator/qualification/submission.py` (200 行、durable intent の既存 pattern) |
| M9 | **解除 decision の識別子** | **D 番号は fold の瞬間まで確定しない** (`docs/spool/decisions/README.md`: fragment は `{{D:slug}}` placeholder だけを書き、採番は段 9 の land が lock 内で行う)。**したがって gate は D 番号で解除 decision を同定できない。** 節見出しの題文か、本文中の機械可読 payload block を marker にするしかない。**親案 = 本文に固定 key の payload block を置き、gate はその block を canonical `docs/decisions.md` から探す。** 題文だけに頼ると、fold が題を触らないことに依存する暗黙の契約になる |
| M8 | production caller | `orchestrator/preregistration/` を呼ぶ非 test caller は **0 件** (land2-s2 の実測を再確認)。本 wave が最初の production 経路を作る |

## 3.1 【最重要】pilot 投入前提 9 件の現況 (段 1 の実測。これが本 wave の中心論点)

一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t139-pilot-precheck.md` の前提表 +
`output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json` の
`claim_scope` (実測値: `pilot_ready = false`、`remaining_unmet_pilot_prerequisites = [1,4,5,6,7,8,9]`、
`verdict = pass`、`run_status = completed`)。

| # | 前提 | 現況 | 本 wave |
|---|---|---|---|
| 1 | `pilot_submission = forbidden` の解除 | canonical `docs/decisions.md` に解除 decision **無し** | **本 wave が閉じる** |
| 2 | `a13` α 予約 1 件 | **充足** (`t139-alpha-reservations.jsonl` ordinal 1、land 1 の `87cd8d4a` で導入) | — |
| 3 | `a12` 完走 | **充足** (2026-08-12、job 907407.nqsv、tracked artifact) | — |
| 4 | 受領証 schema の digest を `PreregBinding` へ固定 | 未充足 (pin する approval manifest が無い) | **scope 外** (Q1/Q2 の下流) |
| 5 | approval manifest (D282 `F_r` / D291 `F_p` の二重 exact 閉包) | 未充足 | **scope 外** (Q2 = 機構を新設しない) |
| 6 | resolver + `PreregBinding` + receipt writer | 未充足 | **scope 外** (Q2 の下流) |
| 7 | `submit_pilot` + durable submission intent | 未充足 | **本 wave が閉じる** |
| 8 | PBS preflight / driver / collector | 未充足 | **本 wave が閉じる** |
| 9 | cluster slot 1〜8 の identity を pilot 前に固定 | 裁定済だが `a09` 生成が未実装で**発火点が無い** | **本 wave が発火点を作る** |

**帰結: 本 wave 後も #4 / #5 / #6 は未充足で残り、最終的な認可判定は deny のままである。**
`claim_scope` は producer 申告値であり §8 否定検査が「受理条件の入力に使ってはならない」と
列挙する型と同種であるため、gate は**再導出**しなければならず、この field をそのまま読まない。

## 4. 親の provisional 裁定 (攻撃対象。段 3 は必ずここを狙うこと)

- **(P1) 【最重要】R3 (恒真な gate を land しない) との適合。** §3.1 のとおり本 wave 後も
  #4 / #5 / #6 が未充足で、`submit_pilot` の**最終認可の受理集合は空のまま**である。
  エントリ 470 の R3 が禁じた形と同型に見える。親の provisional は次の 3 点セットである。
  1. **層を分ける。** `submit_pilot` の戻り値を「本 wave が所有する検査の逐次結果」と
     「最終認可」に分け、未実装層 (#4/#5/#6) は `prerequisite_layer_not_implemented` として
     **名指しで deny** する。恒真な `raise` にも「常に False」にもしない。
  2. **正例は所有層で構成する。** 本 wave が所有する 6 前提 (#1 解除 decision・#2 α 予約・
     #3 a12・#7 durable intent・#8 driver/collector・#9 slot identity) は
     **すべて実物または本 wave の成果物で満たせる**。この 6 件を満たす入力で
     「所有層の判定が accept へ変わる」ことを正例とし、1 件ずつ落とした 6 負例と対比する。
     → 470 が挙げた「区別できない 4 実装」は、この 6 対比で**すべて区別される**。
  3. **`authorized` を名乗らない。** 本 wave の gate は `pilot_ready` を返さず、
     「実走投入は本 wave の scope 外」を実装の形で保証する。
  **争点:** これを R3 適合と読めるか、それとも「恒真な防壁の land」に当たるか。
  段 3 は**両側から**攻撃すること。適合しないと判断するなら、その根拠を裁定パッケージ候補として返せ。
- **(P1b) 解除 decision の fold 時点問題。** 解除 decision は段 9 の land (fold) で初めて canonical
  `docs/decisions.md` に入る。したがって「実 canonical 台帳に解除 decision がある」正例は
  **受入時点では緑にできない**。親案 = 正例は**テスト内の定数 fixture で canonical 台帳の形を
  合成**して gate を通し、`a12` artifact と `a13` 予約は**実物**を使う。加えて
  「canonical 台帳に解除 marker があるなら、その payload は定数と一致する」条件付き検査を置く
  (land 前は前件偽、land 後に発火)。**この条件付き検査を「恒真な保証」と数えないか**が争点。
- **(P2) 解除 decision の粒度。** pilot のみ解除し `main_submission = forbidden` を明示的に維持する。
  D291 `operational_state_on_fold` の他 field (`addendum_p_blob = not_approved`、`p03 = not_determined`、
  `source_main_run_gate = not_implemented`) は 1 つも動かさない。
- **(P3) gate の権威読み取り。** `submit_pilot` は canonical `docs/decisions.md` を
  「指定された一つの canonical local main」から読む。`repository_root` を caller 供給にしない
  (land2-s2 のレンズ指摘)。**spool fragment・handoff・環境変数は権威にしない。**
- **(P4) `schedule_sha256` の扱い。** R2 (a) に従い canonical を名乗らない。driver が出す digest は
  `operational_schedule_digest` 等の**別名**とし、受領証の `planned_execution.schedule_sha256` を
  埋める経路を本 wave では作らない。→ **本 wave は受領証を完成させない**ことを明記する。
- **(P5) `submit_pilot` の副作用境界。** 本 wave は実走投入を行わないため、`submit_pilot` は
  「認可 + durable intent の書き出し + driver への引き渡し」までとし、qsub の実行は
  driver 側の別関数に置いて注入可能にする (テストが実 qsub を呼ばない)。
- **(P6) D264 の扱い。** 既存 2 テストの期待値 (`FORBIDDEN_*` 集合) は**実装子が触らない**。
  親が解除 decision で D264 を前向きに更新したうえで、期待値の変更は段 4 で明示裁定してから
  実装単位へ渡す。**実装子の独断で禁止集合を削らせない。**

## 5. 成果物影響 (`DW-G05`。実装しない/放置した場合に何が変わるか)

| 項目 | 実装しない場合に変わるもの |
|---|---|
| `submit_pilot` | pilot 投入が canonical な認可検査を通らない経路でしか起こせず、試行台帳に載る run の認可 provenance が空になる |
| PBS driver | pilot の割当てが `a09` の事前 schedule でなく実行時判断で決まり、`allocations[]` の identity が結果依存になる |
| collector | qsub 失敗 attempt の row が回収されず、`attempts[]` の exact 被覆 (§4.13) が構造的に満たせない |
| 解除 decision | D292 により pilot は永久に投入不可。ladder の実測が 1 本も得られず certified 選択の材料が欠ける |
| 束縛検査 | 解除だけが land し「止める文は無く通す gate も未検証」の窓が開く (D308 が禁じた形) |
| D264 更新 | 実装と canonical decision が矛盾し、機械検査が赤のまま land できない |

**分割 land した場合 (D308 が要求する問い):** 解除 decision だけ先に land すると受理集合が
一方的に広がる (窓が開く)。束縛検査だけ先に land すると安全側だが発火しないまま land され
検出力を実測できない。**よって同一 land 以外の形を採らない。**

## 6. 並列分割方針 (段 5)

編集ファイル所有が素集合になる 3 単位を想定する。依存があるため **U1 を先行**させ、
所有パス限定 patch を展開してから U2 / U3 を並列投入する。

- **U1 (先行)**: `orchestrator/preregistration/` の admission gate 本体 + 権威読み取り
  (`submit_pilot`、release decision resolver、`PreregBinding` = identity-only) + その test
- **U2**: `tools/pegasus/` の PBS driver (`a09` 意味的 generator + job script + 投入 script)
- **U3**: `tools/pegasus/` の collector (qsub 結果・preflight reject 回収) + その test

U2 と U3 は同じ directory を触るため、**ファイル所有を素集合にできなければ 1 単位へ統合**する。

## 7. 既存被覆の検索 (性質で検索。純増検出力だけを書く)

- 「canonical decision が無ければ投入を拒む」性質の既存検査 = **0 件** (`pilot` を含む test は
  floor campaign / t793 / t810 系で、いずれも T-139 の投入認可ではない)
- 「投入前に事前 simulation の完走を要求する」性質の既存検査 = **0 件**
- 「durable submission intent を qsub より前に create-only で書く」性質の既存検査 =
  `orchestrator/qualification/submission.py` 系に T-126 の実装はあるが、T-139 の受領証契約への
  束縛は **0 件**
- **純増検出力**: 上記 3 性質を初めて機械検査にする。既存 gate との二重化は無い

## 8. 軽量版を採らない理由

投入禁止という**正しさ防壁に触れ受理集合を変える** wave である (`DW-C00`)。
段 2・3 と段 6 の敵対検証子を省かない。先行 wave (エントリ 470) も同じ判断をした。
