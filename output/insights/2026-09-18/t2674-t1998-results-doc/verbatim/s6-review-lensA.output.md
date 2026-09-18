## 所見

対象は[統制稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md)。行番号はレビュー中の更新を再読した時点のもの。静的検査のみ実施した。

1. **must-fix — §4.3(j)、369–370行：最初に是正 commit を含む commit が違う。**
   稿は `291892b909706a72d501ce711f58f5fb511c56db`（09-14 11:40:29 JST）とする。しかし現行 `main` の first-parent 列では、既に `b1a3d45d61ac7a62f589c514683e5ba999b50609`（同日 **08:30:25 JST**）が `4d7cd40a9…` を含む。`git merge-base --is-ancestor` は同 commit に対して rc=0、その第1親 `e0b1c336…` に対して rc=1。
   「最初に含む」は訂正が必要。ただし、この履歴上の境界を実際の land 時刻と同一視することもできない。

2. **must-fix — §2.5、267行／§5.4、455行：終了時刻・Elapse の出所が違う。**
   稿の出所は「job stdout 末尾」。現物では `…-balanced.stderr` に `Ended Request Time: Sun Sep 13 22:39:23 2026`、`Elapse: 712S` がある。stdout 末尾は `backoff sweep: 全 genome 計測成功` で終了する。**時刻と712秒は正しいが、file が誤っている。**
   また257行の「receipt / WAL の epoch」について、submit receipt の2 recordに epoch field はない。投入時刻は qstat の `Created Request Time` などへ出所を限定する必要がある。

3. **must-fix — §5.4、448行：`genome` の field 階層が違う。**
   稿は `WAL build_start.payload.build_admission.source` を出所とする。現物の canonical genome は **`build_start.payload.genome`**。`build_admission.source` にあるのは `genome_sha256` で、`genome` はない。他の source fields と行を分ける必要がある。

4. **must-fix — §1.3、108行：lock の field 名が違う。**
   稿は `ycsb {rmw 0, rratio 50, zipf_skew 0.9}` と記載。`campaign.lock.identity_preimage` を JSON として復号した現物は：
   ```json
   {"ycsb_rmw":"0","ycsb_rratio":"50","ycsb_zipf_skew":"0.9"}
   ```
   key は `ycsb_` 付きで、値は文字列。現物を持つという記述なので、省略せず正確に転記すべき。

5. **must-fix — §2.2、198行：`perf_counter_statuses` の値・型が違う。**
   稿は `perf_counter_statuses = not_required`。現物の `result.json.perf_counter_statuses` は **`["not_required"]`**。文字列を示すなら、WAL の `bench_done.payload.perf_observation.counter_status = "not_required"` が対応する。

6. **must-fix — §1.2、84行：言い換えを「逐語」としている。**
   稿：「測定を 1 度も走らせる前に**固定された**（§4 冒頭の逐語）」
   事前登録 §4：「**次の値を、**測定を 1 度も走らせる前に**固定する。**」
   逐語ではない。原文を引用するか「逐語」を外すこと。§5.4、456行の「判定規則の逐語」も、§1.1では要約・記号置換をしているため「要約／転記」と書き分けるべき。

7. **must-fix — §2.3、231行：`result.json` の key 数が違う。**
   稿は「24 key」。現物のトップレベル key は **23件**。`correctness` が存在しないという主張自体は正しい。

8. **should-fix — §2.1、166行：「`preregistered` block は事前登録 §5 と同値」が不正確。**
   現物の `decision-final.json.preregistered.common` は `repository_commit` を追加しており、事前登録 §5 にある `schema_version` は `preregistered` にない。共有する identity 値は一致するが、block 全体は同一ではない。「§5 の対応する identity fields は全項一致」と限定するのが正確。

9. **should-fix — §2.3、229行／§3限定7、301行：A-2／A-6 の検査件数に一次資料の参照がない。**
   稿の「legacy 1回＋性能条件側5回」は、指定された T-1998 の WAL・判定 JSON・事前登録・insight README からは確認できない。該当 attempt の一次記録を明示するか、比較文を削除すべき。横断稿から転用したと断定する証拠はないが、現状ではこの命題の出所を辿れない。

観点別の照合結果：

- **観点1：** 上記の field・型・件数の不一致あり。それ以外の登録 identity、標本、判定値、binary digest、receipt ID は一致。
- **観点2：** 上記の逐語表記に不一致あり。事前登録 §2の比較対象、§4.2の拒否 digest、§6の計算内容、§9の限定、および「受理集合は広がる」の引用内容は一致。results 系列の射影は README 現物と一致。
- **観点3：不一致なし。** WALから8点すべての median と標本標準偏差÷平均を再計算し、全桁一致。登録対の ratio `1.1122537536191646`、improvement_percent `11.225375361916456` も一致。lock／WAL、事前登録、稿が掲げる `a551cdd3` の各 blob の SHA-256 と gitlink も独立に照合した。
- **観点4：不一致なし。** 両 arm 各1件の `verify_done`、`verify_configs=["legacy"]`、各1件の verifier evidence、`verify_done → bench_done` の時刻順を確認。検査 argv は対象成果物にない。
- **観点5：不一致なし。** 8行すべての variant、flags、token 前置、40標本、median、CV小数4桁、commits／aborts、WAL記載順を確認。行2の source digest は事前登録 §4.2の退けた digest と一致。
- **観点6：** 時刻・UTC/JST換算・712秒は一致。出所と「最初に含む commit」は上記のとおり不一致。
- **観点7：不一致なし。** §5.1の掲載 SHA-256 全件を再計算。4主要fileの bytes 数、WAL40 record、receipt2行、stdout268行も一致。
- **観点8：** 限定20件、欠落10件、root23 file、空file9件、WAL40 record、loader63 blobを確認。insight README は5本。冒頭の旧「4つ」はレビュー中に修正済み。別途、`result.json` の「24 key」は未修正。
- **観点9：不一致なし。** 更新後の稿と README 追加行の効果量、件数、判定、限定は整合。
- **観点10：** 上記A-2／A-6の検査件数は出所不足。T-1998自身の性能値・identity・判定は一次資料で確認でき、横断稿や版による補完を必要としなかった。

## 親の brief への異議

数値導出についての異議はなし。`wal-table-parent-derived.txt` の8点の標本・median・CV・正しさ件数・時刻は原WALと一致した。`wal-two-arms-full-records.txt` の登録2 arm・計10 recordも、原WALとJSON構造・値が一致した。

ただし、稿の§4(j)にある親の履歴調査結果は所見1の反証により採用できない。また依頼文の「job stdout末尾」という出所指定自体も、現物では stderr だった。

## 総括

**must-fix 7件、should-fix 2件、nit 0件。着地は止める。**

主要な性能値とハッシュは一致するが、履歴・出所・逐語引用・field・件数の誤りを凍結前に修正する必要がある。
