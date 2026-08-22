# D510 追随実装の所在監査 — 床値判定方式の再凍結 (2026-08-21)

## 総合結論

**D510 (2026-08-18、`docs/decisions.md` D510) が要求する判定器・3表・事前割当 attempt
registry は、command 引数が土台に指定した `orchestrator/campaign/between_run_floor.py` /
`s8b_floor_campaign.py` / `s8b_oracle_driver.py` とは無関係であり、既に別 wave
(T-1352・T-325/T-1310/T-1337・[T-1311]) が実装済みであると確定した。** 唯一の未実装項目
(D510 項目6「測定の近接性と主張の強さ」) は、本 wave では **実装しなかった**。理由は
(a) `s8c_result_judge.judge()` に production caller が現存せず DW-G04 の発火 gate が不成立、
(b) 最小実装案自体に是正必須の設計欠陥がある、(c) D510 項目7 の epoch 境界により正式系列は
既に fail-closed で当面の実害がない、の3点。approval bytes 生成・裁定代行・正式実験起動・
測定は一切行っていない。

## 1. 経緯・目的

command 引数は「[T-1472由来] 床値判定方式の再凍結」として、D510 の判定器・attempt
registry・judge・3表・validator を `between_run_floor.py` 等を土台に実装するよう指示した。
一次資料として `output/insights/2026-08-21_t1472-h1h2-readiness-audit/README.md`
(以下「readiness audit」) §5・§10「floor判定方式」行を引用していた。段1 brief で
この前提を実測したところ、`between_run_floor.py` は A2 (between-run noise floor
calibration driver) であり D510 の判定器と無関係と判明したため、段2 codex plan・段3
敵対2レンズで独立に再検証した。

## 2. 段1 brief の前提修正 (P1)

`git log --oneline -- orchestrator/campaign/between_run_floor.py` で T-425 commit
`3ef63484` の実際の diff (3 hunks: schema_version 定数追加・receipt へのkey追加・CLI
余分引数拒否) を確認。commit message 自身が「between_run_floor.py が**そもそも
official/pilot 儀式を経ない設計であるため、この driver の手続きを直接は変更しない**」と
明記していた。

一方、D510 の実体は次に既に存在すると確認した (git log で各 wave の commit を裏取り):

| D510 機構 | 実装場所 | 実装 wave |
|---|---|---|
| judge (paired diff 判定) | `orchestrator/campaign/s8c_result_judge.py:763-893` | T-1352 (`296b4ba4`) + fix2件 |
| 3表 (`descriptive_only`/`official_status`/`selection_evaluation`) | 同上 `:39,896-1000,1437-1462` | 同上 |
| 事前割当 attempt registry | `orchestrator/campaign/trial_registry.py:2672-3307` | T-325 (`f236a6da`) → T-1337 → T-1310 (`c1295565`、「D510 attempt registryへ統合する」) |
| role payload 非干渉性 二層digest | `orchestrator/campaign/s8c_generation_projection.py` 等 | [T-1311] |

役割分担・詳細は `verbatim/stage1-brief-and-stage4-adjudication.md` の (P1)/(P1-継続) 節。

## 3. 段2 codex plan (`--reasoning max`, sandbox read-only)

独立に (P1) を再検証し、D510 の7項目それぞれについて file:line 判定を行った (項目1〜4
実装済み・項目5部分実装 (role payload非干渉性、機械検査対象だが評価器は非充足を返し続ける
意図的 fail-closed 設計)・**項目6欠落**・項目7構造的 fail-closed)。項目6の最小実装案
(`_ObservationProvenance` 追加・`_build_observation_context` 拡張・`_evaluate_contrast`
への diagnostics 接続・(c) は `INDETERMINATE` 化) を file:line 粒度で提示し、規律5に
沿った分割候補4件 (① provenance型検証、② ペア近接性ラベル導出、③ 3表出力、④ producer側
生成) を提示、①②を同一実装単位・③④を延期と推奨した。全文: `verbatim/stage2-plan.md`。

## 4. 段3 敵対相談2レンズ (`--lane sol`/`--lane luna`, `--reasoning max`, sandbox read-only)

**レンズ sol (正しさ境界)**: real 4件。(a) provenance 必須化が `judge()` の旧形式入力の
受理結果を変え brief の不変条件と矛盾。(b) 近接性ラベル・時間差が diagnostics 止まりで
3表・公開成果物に届かない。(c) 「3表への影響なし」は誤り — (c)ラベル観測は official
table の内容 bytes を変える。(d) **`relation_kind` が既存 raw-value attestation
(SHA/issuer) に束縛されず自己申告可能** — 観測の実性質を偽って最強の主張ラベル
(`continuous`) を詐称できる、規律2隣接の脆弱性。全文: `verbatim/stage3-lensA-sol.md`。

**レンズ luna (整合・実効性・所有範囲)**: (P1) は独立確認で正しい (別実装の見落としなし、
ただし brief の `s8c_result_judge.py` 行数記載「777行」は誤り、実際1512行 — 是正済み)。
**決定的所見: `judge()` (1012-1070行) に production caller が存在せず、参照はテストと
静的 AST evaluator (`s8c_preregistration_evidence.py:2776-2803`) に限られる。DW-G04
(発火gate) の要件が不成立。** 明確な推奨: 実装しない。C02 (t1472-c02-arm-noninterference
想定 scope) との直接ソース衝突は低いが、将来の入力契約統合方針は未定義。全文:
`verbatim/stage3-lensB-luna.md`。

## 5. 段4 裁定 (親)

**裁定: 実装しない (`4→7→8→9`)。** 両レンズの所見を採用し、(P1) の前提修正を確定
記録として残す。裁定の全文・採否・裁定パッケージ (次の一手の前提条件) は
`verbatim/stage1-brief-and-stage4-adjudication.md` の「段4 裁定 (親)」節を正本とする。
decisions への反映は `{{D:d510-followup-implementation-audit}}` (fold 後の実番号は
`docs/decisions.md` を参照)。

## 6. 稼働中 wave との重複確認

`ListAgents` (17 peer session) と `git diff main..<branch> --stat` の実測により、
`worktree-dev-wave-t1472-c02-arm-noninterference` (peer 名「arm c02 non-interference
correction」、D510項目5相当の可能性) が live・busy だが未 commit と確認した。
`worktree-T-1371-official-run-root` / `worktree-dev-wave-t1280-role-output-contract` /
`worktree-dev-wave-t1458-noncertifying-consumer` は `trial_registry.py` /
`p3_autonomous_workload_trial.py` / `autonomous_trial_completeness.py` を活発に変更中と
確認し、本 wave はこれらへ触れなかった (実装差分ゼロのため実害なし)。T-425/T-972/
rulings-calibration-registration 系の候補 branch は全て main に完全包含済み
(`ahead=0`) と確認した。

## 一次資料索引

- D510 全文: `docs/decisions.md` (grep `^## D510`)。
- D496 全文: `docs/decisions.md` (grep `^## D496`)。
- `docs/phase3-8b-descriptor-design.md` §10 (10.1〜10.7、2026-08-18再凍結の規範本文)。
- `docs/phase3-8c-preregistration.md` §4 (非干渉性の要求)・§6 (C02 の実装状況記述)。
- readiness audit: `output/insights/2026-08-21_t1472-h1h2-readiness-audit/README.md` §5
  (C01〜C12個別評価表)・§10 (blocker要約表、「floor判定方式」行)。
- T-425 実装 commit: `3ef63484`。
- 本wave verbatim: `verbatim/stage1-brief-and-stage4-adjudication.md`・
  `verbatim/stage2-plan.md`・`verbatim/stage3-lensA-sol.md`・`verbatim/stage3-lensB-luna.md`。
