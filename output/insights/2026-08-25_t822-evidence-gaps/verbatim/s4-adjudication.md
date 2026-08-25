# [T-822] 段 4 裁定

## 0. 親の段 0 前提 (P3) は反証された

段 1 brief で親は「D863 の 3 件は既に実装済み」と書いた。段 3 レンズ A がこれを
原典で反証し、親が逐語で裏取りした。**裁定 D863 は覆らない。3 件は実質的に開いている。**

親の誤りは「呼び出しが存在すること」を「保証が発火すること」と同一視した点である。
これは `docs/failures.md` が繰り返し記録してきた「謳うだけで発火しない保証」の型そのもので、
親自身がその型を踏んだ。段 3 を省いていれば、既に閉じた 3 件として台帳へ書き、
正式系列の起動条件を誤って解除していた。

## 1. 所見の裁定

### レンズ A

| # | 主張 | 裁定 | 根拠 |
|---|---|---|---|
| 1 | 層 3 鎖は必須経路でない | **real・採用** | trial_registry.py:5736-5738 で do_build=False は関数を呼ばず、5750-5753 で campaignless failure cell は `continue` する。test_trial_registry.py:1799-1820 がこの受入成功を逐語で固定している (親が確認)。 |
| 2 | layer3-chain-absent は certifying を駆動しない | **real・採用** | s8c_acceptance_receipt.py:393-396 が `certifying is not False` を無条件拒否。理由コードは因果ではない。 |
| 3 | 宣言 arm から実 CCBench source までの因果鎖が切れている | **real・採用・scope 外** | proposal bytes は hash されるだけで WAL source・trigger binding と比較されない。閉じるには producer / completeness 側が要る。 |
| 4 | measurement_head 一致は計測対象の一致でない | **real・採用・本 wave の実装対象** | 親が独立確認。trial_registry.py の受入は measurement_env を一切参照せず、ratified 世代も参照しない (grep 0 件)。 |
| 5 | loop_state.iteration は独立な世代数証拠でない | **real・採用 (最重要)** | p3_s4_loop.py:632-634 が逐語で「checkpoint は WAL でなく loop 状態の投影 — 正本は WAL」、同 :703-704 が「iteration 整合・entry 件数・campaign/run origin は本関数では検査しない」。段 2 plan の芯はここに乗っており、**採用しない**。 |
| 6 | P2 は弱い自己整合検査についてだけ成立 | **real・採用** | 5 の帰結。真の修正は禁止編集面を含む。 |
| 7 | 弱い述語を強い証明として扱うのは規律 2 違反 | **real・採用** | 段 2 plan をそのまま実装して「T-1211 を閉じた」と記録することを禁じる。 |

### レンズ B

| # | 主張 | 裁定 |
|---|---|---|
| 1 | 空の母集合でも受入が完了する | **real・採用**。本 wave の gate は母数下限を明示検査する。 |
| 2 | 迂回経路が 3 系統ある | **real・採用**。ただし迂回を hard failure へ倒すかは設計択一 (下記 §3)。 |
| 3 | standalone verifier で再発火しない | **real・scope 外**。受領証の耐久性は D863 が名指ししていない別面。 |
| 4 | skip 分岐は禁止 | **real・採用**。本 wave の gate に skip 分岐を置かない。 |
| 5 | 入力は到達可能だが fixture 未整合 | **部分 real**。到達可能性はレンズ B が正しく、独立性はレンズ A が正しい。両者は矛盾しない — 値は取れるが証拠にならない。 |
| 6 | 空実装検出の負例が足りない | **real・採用**。 |
| 7 | 禁止編集面は要求していない | **refuted の指摘として採用**。本 wave も 0 byte を守る。 |

## 2. 本 wave の実装 scope (プラン v2)

**段 2 plan の芯 (loop_state.iteration による世代数照合) は採用しない。**
代わりに、D863 の第 3 条件を実質的に閉じる。

### 実装するもの — 正式受入における計測対象の同一性

正式受入 `assert_trial_registry_acceptance` は現在、6 report が同じ
`measurement_head` (izanagi 側の git commit) を持つことだけを要求する。
**何を計測したかは一切照合していない。** 6 セルが別々の CCBench source を、
別々の環境で計測していても受理される。arm 間比較 (on/off/swapped) の差を
機構へ帰属させる成果物にとって、これは中核の穴である。

閉じ方: 各 trial の materialized campaign が持つ層 3 レポートを受入自身が再読し、
6 report 横断で次を要求する。

1. `meta.ccbench_commit` が 6 件すべてで同一。
2. `env_tags` が各 report でちょうど 1 件、かつ 6 件すべてで同一。
3. **母数下限:** 完全 build 束 (no-build も campaignless failure も無い束) では、
   層 3 レポートがちょうど 6 件存在すること。0 件・欠落は hard failure とする。
   これがレンズ B 所見 1 への手当てであり、空集合で緑になる恒真化を塞ぐ。

入力の実在 (DW-O13): 実成果物で実測済み。
`output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/layer3_report.json`
は `env_tags = ["linux-baremetal"]`、`meta.ccbench_commit = "d706650"` を持つ。
両 field は `layer3_schema.json` の required に入っており、欠落しない。

編集面: `orchestrator/campaign/trial_registry.py` と
`orchestrator/tests/test_trial_registry.py` のみ。
`orchestrator/campaign/autonomous_trial_completeness.py` は **0 byte**。

### 実装しないもの

- 段 2 plan の loop_state.iteration 照合 (レンズ A 所見 5)。
- D863 第 1 条件の完全な閉塞 (迂回の hard failure 化) — §3 の設計択一。
- D863 第 2 条件 (arm から実 source への因果束縛) — 禁止編集面を含む。
- [T-1211] — 自身の記述が「外部 immutable anchor が要る」と述べており、
  本 wave の範囲では閉じられない。**open のまま残す。**

## 3. ユーザーへ返す設計択一

**正式受入は、no-build または層 3 不在の trial を含む 6 report 束を拒否すべきか。**

- 現状: 受理し、理由コードを付けた非 certifying 受領証を発行する。
  test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason が固定している。
- 択 (a): 正式受入は拒否し、診断用の受領証は別 API・別成果物へ分離する。
  D863 第 1 条件を実質的に閉じるが、失敗した正式試行を台帳へ残す経路を作り直す必要がある。
- 択 (b): 現状維持。理由コードで不完全性を記録する。
  ただし「no-build を certify しない」という契約上の保証は、
  certifying が構造上つねに False である以上、恒真である。

親の推奨は **(a)**。理由: 正式系列の成果物は 6 セル全部の計測を要求するので、
1 セルでも計測が無い束は正式主張を支えられない。受領証が「受理」と言いながら
中身が空である状態は、規律 2 が禁じる恒真な保証の典型である。
ただし失敗試行の記録経路を同時に設計する必要があるため、ユーザー裁定を求める。

## 4. 正式系列 ([T-1135]) の実残 blocker

D863 の 3 件とは別に、次が閉じていない (親が判定器で実測)。

- C03 `manifest-registry-proof-undefined` (UNSATISFIED)
- C05 `schedule-schema-absent` — `output/s8c-preregistration/schedule.v1.json` が不在
- C08 `prereg-binding-proof-undefined`
- T-468 承認権限の不在 — 受領証は構造上つねに非 certifying

## 5. 変異事前登録 (DW-M01)

実装後に登録する変異は次の 3 件。いずれも本 wave が新設する述語だけを単一理由で赤にする。

1. `meta.ccbench_commit` の 6 件一致検査を無効化 → 新設テストの
   ccbench 不一致負例だけが赤。前後に同じ入力を拒否する層は無い (親が grep で確認済み、
   trial_registry.py に `ccbench` の出現 0 件)。
2. `env_tags` の一致検査を無効化 → env 不一致負例だけが赤。
3. 母数下限 (層 3 レポート 6 件) の検査を無効化 → 空母集合負例だけが赤。

受理集合を縮小する wave のため、**承認外の過剰拒否を検出する正例**も登録する。

4. 正しい 6 report 束 (同一 ccbench_commit・同一 env_tag) が従来どおり
   受領証発行まで到達する正例。これが赤くなる変異は過剰拒否である。
