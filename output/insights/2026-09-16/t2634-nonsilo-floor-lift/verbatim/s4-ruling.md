# 段 4 裁定 — [T-2634] 非 silo の within-run floor の保留解除

裁定時刻 2026-09-16 20:35 JST。段 4 直前の再走査: local main は 8f17db598 から 702b3c26f へ 19 commit 進んだ
(merge / fold のみ、本 wave の編集面 `docs/phase3.md` / `between_run_floor.py` / `layer3_report.py` に差分なし)。
T-2634 の状態語は carry のまま (1561 まで変更なし)。T-2634 に触れる新規 D は D2044 項 12 以外に無い。

## 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | A-3, A-裁定1 | P5 の「D1360 が禁じるのは性能比較値だけ」は逐語より狭い。登録根拠は D2044 項 12 の用途限定解除に置く | real | **採用**。P5 を撤回し、根拠を D2044 項 12 に一本化 |
| 2 | A-8, B-3 | mocc rr50 の LLC miss / CV は record 自身にある (14.821% / 1.4348% / n=10)。plan の「欠落扱い」は README 単独の限界 | real | **採用**。4 件とも record JSON を出典に転記 |
| 3 | B-1 | `layer3_report.py:518-538` は `calibration/` 直下 + contract pin だけを走査し `registered/` を再帰しない (D1508)。phase doc 登録は report 消費の開通ではない | real | **採用**。phase3・decisions・insight に「layer3 の探索・契約世代・活性化は変更していない」を明記。silo rr95 / rr5 も同じ状態なので登録の水準は揃う |
| 4 | A-5, A-裁定3, B-訂正4 | 再開条件「pin を進めれば通る」は条件不足。実 checkout の CMake SOURCES 列挙 file に include / `#if TRACE` / hook 呼出しの 3 証拠が要り、tictoc は baseline 対応も要る。関門通過は測定成功・verifier 通過の十分条件ではない | real | **採用**。decisions に必要条件として書く |
| 5 | A-6 | 「between-run floor は現行 pin で起動不能」は protocol を省くと過大 (silo は True) | real | **採用**。「mocc / tictoc は測定開始前に拒否される」と限定 |
| 6 | A-7, A-裁定4 | login node の probe を計算ノード実走の証拠にしない。関門は source text を読み環境非依存なので静的帰結として書ける | real | **採用**。「計算ノードで実走確認済み」とは書かない |
| 7 | A-訂正3, B-訂正3 | F2 は実測 (述語値・BASELINES・argv) と静的帰結 (rc=2・ValueError) を分ける | real | **採用** |
| 8 | A-規律2判定 | within-run の登録は D1639 の between-run (環境節の走行間ばらつき) を充足しない。brief の研究前進にこの区別を残す | real | **採用**。研究前進 = 非 silo の「1 測定の品質」の公式記録。走行間ばらつきは未充足のまま |
| 9 | A-9 | accepted 較正は意味論的正しさ・verifier 通過を保証しない。correctness certification を付けない | 判定不能 → 制約として採用 | **採用**。「certified」「検証済み」と書かない |
| 10 | B-1 訂正1, B-登録先表 | F1 の「実体は未登録の散文だけ」は不十分。政策上の保留 (docs) と report 接続条件 (T-2136、D1508) を分けて書く | real | **採用** |
| 11 | B-裁定3 | runbook `:1373` の「登録済み calibration は 2 件」は無限定だと現物 8 件と不一致 | real (scope 外) | **不採用 (本 wave では触らない)**。依頼「本題の解除と実測だけ」。insight に観察として残す |
| 12 | A-訂正6, B-P4 | P4 (tictoc BASELINES を足さない) は維持。ただし「起動できない baseline は規律違反」の一般論は撤回 (現行 mocc が反例) | real | **採用**。理由 = 今回の登録に不要・測定は開通しない |
| 13 | A-訂正7, B-訂正6 | 「output/ を書かない」は新規 insight と矛盾 | real | **採用**。「既存較正 record・凍結成果物の bytes 不変、新規 insight は作る」 |
| 14 | B-fragment | `[T-2634]` は `完了` でよい (起票逐語 = 裁定を求める、裁定逐語 = between-run を終端条件にしない)。report 接続まで求めるなら `更新` | real | **完了を採用** (争点 1 = A)。完了範囲を「用途限定の文書登録」と明記 |
| 15 | A-2, A-4, B-2, B-4, B-5, B-7 | 各 refuted (裁定矛盾、5 件目、非 silo 一律拒否分岐、受理集合変化、test 赤、他 branch の 8b 変更) | refuted | 記録のみ |

## 争点の裁定

1. **公式登録の説明根拠** = A (D2044 項 12 の明示的な用途限定解除)。
2. **mocc rr50 の表記** = A (record 一次値)。4 件とも `saturation.miss_rate_at` / `noise_floor.cv` / `noise_floor.throughputs` の長さ / `host.node` / `acquisition_receipt.qsub.request_id` から転記。
3. **「公式成果物へ入れる」の完了範囲** = A (用途限定の文書登録で完了)。layer3 report への接続 (契約世代の登録・活性化・v2 campaign) は変更しない、と明記。
4. **between-run 再開条件** = A (実 checkout の source 証拠 + tictoc の baseline 対応 + 関門通過 ≠ 測定成功)。
5. **計算ノードへの一般化** = A (静的帰結として書く)。
6. **runbook の「2 件」** = B (触らない、insight に観察)。
7. **tictoc baseline** = A (今回は追加しない)。

## plan v2 (確定)

- **実装面差分ゼロ (docs-only)。** 段 5 実装子・段 6 レビュー子は起動しない (DW-C00)。変異 matrix = 実装面差分ゼロで免除。
- 変更 file: `docs/phase3.md` (8b 節、`[x] [T-2515] write-heavy …` の項の直後に `[x] [T-2634]` 1 項目)、
  `docs/spool/worklog/2026-09-16-dev-wave-t2634-nonsilo-floor-lift-1.md`、
  `docs/spool/decisions/2026-09-16-dev-wave-t2634-nonsilo-floor-lift-2.md`、
  `output/insights/2026-09-16/t2634-nonsilo-floor-lift/README.md` + `verbatim/`。
- phase3.md の行は plan の文面案を基に、上の裁定 2・3・5・9 を反映 (record 出典、layer3 未接続の明記、mocc / tictoc 限定、certified と書かない)。
- decisions は 1 件: 決定 (4 対の登録、登録先、between-run 未実測と再開の必要条件、変更しないもの、D2044 項 12 の用途限定解除としての適用)。
- 受入・実測: 安い関門 (`check_ai_provenance.py`、`check_docs.py`、`spool_fold.py --dry-run --show-diff`、焦点 test) を緑にしてから受入全走 1 回 (`dev_wave_wait.py acceptance`、docs-only なので `--owned-path` 不要)。実 repo を読む焦点 test = `orchestrator/tests/test_spool_fold.py` の phase3 現物 test と `test_check_docs.py` の repo 実走部。
- 段 7 の記録は受入前に commit し、受入は記録 commit を含む最終 tip に対して 1 回。

## 不変条件 (訂正版)

- 規律 2: D1373 の関門・`test_between_run_floor.py` の期待値・pin を変えない。規律 1: trace-disabled のまま。
- 既存の較正 record (`registered/` 8 件)・`between_run_noise_*.json`・凍結成果物の bytes を変えない。新規 insight は作る。
- 4 対以外 (非 silo rr5、cicada、silo) の状態語を変えない。「性能比較」「床値本走の完了」「certified」「検証済み」「解除により測定可能になった」と読める文を書かない。
