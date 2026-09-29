## レンズ 1

**L1-F1（must-fix）— 再投入の地位と費用が未確定。** plan は「1 request」と定めつつ、起動時停止後の再投入を §0 の記載次第としている（`s2-plan.md` §D・§E）。D1870 は attempt 数と停止基準の結果前の固定を求め、D2212 項4・D2219 項1は投入する全 job の Elapse 見積りで確認線を判定する。**放置すると、停止後の job を R2 attempt に含める地位と、2 node 時間以上の確認要否が結果を見てから変わり得る。** §0 で「再投入なし」か、再投入できる条件・上限・費用の再判定を投入前に確定する。現行の 1.72 node 時間は、5 node × 実績 1,057 秒 ÷ 3,600＝1.47 と受入見積り 0.25 の和であり、再投入を含まない（`a6-20260909b/jobs/rr95/scheduler/job.stderr:5-16`）。

**L1-F2（should-fix）— R2 図の hash override の権威を言い過ぎない。** `expected_hashes` に実ファイルから計算した値を渡すと、生成器の固定 pin 表は使われない（`tools/plotting/plot_a2_certification.py:129-159`）。一方、provenance の入力欄は固定文言 `canonical frozen report bytes` のままになる（同`:150-164`）。WAL・raw・正しさとの照合は `load_measurements` に残る（同`:512-568`）ため、これ自体は anomaly 受理条件の緩和ではない。**放置すると、図の provenance が R2 入力に独立した canonical pin があるかのように読める。** insight で「hash は collect 後の bytes を束縛するための自己計算値」と明記し、受理根拠は driver の receipt chain と生成器の照合結果に置く。caption 差し替え後の closure と再現 command は wrapper 経由で実際に成立させる（同`:897-918,932-959,966-979`）。

**L1-F3（should-fix）— 現行 pin の測定前停止を、login で減らせる範囲まで絞る。** `511c953→6810666` の差分は `cc/mocc/transaction.cc` のみで、silo 側が同一という主張は差分上正しい。ただし condition gate は isolated checkout への patch 適用後、実 compiler と依存 source を使って判定する（`orchestrator/campaign/paper_story_a2_certification.py:680-814`）。「同一 silo」から gate 通過や性能値の同一性までは言えない。**放置すると、5 node の request が測定前に止まり、R2 の値と図が得られない。** 投入前に exact pin で patch の dry check と source path の確認を行い、実 compiler・意味 witness・fanout の成否は未実測と記す。durable base の確認できた preregistration は旧 pin `511c953` であり、「6810666 での投入記録 0 件」はこの base の範囲に限定する（`a6-20260908b/preregistration.json`、`a6-20260909a/preregistration.json`、`a6-20260909b/preregistration.json`）。

## レンズ 2

**L2-F1（should-fix）— 図の負例を新たに作る作業は削れる。** plan §C は hash 不一致・外部 file 欠落・condition receipt 改変の負例を提案する。依頼は成果を insight に限り、仮想リスク向け検査の追加を scope 外としている（`request.md:3-9`）。生成器には既に hash、外部 file、receipt、描画前 layout の拒否経路がある（`tools/plotting/plot_a2_certification.py:150-159,278-355,897-918`）。**放置すると、値・図を得る作業が検査作成へ広がり、成果物が遅れる。** 原 metadata の陽性対照と、R2 実入力での通常実行・拒否理由の記録に絞る。

**L2-F2（nit）— §0 は再投入以外は足りている。** 別 attempt の地位、元系列と合算しないこと、結果によらず報告すること、規律1・2、元成果物の bytes 不変は plan §E にある。submitter の `qsub -v` は固定列挙で trace archive 変数を渡さず（`tools/pegasus/submit_paper_story_a2_certification.sh:266-275`）、checkout と collect-root の分離も実経路に合う（同`:165-233`、`orchestrator/campaign/paper_story_a2_certification.py:4811-4825`）。**放置してもこの点だけで表・図の値は変わらないが、§0 が長くなる。** §0 は地位・回数と停止基準・非合算・正しさ・保存先に絞り、運用手順は後節へ置く。

## 総括

投入 argv、5 node の会計、別 checkout／別 collect-root、trace 保全口の不在は概ね実装と整合する。規律1・2を緩める提案も見当たらない。投入前の実質的な修正点は、**再投入条件を §0 と全 job の費用見積りで確定すること**。今回の判断は静的検査であり、テスト・測定の実測は行っていない。