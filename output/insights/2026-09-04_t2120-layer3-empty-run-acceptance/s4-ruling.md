# 段 4 裁定 — [T-2120] 層 3 の空走を受入限定で閉じる

基準 commit 764fdf202 (local main = wave HEAD、段 4 直前に main 未前進を確認)。

## 結論

**実装しない (4→7→8→9)。** D1460 が定めた「受入限定で閉じる」は現行 tree で既に成立しており、
受入 `assert_trial_registry_acceptance` において層 3 の鎖が `_fresh_layer3_for_comparison` を 1 度も
通らずに受領証発行へ達する report の形は存在しない。段 2 plan の主案 (鎖の実体検証済み campaign を返し
受入が全件一致を要求) も対案 (述語型) も、現行の受入では到達不能の恒真 gate になる。到達不能な gate を
足すことは、本 wave の依頼が scope 外とした「仮想リスク向けの gate・検査の追加」そのものであり、
DW-G04 (発火条件を満たす既存 artifact を brief に書けない条件付き機能は実装しない) と DW-G05
(放置時に成果物の値・受理集合・参照が変わらない) にも当たる。

## 所見の裁定

| # | 出所 | 所見 | 性質 | 採否 / scope |
|---|---|---|---|---|
| A1 | sol | campaign 付き admission 失敗 cell は、受入が鎖の前に呼ぶ `assert_execution_digest_chain` (`trial_registry.py:5995-6003`) の腕 digest 検査 `autonomous_trial_completeness.py:1137-1142` "cell admission failure projection is not exact" で拒否され、鎖に到達しない | real (親が現物で検算: registered launch では `requires_arm_digest_chain` が真、failure decision かつ非 campaignless-exact な cell は `_fail`) | 採用。裁定の根拠 |
| A2 | sol | 主案の returned-ID gate は現行到達集合で恒真 | real | 採用 → 実装しない |
| A3 | sol | 対案の述語型も候補集合が空で不発、将来は過剰拒否しうる | real | 採用 → 実装しない |
| A4 | sol | T-2075 の post-check を「機構として数えない」判断は正しく、新 gate も同様 | real | 採用 |
| A5 | sol | 変更前受理・変更後拒否の report 集合は空 | refuted (受理集合変化なし) | 記録 |
| A6 | sol | 戻り値追加は producer / standalone を変えない | refuted (懸念不成立) | 記録。実装しないので無関係 |
| A7 | sol / B6 | pin は live tree 追随型、`autonomous_trial_completeness.py` は tuple 外 | real (brief の誤り) | brief 補正として記録 |
| B1 | luna | plan の負例 fixture は producer 実在形 (diagnosis key、critic count=1、accounting) にならない | real | 実装しないので消化。A1 の傍証 (producer の failure cell の key 集合は campaignless-exact と異なる) |
| B2 | luna | `build_report` 直接観測の不足 | real | 実装しないので消化 |
| B3 | luna | 変異 2 件が単一理由でない | real | 実装しないので消化 |
| B4 | luna | 呼び手破壊の懸念 | refuted | 記録 |
| B5 | luna | T-524 との統合可能性は確定済みと扱えない | real | 実装面差分ゼロなので統合対象なし。親の live 再走査 (merge-base c6a94ec99 基準、hunk +6193/+6360/+6347、鎖区間 6021〜6096 不変) は記録 |
| B7 | luna | D863 の機械 readiness (C09 evaluator は `EVIDENCE_UNDEFINED`) は本 wave で変わらない | real | scope 外。C09 は既存項 (entry 1127 fold で採番済みの c09 系 2 項) の所有 |
| B8 | luna | brief の到達位置・既存被覆の一般化過多 | real | brief 補正として記録 |
| — | 親 | shape 2 を実際に止めている arm-digest-chain の拒否 message にテストが無い (`grep -rn "projection is not exact" orchestrator/tests/` 0 件) | real | scope 外 (本題は空走の閉鎖であり、既存機構の被覆追加は別変更単位)。worklog 次の一手へ P3 新規項として残す |

## brief の (P1)〜(P4) の帰結

- (P1) 実体観測型は設計として述語型より強いが、到達不能なので採らない。
- (P2) 戻り値追加が producer / standalone を変えないのは正しいが、実装しないので不要。
- (P3) 既存 post-check は残る (触らない)。
- (P4) `do_build=False` と鎖の既存受理・拒否は 1 件も変わらない (差分ゼロ)。

## 変異事前登録

実装面の差分ゼロのため変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 段 7 で記録するもの

- insight `output/insights/2026-09-04_t2120-layer3-empty-run-acceptance/README.md` に、受入の空走 3 形が
  どこで止まるかの file:line 鎖と、実装しない理由、brief の誤り 3 点、plan / 2 レンズの全文を凍結。
- worklog fragment: [T-2120] 完了 (remaining: none、base digest 2a46970f…)、新規 P3 項 1 件
  (arm-digest-chain の failure-projection 拒否の受入テスト不在)。
- decisions fragment は書かない (D1460 を覆さず、新しい設計判断もない)。failures fragment も書かない
  (事故なし)。
