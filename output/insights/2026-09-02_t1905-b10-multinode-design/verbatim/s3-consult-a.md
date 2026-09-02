## 規律 2 の破れ

- [real] verifier 多重化設計が既存の `legacy + performance` 二重ゲートを「5 反復」だけへ縮約している。プランは「各変種の正しさ検証は5反復」「全5件の論理積」とするが、実装は既定 legacy 1 回に performance 5 回を追加する構造である。`plan.md:20,33`、`orchestrator/campaign/pipeline.py:1011-1014`、`orchestrator/campaign/loop.py:149-158`、`docs/b10-backoff-shape-preregistration.md:423-429`。

  成果物への影響: legacy だけで検出される異常を持つ variant が certified になり、bench と45セルの記録へ進む受理集合拡大になりうる。

- [real] 推奨する process worker pool は、現行の正しさ capability を coordinator へ返せない。プランは coordinator が capability 順序を所有し、worker process が検査するとしているが、`VerificationCapability` は発行 PID と process 内 issuer registry に束縛され、別 PID では拒否される。`plan.md:25-28,35-38`、`orchestrator/verifier/core.py:162-217,224-247`、`orchestrator/verifier/commit_receipt.py:296-323`。

  成果物への影響: capability を維持すれば COMMIT receipt が発行できず certified 成果物はゼロになる。結果だけを coordinator へ返して代用すれば、既存 proof chain を外して受理集合を広げる。thread pool なら PID は保てるが、単一プロセスの Python 検査を多コア化する根拠にならない。

- [suspect] worker の timeout、OOM、異常終了という「結果が返らない」場合の exact な reject 規則がない。プランが定めるのは anomaly または「検証不能結果を受けた時」であり、Future 消失や pool 崩壊は結果ではない。`plan.md:28,33`。現行の同期経路では予期しない例外も terminal abort へ変換する。`orchestrator/campaign/loop.py:593-616`。

  成果物への影響: 実装次第で workload 全体が無成果になるか、欠落反復を除いた capability 列を certified とする false-green になる。後者は現行の exact capability 数検査を緩めた場合に発生するため未確認とする。

## 規律 1 の破れ

- [real] 「verifier の CPU 利用は性能値ではない」だけでは観測者効果を分離できない。プランは最大規模の worker pool 終了直後に perf loop へ進めるが、性能前の `settle()` は load average が下がらなくても20秒で `settled=False` を返して続行する。B-10 の usability 判定は `settled` を検査しない。`plan.md:29-31`、`orchestrator/calibrator/runner.py:271-289`、`orchestrator/campaign/b10_backoff_shape_sweep.py:2238-2249,1655-1669`。

  成果物への影響: verifier pool の熱、load EMA、page cache、メモリ圧力が block-1 の先頭 `none` セルへ漏れても、その中央値は利用可能値として `shape/constant-1`、CI、Holm 判定へ入る。

- [real] 正しさ run との非重複は trace producer についてしか定義されていない。プランは worker 終了、子 process 回収、memory reclaim 完了を perf 解禁条件にしておらず、測るのは事前の容量見積りだけである。`plan.md:26-31,35-45`。

  成果物への影響: 生存 worker や回収未了資源があれば、性能セルが競合下で取得される一方、現在の `_record_usable()` はその状態を拒否せず正式な効果量へ流す。

## 事前登録との不適合

- [real] §8 の判定不能報告と「135セル exact でなければ report を書かない」が両立していない。プランは全 request terminal 後にも3×45 exact 集合がある場合だけ report を書くが、失敗 job の45セルを missing として具体化する規則がない。`plan.md:69-70,120`、`docs/b10-backoff-shape-preregistration.md:460-486,658-667`。

  成果物への影響: 2 workload 成功、1 workload 失敗の terminal group では、必須の「判定不能族」を含む報告が生成されない。逆に成功分だけを渡せば、exact 集合契約を破る。

- [real] workload fan-out の job 間集約について、量に対する node 作用が固定されていない。プランは「raw throughput ではなく Holm」とだけ述べる。実際の対は
  `d = Y(shape) / Y(constant) - 1`
  であり、共通乗数 `q` には不変だが、共通加算 `a` では
  `d' = (Y(shape)-Y(constant)) / (Y(constant)+a)`
  となり不変でない。`plan.md:7`、`orchestrator/campaign/b10_backoff_shape_sweep.py:1672-1673,1745-1772`、`docs/pegasus-runbook.md:1328-1339`。

  成果物への影響: node 作用の仮定と割付けを protocol に固定しないままでは、18個の効果量、符号反転 p 値、block 平均 CI、Holm 結果が workload→node 割付けで変わりうる。

§7 の SHA 照合そのものは文言だけではない。committed attempt の `perf_bin_sha256` を抽出し、測定直前に再 hash して二重一致を要求する実体がある。`orchestrator/campaign/b10_backoff_shape_sweep.py:2433-2485,2988-2990`。また、正確な135レコードが入れば推定量は従来どおり18個の block 内比、3 block 平均 CI、3族 Holmになる。推奨案の問題は、この実体へ到達する capability 経路と fan-in 境界である。

R2 の performance `blocks.run_order` は、推奨する workload 単位自体では変更されない。`orchestrator/campaign/b10_backoff_shape_sweep.py:2978-3045`。

## 既裁定の射程拡大

- [real] 親 brief は D1169 を一般的な B-10 分割許可として列挙しているが、決定本文の対象は A-2 である。`brief.md:21-22`、`verbatim-decisions.md:62-69`。プランはこの点を正しく限定している。`plan.md:13`。

  成果物への影響: D1169だけで進めると、B-10 の exact 3-member composition を変えても B-10 protocol SHA が追随しない成果物を受理できる。

- [real] 親 brief の P2 は、既登録の schedule block を node block と同一視し、「job内で閉じるから node 因子の要件を満たす」としている。`brief.md:78-81`。発効版の block は15点の実行順を定めたものにすぎず、node 割付けを定義していない。`docs/b10-backoff-shape-preregistration.md:339-398`。runbook は投入前の node 因子、対照、推定量、集約の固定を別途要求する。`docs/pegasus-runbook.md:1336-1339`。

  成果物への影響: P2をそのまま採ると node=block の追加構造を未登録のまま paired-block CI と18対検定へ混入させる。プラン自身は `plan.md:8,114` でこの点を修正している。

- [real] D1126 が残した実行ノード記録を、プランの group artifact が保持しない。group manifest の列挙は request、入力 hash、namespace、期待成果物までで host がない。`plan.md:74`。現行 block record と `SubmissionIdentity` にも host はない。`orchestrator/campaign/b10_backoff_shape_sweep.py:330-339,3004-3033`。D1126 は host 記録を明示的に残す。`verbatim-decisions.md:42-54`。

  成果物への影響: workload ごとの45セルを実際に生成した node を report/provenance から参照できなくなる。

- [real] 親 brief P4 の「D1220 の射程が binary 輸送に届けば P2 が唯一」は偽である。`brief.md:85-87`。binary を輸送せず、各 workload job 内で verify/perf を完結する3-job案が存在する。`plan.md:7,51-59`。

  成果物への影響: この一般化を採ると、不要な9-job構成、正しさ認証3倍、node=block という未登録 composition を唯一案として選んでしまう。

D1220 と D1372 について、プランの「binary 単体輸送を承認も禁止もしていない」という限定は逐語範囲内である。D1255 と D193 についても、fresh identity と中断 WAL 非回復の扱いに射程拡大は見つからなかった。

## 親 brief の誤り

- [suspect] P1 の「律速は直列化可能性検査」「47コア遊休」は read-heavy 1 workload の混合区間からの一般化である。一次資料が確定しているのは CPU/経過=1.0 と、「残りは trace 書き出しと直列化可能性検査」という二成分までで、両者の個別時間を分離していない。`brief.md:74-77`、`verbatim-worklog-1186.md:14-17,58-62`、`verbatim-insight-t1905.md:140-158`。

  成果物への影響: trace I/O が支配的、または write-heavy/balanced の構成が異なる場合、`C/P` 外挿で walltime を過小評価し、正式 job が打ち切られて missing family になる。

- [real] 「性能測定本体は1 workload 4.5分」の算術は発効版 producer と一致しない。登録値は3 block×15 cell×5 performance reps×3秒で、名目実行時間だけで675秒、11.25分である。brief の「3秒×6記録×15変種」は block=3 と reps=5 のどちらにも一致しない。`brief.md:43-46`、`docs/b10-backoff-shape-preregistration.md:339-429`、`orchestrator/campaign/b10_backoff_shape_sweep.py:2227-2258,2978-2997`。プランも4.5分をそのまま差し引いている。`plan.md:78,84-90`。

  成果物への影響: 各 workload の perf 時間を少なくとも名目6.75分、3 workload 合計で20.25分過小計上し、同じ分だけ verifier 時間 `C` を過大計上する。

- [real] P5 の競合面は不完全である。親 brief は claim、block record、reportだけを列挙するが、現行 `cache_root` も共有され、trial も submission nonce を含まない。`brief.md:88-90`、`orchestrator/campaign/b10_backoff_shape_sweep.py:1518,2883`、`docs/pegasus-runbook.md:1300-1305`。プランは `plan.md:72,106` でこれを補っている。

  成果物への影響: 親 brief の列挙だけで並行投入すると、build-cache claim の競合または同一 campaign identity により workload job が abortし、部分成果しか残らない。

- [real] 親 brief の SHA アンカーがずれている。表は `verify_performance_binary` 呼出しを `:2992` とするが、実体は `:2988-2990` であり、`:2992` は performance 測定呼出しである。`brief.md:64`、`orchestrator/campaign/b10_backoff_shape_sweep.py:2988-2993`。

  成果物への影響: 設計文書の参照先が SHA gate でなく測定 producer を指し、§7 適合の実体を誤参照する。

175秒頭打ちについて、brief は未確認と明記し、プランも固定上限には使わず線形外挿の限界としている。`brief.md:45-46`、`plan.md:92`。この点の確定値化は反証されなかった。

## 信頼境界

- [real] fan-in が読む job record は自己 hash されているだけで、測定値を WAL、certification attempt、performance producer へ束縛する admission がない。現行 validator は metadata と record 自身が示す receipt bytes の hashを調べるが、`median_tps`、`correctness_certified`、`performance_binary_sha256` 等を元 job の WAL と照合しない。`orchestrator/campaign/b10_backoff_shape_sweep.py:2310-2326,2361-2430`。その値はそのまま `_record_usable()` と `judge()` に入る。`同:1655-1769`。プランは exact member 数しか定めていない。`plan.md:69-70`。

  成果物への影響: 別 job が作った自己整合的な record は、測定実体との束縛がなくても中央値、18効果量、p値、Holm outcomeを変更できる。

- [suspect] group manifest の所有者と不変化点が定義されていない。プランは manifest の内容を列挙するだけで、worker が期待 member、request対応、成果物 hash を変更できない構造を示していない。`plan.md:67-74`。

  成果物への影響: manifest が並行 writer に開かれる実装なら、失敗 request を期待集合から外し、部分成功を exact conjunction として受け取れる。設計文書だけでは writer 権限を確認できないため未確認とする。

## nit (成果物への影響を言えないもの)

該当なし。

## 総括

プランはこのままでは承認できない。最大の反証は、推奨する process verifier pool が現行の process-bound capability と両立せず、さらに legacy 1回を含む実際の6回ゲートを5回へ縮約している点である。加えて、worker負荷の performance への持ち越し、失敗 group の判定不能報告、node 作用を含む推定量、外部 record の admission が未成立である。

一方、発効版本文は指定 blob `ea910de32` と一致した。workload 単位そのものは R2 の performance run orderを変えず、§7 の SHA gate にも実装実体がある。問題は、その手前の認証多重化と、その後の fan-in 境界である。

本検査は静的検査のみで、pytest、実測、投入は行っていない。