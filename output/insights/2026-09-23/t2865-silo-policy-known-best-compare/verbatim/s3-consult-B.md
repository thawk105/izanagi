## 所見

1. **must-fix — 3% を「既知最良に勝った」と断定しない。** 根拠: [brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:18) の判定は、同 job の参照 3 本の中央値の最大との比較としては正しい。一方、段階 D の abort0 中央値は job 間で 5.1% 動き、3% 床は Pegasus で未較正である（[README.md:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md:70)、[同:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md:109)）。結果 JSON の 5 rep から計算すると、中央値からの最大偏差は abort0 の job 0 で −7.36%、job 5 で −7.26%。**影響:** 3% を超えた点数を確かな勝利数として示すと、段階 E の判断材料を過大評価する。**代案:** 参照 3 本それぞれの中央値と比、最大参照に対する比を別掲し、`>1.03` は探索的な目印と明記する。欠測した参照が一つでもあれば「3 本中の最良」比とその判定は null とし、取得できた参照との個別比だけ残す。

2. **must-fix — 16 点の最大値と再測 1 点の意味を限定する。** 根拠: [brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:3) は超過点数を完了指標にし、[同:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:20) は最大比の 1 点だけを再測する。段階 D 自身も最大選択の有意水準を保証していない（[README.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md:109)）。**影響:** 最大比は上振れしやすく、1 点の再測から残る 15 点の再現性や「勝ち点数」は確定できない。**代案:** 初走の超過点数は探索的観測値として報告する。再測は「最大比の点を別 job で一度確認した」結果として別掲し、全点の再現判定に使わない。8 job の小比較だけでも依頼は満たすため、再測は省略可能。

3. **should — 巡回順の効能を狭く記す。** 根拠: 段階 D は候補 2 点を先に、abort0 を末尾に置いた（[silo_policy_recon.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/campaign/silo_policy_recon.py:35)）。[brief.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:19) の 6 方策×8 job の巡回では、各候補は一つの位置で一度しか走らず、個々の候補と位置の交絡は消えない。**影響:** 順序効果を除去済みと書くと、近接した比の解釈が強すぎる。**代案:** 巡回は参照方策の位置を分散する工夫として採用し、各 job の実行順を結果に残す。段階 D の絶対値との直接比較は行わず、新しい同 job の参照比で判断する。

4. **must-fix — 見積りの下限と費目の根拠を直す。** 根拠: 段階 D の 3 方策 428〜436 秒、4 方策 506〜564 秒（[README.md:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md:88)）からの 6 方策約 650〜830 秒、8 job 約 1.44〜1.84 node 時間は概ね妥当。ただし [brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:21) の費目を足すと、再測込みの下限は **約 2.24** node 時間で、記載の 2.1 にはならない。変異の 2,029 秒は待ち行列込みの上限値で、受入 0.25 時間には同記録内の実測根拠がない（[README.md:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md:96)）。**影響:** ユーザーが承認する計算量の内訳を誤認する。**代案:** 再測あり・なしを分け、焦点走、変異、受入の根拠と不確実性を明示して投入前に確認する。参照の verify 省略は規律 2 に反し、bench rep 削減は段階 D との比較可能性と中央値の安定性を損ねるため採らない。

5. **should — 完了文を判断材料の射程に合わせる。** 根拠: 裁定は段階 E に進むかを**結果を添えて人間が改めて判断する**もの（[D2235-item7.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/verbatim/D2235-item7.md:5)）。固定 16 点が未調整で負けても軸の否定ではない（[同:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/verbatim/D2235-item7.md:9)）。**影響:** [brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-silo-small-compare/brief.md:3) の「3% 超えた点の数」だけでは、僅差、欠測、参照間の差、未調整という限定が落ちる。**代案:** insight に各参照との比、最大参照との比、超過点数、欠測・除外、再測をした場合の結果、固定部分空間という限定を載せ、継続判断はユーザーへ返す。

## brief の前提の判定

- **P1: 要修正。** 同 job の最大参照は問いに合うが、3% は未較正で、超過点数は探索的結果に限る。個別参照値と null を併記する。
- **P2: 要修正。** 巡回は参照の位置を分散するが、候補ごとの位置効果は消せない。段階 D との直接的な値の比較は避ける。
- **P3: 要修正。** 1 job の追加は費用を明示すれば小比較の補助確認として扱えるが、最大 1 点の再測は 16 点の再現判定にならない。省略も妥当。
- **P4: 要修正。** 6 方策と 8 job の単価は概ね妥当。総額の下限、待ち行列込みの変異時間、受入費の根拠を訂正する。

## 削れるもの

新しい phase 文書、agent role、投影 JSON、一般化した比較基盤、仮想リスク向けの gate・台帳・変異 matrix は不要。`compare` と `fixed10` は既存 driver 内の値として足り、新しい集計 subcommand も既存の集計関数を拡張すればよい。必要なのは固定 10 µs の**実適用確認**、6 方策の実行と両 verify・trace0・5 rep、同 job 比と欠測を読める集計、変更箇所の焦点 test である（現行の stock build は `BACK_OFF` しか渡さない: [silo_policy_coverage.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/campaign/silo_policy_coverage.py:362)）。

## 総括

**adopt_with_conditions。** must-fix は、①3% 超を確証ではなく探索的結果として扱う、②16 点の最大選択と再測 1 点の射程を明記する、③計算見積りの下限と費目を訂正する、の 3 件。これを直せば、8 job の同 job 比較は段階 E の人間判断に有用な小比較になる。