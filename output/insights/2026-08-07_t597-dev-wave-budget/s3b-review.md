pytest と `tools/check_docs.py` は実行していません。以下は source と raw UTF-8 bytes の静的検査です。

## byte・checker 検算

計画中の置換対象は現行文書に各 1 件だけ存在しました。計数過程は次のとおりです。

| 変更 | UTF-8 計数 | 増減 |
|---|---:|---:|
| M08 before | 201 code points・LF 4 = 383 bytes | |
| M08 after | 72 code points・LF 1 = 124 bytes | −259 |
| O19 削除文 | 27 code points・LF 1 = 73 bytes | −73 |
| O01 `.done` | 101 → 167 bytes | +66 |
| 待ち手 | 94 bytes | +94 |
| 機構名検索 | 79 bytes | +79 |
| 解除条件 | 64 bytes | +64 |

したがって、捻出量は `383 − 124 + 73 = 332 bytes`、採録量は `66 + 94 + 79 + 64 = 303 bytes` で、プランの計数は正しいです。[mutation.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/mutation.md:49)、[operations.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:105)、[s2-plan.md:179](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:179)

| 文書 | 現在 | 変更後 | cap | 静的判定 |
|---|---:|---:|---:|---|
| core | 8,534 | 8,677 | 9,600 | pass |
| workers | 4,668 | 4,668 | 5,000 | pass |
| mutation | 3,674 | 3,415 | 3,750 | pass |
| operations | 8,311 | 8,398 | 8,400 | pass |
| 合計 | 25,187 | 25,158 | 25,200 | pass |

cap 総和も `9,600 + 5,000 + 3,750 + 8,400 = 26,750 ≤ floor(25,200 × 110 / 100) = 27,720` です。[check_docs.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:176)、[check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:254)、[check_docs.py:3342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:3342)

H2 は変更されず、削除対象 2 文の逐語は checker/test に pin されていません。required sections、dispatch 契約、allowlist、land literals、Codex-first literals の変更もありません。[check_docs.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:376)、[check_docs.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:425)、[check_docs.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:509)、[test_check_docs.py:4707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_check_docs.py:4707)

採録候補はいずれも発火 artifact を書けます。

| 候補 | 発火 artifact / ID | 配置先の読了 |
|---|---|---|
| (a) `.done` | [s2-plan.done](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/logs/s2-plan.done)、[worklog:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/archive/worklog-phase3-0805-217-218.md:33) | O01 は Codex 再投入前に読まれる |
| (b) 待ち手 | [land_loop.log](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/logs/land_loop.log)、[事故記録:8](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-05-background-waiter-duplication.md:8) | 下記 B-2 のとおり不整合 |
| (c) 機構名検索 | [T-419 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/output/insights/2026-08-07_t419-iii-withdrawn-ruling/README.md)、[worklog:2181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/worklog.md:2181) | S01 は段1必読 |
| (d) 解除条件 | [calibration artifact](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json)、計測 ID `892707.nqsv` [handoff:51](/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-impl-reraise.md:51) | S01 は段1必読だが、B-3/B-4 が残る |

## 所見

### B-1

- **主張** — P1 は、供給タスク T-597 の起動だけで需要タスク T-592 の採録まで同梱できると解釈しており、起動 scope を越えている。
- **根拠** — 静的事実: 起動引数は T-597 の予算捻出だけです。[handoff:7](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t597-budget.md:7) T-592 は規約採録、T-597 は後発の捻出先として別々に起票され、現在も双方が独立に持ち越されています。[worklog archive:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/archive/worklog-phase3-0806-263-264.md:798)、[worklog archive:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/archive/worklog-phase3-0806-271.md:445)、[current worklog:3026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/worklog.md:3026) spool の起票元も別 wave です。[FOLDED.md:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/spool/FOLDED.md:412)、[FOLDED.md:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/spool/FOLDED.md:423)
- **深刻度** — blocker
- **成果物影響** — `DW-STOP` の scope・所有不整合に当たり、T-597 の成果として T-592 を閉じると未承認の契約義務を land する。[core.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:19)

### B-2

- **主張** — 待ち手規約を DW-O01 に置くと、発火実績である land-loop 等の非 Codex producer では読まれず、採録が空振りする。
- **根拠** — 静的事実: O01 の条件 dispatch は「codex subprocess 起動直前」だけです。[dev-wave.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:84) 段7・段9にも O01 はありません。[dev-wave.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:72) 一方、73 本残留の発火 artifact は `land_loop.log` / `land_loop2.log` で、Codex subprocess ではありません。[ruling inbox:11](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-05-background-waiter-duplication.md:11) プランは同文を O01 へ置きます。[s2-plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:112)
- **深刻度** — blocker
- **成果物影響** — land・supervisor 待機では規約が読まれず、同条件の待ち手大量残留と通知噴出を再び許す。

### B-3

- **主張** — 候補 (d) は発生元 T-529 wave がまだ敵対裁定前の live candidate であり、T-597 が先に契約化してはならない。
- **根拠** — 静的事実: T-529 handoff は段2完了後に段3投入中で、本文自身も「候補」「T-597 従属の可能性」としか記録していません。[handoff:8](/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-impl-reraise.md:8)、[handoff:40](/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-impl-reraise.md:40) プランはこれを確定義務として工程4で採録します。[s2-plan.md:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:143)、[s2-plan.md:169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:169)
- **深刻度** — must-fix
- **成果物影響** — T-529 の段3/4で候補が棄却・変更されても、先取りした stale 義務が全 wave を拘束する。

### B-4

- **主張** — 候補 (d) の64-byte 文は、元候補の核心である「今回の裁定が各解除条件へ効くかの対応づけ」を落としており、意味等価ではない。
- **根拠** — 静的事実: 元候補は「条文単位の棚卸し」と「現裁定を各条件へ対応づける」の2動作です。[handoff:42](/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-impl-reraise.md:42) 計画文は前者だけです。[s2-plan.md:147](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:147) 計数: 元文を一行化すると121 bytes、計画文は64 bytesで57 bytes欠落し、逐語復元なら `25,158 + 57 = 25,215` となり aggregate gate を15 bytes超えます。
- **深刻度** — must-fix
- **成果物影響** — 条件一覧だけ作って裁定の効きを確認せず解除でき、元事故の scope 誤判定防止義務が空振りする。

### B-5

- **主張** — M08 の tool pointer 化は、M05 が許す独自 harness にも同じ `-rf`・抽出・fail-closed 意味論を課すことを明示しておらず、現行本文との等価性が曖昧である。
- **根拠** — 静的事実: M05 は独自 harness を明示的に許可しています。[mutation.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/mutation.md:31) 現行 M08 は主体を一般の `harness` として全義務を課します。[mutation.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/mutation.md:51) 計画文は `tools/mutation_harness.py` だけを正本とします。[s2-plan.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:20) 「harness は同 tool と同等」とする形でも136 bytes、現案との差は12 bytesで、変更後合計25,170に収まります。
- **深刻度** — must-fix
- **成果物影響** — 独自 harness が失敗 node 抽出や node 0 件の停止を省いても、契約違反か判定できず変異台帳を誤認する。

### B-6

- **主張** — 需要一覧は少なくとも3性質を取りこぼしており、c/dへ143 bytesを配る優先順位は成立していない。
- **根拠** — 静的事実: 段8済みの T-300 には「投入と完了待ちを対にする」と「変異中に tree を書かない」という、2時間空転・再発 near miss に基づく予算見送り候補があります。[T-300 handoff:76](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t300-login-headroom.md:76) また、T-244 には「生存なし MISMATCH では変異を変えず、実測集合へ訂正し初回を erratum として再走する」という予算見送り候補があります。[worklog:514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/worklog.md:514) 計画は別候補として run-script だけを挙げ、これらを列挙も見送り判定もしていません。[s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/s2-plan.md:163) 332 bytesを回収して元裁定の残存 (a)(b) 160 bytesだけを入れた時点では `25,015 / 25,200`、配分可能量は185 bytesあります。
- **深刻度** — must-fix
- **成果物影響** — zero-waiter、変異中 tree 編集、MISMATCH 誤処理の3義務を比較せずc/dへ予算を先払いし、「既知需要を採録・見送りした」という記録が虚偽になる。

## P3 の判定

P3 は攻撃に耐えています。D97 は O11 の部分機械化に留まり、後発 D186 が未機械化の3経路と回収可能量0 bytesを明記しています。[D97:4305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/decisions.md:4305)、[D186:9058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/decisions.md:9058) O10 には後発の実発火もあり、D94 の「発火なし」条件を満たしません。[worklog archive:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/archive/worklog-phase3-0806-256-261.md:894) よって本 wave に実施可能な H2 削除はなく、過剰自制でもありません。

P1 は棄却、P2 は B-5 修正付き、P3/P4/P5 は維持可能です。

## 総括

- blocker: **2件**
- 捻出量の再計算値: **332 bytes**
- 計画どおりの変更後値: **25,158 / 25,200 bytes**。3数値 gate は静的には pass
- checker/literal pin: 計画差分との直接衝突なし
- 判定: **NO-GO**

T-592 同梱の明示承認、待ち手規約の wave-start 必読節への再配置、live な (d) の除外または発生元確定、M08 の独自 harness 等価性、欠落需要の再配分を段4で解消するまで、そのまま実装してはいけません。