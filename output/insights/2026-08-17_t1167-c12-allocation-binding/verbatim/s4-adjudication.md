# [T-1167] 段 4 裁定 — 8c 事前登録 C12 allocation 節の縮小

親が段 2 プランと段 3 レンズ A / B の全所見を real / refuted、採用 / 不採用、scope 内 / 外へ裁定する。

## 0. 裁定の前に親が実測したこと (2026-08-17 01:1x〜01:5x JST)

| 検算 | 結果 |
|---|---|
| g3 の raw sha256 = `2b28cde32feaa4509ff6c8cfe382240d7b4d2d8f919608a6199f2b282c2f23e1` | プランと一致 (実測) |
| `test_current_evidence_contract_hash_is_frozen` の現行値 `983f5d7c…adb89` | 実測一致 |
| `_snapshot_current_commit` は required path を HEAD blob から、契約だけ worktree bytes から取る | 実装で確認 (`test_s8c_preregistration_predicates.py:65-87`) |
| `ReservationBinding` は `job_id` / `boot_id` / `deadline_epoch` を実在 field として持つ | `reservation.py:27-37` |
| `check_reservation` は PBS job・boot・期限残の 3 点を実際に照合する | `reservation.py:237-257` |
| 8c supervisor に `reservation` の grep hit は 0 件 | `p3_autonomous_workload_trial.py` 全体 |
| `docs/decisions.md` に /rulings 各回の裁定を記録した D は**存在しない** | main tip の全文検索で 0 件 |
| main が wave 中に `5a19b8ab` → `7c83eeac` へ進み、/rulings 第 4 回 11 件が着地。本 wave の対象は含まれない | `git show 7a0129dc` |
| 並行 wave [T-1202] は C12 の canonical target を `(reservation.py, single_process_required)` に固定する計画 | `t1202-…/s2-plan.md:149,164,189` |
| 並行 wave [T-1250] は `ruling_reference=D458` で g4 を発行し、`DECIDER_VERSION` を bump しない計画 | `t1250-…/s1-brief.md:5-29` |

## 1. 所見の裁定

### レンズ A

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | `D441` は択 (c) を承認しておらず、g4 の裁定根拠に使うのは誤参照 | **real (部分)** | **緩和して採用** — 下記 §2 |
| A2 | [T-1202] 未着地では allocation helper が production 経路から発火しない。helper 直呼びは発火の証拠にならない | **real** | **採用 (設計変更で解消)** — 下記 §3 |
| A3 | 契約案が実在しない `run_trial.reservation_binding` / `reservation_check` を宣言する。形状のみの検査は dead branch / shadow / fake callback で通せる | **real** | **一部採用** — 下記 §4 |
| A4 | negative control の変異が複数行 block に対する 1 行 exact 置換で、置換数 0 になりうる | **real** | **全面採用** |
| A5 | `"PBS_JOBID"` / `_require_capacity` の綴り固定は安全な refactor で偽陽性、branch を空にしても偽陰性 | **real** | **一部採用** — 下記 §4 |
| A6 | `read_binding` は実際には 8 field 全部を要求し、「PBS job・boot・期限だけ」と一致しない | **real** | **全面採用** (本文で名指しする) |
| A7 | 実 HEAD の `UNSATISFIED` 固定は、正しく配線した瞬間に赤になる | **real** | **採用** (tripwire と明記) |
| A8 | 親 brief の「binding が実 production module に実在しない」は一般化しすぎ | **real** | **採用** (記述を限定する) |

### レンズ B

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B1 | [T-1250] / [T-1202] と g4・版・C12 ledger が排他。順序依存になる | **real** | **採用 (運用で解消)** — 下記 §5 |
| B2 | [T-1202] が旧 symbol を canonical target に固定するため、両者が競合する | **real** | **採用 (運用で解消)** — 下記 §5 |
| B3 | may-reach を実 consumer の代用にしている (data-flow / dominance を見ない) | **real** | **一部採用** — §4 (A3 と同型) |
| B4 | 実 HEAD test と synthetic negative control の closure が cross-module land で揮発する | **real** | **採用** (§5 の再検証で閉じる) |
| B5 | semantic hash を raw byte hash と誤読している。canonicalizer は整形差を吸収する | **real** | **全面採用** (文言を直す) |
| B6 | Pegasus runbook が今も単独性を運用要件として書いており、読者が混同する | **real** | **全面採用** (本文で境界を明記、runbook は no-touch) |

**refuted はゼロ。** 両レンズの所見はすべて実 bytes で裏が取れた。

## 2. 裁定 (1) — `ruling_reference` は `D441` とし、限界を台帳へ明記する

**A1 は real だが、代案が存在しない。**

- `_assert_rulings_exist` は導入 commit 時点の `docs/decisions.md` に `## D<N>.` 見出しを要求する
  (`s8c_preregistration.py:1381-1403`)。
- 3 台帳は直接編集できず、D 番号は land の fold が採番する (`CLAUDE.md`、`DW-S07`)。
  したがって**本 wave の commit に新 D を存在させることは構造的に不可能**である。
- `docs/decisions.md` に /rulings 各回の裁定を記録した D は 1 件も無い (親実測)。
- レンズ A の提案「択 (c) を記録する decision-only wave を先に land し、次の wave で g4 を作る」は
  正しい形だが、**1 wave = 1 fresh context・自己再帰禁止**のため本 wave では実行できない。

**採る形:** `ruling_reference` は `D441` とする。D441 は C12 の構成上充足不能・択一集合 (a)(b)(c)・
消える保証を所有する唯一の決定であり、本改訂はその択 (c) の実装である。実際の承認
(2026-08-16 /rulings 全件 第 3 回、択 (c)) は `revision_reason` に逐語で焼く。
あわせて本 wave は択 (c) を記録する decisions fragment を書き、以後の世代が引ける D を作る。

**台帳へ明記する限界:** g4 の `ruling_reference` が指す D441 は択一集合を記録した決定であって
択 (c) の承認そのものではない。承認の一次資料は `revision_reason` の逐語と worklog である。

## 3. 裁定 (2) — allocation gate を env gate より**前**へ移し、実データで発火させる

**A2 は real。** helper 直呼びテストは production 発火の証拠にならない。しかし [T-1202] を
hard prerequisite にすると、ユーザーが本 wave に課した「縮小後の binding が実際に発火することを
実データで示す」が別 wave の完了に依存する。

**採る形:** `_evaluate_c12` の判定順序を `allocation gate → environment/guard gate` へ入れ替える。

**根拠 (実測済み):**

- D441 決定 (4) は、env gate が返す `environment-contract-consumer-absent` が**誤診断**であることを
  実測で確定している。`lookup` と `attest_and_build_receipt` は cross-module で実際に走っており、
  「不在」ではない。
- D441 決定 (5) は、**実際に欠けているのは allocation 検査だけ**であることを確定している。
- したがって順序入替は、実 tree の C12 が返す理由を**誤診断から実在の欠落へ直す**変更である。
  status は `UNSATISFIED` のまま動かず、**受理集合は 1 bit も変わらない**。
- 並行 wave [T-1202] の予測表も、cross-module 化後の C12 を
  `UNSATISFIED / allocation-enforcement-consumer-absent` と書いている
  (`t1202-…/s2-plan.md:164`)。順序入替は両 wave の終端値を**一致させる**方向であり、対立しない。

**これにより「実データで発火」は production registry 経路で示せる:**
実 HEAD blob に対し `PredicateRegistry.evaluate_all` を通した C12 の理由が
`environment-contract-consumer-absent` から `allocation-enforcement-consumer-absent` へ変わる。
これは捏造被検体ではなく実 repository の bytes が駆動する。

**gap ledger の更新は許可する。** `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
の C12 行だけを新理由へ更新し、理由を worklog へ書く。同テストは「他 wave の land 時は意図を
再審査して更新する」ための台帳であり、これはその手続きに従った更新である。
**他の 11 条件の行と `test_current_repository_snapshot_has_zero_satisfied_predicates` は 1 文字も触らない。**

helper 直呼びの実 blob テスト (プラン (c)) も**併せて残す**。registry 経路が env gate 側の変更で
揺れても、allocation 判定そのものの実データ挙動を独立に pin するため。

## 4. 裁定 (3) — 形状検査の射程を狭く宣言し、恒真化を本文で封じる

A3 / A5 / B3 は real。ただし data-flow・dominance の静的証明は**本 wave の scope 外**である
(裁定 (c) は「実現可能な allocation binding へ縮小する」であって「証明力を上げる」ではない)。

**採る形:**

1. 契約の `field_paths` から**実在しない名前を消す**。`run_trial.reservation_binding` /
   `run_trial.reservation_check` は宣言しない。宣言するのは実在する
   `ReservationBinding.job_id` / `.boot_id` / `.deadline_epoch` / `read_binding` / `check_reservation`。
2. 判定は「top-level 定義の実在」と「`run_trial` からの到達」に限る。
   `"PBS_JOBID"` literal / `_require_capacity` / `boot_id_read_fn` の**綴り固定は採らない**
   (A5 の偽陽性が実害。安全な refactor で赤になる)。代わりに
   `read_binding` / `check_reservation` の実在と到達だけを要求する。
3. `static_only_note` と事前登録本文に、**この検査が may-reach であり、
   同一 binding の data-flow・launch 前 dominance・例外の非握り潰しを証明しないこと**を明記する。
4. 終端は従来どおり `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`。
   **`SATISFIED` を返す経路は 1 本も作らない。**

## 5. 裁定 (4) — 並行 3 wave の順序は「後発が合成する」で解く

B1 / B2 / B4 は real。ただし本 wave で解ける形がある。

1. **段 5 実装は現在の main 取り込み後の木で行う。**
2. **受入投入の直前に再度 main を取り込む。** [T-1202] または [T-1250] が着地していたら、
   Codex `role=author` の合成監査つき merge を行い、次を再導出する。
   - 世代 record: `prepare-revision` を**再実行**して g4 → g5 へ作り直す
     (`supersedes_sha256` は新 tip の raw sha256 になる)。
   - [T-1202] の canonical target `(reservation.py, single_process_required)` を、
     本 wave の縮小後 binding へ**書き換える**。裁定は対 ([T-1167] (c) と [T-1202] (ii)) であり、
     縮小後の binding が canonical target であることが両裁定の整合解である。
   - gap ledger の C12 行は両 wave とも同じ理由へ収束するため、値の競合は起きない。
3. `DECIDER_VERSION` の v1 → v2 bump は **D458 決定 1 が命じる義務**であり過剰変更ではない
   (評価器の拒否理由の意味が変わる)。[T-1250] は bump しない wave なので、
   どちらの順序でも tip 世代が走行中の定数を束縛する形に収束する。

## 6. 変異事前登録 (DW-M01)

実装前に登録する。位置は縮小後の実装に対する逐語 anchor で、段 6 の fix 後に `DW-M07` で再検証する。

| ID | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `_evaluate_c12` の allocation gate | `read_binding` の要求を落とす (要求集合から除去) | KILLED | 前後に同じ入力を拒否する層が無い。env gate は後段へ移り、C12 の allocation 判定はこの 1 箇所だけ |
| M2 | `_evaluate_c12` の allocation gate | `check_reservation` の要求を落とす | KILLED | 同上 |
| M3 | `_evaluate_c12` | allocation gate を env gate の**後ろ**へ戻す (順序を旧に戻す) | KILLED | 実 HEAD の理由が誤診断へ戻るため gap ledger テストが単一理由で赤 |
| M4 | 契約 JSON C12 | `allocation_consumer` の `field_paths` を旧 `single_process_required` へ戻す | KILLED | 契約 hash pin と negative control ID の 2 層で赤になるため**過剰決定**。冗長 gate と明記し、単独変異の証拠から外す (`DW-M03`) |
| M5 | negative control fixture | 変異置換を「一致 0 件でも通る」形へ戻す | KILLED | 置換数 assert が単一理由で赤 |
| M6 (正例) | 実 HEAD helper テスト | production に `read_binding` / `check_reservation` の呼出しを**追加**した木 | 期待: allocation gate を通過し、承認外の過剰拒否をしない | 受理集合を縮小する wave の正例 (`DW-M01`) |

M4 は `DW-M03` に従い冗長 gate として登録するが、単独 kill の証拠には数えない。

## 7. scope 外として裁定パッケージへ回すもの

- **data-flow / dominance を証明する C12 判定への強化** (A3 / B3 の全面版)。
  裁定 (c) の射程外であり、`SATISFIED` 経路が無い現状では受理集合を変えない。
  成果物影響: 実装しなければ、8c launcher が形だけ両関数を呼び実質の拒否をしない木でも
  C12 の理由が `EVIDENCE_UNDEFINED` へ進む。受理集合は変わらない (`SATISFIED` にならない)。
- **`check_reservation` が `host` / `script_sha256` / `nonce` を照合しないこと** (D441 決定 8 が
  別タスク所有と明記済み)。本 wave は境界を開かない。
- **Pegasus runbook の運用要件そのものの改訂** (B6)。本 wave は本文で境界を書くだけとし、
  runbook は no-touch とする。

## 8. プラン v2 (実装単位)

単一 Codex `role=author` 単位とする。編集ファイル所有が素集合に割れないため (契約 JSON と
判定器と test が相互拘束する)、分割しない。

編集面:

1. `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` — C12 の縮小。
2. `orchestrator/campaign/s8c_preregistration_evidence.py` — allocation gate の helper 化と順序入替。
3. `orchestrator/campaign/s8c_preregistration.py` — `DECIDER_VERSION` を `s8c-decider/v2` へ。
4. `orchestrator/tests/test_s8c_preregistration_predicates.py` — 実 HEAD 発火テスト新設、
   negative control 差し替え、gap ledger の C12 行更新。
5. `orchestrator/tests/test_s8c_preregistration_core.py` — 版 bump に伴う literal 更新 5 件。

親が編集する docs (実装子は触らない):

6. `docs/phase3-8c-preregistration.md` — §6 条件 12 の縮小と、衝突 (e) の注記。
7. `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json` — `prepare-revision` で生成。
8. spool fragment (worklog / decisions)。
