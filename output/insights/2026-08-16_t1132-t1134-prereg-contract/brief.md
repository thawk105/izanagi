# 段 1 brief — [T-1132] [T-1133] [T-1134] 8c 事前登録の証拠契約

wave: `dev-wave-t1132-t1134-prereg-contract` / branch `worktree-dev-wave-t1132-t1134-prereg-contract`
base main: `10813338` / 開始 2026-08-16 07:49 JST

## 1. scope

8c 事前登録 (`docs/phase3-8c-preregistration.md`) の発効経路を塞いでいる構造衝突 (a)(b)(c) を、
D96 手続に従って解く。(d) arm 未束縛は scope 外 (別条件・別実装量)。

編集面 (実装面は Codex author、docs 本文は親):

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` — 凍結範囲内
- `docs/phase3-8c-preregistration.md` §6 条件 3/8/11、衝突 (a)(b)(c) の記述 — 凍結範囲内
- `orchestrator/campaign/s8c_preregistration_evidence.py` — 凍結範囲**外**
- `orchestrator/campaign/s8c_preregistration.py` — 凍結範囲外 ((P1) の帰結次第)
- `orchestrator/tests/test_s8c_preregistration_predicates.py` — D96 (2) の境界テスト
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json` — 新規

## 2. 確定済みユーザー裁定 (2026-08-16 一括裁定 #1〜#4、逐語「推奨通りで」)

1. [T-1132] 証拠契約を D96 手続で改訂する (発効経路の最手前の閂)
2. [T-1133] 択 (a) 既存 4 機構を条件 11 の証拠とする契約へ改訂する
3. [T-1134] 択 (a) 内容 commit と発効 commit を分ける二段束縛にする
4. [T-324] 同一 wave で land — 文書は既に main へ着地済みなので land 対象外

## 3. 起動時に実測した事実 (裁定当時に未見。段 4 で再裁定の材料)

すべて worktree HEAD = main `10813338` に対する実測。

- **M1.** 契約は 12 条件すべて `machine_checkable: false`。評価器は 6 本 (C01/C04/C09/C10/C11/C12)
  実装済みで、`PredicateRegistry.evaluate_all` は false のとき `_evaluate_undefined` へ落とすため
  1 本も呼ばれない。= 衝突 (a) の機構。
- **M2.** 6 本を強制的に発火させた実測結果は**全件 `UNSATISFIED`** (終端の
  `EVIDENCE_UNDEFINED` には 1 本も到達しない):
  C01 `workload-projection-mismatch` / C04 `crash-policy-cell-partial` /
  C09 `formal-acceptance-layer3-consumer-absent` / C10 `cross-binding-verifier-incomplete` /
  C11 `sample-plan-absent` / C12 `environment-contract-consumer-absent`。
  → `machine_checkable` を反転しても**受理集合は 1 bit も広がらない** (充足 0 のまま、
  診断が uniform な「機械検査対象外」から条件別の具体理由へ変わるだけ)。
- **M3.** ただし 6 本とも**すべての検査を通過した先の終端が
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`** であり、
  `SATISFIABLE_CONDITION_IDS` は空集合。つまり閂は二層。
- **M4.** 条件 11 の「既存 4 機構」は実在する: `MAX_APPROVED_GENERATIONS = 2`、
  `_validate_generation_budget` が main/run_trial/_run_workload の 3 入口すべてで呼ばれる、
  `apply_critic_feedback` が `_run_workload` で呼ばれる、negative control
  `nc_c11_generation_cap_reverts_to_one` が登録済み。**作らないと裁定済みの 2 件**は
  `output/s8c-preregistration/sample-plan.v1.json` と
  `output/s8c-preregistration/generation-cap-lift.v1.json`。
  この 2 件を証拠から外すと、C11 は残る検査を全通過して**終端へ到達する** (実測)。
  → M3 を解かない限り T-1133 の改訂は C11 を `UNSATISFIED` から `EVIDENCE_UNDEFINED` へ
  移すだけで、充足には近づかない。
- **M5 (裁定前提を覆しうる最大の事実).** D96 手続が要求する世代記録
  `condition-freeze.v1.g3.json` は `ruling_reference` に `docs/decisions.md` の `## D<N>.` 見出しを
  要求し、`_assert_rulings_exist` はその存在を**記録を導入した commit の時点で**検査する。
  D 番号は land の fold が採番するため、wave 側 commit には存在しない。
  前例 g2 は D410 を引き、D410 は g2 の導入 commit `d0fc008c` (08-15 23:32) の
  **12 時間前**に別 land (`94ce4ccf`, 08-15 11:12) で着地していた = 「先に着地した D を引く」形。
  受入テスト `test_s8c_preregistration_invariant.py` は作業ツリーから候補 commit を合成して
  実検査するので、この不整合は**受入で赤になる**。
- **M6.** 境界テスト (D96 (2) が同一変更単位での更新を義務づける対象) は
  `orchestrator/tests/test_s8c_preregistration_predicates.py:506`
  `assert machine_checkable == M.SATISFIABLE_CONDITION_IDS == frozenset()`。
  同 file には 6 条件分の `NEGATIVE_CONTROL_CASES` が既に登録済み。
- **M7 (pin 閉包, DW-O09).** 生きた pin: `s8c_preregistration.py` / 上記 3 test file /
  `tools/check_docs.py:64` (prereg doc は「発効前は living」扱いで exact pin なし) /
  freeze 記録 g1・g2 / `docs/README.md` / `docs/phase3-s8c-autonomous-trial-runbook.md` /
  `output/README.md` / `docs/decisions.md`。`output/insights/**` と `docs/archive/**` は歴史記録。

## 4. 親の provisional 裁定 (すべて攻撃対象)

- **(P1) M5 の解き方。** 親の provisional は **g3 の `ruling_reference` に D96 を引く**
  (D96 は受理集合を変える改修を統べる決定そのもので、本改訂はその手続に従う)。
  `revision_reason` に 2026-08-16 のユーザー裁定と T-1132/1133/1134 を明記し、
  D96 (1) が要求する新 D は spool fragment で別途起こす。
  対案 (P1b): `_assert_rulings_exist` の受理形を「同 commit の tree に実在する decisions spool
  fragment」まで広げる (= freeze 検証器の受理集合変更。別 D と境界テストが要る)。
  対案 (P1c): 本 wave では凍結範囲を触らず D だけ land し、改訂は次 wave (成果ほぼゼロ)。
- **(P2) M3 の終端を SATISFIED へ変えるか。** 親の provisional は **変える** — ただし
  「評価器の検査が当該条件の `required_evidence` と `consumer_requirement` を完全に discharge
  している」条件だけ。M2 より、本 wave で実際に受理側へ動くのは **C11 のみ**
  (他 5 本は依然 UNSATISFIED)。これは裁定 #2 (a) が明示的に認めた変更である。
  **本 wave の制約上、最も攻撃されるべき前提。** 変えない選択 (P2b) も成立し、
  その場合 T-1133 は診断の変化だけを生む。
- **(P3) T-1134 の二段束縛の形。** 親の provisional は、条件 3/8 の `prereg_commit` を
  `prereg_content_commit` (manifest の bytes を含む内容 commit) と
  `prereg_effective_commit` (発効 commit) の 2 つへ分け、
  「祖先代用の禁止」を「発効 commit の親が内容 commit であること」の要求として維持する。
- **(P4) 変更単位の分割。** 契約 JSON + doc §6 + 評価器 + 境界テスト + g3 は
  1 つの commit にまとめる (freeze の履歴遷移検査が中間状態を赤にするため)。

## 5. 不変条件 (破ったら停止)

- 受理集合を**広げる方向の緩和**は規律 2 違反として採らない。契約を実態へ合わせるのは、
  到達不能な評価器を到達可能にする方向だけ。未定義・エラーを充足側へ倒さない (fail-closed 維持)。
- 12 条件・`PREDICATE_IDS`・reason_code の値域は閉じたまま保つ。自由文を reason_code にしない。
- 評価器は指定 commit の git blob だけを読む。worktree の module / artifact を import・open しない。
- 8b が凍結する事項には触れない (触るなら 8b §8 の再凍結 + ユーザー承認が別途要る)。
- 衝突 (d) arm 未束縛は解かない。解けたと書かない。

## 6. 成果物影響 (DW-G05)

- (a) 未解決なら: certified 選択・材料レポート・試行台帳のいずれも 8c 本走から生まれない
  (事前登録が永久に未発効 → 本走が始まらない)。
- (b) 未解決なら: 条件 11 が構造的に永久未充足となり、(a) を解いても発効しない。
- (c) 未解決なら: 条件 3/8 が構成不能で、(a)(b) を解いても発効しない。
- 本 wave の受理集合の実変化: **C11 が「決して充足しない」から「4 機構が揃えば充足しうる」へ**
  ((P2) を採る場合)。他 11 条件の受理集合は不変。

## 7. 成果物の形

契約 JSON の改訂 / doc §6 条件 3・8・11 と衝突節の改訂 / 評価器の到達可能化 /
境界テストの追随 / g3 世代記録 / 変異事前登録 (受理集合を変えるため必須) /
worklog・decisions の spool fragment。

## 8. 並列分割方針

段 5 は 2 単位: (A) 契約 JSON + 評価器 + 境界テスト、(B) g3 生成と freeze 検査経路。
docs 本文は親。段 6 は敵対レビュー 2 本 (規律 2 の受理集合レンズ / freeze 履歴と D96 手続レンズ)。

## 9. 受入・実測環境

Pegasus login node、repo root = 本 worktree。受入は `tools/run_tests.py` の受入形を
受入 lease (`tools/dev_wave_wait.py acceptance`) 取得後に背景投入する。
変異は事前登録変異 (受理集合を変えるため免除されない)。
