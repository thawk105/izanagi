# [T-288] 受け渡しの明示と単位ずれ — 逐語台帳

worklog エントリ (106)、決定は D118。branch `worktree-dev-wave-t288-recipient-matrix`、
commit `a1afaa1` (実装) / `168edbd` (焦点再レビュー fix)。

## 逐語

| file | 内容 |
|---|---|
| `s2-plan.md` | 段 2 codex プラン起草 (reasoning=max、read-only) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A (正しさ境界・リーク・規律 2/6)。NO-GO、blocker 4 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B (換装の実効性・scope 取り残し・恒真性)。NO-GO、blocker 3 |
| `s4-adjudication.md` | 段 4 裁定。所見 20 件すべて real、refuted ゼロ。プラン v2 と変異事前登録 |
| `s6-revA.md` | 段 6 敵対レビュー A (裁定遵守・正しさ境界)。NO-GO、blocker 2 |
| `s6-revB.md` | 段 6 敵対レビュー B (検出力・変異生存)。NO-GO、blocker 5、生存変異 4 |
| `s6-fix-brief.md` | 段 6 fix 裁定と変異表の再登録 (N01〜N15、一意 anchor) |
| `s6-refocus.md` | fix 後の焦点再レビュー。NO-GO、blocker 2、closed 5 / partial 4 / regressed 0 |
| `mutation_harness.py` | 変異 harness (flock 単一走行、内容比較復元、失敗 node 記録) |
| `mutation-ledger.json` | 変異本走の生台帳 |

## 実測

- **変異 matrix N01〜N15 = 15/15 KILL、生存ゼロ、ANCHOR_ERROR ゼロ。** 最終 anchor commit
  `168edbd` で再走しても同結果 (`168edbd` は `p3_autonomous_workload_trial.py` を変更していない)。
  baseline 走 + 15 dispatch を Pegasus gen_S 計算ノードで実行。
- **受入全走 = 4811 passed / 19 skipped** (request `877321`)。対象 2 file = 113 passed
  (基準線 104、純増 9)。
- provenance 監査 712 件・違反なし。三軸 conjunction の repo scan invariant 緑、
  placeholder hit ゼロ。

## 段 1 前提実測で確定した defect

`_metric_projection()` に abort 7.9% / LLC miss 12.4% 相当を入れると
`abort_rate_pct=0.079` / `cache_miss_rate_pct=0.124` が role へ届いた。role 定義の例示は
7.9 / 12.4 (`.claude/agents/planner-v4.md`)。**ちょうど 100 倍**。

## 親 brief が反証された 4 点

段 2 と段 3 が親の主張を 4 件反証した。いずれも一次資料で裏付けられている。

1. 「8c の live artifact は 1 件も存在しない」は**偽**。tracked な report と attempt journal が
   実在する (`output/insights/2026-08-01_t241-compute-llm-transport/evidence/`)。ただし
   `FROZEN_MANIFEST` の exact 23 path には含まれず、問題の key を 1 つも持たないため
   「key 互換は壊れない」という結論自体は残った。
2. 親が指した `:963` は `generation_record["metrics"]` ではなく
   `critic_payload["harness_result"]["metrics"]` であり、前者は**現行に存在しない**。
3. **親は第 4 の recipient (critic) を見落としていた。** critic は同じ dict を受け取り、
   現行はそこへ percent 名の field に率を入れて渡していた。
4. 親の成果物影響は**過大表現**だった。`MAX_APPROVED_GENERATIONS=1` なので、承認済み run で
   有限値を受けるのは critic だけであり、planner / coder は全 `None` を読む。

## 段 6 で塞いだ生存変異

段 6 レビュー B が 4 件の生存変異を実証した。いずれもテスト緑のまま通っていた。

- critic の `llc_miss_rate` を ×100 する変異 — E2E の疑似 drive が metrics を返さず、
  値が全て `None` だったため検出されなかった
- `contention_level="wrong"` — 値でなく key の存在しか見ていなかった
- live outcome にだけ `generation_record["metrics"]` を復活させる変異
- `metric != 1.0` — 境界 `1.0` が未被覆だった

焦点再レビューはさらに 4 件を返した (critic の残り 3 指標が未 assert、payload の
top-level key 集合が部分集合検査、範囲 guard の後付けが未 pin、docstring の残る断言)。
これらも fix 2 巡目で塞いだ。

## 閉じ方 (`DW-O16`)

`DW-O16` の上限 3 巡に対し 2 巡で閉じた。焦点再レビューの残る blocker 2 件のうち、
RF-01 (critic の 3 指標未 assert) は fix 2 で closed、RF-02 (report の形を全 outcome で
固定していない) は **scope 外として backlog へ回した** — 本 wave は report の形を変えておらず、
全 outcome 分の report 形テストは独立した検査追加である。根拠は変異本走 15/15 KILL と
受入全走 4811 passed。

## 裁定パッケージ (ユーザーへ返す。本 wave 未実装)

D118 の「残余」節および worklog (106) の「次の一手」を正本とする。
