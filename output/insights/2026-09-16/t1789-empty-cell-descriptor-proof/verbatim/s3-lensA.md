## 所見一覧

**plan の条件は、再現済みの complete＋cells=[] を塞ぐ。正規 producer が発行する receipt の新たな誤拒否は、静的検査では見つからない。** ただし「実行 descriptor 不在の receipt 全般を排除」「将来の certified 選択への流入まで実証」という説明は広すぎる。

以下、`V` は [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/campaign/s8c_acceptance_receipt.py)、他のファイル名は当該 worktree 内を指す。real / refuted は各懸念への判定。

| 懸念 | 判定 | 根拠 |
|---|---|---|
| v5 で partial に変更し、observed を残せば逃げられる | **refuted** | V:1715–1727 が status 対応と report hash を検査する |
| cells の型変更・複数化・descriptor 欠落で新条件を避けられる | **refuted** | V:1461–1481 が既に拒否する |
| 新条件は既存 gate の恒真な言い換え | **refuted** | 現在受理される C2/C3 が新条件で拒否される。expected digest 一致と descriptor 存在は別条件 |
| partial を「実行していない」と解釈できる | **real：解釈が誤り** | terminal-failure にも observation-start がある。test_s8c_acceptance_receipt_v2.py:403–422 |
| legacy の status も v5 同様に束縛される | **real：束縛されない** | V:918 は非空文字列のみ。attempt 検査の呼出しは v5 限定、V:2075 |
| 正規 partial / no-build を新たに拒否する | **refuted** | 新条件は complete のみ。producer の complete は非空 workload に対応した cell を必要とする |
| DW-G05 が将来の成果物汚染を実証している | **real：過大な一般化** | 現 checkout に certified-selection consumer はなく、certifying 検査後にも別条件が残る |

## brief の誤り

1. **P3 の対応関係は正しいが、「実行を名乗らない」は不正確。**  
   v5 では、registry の履歴・prefix・事前登録 projection を検査し、receipt trials と projection の集合を一致させた上で、各 unit に observed / terminal-failure の最終行をちょうど1件要求する。そこで `complete→observed`、`partial→terminal-failure` と report hash を照合する（V:1607–1727）。  
   これは「完了・観測成功を名乗らない」という保証であり、実行開始や途中までの実行を否定しない。plan:5 の訂正は妥当。

2. **P1 の status 式は説明が不足しているが、登録済み producer に関する結論は正しい。**  
   driver は件数一致・fatal_error 不在に加えて stop_reason と build admission を条件にする（p3_autonomous_workload_trial.py:3816–3834）。空 selected の排除は式単独からは導けず、登録 workload の singleton 制約が必要（trial_registry.py:3764、3961–3967）。これらを合わせれば complete＋cells=[] は正規経路にない。

3. **P2 の「production shape」の実測範囲は限定すべき。**  
   P6 テストは最初の trial が1-cell partial、残り5件が空-cell partial で、production の受入処理から receipt を発行する。しかし最後に行うのは **parse** であり、公開 verifier / capability の検証ではない（test_trial_registry.py:3005–3030）。  
   plan の P はその公開経路を検査するが、fixture の status を変更した合成例であり、fatal_error 経路全体を再現するものではない。親の検証結果では、この2種類の証拠を区別する必要がある。

4. **DW-G05 の将来影響は断定できない。**  
   [brief:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/s1-brief.md:61) の「certifying を有効化する世代で…選択が…乗る」は、今回の証拠を超える。`build_accepted_report` は現 checkout に certified-selection consumer がないと明記し、certifying 検査後にも campaign 対応、admission、certified commit evidence、E1 epoch を要求する（layer3_report.py:911–982）。probe は存在しない campaign を渡しており、これらの通過を調べていない（probe_t1789_counterexample.py:135–139）。  
   正確な影響は「現在の verifier と v5 capability の受理集合に不正な complete 主張が残る。現在の certified 成果物への到達は確認されていない」。

5. **「全 case が do_build=False」は C4 を除く必要がある。**  
   brief:15 の表現に対し、probe:107–110 は C4 を明示的に True に変更している。C2/C3 の根拠を損なわないが、実測範囲の記述として訂正が必要。

## 修正後も残る形

| 入力形 | 修正後の扱い・T-1789 該当性 |
|---|---|
| complete＋cells=[]＋C02 | 新条件で拒否。再現済み欠陥を塞ぐ |
| cells が list でない／複数／1件だが descriptor がない | 既存 V:1462–1469 で拒否 |
| descriptor が残り、digest が矛盾する | status に関係なく V:1476–1480 で拒否 |
| v5 の `completed`、`Complete` 等 | V:1715–1723 で拒否。対応表にない文字列は最終 terminal と一致しない |
| v5 partial＋observed | 同じ status 対応検査で拒否 |
| v5 partial＋terminal-failure＋cells=[]＋C02 | 残る。D519 が許容する部分 report。**完了・観測成功の偽装という意味では当たらない** |
| legacy partial＋cells=[]＋C02 | 残る。status は registry に束縛されないが、current capability には届かない |
| legacy の任意の非空 status＋cells=[]＋C02 | 残る。**任意 status を拒否できない点は real**。ただし `completed` 等を有効な成功表記とする producer / consumer は確認できず、再現済み complete 欠陥と同一とは断定しない |

したがって、今回確認した範囲に追加で塞ぐべき v5 の抜け道はない。partial も含めた「descriptor 不在の実行宣言すべて」を欠陥と呼べば残るが、それは指定された正例と D519 に衝突する。

**P4 の共通適用は妥当。ただし根拠は版分岐削減ではない。** legacy v2 にも A2/A3/B2 の反例があり、complete 主張と descriptor の関係を同じ既存 bytes で検査できる。D1757 が問題にした、失われた campaign 現物の追加要求とは異なる。一方、legacy の status 全般の信頼性まで修復したとは書けない。

**D949 の冗長照合には当たらない。** V:1336 の expected digest 一致は、V:1464 の descriptor_proven=False と両立する。C02 が残れば V:2039 の gate も通る。C2/C3 の既存 verified という実測は、まさにこの非含意を示している。

## 正規形の誤拒否の有無

**新条件による誤拒否は見つからない。**

- **fatal_error＋partial＋cells=[]、no-build：維持される。**  
  `_partial_report` はこの形を作り、P6 はその受入を検査する（test_trial_registry.py:1435–1449、3008–3030）。新条件の complete に該当しない。no-build の cross-binding leaf は status を含まないため、plan の helper 呼出し順にも問題はない（autonomous_trial_completeness.py:4165–4188）。

- **lifecycle_terminal_status=indeterminate：新たな拒否ではない。**  
  driver は attempt を not-consumed にする（p3_autonomous_workload_trial.py:4481–4494）。この形は既に formal acceptance の拒否対象であり、そのテストもある（test_trial_registry.py:3033–3057）。正規に発行される受入 receipt の正例として数えるべきではない。

- **do_build=True＋fatal_error＋cells=[]：既に receipt 発行前に拒否される。**  
  standalone completeness には例外経路があるが（autonomous_trial_completeness.py:5054–5078）、trial_registry の受入は build の非空 cells を要求する（trial_registry.py:6208–6213）。v5 verifier でも cross-binding が空 cells を拒否する。今回の変更に起因する互換性問題ではない。

- **complete の正規 no-build：維持される。**  
  no-build は descriptor 不要という意味ではない。正規 complete は登録 workload の cell を持つため、descriptor 証明が成立して新条件を通る。

## scope 外候補

**legacy が任意の非空 status を受理する点**は、静的に確認できる別課題（V:918、2075）。今回の実装へ値域 gate を追加することは推奨しない。成功表記の意味・互換性方針を別途定義せずに一般化すると、再現された欠陥だけを修正する scope を超える。

partial の実行履歴や証拠削除の過去まで証明する追加検査については、今回新たな実在反例を確認していないため提案しない。

## 総括

**plan の1ブロック追加は支持する。** 再現済み complete＋空-cell の受理を狭め、既存 mandatory-reasons の診断順と正規 partial を維持する。

親側では、P3 を「完了・観測成功の主張」に限定し、DW-G05 の将来影響の断定を修正すること。正例の報告では、production 発行・parse と公開 verifier / capability 通過を区別すること。

ファイル変更・テスト実行は行っていない。修正後の通過・拒否は静的判断であり、親の実測で確定する。