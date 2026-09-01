# 段 1 brief — [T-1777] A-1 pilot の事前登録本文を人間の発効直前まで用意する

- wave = `worktree-dev-wave-t1777-pilot-prereg`、基準 commit `c6a94ec998bba8c20c302105f28af3850f8134a6` (着手直前の local main)
- worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg`

## 1. 実測した関門 (依頼の前提の裏取り)

`load_policy("paper-story-a1-20260901-balanced5-pilot-v1")` は通り、policy bytes の SHA-256 は
`405e26b976fc421203cda0d29f74b762f53e7a982bcd536dc8da4a42a5c079c4`。`preregistration` は
`{"path": None, "sha256": None}`。`_require_policy_ready_for_execution` は
`PaperStoryError("v3 policy preregistration binding is not frozen by the parent")` を投げた。
依頼が置いた関門は着手時点で成立している。

## 2. scope

- **成果物 A (本題):** `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`
  — pilot の事前登録本文。機械可読の正本 `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json` の
  人間可読の対。
- **成果物 B:** 本 wave の insight
  `output/insights/2026-09-01_t1777-pilot-preregistration/README.md` に「発効手順」節を置き、
  人間が 1 commit で行う編集箇所と、成果物 A の SHA-256 を書く。
- **scope 外 (実装しない):** 発効そのもの (module pins・policy JSON・`V3_PILOT_POLICY_SHA256`・
  未凍結正例テストの書き換え)、pilot の投入と計測、sized study の policy と事前登録、
  gate・検査・台帳・一般化の新設。

## 3. 確定済みユーザー裁定

- **D1295** — 配置 (5-rep ブロック交互 + AB/BA 均衡)。項目 5 =「推定対象は『5-rep 均衡スケジュール
  下での差』とし、残留効果の無い定常状態の直接効果と同一視しない。この限定を事前登録の本文に書く」。
- **D1296** — 反復数は同じ機構で走らせた pilot から取り直す。60 対/workload (5 対/ブロック × 12
  ブロック、A 先行 6・B 先行 6、組内順は凍結 seed)。対 SD にカイ二乗上側係数を掛けた計画 sigma と、
  ブロック平均から作る実効 sigma の**大きい方**で反復数を探索。判定式・floor・3 条件と成功率は既存の
  sizing 手順に揃える。**pilot の観測値は最終推定へ混ぜない。**
- **D1383 / D1391** — 工程分割。AI は準備と算出まで、発効 (record の発行と pointer の commit) は人間。
  AI は既成事実として値を埋めない。
- **D95** — 実装面は Codex `role=author` 必須。本 wave の編集面は Markdown だけで、決定 2 の
  実装面 (`orchestrator/` 等配下の非 Markdown、場所を問わない Python/shell/C++) に **1 byte も触れない**
  ため docs-only であり、実装子は起こさない。実装面に触る必要が判明した時点で段 1 へ巻き戻す。

## 4. 不変条件

1. **規律 2 を緩めない。** 事前登録本文は `invalid_rules`・`rerun.allowed_reasons`・CV 規則・
   `authority` を弱める文言を持たない。逃がし道・裁量・「必要なら」を書かない。
2. **数値と規則は policy からの射影に限る。** 本文で新しい定数を発明しない。policy に無い値
   (計画 sigma の実値・採用 n) は pilot 未走のため**存在しない**ので、欄を作らず「pilot 後に決まる」と書く。
3. **本文に policy の hash を書かない** (自己参照の禁止、F36)。逆向き (policy → 本文の hash) が正。
4. `orchestrator/` 配下を 1 byte も変えない。発効を既成事実化しない。
5. 追加のみ。既存の凍結 artifact の bytes を変えない。
6. 三軸語・placeholder の機械走査 (`tools/check_docs.py`) に通す。

## 5. (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-1)** 置き場は `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md`。
  v2 の先例 (`output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md`) と同型で、
  計測先 `output/insights/2026-09-01_paper-story-a1-balanced5-pilot` と接頭辞を共有する形も先例と同じ。
- **(P1-2)** 本文は本 wave で local main へ着地させ、その bytes の SHA-256 を算出して報告する。
  人間が 1 byte でも直せば hash は変わるため、発効手順には**採用する bytes に対して再計算する
  1 コマンド**を必ず添え、算出値は「本 wave が着地させた bytes に対する値」と限定して書く。
- **(P1-3)** 判定式 (`resolved-above-floor` / `bounded-below-floor` / `unresolved`) は
  **反復数探索の動作特性を評価するための式**として書き、pilot 自身の結果に分類を出さない
  (`final_estimate_eligible: false`、`authority.result_authority: "pilot-sizing-input-only"`)。
- **(P1-4)** D1295 項目 5 の限定は独立した節に置き、policy の `pairing.estimand` の英文逐語と
  日本語の限定文を併記する。
- **(P1-5)** docs-only につき変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 6. 発効閉包 (人間の手番。AI は触らない)

| # | file | 現状 |
|---|---|---|
| 1 | `orchestrator/campaign/paper_story_a1_paired.py:175-176` | `V3_PILOT_PREREGISTRATION_RELATIVE_PATH` / `_SHA256` = `None` |
| 2 | `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json` | `preregistration` = `{path: null, sha256: null}` |
| 3 | `orchestrator/campaign/paper_story_a1_paired.py:168-170` | `V3_PILOT_POLICY_SHA256` (JSON bytes 変更に連動) |
| 4 | `orchestrator/tests/test_paper_story_a1_paired.py:1386-1390` | 未凍結を固定する正例 |

## 7. 成果物の形と分割

- 成果物 A / B に加えて spool fragment (worklog 1・decisions 1) と本 wave insight。
- 段 2 = read-only codex 1 本 (plan)。段 3 = read-only codex 2 本、レンズを分ける
  (sol = 本文の内容が規律 2/3 を緩めていないか・policy との不一致、luna = 工程分割と発効閉包の抜け・
  追加だけで赤になる gate)。段 6 = review 2 本 + 受入全走。
- 受入・実測環境 = login node での受入全走 (docs-only、計算ノード不要)。
