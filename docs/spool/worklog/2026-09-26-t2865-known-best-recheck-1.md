---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: t2865-known-best-recheck
seq: 1
title: silo-function-policy 軸で既知最良 (静的 10 µs) を 3% 超えた IR 3 点を別 job で再測し、計測前に固定した判定規則で 3 点とも再現 (r' 1.051〜1.073)。既存 driver をコード変更なしで 3 job 投げ直し、repo 外の集計で判定 (計測 JSON + insight、branch t2865-known-best-recheck)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-26/t2865-known-best-recheck/verbatim/request.md`): [T-2865] の付随。D2243 項 1 の別 job 再測。記録 = 同 insight の README、設計判断 = {{D:silo-policy-known-best-recheck}}。
- 起点 = local main `265cce13c` (fresh worktree、開始 gate rc=0)。並走中の段階 E wave (`worktree-dev-wave-t2865-silo-policy-stage-e`) が `silo_policy_ir.py` に追加中 (未着地) だったので、計測は起点の driver で行い、IR 本文 sha256 の一致で同一性を確かめた。同 wave が [T-2865] の台帳項目を更新する見込みのため、本 fragment は [T-2865] の項目に触れない。点 ID・比は段階 E wave へ送っていない。
- **判定規則は計測前に commit した** (insight §1、commit `4175771006`、20:15:46 JST、計測投入は 20:16 JST ごろ)。段 3 相談 1 本 (adopt_with_conditions) の must-fix 2 件 (分類の優先順位、値を見ない投げ直し規則) を採用した。
- **計算の見積り (投入前、job Elapse の実測単価):** 計測 3 job 約 0.65、最悪 (全 job 投げ直し) 1.30、受入 1 回 約 0.30 (当日の受入 3 shard の Elapse 合計 約 1,070 秒) × 最大 2 回。検査込み 通常 約 0.95・最悪 約 1.89 node 時間 < 2 で、D2212 項 4 のユーザー確認は不要と判断した。
- **結果:** 3 job とも rc=0、投げ直し 0 本。1111 (job 0) r' = 1.051、1110 (job 1) 1.065、1001 (job 6) 1.073 で 3 点とも「再現」。最良参照は 3 job とも fixed10。18 方策すべて両 verify serializable・trace0 clean。相方点は 0.973〜0.989。
- **段 6:** read-only レビュー 1 本は数値を全件照合して一致としたうえで NO-GO (must-fix 1: 「選択の上振れを含まない」は断定しすぎ、should 2: 元 throughput 3 値の丸め、集計スクリプトの追加照合の明記)。README を直し、焦点再レビュー 1 巡で閉じた (結果は下)。
- 焦点再レビュー 1 巡目は GO (3 所見とも closed、修正値は元 JSON から再計算して一致、新規所見なし)。
- 計算ノードの使用 (job Elapse): 計測 29950〜29952.nqsv 770・774・774 秒 (計 2,318 秒)。焦点走・変異なし (repo の実装面の差分ゼロ、DW-S04)。受入は land の受領証。
- 工数: Codex 子 = consult 1、author 1 (repo 外の集計スクリプト、`.md` 逐語で insight に置き実行可能資材は commit しない)、review 1、focus 1。

## 次の一手差分
