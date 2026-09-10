結論は **NO-GO** です。18 block の数値、seed、巡回、欠測、H1からH3の判定自体は再現しましたが、事前登録上の compiler identity が実成果物に存在せず、consumer に2件の受理集合漏れがあります。

## 所見

### 1. Must-fix: compiler の「完全 identity」が記録されていない [恒真ゲート][テスト代表性]

- 事前登録は compiler の完全 identity の一致を要求しています。[preregistration.md:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/docs/backoff-policy-performance-preregistration.md:148)
- 正誤表も全18 block で compiler identity が一定だと要求しています。[erratum-1.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/docs/backoff-policy-performance-preregistration-erratum-1.md:69)
- しかし producer は `compilers_for_current_site()` の返す要求名だけを記録し、実成果物は全件 `"cc":"gcc"`、`"cxx":"g++"` です。[producer.py:4203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:4203) [rep0 JSON:61](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2417-policy/t2417a02/policy-perf-rep0-0_982986.nqsv.json:61)
- consumer は非空文字列だけを検査します。[analysis.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:296)

反例は、各 bnode の PATH が別バージョンの `g++` を解決しても、全件が文字列 `"g++"` を記録すれば通ることです。binary の block 間一致は正誤表で要求されないため、そこで検出することもできません。

具体的影響は、18 block を同一 compiler identity として受理した根拠が不足し、`analysis_status=complete` と H1/H2/H3 を「事前登録へ完全適合した判定」とする部分です。数値計算そのものは壊れていませんが、受理集合が登録条件より広い状態です。

- scope: 既存 producer、consumer、README の完了主張なので scope 内。
- 最小修正: 当時の全18 nodeについて、既存の同時点証拠から resolved path、version、binary digest を束縛できるならそれを明示的に結合する。できなければ frozen JSON は変更せず、README/worklog で構造適合と仮説判定を条件付き記述へ降格する。新測定は scope 外。
- real 根拠: 欠けているのは仮想的な将来 field ではなく、現存18 JSONそのものです。

### 2. Must-fix: `median_tps` が生の `throughputs` と結合されていない [恒真ゲート][テスト代表性]

consumer は `median_tps` と `missing_reason` だけを読み、`throughputs` を検査しません。[analysis.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:342)

一方 producer は、`throughputs` から median と欠測理由を導出しています。[producer.py:4517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:4517) テストには、`median_tps` を欠測へ変えながら元の正値 `throughputs` を残し、それを正常な欠測として受理させる例まであります。[test_analysis.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/tests/test_backoff_policy_performance_analysis.py:965)

反例:

- `throughputs=[1000000]` のまま `median_tps=None` と理由を付けると、その点を不必要に `n-insufficient` にできる。
- 1 block の `median_tps` だけ10倍すると、raw sampleを変えずに点推定の平均 log 比を `ln(10)/18` だけ動かせる。

受理集合と欠測判定、点推定、CI、仮説判定へ直接影響します。ただし既存1296行はすべて `throughputs` が1要素で `median_tps` と一致し、欠測理由もありません。保存結果の改変が起きているという疑いは refuted です。

- scope: 現 consumer と対応テストの局所修正で scope 内。
- 最小修正: `reps_per_job=1` に対応して producer の導出規則を consumer でも検査し、不整合を `artifact-invalid` にする。
- real 根拠: 公開 consumer が上記反例を受理し、テストがその不整合を正例化しています。

### 3. Must-fix: 実行順の回帰を consumer と単体 fixture が検出できない [恒真ゲート][テスト代表性]

事前登録は `rep_index mod 6` の実行順を構造条件にしています。[preregistration.md:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/docs/backoff-policy-performance-preregistration.md:127)

consumer は行を座標辞書へ入れて集合だけを確認するため、`cells` の実行順を捨てます。[analysis.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:488) さらに単体 fixture は全 block を常に p0、p1、p2 の順で生成し、rep 1以降の登録 permutation を表現していません。[test_analysis.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/tests/test_backoff_policy_performance_analysis.py:269)

反例は rep 1 の行列を p0、p1、p2 の順で出し、metadata の `cell_order` だけ p0、p2、p1 とするものです。現 consumer と単体 fixtureでは通ります。producer の loop が固定順へ退行しても統合テストが検出しません。

順序均衡と213回ずつの一次持越しという設計根拠に影響します。ただし既存18 JSONの実行行列はすべて `workload -> threads -> 登録 permutation` と一致しました。現在の18 blockへの影響は refuted です。

- scope: 登録済み順序を守る既存 producer/consumer/testなので scope 内。
- 最小修正: `cells` の座標列を登録順と照合し、fixture も各 block の permutation 順で生成する。
- real 根拠: 現 fixture 自体が5種類の非登録行順を正例として使っています。

### 4. Must-fix docs: H3 の機序説明が raw abort 値を越えている [捏造/幻覚][ドリフト]

README は「abort がほぼ無い read-heavy」の予測が逆向きに反証されたとし、abort が少ないほど待ち時間乖離が大きいという候補を述べています。[README.md:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/output/insights/2026-09-08_t2417-policy-arm-performance/README.md:114) [README.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/output/insights/2026-09-08_t2417-policy-arm-performance/README.md:118)

しかし read-heavy の raw `abort_rate` は次の範囲でした。

- p0: 1.91%から15.40%、平均8.94%
- p1: 1.36%から5.56%、平均3.69%
- p2: 1.57%から12.23%、平均5.91%

rep 0、48 threadsだけでも p0 は15.35%です。[rep0 JSON:7288](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2417-policy/t2417a02/policy-perf-rep0-0_982986.nqsv.json:7288) [rep0 JSON:7315](/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2417-policy/t2417a02/policy-perf-rep0-0_982986.nqsv.json:7315)

正式な H3 predicate、すなわち read-heavy 8点の p0/p1 等価は確かに rejected です。refuted なのはその判定ではなく、「実際の無abort域で条件付き予測を反証した」という機序解釈です。事前登録自身も `abort_rate` は生値を記録するだけで解析しないとしています。[preregistration.md:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/docs/backoff-policy-performance-preregistration.md:246)

同様に「常に逆へ進むのは破滅的」は最大 +249% を全体へ広げています。[README.md:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/output/insights/2026-09-08_t2417-policy-arm-performance/README.md:127)

- scope: README/worklog の局所訂正で scope 内。
- 最小修正: 「事前登録した read-heavy 等価予測が棄却された」と限定し、abort 値は低めだが非ゼロだったことを併記する。clamp は未同定の候補のままにする。「破滅的」は balanced・30 threads の観測点へ限定する。
- real 根拠: raw abort 値と現在の説明が一致しません。H1/H2/H3 の形式判定への影響はありません。

### 5. 軽微: 等価域の百分率表現が非対称性を隠している [ドリフト]

README は `+-ln(1.03) = +-3.00%` と書きます。[README.md:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/output/insights/2026-09-08_t2417-policy-arm-performance/README.md:68)

反例は負側で、`exp(-ln(1.03))-1 = -2.9126%` です。正確な比の区間は `[1/1.03, 1.03]` です。

- 影響: 表示だけ。code、受理集合、判定への影響なし。
- scope: README 1行の scope 内修正。
- 最小修正: 「log scaleで対称、比では -2.91%から+3.00%」とする。
- real 根拠: 数式上の不一致です。

## 確認できた事項

- 18 JSON、rep 0から17、18 hostname、1296座標、欠測ゼロを確認。
- seed は導出式と逐語表の両方に一致。全JSONの実行行順も登録6 permutationに一致。
- 保存された18 input SHA は原JSON bytesと一致。
- 全72点を raw `median_tps` から独立に再計算し、保存済み点推定とCIに一致。H1 accepted、H2 rejectedの反例は write-heavy・42 threads の p2/p1、H3 rejectedの反例はread-heavy全8点で一致。
- preregistration、erratum、analysis-result の frozen bytes は導入時から不変。
- 測定 driver/PBS SHA は `deb1f0643` の bytesと一致し、現在コードのSHAとは異なる。READMEは測定 commitを別に記載しており、既存測定と現在コードの同一視はしていない。
- merge の acceptance ledger は両親の exact union 22346件、shared値衝突ゼロ、脱落ゼロ。
- 親固有テスト名の脱落は、3契約用テストがmain側の4契約用テストへ置換された1件だけで、意味上は拡張。T-2417 producer/consumer testsとmain側nonmonotonic経路の双方が残っています。
- 未認証隔離は raw 全件で `headline_eligible=false`、`correctness_status=uncertified`。既存 certification consumerも `performance_contract` を拒否します。

## 総括

**NO-GO。**

Must-fix は compiler identity の実証不足、`median_tps` と raw sample の未結合、実行順を検出できない consumer/test、H3機序説明の訂正です。凍結18 JSONや既存 analysis-result を書き換える修正は不可です。

未実走: pytest、`run_tests.py`、docs checker、provenance checker、公開解析関数の再実行は行っていません。実施したのは read-only の静的検査と raw 値の独立再計算だけです。

残余限界: 3腕は未認証、単一環境、単一protocol、単一record数、自動撤回なしです。また同一主体が文書とgateを同時変更できる限界は残りますが、これは既に明記済みであり、仮想リスク向けの新gateをmust-fixにはしていません。