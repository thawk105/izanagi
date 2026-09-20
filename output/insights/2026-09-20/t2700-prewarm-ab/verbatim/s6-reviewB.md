## must-fix

**B1 — 取り直しの投入順と終了条件が、親の事後判断に残っている。**

根拠: `run-series.sh:3–4,13–22`、`t2700_ab_analyze.py:290–309`、`s4-ruling.md:54,66,73–75`。

系列は失敗しても指定済みの次走へ進み、取り直す slot・順番・時点は親が別系列で指定する。集計器も slot 内の E/L 順だけを確認し、slot の進行順は検算しない。したがって「失敗した対を直ちに同順序で再投入」と「全 slot を一巡してから任意順で補充」の両方を受理する。上限20走・有効8対での投入停止も launcher にはない。

- **成果物への影響:** 取り直し時点と残り予算の配分によって採用対、順序の均衡、中央値・p・判定が変わる。
- **是正案:** 測定前に、対を最後まで投入するか、失敗後いつ再試行するか、複数未達 slot の優先順、残り1走の扱いまで固定する。その逐語手順を親が守り、集計器が系列を検算する。汎用 scheduler の追加は不要。既存系列を継続する方式でも、補充順を固定すればよい。

**B2 — 超過走が失敗感度分析と最終文言に入る。**

根拠: `t2700_ab_analyze.py:288–291,314–335`、`s4-ruling.md:54,73`。

対統計は上限内に限定されるが、失敗件数・符号検定・結論の腕別失敗件数は全 `rows` を使う。有効8対確定後、または21走目以降の失敗を追加すると、確定済みの最終文言と感度分析が変わる。「超過走は表に残すが判定に使わない」と一致しない。

- **成果物への影響:** 同じ採用対表でも、停止後の追加投入によって符号検定の p と失敗付き結論が変わる。
- **是正案:** 「8対成立時点と20走目の早い方」を解析締切として保存する。全投入の監査表は維持し、事前登録期間内の失敗推定・感度分析と、締切後の件数を分ける。

**B3 — 同一 worktree・同一 session の検算が足りず、receipt の終端状態も確認していない。**

根拠: `write_run_json.py:8–19`、`run-measure.sh:91,112–120`、`t2700_ab_analyze.py:143–180,274–283`、`dispatch_compute.py:3737–3767,4355–4370`。

SHA は `run.json` 内の申告値を比較しているが、worktree の識別 field がない。receipt から読むのは job 番号だけで、request の session/shard 引数、終端 outcome、child rc を照合しない。JUnit の時刻も投入・完了区間との包含を確認していない。別走の session 一式を取り違えても、hash を含めて整った複製なら通り得る。

receipt が SHA256SUMS にない点は author の申告どおりであり、job 番号照合は receipt 自体の完全性や session 対応の代わりにならない。

- **成果物への影響:** 別 session・別 worktree の W/H/D や失敗 receipt を有効走に結び付け、対差と判定を変え得る。
- **是正案:** `worktree_realpath` を記録し全走で一致確認する。receipt を必須 hash 対象とし、既存の request 引数から session/shard を照合、成功 outcome と child rc を確認する。必要なら既存 request.json を追加保存して repo/env を照合する。JUnit 時刻も、外側の秒精度を考慮した固定許容幅で区間確認する。consumer registry の抽出元 SHA・hash も記録する。

**B4 — receipt 不発行と複製失敗を区別できず、失敗原因が誤分類される。**

根拠: `run-measure.sh:102–128`、`write_run_json.py:13–15`、`t2700_ab_analyze.py:127–148`、`s4-ruling.md:53,65`。

receipt の copy 失敗はログだけで `COPY_OK=0` にしない。集計器は複製先に receipt がないだけで、`copy_ok` 検査より先に `infrastructure` を返す。このため、正常走の receipt 保存失敗も「receipt 不発行」と同じになる。stderr の複製失敗では treatment-failure の証拠を失い、rc=16 の infrastructure に落ちる。

- **成果物への影響:** 腕別の artifact／infrastructure／treatment-failure 件数が変わり、介入に伴う失敗を過小計上し得る。
- **是正案:** 必須ファイルごとに「原本なし／copy失敗／hash失敗」を記録し、receipt・stdout も `COPY_OK` に反映する。原本 receipt 不発行と複製先欠損を分離する。失敗時の `dispatcher.log`・login collection log も保存し、証拠欠損時は原因不明を明示する。

## should

**B5 — 裾モデルの説明と σ_d の意味を修正する。**

根拠: `power_rule.py:2,50–58`、`s4-ruling.md:10`、`t2700_ab_analyze.py:238–258`。

親と集計器の実装はともに、独立な15%の正・負の裾を加える**対称モデル**である。「L側だけの非対称な裾」という説明とは異なる。また裾モデルでは、入力 `sd` は正規成分の SD であり、裾を加えた対差全体の SD ではない。

- **成果物への影響:** 感度表を「観測 σ_d と同じ総分散」「L固有の非対称性を評価済み」と解釈すると、必要走数の根拠が変わる。
- **是正案:** 現モデルを維持して「正規成分SD＋両腕独立の遅延」と明記する。非対称性も評価するなら、測定前に別モデルとして固定する。集計器の R=2000 と親の R=4000 は許容範囲だが、結果の完全一致は期待しない。

**B6 — warm-up の成立を投入前条件として明記する。**

根拠: `run-warm.sh:11–18`、`run-measure.sh:40–43,71–88`、先行手順 `t2766-README-s4-s5.md:5`。

warm-up は rc と pyc 数を保存するが、測定 launcher は成功・同一tip・実行完了を確認しない。collect-only 一回で温まるのは主に収集時に import されるコードであり、実行時 import、page cache、fixture まで同じにはならない。

- **成果物への影響:** warm-up 失敗やその後のソース変更を見逃すと、最初の E/L 差に bytecode 生成・読込み状態の差が混ざる。
- **是正案:** 親の起動手順に「最終測定tipで warm rc=0を確認後に開始」を固定し、そのtip・環境・logを保存する。一律の warm-up 増量は不要。E/L順の均衡は残し、「全キャッシュが同一」とは記述しない。

**B7 — 履歴表は A5 の最小絞込みを満たすが、SHA・scheduler の構成が見えない。**

根拠: `t2700_history_estimate.py:34–60,78–104`、`s3-consult.md` の A5、`s5-author.md:31`。

shard_count=3、pytest_rc=0、timeline、offset は検査している。抽出・除外・session数・日付・hostname種類も出す。一方、SHA と scheduler を出さず、E の直近N件は適合判定前の stderr mtime で選ぶ。

- **成果物への影響:** 異なるtip・scheduler・採取窓の分布を、今回へ移植可能な δ/σ の根拠として扱い得る。
- **是正案:** 取得可能な SHA・scheduler の構成と欠損数を追加する。E の「適合前N件」という現規則は明記して維持し、結果を見て適合後N件へ切り替えない。

author の **197−56=141 shard／130 session** は算術上・構造上は矛盾しない。ただし、指定された資料だけでは5,487件の原本抽出結果を独立再確認できず、件数と「除外は全件 pytest_rc 非0」は author 報告として扱う。

## nit

**B8 — 実装の縮小は不要だが、測定予算外の近似分岐は削れる。**

根拠: `s5-author.patch:8–48,68–100,114–197`、`t2700_ab_analyze.py:218–227,383–479`。

定数3・helper2・属性経由・allowlist・結線テストは局所的で、研究目的に対応する。集計器は実物では515行、履歴 script は131行で、申告された概算より小さい。selftest 約100行も妥当。ただし m>20 の正規近似は今回の8対／20走では不要。

- **成果物への影響:** 登録予算内の成果物は変わらない。
- **是正案:** 近似分岐は削除して範囲外を拒否してよい。selftest は増量より、B1〜B4の具体的な反例を既存合成走へ追加することを優先する。

**B9 — 機序と exact の主張範囲を README に残す。**

根拠: `conftest.py:2493–2515`、`t2700_ab_analyze.py:366–369`、`s3-consult.md:18–28`。

- **成果物への影響:** 数値表・登録判定は変わらないが、因果・機序の説明が過大になり得る。
- **是正案:** stderr 行は join 後・例外再送出前にも出るため、起動時刻や成功単独の証拠ではないと明記する。ΔD_0 は ΔW_max と同一ではなく、最遅shardの交代、実行部、tail、共有資源競合が介在する。交互順は位置効果を均衡させる工夫であり、無作為割付ではない。Wilcoxon exact は符号対称性・独立性を前提とする。

**B10 — 非landing設計は妥当。再現資料を閉じてから記録を land する。**

根拠: `s4-ruling.md:94`、`D2164.md:15–17,36`、`s5-author.md:3,39`。

- **成果物への影響:** 今回の計算値は変わらないが、保存漏れがあると同じ対表・判定を再生成できない。
- **是正案:** 実装commitを `impl-t2700-early-memo-optout` に保持し、landing branch は main から記録だけを作る。保存対象は、完全なmeasurement SHA、最終patchとsha256、launcher・集計器・履歴script・MCの逐語とsha256、consumer一覧と抽出元、事前登録版、起動・warm-up手順、全attempt／abort索引、raw成果物とhash、解析コマンド・出力。実装branch自体をlanding branchへmergeしない。

## 静的に確認できた整合点

- **直接投入:** `run_tests.py:267–298,2490–2502,2620–2629` により、通常のPegasus LOGIN・空argv・明示3 shardは `_dispatch_result(shard_count=3)` に入る。内部childは `1460–1533` で実受入を実行する。
- **Eの空文字:** `_dispatch_environment` はコピー時に新keyを落とさず、dispatcherは `key in command_env` で採取する（`dispatch_compute.py:3695–3697`）。compute側は `1844–1845` でoverlayするため残留tokenを消す。parserは空文字をFalseとし、collect-onlyでもUsageErrorにならない。
- **session_rootとlayout:** `acceptance_shards.py:1417–1424` の空白なしJSONに対し、launcherの抽出は一致する。平坦化したstderr/stdoutの配置、二空白区切りSHA256SUMS、run.jsonのfield名、offset付き時刻は集計器と整合する。
- **失敗時の記録:** 通常のrc=16・reportなしでも、`set -e`を使わず保存処理へ進み、run.jsonとchild.logを残す。`copy_ok=0`でも複製済みstderrは検索されるため、timeout文字列が残れば treatment-failureになる。問題はB4の証拠保存失敗との区別である。
- **門番と直列化:** flockは門番からrun.jsonまで保持される。他leader≤1・load1<30・2回連続・乱数後再検査は実装どおり。ただし他の直接投入やcompute負荷の不在を保証しない。最大sleep合計は **90×140＋45×45＝14,625秒、4時間3分45秒**。コマンド実行時間を含む厳密なwall上限ではない。
- **clean判定:** `.gitignore:2,27` が `__pycache__/` と `output/pegasus-dispatch/` を除外するため、通常の新規生成は指定git statusをdirtyにしない。ただし「worktreeへ一切書かない」という説明は実態に合わず、自動生成物の例外を明記すべき。
- **H/D/tail:** 集計器のHはreportのcollection-finish値を使用し、そのproducerはworker観測の最大値を返す（`acceptance_shards.py:1075–1092`）。Dは最初のtest開始、tailは `W−(last−timestamp)` で正しい。

## 統計実装の判定

`wilcoxon:208–228` の平均順位・0差除外・符号全列挙・片側上側確率・両側確率は、登録予算内では正しい。固定反例も一致する。

| 対差 | 片側p | 判定 |
|---|---:|---|
| +40×5、−45 | 17/64 | 未確立 |
| 10,20,30,40,50,−60 | 14/64 | 未確立 |
| 5,6,7,8,9,10 | 1/64 | 方向のみ |
| 0,0,12,20,30,40 | 1/16 | 未確立 |

標本SD、対応t統計量、両側5%臨界値表も整合する。SD=0でtを出さず、m=0で判定不能とする。未達は出力され、腕別失敗件数も常に結論へ付く。ただし解析締切はB2の修正が必要。

親と集計器のMCは同じ支持規則と同じ生成モデルを評価している。R=2000の最悪標準誤差は約1.12ポイント、R=4000では約0.79ポイントで、今回の探索感度には妥当。親の表でδ=27・正規成分SD=22・8対が正規0.85、裾混合0.50となることは、「必要走数は仮定依存で確定できない」を支える。集計器単独は観測対数での6条件だけなので、必要対数を論じる記録には親のn=6/8/10表も必要である。

## 総括

**must-fixは4件。**

- **launcherと集計器の契約:** 通常走の形式は一致。失敗分類・成果物の対応検算・停止後の扱いは未完。
- **事前登録の裁量:** 取り直しの時点・優先順と系列停止に残る。測定前の固定が必要。
- **統計実装:** 登録範囲のWilcoxon・t・SDは支持。MCの規則も一致するが、裾モデルの説明を修正する。
- **実装規模:** 概ね妥当。一般化や追加機構より、上記4件の局所修正を優先する。

静的読解のみ。pytest・selftest・MCの再実行、ファイル書込みは行っていない。