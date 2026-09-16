## 判別すべき命題

現時点では **「子孫の存在」と「stdout/stderr の保持」を分離できていない**。以下の判定基準を実験前に固定する。real / refuted は今回の実行環境・process 構造についての判定であり、過去の F853 への帰属とは分ける。

以下、`D` は `tools/pegasus/dispatch_compute.py`、`F` は `docs/failures.md` を表す。

| 命題 | real に倒す観測 | refuted に倒す観測 |
|---|---|---|
| H1：job 本体終了後も、生存子孫の存在だけで RUN が続く | stdout/stderr とその複製を持たない子孫が生存する間 RUN が続き、その自然終了に合わせて END | 子孫が生存している証拠がある時点で END |
| H2：stdout/stderr の保持が、子孫存在による待機とは独立に終端を遅らせる | 子孫の寿命を固定して fd 解放時刻を変えると、END が解放時刻に追随 | fd を解放しても同じ子孫の自然終了まで待つ、または fd 保持中に END |
| H3：遅延は NQSV 終端処理以前、job 側 process に残っている | `job-run-returned` が遅れる、または記録後も dispatcher の同一 PID/starttime が生存 | dispatcher の消滅を確認した後も長く RUN が続く。ただしこの観測だけで H1/H2 は分かれない |
| H4：result 公開周辺の fsync が当該停止を起こした | 停止個体で fsync 開始後の完了が欠け、process の待機箇所も対応 | **同じ停止個体**が `result-write-return`、`job-run-returned` まで到達 |
| H5：今回の機序が F853 の原因でもある | 保存された当時の process/fd 証拠と今回の条件が対応する | 当時の停止位置・fd 状態が今回の必要条件と矛盾する |

H5 は当時の submission dir が失われているため、今回の再現だけでは確定しない。根拠は M3、`F:23215`。

## 既存データで先に絞れること

1. **fsync の否定を修正する。**
   `D:691` が file fsync、`D:693` が result 置換、`D:697` が directory fsync。したがって directory fsync 停止と result 公開済みは両立する。さらに `D:1556` で先に guard を作るため、`result.json` の存在だけでは正常結果公開すら意味しない。`stage`・内容・trace を照合する。

   M4 の159件は「その159件では長時間 fsync 停止を観測しなかった」証拠であり、稀な停止一般の refutation ではない。

2. **再発ゼロの母集合を点検する。**
   親に、既存 request/receipt と `.e` の対応を一覧化してもらう。会計欠落、未終了、ログ欠落、同一 request の重複、trace 非搭載を別々に数える。M1 は「終了した job」、M3 は「保存された `.e`」を対象としており、未終了・消失個体の取りこぼしをそのまま否定できない。長い受入全走が含まれないことも M5 が明記している。

3. **pytest 完了から dispatcher 復帰までを区別する。**
   supervisor は直接の子を待つ（`D:328`）。dispatcher は supervisor 終了後にも status/exec-error pipe を読む（`D:1151`、`D:1155`、`D:1158`）。既存 trace から、この区間・result 公開区間・復帰後の区間を分ける。
   内部 pipe は exec 時に閉じる設定（`D:229`）なので、通常の generic probe がこれを保持すると推定してはならない。

4. **終了判定の説明を補正する。**
   `D:3969` の END に加え、一度見えた request が正常な qstat 応答から消えた場合も END 扱いになる（`D:3940`）。receipt の `terminal_reason` を会計と併読する。結果ファイルによる終了ではないことは確認できる（`D:4022`）。

元の個別成果物は本子から読めなかったため、数値は指定された `s1-measurements.md` を一次資料として扱う。上記の再集計は親による追加読取りであり、実施済みとはしない。

## 計算ノード実験の設計

**子孫の自然寿命を75秒に固定し、job stdout/stderr を手放す時刻だけを変える3条件**とする。

新規予定ファイルは `tools/probe_t2622_job_exit.py`。以下の行番号は**実装予定アンカー**であり、実在するコードの引用ではない。author が実装後に実行版の行番号へ更新する。

| 予定アンカー | 内容 |
|---|---|
| `tools/probe_t2622_job_exit.py:1` | CLI、条件と時刻の固定値、入力検査 |
| 同 `:30` | 時刻・PID/starttime・PPID・PGID・SID・fd 状態の記録 |
| 同 `:65` | fork 前の準備、通常ファイルの観測先確保、stderr 出力 |
| 同 `:95` | 子孫の有限時間処理、fd 解放、75秒で正常終了 |
| 同 `:145` | 直接の子である probe 本体が5秒で正常終了 |

`tools/pegasus/` は変更しない。generic の argv 実行は `D:1660`、既存 isolation 経路は `D:1669` を通す。

**process 構造と時刻**

- probe 本体が1子を `fork` する。追加の `setsid`、二重 fork、subreaper は使わず、3条件の所属関係を揃える。
- fork 直前の monotonic 時刻を `t0` とする。本体は `t0+5秒` に終了し、子を wait しない。
- 子は全条件で `t0+75秒` に `os._exit(0)` する。有限期限への sleep と有限回の観測だけを行う。
- 無期限 pipe read、FIFO open、子孫待ち、ネットワーク待ちを設けない。通常ファイルの観測先は fork 前に開く。記録失敗は寿命を延長せず、判別不能として扱う。

| 条件 | 子が job stdout/stderr を手放す時刻 | 子の終了 | 判別対象 |
|---|---:|---:|---|
| A：`close-now` | fork 直後 | 75秒 | fd を持たない子孫の存在だけで待つか |
| B：`close-30` | 30秒 | 75秒 | 生存中の fd 解放に END が追随するか |
| C：`hold-75` | 終了時 | 75秒 | fd を保持する比較条件 |

「手放す」は fd 1/2 を `/dev/null` に差し替えることとし、元の出力先への複製を残さない。全 fd の `readlink` と `fstat` を解放前後に記録し、標準 fd 番号以外の保持も点検する。fd 0 は全条件で `/dev/null`。stdout/stderr の片方ずつの分離は初回には含めない。

**投入 argv**

親が既存の detached launcher/detach 経路から、条件ごとに直列で実行する。外側に短い `timeout` を被せない。argv は以下の順で、各行が1引数。

```text
python3
tools/pegasus/dispatch_compute.py
--task
generic
--walltime
00:02:00
--queue-wait-timeout
900
--overall-grace
300
--accounting-grace
60
--poll-interval
2
--
python3
-B
tools/probe_t2622_job_exit.py
--condition
close-now
--evidence
output/insights/2026-09-16_t2622-compute-job-exit-hang/probe-A.jsonl
```

B/C は `close-now` をそれぞれ `close-30` / `hold-75`、観測先を `probe-B.jsonl` / `probe-C.jsonl` に置換する。flag は `D:4505` 以降の既存 CLI。120秒の walltime は非常用上限であり、成功条件は75秒での自然終了である。

**観測量と判定**

job stderr には本体から、条件、`t0` の realtime/monotonic ns、hostname、祖先の PID/starttime、子 PID、初期 fd 情報、予定解放・終了時刻、本体終了直前時刻を出す。子は fd を保持している間だけ、解放直前の時刻を短い行で出す。

**解放後の記録のために stderr を dup しない。** 子の観測は別の通常ファイルへ記録する。解放完了、45/60秒時点の生存、75秒の終了直前、可能なら dispatcher の同一 PID/starttime の存否を残す。`/proc` が読めなければ「不在」ではなく「観測不可」。

親は以下を突き合わせる。

- `.e` の `Started Request Time`、`Ended Request Time`
- `job-run-returned` の時刻 `J`
- 実測 fd 解放時刻 `R`、終了直前時刻 `X`
- receipt の状態履歴と終端理由
- 子の生存記録、dispatcher の消滅記録

親は END が早く来ても次条件を直ちに投入せず、75秒の寿命と証拠回収を待つ。終了直前記録だけを process 消滅の証明とはせず、残存状態が観測できない場合はその限界を残す。

事前に「時刻が対応する」を **差の絶対値5秒以内**、「十分に離れる」を **15秒以上**とする。30秒と75秒の差は45秒あり、会計の秒精度と2秒 polling に対して十分大きい。実際の `J` が遅れて分離幅を失った回は判定から外す。会計時刻の timezone を明示して変換し、`Ended−Started` と probe 内の経過時間も併記する。

| 結果 | 判定 |
|---|---|
| A は `J` 付近、B は30秒付近、C は75秒付近で END。B では END 後の子生存も確認 | H1 refuted、H2 real |
| A/B/C とも75秒付近で END。A/B の解放と生存を確認 | H1 real を支持、H2 の「fd が決め手」は refuted |
| 全条件が `J` 付近で END、C の fd 保持中の生存を確認 | この構造では H1/H2 とも refuted |
| dispatcher 自体が30秒または75秒まで残る | NQSV への直接帰属を保留し H3 を調べる |
| 条件間で process が早期消滅、記録不足、時刻対応なし | 判別不能 |

成立した差は順序を逆にした再実施で確認する。generic の clean 環境で得た結果を、そのまま pytest 全体や過去の F853 へ一般化しない。

## 空振り時の次の一手

- **子が本体終了時に消える場合：** scheduler による終端時の子孫処理等が交絡している。保持中の子が生きていないため、fd 仮説の反証には使わない。既存会計の signal/終了情報と、消える直前の PID・所属情報を先に確認する。
- **A/B/C が全部75秒の場合：** fd の複製漏れと dispatcher 生存を先に確認する。それらが除外できた場合だけ、同じ自然寿命で所属関係を変える追加実験を別途設計する。
- **全部早期 END の場合：** C の fd が本当に NQSV 出力先を継承していたか、通常ファイルか pipe か、子が END 後も生存したかを確認する。F853 当時の構造との相違を調べる。
- **`job-run-returned` が遅れる場合：** `direct-child-wait-complete`、`supervisor-wait-complete`、result 各段を照合する。stderr の `print(..., flush=True)` 自体も待ち得るため、最後の trace だけで次の処理を断定しない（`D:710`）。
- **正常終了のみで再発しない場合：** 「短い generic probe では再現せず」と報告する。停止を起こす変異や無期限 FIFO は投入しない。

## 危険の自己点検

- 本子はファイル変更、commit、ジョブ投入、pytest 実行を行っていない。
- 計画に kill、killpg、手動 qdel、既存 job への操作は含めない。
- 子孫は最大75秒の有限寿命を持ち、walltime による強制終了を実験の終了手段にしない。
- detached 実行を維持し、同一 worktree の投入は直列にする。観測失敗時に再投入を重ねない。
- 防壁、gate、回収処理、subreaper の追加は提案しない。

**ただし、指定 dispatcher を使えば「qdel・orphan hold が絶対に発生しない」とは保証できない。** 既存コードには例外時の cleanup（`D:4283`）、取消可能 snapshot 後の qdel（`D:2990`、実コマンド `D:2726`）、hold 設定（`D:4208`）がある。短い自然寿命でも、queue 待ちや scheduler 障害を除去できない。

したがって本計画は、実験自身が timeout を意図的に作らない設計である。異常経路まで含む絶対保証が必須なら、現行の指定経路ではその条件を証明できず、投入可能な計画として承認済みとは扱えない。迂回や機構追加では埋めない。

## 親 brief への指摘

- **P1-a：帰属が先行している。** `exec`（`D:913`）は shell の置換を示すだけで、dispatcher の実際の終了も NQSV の待機条件も証明しない。F853 は重要な事例だが、存在と fd 保持の分離証拠ではない。
- **P1-b：refuted は撤回すべき。** 公開後の directory fsync がある。「pytest 完了」と「result 公開」も別事象。159件の最大値を稀な停止の上限として扱えない。
- **P1-c：中心仮説として妥当だが未確定。** A/B/C の介入で初めて存在から分離する。
- **P1-d：条件付きで正しい。** `job-run-returned` まで来た個体には会計・process 生死が必要。一方、fsync や supervisor 待機中の停止では別の最終 trace になる。「hang 時も必ず最後は同じ」は広すぎる。
- **P1-e：対象範囲を限定すべき。** 保存・終了済み標本で未観測であり、全期間の再発ゼロではない。既存データによる区間分析と欠測点検はまだ可能。
- **F846 の要約は誤り。** `F:23072` は根本原因未特定と明記する。futex 待ちを thread join 待ちと確定してはいけない。
- **孫6本の回収も原因の証明ではない。** `F:25676` は残存の実在を示すが、その6本が NQSV 終端を止めたかは別の命題である。

## 総括

先に fsync の誤った反証と標本の欠測を整理し、その後、**75秒の自然寿命を共通にした3条件で fd 解放時刻だけを変える**。機序の判定には会計だけでなく、子孫の生存と dispatcher の消滅を対応づける。

得られる結論は今回の条件での機序まで。F853 への歴史的帰属や、未観測の停止原因まで確定扱いにしない。