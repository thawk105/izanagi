## 検査前提

指定された 8 ファイルだけを静的検査した。pytest、実測、書込み、commit は行っていない。

## 1. 認証対象の genome が主判定の実行体と一致しない

- 判定候補: **real、最重要**
- 成果物影響: receipt は `BACKOFF_TRACE=0` かつ terminal define なしの genome を certified とする一方、主解析は `BACKOFF_TRACE=1` かつ terminal 期限ありの binary を読むため、主判定を correctness-qualified へ昇格できない。

現行 certification は `genome_for(cell)` を引数なしで呼び、backoff trace と terminal define を含めない。段2プランも seed を渡す変更しか予定していない。対して cohort 2 解析器が要求する genome は `BACKOFF_TRACE=1` と `BACKOFF_TRACE_TERMINAL_US=5000000` を含む。terminal は記録だけでなく更新、LCG、割当を止める契約なので、単なる無害な表示差とも言えない。

規律1が要求する verifier 用 build と測定用 build の分離は守る必要があるが、そこから異なる CC genome の直列性を一般化してよいとは導けない。cohort 2 の exact config に transaction trace を加えて認証するか、両 genome 間の直列性意味互換を別の正本で証明しなければならない。

根拠: [probe.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:691)、[probe.py:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3330)、[analysis.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:282)、[preregistration.md:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:147)、[preregistration.md:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:170)、[stage2-plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:103)

## 2. anomaly 0 は現行 gate が検証していない

- 判定候補: **real**
- 成果物影響: target result に anomaly を残したまま `complete=true`、`certified_requests=24`、および「anomaly を1件も観測しなかった」という claim を持つ receipt が生成可能であり、レポートの anomaly 0 も虚偽になりうる。

`_validate_target` は aggregate、verdict、`certified`、integrity、stats を検査するが、target の `anomalies` が空であることを要求しない。したがって既存の certified JSON の target result に anomaly を追加し、`stdout` と `verifier_json` を同じ JSON に更新する変異は、静的に見る限り拒否されない。group aggregation は verifier を再実行せず、その自己整合した記録を読むだけである。

少なくとも `result["anomalies"] == []`、aggregate anomaly count 0、正規化 row と receipt の `anomaly_count=0` を全層で要求し、非空 anomaly の変異テストを追加する必要がある。段2テスト計画にはこの負例がない。

根拠: [probe.py:1851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1851)、[probe.py:2353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2353)、[probe.py:2637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2637)、[brief.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:14)、[stage2-plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:242)

## 3. performance artifact 束縛は同じ field 名のまま別の意味になる

- 判定候補: **real**
- 成果物影響: seed X の receipt の `performance_artifact` が default-seed の性能値を指すため、consumer は「seed X の認証済み実行体で得た性能値」と誤結合でき、certified 選択、レポート、台帳の binary 対応が壊れる。

現行束縛は performance row の default seed と default-seed genome を要求する。段2案はこの検査を残したまま certification seed だけを別にする。その結果、束縛が保証するのは repo、patch、cell、extime、予定する thread の共通性までであり、同一 genome、同一 seed、同一 binary で測定したことではなくなる。しかも receipt field は引き続き `performance_artifact` で、schema v3 も維持する計画である。

代案の得失は次のとおり。

- seed ごとの performance artifact: exact binary と性能値の対応には最強。ただし新しい trace-disabled 測定が必要で、この wave の scope を超える。また cohort 2 の局所 ITT は性能 headline ではないため、それだけで主判定を認証しない。
- 束縛を外す: correctness receipt と性能参照の誤結合を完全に避けられる。一方、選定元の provenance は receipt 外のレポートへ移る。
- field を分ける: 最も妥当。`certified_execution_identity` と `selection_reference_performance_artifact` を別にし、両 seed、binary、`same_execution=false` を明記して schema を上げる。将来 exact な性能主張を行う場合だけ seed 別 artifact を要求する。

段2裁定点1は現状の文言では撤回すべきである。

根拠: [probe.py:2024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2024)、[probe.py:2651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2651)、[stage2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:85)、[stage2-plan.md:382](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:382)、[brief.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:63)

## 4. thread 24 を既存4 cellすべてへ開く案は過剰な widening

- 判定候補: **real**
- 成果物影響: cohort 2 に不要な `tuned@24` と `cw-as-dyn@24` が新規 certified receipt の受理集合へ入り、台帳上の認証範囲が依頼より広がる。

投入格子が必要とする24 thread は p1 と、任意の波3における p2 である。ところが段2裁定点3は、定数の意味を分裂させたくないという実装上の都合で4 cellすべてへ24を開く。これは正しさ gate の受理集合を研究目的以上に広げる理由にならない。

cell 別閉表にすべきである。少なくとも tuned と既存 dynamic は48のまま、p1は24/48、p2は事前登録 seed と24/48の直積に限定できる。定数が一つであることより、受理集合が必要最小であることを優先すべきである。

根拠: [stage2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:11)、[stage2-plan.md:111](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:111)、[stage2-plan.md:384](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:384)、[brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:46)、[CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/CLAUDE.md:67)

## 5. claim 案Bは順序を API で強制していない

- 判定候補: **real、設計証明の欠落**
- 成果物影響: 閉表外 seed または thread から「それらしい exact claim」を自己生成して比較できる実装になると、row、group、published receipt の受理集合が閉表外へ広がる。

次の順序は危険である。

```python
threads = document["threads"]
seed = document.get("step_policy_seed")
expected = _certification_claim(cell, threads, seed, allow_legacy=False)
if document["allowed_group_claim"] != expected:
    reject()
# thread と seed の閉表検査が後、または欠落
```

この場合、thread 25 や13番目 seed でも、同じ不正値から期待 claim を作れば全文 equality は通る。段2の「near miss なら claim が異なる」というテストは文字列補間を証明するだけで、生成関数が不正軸を拒否することを証明しない。

正しい順序は、raw literal 検査、parse、singleton、cell 別閉表 membership を完了し、検証済み `CertificationAxes` を構築してから `_certification_claim(axes)` を呼ぶことである。row、group、published の各 consumer も、文書値から先に同じ閉表検証を行う必要がある。`allow_legacy` は汎用 claim generator の引数に置くべきではない。

根拠: [stage2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:63)、[stage2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:79)、[stage2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:119)、[stage2-plan.md:246](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:246)、[probe.py:2218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2218)

## 6. legacy branch の直接 CLI bypass は反証可能だが、形だけの legacy 判定は抜け道になる

- 判定候補: **直接の seed 省略 CLI bypass は refuted、発行時点を識別しない互換分岐は real**
- 成果物影響: exact な既発行 digest ではなく `(p2,48,default seed,old claim)` という形を legacy と呼ぶと、後から作られた同形の receipt も再受理され、台帳の「既発行 receipt」参照が新規 artifact へ置換可能になる。

新規 request contract が先に実行され、p2 の seed 必須と12 seed membership を要求し、`allow_legacy=True` が published receipt 検証からしか呼ばれないなら、利用者が CLI flag 一つで default seed を通す経路は閉じる。

ただし「legacy」は値の組ではなく発行済み artifact の同一性である。attempt id は安全な文字列であることしか検証されず、receipt path も global certify prefix 配下であればよい。したがって同じ attempt id と旧 claim を後から再利用することを、形だけでは区別できない。

既発行 group receipt と24 row の絶対 path、SHA-256を固定 allowlist にするか、live `_certify_main` から到達不能な専用 migration validator に分離すべきである。固定 digest を持てないなら、再受理を止め、過去の発行事実だけを台帳に保持する方が安全である。

根拠: [stage2-plan.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:15)、[stage2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:97)、[stage2-plan.md:181](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:181)、[probe.py:1421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1421)、[probe.py:2684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2684)、[probe.py:2890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2890)

## 7. mixed seed/thread の受理は閉じられるが、group namespace は束縛されていない

- 判定候補: **mixed-axis acceptance は refuted、path/attempt alias は real**
- 成果物影響: 異なる seed/thread の混在なら receipt は生成されないが、同一軸の別 path 群や軸と食い違う attempt 名を参照した receipt は受理可能で、レポートと台帳の path 表示が実軸を誤伝達する。

3層の評価は次のとおり。

- row: document の thread、seed、genome を先に閉表検証するなら、別軸を claim で隠せない。
- group: 24 row から `(cell,threads,seed)` の singleton を作る計画なら、混在は reject される。
- published: receipt 軸と全24 row を再比較する計画なら、出版後の軸 drift も reject される。

一方、現行 contract は24個の一意な絶対 path と `--out` の包含しか要求せず、各 path、group receipt、out が同じ `<attempt>/results` 配下にあることを検証しない。attempt id も軸から導出されない。親が mixed list を渡せば個別 certified row だけが残り group は不成立になる。全 path が同一軸で attempt も同じなら、別 group root の24件を別 receipt path に束縛できる。

canonical group root、receipt 名、workload/slot 別 basename を軸と attempt から導出し、その24 path と軸を hash 化した `group_manifest_sha256` を全 request に共通で持たせるべきである。

根拠: [stage2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:131)、[stage2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage2-plan.md:148)、[probe.py:1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1024)、[probe.py:1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1447)、[probe.py:2205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2205)

## 8. 波2は cohort 2 の24-thread 副次層を支えない

- 判定候補: **real**
- 成果物影響: 波1と波2だけなら、レポートで支えられるのは、前述の genome 問題を直した後でも policy 2 の12 seedにおける48-thread主層と48-thread副次2層、および独立な p1@24 certificate だけである。24-thread副次3層は uncertified のままになる。

解析器の primary と secondary はすべて policy 2 row を選ぶ。したがって波1は write-heavy@48 の主層と balanced/read-heavy@48 の副次層を直接支える。波2の p1@24 は24-thread 経路の生死確認と p1 binary の認証にはなるが、policy 2 の write-heavy、balanced、read-heavy 各24-thread副次値を一つも支えない。

波3を走らせない場合に許される表現は「policy 2 の12 seedについて48-thread層を認証し、p1について24-thread認証経路を実測した」であり、「cohort 2を認証した」ではない。p0、p2@24、exact diagnostic genome は別に残る。完了判定は全体 boolean ではなく層別 coverage matrix にすべきである。

根拠: [brief.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:14)、[brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:46)、[analysis.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:692)、[analysis.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:722)、[preregistration.md:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/docs/backoff-counterfactual-cohort2-preregistration.md:230)

## 9. D1852 は費用面だけを部分上書きすべきである

- 判定候補: **real**
- 成果物影響: 新 decision が D1852 を全面撤回すると、将来の台帳上で seed/thread 受理拡張が費用問題だけだったことになり、正しさ gate の拡張抑止が消える。

今回の射影には D1852 本文がないため本文自体は独立確認できない。しかし親 brief の「却下理由は費用だけ」という断言は、ユーザーが明示した非費用理由および絶対規律2と両立しない。

直接指示が上書きするのは「312 job を実施しない」という費用判断である。残すべき理由は「認証の射程を広く書かない」「新軸は exact 閉表」「不要な cell へ広げない」「旧 receipt と新規受理を分離」「成果物は coverage を層別表示」である。段7の decision は全面 supersede ではなく部分 supersede と記録すべきである。

根拠: [brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:18)、[brief.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/brief.md:61)、[CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/CLAUDE.md:67)、[CLAUDE.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/CLAUDE.md:109)

## 10. 信頼境界では命令実行より artifact 参照と削除が危険

- 判定候補: **文字列による命令注入は refuted、汚染 JSON による証拠参照と削除は real**
- 成果物影響: accepted receipt の `trace_dir` が foreign path を指し、その証拠が削除されると、receipt は監査不能な参照を残し、場合によっては group 外ディレクトリを消す。

verifier argv は固定構築され、seed/cell/claim を shell command や指示として解釈する経路は見当たらない。この意味で典型的な prompt injection 面は増えていない。

しかし row の `trace_directory` は canonical absolute path であることしか要求されず、group root の子であることを要求しない。manifest 検査は記録された SHA の形式と実ファイルの size を見るが、実 SHA と line count を再計算しない。group 完了後は receipt 由来の `trace_dir` をそのまま `shutil.rmtree` へ渡す。段2の「out.parent 下に作られる」は producer recipe の説明であり、consumer の信頼境界ではない。

trace path を row output から導出した canonical child に限定し、symlink を拒否し、集約直前に digest と行数を再計算し、削除対象も receipt 値ではなく検証済み導出値だけにすべきである。seed/thread/legacy の受理拡張は、この既存の危険な consumer に到達できる artifact の集合を増やす。

根拠: [CLAUDE.md:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/CLAUDE.md:88)、[probe.py:1624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1624)、[probe.py:2100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2100)、[probe.py:2319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2319)、[probe.py:2971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2971)

## 総括

- 最も重い所見: planned receipt が認証する genome と cohort 2 主解析の genome が異なり、現状では主判定を認証済みにできない。
- 段4で必ず裁定すべき点: performance artifact を exact executable 束縛と呼ぶのを止めて field と schema を分け、legacy は既発行 digest だけに限定すること。
- 撤回すべき部分: 段2裁定点1の現行表現と、`CERT_THREADS=(24,48)` を既存4 cellすべてへ適用する裁定点3。