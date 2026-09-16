# [T-2671] 段 1 brief — 層3 の bench-first screening 対応の現況確定 (論文ストーリー §8 B-9)

**基準 commit:** `262c2993eae89f452dcea35fc61f97e41a689e8e` (local main tip)
**worktree:** `.claude/worktrees/dev-wave-t2671-layer3-screening`
**日付:** 2026-09-16

## 研究前進

論文ストーリー §8 の **B-9「層3 の対象拡張・値整合検査・機序仮説層 (v3)」** は未取得証拠表の 1 項で、
最新版 (2026-09-14) は「変化なし」と書く。**この記述は執筆時点で既に偽だった。**
本 wave は 3 項のうち **(a) 対象拡張**を成果物で確定し、(b) は既裁定、(c) は発効条件待ちであることを
一次資料で示す。完了判定 = (1) `backoff-sweep-silo-read-heavy-sweep-6f169f90` の材料レポートが repo に
tracked で存在し双射検査を通っていること、(2) その射影完全性が回帰テストで pin されていること、
(3) `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」に 1 項積まれていること。
これにより §3 の限定文「bench-first screening campaign は対象外」が外れ、説明可能性 (軸 3) の
**補助**証拠 (D1598 — 核ではない) の射程が 1 段広がる。新規計測はゼロ。

## 段 1 で実測した事実 (main checkout、2026-09-16 10:17〜10:35 JST)

1. **(a) は 2026-08-25 に閉じている。** 現行 producer で 6f169f90 を描画 → **rc=0**。
   `runs[1].screening=true` 保持、`aborts[0]` に `reason=screen-slower-than-floor` と `screen` payload
   7 key 射影、`rejects[0]` に screened variant、双射検査通過。着地 commit `ed251424d`、
   既存 test は `test_named_screening_artifact_builds_layer3_report_end_to_end` (assertion 1 本)。
   schema は `layer3_schema.json:128,145-156` に `screening` / `screening_disabled` を既に持つ。
2. **(b) は裁定で止まっている。** `docs/phase3.md:713` の見送り台帳 **[T-326]** — 2026-08-03 (124) の
   ユーザー裁定 (択 b) が `layer3_report` 本体の深い一致強化を**実施しない**と決め、
   「本体側へ着手するには択 (a) の再裁定が要る」と明記。verifier 経由の深い一致は
   `docs/phase3-8c-preregistration.md:516-520` のとおり実装済み。
3. **(c) は原料が 0 件。** 凍結設計 `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` が
   要求する `runs/agent_outputs.jsonl` は repo 内に存在しない。発効条件は「次に agent 出力が生まれる
   loop 再走と同時」。**DW-G04 により本 wave では実装せず設計メモに留める。**
4. **既存 7 レポートの campaign は現行 producer で再生成できない** (`campaign is legacy-unclassified`、
   rc=2 実測)。6f169f90 は admitted (`test_artifact_admission.py:218`)。
   **「対象 campaign 群」は記録当時と現在で同一ではない。**
5. **`_artifact_refs()` は campaign dir を `rglob("*")` で全走する**が、既存 7 レポートの
   `artifact_refs` に自分自身は入っていない (レポートは生成後に書かれるため)。

## scope

- **S1.** 現行 producer で `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json`
  を生成し tracked にする (親が実行)。成果物影響: 材料レポートが 7 件 → 8 件。screening campaign が
  「レポートを持つ campaign 群」へ初めて入る。
- **S2.** 射影完全性の回帰 pin を足す (**実装面 = Codex `role=author` 必須**)。現行 1 assertion を、
  (i) `screen` payload の全 key が `aborts` へ射影される、(ii) screened variant が `rejects` に載る、
  (iii) 双射検査の入力 multiset に abort event が含まれる、(iv) `verify_done` 不在でも fails-closed しない、
  の 4 点へ広げ、**それぞれに落とすと赤になる負例を対で置く**。
- **S3.** docs 現況化 (親)。`docs/phase3.md` の層3 項 (「bench-first screening campaign は対象外のまま」)
  を現況へ。`docs/paper-story/README.md` の stale 注記へ 1 項積む。
- **S4.** 起票。**[T-2671]** = 本 wave 本体。**[T-2672]** = (c) 機序仮説層 v3 (発効条件付き)。
  (b) は既存 [T-326] を指すだけで新規起票しない。
- **S5.** insight に着手順と残件を残す。

## scope 外 (実装しない)

- **(b) `layer3_report` 本体の深い一致強化** — [T-326] の裁定で実施しない。再裁定はユーザー手番。
  本 wave は受理集合を変えないテスト追加だけを行い、本体の検査強度は 1 mm も変えない。
- **(c) 機序仮説層 v3 の実装・`agent_outputs.jsonl` の writer 新設** — DW-G04 (原料 artifact 0 件)。
- legacy-unclassified campaign の admission 復旧、schema 拡張、`layer3_schema.json` の編集。
- 仮想リスク向けの framework・一般化・互換層 (ユーザー明示の scope 外)。

## 不変条件

- **規律 2 を緩めない。** 層3 は報告層であり correctness gate ではないが、双射検査・fails-closed・
  `additionalProperties:false` の受理集合は 1 つも広げない。追加は test だけ。
- **`orchestrator/campaign/layer3_report.py` を編集しない。** 1 byte でも変えると
  `meta.generator.sha256` が変わり、以後生成する全レポートの bytes が変わる (DW-O10)。
  docstring の加筆も同じ理由で不可 — 必要なら別 wave。
- **`layer3_schema.json` を編集しない。** screening は既に受理されるので schema 再凍結は不要。
- **既存 7 レポートの bytes を変えない。** 再生成しない (D828 / 記録済み artifact)。
- **凍結物を書き換えない。** `docs/paper-story/<日付>.md` の版と `claim-evidence/` は append-only。
  C11 の「7 件」はそのまま残し、訂正は README の stale 注記が担う。
- AI provenance: 実装面を含む commit は Codex `role=author` trailer を持つ (D95)。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 実レポートを campaign 配下へ生成するのは純増であり、自己参照 (`_artifact_refs` が
  以後 `reports/layer3_report.json` を含む) で fresh rebuild の bytes が変わるのは**既存 7 件と同じ状態**で、
  新しい欠陥ではない。→ 反例: 8c の「persisted ↔ fresh rebuild の深い一致」consumer が
  この campaign を読む経路が実在するなら、生成が新しい赤を作る。
- **(P2)** 「bench-first screening campaign は対象外」の否定には、名指し 1 campaign の end-to-end で足りる。
  任意の screening campaign について完全とは**主張しない** (DW-G03 の族一般化はしない)。
- **(P3)** [T-326] の裁定射程は `layer3_report` 本体の**検査強度**であり、既存挙動を変えない
  test 追加はその射程外である。→ 反例: 追加 test が実質的に本体の受理集合を狭めるなら射程内。
- **(P4)** T-2671 / T-2672 の採番は、稼働中の別 wave (`dev-wave-t2670-b7-three-run-materials`) が
  T-2670 を未 land で使っているため 1 つずらした。段 7 直前に再走査する (D70)。

## 変更面 (実アンカー)

| # | path | 変更 | 担当 |
|---|---|---|---|
| A1 | `orchestrator/tests/test_layer3_report.py` (既存 `test_named_screening_artifact_...` は 1415 行) | 射影完全性 4 点 + 負例を追加 | Codex author |
| A2 | `orchestrator/tests/acceptance_duration_ledger.json` | 追加 node の所要を登録 (要否を段 2 で確認) | Codex author |
| A3 | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json` | 新規生成 | 親 |
| A4 | `docs/phase3.md` 層3 項 (664 行付近) | 「対象外のまま」を現況へ | 親 |
| A5 | `docs/paper-story/README.md` stale 注記 (68 行節) | 1 項積む | 親 |
| A6 | `docs/spool/` fragment | worklog / decisions | 親 |
| A7 | `output/insights/2026-09-16/t2671-layer3-screening/` | brief・相談・残件 | 親 |

**触らない:** `orchestrator/campaign/layer3_report.py`、`orchestrator/campaign/layer3_schema.json`、
既存 7 件の `reports/layer3_report.json`、`docs/paper-story/2026-*.md`、`docs/paper-story/claim-evidence/`。

## 並列分割

- 段 2: plan 子 1 本 (read-only codex、`--reasoning` 必須)。
- 段 3: 敵対相談 2 本 — レンズ A = 「現況確定は本当に成立するか」(実測の読み違い・成果物影響)、
  レンズ B = 「裁定射程と scope の逸脱」([T-326]・D1598・凍結物・DW-G04 の射程)。
- 段 5: 実装子 1 本 (A1・A2 のみ)。
- 段 6: 変更面確定後に review 本数を再評価 (受理集合が変わらず正しさ防壁に触らないため軽量版候補)。
  変異 matrix は S2 の負例に対して必須。
