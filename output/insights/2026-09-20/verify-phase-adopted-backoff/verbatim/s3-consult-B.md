## 所見

以下、`J` は本 wave の job dir、`R` は指定 worktree、`先例` は指定された `verifier_cli_timing_probe.py` を指す。静的検査のみ実施した。

1. **投入 CLI は成立する。18 submit-tree は削減できる。**
   **対象:** plan §4、brief P4。
   **攻撃の内容:** CLI 不成立は **不成立**。`dispatch_compute.py:3601` は script の実体位置から repo を決め、`:1573` の generic 検査は非空の文字列 argv を受理する。`:1880` 以降でその argv を実行するため、plan の形は成立する。後半の `--repo-root` は新 runner の引数であり、dispatch の引数ではない。

   clean env は `PATH` を残すが `TMPDIR` と `PBS_JOBID` は残さない（`:354`）。選択 interpreter の dirname を PATH に前置する（`:1851`）。Python の実測所在は runbook §3 の `/bin/python3.10`／`/usr/bin/python3.10`。runner 内で scratch 作成後に `TMPDIR` **と `tempfile.tempdir`** を設定する先例 `:236` 以降を維持すればよい。hydrate の `--staging-root` と出力 `source_root` も実在する（`fetch_third_party.py:712,760`）。対象は FetchContent 3 本だけでなく gflags/glog を含む計5本。

   18 tree 必須説への攻撃は **成立／should**。hold の根は既定で各 tree の `output/pegasus-dispatch`（`dispatch_compute.py:3623`）、投入前に pending hold を作る（`:4002`）。段 A の6 tree は、全 request 終端・receipt 回収・残存 job 不在・hold/latch 解消・HEAD/clean 確認後、段 B の6 jobへ再利用できる。さらに6 treeを追加すれば **計12 treeで段Bの12 jobを並行投入**できる。6 treeだけで段Bを二波に直列化する必然性はない。
   **成果物への影響:** 判定集合を変えず、不要な作業木6本を削減できる。

2. **walltime の上限設計が未完成。4時間会計も投入可否を左右する。**
   **対象:** brief P1、plan §2〜4。
   **攻撃の内容:** **成立／must-fix**。段 A が10秒まで進む場合、3秒・6秒の verifier はそれぞれ600秒以下である。したがって verifier 部分の最大は `600+600+1800=3000秒`。1800秒を3回足す必要はない。

   setup/build 上限を `F`、各走の count・inventory・圧縮・保全を `A_e`、終了余裕を `H` とすれば、

   \[
   W_A \le F+3(120)+3000+\sum_{e=3,6,10} A_e+H
   \]
   \[
   W_B \le F+4(120+1800)+\sum_{i=1}^{4} A_i+H
   \]

   ただし現 plan は `F` と `A` の上限を定めていない。先例だけでも warmup build に1200秒、本 build に900秒を許す（先例 `:278,287`）。configure・依存 build・圧縮も含めた上限がなければ、具体的な walltime に完走保証は付かない。

   また先例を全 workload に仮置きすると、本走は `24×462.564 + 6×240 = 12,541.536秒 ≈3.48時間`。さらに校正 verifier だけを `3×(421.707+843.414)` と置くと、合計 **16,336.899秒 ≈4.54時間**で、校正 build 等を足す前に4時間を超える。これは予測の確定値ではないが、「校正込みでも余裕がある」とは言えない。

   期限式についての攻撃は **不成立**。plan の訂正は正しい。初期値は `submitted_at + walltime + grace`（`dispatch_compute.py:4156`）、信頼できる RUN 初観測で `run_observed_at + walltime + grace` に更新（`:4200`）。queue timeout は別判定（`:4215`）。grace は scheduler の実行時間枠を延長しない。
   **成果物への影響:** 会計範囲と上限を先に固定しないと、途中で予算切れになり24枠が完成しない。

3. **「6秒なら約88 GiBなので完走見込み」は資源根拠にならない。**
   **対象:** brief「前提の実測」、plan §7。
   **攻撃の内容:** brief への攻撃は **成立／must-fix**、plan が既に保証を否定している点への攻撃は **不成立**。

   `43.95×2=87.90 GiB` は算術として正しい。しかし1681 README `:79` は、43.95 GiBを**同時 process tree 合計でも cgroup peak でもない**と明記している。115 GiBとの差27.1 GiBを余裕と扱えない。parse は既定 `min(n_files, affinity,16)`（`parse.py:493`）、worker 数を増やすと charged memory が増える旨も `:509` にある。16倍する推定も誤りである。

   OOM 観測にも限界がある。worker 異常終了は並列処理失敗から逐次再読込みへ進み得る（`parse.py:649,795`）。外側の verifier が SIGKILL になるとは限らない。generic の隔離は user/mount namespaceであり（`dispatch_compute.py:1332`）、`/sys/fs/cgroup` を隠す処理はないが、これだけで `memory.events` の存在・読取り権限を保証できない。さらに runbook `:52` は **per-job cgroup ではなく共有 service cgroup** とする。読めた差分でも当該 verifier の OOM と一意に帰属できない。

   cgroup 採取は任意診断とし、取得不能を失敗にしない。signal・stderr・scheduler 記録を残し、根拠不足なら `killed_unknown` とする plan は妥当。
   **成果物への影響:** OOM の誤分類と「メモリ内に収まる」虚偽の保証を防ぐ。

4. **容量不足そのものより、総量・圧縮時間の未計上が問題。**
   **対象:** brief P5、plan §1・3・7。
   **攻撃の内容:** `/scr` の公称容量不足という攻撃は **不成立**。保全所要の根拠不足は **成立／should**。

   `U=6,520,332,111 bytes` を3秒走の代理値とし、bytes が extime に比例すると仮定すると、1走は3秒で6.52 GB、6秒で13.04 GB、10秒で21.73 GB。rep ごとに保全後削除すれば必要量は「build・依存領域＋最大1走＋圧縮一時領域」であり、公称5.4 TBには十分小さい。ただし実空き容量を確認する必要がある。圧縮を永続側の一時ファイルへ直接出せば、scratch 上の圧縮コピーは不要。

   全 workload を同じ代理値に置いた、校正最大18走込みの**非圧縮総量**は次のとおり。

   | 本走 extime | 校正 `6×U×(3+6+10)/3` | 本走48走 | 合計 |
   |---|---:|---:|---:|
   | 3秒 | 247.77 GB | 312.98 GB | **560.75 GB** |
   | 6秒 | 247.77 GB | 625.95 GB | **873.72 GB** |
   | 10秒 | 247.77 GB | 1,043.25 GB | **1,291.03 GB** |

   単に「66走×6.5 GB」とすると長い校正走を過小計上する。表は上限保証ではなく、retry・一時ファイル・build は別。圧縮率は不明なので、容量予約は非圧縮基準が妥当。親の「quota無制限・空き82 TB」は容量制約が消える意味ではない。

   1681の複製速度は約1.64 GB/sだが、1回・1 jobの値であり12 job並行時には外挿できない。`zstd -T0` の速度は資料に実測がない。例えば入力処理速度を仮に0.1／0.5 GB/sと置くだけでも、6.52 GBの圧縮は約65／13秒と変わり、hash・検算・転送はさらに加わる。段 A で実際の保全費を計り、本走会計へ反映する必要がある。
   **成果物への影響:** 全trace保全の容量と4時間予算を過小評価しない。

5. **再開の対象分類が足りず、成功までの再試行にも永久未確定にも読める。**
   **対象:** plan §4・5・7、brief P3。
   **攻撃の内容:** **成立／must-fix**。

   | 失敗 | 必要な扱い |
   |---|---|
   | hydrate／pinned-clean 失敗 | bench 前に停止。環境修復後の再開は可能。pin・条件は変更しない |
   | identity 不一致 | 自動retry対象外。期待値を観測結果に合わせて更新しない |
   | bench 120秒 timeout | 部分traceを保全。bench 完走枠として採らず、新attemptを許す条件・回数を事前固定 |
   | verifier rc=1 | anomaly。再実行成功で取り消さない |
   | verifier rc=3 | 完了したCLIの indeterminate。未実行扱いにしない |
   | rc=2／JSON破損 | trace hash・原因を確認。決定的な入力不良と一時的な出力破損を同列に再試行しない |
   | verifier timeout／walltime kill | 完全保全された入力なら同じtraceで検証再開。未保全なら再生成規則に従う |
   | dispatch rc=16 | receipt の reason・state history・起動証拠・rep状態を照合。rcだけで未開始と決めない |

   queue timeoutでも「確実にQUEだった」証拠の有無を区別する実装がある（`dispatch_compute.py:4216`）。hold中に別treeへ逃げて再投入すると、元jobとの重複実行になり得る。

   **同一traceの検証再開が独立反復を壊す、という攻撃は不成立。** 独立単位をbench processが生成したtraceと定めれば、同じ入力の再検証はNを増やさない。ただし `bench_attempt_id` と `verify_attempt_id` を分け、同じrepを二重計数しないこと。

   plan の「indeterminateを消さない」と「未解決indeterminateなしならpass」の関係は未定義。**履歴は残すが運用上の未完了は解決可能なのか、1回でも発生すれば永久に未確定なのか**を裁定すべき。校正のtimeout/OOM打切りを、retry成功で迂回してはならない。
   **成果物への影響:** 観測結果による選択的再測と24枠の水増しを防ぐ。

6. **削れる診断はあるが、全 anomaly の JSON 保全は確認できない。**
   **対象:** plan §1・5。
   **攻撃の内容:** **成立／should**。

   - cgroup の常時監視・独自samplerは削減可能。任意の前後snapshotで十分。
   - page cache の常駐測定や制御は不要。「count→inventory→保全→verify」の順序記録は校正解釈に効くので残す。
   - compiler 実体照合は削らない。`cxx="g++"` で導出したidentityと実buildの対応に効く。ただしjobのbuild前後にまとめ、repごとの重複採取は削れる。
   - 汎用resume frameworkは不要。ただしrep台帳・重複拒否・保全済みtrace再検証の最小経路は成果物に直接効く。

   `cli.py:46` の `--max-report` は既定20で、`:71` から検証本体へ渡る。**全 witness がJSONに載るとは言えない。** 一方、「`anomaly_count` が存在しない」という攻撃は **不成立**。1681 README `:90` に実出力の当該fieldがあり、先例 `:187` も参照する。

   ただし `cli.py:91` は `result_to_dict` に委譲しており、このファイル自体では **`anomaly_count` が表示上限を超えた全件数かどうか確認できない**。射影外の実装を読んだとは主張しない。plan §5 の「原 `anomaly_count` 合計＝全件数」は未立証であり、`total_cycles` と表示配列長を区別する必要がある。pass/失格はCLI verdictを保持すれば成立し、全 witness 出力のために報告上限を巨大化する必要はない。
   **成果物への影響:** 判定表は維持できるが、異常の「総件数」を過大に意味付けしない。

7. **先例の機構流用は妥当。ただしidentityの旧期待値は確実に衝突する。**
   **対象:** plan §1、brief候補表、`J/refs/identity-precheck.md:18–36`。
   **攻撃の内容:** 関数流用への攻撃は **不成立**。`timed_process` のwait4唯一のreaper・process group timeout、`count_c_lines` のC行再計数は流用できる。`bench_argv` はrr95固定を変更し、`configure_argv` は候補defineへ変更する必要があり、planはその差を認識している。

   先例の `BACK_OFF=0`・`BACKOFF_FIXED` 未指定を候補へそのまま移すことはできない。今回はpatch適用後の `BACK_OFF=1` と fixed値が必要である。`checkout→assert_pinned_clean→applied→resolve/build/verify` の順序も実在APIに合う（`patchharness.py:247,346`）。

   **期待identityへの攻撃は成立／must-fix。** planの「A-2 token prefix不一致なら停止」を残すと、今回の候補は停止する。親の事前照合は単なる全桁補完ではなく、**旧A-2 tokenとの不一致を示している**。段4では親案の現行期待値、

   - fixed-5: `678b7203…80b12`
   - fixed-10: `16c29935…a479d`

   の全桁を固定するか、旧A-2 sourceを対象とする別設計にするかを選ぶ必要がある。前者なら「現行patchの同genomeの検証」と記し、A-2とのsource bytes同一性は主張できない。
   **成果物への影響:** 起動不能を防ぎ、何を検証したかを正しく同定する。

8. **性能buildのtpsからtrace規模・verify費用を外挿する根拠はない。**
   **対象:** 依頼で挙げられた親の暗黙見積り、brief「前提の実測」、plan §2〜4。
   **攻撃の内容:** **成立／should**。ただし指定brief本文には「balanced≈4.3M tps」「write-heavy≈4M tps」の記載は見当たらず、明記された数値の誤りとは報告しない。

   `4.3M×3≈12.9M commit` は算術として正しいが、trace有効化・backoff・abort率でcommit数は変わる。さらに同じcommit数でもworkloadでtrace行数・edge数・検証時間は変わる。1681はstock・rr95・1反復である。

   「校正で実測するので本走のextime選定には固定的に使わない」は成立する。しかし校正自体のwalltime・メモリ・scratch予約には先行見積りが必要なので、設計への影響がなくなるわけではない。候補ごとの実測bytesと保全費を段Bへ引き継ぎ、初期値は代理値と明記すべき。
   **成果物への影響:** 未校正workloadの資源見積りを実測値として扱わない。

## 投入パラメータ案

以下は、**setup/build合計上限2400秒、count・inventory・保全等の合計上限300秒/走、終了余裕300秒**をrunner側でも実装する条件付き案。これらは実測値ではなく設計上の上限である。

| 段 | walltime | queue-wait-timeout | overall-grace | submit-tree数 | job数 |
|---|---|---:|---:|---|---:|
| A：校正 | `02:00:00` | `14400` | `14400` | 6本新規 | 6 |
| B：4反復/job | `03:30:00` | `14400` | `14400` | Aの6本再利用＋6本新規＝12本 | 12 |

- 段A上限式：`2400 + 3×120 + 3000 + 3×300 + 300 = 6960秒`。予約7200秒。
- 段B上限式：`2400 + 4×(120+1800+300) + 300 = 11580秒`。予約12600秒。
- 先例による段B期待値は約35分だが、hard timeoutを収容する予約値とは別である。
- runbook `:1660–1661` に記載されたgen_S上限24時間より小さい。これは文書上の照合であり、現在の `Per-Req Elapse` は親が投入前に確認する。
- **予約walltimeを4時間予算の実消費として足さない。一方、この予約では候補別4時間の実消費上限は守れない。** 本走開始前の予算配分・次rep開始可否・超過時の未確定扱いを段4で別途固定する必要がある。

## 総括

最も強い攻撃は、旧A-2 identityとの必然的衝突と、校正込み4時間会計では本走が入らない可能性である。
投入CLI不成立、同一trace再検証による独立反復の破壊、公称scratch容量不足という攻撃は成立しなかった。
段4では「現行patchの候補を検証する／旧A-2 sourceを再現する」を選び、全桁期待値を固定すべき。
併せて「4時間に校正等を含める範囲」と「運用上の未完了を同一trace再検証で解決可能とするか」を確定する。
推奨は計12 submit-tree、診断は最小限、失敗履歴と24枠の対応は厳密に保持する構成。