---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1434-adjudication-oracle
seq: 1
title: [T-1434] adjudication 層を reveal 後の task 別 oracle へ束縛し、同じ束縛が組込み manifest では 1 度も発火しないことを実測した (コード + docs、branch worktree-dev-wave-t1434-adjudication-oracle、変異 matrix = baseline PASSED・9/9 一致・KILLED 9・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「事前登録文書の (b) adjudication 層の task-specific oracle 対応を実装する。
  到達度記述が複数箇所に複製される構造なので、実装が進んだら同じ commit で全複製箇所を揃えること。
  task-specific oracle が実際に呼ばれることを実体名で検査すること」。
- **直近 wave の記録と依頼が食い違っていた。** worklog (1027) の持ち越しと事前登録 §5.2 は
  「(b) は §8 の独立 oracle ledger が未作成のため着手条件を満たさない」と書いていた。
  親は**機構については覆ると裁定した** — 同じ文書の §5.3 が「着地したのは現行 task manifest の
  中にある oracle 契約、すなわち `oracle_kind` と `known_finding_ids` とその consumer であって
  機構は着地」と既に書いており、`_aggregate_verified` は同じ per-task 検査を実装済みだったからである。
  **台帳の中身が無いことと、装置が task 別に束縛できないことは別の事実である。**
  段 3 の敵対レンズ B が §8 の逐語から独立に同じ結論へ達した — §8 は ledger を実験開始前に
  作ることを要求するが、generic な consumer の実装前に ledger が存在せよとは書いていない。
  詳細は {{D:oracle-ledger-vs-binding-separation}}。
- **この wave の一番大事な実測は、実装した機構が現行入力では 1 度も発火しないことである。**
  組込み `TASK_MANIFEST` は `_manifest_task_entry` が POS/NEG の双方へ同じ
  `sorted(_LEGACY_KNOWN_FINDINGS)` を入れるため、親が module を import して測ったところ
  両者は完全に同一の 11 件 (`A-1..A-4, B-1..B-6, R-1`) だった。task 別集合と manifest 全体 union が
  同じ集合を返す。**したがって新しい narrowing も、既に「機構は着地」と記録されていた
  `_aggregate_verified` の task 別検査も、組込み manifest の入力では union より狭い受理集合を
  作らない。** 差が出るのは task ごとに集合が異なる外部 v3 manifest だけである。
  事前登録の §5.2 / §5.3 / 総括にこの限定を明記した。
- **段 3 の敵対相談 2 レンズは所見 13 件を出し、親は 13 件すべてを real と裁定した。
  うち 4 件は親 brief 自身への反証である。**
  - **join 前提が誤りだった。** 親は「`_load_adjudication` は reveal 後に走るので検査時点で
    task が同定できている」と書いたが、実コードでは verdict 検査ループが `mapping` の辞書化と
    `slot_by_run` の構築より**前**に走る。既存の検査位置へ `benchmark_task_id` を渡すことは
    できない。段 2 プランが先にこれを正し、join 後の第 2 検査という唯一の方針が確定した。
  - **「真部分集合」は一般には偽だった。** 等しくなる場合が 3 通りある (組込み manifest、
    task 1 件の manifest、対象 task が union 全体を持つ manifest)。
  - **「bytes で pin する台帳・trust root は存在しない」は偽だった。**
    `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` が
    `tool_sha256` に旧装置の値を持つ。親が現物で裏取りしたところ現行 bytes と一致せず、
    F39 の分類は**歴史記録**で、更新閉包 0 件という結論自体は維持できた。
    書き分けの欠落であり、詳細は {{F:absence-claim-must-distinguish-live-consumer-from-any-pin}}。
  - **成果物影響の記述が実コードと一致していなかった。** 親は「§8 の記述的 finding coverage の
    分子が誤って増える」と書いたが、**その分子は実装されていない**。親が確認したところ
    `output/` に `judgments` を持つ material manifest は 1 件も存在しない。実際に変わるのは
    材料レポートの `valid` と `experiment_complete` を false にし、`primary_judgment_ledger` /
    `new_finding_ledger` / `decision` を null 化することである。裁定で書き換えた。
- **段 3 レンズ B が fixture の設計を 1 段深くした。** 当初案の alpha/beta 各 1 slot は
  `_validate_schedule` の block 検査 (同一 task・stage・cache・price の 2 行が連続し
  `(arm, requested_model)` の組が 2 つ異なる) を通らない。schedule を packet source から省く
  逃げ道は `make_packets` の scheduleless 互換経路を通るだけで、v3 schedule・`_replay_manifest`・
  実 entrypoint の配線を 1 つも証明しない。**4 slot の paired schedule を必須にした。**
- **段 6 の敵対レビューは、実装ではなく変異の帰属を 2 件突いた。**
  - 変異 M7 (`_replay_manifest` の `task_manifest` 転送を組込み manifest へ差し替える) は
    赤にはなるが、赤の理由は既存の digest 不一致と既存 union 検査であって新分岐とは無関係だった。
    fix 子が `_load_adjudication` を**実物へ委譲する spy** で包み、渡された manifest の
    canonical digest だけを 1 個の assert で検査する専用 node を足して単一理由化した。
  - 変異 M8 (dimension join 失敗時の packet 単位 reason 削除) の赤は診断文字列だけだった。
    `_slot_dimension_map` が先に slot 単位の reason を積み、変異の有無にかかわらずその slot は
    `joined` されず成果物は既に無効である。`DW-M03` / `DW-M08` に従い **kill でなく
    診断 sensitivity pin** として別枠記録した。**内訳は correctness kill 8 件 + 診断 pin 1 件**であり、
    harness の「KILLED 9」をそのまま「正しさゲートを守る変異が 9 件」と読んではならない。
- **変異 M6 が機構の必要性の反実仮想を確定した。** 既に着地し「機構は着地」と記録されていた
  `_aggregate_verified` の `equivalent not in known_finding_ids` は、**削除しても本 wave 前は
  全テストが緑だった**。本 wave で新設した 1 node だけがこれを検出する。
- **変異 matrix は 2 段構えで回した。** `DW-M08` が期待 node の完全集合一致を要求するため、
  まず全件 SURVIVED 期待の probe を回して観測 node を集め (9 件すべて MISMATCH = 全部赤になり
  node が取れた)、その完全集合を pin した本走で 9/9 KILLED・完全一致を得た。
  期待 node を推測で書いていたら、当たっても偶然か実力か区別できなかった。
- **単一理由性は 2 対で確認した。** 変異 M2 は `[second-reader]` だけを赤にし `[parent]` を
  緑のまま残す。変異 M4 (欠落を受理させる) は `[missing]` だけを赤にし `[wrong]` を緑のまま残す。
  reader 方向と wrong/missing の 2 軸が独立に所有されている。
- **段 6 レビュー A は所見 0 件だった。** `DW-S06-A` に従い変異で裏取りするまで緑と数えず、
  上記の matrix で裏取りした。焦点再レビューの対応表は 3 件すべて `closed`、GO。
- **背景 job の完了通知が producer 生存中に先行して届いた** (3 回)。`.done` 不在・artifact 不在・
  pid 生存を毎回実測して回復した。**`DW-O01` が既に「通知は先行しうる」と明記しており、
  親の判定は契約どおりである。新しい欠陥ではないので台帳へは起票しない。**
  最初にこれを待ち手 tool の欠陥へ帰属させかけたが、素の `until` ループでも同じことが起き、
  かつ後で見るとその `until` ループ自体は正しく完走していたため、帰属を 2 度訂正した。
- 子の工数は Codex 8 本で wall 4243 秒、model call 242、出力 token 172050。
  内訳は plan 455 秒 / consult(sol) 603 秒 / consult(luna) 450 秒 / author 1258 秒 /
  review 411 秒 / review 462 秒 / fix 269 秒 / focus 335 秒。全 8 本が `gpt-5.6-sol` の `xhigh`。
- 親の焦点走は 2 回とも緑 (`orchestrator/tests/test_codex_reasoning_ab.py`、
  実装後 597 passed / 2 skipped、fix 後 598 passed / 2 skipped)。変異 baseline も PASSED (80.1 秒)。
- 起動時の編集面重複検査で、`tools/codex_reasoning_ab.py` と
  `docs/phase3-t189-model-routing-preregistration.md` に触れている branch も稼働 worktree の
  未 commit も 0 件であることを確認した。同時刻に起動した `dev-wave-t1769-b4-wiring-probe` は
  **B-4** 事前登録の wave であって T-189 ではない。

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: (a) task manifest の CLI 入力口、
  (c) 費用の部分正規化計算、**(b) adjudication 層の task 別 oracle 束縛**が接続済み。
  (b) は 2026-08-27 に、mapping reveal 後の join を確定させ、両 reader の raw verdict 行を
  その task 自身の `known_finding_ids` で検査し、`oracle_kind` を
  `combined_verdict_sha256` の計算前に束縛するところまで着地した。
  **ただし組込み manifest では POS/NEG の集合が同一のため、この束縛は 1 度も発火しない。**
  費用を gate へ接続する件は D932 が「記述統計として出し certified な判定を動かさない」と
  裁定済みで、接続しないことが結論である。残る未解決点は次のとおり。
  §8 の独立 oracle ledger の作成・凍結とその固有 hash 契約・finding schema
  (severity / must-fix / 根拠 artifact / 検出条件 / canonical identity)。
  §8 の記述的 coverage の集計 ({{T:t189-oracle-coverage-metrics}} が持つ)。
  task 固有 acceptance (D767 により `unbound` 固定)。
  正規 receipt へキャッシュ書込の数量を保存し完全な費用を出すこと。
  `_certification_scope` を改訂して費用を certified field にすること。
  `SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。served model attest の不在。
  schedule が `requested_model` を省略すると `MODEL` へ既定化される件と、`collect-run` verb の
  `--expected-model` の既定値。block 検査が sol/luna 各 1 回を固定しない件。
  v3 schedule の task/arm 期待件数が schedule 自身から導出される件。schema v2 と
  `schema_version` 欠落の schedule が `LEGACY_EXPECTED_SCHEDULE` 固定である件。
  standalone `verify-snapshot` が `--task-manifest` を持たない件。
  base: 79215c057a6d7d881f8e33b329f79ad7108f2955ed9214edd805ece531a58f57

### 新規

- {{T:t189-oracle-coverage-metrics}} **P2・新規**: 事前登録 §8 の記述的 finding coverage を
  装置へ実装するか、実装しないと裁定するかを決める。§8 は
  「両 reader が検出と一致した oracle finding 数 / oracle finding 総数」という式と、
  negative control の分母除外、false-finding rate の別集計を明文で要求しているが、
  `_aggregate_verified` には numerator も denominator も存在しない。段 3 レンズ B と
  段 4 裁定で scope 外の real 所見として確定した。**§8 の独立 oracle ledger が
  作られるまで分母が定義できないため、ledger の作成と順序関係がある。**
- {{T:t181-apparatus-pin-history}} **P2・新規**: `output/insights/2026-08-09_t181-certified-rerun/
  apparatus-pin.json` が旧装置の `tool_sha256` を trust root として持つ歴史記録の今後の扱いを
  裁定する。本 wave では F39 の分類を**歴史記録**とし更新しなかった。更新すると過去の
  `aggregate.json` / `verify.json` がどの装置で certified だったかという参照が改変されるためである。
  同種の歴史 pin が他にもあるかは未調査である。
