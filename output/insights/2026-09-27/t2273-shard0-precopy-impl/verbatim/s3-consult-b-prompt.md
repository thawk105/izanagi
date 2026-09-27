単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s1-brief.md — 親の段 1 brief ((P1)〜(P8)、受入・実測環境、計算量)。**brief 自身も攻撃対象である。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md — 段 2 plan (攻撃対象)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/verbatim/ — 依頼の逐語 (T-2273-origin.md) と既裁定 D2253・D2242・D357・D2068・D2061・D2062 の逐語。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md — 対照診断 (P の効果)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md と同 dir の verbatim/s4-ruling.md — 前回の実装・変異・実受入隣接 3 対の事前登録と結果 (計測の型の雛形)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ — 前回の計測 probe (門番付き逐次投入 `t2273lc_run_series.sh` / `t2273lc_run_measure.sh` / `t2273lc_run_warm.sh`、集計器 `t2273lc_ab_analyze.py`、`t2273lc_gate.conf`)。本 wave で移植する予定。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py と orchestrator/tests/test_s8b_oracle_driver.py — plan が名指す行だけ grep / sed で引く。

書込可能な tmp は無い。静的検査だけでよい (実走は親が行う)。予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終われ。

## レンズ B — 過剰・削除・計測設計

plan と brief を守らず、削れるもの・足りないものを探せ。特に:

1. 過剰: 本題 (D2253 項 2 の形の実装) を超える機構・検査・marker・例外経路・test は無いか。より短い等価な実装 (行数・分岐数) を示せ。仮想リスク向けの gate・検査・台帳・一般化の追加は依頼で scope 外。
2. test の最小性: 正例 1 件で足りるか / 多すぎないか。変異 6 本のうち冗長なもの、逆に P の本質 (collection と重ねる = configure_node で起動) を殺せていない穴。
3. 計測の事前登録案を書け (前回 s4-ruling の「計測の事前登録」1〜8 を雛形に): A / B の定義、順序、門番、温め、有効性、判定量、land 条件 (前回と同じ「3 対すべて Δ > 0 ∧ 対率中央値 ≥ 10 %」でよいか)、5 分上限の別判定 (B の W_max 3 走の中央値 ≤ 300 秒か、W_0 か)、補助量 (W_1・W_2、写し待ち)。依頼は「5 分に届かなければ次は (b) = 発行 subprocess と記録して止める」。land 条件と 5 分判定の 4 通りの組合せそれぞれで何を記録するかを書け。
4. 前回 probe の移植で変える必要がある箇所 (job dir・slug の直書き、E1 の「B で増える node 1 件」の定数、分類)。実受入に写しの待ち時間の計器が無いこと — 計器を足すべきか (scope 外か)、既存出力から取れる代理量があるか。
5. 計算量: 前回実績 (29 shard job の Elapse 合計 8,333 秒、10 走中 infra 失敗 3 走) を単価に、本 wave の見積り (6 走 + 取り直し見込み + 焦点走 + 変異 + 記録前受入) を node 時間で出せ。2 node 時間を超えるか。
6. brief の数値・前提の誤り。

## 出力形式

見出し「## 所見」(各所見に ID B1〜、重大度 must-fix / should / nit、file:line、根拠、修正案)、「## 計測の事前登録案」、「## 計算量見積り」、「## 削れるもの」、「## GO 判定」(GO / 修正後 GO / NO-GO と 1 行理由)、「## 総括」(5 行以内)。
