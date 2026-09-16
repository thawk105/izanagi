## 所見

本段は静的読解と算術反例による相談結果であり、変更・pytest・実走は行っていない。「real」はコードと反例で成立する欠陥を指し、本番での発火実測とは区別する。

1. **real — baseline も同じ規則で集約しても、certified の受理集合は不変にならない。**

   **根拠:** `orchestrator/campaign/screening_driver.py:491-512` は新規 baseline の WAL から abort_rate を取得し、`pipeline.py:2366-2375` は candidate と baseline の比で verify 到達を決める。反例として、baseline の `(tps, abort)` を `(99,.1),(101,.1)`、candidate を `(79,.5),(81,.1)`、`high_abort_factor=2`、`k=2`、`floor=.05`、bench は stable とする。baseline は旧新とも abort=.1、性能閾値=90。candidate は旧 abort=.1 なので screen-reject、新 abort=.3 なので verify へ進む。全 verify を通れば `pipeline.py:2440` で certified になる。candidate の abort を低速側 .1／高速側 .3 にすれば逆方向も成立する。

   **成果物への影響:** 同じ生 throughput・同じ verifier を使っても、COMMIT 集合、terminal verdict、critic に渡る緑／赤の集合が変わる。

   **推奨:** **採用** — この反例を受入に含め、不変条件を「固定入力に対する median_tps と verifier の判定規則は不変」へ限定する。certified 集合不変を必須とするなら現在の P1 は不採用。screening の別改変で帳尻を合わせることは勧めない。

2. **real — counters / maxrss の代表変更は、診断分類と校正条件にも到達する。**

   **根拠:** 現行 `runner.py:1050-1060,1287-1304` は上側中央 throughput の rep を採る。P1 の「実行順が先」への変更で、abort/latency 以外も変わる。例えば先行する低速中央 rep の counters が欠損、後行する高速中央 rep が完備なら、旧 IPC は数値、新 IPC は None。`perf_preflight.py:348-362` がこれを `counter_status=complete→incomplete`、`missing_leading_indicators` の変更へ射影する。逆順の欠損なら incomplete→complete も成立する。

   また `calibrator/analyze.py:88-95` は miss rate で飽和点を、`:166-170` は maxrss と miss rate で下限点を選ぶ。`calibrator/sweep.py:262` は設定された sweep_reps を渡すため、偶数有効数でこの経路にも届く。

   **成果物への影響:** WAL／layer3 の perf 欠損分類、校正の採用 records・警告が変わり得る。校正条件が変われば後続実測の fitness まで一律不変とはいえない。

   **推奨:** **scope 外の裁定パッケージ候補** — 本題の abort/latency 整合に resource 代表変更は必須ではない。旧代表を維持するか、この診断・校正への影響も本 wave で受け入れるかを明示する。「anomaly 検出に触れない」という包括的説明は不採用。

3. **refuted／real — 比の平均そのものは誤りではないが、既存の field 説明では意味を取り違える。**

   **根拠:** 中央 2 rep の abort 比が .5 と 0 なら、A は .25。各 rep の `(aborts,commits)` が `(100,100),(0,300)` なら pooled 比は .2。これは集約対象が異なるためで、A は「throughput 順中央 2 rep の per-rep 比の等重み平均」として正しい。pooled 比であるという契約はない。

   latency も、threads=1、tps=100,300 なら A は約 6,666,667ns、`1e9/平均tps` は 5,000,000ns。ただし `model.py:70-72` は現在「代表 rep」「平均トランザクションレイテンシ」と説明しており、A の値を単一実測 rep と読む説明は変更後に偽になる。

   **成果物への影響:** WAL／8c の値が単一 rep 値から集約値へ変わり、pooled 比・実測応答時間・中央値 throughput の逆数と誤読され得る。

   **推奨:** **採用** — A の統計量を helper と field の説明に明記する。B は単一 rep の共起関係を調べる目的には適するが今回の中央 2 rep 要件を満たさず、C は指標ごとの典型値を求める目的には適するが奇数互換性を破る。行全体の統一集約は A でも保証しない。

4. **real — P3 は「同じ rep 集合」の例外に加え、欠損時の screening 動作も変える。**

   **根拠:** 中央 2 rep の throughput が `(79,81)`、abort が `(.1,None)` なら、現行は上側 rep の None。`pipeline.py:2367` により screen-reject せず verify へ進む。P3 では .1 が入り、所見1の baseline 条件なら reject になる。throughput は 2 rep、abort は 1 rep なので、同じ集合・同じ演算という無条件の完了判定も成立しない。`digest.py:1173-1175` の `_mean` が同じ欠損除外を行う事実は、screening での意味を保証しない。

   **成果物への影響:** 欠損を含む測定が、従来の「曖昧なので verify」から uncertified reject へ変わり得る。

   **推奨:** **採用** — P3 を採るなら完全観測時だけの整合保証とし、片側欠損の screening 反例も所見1と同じ受入範囲に含める。

5. **real — latency の恒等変換という主張は通常出力に限定され、fallback 全体には成立しない。**

   **根拠:** `external/ccbench/common/result.cc:52-56` の throughput は `(commit+batch_commit)/extime` を整数へ格納した値で、latency はその逆数。一方 `benchparse.py:60-64` の fallback は `commit_counts_/actual_extime` であり、batch を含まず、分母・丸めも異なる。例えば通常 commits=100、batch=0、displayTps の extime=3、actual_extime=3.1 なら、出力 throughput=33 に対する latency と、fallback throughput≈32.258 の逆数は一致しない。

   T-2588 の逐語資料は 710664／727985 と記録 latency の照合を示しており、その事例の確認は支持できる。fallback や全 consumer の動作まで実測した証拠ではない。

   **成果物への影響:** digest から latency を除外する方針は維持できるが、「全経路で情報ゼロ」という台帳上の説明は過大になる。

   **推奨:** **採用** — 「CCBench 通常出力では throughput 由来の量であり、独立した latency 計測ではない」と記す。fallback 修正は本 scope 外。

6. **refuted／未実測 — latency 列欠落による closed critic の機械的破損は見つからない。role の意味上の不整合は残る。**

   **根拠:** `p3_b4_closed_critic.py:478-498` は digest を非空文字列として検査し、列を要求しない。`:114-121` の上位契約は欠損を uncertainty とする。`claude_projected_provider.py:162-167` はその契約を role 本文へ優先適用し、`:259-276` は payload を JSON として運ぶだけである。

   一方 `.claude/agents/critic.md:26-27` と `critic-experiment.md:36-37` は恒等変換に基づく誤帰属を引き続き教える。brief の列挙外にも `critic.md:36` の「latency 律速、再訪不要」が残る。LLM がどう応答するかは未実測。

   **成果物への影響:** payload schema は破損しないが、attribution／avoid の解釈不整合が残る。また digest 自体が変わるため、role bytes 据置きだけでアーム入力不変とはいえない。

   **推奨:** **scope 外の裁定パッケージ候補** — P2 は射程管理として支持できる。ただし上記4箇所を残件へ含め、「アーム条件を維持できるから不要」という理由付けは不採用。

7. **refuted／real — D118 と (a) は両立する。ただし key 不変は意味不変の証明ではない。**

   **根拠:** `docs/decisions.md:5601` の D118 は recipient ごとの単位・射影を定める。(a) は WAL の latency を残し、`s8c_generation_projection.py:58-81` の閉列挙も変更しないので矛盾しない。`model.py:95-101` と `pipeline.py:1455-1468` の WAL key も維持される。

   ただし D118 決定(4)は同じ schema で値の意味が変わる問題を扱っている。今回の A は単位変更ではないものの、producer の統計量を変更する。D828 は layer3 の optional property 追加の裁定であり、この意味変更を自動的に承認する根拠ではない。

   **成果物への影響:** WAL／layer3／8c の key 集合は維持されるが、偶数有効 reps の payload 値・hash・過去値との比較条件は変わる。

   **推奨:** **採用** — (a) のみなら D118 整合は支持。A の前後比較には集約規則の変更を明記する。新 schema／台帳の追加を本所見から要求するものではない。

8. **real — consumer／閉包の列挙には追加漏れがある。ただし凍結 pin 破損は未確認。**

   **根拠:** `orchestrator/` と `tools/` の検索で以下を確認した。

   - `search_baselines.py:102-110` は `GenomeLI` と `axis_effects` を直接使用する。選好は throughput のみなので今回の列削除で不変。
   - `guided.py:148-154` は leading_indicators を誘導 WAL へ複写する。
   - `tools/plotting/plot_b10_extended_backoff.py:605-622` は5反復を要求し、WAL latency と throughput の逆数関係も検査する。正常な奇数5反復を維持する限り今回の直接破損は反証できる。
   - `tools/plotting/plot_a2_certification.py:461-466` は abort_rate を読み、範囲検査する。
   - `p3_b4_raw_record_producer.py:987-1045` も digest／role を閉包に含め、bytes の hash を取得する。closed critic 本体だけの列挙では不足。

   **成果物への影響:** consumer 調査の完了記録が不完全になる。新規 B4 の閉包 hash は変わるが、既発行の凍結 pin を破る実例は本段で確認していない。

   **推奨:** **採用** — 親の consumer／閉包記録へ追記する。pin を更新・解除する必要があるとの推測は採らない。

9. **refuted — plan の奇数分岐は、固定入力での既存 runner 集約値を維持できる。verifier 本体への直接変更もない。**

   **根拠:** 奇数有効数では `model.py:236-242` の `_median` と現行 runner の中央 throughput が一致する。plan は元順序の `min(abs(...))` と `rep[1:]` を保つため、同値 tie、abort/latency/counters の None も加工されない。有効0件の最後の rep、全実行失敗の例外も維持する計画である。

   `digest.py:785` 以降の rejection 読出し、`:1121` 以降の verify abort signal は変更対象でない。screening を抜けた候補には引き続き `pipeline.py:2388-2440` の全 verify が必要。

   **成果物への影響:** 奇数有効数の runner 集約 bytes は固定入力・固定時計で維持可能。ただし digest bytes は列削除で変わり、screening 前後の verdict 出現集合は所見1の例外がある。

   **推奨:** **採用** — plan の奇数互換テストを維持する。「規律2を緩めない」は支持するが、「正しさに関係する経路へ一切触れない」は不採用。

## (P1)(P2)(P3) への判定

- **P1：条件付き支持。** 完全観測された abort/latency を throughput 順中央2 rep で平均する A は目的に合う。ただし certified／terminal verdict 不変は撤回が必要。resource 代表変更は欠損分類・校正への影響を別途明示し、必要性を再判断する。
- **P2：条件付き支持。** 機械契約上 latency 列は必須でないため、本 wave で role を据え置ける。誤帰属例とアーム入力変更を残件として明示することが条件。
- **P3：条件付き支持。** 欠損でない値を残す方針として妥当。ただし「同じ rep 集合」は完全観測時だけの保証であり、欠損による screening の保守動作が変わることも受け入れる必要がある。

## 総括

(a) の digest 列削除は支持でき、D118 の recipient matrix とも両立する。
A の abort/latency 集約は妥当だが、certified 集合・terminal verdict 不変という brief の保証は成立しない。
resource 代表変更は perf 欠損分類と校正点選択にも届くため、表示修正だけとは扱えない。
奇数有効数の runner 互換性と、全 verify 通過を必須とする規律2は維持可能。
実装前に不変条件と resource 変更の射程を確定する必要がある。
