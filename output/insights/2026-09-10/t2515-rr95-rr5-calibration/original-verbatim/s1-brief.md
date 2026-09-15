# 段 1 brief — [T-2515] rr95 / rr5 の t48 pegasus accepted calibration

## 研究前進
pegasus/t48 の accepted calibration は balanced (rr50/skew0.9/rmw0) の 2 件しかない。D15 が
calibration を (env, thread, 代表 workload) でキーすると決めているため、read-heavy (rr95) と
write-heavy (rr5) のセルは今 balanced の record を借りている (`orchestrator/tests/fixtures/
b10_backoff_shape_locks/read-heavy.campaign.lock` と `write-heavy.campaign.lock` がいずれも
`calibration-753f535a8d024727.json` を指す)。本 wave の完了判定は「rr95 と rr5 の
`quality.status=accepted` な calibration が `output/env/pegasus/calibration/registered/` に
1 件ずつ実在すること」。最小差分は既存 certification 経路の rratio allowlist を 2 値ぶん広げること。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- **(P1) 依頼の「A-6 がここで止まっている」は一次資料と食い違う。** `docs/paper-story/2026-09-05.md`
  §8 の A-6 は停止原因を「計算ノードで `FetchContent_Populate(masstree)` が落ちる」と書き、
  calibration 不足とは書いていない。親の provisional 裁定: **成果物は変えない** (rr95/rr5 の
  accepted calibration を取る)。ただし本 wave が A-6 を解除したとは書かず、根拠は T-2515 原文の
  「B-4 の 3 workload セル集合が 2 件不足」に置く。
- **(P2) allowlist は閉じた exact 集合を保つ。** D1488 が「任意 N への一般化を採らない」と定めた
  精神に従い `{5, 20, 50, 80, 95}` の exact 集合へ置き換える。任意 rratio 受理・範囲判定にしない。
- **(P3) レコード数は calibrator に決めさせる。** 既存 balanced 2 件は `saturated:false` /
  `lower_bound_selected:true` / `records:1,000,000`。rr95/rr5 も D15 の同じ規則で決まった値を
  そのまま採る。親が 1,000,000 を期待値として先に書かない (規律 4 の両側の罠)。

## scope (実アンカー)
| # | file | anchor | 変更 |
|---|---|---|---|
| A1 | `tools/pegasus/submit_certify.sh` | 42-45 行 `RRATIO` 検査 / 8 行 usage | allowlist を 5 値へ |
| A2 | `tools/pegasus/certify_calibration.sh` | 154-158 行 `IZANAGI_CALIBRATION_RRATIO` 再検査 | 同上 |
| A3 | `orchestrator/tests/test_pegasus_calibration_workload.py` | 35-63 / 429-446 / 639-647 行 | pin 更新と 5/95 の正例・未登録値の負例 |
| A4 | `docs/pegasus-runbook.md` | 639-643 行が pin する H1/H2 例の周辺 | 例の追記 (親が編集) |

## scope 外
`tools/pegasus/admission_registry.json` (新規実行体を作らないので触らない — 稼働 wave
dev-wave-t2417-policy-arm-perf の唯一の重複候補だった)、env_contract の generation 追加、
既存 registered 2 件の bytes、gate・検査・台帳の新設、任意 rratio への一般化。

## 不変条件
規律 2 — 正しさゲートを緩めない。`calibrate.py --certify` の accepted 8 条件 (`report.py`
`certification_quality_reasons`) と schema_v2 の accepted 追加条件は 1 byte も緩めない。
allowlist 拡張は「どの workload を測ってよいか」だけを変え、「測った結果を accepted と呼ぶ条件」は
変えない。投入側と job body 側の 2 重検査という構造も維持する (片方だけ広げない)。
`submit_certify.sh` は main 側 admission_registry.json に `local-ok` で登録済みなので F660 の
「新規実行体は同 wave で実測できない」に当たらない。

## 成果物
(1) rr95 / rr5 の accepted calibration JSON + md 各 1 件 (registered/ 配下、job が書く)、
(2) 実装 4 file、(3) `output/insights/2026-09-09_t2515-rr95-rr5-calibration/` の逐語・変異台帳、
(4) worklog / decisions の spool fragment。

## 分割方針
段 2 プラン 1 本、段 3 敵対相談 2 本 (受理集合が広がるので省略しない)、段 5 実装子 1 本
(変更面が 3 file と小さく所有を割る利得がない)、段 6 レビュー 2 本 + fix。
実測は実装 commit 後に rr95 / rr5 を別 submit-tree から 2 job 同時投入 (walltime 02:00:00)。
