結論は **NO-GO**。protocol 本体の主要な修正は概ね成立したが、対象 diff が §9 の循環を入口文書で再導入している。残 blocker は **1 件**。

## 7 点の判定

| # | 判定 | 現物による根拠 |
|---:|---|---|
| 1 | **closed** | 各 node の 10 観測から切片＋傾きの OLS を計算でき、`β̂_i`・`se_i` の残差自由度は `R−2=8`。したがって `S_β` と `V_β` は cell 内反復なしでも計算可能で、閾値 `2` も測定前 literal になっている。[§5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:319) |
| 2 | **partial** | round を順序位置と定義し、壁時計共通外乱を吸収しないこと、§1.1 の二元配置との対応は明記された。一方、過去データは反復番号と経過時間が完全に共変しており、「壁時計に共通の外乱ではない」とまでは識別できない。[§5.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:294) |
| 3 | **partial** | §5.4 の上から評価する 5 状態は排他的で、12 完了 node は `terminal_reduced` へ到達可能。§3.3・§5.3・§6.2 も整合する。ただし §3.1 に旧称「開始後不完全」、§7 に非 canonical な「attempt 無効」が残る。[§3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:161) |
| 4 | **regressed** | protocol 本体の §0 と §9 は二段化され、第1段に生死確認成功 receipt は混じっていない。しかし README は「承認関門を全部」、runbook は「生死確認…がすべて揃うまで投入不可」とし、builder／生死確認にも読める循環を再導入した。[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/README.md:42)、[runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-runbook.md:992) |
| 5 | **closed** | `N=13,R=10` は確定で、生死確認の `P` は別 protocol の材料に限る。§8 も変更禁止、§10 も未計測事実の記録だけで、再導出分岐は残っていない。[§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:233) |
| 6 | **closed** | clean 検査、source-tree hash、compiler path/SHA-256/version、完全 argv、依存 head/clean、環境 hash を build 前 artifact の literal とし、第1段承認前に凍結する。builder 前の候補は一つに束縛できる。[§3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:141) |
| 7 | **partial** | NumPy 2.2.6 では記載順を再現し、`338491/400000 = 0.8462275`、`323211/400000 = 0.8080275`、丸めて `0.8462 / 0.8080` になった。ただし NumPy version が未固定で、`Generator` 自体に version compatibility guarantee がないため第三者完全再現はまだ保証されない。[§4.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:245) |

集計: **closed 3 / partial 3 / regressed 1 / 未対応 0**

## 回帰検査

| 検査 | 結果 | 根拠 |
|---|---|---|
| 自由度 | **PASS** | §1.1・§4.2・§5.2 はすべて `ν2=(N−1)(R−1)`。full は 108、reduced は 99。 |
| 状態名 | **FAIL** | 正式 5 状態の表同士は一致するが、§3.1「開始後不完全」と §7「attempt 無効」が残存。 |
| §5.3 の5行 | **PASS** | 順序評価。行1が状態、行2が gate、行3/4は `τ_L≤τ_U` により同時成立せず、行5が等号・残余を包含する。 |
| 脱落状態 | **PASS（名称残存を除く）** | 12 node 完全行列は row 3 に該当せず row 4 `terminal_reduced` に到達する。presence 表も推定必須。 |
| 測定後の選択余地 | **PASS** | 外れ値除去・補完・差し替えは禁止。retry は `pre_release_invalid` のみ、採用 attempt は投入順最初の valid/reduced に固定。結果用途も対応表で固定。 |
| 対象 diff | **FAIL** | README/runbook が二段承認を一括関門へ戻し、循環を再導入。 |
| 空白回帰 | **PASS** | `git diff --check` は無出力。 |

## 新規・残存所見

### blocker — 入口文書で承認循環が復活

- **主張:** protocol 内部では解けた循環が、README/runbook の新規記述で復活している。
- **根拠:** 「全部通ったとき」「生死確認…がすべて揃うまで投入できない」は、第1段の builder／生死確認も禁止する読みになる。
- **成果物影響:** 正式入口に従うと生死確認 receipt を合法的に生成できず、承認 ID と実験台帳の信頼性を失う。
- **提案:** 両文書を「builder＋生死確認は第1段、本走は第2段」と明示的に分ける。

### must-fix — round ドリフトの原因を識別したと断定している

- **主張:** 順序との関連は観測済みだが、壁時計・経過時間由来でないとは判定できない。
- **根拠:** 各 run の反復番号は開始後経過時間と共変し、2 世代は別日・別 binary。
- **成果物影響:** round 同期不要の根拠を実測以上に強く見せる。
- **提案:** 「順序位置との関連を観測したが原因は識別不能。壁時計共通外乱は吸収しない」に直す。

### must-fix — 非 canonical 状態名が残る

- **主張:** 「5 状態だけ」という契約と旧称が共存している。
- **根拠:** §3.1 の「開始後不完全」と §7 の「attempt 無効」。
- **成果物影響:** runner・receipt・presence validator が異なる状態文字列を実装し得る。
- **提案:** §3.1 は境界に応じた正式状態名へ、§7 は3つの無効状態を列挙する。

### must-fix — MC 実装 version が未固定

- **主張:** 現環境では再現するが、第三者の将来的な同一乱数列までは固定していない。
- **根拠:** NumPy `Generator` は version 間互換を保証せず、文書に NumPy version がない。
- **成果物影響:** assurance 台帳の exact count／4桁値が環境差で変わり得る。
- **提案:** `numpy==2.2.6` と `Generator(PCG64(810))` を literal 化する。

## 総括

**NO-GO。残 blocker 1 件。**

測定後に選べる解析・状態・attempt は見つからなかった。停止理由は、二段承認を導入した protocol と、今回追加された README/runbook の一括関門が矛盾し、承認循環が入口側で残っているためである。