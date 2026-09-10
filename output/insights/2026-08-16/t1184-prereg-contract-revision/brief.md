# 段 1 brief + 段 4 裁定 (plan v2) — [T-1184] 8c 事前登録 証拠契約の改訂

親 / 2026-08-16 14:2x JST / worktree `dev-wave-t1184-prereg-contract-revision` / base main `2f7eeb22`

## 0. この wave の位置づけ

前 wave (worklog entry 580) が段 1〜4 を実施し、**改訂の実装形を D438 として land した**。
D439 が「決定を先に land する wave」と「世代記録・契約改訂・境界テストを同一 commit で land する
wave」の分割規律を定めた。本 wave は D439 形 1 の後半である。D438 が main に実在するため、
第 3 世代の凍結記録は `ruling_reference = "D438"` を引ける。

読み込み契約の「裁定後に別 context が段 4 から再開する型は、変更面の骨格が同一なら前 wave の
段 2・3 成果物を流用でき、再検査は段 6 レビューへ寄せる」に該当する。段 2 プラン・段 3 レンズ 2 本・
段 4 裁定書は `output/insights/2026-08-16_t1132-t1134-prereg-contract/` にある。

## 1. scope

**scope 内 (同一 commit に入れる):**

1. `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` — D438 決定 (1)(2)(4)
2. `orchestrator/campaign/s8c_preregistration_evidence.py` — `_evaluate_c11` の証拠差し替え
3. `docs/phase3-8c-preregistration.md` — 規範本文の追随 (親が書く)
4. `docs/phase3-s8c-autonomous-trial-runbook.md` — 旧識別子 `prereg_commit` の追随 (親が書く)
5. `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json` — 親が CLI で生成
6. 3 つの s8c テストファイル — 既存期待値の追随 + D96 条項 2 の境界テスト

**scope 外 (触らない):**

- [T-1186] 凍結範囲へ評価器・判定器の bytes を含めるか — **ユーザー裁定待ち。触らない**
- [T-1187] 条件 3 / 8 二段束縛の consumer 配線 (`trial_registry.py` ほか) — 本 wave に含めない
- [T-1185] exact `G=2` を要求する受入 consumer の新設
- 衝突 (d) arm 未束縛
- `docs/phase3-8c-wiring-design.md:402` の `TrialBinding` 記述 — 現行実装 (`trial_registry.py`) の
  説明であり、実装を変えない以上、変えると記述が実装から乖離する。**据え置く**

## 2. 確定済みユーザー裁定 (2026-08-16 /rulings 全件 #1〜#3、authority = ユーザー)

控え: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full-43rulings.md`
実装形の正本: **D438 決定 (1)〜(4)**。以下は逐語ではなく本 wave が実装する形。

- **決定 (1)** 評価器を持つ 6 条件 (C01・C04・C09・C10・C11・C12) だけ `machine_checkable` を
  `true` へ反転する。**6 評価器の終端 `EVIDENCE_UNDEFINED /
  completion-proof-not-machine-checkable` と、空集合の `SATISFIABLE_CONDITION_IDS` は維持する。**
  実利は受理側ではなく、恒真だった負の対照 6 件が発火することにある。
- **決定 (2)** 条件 11 の証拠を、廃止確定の 2 方針成果物から
  `orchestrator/campaign/s8c_generation_projection.py` の閉じた第二層射影へ差し替える。
  C11 は `UNSATISFIED / sample-plan-absent` から `EVIDENCE_UNDEFINED /
  completion-proof-not-machine-checkable` へ移る (どちらも非充足、受理集合は広がらない)。
- **決定 (3)** 世代下限の強制は条件 11 の機構に求めず、起動形の責務のまま残す。
  → **`_evaluate_c11` の `cap < 2` 判定を exact `2` へ狭めない。** 段 2 プランの「exact 2」提案は
  SATISFIED 経路とセットの案であり、段 4 で不採用になった側に属する。
- **決定 (4)** 条件 3 / 8 は、内容 commit `P` と発効 commit `C` を分ける二段束縛へ改める。
  manifest は `P` の識別子も自身の digest も持たない。`C` は `P` の直子で binding record だけを
  導入し、`C` 自身の識別子は持たない。祖先代用の禁止は `is-ancestor` ではなく
  **「`C` の親集合が exact `{P}`」**で維持する。`prereg_commit` を互換 alias として残さない。
  **契約と規範本文の形だけを直し、C03 / C08 は `machine_checkable: false` のまま残す**
  (実装したふりをしない)。

## 3. 不変条件 (破ったら停止)

- **I1** 受理集合を 1 bit も広げない。`SATISFIABLE_CONDITION_IDS` は `frozenset()` のまま。
  6 評価器の成功終端は追加しない。`SATISFIED` を返す経路を新設しない (規律 2)。
- **I2** 反転するのは評価器が実在する 6 条件だけ。C02・C03・C05・C06・C07・C08 は `false` のまま。
- **I3** g1 / g2 の凍結記録の bytes を 1 byte も変えない。歴史 pin
  (`test_existing_g1_record_pins_are_unchanged`) も変えない。
- **I4** g3 は doc と契約 JSON の最終 bytes が確定した後に CLI で生成する。hash を手入力しない。
- **I5** 凍結範囲 (規範本文・§5 欄名・発効ブロック・契約 JSON の意味内容) の変更と g3 は
  同一 commit に置く。分割すると `record-protected-mismatch` / `spurious-revision` で赤になる。
- **I6** §5 の**値**セルは触らない (凍結対象外だが本 wave の scope 外)。§5 の**欄名**は変えない
  (変えると `section5_field_names_sha256` が動き、意図しない凍結差分になる)。
- **I7** doc に `output/…json` 形の path を新規に書かない。`check_docs.py` の PATH_REF が
  実在検査を行い、未作成の binding record path を書くと赤になる。ディレクトリ名か
  拡張子付き basename 単独で書く。
- **I8** doc の D 参照は decisions.md に実在するものだけ。D438 / D439 は実在する。

## 4. 親が段 1 で実測した事実 (一次資料は下記コマンドの出力)

| ID | 実測 | 値 |
|---|---|---|
| M1 | 契約 JSON の 12 条件の `machine_checkable` | **全件 `false`** |
| M2 | 現 HEAD で 6 評価器を直接呼んだ結果 | C01 `UNSATISFIED/workload-projection-mismatch`、C04 `UNSATISFIED/crash-policy-cell-partial`、C09 `UNSATISFIED/formal-acceptance-layer3-consumer-absent`、C10 `UNSATISFIED/cross-binding-verifier-incomplete`、C11 `UNSATISFIED/sample-plan-absent`、C12 `UNSATISFIED/environment-contract-consumer-absent` |
| M3 | C11 の sub-check | `MAX_APPROVED_GENERATIONS = 2`、3 入口とも `_validate_generation_budget` を call、`_run_workload` は `apply_critic_feedback` を call、`sample_plan_sha256`/`cap_lift_sha256` 文字列は**不在** |
| M4 | → sample/cap 検査を外すと C11 は終端 `EVIDENCE_UNDEFINED` へ到達する | D438 決定 (2) と一致 |
| M5 | `check_docs.py` の baseline | rc=0 (違反なし) |
| M6 | 契約 hash の live pin | `orchestrator/tests/test_s8c_preregistration_core.py` の 2 箇所のみ (`test_current_evidence_contract_hash_is_frozen` = 現行値、`test_existing_g1_record_pins_are_unchanged` = g1 歴史値で不変) |
| M7 | 旧識別子 `prereg_commit` の docs 側出現 | `docs/phase3-s8c-autonomous-trial-runbook.md` 1 箇所、`docs/phase3-8c-wiring-design.md` 1 箇所 (後者は現行実装の説明なので据え置く) |
| M8 | `docs/phase3-8c-preregistration.md` は `check_docs.py` の LIVING_DOCS、runbook は glob で自動編入 | I7 / I8 の根拠 |

**M2 は snapshot である** — 「現 HEAD の 1 点でこの vector を得た」以上の一般化をしない。

## 5. 前 wave の 13 nodeid 一覧を一次資料として使わない理由 (親の裁定)

command 引数は「段 2 と段 3 が独立に列挙して 13 件で一致」した一覧を一次資料に使えと指示する。
しかし段 2 プラン §5 の 13 件は、**段 4 が不採用にした「C11 を SATISFIED にする」案の前提**で
数えられている (同 §5 の 3・4・5・10・12・13 番が `SATISFIABLE_CONDITION_IDS = {"C11"}` と
`generation-policy-satisfied` を前提にしている)。D438 決定 (1) は終端を動かさないと定めたので、
母集合はこの前提と異なる。

**裁定: 13 件一覧は着手時の予測として使い、確定は実測で行う。** 具体的には
`test_s8c_preregistration_invariant.py` の zero-satisfied テストは D438 形では赤にならない
(SATISFIED が 0 件のまま) 一方、13 件一覧はこれを赤としている。実測で採り直す
(F1: 件数は成果物 field から取り、既存 docs は一次資料と一致するまで根拠にしない)。

### 親の予測 (段 6 で実測して確定する)

| # | nodeid | 赤になる理由 |
|---|---|---|
| 1 | `test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | C01/C04/C09/C10/C12 が `UNSATISFIED` + 個別理由へ移る。C11 行は変わらない |
| 2 | `…::test_satisfiable_predicate_requires_negative_control` | `machine_checkable == SATISFIABLE_CONDITION_IDS == frozenset()` の三者等値が崩れる |
| 3〜8 | `…::test_noop_and_token_only_fixtures_never_satisfy[nc_c01…-C01]` ほか 6 param | mutation 側が個別 `UNSATISFIED` を返すようになる (= 対照が初めて発火する)。C11 は fixture 自体も差し替えが要る |
| 9 | `…::test_c11_prohibition_ruling_blob_alone_is_not_compliance` | cap=1 で `UNSATISFIED / generation-cap-not-lifted` |
| 10 | `test_s8c_preregistration_core.py::test_contract_path_inventory_has_expected_count` | path 数 38 → 変化 |
| 11 | `…::test_current_evidence_contract_hash_is_frozen` | 契約 JSON の semantic hash が変わる |
| — | `test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates` | **赤にならない見込み** (SATISFIED は 0 件のまま)。実測で確認する |
| — | `…::test_candidate_freeze_matches_contract_and_generation_chain` | g3 が worktree と整合しなければ赤。g3 生成前は意図的に赤 |

## 6. 成果物影響 (DW-G05)

- 本改訂を行わない場合: 証拠契約が 12 条件すべてを機械検査対象外と記す限り、実装済みの評価器は
  1 本も呼ばれず、8c 本走の事前登録は永久に発効しない。正式系列は開始できず、certified 選択・
  材料レポート・試行台帳のいずれも 8c 由来の値を持てない。
- 本改訂を行った場合: certified 選択・材料レポート・試行台帳のどの値も変わらない
  (受理集合は不変)。変わるのは、恒真だった負の対照 6 件が実際の拒否能力を持つようになる点である。
  これが無いと「負例あり」という契約表示が台帳・材料レポートの信頼根拠にならない。

## 7. 変異事前登録 (DW-M01)

段 4 裁定書 §10 が後続 wave 向けに登録した 6 件を採る。単一理由性を実装後に確認し、
確認できないものは登録せず実効 gate へ再照準する。

| # | 変異 | 期待 | 単一理由性の注意 |
|---|---|---|---|
| V1 | C01 の `machine_checkable` を `false` へ戻す | 対照 `nc_c01…` の mutation 側が `completion-proof-not-machine-checkable` へ戻り赤 | gap snapshot テストも同時に赤になる。**先取りされる後段検査を数える** |
| V2 | 評価器のない C02 を `true` にする | `ERROR` (現行は `commit-blob-read-error` に潰れる) | 潰れ先が変わらないなら診断 pin として別枠 |
| V3 | 6 評価器のどれかの終端を `SATISFIED` へ変える | token-only fixture が充足し、対照テストが赤 | 受理集合を広げる方向の検出 |
| V4 | `_evaluate_c11` の射影 blob 検査を外す | 射影不在 fixture が終端へ到達して赤 | C11 の新規検査の実効性 |
| V5 | **正例**: 現 HEAD の実コードが反転後も M2 の status vector を返す | KILL されない (過剰拒否なし) | 承認外の過剰拒否の検出 |
| V6 | **wave 前の実コードの形**: 反転前の全件 `false` を撃つ | 対照 6 件が恒真に戻り赤 | 禁止したい形を wave 前の実コードが使っていた (memory: mutation-must-include-pre-wave-form) |

## 8. 分割と所有

| 単位 | 所有 path | 担当 |
|---|---|---|
| A (実装面) | `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`、`orchestrator/campaign/s8c_preregistration_evidence.py`、`orchestrator/tests/test_s8c_preregistration_core.py`、`orchestrator/tests/test_s8c_preregistration_predicates.py`、`orchestrator/tests/test_s8c_preregistration_invariant.py` | Codex `role=author` (D95) |
| B (docs) | `docs/phase3-8c-preregistration.md`、`docs/phase3-s8c-autonomous-trial-runbook.md` | 親 |
| C (凍結記録) | `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json` | 親 (CLI 生成、A と B の bytes 確定後) |

A と B は同一 commit に入るが編集 path が素集合なので並行してよい。C は A・B の後。

## 9. 受入・実測の環境

- テスト: `tools/run_tests.py` の bounded local (`--force-dispatch` なし)。所在は worklog。
- 受入全走: 受入 lease を `tools/dev_wave_wait.py acceptance` で claim してから投入する。
- `check_docs.py` は毎回 rc をパイプに通さず単独で走らせる。
