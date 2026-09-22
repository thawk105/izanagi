# 段 6 裁定 5 巡目 — [T-2857] (2026-09-22 22:1x JST、親 = Claude manager)

入力: coverage-3 (18195.nqsv、Elapse 878 秒、HEAD 6d7014707 = main bc3b23953 取り込み後、結果 = job dir `coverage-3.json`、要約 = `coverage-3-summary.txt`)。
全 30 case が走り、55 check のうち 54 が真。偽は `mutation/no-prefix-unlock-limit:expected` の 1 件。

| # | 内容 | 判定 | 扱い |
|---|---|---|---|
| J1 | 上限出口の prefix unlock 変異を `maxwait` (lock 競合で 50 µs 待って retry) で走らせたが、変異ありでも certified (commits 258,439、aborts 2,847) で対照 (commits 260,047、aborts 2,850) とほぼ同じ。`maxwait` は 1 周 50 µs × 32 周 = 1.6 ms 待つ間に保持者が解放するので、legacy workload (200 records / 4 threads / skew 0.9 / RMW / 1 秒) では上限出口にほぼ到達しない。同じ workload で `retry` (待機 0 で retry) の焦点走 `focus/retry` は probe の上限 abort 125,445 回 (retry 後の取得成功 19,856) で、上限出口に大量に到達する。つまり偽は検出の失敗ではなく、事前登録 (段 6 裁定 1 巡目 F5 の `maxwait`) の方策の構成で上限出口に到達していなかった空振りである | real (親の事前登録の誤り) | fix。上限出口を狙う case (`mutation/no-prefix-unlock-limit` と対照 `control/no-prefix-unlock-limit`) の方策を `retry` に替える (`retry` は常に retry を返すので action-abort 出口には行かず、lock 競合は CAS 成功か上限出口でだけ終わる)。期待 (変異は trace-timeout、対照は certified) は変えない。加えて、上限出口の到達の証拠として「同じ方策・同じ workload の `focus/retry` の probe の上限 abort > 0」を `mutation/no-prefix-unlock-limit` の判定に要求する (到達しない構成で空振りを合格にしない、DW-O13)。事前登録からの変更は訂正として insight と decisions fragment に記録する |

その他の 54 check の実測 (要約): 負例 6 走は既存 driver と同じ判定で合格 (norw non-serializable cycle 40,756 / 15,786・exit 1、lockskip X 2 種、early-unlock 保持欠落のみ)。焦点 `focus/focus` の 3 照合は一致 56,777〜62,431・不一致 0、成功後比較も合格。hook 変異の赤集合は宣言と完全一致 (abort 解除 {abort, lock, commit}、lock 解除 {abort, lock}、commit 解除 {commit}、要因誤記録 {reason})。再読込削除で retry 後の取得成功 0 (対照 19,856)。clamp 削除と action-abort 出口の unlock 削除は trace-timeout。上限削除は certified (非検出対照)。flag 境界 4 種は `#error`、TRACE=0 は不混入。

変異の事前登録: 追加なし。
