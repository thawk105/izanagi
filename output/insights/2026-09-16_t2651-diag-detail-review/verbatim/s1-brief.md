# [T-2651] 段 1 brief — 診断本文保持の敵対レビューと変異 harness 本走

基準: local main d97c423bdd14e0b416cb4f585d350e6c2b251287 (着手直前)。
wave branch: worktree-dev-wave-t2651-diag-detail-review。

## 研究前進 (土台)

止めている研究は **official 床値 campaign (T-1851 / T-2650)** である。この campaign は
condition gate の拒否で 3 回とも停止し (request 998882 / 999039 / 999102)、gate 専用の
isolate worktree は `/scr` にあり job 終了で消えるため、拒否本文は二度と取れない。
直前 wave (worklog 1515) はこの診断本文の保持を実装して着地させたが、**段 3 のレンズは
走行前の plan と brief を攻撃したため実装差分を見ておらず、変異 harness 本走も未実施**である
(一次資料: `output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §7・§8)。
最小差分は「着地した実装差分そのものへ敵対レビューを当て、登録済み 6 変異を本走で殺しきる」こと。
完了判定は (a) レンズ 2 本の全所見が real/refuted へ裁定済み、(b) M1-M3 / M5-M7 が
期待 node 完全一致で KILLED、(c) 受入全走が緑、の 3 つ。

## 対象 (レビュー対象の実体)

着地差分 = `affd2a105^..c185b9fd4` のうち次の 3 file。

- `orchestrator/campaign/s1_direct_comparison.py` (+47 行) — `_CONDITION_DETAIL_LIMIT_BYTES`、
  `_bounded_condition_detail()` 新設、`_condition_records_for_genome()` の
  `if not admission.admitted:` 内側 (現行 HEAD で 334-352 行)
- `orchestrator/tests/test_s1_direct_comparison.py` (+221 行) — 163 / 201 / 235 / 278 / 312 /
  320 / 329 / 345 行の 8 テスト
- `orchestrator/tests/test_s8b_oracle_manifest.py` (±4 行) — materializer live sha256 と
  `PIN_GATE_SPEC_SHA256` の追随更新のみ

## 段 1 で実測した事実

- 変異 harness は実行可能: `tools/mutation_harness.py --help` rc=0 (`--plan-only` あり)、
  dispatch 可 (qstat rc=0、他 session の 1067.nqsv が 1 件のみ)、orphan hold 0 件。
- baseline 緑: 上記 2 test file の焦点走が計算ノード dispatch で rc=0 (request 1110.nqsv、Elapse 20S)。
- **masking 層が 1 つ実在する**: `orchestrator/tests/test_s8b_oracle_manifest.py:88-89` が
  `s1_direct_comparison.py` の live byte sha256 (`c7364f2da5…`) を golden 逐語で pin している。
  この file への**任意の**変異は当該テストを必ず赤にするため、runner の対象へ入れると
  全変異が同一理由で赤になり `DW-M03` の kill 要件を満たさない。兄弟の
  `test_s8b_oracle_report.py` / `test_s8b_oracle_driver.py` は live file から hash を
  動的に組むため自己整合で、masking しない。
- 同型欠陥を持つ兄弟 driver は 14 箇所実在する (`backoff_sweep.py:225`、`p3_kickoff.py:94`、
  `p3_s4_loop_sort.py:137` ほか)。前 wave は `DW-G03` 充足を確認したうえで**横展開しない**と裁定済み。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 変異 runner の対象集合を `orchestrator/tests/test_s1_direct_comparison.py` 単独に絞り、
  `test_s8b_oracle_manifest.py` を冗長 gate として `DW-M03` に従い単独変異の証拠から外す。
- **(P2)** 事前登録は前 wave の M1-M3 / M5-M7 を現行 HEAD の anchor へ取り直してそのまま本走する。
  変異の追加・削除をしない。M4 は取り下げ済みのまま復活させない。
- **(P3)** 本 wave の実装差分は原則ゼロとする。段 4 で real と裁定した所見がある場合だけ
  段 5 で Codex `role=author` を起こす。
- **(P4)** 敵対レンズは plan ではなく**着地実装差分**を攻撃対象にする (ユーザー明示の取り直し)。

## 不変条件

- 規律 2 を緩めない。condition gate の受理集合・reason code 語彙・admission 判定・rc・
  green 経路の bytes は不変。`condition_meaning_gate.py` は触らない。
- 既存テストの期待値を変えない。反転・緩和・skip・削除を禁じる。
- 凍結成果物の bytes を変えない。`PIN_GATE_SPEC_SHA256` と manifest の materializer sha256 は
  実装差分が出た場合だけ追随更新し、RAW 内の変更を当該 1 field に限定して旧新両値を報告する。
- 変異は `DW-O19` に従い統合 commit 後・`--porcelain` 空確認のうえで harness 経由だけで行い、
  復元は `git checkout --` を正本とする。

## scope 外 (ユーザー明示)

兄弟 driver への横展開、仮想リスク向けの gate・検査・台帳・一般化の追加、
condition gate 本体の受理集合変更、床値 campaign の再投入。

## 成果物

`output/insights/2026-09-16_t2651-diag-detail-review/` に
README.md (所見表・変異 matrix・検査表)、`verbatim/` (brief・plan・レンズ 2 本・レビュー)、
`mutation-probe-spec.json` / `mutation-probe-out.json` /
`mutation-final-spec.json` / `mutation-final-out.json`。
台帳は `docs/spool/` の fragment として書き、fold は段 9 の land に任せる。

## 並列分割方針

段 2 は plan 1 本 (read-only)。段 3 はレンズ 2 本並列 (read-only) —
A は正しさ境界と受理集合 (規律 2 への攻撃)、B は整形器の実効性と証拠の復元可能性。
段 5・6 は real 所見が出たときだけ起こし、所見が編集 path で素集合に割れるときだけ並列にする。
